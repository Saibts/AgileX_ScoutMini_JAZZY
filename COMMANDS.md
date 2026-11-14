# Command Sheet

ROS 2 Jazzy, Gazebo Harmonic, Nav2. Workspace: `~/agilex`.

## Build

```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Rebuild after editing a script (CMake installs a copy of it) or after adding a new executable.

## Run

```bash
./run_slip_demo.sh                      # slip world + patrol, one command
./run_slip_demo.sh slip_correction:=false   # same, correction off
./run_civil_nav.sh                      # normal floor, Nav2 + ground station
./run_patrol_and_record.sh              # patrol with video in recordings/
./run_civil_mapping.sh                  # SLAM mapping
./run_teleop.sh                         # keyboard teleop (second terminal)
./save_civil_map.sh my_map              # save the map under a new name
./run_civil_sim.sh                      # simulation only
```

Warning: `./save_civil_map.sh` without a name overwrites `civil_map`, which Nav2 uses.

Teleop keys: `W/S` forward/back, `A/D` turn, `Space` brake, `+`/`-` speed.

## Patrol by hand

Terminal 1: `./run_civil_nav.sh` (wait for `Managed nodes are active`).

Terminal 2:
```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
export ROS_DOMAIN_ID=19 ROS_LOCALHOST_ONLY=1
ros2 run assem2_robot civil_nav2_mission
```

Restart Terminal 1 before running it again, because the robot must start at the origin.

Single goal: click **2D Goal Pose** in RViz2, or click the map in the ground station.

## Check things

Use `export ROS_DOMAIN_ID=19 ROS_LOCALHOST_ONLY=1` first.

```bash
ros2 topic hz /scan                         # lidar, about 20 Hz
ros2 topic echo /odometry/filtered --once   # EKF output
ros2 topic echo /slip/active                # slip flag
ros2 topic echo /slip/ratio
ros2 topic echo /motor/torque               # per-wheel torque
ros2 topic echo /motor/battery_voltage
ros2 run tf2_ros tf2_echo map base_footprint
gz topic -e -t /stats -n 1                  # real-time factor, should be about 1.0
python3 -m pytest src/assem2_robot/tests -q # motor model unit tests
```

## Clean stop and clean build

```bash
for n in gz ruby parameter_bridge rviz2 robot_state_publisher ekf_node component_container_isolated; do killall -9 $n 2>/dev/null; done
for p in $(ps -eo pid,cmd | grep "[a]ssem2_robot/civil_interactive_nav" | awk '{print $1}'); do kill -9 $p; done
```

```bash
rm -rf build/ install/ log/ && colcon build --symlink-install
```

## Key files

| File | Purpose |
|---|---|
| `scripts/slip_control.py` | slip detection and correction |
| `scripts/motor_model.py` | motor, gearbox and battery model |
| `scripts/civil_nav2_mission.py` | 20-leg patrol with ground-truth check |
| `config/nav2_params.yaml` | AMCL, costmaps, Smac planner, pure pursuit |
| `worlds/civil_world_slip.sdf` | civil world with three low-friction patches (mu 0.04) |
| `urdf/Assem2.SLDASM.urdf` | robot model, sensors, DiffDrive |

(Paths are under `src/assem2_robot/`.)
