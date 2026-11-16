# AgileX Scout Mini Simulation (ROS 2 Jazzy, Gazebo Harmonic)

Simulation of the AgileX Scout Mini, a four-wheel skid-steer robot, converted from a SolidWorks model to URDF. It maps a civil facility, localizes, and navigates with Nav2. A slip controller detects and corrects wheel slip on a low-friction floor.

## Features

- URDF model with 2D LiDAR, IMU and RGB-D camera
- SLAM Toolbox mapping, EKF odometry fusion, AMCL localization
- Nav2 navigation (Smac 2D planner, regulated pure pursuit) with a PyQt5 ground station
- Wheel-slip world with slip detection and correction
- Motor, gearbox and battery model

## Setup

Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic. The repository must be in `~/agilex`.

```bash
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-slam-toolbox ros-jazzy-robot-localization ros-jazzy-rviz2 \
  ros-jazzy-robot-state-publisher ros-jazzy-teleop-twist-keyboard python3-pyqt5

git clone https://github.com/Saibts/AgileX_ScoutMini_JAZZY.git ~/agilex
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```

## Run the slip simulation

```bash
./run_slip_demo.sh                          # slip correction ON
./run_slip_demo.sh slip_correction:=false   # correction OFF, for comparison
```

It opens Gazebo, RViz2 and the ground station in the slip world, then starts the patrol automatically.

## Other simulations

| Goal | Command |
|---|---|
| Navigation with ground station | `./run_civil_nav.sh` |
| SLAM mapping | `./run_civil_mapping.sh`, then `./run_teleop.sh` |
| Patrol with video recording | `./run_patrol_and_record.sh` |
| Simulation only | `./run_civil_sim.sh` |

## More

- [COMMANDS.md](COMMANDS.md): full command sheet (checks, clean stop, key files)
- [NAVIGATION_ISSUES_LOG.md](NAVIGATION_ISSUES_LOG.md): navigation problems and fixes

MIT license, see [LICENSE](LICENSE).
