import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'mapper'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='acrl-uiuc',
    maintainer_email='acrl-uiuc@todo.todo',
    description='Multi-LiDAR point cloud merger for CARLA simulation',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'carla_merged_lidar_publisher = mapper.carla_merged_lidar_publisher:main',
        ],
    },
)
