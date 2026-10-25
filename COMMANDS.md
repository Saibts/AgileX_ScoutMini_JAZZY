# ⚡ AgileX Scout Mini AMR — Master Command Sheet

The single comprehensive, all-in-one command cheat sheet to build, simulate, teleoperate, map, and autonomously navigate the **AgileX Scout Mini 4WD Autonomous Mobile Robot (AMR)** in **ROS 2 Jazzy Jalisco** and **Gazebo Harmonic**.

---

## 📑 Quick Navigation
1. [Build & Environment Setup](#1-build--environment-setup)
2. [Civil Facility: Simulation & 2D SLAM Mapping](#2-civil-facility-simulation--2d-slam-mapping-recommended)
3. [Civil Facility: Autonomous Navigation](#3-civil-facility-point-and-click-autonomous-navigation)
4. [Obstacle Arena: Base Simulation & Teleoperation](#4-obstacle-arena-base-simulation--teleoperation)
5. [Obstacle Arena: 2D SLAM Mapping](#5-obstacle-arena-2d-slam-mapping--map-saving)
6. [Obstacle Arena: Nav2 Autonomous Navigation](#6-obstacle-arena-nav2-point-and-click-navigation)
7. [Obstacle Arena: Multi-Station Autonomous Patrol](#7-obstacle-arena-multi-station-autonomous-patrol)
8. [Master Teleoperation Keymap Cheat Sheet](#8-master-teleoperation-keymap-cheat-sheet)
9. [Live Sensor Topics, TF & Diagnostics](#9-live-sensor-topics-tf--diagnostics)
10. [Emergency Clean Stop & Cache Cleanup](#10-emergency-clean-stop--cache-cleanup)

---

## 1. Build & Environment Setup

Run once or whenever URDF, launch files, or configurations are updated:

```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

---

## 2. Civil Facility: Simulation & 2D SLAM Mapping (Recommended)

Spawns the Scout Mini in the multi-room NIST civil architectural benchmark ([`civil_world.sdf`](src/assem2_robot/worlds/civil_world.sdf)) with real-time Ceres scan-matching 2D SLAM.

#### Terminal 1 — Start Civil Simulation & 2D SLAM Mapping:
```bash
cd ~/agilex
./run_civil_mapping.sh
```

#### Terminal 2 — Run Smooth Keyboard Teleoperation:
```bash
cd ~/agilex
./run_teleop.sh
```

#### Terminal 3 — Save the Completed Civil Floor Map:
```bash
cd ~/agilex
./save_civil_map.sh
```
*(Saves high-res 2D occupancy grid to `src/assem2_robot/maps/civil_map.yaml` and `civil_map.pgm`).*

---

## 3. Civil Facility: Point-and-Click Autonomous Navigation

Launches Nav2 with costmap inflation, global path planning, and dynamic obstacle avoidance in the civil facility:

```bash
cd ~/agilex
./run_civil_nav.sh
```
* In the Ground Station GUI, click any station (**`S1`** to **`S7`**) or click **`Run Full Autonomous Patrol Loop`**.
* In RViz2, click **`2D Goal Pose`** (or **`Nav2 Goal`**) and drag anywhere on the floor plan to dispatch the robot.

### 3.1. Civil Facility: Automated Multi-Room Patrol & 1080p Video Recording

To automatically launch the entire suite, record a high-definition 1080p video demonstration of the robot autonomously visiting all 7 civil stations at full cruising speed (1.55 m/s), and save the MP4 video:

```bash
cd ~/agilex
./run_patrol_and_record.sh
```
*(Saves finalized video to `recordings/agilex_civil_patrol_demo.mp4`).*

To run just the autonomous patrol mission in an existing simulation terminal:
```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run assem2_robot civil_patrol_mission
```
*(Optionally specify `--loops 1` for a single complete lap).*

---

## 4. Obstacle Arena: Base Simulation & Teleoperation

Spawns the Scout Mini in the 10m × 10m obstacle arena with 2D LiDAR, 6-Axis IMU, RGB-D camera, and EKF state estimation.

#### Terminal 1 — Start Simulation:
```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py
```

#### Terminal 2 — Drive with Teleop:
```bash
cd ~/agilex
./run_teleop.sh
```

---

## 5. Obstacle Arena: 2D SLAM Mapping & Map Saving

#### Terminal 1 — Launch Arena SLAM:
```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py use_slam:=true
```

#### Terminal 2 — Teleoperate & Explore:
```bash
cd ~/agilex
./run_teleop.sh
```

#### Terminal 3 — Save Map:
```bash
source /opt/ros/jazzy/setup.bash
ros2 run nav2_map_server map_saver_cli -f ~/agilex/src/assem2_robot/maps/amr_world_map --ros-args -p use_sim_time:=true
```

---

## 6. Obstacle Arena: Nav2 Point-and-Click Navigation

```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py use_nav:=true
```
* Click **`2D Goal Pose`** on the RViz top toolbar and click-drag anywhere on the map floor.

---

## 7. Obstacle Arena: Multi-Station Autonomous Patrol

Executes continuous waypoint loops through 5 inspection stations without manual mouse clicks:

#### Terminal 1 — Start Nav2 Simulation:
```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py use_nav:=true
```

#### Terminal 2 — Start Patrol Mission Executor:
```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run assem2_robot patrol_mission
```
*(Waypoints: Charging Base `(0,0)` $\rightarrow$ Loading Zone `(1.5,1.5)` $\rightarrow$ Inspection Point `(-1.5,1.5)` $\rightarrow$ Unloading `(-1.5,-1.5)` $\rightarrow$ Checkpoint `(1.5,-1.5)`).*

---

## 8. Master Teleoperation Keymap Cheat Sheet

Runs via `./run_teleop.sh` with continuous velocity streaming and S-curve acceleration ramping:

| Key | Controls | Action |
| :---: | :--- | :--- |
| **`W`** / **`▲`** / **`i`** | Core Drive | **Drive Forward** linearly ($+X$) |
| **`S`** / **`▼`** / **`,`** | Core Drive | **Drive Reverse** linearly ($-X$) |
| **`A`** / **`◀`** / **`j`** | Core Steering | **Arc Left** (or Spin Left if stopped) |
| **`D`** / **`▶`** / **`l`** | Core Steering | **Arc Right** (or Spin Right if stopped) |
| **`Space`** / **`x`** / **`k`** | Safety | **Instant Emergency Brake** (Zero velocities) |
| **`Q`** / **`u`** | Dedicated Arc | **Arc Forward-Left** |
| **`E`** / **`o`** | Dedicated Arc | **Arc Forward-Right** |
| **`Z`** / **`m`** | Dedicated Arc | **Arc Reverse-Left** |
| **`C`** / **`.`** | Dedicated Arc | **Arc Reverse-Right** |
| **`+`** / **`=`** / **`]`** | Speed Tuning | Increase speed limits (+0.05 m/s, +0.10 rad/s) |
| **`-`** / **`_`** / **`[`** | Speed Tuning | Decrease speed limits (-0.05 m/s, -0.10 rad/s) |
| **`r`** | Speed Reset | Reset to SLAM defaults (0.35 m/s, 0.60 rad/s) |
| **`Tab`** / **`t`** | Mode Toggle | Switch between **Cruise Mode** (Default) & **Momentary Hold** |
| **`Ctrl+C`** | Exit | Safe shutdown with clean zero velocity broadcast |

---

## 9. Live Sensor Topics, TF & Diagnostics

```bash
# List all active ROS 2 topics
ros2 topic list

# Echo live odometry (fused wheel encoders + 6-Axis IMU)
ros2 topic echo /odometry/filtered

# Verify 2D LiDAR streaming rate (~20 Hz)
ros2 topic hz /scan

# Verify IMU streaming rate (~100 Hz)
ros2 topic hz /imu

# Verify coordinate transform trees
ros2 run tf2_ros tf2_echo map base_footprint
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_footprint lidar_link
```

---

## 10. Emergency Clean Stop & Cache Cleanup

Kills any background Gazebo, bridge, RViz, or EKF processes in one command:

```bash
killall -9 gz sim gz-sim-server gz_sim_server ruby parameter_bridge rviz2 robot_state_publisher ekf_node civil_interactive_nav async_slam_toolbox_node 2>/dev/null || true
```

Clean build & log caches:
```bash
cd ~/agilex
rm -rf build/ install/ log/ ~/.ros/log/
colcon build --symlink-install
source install/setup.bash
```
