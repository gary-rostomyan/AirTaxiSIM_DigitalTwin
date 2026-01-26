from setuptools import find_packages, setup

package_name = 'jaxguam'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='JAX-based GUAM vehicle simulation node for ROS 2',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'node_vehicle = jaxguam.node_vehicle:main',
            'node_static_landing_planner = jaxguam.node_static_landing_planner:main',
            'landing_controller = jaxguam.landing_controller:main',
        ],
    },
)
