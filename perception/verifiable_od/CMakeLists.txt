cmake_minimum_required(VERSION 3.8)
project(verifiable_od)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(vision_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(PCL REQUIRED)
find_package(OpenCV REQUIRED)

# Depth clustering library path
set(DC_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/src/lib/depth_clustering/install/amd64/depth_clustering/release/lib)

# Set RPATH so the executable can find the shared libraries at runtime
set(CMAKE_INSTALL_RPATH "${DC_LIB_DIR}")
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# Add executable
add_executable(verifiable_od_node src/verifiable_od_node.cpp)

# Link ROS 2 dependencies
ament_target_dependencies(verifiable_od_node
  rclcpp
  sensor_msgs
  std_msgs
  vision_msgs
  visualization_msgs
  pcl_conversions
)

# Include directories
target_include_directories(verifiable_od_node PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/src/lib/depth_clustering/src/depth_clustering
  ${PCL_INCLUDE_DIRS}
  ${OpenCV_INCLUDE_DIRS}
)

# Link depth_clustering libraries
target_link_libraries(verifiable_od_node
  ${DC_LIB_DIR}/libdc_api.so
  ${DC_LIB_DIR}/libdc_communication.so
  ${DC_LIB_DIR}/libdc_ground_removal.so
  ${DC_LIB_DIR}/libdc_image_labelers.so
  ${DC_LIB_DIR}/libdc_post_processing.so
  ${DC_LIB_DIR}/libdc_projections.so
  ${DC_LIB_DIR}/libdc_utils.so
  ${PCL_LIBRARIES}
  ${OpenCV_LIBS}
)

# Install executable
install(TARGETS verifiable_od_node
  DESTINATION lib/${PROJECT_NAME}
)

# Install config files
install(DIRECTORY src/cfg/
  DESTINATION share/${PROJECT_NAME}/cfg
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
