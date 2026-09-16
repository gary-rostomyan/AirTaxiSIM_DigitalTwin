# FROM nvidia/cuda:11.8.0-devel-ubuntu20.04

# ENV NVIDIA_VISIBLE_DEVICES ${NVIDIA_VISIBLE_DEVICES:-all}
# ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics,compute,utility
# ENV DEBIAN_FRONTEND=noninteractive
# ENV PATH="/usr/local/bin:${PATH}"

# # Install basic dependencies and OpenGL libraries
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     curl \
#     software-properties-common \
#     gnupg \/
#     lsb-release \
#     wget \
#     libgl1-mesa-glx \
#     libgl1-mesa-dri \
#     libglu1-mesa \
#     mesa-utils \
#     libxrender1 \
#     libxext6

# # Add ROS2 Foxy repository (Ubuntu 20.04)
# RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg && \
#     echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null

# # Install ROS2 Foxy and dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     bash-completion \
#     build-essential \
#     cmake \
#     freeglut3-dev \
#     g++ \
#     git \
#     less \
#     libboost-all-dev \
#     libeigen3-dev \
#     libomp-dev \
#     libopencv-dev \
#     libqglviewer-dev-qt5 \
#     libtbb-dev \
#     make \
#     pcl-tools \
#     protobuf-compiler \
#     python3-tk \
#     qtbase5-dev \
#     ros-foxy-desktop \
#     ros-foxy-octomap \
#     ros-foxy-octomap-msgs \
#     ros-foxy-cv-bridge \
#     ros-foxy-rosbag2 \
#     ros-foxy-gazebo-msgs \
#     ros-foxy-sensor-msgs-py \
#     python3-colcon-common-extensions \
#     sudo \
#     tar \
#     tmux \
#     vim \
#     wget \
#     xdg-user-dirs \
#     xsel

# # Install Foxy packages that may need special handling
# # octomap-server and rosbag2-py: try to install, skip if unavailable
# RUN apt-get install -y ros-foxy-octomap-server || \
#     echo "WARNING: ros-foxy-octomap-server not available, may need to build from source"
# RUN apt-get install -y ros-foxy-rosbag2-py || \
#     echo "WARNING: ros-foxy-rosbag2-py not available"

# # Install Python dependencies
# RUN apt-get install -y python3-pip && \
#     pip3 install \
#         catkin_pkg \
#         empy \
#         lark \
#         "extensisq<=0.4.0" \
#         "matplotlib<=3.7.5" \
#         "opencv-python<=4.9.0.80" \
#         "pandas<=2.0.3" \
#         pygame \
#         scikit-spatial \
#         "scipy<=1.10.1" \
#         setuptools \
#         typing_extensions \
#         "torch<=2.0.1" \
#         "torchaudio<=2.0.2" \
#         "torchvision<=0.15.2" \
#         transforms3d \
#         loguru \
#         ipdb && \
#     pip3 install "numpy<2.0" --force-reinstall

# # Install CARLA Python API from local wheel file (cp38 version matching server 0.9.15-273-gc7339367b)
# # Note: This wheel only works on linux/amd64. On other platforms (e.g., ARM), skip this step.
# COPY carla-0.9.15-cp310-cp310-linux_x86_64.whl /tmp/
# RUN pip3 install /tmp/carla-0.9.15-cp310-cp310-linux_x86_64.whl

# # Create colcon workspace
# RUN mkdir -p /colcon_ws/src
# WORKDIR /colcon_ws

# # Install X11 and display dependencies
# RUN apt-get update && apt-get install -y xvfb python3-pygame x11-xserver-utils

# # Source ROS2 Foxy setup
# RUN echo "source /opt/ros/foxy/setup.bash" >> ~/.bashrc
FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

ENV NVIDIA_VISIBLE_DEVICES=${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES=${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics,compute,utility
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/local/bin:${PATH}"
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV ROS_DISTRO=humble

SHELL ["/bin/bash", "-lc"]

# Basic system deps + locale + Universe repo
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    curl \
    software-properties-common \
    gnupg \
    lsb-release \
    wget \
    ca-certificates \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libglu1-mesa \
    mesa-utils \
    libxrender1 \
    libxext6 \
    && locale-gen en_US en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && add-apt-repository -y universe \
    && rm -rf /var/lib/apt/lists/*

# ROS 2 apt source (current recommended setup)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}') \
    && curl -L -o /tmp/ros2-apt-source.deb \
       "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb" \
    && dpkg -i /tmp/ros2-apt-source.deb \
    && rm -f /tmp/ros2-apt-source.deb

# ROS 2 Humble + build/runtime deps
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
    ros-humble-cv-bridge \
    ros-humble-rosbag2 \
    ros-humble-gazebo-msgs \
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

# Optional Humble packages: keep best-effort behavior
RUN apt-get update && apt-get install -y --no-install-recommends ros-humble-octomap-server || \
    echo "WARNING: ros-humble-octomap-server not available, may need to build from source"

RUN apt-get update && apt-get install -y --no-install-recommends ros-humble-rosbag2-py || \
    echo "WARNING: ros-humble-rosbag2-py not available"

# Python deps (now on Ubuntu 22.04 / Python 3.10)
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir \
        catkin_pkg \
        empy \
        lark \
        "extensisq<=0.4.0" \
        "matplotlib<=3.7.5" \
        "opencv-python<=4.9.0.80" \
        "pandas<=2.0.3" \
        pygame \
        scikit-spatial \
        "scipy<=1.10.1" \
        typing_extensions \
        "torch<=2.0.1" \
        "torchaudio<=2.0.2" \
        "torchvision<=0.15.2" \
        transforms3d \
        loguru \
        ipdb && \
    python3 -m pip install --no-cache-dir --force-reinstall "numpy==1.23.5"

# CARLA Python API wheel for cp310
COPY carla-0.9.15-cp310-cp310-linux_x86_64.whl /tmp/carla-0.9.15-cp310-cp310-linux_x86_64.whl
RUN python3 -m pip install --no-cache-dir /tmp/carla-0.9.15-cp310-cp310-linux_x86_64.whl && \
    rm -f /tmp/carla-0.9.15-cp310-cp310-linux_x86_64.whl

# Create colcon workspace
RUN mkdir -p /colcon_ws/src
WORKDIR /colcon_ws

# Source ROS 2 Humble
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc