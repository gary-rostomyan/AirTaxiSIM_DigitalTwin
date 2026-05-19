#!/usr/bin/env python3
#/vehicles/jaxguam/jaxguam/node_vehicle.py

import functools as ft
from time import sleep as _sleep
import ipdb
import numpy as np
import os
import traceback
import threading
import rclpy
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from loguru import logger

from geometry_msgs.msg import Pose, PoseStamped
from trajectory_msgs.msg import JointTrajectoryPoint
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray

import jax
import jax.random as jr
import jax.numpy as jnp
import jax.tree_util as jtu
from jax_guam.functional.guam_new import FuncGUAM, GuamState
from jax_guam.guam_types import RefInputs
from jax_guam.utils.jax_utils import jax2np, jax_use_cpu, jax_use_double
from jax_guam.utils.logging import set_logger_format

from jaxguam.guam_plot_batch_with_ref import plot_batch_with_ref

from utils.vehicle import Vehicle_Node
from utils.config import load_yaml_file
from utils import constants

class GUAM_Node(Vehicle_Node):
    def __init__(self, config):
        self.config = config
        super(GUAM_Node, self).__init__(config)

        jax_use_cpu()
        jax_use_double()
        set_logger_format()

        self.skip_sleep = config['ego_vehicle']['skip_sleep']
        self.plot_switch = config['ego_vehicle']['plot']
        self.save_video = config['ego_vehicle']['save_video']

        self.guam = None
        self.guam_reference = None
        self.guam_reference_sub = None

        logger.info("Subscribing to planner for trajectory reference...")
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        self.guam_reference_sub = self.create_subscription(
            Float32MultiArray,
            config['ego_vehicle']['planner_topic'],
            self.guam_reference_callback,
            qos_profile
        )

        self.guam_reference_init()

    def guam_reference_init(self):
        pos_des = jnp.array(self.initial_position) * jnp.array([3.28084, 3.28084, -3.28084])
        vel_bIc_des = jnp.array(self.initial_velocity) * jnp.array([3.28084, -3.28084, -3.28084])
        chi_des = jnp.float32(0.0)
        chi_dot_des = jnp.float32(0.0)
        self.guam_reference = RefInputs(
            Vel_bIc_des=vel_bIc_des,
            Pos_des=pos_des,
            Chi_des=chi_des,
            Chi_dot_des=chi_dot_des,
        )

    def guam_reference_callback(self, msg):
        logger.debug(f"Received waypoint: {msg.data[:3]}")
        pos_des = jnp.array([msg.data[0], msg.data[1], msg.data[2]]) * jnp.array([3.28084, 3.28084, -3.28084])
        vel_bIc_des = jnp.array([msg.data[3], msg.data[4], msg.data[5]]) * jnp.array([3.28084, -3.28084, -3.28084])
        chi_des = jnp.float32(0.0)
        chi_dot_des = jnp.float32(0.0)
        self.guam_reference = RefInputs(
            Vel_bIc_des=vel_bIc_des,
            Pos_des=pos_des,
            Chi_des=chi_des,
            Chi_dot_des=chi_dot_des,
        )

    def main(self):
        logger.info("Constructing GUAM...")
        self.guam = FuncGUAM()
        batch_size = 1
        state = GuamState.create()

        state.aircraft[:] = np.array([self.guam_reference.Vel_bIc_des[0],
                                      self.guam_reference.Vel_bIc_des[1],
                                      self.guam_reference.Vel_bIc_des[2],
                                      0, 0, 0,
                                      self.guam_reference.Pos_des[0],
                                      self.guam_reference.Pos_des[1],
                                      self.guam_reference.Pos_des[2],
                                      1, 0, 0, 0])

        logger.info("Calling GUAM...")
        b_state: GuamState = jtu.tree_map(
            lambda x: np.broadcast_to(x, (batch_size,) + x.shape).copy(), state)

        vmap_step = jax.jit(
            jax.vmap(ft.partial(self.guam.step, self.guam.dt), in_axes=(0, None)),
            backend='cpu'
        )

        def simulate_batch(self, b_state0) -> GuamState:
            b_state = b_state0
            if self.plot_switch:
                Tb_state = [b_state0]
                time_list = [0]
                vel_des0 = b_state0.aircraft[0][0:3].tolist()
                pos_des0 = b_state0.aircraft[0][6:9].tolist()
                Ref_list = [vel_des0 + pos_des0]

            kk = 0
            logger.info("Entering simulate_batch loop... (first step triggers JIT compilation)")
            while rclpy.ok():
                # FIX: no spin_once here — a dedicated thread runs rclpy.spin()
                # so callbacks are always processed regardless of main loop timing.

                t = kk * self.guam.dt
                kk += 1

                ref_inputs = self.guam_reference

                try:
                    b_state = vmap_step(b_state, ref_inputs)
                except Exception:
                    logger.error("Exception in vmap_step:")
                    traceback.print_exc()
                    raise

                if kk == 2:
                    logger.info("JIT compilation done, simulation running.")
                if kk % 1000 == 0:
                    logger.info(f"Step {kk}, "
                                f"pos=({float(b_state.aircraft[0][6]/3.28084):.2f}, "
                                f"{float(b_state.aircraft[0][7]/3.28084):.2f}, "
                                f"{float(b_state.aircraft[0][8]/3.28084*-1):.2f}), "
                                f"ref_pos=({float(ref_inputs.Pos_des[0]/3.28084):.2f}, "
                                f"{float(ref_inputs.Pos_des[1]/3.28084):.2f}, "
                                f"{float(ref_inputs.Pos_des[2]/3.28084*-1):.2f})")

                if self.plot_switch:
                    time_list.append(t)
                    Ref_list.append(ref_inputs.Vel_bIc_des.tolist() + ref_inputs.Pos_des.tolist())
                    Tb_state.append(jax2np(b_state))

                try:
                    self.vehicle_pose_msg.pose.position.x = float(b_state.aircraft[0][6] / 3.28084)
                    self.vehicle_pose_msg.pose.position.y = float(b_state.aircraft[0][7] / 3.28084)
                    self.vehicle_pose_msg.pose.position.z = float(b_state.aircraft[0][8] / 3.28084 * -1)

                    q_x = float(b_state.aircraft[0][9])
                    q_y = float(b_state.aircraft[0][10])
                    q_z = float(b_state.aircraft[0][11])
                    q_w = float(b_state.aircraft[0][12])
                    self.vehicle_pose_msg.pose.orientation.x = -q_w
                    self.vehicle_pose_msg.pose.orientation.y = -q_z
                    self.vehicle_pose_msg.pose.orientation.z = q_y
                    self.vehicle_pose_msg.pose.orientation.w = q_x
                    self.vehicle_pose_pub.publish(self.vehicle_pose_msg)

                    self.vehicle_vel_msg.linear.x = float(b_state.aircraft[0][0] / 3.28084)
                    self.vehicle_vel_msg.linear.y = float(b_state.aircraft[0][1] / 3.28084)
                    self.vehicle_vel_msg.linear.z = float(b_state.aircraft[0][2] / 3.28084 * -1)
                    self.vehicle_vel_pub.publish(self.vehicle_vel_msg)
                except Exception:
                    logger.error("Exception in publish:")
                    traceback.print_exc()
                    raise

                if self.skip_sleep == False:
                    _sleep(self.guam.dt)

            if self.plot_switch:
                bT_state = jtu.tree_map(lambda *args: np.stack(list(args), axis=1), *Tb_state)
                return bT_state, Ref_list, time_list

        if self.plot_switch:
            if not os.path.exists("results"):
                os.makedirs("results")
            bT_state, Ref_list, time_list = simulate_batch(self, b_state)
            np.savez("results/bT_state.npz", aircraft=bT_state.aircraft)
            Ref_list = np.array(Ref_list)
            np.savez("results/Ref_list.npz", Vel_des=Ref_list[:, 0:3], Pos_des=Ref_list[:, 3:6])
            np.savez("results/time_list.npz", np.array(time_list))
        else:
            simulate_batch(self, b_state)


def main(args=None):
    rclpy.init(args=args)

    config = load_yaml_file(constants.merged_config_path, __file__)

    vehicle_type = config['ego_vehicle']['type']
    assert vehicle_type == 'jaxguam', "This node only supports JaxGUAM vehicle, remove jaxguam service from config."

    try:
        guam_node = GUAM_Node(config)

        # FIX: run rclpy.spin in a dedicated thread so callbacks (especially
        # guam_reference_callback) are always processed even when the main
        # thread is busy with GUAM computation.
        spin_thread = threading.Thread(target=rclpy.spin, args=(guam_node,), daemon=True)
        spin_thread.start()
        logger.info("Spin thread started.")

        if config['ego_vehicle']['debug']:
            with ipdb.launch_ipdb_on_exception():
                guam_node.main()
        else:
            guam_node.main()

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down.")
    except Exception:
        logger.error("Unhandled exception in main:")
        traceback.print_exc()
    finally:
        rclpy.shutdown()

    if vehicle_type == 'guam' and config['ego_vehicle']['plot']:
        logger.info("Ploting...")
        plot_batch_with_ref(save_video=config['ego_vehicle']['save_video'])


if __name__ == "__main__":
    main()