FROM ros:humble

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update --fix-missing
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    ros-humble-std-msgs

RUN pip install -U pip
RUN pip install loguru ipdb tqdm matplotlib

RUN mkdir -p /colcon_ws/src
WORKDIR /colcon_ws

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
