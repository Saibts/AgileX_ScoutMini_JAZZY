# 📊 MATLAB & Python Simulation Suite: AgileX Scout Mini AMR

This directory provides a production-grade suite of **simulation scripts, 4WD physical dynamics models, SolidWorks Simscape Multibody models, and ROS 2 bridges** to simulate, inspect, and control the **AgileX Scout Mini 4WD Autonomous Mobile Robot (AMR)**.

---

## 📁 Included Simulation Modules

| Script / Module | Purpose | Environment |
| :--- | :--- | :--- |
| 🚜 **[`scout_mini_dynamics_sim.py`](scout_mini_dynamics_sim.py)** | **Standalone 4WD Physical Dynamics Simulator:** Full skid-steer multi-body physics, in-hub motor torque limits ($\pm 17.5\text{ Nm}$), slip dynamics ($\alpha = 1.05$), and 6-panel real-time telemetry dashboard. | Python 3 (Terminal) |
| 🚀 **[`run_amr_matlab_suite.m`](run_amr_matlab_suite.m)** | **Master Suite Launcher:** Interactive 1-click terminal menu to launch any simulation mode. | MATLAB Core |
| 🚜 **[`scout_mini_dynamics_sim.m`](scout_mini_dynamics_sim.m)** | **4WD AMR Physical Dynamics:** MATLAB version of the 4WD skid-steer multi-body dynamics simulator with full 6-panel graph suite. | MATLAB Core |
| 🏗️ **[`simscape/simulate_solidworks_amr.m`](simscape/simulate_solidworks_amr.m)** | **SolidWorks Simscape Multibody Runner:** Loads CAD mass/inertia (`Assem2_DataFile.m`), STEP 3D parts, and opens `Assem2.slx` in 3D Mechanics Explorer. | MATLAB / Simscape |
| 🤖 **[`scout_mini_kinematics_sim.m`](scout_mini_kinematics_sim.m)** | **Autonomous Patrol Simulation:** 10m × 10m obstacle arena, 5-station automated patrol mission with VFH dynamic obstacle avoidance. | MATLAB / Navigation Toolbox |
| 🎮 **[`scout_mini_teleop_gui.m`](scout_mini_teleop_gui.m)** | **Interactive Teleoperation & Goal Dispatcher:** Real-time keyboard driving (`W`/`A`/`S`/`D`/`Space`) and click-to-navigate waypoint dispatching. | MATLAB Core |
| 🌐 **[`scout_mini_ros2_bridge.m`](scout_mini_ros2_bridge.m)** | **Live ROS 2 Jazzy Co-Simulation:** Connects MATLAB to Gazebo Harmonic / ROS 2 Jazzy over DDS. | MATLAB / ROS Toolbox |

---

## 🚀 How to Run

### 1. In Linux Terminal (Immediate Python Simulation):
```bash
cd /home/sailakshmi/agilex/matlab
python3 scout_mini_dynamics_sim.py
```

### 2. In MATLAB Application Command Window:
```matlab
cd /home/sailakshmi/agilex/matlab
run_amr_matlab_suite
```

### 3. SolidWorks 3D Simscape Multibody (`Assem2.slx`):
```matlab
cd /home/sailakshmi/agilex/matlab/simscape
simulate_solidworks_amr
```
