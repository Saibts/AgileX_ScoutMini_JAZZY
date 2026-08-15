# 📊 MATLAB Simulation & Co-Simulation Suite: AgileX Scout Mini AMR

This directory provides a comprehensive, production-grade suite of **MATLAB scripts, object-oriented kinematic/dynamic models, obstacle avoidance controllers, Simscape Multibody physical models, and ROS 2 Jazzy bridges** to simulate, inspect, and control the **AgileX Scout Mini 4WD Autonomous Mobile Robot (AMR)**.

---

## 📁 Included Files & Simulation Modes

| Script / Module | Purpose | Toolboxes Required |
| :--- | :--- | :--- |
| 🤖 **[`ScoutMiniRobot.m`](ScoutMiniRobot.m)** | **Core Robot Class:** 4WD skid-steer kinematics with ICR slip factor, hub motor rate limits, 2D LiDAR raycaster, 6-axis IMU with noise/bias, wheel encoders, and onboard Extended Kalman Filter (EKF). | MATLAB Core |
| 🚀 **[`scout_mini_kinematics_sim.m`](scout_mini_kinematics_sim.m)** | **Autonomous Patrol Simulation:** 10m × 10m obstacle arena (matching `amr_world.sdf`), 5-station automated patrol mission (Stations A $\rightarrow$ B $\rightarrow$ C $\rightarrow$ D $\rightarrow$ E $\rightarrow$ A), VFH dynamic obstacle avoidance, and real-time multi-panel telemetry HUD. | Navigation Toolbox, Robotics System Toolbox |
| 🎮 **[`scout_mini_teleop_gui.m`](scout_mini_teleop_gui.m)** | **Interactive Teleoperation & Goal Dispatcher:** Real-time keyboard driving (`W`/`A`/`S`/`D`/`Space`) and interactive click-to-navigate waypoint dispatching with live 4-wheel RPM bars. | MATLAB Core / Navigation Toolbox |
| 🤖 **[`import_scout_mini_urdf.m`](import_scout_mini_urdf.m)** | **3D RigidBodyTree Import & Visualizer:** Multi-path URDF loader (`Assem2.SLDASM.urdf`), kinematic hierarchy summary, and interactive 3D visualizer with mesh rendering. | Robotics System Toolbox |
| 🏗️ **[`simscape/launch_scout_simscape.m`](simscape/launch_scout_simscape.m)** | **SolidWorks Simscape Multibody Loader:** Loads CAD mass/inertia (`Assem2_DataFile.m`), STEP 3D parts, sets up 4-wheel torque limits, and opens `Assem2.slx` in 3D Mechanics Explorer. | Simscape Multibody, Simulink |
| ⚙️ **[`import_to_simulink.m`](import_to_simulink.m)** | **Simulink Simscape Generator:** Automatically converts the URDF and 3D STL meshes into a complete physical multi-body Simulink block diagram (`.slx`). | Simscape Multibody |
| 🌐 **[`scout_mini_ros2_bridge.m`](scout_mini_ros2_bridge.m)** | **Live ROS 2 Jazzy Co-Simulation:** Connects MATLAB directly to Gazebo Harmonic / ROS 2 Jazzy over DDS, streaming `/odometry/filtered`, `/scan`, `/imu`, `/joint_states`, and publishing `/cmd_vel`. | ROS Toolbox |

---

## 🧮 1. Kinematic Model & Mathematical Parameters

The AgileX Scout Mini operates as a **4-Wheel Skid-Steer / Independent In-Wheel Hub Drive** robot:

