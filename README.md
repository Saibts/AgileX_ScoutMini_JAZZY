# AgileX Scout Mini Simulation (ROS 2 Jazzy, Gazebo Harmonic)

Simulation of the AgileX Scout Mini, a four-wheel skid-steer robot, converted from a SolidWorks model to URDF. The robot maps a civil facility, localizes itself, and navigates autonomously with Nav2. A slip controller detects and corrects wheel slip on a low-friction floor.

## Features

- SolidWorks model exported to URDF, with a 2D LiDAR, IMU and RGB-D camera
- Gazebo Harmonic simulation with RViz2 visualisation
- SLAM mapping (SLAM Toolbox), EKF odometry fusion and AMCL localization
- Nav2 navigation: Smac 2D (A*) planner and regulated pure pursuit controller
- PyQt5 ground station: click a goal on the map and the robot drives there
- Wheel-slip world, slip detection and correction (`slip_control`)
- Motor, gearbox and battery model (`motor_model`)

## Requirements

Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic.

```bash
sudo apt update
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-slam-toolbox ros-jazzy-robot-localization ros-jazzy-rviz2 \
  ros-jazzy-robot-state-publisher ros-jazzy-teleop-twist-keyboard python3-pyqt5
```

## Build

The run scripts expect the repository in `~/agilex`.

```bash
git clone https://github.com/Saibts/AgileX_ScoutMini_JAZZY.git ~/agilex
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Run

| Goal | Command |
|---|---|
| Slip demo (slip world and patrol, one command) | `./run_slip_demo.sh` |
| Autonomous navigation with ground station | `./run_civil_nav.sh` |
| Build a map with SLAM | `./run_civil_mapping.sh`, then `./run_teleop.sh` in a second terminal |
| Save the SLAM map | `./save_civil_map.sh` |
| Simulation only, no SLAM or Nav2 | `./run_civil_sim.sh` |
| Patrol with video recording | `./run_patrol_and_record.sh` |

Turn slip correction off for comparison: `./run_slip_demo.sh slip_correction:=false`

Unit tests of the motor model: `python3 -m pytest src/assem2_robot/tests -q`

## Repository layout

```
src/assem2_robot/
  config/    Nav2, EKF, SLAM and RViz settings
  launch/    simulation and navigation launch files
  maps/      saved occupancy maps
  meshes/    STL meshes from SolidWorks
  scripts/   slip_control, motor_model, ground station, patrol missions
  urdf/      robot description
  worlds/    civil facility and slip world
run_*.sh     launch scripts
```

## More documentation

- [COMMANDS.md](COMMANDS.md): full list of commands
- [NAVIGATION_ISSUES_LOG.md](NAVIGATION_ISSUES_LOG.md): navigation problems and how they were fixed

## License

MIT, see [LICENSE](LICENSE).
