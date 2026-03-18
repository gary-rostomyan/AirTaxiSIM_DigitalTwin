FROM ros:humble

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update --fix-missing
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     python3-pip \
#     python3-colcon-common-extensions \
#     ros-humble-std-msgs \
#     ros-humble-sensor-msgs \
#     ros-humble-sensor-msgs-py \
#     ros-humble-octomap \
#     ros-humble-octomap-msgs \
#     ros-humble-octomap-server

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    build-essential \
    cmake \
    freeglut3-dev \
    g++ \
    git \
    less \
    libboost-all-dev \
    libeigen3-dev \
    libomp-dev \
    libopencv-dev \
    libqglviewer-dev-qt5 \
    libtbb-dev \
    make \
    pcl-tools \
    protobuf-compiler \
    python3 \
    python3-dev \
    python3-pip \
    python3-tk \
    qtbase5-dev \
    ros-humble-desktop \
    ros-humble-octomap \
    ros-humble-octomap-msgs \
    ros-humble-octomap-server \
    ros-humble-cv-bridge \
    ros-humble-rosbag2 \
    ros-humble-gazebo-msgs \
    ros-humble-std-msgs \
    ros-humble-sensor-msgs-py \
    ros-humble-tf-transformations \
    python3-colcon-common-extensions \
    sudo \
    tar \
    tmux \
    vim \
    xdg-user-dirs \
    xsel \
    xvfb \
    python3-pygame \
    x11-xserver-utils \
    && rm -rf /var/lib/apt/lists/*

# RUN apt-get -y install -y --no-install-recommends libc-dev libx11-dev libgl1-mesa-glx libxrender1
# RUN apt-get -y install build-essential
# RUN pip install -U pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    libc6-dev \
    libx11-dev \
    libgl1-mesa-glx \
    libxrender1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir -U pip
# RUN pip install numpy


RUN python3 -m pip install --no-cache-dir --force-reinstall "numpy==1.23.5"

RUN mkdir -p /colcon_ws/src
WORKDIR /colcon_ws

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc