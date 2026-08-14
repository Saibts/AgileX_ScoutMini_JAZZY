# AgileX Scout Mini 4WD Robot Simulation (ROS 2 Jazzy & Gazebo Harmonic)

Academic Project repository for the simulation, kinematics calibration, and teleoperation of the **AgileX Scout Mini** 4-wheel differential/skid-steer drive mobile robot under **ROS 2 Jazzy Jalisco** on Ubuntu 24.04 LTS with **Gazebo Harmonic (Gz Sim)** and **RViz2**.

📄 **[Read the Full Engineering & Problem-Solving Report (PROJECT_REPORT.md)](PROJECT_REPORT.md)**

---

## 📋 System Specifications & Requirements

- **Operating System:** Ubuntu 24.04 LTS (Noble Numbat)
- **ROS Distribution:** ROS 2 Jazzy Jalisco
- **Simulation Engine:** Gazebo Harmonic (`gz-sim8` via `ros_gz`)
- **Visualization:** RViz2
- **Robot Model:** AgileX Scout Mini 4-Wheel Skid-Steer / Differential Drive

---

## 🏗️ Repository Architecture

```text
agilex/
├── .gitignore                      # Excludes build/, install/, log/ to save disk space
├── README.md                       # Project documentation & quickstart guide
├── PROJECT_REPORT.md               # Exhaustive engineering & problem-solving report
├── launch/
│   └── simulation.launch.py        # Workspace launch link
└── src/
    └── assem2_robot/
        ├── CMakeLists.txt          # Package build configuration
        ├── package.xml             # ROS 2 Jazzy dependencies
        ├── config/
        │   ├── display.rviz        # Pre-configured RViz layout (RobotModel, TF, Odom, Grid)
        │   └── joint_names_Assem2.SLDASM.yaml
        ├── launch/
        │   ├── display.launch
        │   ├── gazebo.launch
        │   └── simulation.launch.py # Master launch file (Gazebo + RViz + Bridge + RSP)
        ├── meshes/                 # High-detail STL visual & collision meshes
        │   ├── base_link.STL
        │   ├── w1.STL (Front Right)
        │   ├── w2.STL (Front Left)
        │   ├── w3.STL (Rear Right)
        │   └── w4.STL (Rear Left)
        └── urdf/
            └── Assem2.SLDASM.urdf  # Calibrated URDF with Gazebo Harmonic plugins & dynamics
```

---

## ⚙️ Model Enhancements & Fixes (ROS 2 Jazzy & Gazebo Harmonic)

1. **4-Wheel Actuation & Dynamics:**
   - All 4 wheel joints (`j1`, `j2`, `j3`, `j4`) are explicitly configured as `continuous` joints with defined rotational axes (`xyz="1 0 0"`), physical damping (`damping="0.1"`), friction (`friction="0.1"`), and effort/velocity limits.
   - Fixed unactuated spinning wheel anomalies by integrating all 4 wheels into the `gz::sim::systems::DiffDrive` plugin.

2. **Ground Plane Calibration (`base_footprint`):**
   - Calibrated `base_footprint` $\rightarrow$ `base_link` transformation (`xyz="0.16662 0.10185 0.2269"`), placing all four tires flush with $Z = 0$ on top of the RViz grid plane.

3. **Gazebo Harmonic Differential Drive Plugin:**
   - **Left Wheels:** `j2` (Front-Left), `j4` (Rear-Left)
   - **Right Wheels:** `j1` (Front-Right), `j3` (Rear-Right)
   - **Track Width (Wheel Separation):** `0.39 m`
   - **Wheel Radius:** `0.08 m`
   - **Odometry & TF:** Publishes `/odom` and broadcasts `odom` $\rightarrow$ `base_footprint` $\rightarrow$ `base_link`.

4. **ROS-Gazebo Bridge Integration (`ros_gz_bridge`):**
   - `/cmd_vel` $\leftrightarrow$ `geometry_msgs/msg/Twist`
   - `/odom` $\rightarrow$ `nav_msgs/msg/Odometry`
   - `/tf` $\rightarrow$ `tf2_msgs/msg/TFMessage`
   - `/clock` $\rightarrow$ `rosgraph_msgs/msg/Clock`
   - `/joint_states` $\rightarrow$ `sensor_msgs/msg/JointState`

---

## 🚀 Quickstart & Usage

### 1. Build the Workspace
```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 2. Launch Simulation (Gazebo + RViz2 + Bridge)
```bash
cd ~/agilex
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py
```

### 3. Teleoperation (Drive the Robot)
```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Use the keyboard keys (`i`, `j`, `k`, `l`, `,`) to drive the robot around the world.

---

## 📑 Full Engineering Case Study
For deep-dive technical explanations of all bugs encountered (Humble to Jazzy migration, wheel spinning dynamics bug, KDL root inertia, Gazebo duplicate entity spawning, and RViz coordinate transformations), see **[PROJECT_REPORT.md](PROJECT_REPORT.md)**.
