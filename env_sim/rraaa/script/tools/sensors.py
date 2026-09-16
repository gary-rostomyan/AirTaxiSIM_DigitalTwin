#!/usr/bin/env python3

import collections
import math
import time
import weakref

import carla
import numpy as np
import pygame
from geometry_msgs.msg import Twist


def get_actor_display_name(actor, truncate=250):
    """Method to get actor display name."""
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


class CollisionSensor:
    """Collision sensor wrapper."""

    def __init__(self, parent_actor, panic=False):
        self.sensor = None
        self.history = []
        self.panic = panic
        self._parent = parent_actor
        # FIX: instead of raising in the CARLA callback thread (which silently
        # kills only that listener), we set a flag and let the main thread
        # react to it inside environment.tick().
        self.panic_triggered = False
        self.panic_event = None

        world = self._parent.get_world()
        blueprint = world.get_blueprint_library().find('sensor.other.collision')
        self.sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self._parent)

        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: CollisionSensor._on_collision(weak_self, event))

    def get_collision_history(self):
        history = collections.defaultdict(int)
        for frame, intensity in self.history:
            history[frame] += intensity
        return history

    def destroy(self):
        if self.sensor is not None:
            try:
                self.sensor.stop()
            except Exception:
                pass
            try:
                self.sensor.destroy()
            except Exception:
                pass
            self.sensor = None

    @staticmethod
    def _on_collision(weak_self, event):
        self = weak_self()
        if not self:
            return

        impulse = event.normal_impulse
        intensity = math.sqrt(impulse.x ** 2 + impulse.y ** 2 + impulse.z ** 2)
        self.history.append((event.frame, intensity))
        if len(self.history) > 4000:
            self.history.pop(0)

        if self.panic:
            # FIX: do NOT raise here — this runs in a CARLA C++ callback thread.
            # Raising would silently kill only this listener; the main thread
            # would never see the exception. Set a flag instead.
            self.panic_triggered = True
            self.panic_event = f"Collision intensity={intensity:.2f} at frame {event.frame}"


class CustomTimer:
    def __init__(self):
        try:
            self.timer = time.perf_counter
        except AttributeError:
            self.timer = time.time

    def time(self):
        return self.timer()


