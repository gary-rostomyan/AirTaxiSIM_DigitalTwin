#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from geometry_msgs.msg import PoseStamped

from utils.config import load_yaml_file, write_shared_tmp_file, log
from utils import constants

class SimStart(Node):
    def __init__(self):
        super().__init__('sim_start')
        self.config = load_yaml_file(constants.merged_config_path, __file__)

        self.rate = self.create_rate(constants.frequency_low)

        self.sim_start_pub = self.create_publisher(Bool, '/sim_start/started', 1)
        self.sim_start_pub.publish(Bool(data=False))

        self.create_subscription(PoseStamped, f"/{self.config['ego_vehicle']['type']}/pose", self.callback, 10)

    def callback(self, msg: PoseStamped):
        # if msg:
            # log.trace("Simulator has started.")
            # self.sim_start_pub.publish(True)

        # Compute the distance
        x_curr = msg.pose.position.x
        y_curr = msg.pose.position.y
        z_curr = msg.pose.position.z
        x_init = self.config['ego_vehicle']['location']['x']
        y_init = self.config['ego_vehicle']['location']['y']
        z_init = self.config['ego_vehicle']['location']['z']
        dist = math.sqrt(
            (x_curr - x_init) ** 2 +
            (y_curr - y_init) ** 2 +
            (z_curr - z_init) ** 2
        )
        
        if dist < self.config['ego_vehicle']['planner']['distance_threshold']:
            log.trace("Simulator has started.")
            self.sim_start_pub.publish(Bool(data=True))
        else:
            log.trace("Simulator not started.")

    def run(self):
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0)
            self.rate.sleep()


if __name__ == "__main__":
    rclpy.init()
    simstart = SimStart()
    simstart.run()
    simstart.destroy_node()
    rclpy.shutdown()
