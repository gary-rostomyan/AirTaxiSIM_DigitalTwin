#!/usr/bin/env python3
import argparse
import atexit
import traceback
import carla
import glob
import numpy as np
import os
import rclpy
from rclpy.parameter import Parameter
import signal
import sys
import time

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

try:
    import pygame
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_q
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

from rosgraph_msgs.msg import Clock  # FIX: sim clock publisher
from tools.environment import Environment
from loguru import logger as log
sys.path.append(os.path.abspath('/colcon_ws/src/utils'))
from utils.config import load_yaml_file
from utils import constants

FREQ_LOW_LEVEL = 10
dt = 1.0 / FREQ_LOW_LEVEL


class GracefulShutdown:
    def __init__(self, environment):
        self.environment = environment
        atexit.register(self.shutdown)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        self.shutdown()
        sys.exit(0)

    def shutdown(self):
        self.environment.destroy()
        log.info("Carla environment destroyed.")


def run_carla_node(args, client):
    pygame.init()
    config = load_yaml_file(constants.merged_config_path, __file__)

    rclpy.init(args=None)
    node = rclpy.create_node('carla_node')

    node.declare_parameter('tracking_control', False)
    node.declare_parameter('reset_called', False)
    node.declare_parameter('episode_done', False)
    node.declare_parameter('done_ack', False)
    node.declare_parameter('reset_ack', False)

    # FIX: publish CARLA simulation time on /clock so all nodes with
    # use_sim_time=True share a single consistent time source.
    clock_pub = node.create_publisher(Clock, '/clock', 10)

    environment = Environment(args, client, config, node)
    _ = GracefulShutdown(environment)

    while not getattr(environment, "ego_vehicle", None):
        print("Waiting for ego vehicle spawn...")
        time.sleep(0.1)

    node.set_parameters([Parameter('reset_called', Parameter.Type.BOOL, False)])
    node.set_parameters([Parameter('episode_done', Parameter.Type.BOOL, False)])
    node.set_parameters([Parameter('done_ack',     Parameter.Type.BOOL, False)])

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0)

            environment.client_clock.tick_busy_loop(FREQ_LOW_LEVEL)

            # Carla Tick — includes ROS message subscription and publishing.
            try:
                environment.tick()
            except IndexError as e:
                print("Environment not ready yet:", e)
                continue

            # Publish sim clock after world.tick() so all nodes with
            # use_sim_time=True share a consistent time source.
            snapshot = environment.world.get_snapshot()
            elapsed = snapshot.timestamp.elapsed_seconds
            clock_msg = Clock()
            clock_msg.clock.sec = int(elapsed)
            clock_msg.clock.nanosec = int((elapsed % 1) * 1e9)
            clock_pub.publish(clock_msg)

            # Use system time for pacing — node_carla.py does not depend on
            # /clock itself, so time.sleep() avoids any circular dependency.
            time.sleep(dt)

            ##########################
            ### Handle Reset Calls ###
            ##########################

            done_ack    = node.get_parameter('done_ack').value
            episode_done = node.get_parameter('episode_done').value
            if not done_ack and episode_done:
                environment.reset()
                node.set_parameters([Parameter('done_ack', Parameter.Type.BOOL, True)])
            elif done_ack and not episode_done:
                node.set_parameters([Parameter('done_ack', Parameter.Type.BOOL, False)])

            reset_called = node.get_parameter('reset_called').value
            if reset_called:
                print('HERE????')
                try:
                    environment.reset()
                except IndexError as e:
                    print("Reset skipped:", e)
                reset_called = False
                node.set_parameters([Parameter('reset_ack', Parameter.Type.BOOL, True)])
            else:
                node.set_parameters([Parameter('reset_ack', Parameter.Type.BOOL, False)])

    finally:
        environment.destroy()
        node.destroy_node()
        rclpy.shutdown()


def main():
    argparser = argparse.ArgumentParser(description='ROS CARLA NODE')
    argparser.add_argument('--host', metavar='H', default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument('-p', '--port', metavar='P', default=2000, type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument('--res', metavar='WIDTHxHEIGHT', default='800x400',
        help='window resolution (default: 800x400)')
    argparser.add_argument('--asynch', action='store_false',
        help='Activate asynchronous mode execution')
    argparser.add_argument('-n', '--number-of-vehicles', metavar='N', default=30, type=int,
        help='Number of vehicles (default: 30)')
    argparser.add_argument('-w', '--number-of-walkers', metavar='W', default=0, type=int,
        help='Number of walkers (default: 10)')
    argparser.add_argument('--safe', action='store_true',
        help='Avoid spawning vehicles prone to accidents')
    argparser.add_argument('--filterv', metavar='PATTERN', default='vehicle.*',
        help='Filter vehicle model (default: "vehicle.*")')
    argparser.add_argument('--generationv', metavar='G', default='All',
        help='restrict to certain vehicle generation (values: "1","2","All" - default: "All")')
    argparser.add_argument('--filterw', metavar='PATTERN', default='walker.pedestrian.*',
        help='Filter pedestrian type (default: "walker.pedestrian.*")')
    argparser.add_argument('--generationw', metavar='G', default='2',
        help='restrict to certain pedestrian generation (values: "1","2","All" - default: "2")')
    argparser.add_argument('--tm-port', metavar='P', default=8000, type=int,
        help='Port to communicate with TM (default: 8000)')
    argparser.add_argument('--hybrid', action='store_true',
        help='Activate hybrid mode for Traffic Manager')
    argparser.add_argument('-s', '--seed', metavar='S', type=int,
        help='Set random device seed and deterministic mode for Traffic Manager')
    argparser.add_argument('--seedw', metavar='S', default=0, type=int,
        help='Set the seed for pedestrians module')
    argparser.add_argument('--car-lights-on', action='store_true', default=False,
        help='Enable automatic car light management')
    argparser.add_argument('--hero', action='store_true', default=False,
        help='Set one of the vehicles as hero')
    argparser.add_argument('--respawn', action='store_true', default=False,
        help='Automatically respawn dormant vehicles (only in large maps)')
    argparser.add_argument('--no-rendering', action='store_true', default=False,
        help='Activate no rendering mode')

    args, unknown = argparser.parse_known_args()
    args.width, args.height = [int(x) for x in args.res.split('x')]
    args.asynch = False

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(10.0)
        run_carla_node(args, client)
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        raise