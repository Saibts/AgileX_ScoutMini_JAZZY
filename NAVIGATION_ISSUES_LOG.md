# Autonomous Navigation: Issues Found, Fixed, and Still Open

Scope: the civil-facility closed-loop Nav2 mission (`civil_nav2_mission.py`) on the AgileX Scout Mini
in ROS 2 Jazzy + Gazebo Harmonic. Last verified run (recorded): **23/23 legs, 0 retries, worst
arrival error vs Gazebo ground truth 0.33 m**. Video: `recordings/agilex_civil_patrol_demo.mp4`.

---

## 1. Problems found and solved

| # | Problem | How it showed up | Root cause | Fix |
|---|---------|------------------|------------|-----|
| 1 | "Autonomous patrol" was not autonomous | Worked only if nothing drifted | `civil_patrol_mission.py` plays timed `cmd_vel` commands, with no localisation, planning or obstacle feedback | New `civil_nav2_mission.py`: every leg is a real Nav2 `NavigateToPose` goal |
| 2 | Robot drove ~8 m through the outer wall | Map y reached 8.9 (wall at 8.0) | Nav2 config ran 1.55 m/s, collision detection off, rotate speed 2.5 rad/s | 0.6 m/s cruise, `use_collision_detection: true`, rotate 0.6 rad/s, lower smoother limits |
| 3 | Robot could not turn | Commanded ω gave ~0° yaw; arcs turned ~17° of 137° | Wheel friction μ=1.0; DART applies one isotropic μ, so `mu2=0.15` was ignored | Wheel `mu1=mu2=0.25` in the URDF; in-place turns now work |
| 4 | Lidar saw the robot's own front | "Collision ahead" in open floor; AMCL scan matching corrupted | Self-hits at 0.25–0.5 m across a ±60° forward arc were marked lethal | `obstacle_min_range`, `raytrace_min_range`, AMCL `laser_min_range` set to 0.55 |
| 5 | Turn-in-place deadlock | Constant 0.10 rad/s command, no motion | Angular acceleration limit applied from *measured* velocity (0), static friction never broken | `max_angular_accel` 8.0, smoother angular accel 6.0 |
| 6 | Planner errors in narrow passages | "Failed to create a plan from potential" | NavFn with `use_astar: true` | Switched to `nav2_smac_planner::SmacPlanner2D` |
| 7 | Waypoint inside an obstacle | Planner failed for goal (4.5, 0.0) | Corridor has posts on the centreline at x=±4.0 | Waypoints routed in the north lane (y=0.65) |
| 8 | Spin on arrival never converged | Controller flipped ±0.6 rad/s every 1.5 s | Goal heading (180°) differed ~270° from arrival heading | Goal heading = direction of travel from the previous waypoint; yaw checked only at stations |
| 9 | Robot wedged on door jambs and furniture | AMCL pose ran 0.6–1.7 m ahead of truth | Nav2 footprint was 0.58 m wide, real robot is ~0.67 m (track 0.612 + wheel width) | Footprint ±0.33 × ±0.35, inflation 0.55 m, scale 4.0 |
| 10 | AMCL lost the robot in similar rooms | AMCL 4 m from truth in the CAD Studio | Motion noise too tight for skid-steer slip; recovery disabled | alpha1 0.30, others 0.10; particles 1000–4000; recovery alphas 0.1 / 0.001 |
| 11 | Tight door tracking | Corner clipped the jamb on room exit | Slack of only 0.26 m per side | True door centre x=±5.9, shift to ±6.3 only after the wall, lookahead 0.25–0.60 m |
| 12 | Verification used the same pose that was wrong | "OK" legs were wrong by 1.4 m | Arrival checked only against AMCL | Each arrival also checked against Gazebo ground truth (`gz model -p`) |
| 13 | Leftover goals contaminated tests | `/cmd_vel` busy while idle | Timed-out runs never cancelled their goal | Mission cancels its active goal on exit |
| 14 | Stale ground-station windows piled up | 5 GUI instances, covered the desktop | GUI is a `python3` process, so `killall` by name missed it | Launcher and record script kill it by PID |
| 15 | Recording showed the terminal, not the sim | Screenshot was all terminal | No window management | `scripts/arrange_windows.py` tiles Gazebo / RViz / ground station via libX11 |
| 16 | Video ran faster than real time and was large | Frames dropped under load; MPEG-4 part 2 | Fixed-rate loop, `mp4v` codec | Repeat frames to hold wall-clock timing; H.264 (`avc1`), 40 MB → 11 MB |

Supporting changes: `run_patrol_and_record.sh` (clean sim every time, waits for Nav2, saves report and
sim log, returns the mission exit code), new mission registered in `CMakeLists.txt`, `COMMANDS.md` updated.

---

## 2. Problems still open

1. **Brief pauses entering the CAD and Materials rooms.** About 590 "collision ahead" warnings (and a few
   "patience exceeded" events) in the last runs, each a 2–3 s stop. The robot's front corner swings within
   ~0.1 m of the rig / press (edge at x=±5.5) as it turns in from the door. Each pause recovered on its own
   and no leg failed. Likely fixes: reposition the furniture, use a smaller footprint model for the planner
   with a safety margin elsewhere, or add a dedicated approach waypoint.
2. **Repeatability is not proven.** The final configuration passed one clean end-to-end run (the recorded one).
   Earlier configurations failed at different legs, so run `./run_patrol_and_record.sh` several times before
   calling it production-ready.
3. **Odometry is poor in rotation.** Skid-steer slip gives roughly 60–65% of the commanded yaw. The plugin's
   wheel odometry over-reports rotation, so the system relies on the EKF's IMU yaw rate and AMCL to correct it.
   `wheel_separation` in the DiffDrive plugin has not been calibrated to the effective track.
4. **Mission assumes the robot starts at the world origin.** It seeds AMCL at (0, 0) and the route is hard-coded.
   Starting anywhere else (or reusing a session where the robot has moved) will fail. Always use a fresh sim.
5. **Waypoints are hand-tuned to this world.** The route avoids the corridor posts and furniture by explicit
   coordinates. Changing `civil_world.sdf` requires re-checking clearances.
6. **Ground-truth verification only works in simulation.** The `gz model -p` check has no equivalent on a real
   robot, where only AMCL covariance can detect localisation loss. The mission does not yet monitor covariance
   or re-localise automatically.
7. **Legs are separate goals, so the robot stops at every waypoint.** `NavigateThroughPoses` would give a more
   fluid path but was not tried.
8. **Only the civil world was tuned.** The Nav2 changes (footprint, speeds, friction, planner) affect the
   obstacle arena too (`simulation.launch.py use_nav:=true`), which was not re-tested. The `patrol_mission`
   waypoints there are unverified with the new parameters.
9. **Legacy items left in place.** `civil_patrol_mission` (open-loop) is still installed, and the reports,
   PDFs and `README.md` still describe the old open-loop demo and the old parameter values.
10. **Recording depends on X11 and screen size.** `arrange_windows.py` and `record_screen.py` assume a
    1920×1080 X11 desktop; Wayland or other resolutions need adjusting. The Gazebo and ground-station windows
    have minimum sizes, so they overlap slightly (the 3D view stays clear).
11. **`ROS_LOCALHOST_ONLY` and fastrtps SHM warnings** appear on every start (`RTPS_TRANSPORT_SHM Error`).
    They are harmless but noisy.

---

## 3. Housekeeping done

Removed: `__pycache__` folders, `log/` (ROS run logs, regenerable), empty `Ogre.log`, three `*.backup`
files, a duplicate `frames_2026-08-21_19.52.31.pdf`, and the duplicate root `launch/simulation.launch.py`
(identical to the one under `src/assem2_robot/launch/`). Kept: all reports, PDFs and DOCX files, the
generator scripts, the MATLAB folder, and the previous open-loop video
(`recordings/agilex_civil_patrol_demo_openloop_old.mp4`, 40 MB, safe to delete if not needed).
