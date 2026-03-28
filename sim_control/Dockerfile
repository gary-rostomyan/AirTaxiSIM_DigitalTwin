FROM ros:humble

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update --fix-missing
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    ros-humble-geometry-msgs \
    ros-humble-sensor-msgs \
    ros-humble-std-msgs \
    ros-humble-rosbag2 \
    ros-humble-rosbag2-py

RUN pip install -U pip
RUN pip install loguru

RUN mkdir -p /colcon_ws/src
WORKDIR /colcon_ws

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
