FROM ros:humble

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update --fix-missing
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    ros-humble-vision-msgs \
    ros-humble-sensor-msgs \
    ros-humble-cv-bridge

RUN apt-get -y install libc-dev libx11-dev libgl1-mesa-glx libxrender1
RUN apt-get -y install build-essential

RUN pip install -U pip
RUN pip install loguru
RUN pip uninstall numpy -y
RUN pip install numpy>=1.21 tqdm pyvista

RUN mkdir -p /colcon_ws/src
WORKDIR /colcon_ws

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc