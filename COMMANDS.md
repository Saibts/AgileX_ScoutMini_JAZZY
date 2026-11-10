# AgileX Scout Mini AMR — Command Sheet

ROS 2 Jazzy · Gazebo Harmonic · Nav2. Workspace: `~/agilex`.

**Status tags:** ✅ = run and confirmed working in the last session (2026-10-25) · ⚠️ = script exists but was **not re-run** after the navigation fixes (friction, footprint, Nav2 params), so treat as unverified.

Problems fixed and still open: [`NAVIGATION_ISSUES_LOG.md`](NAVIGATION_ISSUES_LOG.md)

---

## 1. Build  ✅

```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```
Rebuild after changing `CMakeLists.txt` (new executables). Config, URDF and launch files are symlinked, so edits take effect on the next launch without a rebuild.

---

## 2. Autonomous mission + video recording  ✅ (recommended)

One command. It starts a clean simulation, waits for Nav2, tiles the Gazebo / RViz / Ground Station windows, records the desktop (1080p H.264), runs the closed-loop mission and saves everything:

```bash
cd ~/agilex
./run_patrol_and_record.sh                 # default output
./run_patrol_and_record.sh my_run.mp4      # custom video path
./run_patrol_and_record.sh --keep          # leave the sim running afterwards
```
Outputs in `recordings/`: `agilex_civil_patrol_demo.mp4`, `..._report.txt` (per-leg result), `..._sim.log`.
Exit code is `0` only if all legs pass. Takes about 4 minutes. Do not touch the mouse or keyboard during recording.

Route: Conference Hall → CAD Studio → Materials Lab → home at the corridor hub (23 legs). Each arrival is checked against Gazebo ground truth, with up to 3 retries per leg.

---

## 3. Autonomous mission without recording  ✅

**Terminal 1 — simulation + Nav2 + RViz + Ground Station** (always start fresh; the robot must begin at the world origin):
```bash
cd ~/agilex
./run_civil_nav.sh
```
Wait for the log line `Managed nodes are active` (about 30–60 s).

**Terminal 2 — run the mission:**
```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash && source install/setup.bash
export ROS_DOMAIN_ID=19 ROS_LOCALHOST_ONLY=1
ros2 run assem2_robot civil_nav2_mission
```
Stop the mission with `Ctrl+C`; it cancels its active goal.

To run it again, restart Terminal 1 first (the robot is no longer at the origin).

---

## 4. Manual navigation goals  ✅ (Nav2 up, as in §3 Terminal 1)

* **RViz2:** click **2D Goal Pose**, then click-drag on the map.
* **Ground Station window:** click a station button **S1–S7**, or click on the map.
* **Command line:**
  ```bash
  source /opt/ros/jazzy/setup.bash && source install/setup.bash
  export ROS_DOMAIN_ID=19 ROS_LOCALHOST_ONLY=1
  ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
    "{pose: {header: {frame_id: map}, pose: {position: {x: 0.0, y: 2.9}, orientation: {z: 0.7071, w: 0.7071}}}}"
  ```
Use goals that are clear of walls and furniture. Door centres are x = -5.9 / 0 / 5.9 on the walls at y = ±1.2; the corridor has posts at x = ±4.0, y = 0.

---

## 5. Window layout for screen capture  ✅

```bash
cd ~/agilex
python3 scripts/arrange_windows.py                    # tile Gazebo / RViz / Ground Station
python3 scripts/arrange_windows.py --raise-terminal   # bring the terminal back to the front
```
Needs an X11 session at 1920×1080.

Record only (no mission):
```bash
python3 scripts/record_screen.py --output recordings/test.mp4 --fps 24     # Ctrl+C to stop
python3 scripts/record_screen.py --output recordings/test.mp4 --duration 30
```

---

## 6. Diagnostics  ✅

Run in a new terminal with `export ROS_DOMAIN_ID=19 ROS_LOCALHOST_ONLY=1` and both setup files sourced.

```bash
ros2 topic list
ros2 topic hz /scan                                  # lidar, ~20 Hz
ros2 topic echo /odometry/filtered --once            # EKF output
ros2 run tf2_ros tf2_echo map base_footprint         # AMCL pose
ros2 run tf2_ros tf2_echo odom base_footprint        # EKF odometry
ros2 topic echo /cmd_vel --once                      # what is driving the wheels
ros2 topic info /cmd_vel -v                          # who is publishing
gz model -m assem2_robot -p                          # Gazebo ground-truth pose
gz topic -e -t /stats -n 1                           # real-time factor (should be ~1.0)
```

---

## 7. Clean stop  ✅

```bash
for n in gz ruby parameter_bridge rviz2 robot_state_publisher ekf_node component_container_isolated; do killall -9 $n 2>/dev/null; done
for p in $(ps -eo pid,cmd | grep "[a]ssem2_robot/civil_interactive_nav" | awk '{print $1}'); do kill -9 $p; done
killall -9 ros2 2>/dev/null
```
The Ground Station is a `python3` process, so it is only matched by the `ps | grep` line. Do not use `pkill -f` with a pattern that also appears in your own command, as it will kill your shell.

Clean build caches:
```bash
cd ~/agilex
rm -rf build/ install/ log/
colcon build --symlink-install && source install/setup.bash
```

---

