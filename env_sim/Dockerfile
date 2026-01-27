FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

ENV NVIDIA_VISIBLE_DEVICES ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics,compute,utility
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/local/bin:${PATH}"

# Install basic dependencies and OpenGL libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    software-properties-common \
    gnupg \
    lsb-release \
    wget \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libglx-mesa0 \
    libglu1-mesa \
    mesa-utils \
    libxrender1 \
    libxext6

# Add ROS2 Humble repository
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Install ROS2 Humble and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    build-essential \
    cmake \
    command-not-found \
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
    python3-tk \
    qtbase5-dev \
    ros-humble-desktop \
    ros-humble-octomap \
    ros-humble-octomap-msgs \
    ros-humble-octomap-server \
    ros-humble-cv-bridge \
    ros-humble-tf-transformations \
    ros-humble-sensor-msgs-py \
    ros-humble-rosbag2 \
    ros-humble-rosbag2-py \
    ros-humble-gazebo-msgs \
    python3-colcon-common-extensions \
    sudo \
    tar \
    tmux \
    vim \
    wget \
    xdg-user-dirs \
    xsel

# Install Python dependencies
# IMPORTANT: Pin numpy<2.0 to avoid compatibility issues with cv_bridge and transforms3d
RUN apt install -y python3-pip && \
    pip install \
        extensisq \
        opencv-python \
        pandas \
        pygame \
        scikit-spatial \
        scipy \
        setuptools \
        typing_extensions \
        torch \
        torchaudio \
        torchvision \
        transforms3d \
        loguru \
        ipdb && \
    pip install "numpy<2.0" --force-reinstall

# Install CARLA Python API from local wheel file
# Note: This wheel only works on linux/amd64. On other platforms (e.g., ARM), skip this step.
COPY carla-0.9.15-cp310-cp310-linux_x86_64.whl /tmp/
RUN pip install /tmp/carla-0.9.15-cp310-cp310-linux_x86_64.whl || \
    echo "WARNING: CARLA wheel installation failed (likely due to platform mismatch). Skipping..." && \
    rm -f /tmp/carla-0.9.15-cp310-cp310-linux_x86_64.whl

# Create colcon workspace
RUN mkdir -p /colcon_ws/src
WORKDIR /colcon_ws

# Install X11 and display dependencies
RUN apt-get update && apt-get install -y xvfb python3-pygame x11-xserver-utils

# Source ROS2 setup
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
