from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # Octomap Server Node
        Node(
            package='octomap_server',
            executable='octomap_server_node',
            name='octomap_server',
            parameters=[{
                'resolution': 0.5,
                'latch': False,
                'frame_id': 'map',
                'base_frame_id': 'map',
                'sensor_model.max_range': 50.0,
                'occupancy_min_z': 3.0,
                'occupancy_max_z': 200.0,
            }],
            remappings=[
                ('cloud_in', '/carla_node/lidar_point_cloud'),
            ],
        ),

        # Carla Multi-LiDAR Merger Node
        Node(
            package='mapper',
            executable='carla_merged_lidar_publisher',
            name='carla_merged_lidar_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': True,
            }],
        ),
    ])
