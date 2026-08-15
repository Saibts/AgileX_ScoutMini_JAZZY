# Project Context & Memory: AgileX Scout Mini AMR Project

Whenever the user says **"lets work in my AMR project"**, **"AMR project"**, **"agilex"**, or references their mobile robot simulation, immediately assume the full context of this project.

---

## 📌 Project Overview & Linked History
- **Project Name:** AgileX Scout Mini 4WD Autonomous Mobile Robot (AMR)
- **Primary Conversations:**
  - [**Initial Setup & Debugging Session**](conversation://16fd25ad-0e67-4021-be74-32b15d69c493) (ID: `16fd25ad-0e67-4021-be74-32b15d69c493`)
  - [**Continuation & Repository Deployment Session**](conversation://5f7e7fd4-6a62-4b63-b5e3-310d3792c2f6) (ID: `5f7e7fd4-6a62-4b63-b5e3-310d3792c2f6`)
- **GitHub Repository:** [https://github.com/Saibts/AgileX_ScoutMini_JAZZY](https://github.com/Saibts/AgileX_ScoutMini_JAZZY)
- **Local Workspace Root:** `/home/sailakshmi/agilex`
- **Main Package:** `/home/sailakshmi/agilex/src/assem2_robot`

---

## 💻 Tech Stack & System Specifications
- **Operating System:** Ubuntu 24.04 LTS (Noble Numbat)
- **ROS Version:** ROS 2 Jazzy Jalisco (`/opt/ros/jazzy`)
- **Simulator:** Gazebo Harmonic (`gz-sim8` via `ros_gz_bridge`)
- **Visualization:** RViz2
- **Disk Storage Reminder:** Keep build logs clean (`rm -rf ~/agilex/build/ ~/agilex/install/ ~/agilex/log/ ~/.ros/log/`) if disk fills up.

---

## 🚀 Key Commands

### 1. Build Workspace
```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 2. Launch Simulation (Gazebo + RViz2)
```bash
source install/setup.bash
ros2 launch assem2_robot simulation.launch.py
```

### 3. Keyboard Teleop
```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

---

## ⚙️ Core Architecture & Calibrated Settings
1. **URDF File:** `/home/sailakshmi/agilex/src/assem2_robot/urdf/Assem2.SLDASM.urdf`
   - `base_footprint` $\rightarrow$ `base_link` calibrated transform aligning CAD coordinates with ROS REP-103 standard: `xyz="0.10185 -0.16662 0.2269" rpy="0 0 -1.5707963"`.
   - Wheel joints calibrated: right wheels `j1`, `j2` (`axis xyz="-1 0 0"`) and left wheels `j3`, `j4` (`axis xyz="1 0 0"`).
   - Lateral friction `mu2="0.1"` for smooth skid steering without wheel fight.
   - `gz::sim::systems::DiffDrive` plugin actuates left wheels (`j3`, `j4`) and right wheels (`j1`, `j2`) with track width `0.612 m` and wheel radius `0.08 m`.
2. **Launch File:** `/home/sailakshmi/agilex/src/assem2_robot/launch/simulation.launch.py`
   - Automatically starts `robot_state_publisher`, `ros_gz_sim` (Gazebo Harmonic), `ros_gz_bridge` (for `/cmd_vel`, `/odom`, `/tf`, `/clock`, `/joint_states`), and `rviz2`.
3. **Documentation:** `/home/sailakshmi/agilex/PROJECT_REPORT.md` and `/home/sailakshmi/agilex/README.md`.
