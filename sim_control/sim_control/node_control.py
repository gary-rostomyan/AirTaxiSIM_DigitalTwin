#!/usr/bin/env python3

import os
import sys
import math

import rclpy
from std_msgs.msg import Bool
from geometry_msgs.msg import PoseStamped, Twist

from loguru import logger as log

from utils.config import load_yaml_file, write_shared_tmp_file
from utils import constants

class SimControl:
    def __init__(self) -> None:
        self.config = load_yaml_file(constants.merged_config_path, __file__)

        rclpy.init(args=None)
        self.node = rclpy.create_node("sim_control")
        self.rate = self.node.create_rate(constants.frequency_low)

        # Pose & target pose
        self.pose = None
        self.target_pose = None
        self.target_reached_pub = self.node.create_publisher(Bool, '/sim_control/target_reached', 1)
        self.target_reached = False
        self.pose_threshold = self.config['landing_threshold'] # If the distance between the target pose and the current pose is less than this number in meters, then the target is reached.
        self.pose_sub = self.node.create_subscription(PoseStamped, f"/{self.config['ego_vehicle']['type']}/pose", self.pose_callback, 10)
        self.target_pose_sub = self.node.create_subscription(Twist, "/target/pose", self.target_pose_callback, 10)

    def pose_callback(self, msg):
        if self.target_reached:
            return

        self.pose = msg
        if self.pose_is_within_threshold():
            log.success("Landing target reached.")
            self.target_reached = True
        else:
            log.trace("Landing target not reached.")

        self.target_reached_pub.publish(Bool(data=self.target_reached))
        write_shared_tmp_file(constants.landing_target_reached_file, self.target_reached)

    def target_pose_callback(self, msg):
        self.target_pose = msg

    def pose_is_within_threshold(self) -> bool:
        # Check that both current and target poses are not None
        if self.pose is None or self.target_pose is None:
            return False

        # Current location
        curr_x = self.pose.pose.position.x
        curr_y = self.pose.pose.position.y
        curr_z = self.pose.pose.position.z

        # Target location
        targ_x = self.target_pose.linear.x
        targ_y = self.target_pose.linear.y
        targ_z = self.target_pose.linear.z

        # Find the distance
        dist = math.sqrt((curr_x - targ_x) ** 2 + (curr_y - targ_y) ** 2 + (curr_z - targ_z) ** 2)
        return dist <= self.pose_threshold

    def run(self):
        while rclpy.ok():
            rclpy.spin_once(self.node, timeout_sec=0)
            self.rate.sleep()

        self.node.destroy_node()
        rclpy.shutdown()

def main():
    controller = SimControl()
    controller.run()

if __name__ == "__main__":
    main()