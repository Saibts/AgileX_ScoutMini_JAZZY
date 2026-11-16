# Command Sheet

ROS 2 Jazzy, Gazebo Harmonic, Nav2. The repository must be in `~/agilex`.

## 1. Build (once, and after editing a script)

```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 2. How to run the slip simulation

One command. It rebuilds, opens Gazebo, RViz2 and the ground station in the slip world (three low-friction patches, mu 0.04), waits for localization, then starts the 20-leg patrol.

```bash
cd ~/agilex
./run_slip_demo.sh
```

| Variant | Command |
|---|---|
| Slip correction ON (default) | `./run_slip_demo.sh` |
| Slip correction OFF, for comparison | `./run_slip_demo.sh slip_correction:=false` |
| Open the slip world without starting the patrol | `./run_slip_demo.sh --no-mission` |

What to expect:

1. Gazebo, RViz2 and the ground station open (about 20 s).
2. The patrol starts automatically once AMCL has a pose.
3. When the robot crosses a low-friction patch, `/slip/active` becomes `true` and the correction reduces wheel torque.

Watch the slip signals from a second terminal:

```bash
source /opt/ros/jazzy/setup.bash && source ~/agilex/install/setup.bash
export ROS_DOMAIN_ID=19 ROS_LOCALHOST_ONLY=1
ros2 topic echo /slip/active
ros2 topic echo /slip/ratio
```

## 3. Other simulations

| Goal | Command |
|---|---|
| Navigation on the normal floor, with ground station | `./run_civil_nav.sh` |
| Patrol with video saved in `recordings/` | `./run_patrol_and_record.sh` |
| SLAM mapping | `./run_civil_mapping.sh` |
| Keyboard teleop (second terminal) | `./run_teleop.sh` |
| Save the SLAM map under a new name | `./save_civil_map.sh my_map` |
| Simulation only, no SLAM or Nav2 | `./run_civil_sim.sh` |

`./save_civil_map.sh` without a name overwrites `civil_map`, which Nav2 uses.

Teleop keys: `W/S` forward/back, `A/D` turn, `Space` brake, `+`/`-` speed.

## 4. Send a goal by hand

Click **2D Goal Pose** in RViz2, or click the map in the ground station.

To run the patrol manually, start `./run_civil_nav.sh` in terminal 1 and wait for `Managed nodes are active`. Then in terminal 2:

```bash
source /opt/ros/jazzy/setup.bash && source ~/agilex/install/setup.bash
export ROS_DOMAIN_ID=19 ROS_LOCALHOST_ONLY=1
ros2 run assem2_robot civil_nav2_mission
```

Restart terminal 1 before running the patrol again, because the robot must start at the origin.

## 5. Checks

Run `export ROS_DOMAIN_ID=19 ROS_LOCALHOST_ONLY=1` first.

```bash
ros2 topic hz /scan                          # lidar, about 20 Hz
ros2 topic echo /odometry/filtered --once    # EKF output
ros2 topic echo /motor/torque                # per-wheel torque
ros2 topic echo /motor/battery_voltage
ros2 run tf2_ros tf2_echo map base_footprint
gz topic -e -t /stats -n 1                   # real-time factor, about 1.0
python3 -m pytest src/assem2_robot/tests -q  # motor model unit tests
```

## 6. Clean stop and clean build

```bash
for n in gz ruby parameter_bridge rviz2 robot_state_publisher ekf_node component_container_isolated; do killall -9 $n 2>/dev/null; done
for p in $(ps -eo pid,cmd | grep "[a]ssem2_robot/civil_interactive_nav" | awk '{print $1}'); do kill -9 $p; done
```

```bash
rm -rf build/ install/ log/ && colcon build --symlink-install
```

## 7. Key files (under `src/assem2_robot/`)

| File | Purpose |
|---|---|
| `scripts/slip_control.py` | slip detection and correction |
| `scripts/motor_model.py` | motor, gearbox and battery model |
| `scripts/generate_slip_world.py` | generates the slip world |
| `scripts/civil_nav2_mission.py` | 20-leg patrol with ground-truth check |
| `worlds/civil_world_slip.sdf` | civil world with three low-friction patches |
| `config/nav2_params.yaml` | AMCL, costmaps, Smac planner, pure pursuit |
| `urdf/Assem2.SLDASM.urdf` | robot model, sensors, DiffDrive |
