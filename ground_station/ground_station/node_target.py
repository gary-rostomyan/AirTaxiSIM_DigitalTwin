#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped

from utils import constants
from utils.config import load_yaml_file


class TargetPublisher(Node):
    def __init__(self):
        super().__init__('target')
        try:
            # Load {x,y,z} from the config file
            self.config = load_yaml_file(constants.merged_config_path, __file__)
            self.target_type = self.config['target']['type']
            self.tgt_x = float(self.config['target']['x'])
            self.tgt_y = float(self.config['target']['y'])
            self.tgt_z = float(self.config['target']['z'])
        except Exception as e:
            self.get_logger().error(f"Failed to load config: {e}")
            raise e

        # Publisher for target pose
        self.publisher_ = self.create_publisher(Twist, '/target/pose', 10)
        self.initial_pose = None
        self.msg = Twist()

        # Handle "absolute" or "relative" target type
        if self.target_type == "absolute":
            self.get_logger().info("Mode: ABSOLUTE")
            self.msg.linear.x = self.tgt_x
            self.msg.linear.y = self.tgt_y
            self.msg.linear.z = self.tgt_z
        elif self.target_type == "relative":
            self.get_logger().info("Mode: RELATIVE")
            vehicle_type = self.config['ego_vehicle']['type']
            topic_name = f'/{vehicle_type}/pose'
            # Subscribe to vehicle pose to calculate relative target
            self.subscription = self.create_subscription(PoseStamped, topic_name, self.pose_callback, 10)
        else:
            self.get_logger().error(f"Incorrect target type: {self.target_type}")
            raise ValueError(f"Incorrect target type {self.target_type}. Must be one of: absolute, relative.")

        # Create timer for publishing at 10Hz
        timer_period = 0.1  # 10Hz
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def pose_callback(self, msg):
        """Callback to capture initial pose for relative target calculation."""
        if self.initial_pose is None:
            self.initial_pose = msg
            self.get_logger().info(f"Initial pose captured: x={msg.pose.position.x:.2f}, y={msg.pose.position.y:.2f}")

    def timer_callback(self):
        """Publish target pose at 10Hz."""
        if self.target_type == "absolute":
            self.publisher_.publish(self.msg)
        elif self.target_type == "relative":
            if self.initial_pose is not None:
                self.msg.linear.x = self.tgt_x + self.initial_pose.pose.position.x
                self.msg.linear.y = self.tgt_y + self.initial_pose.pose.position.y
                self.msg.linear.z = self.tgt_z + self.initial_pose.pose.position.z
                self.publisher_.publish(self.msg)


def main(args=None):
    rclpy.init(args=args)

    try:
        node = TargetPublisher()
        node.get_logger().info(f"Starting spin...")
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        rclpy.logging.get_logger('target_main').error(f"Error in target node: {e}")
    finally:
        if 'node' in locals():
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
