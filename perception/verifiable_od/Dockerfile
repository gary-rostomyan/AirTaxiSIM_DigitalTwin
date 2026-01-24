FROM ros:humble

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    tar \
    wget \
    git \
    freeglut3-dev \
    libqglviewer-dev-qt5 \
    qtbase5-dev \
    python3-pip \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Eigen
RUN apt-get update && apt-get install -y --no-install-recommends \
    libeigen3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Boost
RUN apt-get update && apt-get install -y --no-install-recommends \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

# Install ROS 2 packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-pcl-conversions \
    ros-humble-pcl-ros \
    ros-humble-vision-msgs \
    ros-humble-visualization-msgs \
    && rm -rf /var/lib/apt/lists/*

# OpenCV symlink
RUN ln -sf /usr/include/opencv4/opencv2 /usr/include/opencv2

# Setup ROS 2 environment
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
RUN mkdir -p /colcon_ws/src

WORKDIR /colcon_ws
