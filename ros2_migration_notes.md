## ROS 2 Migration Notes

### Project Structure Overview and Update Plan

#### `doc` (does not need to be updated)

#### `docker`
- [ ] `docker-compose.yml`
  - [x] `minihawk`
  - [x] `ground_station`
- [ ] `Dockerfile.roscore` - should be deleted when update completes

#### `env_sim/octomap_server`
- [x] **already updated** - please refer to: [`https://github.com/OctoMap/octomap_mapping`](https://github.com/OctoMap/octomap_mapping)

#### `env_sim/rraaa/script`
- [x] `script`
  - [x] `tools`
    - [x] `sensors.py`
    - [x] `input.py`
    - [x] `environment.py` - required to install `ros-<distro>-tf-transformations`
  - [x] `node_vehicle.py`
  - [x] `node_input_display.py`
  - [x] `node_carla.py`
  - [x] `node_3d_pathplanning.py`
  - [x] `node_2d_pathplanning.py`
  - [x] `debug_node_carla.py`
- [x] `src/convert.cpp`

#### `ground_station/script`
- [x] `node_target.py`
- [x] `CMakeLists.txt`
- [x] `Dockerfile`
- [x] `package.xml`

#### `media` (does not need to be updated)

#### `msg` (does not need to be updated)

#### `path_planner`
- [ ] `planner`
  - [x] `script/node_planner.py` - does not need to be updated
  - [ ] `CMakeLists.txt`
  - [ ] `Dockerfile`
  - [ ] `package.xml`
- [ ] `trajectory_planner/rrt_planner`
  - [x] `script/rrt_planner_node.py`
  - [ ] `CMakeLists.txt`
  - [ ] `Dockerfile`
  - [ ] `package.xml`

#### `perception`
- [ ] `mapper/script`
  - [ ] `carla_merged_lidar_publisher.py`
  - [ ] `CMakeLists.txt`
  - [ ] `Dockerfile`
  - [ ] `package.xml`
- [ ] `verifiable_od/src`
  - [x] `cfg` - does not need to be updated
  - [x] `lib` - does not need to be updated
  - [x] `verifiable_od_node.cpp`
  - [ ] `CMakeLists.txt`
  - [ ] `Dockerfile`
  - [ ] `package.xml`
- [ ] `yolov5`
  - [x] `script/node_yolo.py`
  - [ ] `CMakeLists.txt`
  - [ ] `Dockerfile`
  - [ ] `package.xml`

#### `sim_control`
- [x] `script`
  - [x] `node_control.py`
  - [x] `node_recorder.py`
  - [x] `node_sim_start.py`
- [ ] `CMakeLists.txt`
- [ ] `Dockerfile`
- [ ] `package.xml`


#### `tests` (does not need to be updated)

#### `utils` (some need to be updated)
- [x] `docker.py`
- [x] `min_safety_verifier.py`
- [x] `planner.py` (this requires an extensive update!)
- [ ] ~~`ros.py`~~ (deprecated)
- [x] `vehicle.py`

#### `vehicles/jaxguam`
- [x] `jax_guam`: all depends on `jax` library and does not require any modification.
- [x] `script`: requires update to ROS 2
  - [x] `guam_plot_batch_with_ref.py` - does need to be updated
  - [x] `landing_controller.py` - refactored using OOP design (recommended by ROS 2)
  - [x] `node_static_landing_planner.py`
  - [x] `node_vehicle.py`
- [ ] `CMakeLists.txt`
- [ ] `Dockerfile`
- [ ] `package.xml`

#### `vehicles/minihawk`
- [x] `script/node_vehicle.py`
- [x] `CMakeLists.txt`
- [x] `Dockerfile`
- [x] `package.xml`

#### Root Dir
- [x] `rraaa.py`


### Module Update
- [x] Ground Station
- [x] Octomap Server
- [ ] rraaa
- [ ] Planner (`path_planner/planner/`)
- [ ] RRT Planner (`path_planner/trajectory_planner/rrt_planner/`)
- [ ] Mapper
- [ ] Verifiable OD
- [ ] ~~yolov5~~ (broken submodule)
- [x] sim_control
- [ ] ~~jaxguam~~ (broken submodule)
- [x] Minihawk

### Module Update Test (Constructing Node)
- [x] Ground Station
- [x] Octomap Server
- [ ] rraaa
- [ ] Planner (`path_planner/planner/`)
- [ ] RRT Planner (`path_planner/trajectory_planner/rrt_planner/`)
- [ ] Mapper
- [ ] Verifiable OD
- [ ] ~~yolov5~~ (broken submodule)
- [x] sim_control
- [ ] ~~jaxguam~~ (broken submodule)
- [x] Minihawk
