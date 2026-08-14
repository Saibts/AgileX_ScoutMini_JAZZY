# 📋 Comprehensive Engineering & Problem-Solving Report: AgileX Scout Mini AMR Simulation

**Project:** AgileX Scout Mini Autonomous Mobile Robot (AMR) Simulation, Kinematics Calibration & Teleoperation  
**Author:** Sai ([@Saibts](https://github.com/Saibts))  
**Platform:** AgileX Scout Mini 4-Wheel Differential / Skid-Steer Mobile Robot  
**Environment:** Ubuntu 24.04 LTS (Noble Numbat) | ROS 2 Jazzy Jalisco | Gazebo Harmonic (Gz Sim 8.14) | RViz2  
**Repository:** [https://github.com/Saibts/ROS_AMR](https://github.com/Saibts/ROS_AMR)  

---

## 📖 Executive Summary

During the development, modeling, and simulation of the **AgileX Scout Mini** differential/skid-steer mobile robot, numerous complex technical hurdles were encountered across robot kinematics modeling, physics simulation engines, coordinate transformations, inter-process communication bridges, and version control. 

This document serves as an exhaustive technical case study detailing every issue encountered throughout the project lifecycle (including all phases documented in development chats), the diagnostic root cause analysis, and the finalized engineering solutions implemented to achieve a 100% functional, stable simulation in ROS 2 Jazzy.

---

## 🛠️ Complete Problem-Solving Case Studies

### 1. Distro & Simulator Migration: ROS 2 Humble to ROS 2 Jazzy

#### 🚨 The Problem
Initial project workflows and community tutorials were designed for ROS 2 Humble using Gazebo Classic (`gazebo11` / `gazebo_ros_pkgs`). In Ubuntu 24.04 LTS running ROS 2 Jazzy Jalisco, Gazebo Classic is deprecated and superseded by **Gazebo Harmonic (Gz Sim 8)**. Launch files and URDF plugins from Humble failed to build or execute.

#### 🔍 Root Cause
1. Gazebo Classic plugin tags (`<plugin filename="libgazebo_ros_diff_drive.so">`) are incompatible with Gazebo Harmonic's entity-component-system (ECS) architecture.
2. ROS 2 Jazzy communicates with Gazebo Harmonic via Ignition/Gazebo Transport Protobuf messages (`gz.msgs`), requiring an active middleware bridge (`ros_gz_bridge`).

#### ✅ The Solution
1. Upgraded all simulation dependencies to `ros_gz_sim` and `ros_gz_bridge`.
2. Refactored the URDF plugin configuration to use Gazebo Harmonic's native system plugin:
   ```xml
   <plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive">
   ```
3. Implemented a bidirectional `ros_gz_bridge parameter_bridge` in the launch file to bridge:
   * `/cmd_vel` (`geometry_msgs/msg/Twist` $\leftrightarrow$ `gz.msgs.Twist`)
   * `/odom` (`nav_msgs/msg/Odometry` $\leftarrow$ `gz.msgs.Odometry`)
   * `/tf` (`tf2_msgs/msg/TFMessage` $\leftarrow$ `gz.msgs.Pose_V`)
   * `/clock` (`rosgraph_msgs/msg/Clock` $\leftarrow$ `gz.msgs.Clock`)
   * `/joint_states` (`sensor_msgs/msg/JointState` $\leftarrow$ `gz.msgs.Model`)

---

### 2. Network Multicast Errors & Missing `odom` Frame in RViz

#### 🚨 The Problem
Early testing produced `"Network is unreachable"` multicast errors, and RViz2 displayed `"Global Status: Error"` with a missing `odom` frame, preventing visual tracking of robot motion.

#### 🔍 Root Cause
1. Default ROS 2 DDS discovery attempted to broadcast over non-loopback network interfaces when offline.
2. Odometry was not bridged from the simulation engine to ROS 2 topics.

#### ✅ The Solution
1. Configured local DDS communication:
   ```bash
   export ROS_LOCALHOST_ONLY=1
   ```
2. Bridged Gazebo's odometry topic (`/odom`) and transform broadcast (`/tf`) to ROS 2 via `ros_gz_bridge`.
3. Set RViz Fixed Frame to `odom`, restoring real-time pose and trajectory visualization.

---

### 3. Wheel 3 (`j3`) Infinite Spinning & Unactuated Dynamics Bug

#### 🚨 The Problem
When the robot was spawned in Gazebo at rest (`cmd_vel = 0`), the 3rd wheel (`j3` / Rear-Right) spun continuously and violently without stopping, causing erratic jitter and simulation instability.

```
       [Front]
   (j2) ┌────┐ (j1)
        │    │
   (j4) └────┘ (j3) ──> Infinite Spinning Bug!
       [Rear]
```

#### 🔍 Root Cause
1. **Missing Joint Axis & Dynamics in SolidWorks Export:** The SolidWorks-to-URDF exporter omitted the `<axis>` tag for `j3` and left damping and friction at `0.0`.
2. **Unactuated Wheel Exclusion in Drive Plugin:** The DiffDrive plugin was only driving 2 wheels (`j1` and `j2`). Wheels `j3` and `j4` were treated as passive, unactuated continuous joints. Micro-collisions with the ground plane excited numerical instability in ODE/DART physics, making `j3` spin indefinitely.

#### ✅ The Solution
1. Injected explicit rotational axes and mechanical damping/friction into all 4 wheel joint definitions:
   ```xml
   <joint name="j3" type="continuous">
     <origin xyz="-0.47262 -0.29727 -0.14629" rpy="-2.87166 0 3.14159" />
     <parent link="base_link" />
     <child link="w3" />
     <axis xyz="1 0 0" />
     <dynamics damping="0.1" friction="0.1" />
     <limit effort="100" velocity="100" />
   </joint>
   ```
2. Configured both rear wheels (`j3`, `j4`) alongside front wheels (`j1`, `j2`) inside the DiffDrive plugin so the controller applies active braking torque when velocity is zero:
   ```xml
   <left_joint>j2</left_joint>
   <left_joint>j4</left_joint>
   <right_joint>j1</right_joint>
   <right_joint>j3</right_joint>
   ```
3. Added surface friction parameters (`mu1=1.0`, `mu2=1.0`, `kp=1e6`, `kd=100.0`, `minDepth=0.001`) to all wheel links (`w1`, `w2`, `w3`, `w4`).

---

### 4. Coordinate Frame Misalignment & Sunken Grid in RViz

#### 🚨 The Problem
In RViz2, the robot appeared sunken 23 cm below the grid plane ($Z < 0$), with the chassis slicing through the ground and rotating eccentrically rather than around its geometric center.

#### 🔍 Root Cause
SolidWorks CAD assemblies export link origins relative to the CAD coordinate system origin, which was situated at the upper chassis rather than the wheel contact patch:
* **Vertical Ground Offset:** Wheel axle $z_{\text{axle}} = -0.1469\text{ m}$ + wheel radius $r = 0.08\text{ m} \rightarrow z_{\text{ground}} = -0.2269\text{ m}$.
* **Longitudinal Offset:** Center of front axle ($+0.1394\text{ m}$) and rear axle ($-0.4726\text{ m}$) is $x_{\text{center}} = -0.1666\text{ m}$.
* **Lateral Offset:** Center of left wheels ($+0.0936\text{ m}$) and right wheels ($-0.2973\text{ m}$) is $y_{\text{center}} = -0.1018\text{ m}$.

Because `base_footprint_joint` previously had `<origin xyz="0 0 0"/>`, `base_link` sat directly on the ground plane, submerging the wheels.

#### ✅ The Solution
1. Introduced a standard ROS (REP-120) root `base_footprint` link representing the robot's ground projection plane ($Z = 0$).
2. Applied an exact calibrated transform from `base_footprint` to `base_link`:
   $$\mathbf{T}_{\text{footprint}\rightarrow\text{link}} = \begin{bmatrix} +0.16662 \\ +0.10185 \\ +0.22690 \end{bmatrix}$$
   ```xml
   <link name="base_footprint" />

   <joint name="base_footprint_joint" type="fixed">
     <parent link="base_footprint" />
     <child link="base_link" />
     <origin xyz="0.16662 0.10185 0.2269" rpy="0 0 0" />
   </joint>
   ```
3. **Outcome:** In RViz and Gazebo, all four tires rest flush on $Z = 0$ on top of the grid plane, and steering rotations pivot symmetrically about $(0,0)$.

---

### 5. KDL Parser Root Link Inertia Warning

#### 🚨 The Problem
When running `robot_state_publisher`, the following warning was thrown:
```text
[WARN] [kdl_parser]: The root link base_link has an inertia specified in the URDF, 
but KDL does not support a root link with an inertia.
```

#### 🔍 Root Cause
The Kinematics and Dynamics Library (KDL) used by ROS 2 `robot_state_publisher` requires the root kinematic link of a tree structure to have no inertia.

#### ✅ The Solution
Declared `<link name="base_footprint"/>` with no `<inertial>` block as the root link and connected it to `base_link` via a fixed joint.

---

### 6. Duplicate Robot Spawning in Gazebo ("Two Bots" Bug)

#### 🚨 The Problem
Opening Gazebo showed two overlapping robot models (`assem2_robot` and `assem2_robot_0`) colliding with each other.

#### 🔍 Root Cause
1. `ros_gz_sim create` node defaults to `allow_renaming: true`. If a previous background simulation was active or restarted, the spawner generated a secondary renamed entity instead of rejecting duplicates.
2. Lingering background processes from prior launch attempts remained running in the OS process tree.

#### ✅ The Solution
1. Added `-allow_renaming false` to the `ros_gz_sim create` execution arguments in [`simulation.launch.py`](file:///home/sailakshmi/agilex/src/assem2_robot/launch/simulation.launch.py).
2. Cleaned background tasks and established automated process management (`pkill -9 -f "ros_gz|gz sim"`).

---

### 7. Storage Footprint Optimization (~37 GB Free Partition)

#### 🚨 The Problem
Repeated ROS 2 builds (`colcon build`) can duplicate large binary STL meshes and build logs, rapidly exhausting disk space.

#### ✅ The Solution
1. Employed `colcon build --symlink-install` to reference source files via symlinks rather than copying bulky directories.
2. Added an extensive [`.gitignore`](file:///home/sailakshmi/agilex/.gitignore) excluding `build/`, `install/`, `log/`, and `.colcon/`.
3. Kept the entire repository size minimal at **~3.3 MB**.

---

### 8. GitHub Authentication & Repository Synchronization

#### 🚨 The Problem
* Push attempts over HTTPS prompted for interactive terminal passwords (which GitHub deprecated).
* SSH key submission failed due to multi-line formatting without hyphens (`sshed25519`).
* Initial git push was rejected because the remote GitHub repo contained a preexisting default commit (`fetch first`).

#### ✅ The Solution
1. Rebased local commits onto remote `main` branch (`git rebase FETCH_HEAD`).
2. Configured GitHub Personal Access Token authentication via `git credential.helper store`.
3. Pushed all branches and commit history to [https://github.com/Saibts/ROS_AMR](https://github.com/Saibts/ROS_AMR).

---

## 📊 Summary Matrix of All Resolved Issues

| # | Issue Description | Root Cause | Implemented Fix | Verification |
| :-: | :--- | :--- | :--- | :--- |
| **1** | Humble to Jazzy migration failure | Gazebo Classic plugins incompatible with Gazebo Harmonic | Refactored to `gz::sim::systems::DiffDrive` & `ros_gz_bridge` | Zero bridge errors |
| **2** | Multicast network unreachable | DDS interface broadcast issue | `ROS_LOCALHOST_ONLY=1` & direct topic bridging | Smooth topic communication |
| **3** | Wheel 3 (`j3`) continuous spin | Missing joint `<axis>`, zero damping, unactuated wheel | Added explicit axis, damping `0.1`, friction `0.1`, 4-wheel drive | Wheel stops at `cmd_vel=0` |
| **4** | Robot sunken in RViz grid | SolidWorks CAD origin offset ($Z=-0.2269\text{ m}$) | Introduced `base_footprint` with calibrated $+0.2269\text{ m}$ Z-offset | Wheels rest flat on grid ($Z=0$) |
| **5** | KDL root inertia warning | `base_link` root had inertia | Added massless `base_footprint` as root link | Clean `robot_state_publisher` log |
| **6** | Two robot models in Gazebo | `allow_renaming: true` in `ros_gz_sim create` | Set `-allow_renaming false` and cleaned orphaned processes | Exactly 1 bot in world |
| **7** | Missing `odom` and `/tf` in RViz | Odometry not bridged from Gazebo Transport | Added `/tf` and `/odom` to `parameter_bridge` arguments | Full TF tree: `odom -> base_footprint -> base_link` |
| **8** | Storage bloat | Duplicate builds and untracked logs | Symlink install + comprehensive `.gitignore` | Lean 3.3 MB repo footprint |
| **9** | Git push rejection | Non-fast-forward push & authentication | Rebased on `FETCH_HEAD` and stored PAT credentials | Live on GitHub `main` branch |

---

## 🚀 Quick Verification Commands

```bash
# Build Workspace
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash

# Launch Complete Simulation (Gazebo + RViz2 + RSP + Bridge)
ros2 launch assem2_robot simulation.launch.py

# Teleoperation
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
