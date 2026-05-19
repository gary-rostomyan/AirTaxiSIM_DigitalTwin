import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import Twist

from loguru import logger
from rclpy.parameter import Parameter

class Vehicle_Node(Node):
    def __init__(self, config) -> None:

        self.config = config

        # Record the vehicle type
        self.vehicle_type = config['ego_vehicle']['type']

        # Initialize the ROS2 Node
        # super().__init__(self.vehicle_type)
        super().__init__(
            self.vehicle_type,
            parameter_overrides=[
                Parameter('use_sim_time', Parameter.Type.BOOL, True)
            ]
        )
        
        logger.info(f"Constructing a {self.vehicle_type} node...")

        # Initial position and velocity
        self.initial_position = [float(config['ego_vehicle']['location']['x']),
                                 float(config['ego_vehicle']['location']['y']),
                                 float(config['ego_vehicle']['location']['z'])]
        self.initial_velocity = [float(config['ego_vehicle']['velocity']['x']), 
                                 float(config['ego_vehicle']['velocity']['y']),
                                 float(config['ego_vehicle']['velocity']['z'])]

        # Register publishers
        self.vehicle_pose_pub = self.create_publisher(PoseStamped, f'/{self.vehicle_type}/pose', 1)
        self.vehicle_pose_msg = PoseStamped()
        self.vehicle_vel_pub = self.create_publisher(Twist, f'/{self.vehicle_type}/velocity', 1)
        self.vehicle_vel_msg = Twist()

    def main(self):
        raise NotImplementedError