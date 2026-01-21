#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, HistoryPolicy, ReliabilityPolicy
import functools as ft
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32MultiArray

from utils.vehicle import Vehicle_Node
from utils.config import load_yaml_file, log
from utils import constants

class MiniHawk_Node(Vehicle_Node):
    def __init__(self, config) -> None:
        super().__init__(config)

        # Topic to which pose data is published
        self.pose_topic = "/minihawk_SIM/mavros/local_position/pose"
        self.minihawk_reference_topic = "/minihawk_SIM/mavros/setpoint_position/local"

        qos_reliable_depth_1 = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE
        )

        # Subscribe to the topic which publishes the waypoints
        self.minihawk_reference_sub = self.create_subscription(
            Float32MultiArray,
            config['ego_vehicle']['planner_topic'],
            self.minihawk_reference_callback,
            qos_reliable_depth_1
        )
        self.minihawk_reference_pub = self.create_publisher(
            PoseStamped,
            self.minihawk_reference_topic,
            qos_reliable_depth_1
        )

        self.pose_sub = self.create_subscription(
            PoseStamped,
            self.pose_topic,
            self.pose_callback,
            qos_reliable_depth_1
        )

    def minihawk_reference_callback(self, data):
        # Parse the waypoint data
        x_target, y_target, z_target, x_vel_target, y_vel_target, z_vel_target = data.data

        # Transform the coordinates
        x_target_transformed = x_target
        y_target_transformed = -y_target
        z_target_transformed = z_target
        
        # Publish the target point data to MiniHawk's target point ROS topic (on Gazebo's side)
        waypoint = PoseStamped()
        waypoint.header.stamp = self.get_clock().now().to_msg()
        waypoint.header.frame_id = "map"
        waypoint.pose.position.x = x_target_transformed
        waypoint.pose.position.y = y_target_transformed
        waypoint.pose.position.z = z_target_transformed
        self.minihawk_reference_pub.publish(waypoint)

    def pose_callback(self, pose_data):
        self.vehicle_pose_msg.header.stamp = self.get_clock().now().to_msg()
        self.vehicle_pose_msg.header.frame_id = pose_data.header.frame_id

        # Set the location
        # NOTE: I introduced a "-" sign at the Y-coordinate on Oct-27-2024, because the Y-axis was flipped.
        self.vehicle_pose_msg.pose.position.x = pose_data.pose.position.x
        self.vehicle_pose_msg.pose.position.y = -pose_data.pose.position.y
        self.vehicle_pose_msg.pose.position.z = pose_data.pose.position.z

        # Set the orientation
        # NOTE: Gazebo and CARLA have different frames of reference: right-handed and left-handed respectively. The code below accounts for it correctly.
        x = pose_data.pose.orientation.x
        y = pose_data.pose.orientation.y
        z = pose_data.pose.orientation.z
        w = pose_data.pose.orientation.w
        self.vehicle_pose_msg.pose.orientation.x = z
        self.vehicle_pose_msg.pose.orientation.y = y
        self.vehicle_pose_msg.pose.orientation.z = x
        self.vehicle_pose_msg.pose.orientation.w = w

        self.vehicle_pose_pub.publish(self.vehicle_pose_msg)

    def main(self):
        pass


if __name__ == "__main__":
    rclpy.init(args=None)

    config = load_yaml_file(constants.merged_config_path, __file__)
    vehicle_type = config['ego_vehicle']['type']
    assert vehicle_type == 'minihawk', "This node only supports MiniHawk vehicle."

    try:
        minihawk_node = MiniHawk_Node(config)
        rclpy.spin(minihawk_node)
    except KeyboardInterrupt:
        pass
    finally:
        if 'minihawk_node' in locals():
            minihawk_node.destroy_node()
        rclpy.shutdown()
