# 📊 MATLAB Simulation & Co-Simulation Suite: AgileX Scout Mini AMR

This directory provides a complete set of **MATLAB scripts, kinematic models, obstacle avoidance controllers, and ROS 2 bridges** to simulate and control the **AgileX Scout Mini 4WD Autonomous Mobile Robot (AMR)** directly within **MATLAB & Simulink**.

---

## 📁 Included Files & Scripts

| Script | Purpose | Toolboxes Required |
| :--- | :--- | :--- |
| 🚀 **[`scout_mini_kinematics_sim.m`](scout_mini_kinematics_sim.m)** | **Standalone 2D Simulation:** 4WD skid-steer kinematics, 10m × 10m obstacle arena, 2D LiDAR raycaster, Vector Field Histogram (VFH) dynamic obstacle avoidance, and 5-station automated patrol mission with live real-time animation. | Navigation Toolbox, Robotics System Toolbox |
| ⚙️ **[`import_to_simulink.m`](import_to_simulink.m)** | **Simulink Simscape Generator:** Automatically converts the URDF and 3D STL meshes into a complete physical multi-body Simulink block diagram (`.slx`) with 3D Mechanics Explorer. | Simscape Multibody |
| 🌐 **[`scout_mini_ros2_bridge.m`](scout_mini_ros2_bridge.m)** | **Live ROS 2 Co-Simulation:** Connects MATLAB directly to the live Gazebo Harmonic / ROS 2 Jazzy simulation, subscribes to `/odometry/filtered` and `/scan`, and publishes `/cmd_vel` velocity commands. | ROS Toolbox |
| 🤖 **[`import_scout_mini_urdf.m`](import_scout_mini_urdf.m)** | **3D RigidBodyTree Import:** Loads the URDF (`Assem2.SLDASM.urdf`) and STL visual meshes directly into MATLAB's 3D kinematic tree visualizer. | Robotics System Toolbox / Simscape |

---

## 🧮 1. Kinematic Model & Mathematical Parameters

The AgileX Scout Mini operates as a **4-Wheel Skid-Steer / Differential Drive** robot with the following calibrated parameters:

* **Track Width ($W$):** $0.612\text{ m}$ (effective distance between left and right wheel contact lines)
* **Wheel Radius ($R$):** $0.080\text{ m}$ ($160\text{ mm}$ outer diameter)
* **Footprint:** $0.70\text{ m} \times 0.60\text{ m}$

### Kinematic Equations of Motion:
$$\dot{x} = v \cos(\theta)$$
$$\dot{y} = v \sin(\theta)$$
$$\dot{\theta} = \omega$$

### Wheel Linear & Angular Velocity Decomposition:
$$v_{\text{right}} = v + \frac{\omega \cdot W}{2}$$
$$v_{\text{left}} = v - \frac{\omega \cdot W}{2}$$

$$\text{RPM}_{\text{wheel}} = \left(\frac{v_{\text{wheel}}}{2 \pi R}\right) \times 60$$

---

## 🚀 2. Quickstart Guide in MATLAB & Simulink

### Mode A: Run the Standalone MATLAB Navigation Simulation
1. Open MATLAB.
2. In the MATLAB Current Folder panel, navigate to `/home/sailakshmi/agilex/matlab` (or the `matlab/` folder in your cloned repo).
3. Open and run:
   ```matlab
   scout_mini_kinematics_sim
   ```
4. A high-resolution 2D window will open, rendering:
   * The 10m × 10m obstacle arena (matching `amr_world.sdf`).
   * Real-time 360-ray 2D LiDAR point clouds.
   * Vector Field Histogram (VFH) dynamic obstacle avoidance.
   * Continuous patrol looping through Station A $\rightarrow$ B $\rightarrow$ C $\rightarrow$ D $\rightarrow$ E.

---

### Mode B: Import URDF into a Simulink Model (Simscape Multibody)
1. In MATLAB, navigate to `matlab/`.
2. Run:
   ```matlab
   import_to_simulink
   ```
3. **Simulink will automatically generate and open a complete `.slx` model** containing:
   * Rigid Body subsystem blocks for `base_link`, `w1`, `w2`, `w3`, and `w4` with realistic mass, inertias, and 3D STL meshes.
   * Revolute Joint blocks for wheel drive actuation.
   * A 3D **Mechanics Explorer** interactive visualization window.

---

### Mode C: Connect MATLAB to Live ROS 2 / Gazebo Simulation
1. In your Linux terminal, launch the ROS 2 simulation:
   ```bash
   cd ~/agilex
   source /opt/ros/jazzy/setup.bash
   source install/setup.bash
   ros2 launch assem2_robot simulation.launch.py use_nav:=true
   ```
2. In MATLAB, run:
   ```matlab
   scout_mini_ros2_bridge
   ```
3. MATLAB will connect over DDS/ROS 2, stream live sensor data from Gazebo, and plot the real-time trajectory!

---

### Mode D: Inspect the 3D Kinematic Model
In MATLAB, run:
```matlab
import_scout_mini_urdf
```
This loads the complete robot tree (`base_footprint` $\rightarrow$ `base_link` $\rightarrow$ `w1`-`w4`, `lidar_link`, `imu_link`, `camera_link`) in 3D.