## 8. Civil facility: simulation, teleop, SLAM mapping  ⚠️ not re-tested

Wheel friction, footprint and Nav2 parameters changed since these were last run, so driving feel may differ.

```bash
cd ~/agilex
./run_civil_sim.sh          # Gazebo + RViz, no SLAM, no Nav2
./run_civil_mapping.sh      # same with slam_toolbox mapping
./run_teleop.sh             # keyboard teleop (second terminal)
./save_civil_map.sh my_map  # save the SLAM map as src/assem2_robot/maps/my_map.{yaml,pgm}
```
**Warning:** `./save_civil_map.sh` with no argument writes `civil_map`, which **overwrites the map Nav2 uses**. Always pass a new name, and update `civil_nav2_mission`/launch only if you intend to switch maps.

Teleop keys (`civil_teleop.py`): `W/S` forward/back, `A/D` turn, `Q/E/Z/C` arcs, `Space` brake, `+`/`-` speed, `Ctrl+C` exit.

---

## 9. Obstacle arena (10 m × 10 m)  ⚠️ not re-tested

```bash
cd ~/agilex
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch assem2_robot simulation.launch.py                  # sim only
ros2 launch assem2_robot simulation.launch.py use_slam:=true   # SLAM mapping
ros2 launch assem2_robot simulation.launch.py use_nav:=true    # Nav2
ros2 run assem2_robot patrol_mission                           # 5-station patrol (needs use_nav:=true)
```
`patrol_mission` waypoints were never checked against the new footprint and controller settings.

---

## 10. Legacy open-loop demo  ⚠️ not recommended

```bash
ros2 run assem2_robot civil_patrol_mission
```
Plays timed velocity commands with no localisation or obstacle feedback; it can drive into walls if anything drifts. Use §2 or §3 instead.

---

## Key files

| File | Purpose |
|------|---------|
| `src/assem2_robot/scripts/civil_nav2_mission.py` | Closed-loop mission (waypoints at the top of the file) |
| `src/assem2_robot/config/nav2_params.yaml` | AMCL, costmaps, Smac planner, RPP controller |
| `src/assem2_robot/urdf/Assem2.SLDASM.urdf` | Robot model, wheel friction, DiffDrive |
| `src/assem2_robot/maps/civil_map.yaml` | Map used by Nav2 |
| `run_civil_nav.sh` / `run_patrol_and_record.sh` | Launch / launch + record |

---

## Wheel slip: simulate, detect, correct  ⚠️ (tested with a straight-line launch only, not the full patrol)

`worlds/civil_world_slip.sdf` = the civil world plus three blue low-friction patches (μ = 0.04): Conference Hall doorway (y 1.4–3.2), east corridor (x 0.6–1.6) and west corridor (x −1.6…−0.6), both full corridor width (y ±1.2). Regenerate with `python3 src/assem2_robot/scripts/generate_slip_world.py`.

```bash
./run_civil_nav.sh                                   # normal floor, slip control active
ros2 launch assem2_robot civil_simulation.launch.py \
    world:=$HOME/agilex/install/assem2_robot/share/assem2_robot/worlds/civil_world_slip.sdf
ros2 launch assem2_robot civil_simulation.launch.py slip_correction:=false   # monitor only
```

The `slip_control` node sits between planners and Gazebo (`/cmd_vel` → `/cmd_vel_safe`). It estimates ground speed from the IMU, flags slip when wheel speed disagrees, then (1) limits the wheel command to ground speed + 0.12 m/s (traction control), (2) feeds back IMU yaw rate, (3) estimates sideways slip, and (4) publishes `/odom_corrected` (forward + sideways speed) for the EKF. Monitor with `ros2 topic echo /slip/active`, `/slip/ratio`, `/slip/traction_scale`.

The `motor_model` node sits after it (`/cmd_vel_safe` → `/cmd_vel_motor` → Gazebo). It adds the missing motor layer: per-wheel torque (`/motor/torque`), motor current (`/motor/current`), electrical power (`/motor/power`), battery state of charge and terminal voltage (`/motor/battery_soc`, `/motor/battery_voltage`), a `/motor/saturated` flag when a motor reaches its torque limit, and traction demand against dry floor and the low-friction patch (`/motor/traction_dry`, `/motor/traction_patch`; above 1.0 means the wheels cannot get that force from the floor). Check it with `ros2 topic echo /motor/torque`. Motors are the manual's 4 × 150 W DC brushless hub motors driving the wheels directly (`gear_ratio` 1:1; set it and `gear_efficiency` for a geared drive); the battery model is 25.2 V full to 21.0 V empty with 0.08 Ω internal resistance. Parameters are at the top of `scripts/motor_model.py`; rebuild with `colcon build --symlink-install` after editing it.

**After editing `scripts/slip_control.py` run `colcon build --symlink-install`** – CMake installs a copy of the script, so edits are not picked up otherwise.

Measured (full 23-leg patrol on the slip world, final patch layout): correction off 3/23 (1 run); correction on 23/23 (1 run) – a very small sample. Earlier patch layout: off 3,3,3,21; on 23,21,23,23,21,21,5 of 23. Remaining failures: the robot slides sideways into a column/wall in the corridor lanes. Normal floor with slip control on: 23/23. Simulation only; IMU axis settings are tuned for Gazebo.