* **Track Width ($W$):** $0.612\text{ m}$ (distance between left and right wheel contact lines)
* **Wheelbase ($L$):** $0.450\text{ m}$ (distance between front and rear axles)
* **Wheel Radius ($R$):** $0.080\text{ m}$ ($160\text{ mm}$ outer tire diameter)
* **Robot Mass ($M$):** $30.0\text{ kg}$ (Chassis: $27.6\text{ kg}$, Wheels: $4 \times 1.19\text{ kg}$)
* **Max Linear Speed ($v_{\max}$):** $1.5\text{ m/s}$ (Rated up to $3.0\text{ m/s}$)
* **Max Angular Speed ($\omega_{\max}$):** $2.5\text{ rad/s}$ (Zero-radius turning in place)
* **Skid-Steer Slip Factor ($\alpha$):** $1.05$ (Instantaneous Center of Rotation parameter)

### Kinematic Equations of Motion:
$$\dot{x} = v \cos(\theta)$$
$$\dot{y} = v \sin(\theta)$$
$$\dot{\theta} = \omega$$

### 4-Wheel Speed & RPM Decomposition:
$$v_{\text{right}} = v + \frac{\omega \cdot (W \cdot \alpha)}{2}$$
$$v_{\text{left}} = v - \frac{\omega \cdot (W \cdot \alpha)}{2}$$

$$\omega_{\text{FL}} = \omega_{\text{RL}} = \frac{v_{\text{left}}}{R}, \quad \omega_{\text{FR}} = \omega_{\text{RR}} = \frac{v_{\text{right}}}{R}$$

$$\text{RPM}_{\text{wheel}} = \left(\frac{\omega_{\text{wheel}}}{2 \pi}\right) \times 60$$

---

## 🚀 2. Quickstart Execution Guide

### Mode A: Standalone Autonomous Patrol & EKF Simulation
In MATLAB, run:
```matlab
scout_mini_kinematics_sim
```
* Renders the 10m × 10m arena matching Gazebo `amr_world.sdf`.
* Simulates 360° LiDAR raycasting and Vector Field Histogram (VFH) obstacle avoidance.
* Runs onboard Extended Kalman Filter (EKF) sensor fusion.
* Continuously patrols through Stations A $\rightarrow$ B $\rightarrow$ C $\rightarrow$ D $\rightarrow$ E $\rightarrow$ A.

---

### Mode B: Interactive Keyboard Teleoperation & Click-to-Navigate GUI
In MATLAB, run:
```matlab
scout_mini_teleop_gui
```
* **Drive manually:** Press `W` (Forward), `S` (Reverse), `A` (Spin Left), `D` (Spin Right), `Space` (Brake).
* **Click to navigate:** Click anywhere on the map to set an autonomous goal; the robot maneuvers around obstacles to the target!
* **Toggle Mode:** Press `M` to switch between Manual Teleop and Autonomous Navigation.

---

### Mode C: 3D RigidBodyTree Model & Kinematics Inspection
In MATLAB, run:
```matlab
import_scout_mini_urdf
```
* Automatically locates the URDF across Windows and Linux path layouts.
* Displays link hierarchy, mass properties, and 3D visual mesh rendering.

---

### Mode D: SolidWorks Simscape Multibody 3D Physical Dynamics
In MATLAB, navigate to `simscape/` and run:
```matlab
launch_scout_simscape
```
* Loads CAD mass & inertia properties (`Assem2_DataFile.m`).
* Verifies STEP 3D CAD geometries.
* Opens `Assem2.slx` inside Simulink and Mechanics Explorer for full 3D physical multi-body dynamics.

---

### Mode E: Live ROS 2 Jazzy & Gazebo Harmonic Co-Simulation
1. In your ROS 2 Jazzy environment (Linux / WSL2):
   ```bash
   cd ~/agilex_ws
   source /opt/ros/jazzy/setup.bash
   source install/setup.bash
   ros2 launch assem2_robot simulation.launch.py use_nav:=true
   ```
2. In MATLAB, run:
   ```matlab
   scout_mini_ros2_bridge
   ```
3. MATLAB connects over ROS 2 DDS, displays live EKF odometry, LiDAR scan point clouds, and joint states in real time.
