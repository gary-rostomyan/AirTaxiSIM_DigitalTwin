#!/usr/bin/env python3

import atexit
import os
import rclpy
from rclpy.node import Node
from rclpy.serialization import serialize_message
import rosbag2_py
import signal
from threading import Lock

from std_msgs.msg import Bool, String, Float32MultiArray
from geometry_msgs.msg import PoseStamped, Twist
from sensor_msgs.msg import Image

from utils.config import load_yaml_file, log
from utils import constants

class TopicRecorder(Node):
    def __init__(self):
        self.config = load_yaml_file(constants.merged_config_path, __file__)

        rclpy.init()
        super().__init__('sim_recorder')
        self.rate = self.create_rate(constants.frequency_low)

        # Set up the topics to be recorded
        self.topics_to_record = [
            (f"/{self.config['ego_vehicle']['type']}/pose", PoseStamped),
            (self.config['ego_vehicle']['reference_topic'], Twist),
            (f"/{self.config['ego_vehicle']['type']}/velocity", Twist),
            ("/yolo_node/yolo_pred_frame", Image),
            ("/yolo_node/yolo_predictions", Float32MultiArray)
        ]

        self.recording = False
        self.recording_done = False
        self.writer = None

        try:
            self.recording_requested = self.config['record_rosbag']
        except KeyError:
            self.recording_requested = False

        if not self.recording_requested:
            return

        self.lock = Lock()

        # Subscribe to the trigger topic
        self.create_subscription(Bool, '/sim_start/started', self.sim_start_callback, 10)

        # Subscribe to the topics for recording
        self.subscribers = []
        for topic, msg_type in self.topics_to_record:
            self.subscribers.append(self.create_subscription(msg_type, topic, lambda msg, t=topic: self.record_callback(msg, t), 10))

        atexit.register(self.terminate)
        signal.signal(signal.SIGINT, self.shutdown_handler)
        signal.signal(signal.SIGTERM, self.shutdown_handler)

    def sim_start_callback(self, msg):
        if msg.data and not self.recording and not self.recording_done:
            log.info("Recording started")
            self.recording = True
            rosbag_path = os.path.join(os.path.dirname(constants.merged_config_path), "recorded_topics.mcap")
            log.info(f"Starting rosbag at {rosbag_path}")

            # TODO: is this the right update?
            # ROS 2 requires explicit topic registration and serialization, unlike ROS 1's automatic type inference.
            self.writer = rosbag2_py.SequentialWriter()
            self.writer.open(rosbag2_py.StorageOptions(uri=rosbag_path, storage_id='mcap'),
                             rosbag2_py.ConverterOptions('', ''))
            for topic, msg_type in self.topics_to_record:
                type_name = f"{msg_type.__module__.split('.')[0]}/msg/{msg_type.__name__}"
                self.writer.create_topic(
                    rosbag2_py.TopicMetadata(name=topic, type=type_name, serialization_format='cdr'))

    def record_callback(self, msg, topic):
        if self.recording and self.writer:
            try:
                with self.lock:
                    self.writer.write(topic, serialize_message(msg), self.get_clock().now().nanoseconds)
            except Exception as e:
                self.get_logger().error(f"Failed to write to bag file: {e}")

    def shutdown_handler(self, signal_number, frame):
        self.terminate(signal_number)

    def terminate(self, signal_number=None):
        self.recording = False
        self.recording_done = True
        if self.writer:
            del self.writer  # Triggers close in ROS2 python wrapper
            self.writer = None
        if signal_number == None:
            log.success(f"Recording stopped")
        else:
            log.success(f"Recording stopped with signal {signal_number}")
        if rclpy.ok(): rclpy.shutdown()

    def run(self):
        try:
            while rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0)
                self.rate.sleep()
        except KeyboardInterrupt:
            self.terminate()

if __name__ == "__main__":
    recorder = TopicRecorder()
    if recorder.recording_requested:
        recorder.run()
