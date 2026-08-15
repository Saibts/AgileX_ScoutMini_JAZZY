# 🧠 System Architecture Mindmap & Dataflow: AgileX Scout Mini AMR

This document outlines the detailed system architecture, subsystem dataflows, perception pipelines, kinematics, coordinate frames, and simulation topologies of the **AgileX Scout Mini Autonomous Mobile Robot (AMR)** in **ROS 2 Jazzy** and **Gazebo Harmonic**.

---

## 🗺️ System Architecture Mindmap

```mermaid
mindmap
  root((AgileX Scout Mini 4WD AMR))
    Perception Pipeline
      2D LiDAR Sensor
        Topic: /scan
        FOV: 360° (720 samples)
        Rate: 20 Hz
        Frame: lidar_link
      6-Axis IMU
        Topic: /imu
        Rate: 100 Hz
        Frame: imu_link
      RGB-D Depth Camera
        Topic: /camera/image_raw
        Topic: /camera/depth_image
        Topic: /camera/points
        Rate: 30 Hz
        Resolution: 640x480
    State Estimation & Fusion
      robot_localization EKF
        Inputs: /odom + /imu
        Output: /odometry/filtered
        TF Authority: odom -> base_footprint
        Rate: 50 Hz (2D Mode)
    Kinematics & Control
      4WD Skid-Steer Drive
        gz::sim::systems::DiffDrive
        Track Width: 0.612 m
        Wheel Radius: 0.08 m
      Actuation & Teleop
        Topic: /cmd_vel
        teleop_twist_keyboard
        DWB Local Controller
    Autonomous Navigation (Nav2)
      Global Planner (NavFn)
      Local Controller (DWB)
      AMCL Localization
      Costmaps (Global & Local)
      Waypoint Patrol Mission
    Physics & Simulation
      Gazebo Harmonic (gz-sim8)
      ros_gz_bridge
      amr_world.sdf (10m x 10m)
      Low CoM & Analytical Friction
    Visualization & UI
      RViz2
      RobotModel & JointState
      LaserScan & PointCloud2
      Costmap & Planned Paths
```

---

## 🔄 End-to-End System Dataflow

```mermaid
graph TD
    subgraph Control ["🎮 High-Level Control & Missions"]
        Patrol["Autonomous Patrol Mission<br><i>(patrol_mission.py)</i>"]
        Nav2["Nav2 Stack<br><i>(NavFn Global Planner & DWB Controller)</i>"]
        Teleop["Keyboard Teleop<br><i>(teleop_twist_keyboard)</i>"]
        
        Patrol -->|Target Poses| Nav2
        Nav2 -->|/cmd_vel| Bridge
        Teleop -->|/cmd_vel| Bridge
    end

    subgraph ROS2 ["🤖 ROS 2 Jazzy Workspace"]
        RSP["robot_state_publisher<br><i>(URDF Kinematic Tree)</i>"]
        EKF["robot_localization (ekf_node)<br><i>(Wheel Odom + IMU Fusion)</i>"]
        SLAM["slam_toolbox<br><i>(2D Occupancy Grid Mapping)</i>"]
        Bridge["ros_gz_bridge<br><i>(Actuation, State & Perception Bridge)</i>"]
        RViz["RViz2 Visualization<br><i>(RobotModel, Costmaps, Scan, TF)</i>"]
        
        Bridge -->|/odom, /imu| EKF
        EKF -->|/odometry/filtered, TF: odom->base_footprint| Nav2
        EKF -->|/odometry/filtered, TF: odom->base_footprint| RViz
        Bridge -->|/scan| SLAM
        Bridge -->|/scan, /camera/points| Nav2
        Bridge -->|/scan, /camera/points| RViz
        SLAM -->|/map, TF: map->odom| Nav2
        SLAM -->|/map, TF: map->odom| RViz
        RSP -->|/robot_description, Joint TFs| RViz
    end

    subgraph Gazebo ["🌍 Gazebo Harmonic Simulation (Gz Sim 8)"]
        World["amr_world.sdf<br><i>(10m x 10m Enclosed Obstacle Arena)</i>"]
        
        subgraph ScoutMini ["AgileX Scout Mini 4WD AMR Model"]
            DiffDrive["DiffDrive Plugin<br><i>(4WD Skid-Steer Kinematics)</i>"]
            LiDAR["2D GPU LiDAR<br><i>(20 Hz, 360° FOV, 12m Range)</i>"]
            IMU["6-Axis IMU<br><i>(100 Hz Gyro + Accelerometer)</i>"]
            Camera["RGB-D Depth Camera<br><i>(30 Hz, PointCloud2)</i>"]
            Physics["Calibrated Dynamics<br><i>(Low CoM, Cylinder Collisions, mu2=0.1)</i>"]
        end
        
        Bridge <-->|Actuation & Wheel State| DiffDrive
        LiDAR -->|gz.msgs.LaserScan| Bridge
        IMU -->|gz.msgs.IMU| Bridge
        Camera -->|gz.msgs.Image / PointCloudPacked| Bridge
    end
```

---

## 🌳 Coordinate Frame Hierarchy (TF Tree)

```
[map] (Global Map Frame)
  │
  └── (broadcasted by AMCL / SLAM Toolbox)
      │
      ▼
   [odom] (Odometry Frame)
      │
      └── (broadcasted by robot_localization EKF Filter)
          │
          ▼
      [base_footprint] (Massless ground contact projection, Z=0)
          │
          └── (static calibrated transform: xyz="0.10185 -0.16662 0.2269" rpy="0 0 -1.5707963")
              │
              ▼
          [base_link] (Main CAD Chassis Body)
              ├─── [link1] (Rear-Right Wheel)
              ├─── [link2] (Front-Right Wheel)
              ├─── [link3] (Rear-Left Wheel)
              ├─── [link4] (Front-Left Wheel)
              ├─── [lidar_link] (2D Laser Scanner, Z=0.36m)
              ├─── [imu_link] (6-Axis IMU Sensor)
              └─── [camera_link] ─── [camera_optical_frame] (RGB-D Depth Camera)
```

---

*Documentation maintained by: Sai ([@Saibts](https://github.com/Saibts))*  
*Local path:* [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)  
*GitHub:* [https://github.com/Saibts/AgileX_ScoutMini_JAZZY](https://github.com/Saibts/AgileX_ScoutMini_JAZZY)
