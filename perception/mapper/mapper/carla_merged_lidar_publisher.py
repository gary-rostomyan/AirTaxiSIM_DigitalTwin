#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import sensor_msgs_py.point_cloud2 as pcl2
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import Header
import numpy as np
import threading
from functools import partial

class CarlaMultiLidarMerger(Node):
    def __init__(self):
        super().__init__('carla_merged_lidar_publisher')

        self.get_logger().info('CarlaMultiLidarMerger node starting...')

        self.lock = threading.Lock()
        self.latest_clouds = {}

        # List of topic names to subscribe to
        self.lidar_topics = [
            '/carla_node/lidar_point_cloud_down',
            '/carla_node/lidar_point_cloud_up',
            '/carla_node/lidar_point_cloud_left',
            '/carla_node/lidar_point_cloud_right',
            '/carla_node/lidar_point_cloud_back',
            '/carla_node/lidar_point_cloud_forward',
        ]

        # Subscribe to each topic
        for topic in self.lidar_topics:
            self.create_subscription(PointCloud2, topic, partial(self.lidar_callback, topic=topic), 10)

        # Publisher for the merged cloud (what Octomap will listen to)
        self.pub_merged = self.create_publisher(PointCloud2, '/carla_node/lidar_point_cloud', 1)

        # Publish merged cloud periodically
        self.create_timer(0.1, self.publish_merged_cloud)  # 10 Hz

    def lidar_callback(self, msg, topic):
        with self.lock:
            self.latest_clouds[topic] = msg

    def publish_merged_cloud(self):
        with self.lock:
            if not self.latest_clouds:
                return

            all_points = []

            for msg in self.latest_clouds.values():
                points = list(pcl2.read_points(msg, field_names=["x", "y", "z"], skip_nans=True))
                all_points.extend(points)

            if all_points:
                header = Header()
                header.stamp = self.get_clock().now().to_msg()
                header.frame_id = "sensor"  # Adjust if needed for your TF tree

                merged_cloud = pcl2.create_cloud_xyz32(header, all_points)
                self.pub_merged.publish(merged_cloud)

def main(args=None):
    rclpy.init(args=args)
    try:
        node = CarlaMultiLidarMerger()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()