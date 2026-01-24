import signal
import subprocess
import sys
import time
import threading
from loguru import logger as log

class DockerContainer:
    def __init__(self, service_name, compose_file, service_config):
        self.service_name = service_name
        self.compose_file = compose_file
        self.service_config = service_config
        self.processes = []

        try:
            self.start_delay = service_config['start_delay']
        except (KeyError, TypeError):
            self.start_delay = 0

        try:
            self.start_commands = str(service_config['start_commands'])
        except (KeyError, TypeError):
            self.start_commands = None

    def _run_compose_command(self, command, background = False):
        full_command = ['docker', 'compose', '-f', self.compose_file] + command
        try:
            if background:
                process = subprocess.Popen(full_command, stdout=sys.stdout, stderr=sys.stderr, text=True)
                self.processes.append(process)
            else:
                subprocess.run(full_command, check=True, text=True)
                log.info(f"Command {' '.join(full_command)} executed successfully.")
        except subprocess.CalledProcessError as e:
            log.error(f"Error executing command: {e}")

    def start_service(self):
        log.info(f"Starting service: {self.service_name}")
        self._run_compose_command(['up', '-d', self.service_name, '--remove-orphans'])
        if self.start_commands is not None:
            self.run_command_in_service(self.start_commands)
        time.sleep(int(self.start_delay))

    def stop_service(self):
        log.info(f"Stopping service: {self.service_name}")
        self._run_compose_command(['stop', self.service_name])

    def run_command_in_service(self, command, background = False):
        log.info(f"Running command in {self.service_name} container: {command}")
        return self._run_compose_command(['exec', self.service_name, '/bin/bash', '-c',  command], background)

    def wait_for_all(self):
        try:
            for process in self.processes:
                if process is not None:
                    process.wait()
        except KeyboardInterrupt:
            log.info("\nReceived interrupt. Terminating all processes.")
            self.terminate_all()

    def terminate_all(self):
        for process in self.processes:
            terminated = False
            if process is not None:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=5)
                    terminated = True
                except subprocess.TimeoutExpired:
                    process.terminate()

                if terminated:
                    log.trace(f"Terminated process using SIGINT PID: {process.pid}, Service: {self.service_name}")
                    continue

                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    log.warning(f"Force killed process PID: {process.pid}, Service: {self.service_name}")
                log.trace(f"Terminated process PID: {process.pid}, Service: {self.service_name}")


class ROSContainer(DockerContainer):
    def __init__(self, service_name, compose_file, service_config):
        super().__init__(service_name, compose_file, service_config)
        self.workspace_path = service_config['ros']['workspace']
        self.ros_package = service_config['ros']['ros_package']

        # ROS version: 1 for ROS 1 (noetic), 2 for ROS 2 (humble). Default to 1 for backward compatibility.
        try:
            self.ros_version = int(service_config['ros']['ros_version'])
        except KeyError:
            self.ros_version = 1

        try:
            self.launch_file = service_config['ros']['launch_file']
        except KeyError:
            self.launch_file = None

        try:
            self.rosrun_files = service_config['ros']['rosrun_files']
        except KeyError:
            self.rosrun_files = None

    def build_workspace(self):
        if self.ros_version == 2:
            ros_command = f"cd {self.workspace_path} && source /opt/ros/humble/setup.bash && colcon build --symlink-install"
        else:
            ros_command = f"cd {self.workspace_path} && source /opt/ros/noetic/setup.bash && catkin_make"
        log.info(f"Building {self.ros_package} (ROS {self.ros_version}) in service {self.service_name}")
        self.run_command_in_service(ros_command)

    def run_ros_command(self, command, background = False):
        if self.ros_version == 2:
            ros_command = f"cd {self.workspace_path} && source install/setup.bash && {command}"
        else:
            ros_command = f"cd {self.workspace_path} && source devel/setup.bash && {command}"
        log.info(f"Running ROS {self.ros_version} command in service {self.service_name}: {ros_command}")
        return self.run_command_in_service(ros_command, background)

    def roslaunch(self, target):
        if self.ros_version == 2:
            self.processes.append(self.run_ros_command(f"ros2 launch {self.ros_package} {target}", background=True))
        else:
            self.processes.append(self.run_ros_command(f"roslaunch {self.ros_package} {target}", background=True))

    def rosrun(self, target):
        if self.ros_version == 2:
            self.processes.append(self.run_ros_command(f"ros2 run {self.ros_package} {target}", background=True))
        else:
            self.processes.append(self.run_ros_command(f"rosrun {self.ros_package} {target}", background=True))

    def run_all(self):
        if self.launch_file:
            self.roslaunch(self.launch_file)

            # Delay helps avoid ROS Master conflicts (ROS 1) or aids DDS discovery (ROS 2).
            time.sleep(1)
        elif self.rosrun_files:
            for script in self.rosrun_files:
                self.rosrun(script)
        else:
            log.error(f"No files to launch or run in {self.service_name}")

    # def start_service(self):
    #     super().start_service()
    #     self.build_workspace()
    #     self.launch_file()


class ContainerManager:
    def __init__(self, config, compose_file):
        self.config = config['services']
        self.compose_file = compose_file
        self.containers = []
        self._load_containers()
        for service in self.config:
            service_config = self.config[service]
            try:
                for command in service_config['host_setup']:
                    self.run_command_on_host(command.split(' '))
            except KeyError:
                pass

    def _load_containers(self):
        for service_name, service_config in self.config.items():
            if 'ros' in service_config:
                ros_container = ROSContainer(service_name=service_name,
                                             compose_file=self.compose_file,
                                             service_config=service_config)
                log.info(f"Loaded ROS container for service: {service_name}")
                self.containers.append(ros_container)
            else:
                docker_container = DockerContainer(service_name=service_name,
                                                   compose_file=self.compose_file, service_config=service_config)
                log.info(f"Loaded Docker container for service: {service_name}")
                self.containers.append(docker_container)

    def start_all(self):
        log.info("Starting all containers.")
        for container in self.containers:
            container.start_service()

    def stop_all(self):
        log.info("Stopping all containers.")
        for container in self.containers:
            if isinstance(container, ROSContainer):
                container.terminate_all()
            container.stop_service()

        # After the elegant stop above, bture force stop all running services,
        stop_command = ['docker', 'compose', '-f', self.compose_file, 'stop']
        subprocess.run(stop_command, check=True, text=True)

    def build_all_workspaces(self):
        log.info("Building all ROS workspaces.")
        for container in self.containers:
            if isinstance(container, ROSContainer):
                container.build_workspace()

    def run_all(self):
        log.info("Launching ROS launch files in all ROS containers.")
        for container in self.containers:
            if isinstance(container, ROSContainer):
                container.run_all()

    def reset_all(self):
        log.info("Restarting all ROS containers.")
        for container in self.containers:
            if isinstance(container, ROSContainer):
                container.terminate_all()
            else:
                container.stop_service()
                container.start_service()
        self.run_all()

    def wait_for_all(self):
        for container in self.containers:
            container.wait_for_all()

    def terminate_all(self):
        log.info("Terminating running processes in all containers.")
        for container in self.containers:
            container.terminate_all()

    def run_command_on_host(self, command):
        try:
            subprocess.run(command, check=True, text=True)
            log.info(f"Command {' '.join(command)} executed successfully.")
        except subprocess.CalledProcessError as e:
            log.error(f"Error executing command: {e}")