class SensorManager:
    """
    Backward-compatible sensor wrapper.

    Supports both call styles:
      1) SensorManager(world, sensor_type, transform, attached, sensor_options)
      2) SensorManager(world, display_manager, sensor_type, transform, attached, sensor_options, display_pos)
    """

    def __init__(self, world, *args):
        self.surface = None
        self.world = world
        self.display_manager = None
        self.display_pos = None
        self.sensor_options = {}
        self.sensor = None
        self.timer = CustomTimer()
        self.time_processing = 0.0
        self.tics_processing = 0
        self.data = None
        self.last_frame = None

        sensor_type, transform, attached, sensor_options = self._parse_args(*args)
        self.sensor_options = dict(sensor_options or {})
        self.sensor = self.init_sensor(sensor_type, transform, attached, self.sensor_options)

        if self.display_manager is not None and hasattr(self.display_manager, 'add_sensor'):
            self.display_manager.add_sensor(self)

    def _parse_args(self, *args):
        # Legacy project usage:
        # SensorManager(world, 'RGBCamera', transform, attached, sensor_options)
        if len(args) == 4 and isinstance(args[0], str):
            sensor_type, transform, attached, sensor_options = args
            return sensor_type, transform, attached, sensor_options

        # Optional display_manager without display_pos
        if len(args) == 5 and not isinstance(args[0], str):
            self.display_manager, sensor_type, transform, attached, sensor_options = args
            return sensor_type, transform, attached, sensor_options

        # Original "display_manager" style
        if len(args) == 6 and not isinstance(args[0], str):
            self.display_manager, sensor_type, transform, attached, sensor_options, self.display_pos = args
            return sensor_type, transform, attached, sensor_options

        raise TypeError(
            "SensorManager expected either "
            "(world, sensor_type, transform, attached, sensor_options) or "
            "(world, display_manager, sensor_type, transform, attached, sensor_options[, display_pos])"
        )

    def init_sensor(self, sensor_type, transform, attached, sensor_options):
        if sensor_type == 'RGBCamera':
            camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
            for key, value in sensor_options.items():
                camera_bp.set_attribute(key, str(value))

            camera = self.world.spawn_actor(camera_bp, transform, attach_to=attached)
            weak_self = weakref.ref(self)
            camera.listen(lambda image: SensorManager._on_rgb_image(weak_self, image))
            return camera

        if sensor_type == 'LiDAR':
            lidar_bp = self.world.get_blueprint_library().find('sensor.lidar.ray_cast')
            lidar_bp.set_attribute('range', '100')
            lidar_bp.set_attribute('horizontal_fov', '150')
            lidar_bp.set_attribute(
                'dropoff_general_rate',
                lidar_bp.get_attribute('dropoff_general_rate').recommended_values[0]
            )
            lidar_bp.set_attribute(
                'dropoff_intensity_limit',
                lidar_bp.get_attribute('dropoff_intensity_limit').recommended_values[0]
            )
            lidar_bp.set_attribute(
                'dropoff_zero_intensity',
                lidar_bp.get_attribute('dropoff_zero_intensity').recommended_values[0]
            )

            for key, value in sensor_options.items():
                lidar_bp.set_attribute(key, str(value))

            lidar = self.world.spawn_actor(lidar_bp, transform, attach_to=attached)
            weak_self = weakref.ref(self)
            lidar.listen(lambda image: SensorManager._on_lidar_points(weak_self, image))
            return lidar

        if sensor_type == 'None':
            return None

        raise ValueError(f"Unsupported sensor type: {sensor_type}")

    def get_sensor(self):
        return self.sensor

    def destroy(self):
        if self.sensor is not None:
            try:
                self.sensor.stop()
            except Exception:
                pass
            try:
                self.sensor.destroy()
            except Exception:
                pass
            self.sensor = None

    @staticmethod
    def _on_rgb_image(weak_self, image):
        self = weak_self()
        if self is None:
            return

        t_start = self.timer.time()

        image.convert(carla.ColorConverter.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]  # BGRA -> RGB

        self.data = array
        self.last_frame = image.frame
        try:
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        except Exception:
            self.surface = None

        t_end = self.timer.time()
        self.time_processing += (t_end - t_start)
        self.tics_processing += 1

    @staticmethod
    def _on_lidar_points(weak_self, image):
        self = weak_self()
        if self is None:
            return

        t_start = self.timer.time()

        points = np.frombuffer(image.raw_data, dtype=np.float32)
        points = np.reshape(points, (int(points.shape[0] / 4), 4))
        self.data = points
        self.last_frame = image.frame

        t_end = self.timer.time()
        self.time_processing += (t_end - t_start)
        self.tics_processing += 1


class GuamVelocitySensor:
    def __init__(self, node):
        self.sub = node.create_subscription(Twist, '/guam/velocity', self.on_new_msg, 1)
        self.linear = carla.Vector3D()
        self.angular = carla.Vector3D()
        self.ready = False

    def __str__(self):
        return "x:{}, y:{}, z:{}, roll:{}, pitch:{}, yaw:{}".format(
            self.linear.x, self.linear.y, self.linear.z,
            self.angular.x, self.angular.y, self.angular.z
        )

    def on_new_msg(self, msg):
        if not self.ready:
            self.ready = True
        self.linear.x = msg.linear.x
        self.linear.y = msg.linear.y
        self.linear.z = msg.linear.z
        self.angular.x = msg.angular.x
        self.angular.y = msg.angular.y
        self.angular.z = msg.angular.z

    def get_vel(self):
        return self.linear, self.angular

    def is_ready(self):
        return self.ready