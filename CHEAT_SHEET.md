# ⚡ AgileX Scout Mini AMR — Fast Command Cheat Sheet

Quick-reference commands to build, simulate, teleoperate, and autonomously navigate the **AgileX Scout Mini 4WD Autonomous Mobile Robot (AMR)** in **ROS 2 Jazzy** & **Gazebo Harmonic**.

---

## 🛠️ 0. Build & Environment Setup

Run this whenever code or URDF configurations are updated:

```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

---

## 🎮 Mode 1: Base Simulation & Manual Teleoperation

Spawns the Scout Mini in the 10m × 10m obstacle arena with active 2D LiDAR, 6-Axis IMU, RGB-D Camera, and live EKF sensor fusion in RViz2.

### **Terminal 1: Master Simulation (Gazebo Harmonic + RViz2)**
```bash
cd ~/agilex
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py
```

### **Terminal 2: Keyboard Teleoperation**
```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### **🕹️ Key Controls:**
| Key | Action | Description |
| :---: | :--- | :--- |
| <kbd>i</kbd> | **Drive Forward** | Moves the robot straight toward the front bumper & camera |
| <kbd>,</kbd> | **Drive Reverse** | Moves the robot straight backward |
| <kbd>j</kbd> | **Turn Left** | Counter-clockwise skid-steer in-place rotation |
| <kbd>l</kbd> | **Turn Right** | Clockwise skid-steer in-place rotation |
| <kbd>u</kbd> / <kbd>o</kbd> | **Arc Turns** | Forward left / right curved driving |
| <kbd>k</kbd> | **Emergency Stop** | Zeroes all linear and angular velocities immediately |
| <kbd>w</kbd> / <kbd>x</kbd> | **Speed Adjust** | Increase / decrease linear speed by 10% |
| <kbd>e</kbd> / <kbd>c</kbd> | **Turn Adjust** | Increase / decrease angular speed by 10% |

---

## 🧭 Mode 2: Full Nav2 Autonomous Navigation (Click & Navigate in RViz)

Launches the complete ROS 2 Jazzy Nav2 stack (AMCL particle filter localization, 3D voxel costmaps, global A* planner, and dynamic local obstacle avoidance).

```bash
cd ~/agilex
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py use_nav:=true
```

> **📍 How to Navigate in RViz:**
> 1. Look at the top toolbar in the RViz2 window.
> 2. Click the **`2D Goal Pose`** tool (or press <kbd>G</kbd>).
> 3. Click anywhere in the free space on the map and drag the green arrow in the direction you want the robot to face upon arrival.
> 4. Nav2 will instantly compute an optimal global trajectory and the robot will drive autonomously to the goal while dodging obstacles!

---

## 🤖 Mode 3: Autonomous Multi-Station Waypoint Patrol Mission

Executes continuous, fully autonomous looping through 5 predefined factory inspection stations:
- **Station A:** Charging & Docking Base `(0.0, 0.0)`
- **Station B:** Material Loading Zone `(1.5, 1.5)`
- **Station C:** Automated Inspection Point `(-1.5, 1.5)`
- **Station D:** Unloading Area `(-1.5, -1.5)`
- **Station E:** Perimeter Checkpoint `(1.5, -1.5)`

### **Step 1:** Launch Nav2 Simulation (Terminal 1)
```bash
cd ~/agilex
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py use_nav:=true
```

### **Step 2:** Start Patrol Mission Executor (Terminal 2)
```bash
cd ~/agilex
source install/setup.bash
ros2 run assem2_robot patrol_mission
```

---

## 🗺️ Mode 4: 2D SLAM Mapping (Build Your Own Map)

Builds a real-time occupancy grid map using `slam_toolbox` as you drive around.

### **Terminal 1: Launch SLAM Simulation**
```bash
cd ~/agilex
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py use_slam:=true
```

### **Terminal 2: Teleoperate & Map the Arena**
```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### **Terminal 3: Save Map when Finished**
```bash
source /opt/ros/jazzy/setup.bash
ros2 run nav2_map_server map_saver_cli -f ~/agilex/src/assem2_robot/maps/amr_world_map
```

---

## 🔍 Diagnostics & Health Checks

```bash
# Check streaming topics
ros2 topic list

# Check sensor publishing rates
ros2 topic hz /scan
ros2 topic hz /imu
ros2 topic hz /camera/points
ros2 topic hz /odometry/filtered

# Verify TF tree frame transforms
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_footprint camera_link

# Clean lingering background simulation processes
killall -9 gz sim gz-sim-server gz_sim_server ruby parameter_bridge rviz2 robot_state_publisher ekf_node 2>/dev/null || true
```
