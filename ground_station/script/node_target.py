#!/usr/bin/env python3

import os
import sys
import rclpy
from geometry_msgs.msg import Twist, PoseStamped
# import pdb; pdb.set_trace()
sys.path.append(os.path.abspath('/catkin_ws/src/scripts/utils'))
from utils import constants
from utils.config import load_yaml_file

class PoseListener:
    def __init__(self, node, vehicle_type):
        self.data = None
        self.vehicle_type = vehicle_type
        self.subscriber = node.create_subscription(PoseStamped, f'/{vehicle_type}/pose', self.callback, 10)  # Replace with your topic and message type

    def callback(self, data):
        if self.data is None:
            self.data = data  # Store the received message

def main():
    rclpy.init()
    node = rclpy.create_node('target')
    pub = node.create_publisher(Twist, '/target/pose', 10)
    r = node.create_rate(10) # 10hz
    target_point = Twist()

    # Load {x,y,z} from the config file
    config = load_yaml_file(constants.merged_config_path, __file__)
    target_type = config['target']['type']
    x = config['target']['x']
    y = config['target']['y']
    z = config['target']['z']

    # Handle "absolute", "relative"
    if target_type == "absolute":
        pass
    elif target_type == "relative":
        # Estimate the starting pose
        pose_listener = PoseListener(node, vehicle_type=config['ego_vehicle']['type'])
    else:
        raise ValueError(f"Incorrect target type {config['target']['type']}. Must be one of: absolute, relative.")

    # Publish the target pose
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0)
        if target_type == "absolute":
            target_point.linear.x = float(x)
            target_point.linear.y = float(y)
            target_point.linear.z = float(z)
            pub.publish(target_point)
        elif target_type == "relative":
            if pose_listener.data is not None:
                target_point.linear.x = x + pose_listener.data.pose.position.x
                target_point.linear.y = y + pose_listener.data.pose.position.y
                target_point.linear.z = z + pose_listener.data.pose.position.z
                pub.publish(target_point)
        else:
            raise ValueError(f"Incorrect target type {config['target']['type']}. Must be one of: absolute, relative.")
        r.sleep()

    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()