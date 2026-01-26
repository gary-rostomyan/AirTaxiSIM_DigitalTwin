#!/usr/bin/env python3
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Vector3


# ROS 2 Update (requries OOP design instead of global variables + while loops)
class ControllerNode(Node):
    def __init__(self):
        super().__init__('controller_node')

        self.P_gain = 0.05
        self.I_gain = 0.000
        self.D_gain = 0.001

        self.TARGET_CLASS_INDEX = 2
        self.FREQ_LOW_LEVEL = 10  # Hz

        # Initialize previous error and integral for PID
        self.previous_error_x = 0.0
        self.previous_error_y = 0.0
        self.previous_error_z = 0.0

        self.integral_x = 0.0
        self.integral_y = 0.0
        self.integral_z = 0.0

        # Store the latest received message
        self.tracking_array_received = None

        # subscriber init.
        self.sub = self.create_subscription(Float32MultiArray, '/yolo_node/sort_mot_predictions', self.sub_callback, 10)

        # publishers init.
        self.pub_tgt_box = self.create_publisher(Vector3, '/controller_node/tgt_box_rcvd', 10)
        self.pub_vel_cmd = self.create_publisher(Vector3, '/controller_node/vel_cmd', 10)

        # Timers
        timer_period = 1.0 / self.FREQ_LOW_LEVEL
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.t_step = 0
        self.get_logger().info("Controller Node has been started.")

    def sub_callback(self, msg):
        self.tracking_array_received = msg

    def timer_callback(self):
        self.t_step += 1

        vel_cmd_tracking = Vector3()
        vel_cmd_tracking.x = 0.0
        vel_cmd_tracking.y = 0.0
        vel_cmd_tracking.z = 0.0

        if self.tracking_array_received is not None:
            if hasattr(self.tracking_array_received, 'layout') and len(self.tracking_array_received.layout.dim) >= 2:
                height = self.tracking_array_received.layout.dim[0].size
                width = self.tracking_array_received.layout.dim[1].size
                np_tracking = np.array(self.tracking_array_received.data).reshape((height, width))

                if len(np_tracking) > 0:  # The last object
                    the_obj = np_tracking[-1]
                    x1, y1, x2, y2 = the_obj[0:4]

                    x_ctr = (x1 + x2) / 2
                    y_ctr = (y1 + y2) / 2
                    size = (x2 - x1) * (y2 - y1) / 1000

                    CTR_X_POS = 224
                    CTR_Y_POS = 224
                    AREA_SIZE = 50

                    ### Calculate error ###
                    error_x = x_ctr - CTR_X_POS
                    error_y = y_ctr - CTR_Y_POS
                    error_z = size ** 0.5 - (AREA_SIZE) ** 0.7

                    ### Integral Term ###
                    self.integral_x += error_x
                    self.integral_y += error_y
                    self.integral_z += error_z

                    ### Derivative Term ###
                    derivative_x = error_x - self.previous_error_x
                    derivative_y = error_y - self.previous_error_y
                    derivative_z = error_z - self.previous_error_z

                    ### Update previous errors ###
                    self.previous_error_x = error_x
                    self.previous_error_y = error_y
                    self.previous_error_z = error_z

                    ### PID control signals ###
                    cmd_vx = self.P_gain * error_x + self.I_gain * self.integral_x + self.D_gain * derivative_x
                    cmd_vy = self.P_gain * -error_y + self.I_gain * self.integral_y + self.D_gain * -derivative_y
                    cmd_vz = .5 * error_z

                    ### Clipping ###
                    cmd_vx = np.clip(cmd_vx, -1, 1)
                    cmd_vy = np.clip(cmd_vy, -1, 1)
                    cmd_vz = np.clip(cmd_vz, -1, 1)

                    vel_cmd_tracking.y = float(cmd_vx)  # if target is at the right then generate positive cmd_vx
                    vel_cmd_tracking.x = float(cmd_vy)  # if target is at the above then generate positive cmd_vy
                    vel_cmd_tracking.z = float(cmd_vz)  # if target is small then generate positive cmd_vz

        self.pub_vel_cmd.publish(vel_cmd_tracking)


def main(args=None):
    rclpy.init(args=args)

    node = ControllerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
