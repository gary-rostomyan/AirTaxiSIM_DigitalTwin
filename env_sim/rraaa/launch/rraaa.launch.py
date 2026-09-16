from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Declare launch arguments
    vehicle_arg = DeclareLaunchArgument(
        'vehicle',
        default_value='guam',
        description='Vehicle type to use'
    )
    plot_arg = DeclareLaunchArgument(
        'plot',
        default_value='false',
        description='Enable plotting'
    )
    save_video_arg = DeclareLaunchArgument(
        'save_video',
        default_value='false',
        description='Enable video saving'
    )

    return LaunchDescription([
        vehicle_arg,
        plot_arg,
        save_video_arg,

        # Carla Node - main environment simulation node
        Node(
            package='rraaa',
            executable='node_carla.py',
            name='carla_node',
            output='screen',
            parameters=[{
                'use_sim_time': True,
            }],
        ),

        # Input Display Node - handles user input and display
        Node(
            package='rraaa',
            executable='node_input_display.py',
            name='display_node',
            output='screen',
            prefix='python3',
            parameters=[{
                'use_sim_time': True,
            }],
        ),

        # Vehicle Node - handles vehicle dynamics based on vehicle type
        Node(
            package='rraaa',
            executable='node_vehicle.py',
            name=LaunchConfiguration('vehicle'),
            output='screen',
            parameters=[{
                'vehicle': LaunchConfiguration('vehicle'),
                'plot': LaunchConfiguration('plot'),
                'save_video': LaunchConfiguration('save_video'),
                'use_sim_time': True,
            }],
        ),

        # RViz2 - visualization
        ExecuteProcess(
            cmd=['rviz2', '-d', '/colcon_ws/rraaa/rviz_settings/octomap_navi.rviz'],
            output='screen',
            additional_env={'DISPLAY': ':0'},
        ),

        # Octomap Converter Node (C++)
        # Node(
        #     package='rraaa',
        #     executable='converter',
        #     name='converter_node',
        #     output='screen',
        # ),
    ])