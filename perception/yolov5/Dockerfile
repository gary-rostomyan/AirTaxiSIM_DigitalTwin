FROM ros:humble

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update --fix-missing
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    ros-humble-cv-bridge \
    ros-humble-sensor-msgs \
    ros-humble-std-msgs \
    ros-humble-geometry-msgs

RUN apt-get -y install libc-dev libx11-dev libgl1-mesa-glx libxrender1
RUN apt-get -y install build-essential

RUN pip install -U pip
RUN pip install "numpy<2" torch torchvision pillow matplotlib ultralytics filterpy pandas opencv-python

RUN mkdir -p /colcon_ws/src
WORKDIR /colcon_ws

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
