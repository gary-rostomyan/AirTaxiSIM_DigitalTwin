
FROM ros:humble
ENV NVIDIA_VISIBLE_DEVICES ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics,compute,utility
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/local/bin:${PATH}"
RUN apt-get update && apt-get install -y \
    software-properties-common \
    build-essential \
    curl \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN pip install -U pip
RUN pip install --upgrade --force-reinstall attrs
RUN pip install \
    numpy \
    pandas \
    scipy \
    matplotlib \
    jaxtyping \
    attrs \
    loguru \
    tqdm \
    ipdb \
    extensisq \
    typing_extensions
# Install JAX nightly with CUDA 12 support (required for Blackwell SM_120 / RTX 5070 Ti)
RUN pip install -U --pre jax[cuda12] \
    -f https://storage.googleapis.com/jax-releases/jax_nightly_releases.html
# Copy and install jax_guam package
COPY jax_guam /jax_guam
WORKDIR /jax_guam
RUN pip install -e .
# Set up ROS 2 environment
ENV ROS_DISTRO=humble
SHELL ["/bin/bash", "-c"]
# Create ROS 2 workspace
RUN mkdir -p /colcon_ws/src
# Copy the ROS 2 package
COPY . /colcon_ws/src/jaxguam
WORKDIR /colcon_ws
# Build the ROS 2 package
RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    colcon build --packages-select jaxguam
# Source the workspace on container start
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc
RUN echo "source /colcon_ws/install/setup.bash" >> /root/.bashrc