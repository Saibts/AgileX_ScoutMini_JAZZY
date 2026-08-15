# 📜 Complete Command Guide & Execution Manual: AgileX Scout Mini AMR

A comprehensive, step-by-step reference guide documenting every terminal command used to build, simulate, teleoperate, map, and autonomously navigate the **AgileX Scout Mini 4WD Autonomous Mobile Robot (AMR)** in **ROS 2 Jazzy Jalisco** and **Gazebo Harmonic**.

---

## 📑 Table of Contents
1. [Prerequisites & System Installation](#1-prerequisites--system-installation)
2. [Workspace Sourcing & Building](#2-workspace-sourcing--building)
3. [Mode 1: Basic Simulation & EKF Sensor Fusion](#3-mode-1-basic-simulation--ekf-sensor-fusion)
4. [Mode 2: Keyboard Teleoperation](#4-mode-2-keyboard-teleoperation)
5. [Mode 3: 2D SLAM Mapping & Map Saving](#5-mode-3-2d-slam-mapping--map-saving)
6. [Mode 4: Nav2 Point-and-Click Autonomous Navigation](#6-mode-4-nav2-point-and-click-autonomous-navigation)
7. [Mode 5: Fully Autonomous Multi-Station Patrol Mission](#7-mode-5-fully-autonomous-multi-station-patrol-mission)
8. [Live Sensor & Diagnostics Monitoring](#8-live-sensor--diagnostics-monitoring)
9. [Workspace Maintenance & Cache Cleaning](#9-workspace-maintenance--cache-cleaning)

---

## 1. Prerequisites & System Installation

Installs all required ROS 2 Jazzy simulation, control, localization, mapping, and navigation packages.

```bash
sudo apt update && sudo apt install -y \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-rviz2 \
  ros-jazzy-ros-gz \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-robot-localization \
  ros-jazzy-slam-toolbox \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup
```

### 🔍 What This Does:
* **`ros-jazzy-robot-state-publisher`**: Computes 3D forward kinematics and publishes the complete coordinate TF tree from URDF.
* **`ros-jazzy-rviz2`**: 3D graphical visualization tool for sensor data, costmaps, and robot transforms.
* **`ros-jazzy-ros-gz`**: Core integration bridge connecting ROS 2 with Gazebo Harmonic (`gz-sim8`).
* **`ros-jazzy-teleop-twist-keyboard`**: Converts keyboard keystrokes into velocity vectors (`geometry_msgs/msg/Twist`).
* **`ros-jazzy-robot-localization`**: Runs the Extended Kalman Filter (EKF) fusing wheel encoders and IMU.
* **`ros-jazzy-slam-toolbox`**: 2D Laser-based Simultaneous Localization and Mapping (SLAM).
* **`ros-jazzy-navigation2` & `nav2-bringup`**: Industrial-grade path planners (NavFn), local trajectory controllers (DWB), and costmaps.

---

## 2. Workspace Sourcing & Building

Navigates to the workspace directory, sources the base ROS 2 environment, and compiles the package.

```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 🔍 What This Does:
* **`cd ~/agilex`**: Changes current directory to the robot workspace root.
* **`source /opt/ros/jazzy/setup.bash`**: Sets up core ROS 2 environment variables (`ROS_DISTRO`, `PATH`, `PYTHONPATH`, `AMENT_PREFIX_PATH`).
* **`colcon build --symlink-install`**: Compiles all packages in `src/`. The `--symlink-install` flag creates symbolic links to Python scripts, launch files, and configs so modifications take effect immediately without needing full recompilation.
* **`source install/setup.bash`**: Overlays the workspace installation directory so ROS 2 CLI tools recognize `assem2_robot`.

---

## 3. Mode 1: Basic Simulation & EKF Sensor Fusion

Spawns the AgileX Scout Mini in the 10m × 10m obstacle arena with active 2D LiDAR, 6-axis IMU, RGB-D Camera, and EKF state estimation.

```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py
```

### 🔍 What This Does:
* Launches **Gazebo Harmonic** (`gz-sim8`) in auto-run mode (`-r`) loading [`amr_world.sdf`](src/assem2_robot/worlds/amr_world.sdf).
* Spawns a single instance of the Scout Mini model (`-allow_renaming false`) at origin `(0, 0, 0.02)`.
* Boots **`robot_state_publisher`** broadcasting the kinematic tree (`base_footprint` $\rightarrow$ `base_link` $\rightarrow$ wheels `j1`–`j4`, `lidar_link`, `imu_link`, `camera_link`).
* Starts **`ros_gz_bridge`** bridging actuation (`/cmd_vel`), odometry (`/odom`), clock (`/clock`), joint states (`/joint_states`), LiDAR (`/scan`), IMU (`/imu`), and RGB-D depth point clouds (`/camera/points`).
* Starts **`robot_localization` (`ekf_node`)** fusing wheel odometry and IMU angular velocity into `/odometry/filtered`.
* Opens **RViz2** pre-configured with RobotModel, LaserScan, TF, and PointCloud displays.

---

## 4. Mode 2: Keyboard Teleoperation

Controls the robot's 4-wheel skid-steer drive manually using the keyboard.

```bash
# Run in a separate terminal window:
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### 🕹️ Key Controls:
| Key | Motion | Explanation |
| :---: | :--- | :--- |
| **`i`** | Forward | Drives all 4 wheels forward linearly ($+X$) |
| **`,`** | Reverse | Drives all 4 wheels backward linearly ($-X$) |
| **`j`** | Turn Left | Skid-steers counter-clockwise in place ($+\omega_z$) |
| **`l`** | Turn Right | Skid-steers clockwise in place ($-\omega_z$) |
| **`u`** | Forward + Turn Left | Arc turn forward-left |
| **`o`** | Forward + Turn Right | Arc turn forward-right |
| **`m`** | Reverse + Turn Left | Arc turn backward-left |
| **`.`** | Reverse + Turn Right | Arc turn backward-right |
| **`k`** or **`Space`** | **Emergency Stop** | Commands zero linear and angular velocity |
| **`q`** / **`z`** | Adjust Speeds | Increases / decreases max speed limits by 10% |

---

## 5. Mode 3: 2D SLAM Mapping & Map Saving

Runs SLAM Toolbox to generate a high-resolution 2D occupancy grid map of the arena, and saves it to disk.

### Step 1: Launch Simulation with SLAM Enabled
```bash
# Terminal 1:
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py use_slam:=true
```

### Step 2: Drive Robot to Explore Arena
```bash
# Terminal 2:
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
*(Drive the robot around the perimeter and between pillars until walls and boundaries appear solid in RViz).*

### Step 3: Save the Completed Map
```bash
# Terminal 3:
source /opt/ros/jazzy/setup.bash
ros2 run nav2_map_server map_saver_cli -f ~/agilex/src/assem2_robot/maps/amr_world_map --ros-args -p use_sim_time:=true
```

### 🔍 What This Does:
* **`use_slam:=true`**: Automatically launches `slam_toolbox`'s `online_async_launch.py` with `autostart: true`.
* **`map_saver_cli`**: Captures the live `/map` topic and writes:
  * 📄 `amr_world_map.yaml`: Metadata (resolution: $0.05\text{ m/pixel}$, origin coordinates, thresholds).
  * 🗺️ `amr_world_map.pgm`: 2D grayscale occupancy grid bitmap image.
* **`--ros-args -p use_sim_time:=true`**: Synchronizes the map saver with Gazebo simulation clock.

---

## 6. Mode 4: Nav2 Point-and-Click Autonomous Navigation

Launches the complete Nav2 autonomous navigation stack with AMCL localization, global path planning, dynamic obstacle avoidance, and costmap inflation.

```bash
# Terminal 1:
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py use_nav:=true
```

### 🧭 How to Command in RViz2:
1. In the RViz top toolbar, click **`Nav2 Goal`** (or **`2D Goal Pose`**).
2. Click anywhere on the map floor and drag the green arrow to choose target heading.
3. The robot will automatically compute the global path (`NavFn`), inflate dynamic obstacles in its local costmap, and steer autonomously to the goal with `DWBLocalPlanner`.

---

## 7. Mode 5: Fully Autonomous Multi-Station Patrol Mission

Executes an automated warehouse/industrial patrol loop through 5 pre-defined operational stations without any manual mouse clicks.

### Step 1: Start Simulation with Nav2
```bash
# Terminal 1:
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py use_nav:=true
```

### Step 2: Launch Autonomous Patrol Mission Script
```bash
# Terminal 2:
cd ~/agilex
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run assem2_robot patrol_mission
```

### 📍 Autonomous Route Traversed:
1. 📍 **Station A (Docking / Charging Base):** $(0.0, 0.0)$ $\rightarrow$ pauses 2s
2. 📍 **Station B (Loading Zone):** $(1.5, 1.5)$ $\rightarrow$ pauses 3s (simulates cargo load)
3. 📍 **Station C (Inspection Point):** $(-1.5, 1.5)$ $\rightarrow$ pauses 2s
4. 📍 **Station D (Unloading Area):** $(-1.5, -1.5)$ $\rightarrow$ pauses 3s (simulates cargo unload)
5. 📍 **Station E (Perimeter Checkpoint):** $(1.5, -1.5)$ $\rightarrow$ pauses 2s
6. 🔄 **Repeats continuously in a loop!**

---

## 8. Live Sensor & Diagnostics Monitoring

Useful commands for inspecting live topics, coordinate transforms, and debugging sensor streams.

```bash
# 1. Echo Filtered Odometry (Fused Wheel Encoders + 6-Axis IMU)
ros2 topic echo /odometry/filtered

# 2. Echo Raw 2D LiDAR Range Scans (without large array spam)
ros2 topic echo /scan --no-arr

# 3. Echo Live Wheel Velocity Commands
ros2 topic echo /cmd_vel

# 4. Echo 6-Axis IMU Acceleration and Gyroscope Data
ros2 topic echo /imu

# 5. Verify Transform between Map and Robot Base
ros2 run tf2_ros tf2_echo map base_footprint

# 6. Verify Transform between Odom and Robot Base
ros2 run tf2_ros tf2_echo odom base_footprint

# 7. Check Real-Time Topic Publishing Frequencies (Hz)
ros2 topic hz /scan
ros2 topic hz /imu
ros2 topic hz /odometry/filtered

# 8. View Active Node Graph
rqt_graph
```

---

## 9. Workspace Maintenance & Cache Cleaning

Cleans temporary build artifacts, installation files, and log dumps if disk space gets low.

```bash
# Remove build, install, and log caches
cd ~/agilex
rm -rf build/ install/ log/ ~/.ros/log/

# Rebuild cleanly
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

---

*Repository maintained by: Sai ([@Saibts](https://github.com/Saibts))*  
*GitHub:* [https://github.com/Saibts/AgileX_ScoutMini_JAZZY](https://github.com/Saibts/AgileX_ScoutMini_JAZZY)
