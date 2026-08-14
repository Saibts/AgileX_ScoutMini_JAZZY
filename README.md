# AgileX Scout Mini 4WD Robot Simulation (ROS 2 Jazzy & Gazebo Harmonic)

Academic Project repository for the simulation, modeling, and teleoperation of the **AgileX Scout Mini** 4-wheel differential/skid-steer drive mobile robot under **ROS 2 Jazzy Jalisco** on Ubuntu 24.04 LTS with **Gazebo Harmonic (Gz Sim)** and **RViz2**.

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
├── README.md                       # Project documentation & usage guide
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

## ⚙️ Model Enhancements (ROS 2 Jazzy & Gazebo Harmonic)

1. **4-Wheel Actuation & Dynamics:**
   - All 4 wheel joints (`j1`, `j2`, `j3`, `j4`) are explicitly configured as `continuous` joints with defined rotational axes (`xyz="1 0 0"`), physical damping (`damping="0.1"`), friction (`friction="0.1"`), and effort/velocity limits.
   - Fixed unactuated spinning wheel anomalies by integrating all 4 wheels into the `gz::sim::systems::DiffDrive` plugin.

2. **Gazebo Harmonic Differential Drive Plugin:**
   - **Left Wheels:** `j2` (Front-Left), `j4` (Rear-Left)
   - **Right Wheels:** `j1` (Front-Right), `j3` (Rear-Right)
   - **Track Width (Wheel Separation):** `0.39 m`
   - **Wheel Radius:** `0.08 m`
   - **Odometry & TF:** Publishes `/odom` and broadcasts `odom` $\rightarrow$ `base_link` transforms.

3. **ROS-Gazebo Bridge Integration (`ros_gz_bridge`):**
   - `/cmd_vel` $\leftrightarrow$ `geometry_msgs/msg/Twist`
   - `/odom` $\rightarrow$ `nav_msgs/msg/Odometry`
   - `/tf` $\rightarrow$ `tf2_msgs/msg/TFMessage`
   - `/clock` $\rightarrow$ `rosgraph_msgs/msg/Clock`
   - `/joint_states` $\rightarrow$ `sensor_msgs/msg/JointState`

4. **Optimized Visualizations in RViz2:**
   - Fixed Frame set to `odom` for real-time trajectory tracking.
   - Synchronized `RobotModel`, `TF`, `Odometry` arrows, and `Grid`.

---

## 🚀 Quickstart & Usage

### 1. Build the Workspace
Open a terminal and build using symlink install (preserves disk space and accelerates development):

```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 2. Launch Simulation (Gazebo + RViz2 + Bridge)
Launch the unified simulation pipeline:

```bash
cd ~/agilex
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py
```

### 3. Teleoperation (Drive the Robot)
In a new terminal, run the teleop keyboard node:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Use the keyboard keys (`i`, `j`, `k`, `l`, `,`) to drive the robot around the world.

---

## 💾 Storage Management Tips

To maintain optimal system storage (~37 GB available on the primary partition):
- Use `colcon build --symlink-install` so mesh and configuration files are symlinked rather than duplicated in `install/`.
- Clean old build/log directories if needed:
  ```bash
  rm -rf ~/agilex/build ~/agilex/log
  ```

---

## 🔗 GitHub Synchronization

To maintain this repository on GitHub under [github.com/Saibts](https://github.com/Saibts):

```bash
cd ~/agilex
git init
git add .
git commit -m "feat: configure AgileX Scout Mini simulation for ROS 2 Jazzy and Gazebo Harmonic"
git branch -M main
git remote add origin https://github.com/Saibts/<your-repo-name>.git
git push -u origin main
```
