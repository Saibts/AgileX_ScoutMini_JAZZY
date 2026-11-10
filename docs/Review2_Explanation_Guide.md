# Second Review: Explanation Guide
AgileX Scout Mini, ROS 2 Jazzy + Gazebo Harmonic + Nav2, with slip simulation and a slip controller.
Companion to `ROS_Report_Review2_Sailakshmi.pdf`. Suggested time is 12 to 15 minutes.

---
## 0. The 30-second pitch (say this first)
"In Review 1 I built the robot and got it to navigate in a simulated civil-department building. In Review 2 I added a harder problem: slippery floor patches. I built a slip world, a slip controller that estimates real ground speed from the IMU, detects slip, limits traction and corrects odometry, and a Ground Station GUI to send multi-leg routes. I then tested it with nine runs: normal, slip with correction on, and slip with correction off."

## 1. Review 1 recap (about 1 minute; keep it short)
- Robot model, a 4-wheel skid-steer Scout Mini, driven in Gazebo through a differential-drive plugin.
- Sensors: LiDAR, IMU, wheel odometry. Localisation with an EKF (robot_localization) and AMCL on a map.
- Mapping with slam_toolbox. Navigation with Nav2: Smac 2D planner, RotationShim + Regulated Pure Pursuit controller, velocity smoother, collision monitor.
- Patrol of the building worked on normal floor (+1.8 % tour time).
- The report has a comparison table (Review 1 vs Review 2).
- Say: "Review 1 assumed perfect grip. Review 2 removes that assumption."

## 2. Why slip matters (30 seconds)
- Skid-steer wheels spin on a low-friction floor, so wheel odometry over-reports distance.
- The EKF trusts that odometry, so the robot's position goes wrong and navigation fails.
- Fix: do not trust wheel speed blindly. Compare it with an independent estimate from the IMU.

## 3. Slip world (Section 4)
- World `civil_world_slip.sdf` (world name `amr_world`).
- Three flush patches with μ = 0.04: north doorway (0, 2.3) 1.2×1.8 m; east corridor (1.1, 0) 1.0×2.4 m; west corridor (−1.1, 0) 1.0×2.4 m.
- Wheel friction μ = 0.25. The patches are flush with the floor, so the robot cannot see them. It has to detect slip from motion.
- Show Figs 11–14 (Gazebo renders) and the RViz views.

## 4. Slip controller, the core contribution (Section 5)
Data flow: `/cmd_vel → slip_control → /cmd_vel_safe → bridge → Gazebo`. The EKF takes `/odom_corrected`.

**Step 1: ground-speed estimate.** The IMU acceleration is integrated and blended with wheel speed in a complementary filter. Protections: gating, zero-velocity update, a latch breaker and an energy bound.

**Step 2: slip detection.** Slip ratio = (wheel speed − estimated ground speed) / wheel speed. Hysteresis and debounce stop it flickering. Detection runs at 100 Hz.

**Step 3: traction limiter.** When slip is active, the commanded speed is held to the estimate ± 0.12 m/s for 0.6 s. It stays between the request and the current output, and angular acceleration is halved while limiting.

**Step 4: yaw-rate feedback**, always on (gain 0.4, limit ±0.6 rad/s), to keep the heading straight.

**Step 5: odometry correction.** Lateral velocity is estimated, and the wheel odometry is replaced by the corrected value, with dead-bands of 0.04 and 0.03. This is what makes the EKF stay accurate on ice.

Control step: 50 Hz. Topics: `/slip/active`, `/slip/ratio`, `/slip/traction_scale`, `/slip/ground_speed_est`, `/slip/correction_enabled` (latched).
Honest note: `acc_slip` = 0.8 is declared but unused. Say so if asked.
Show: architecture figure, rqt_graph of the slip world, flowchart (page 23).

## 5. Ground Station (Section 6)
- PyQt5 GUI with an ActionClient for `NavigateToPose`.
- Multi-leg routes with a route_id, so a new route pre-empts the old one.
- Goal snap: a goal that lands in an obstacle is moved to free space (≥ 0.55 m).
- Near-goal acceptance: within 0.30 m, or after 6 s.
- Show: Ground Station screenshots (flat floor, slip floor, goal, route).

## 6. Motors and sensors (Section 3)
- Drive: 4 wheels, skid steer, left and right sides driven in pairs by DiffDrive.
- Sensors: 2D LiDAR (scan), IMU (orientation, yaw rate, acceleration), wheel odometry.
- Note: the real-robot spec values come from the published AgileX pages, not from my own measurement.

## 7. Algorithms (Section 7), one line each
- Smac 2D: grid planner for the global path.
- RotationShim + RPP: rotate to the path heading, then follow it.
- Velocity smoother: acceleration limits.
- Collision monitor: emergency stop and slowdown.
- AMCL: particle-filter localisation on the map.
- EKF: fuses corrected odometry (vx, vy) and IMU yaw rate at 20 Hz.
- slam_toolbox: mapping.
- Slip control: Section 4 above.

## 8. How to run (Section 8)
1. Build: `colcon build`, then `source install/setup.bash`.
2. Launch: `ros2 launch assem2_robot civil_simulation.launch.py use_nav:=true world:=<civil_world_slip.sdf> slip_correction:=true`
3. Open the Ground Station and send a route.
4. Toggle correction on or off with `slip_correction:=true/false` (this is how I produced runs 4–9).

## 9. Experiments and results (Sections 9–10)
Nine runs: 3 conditions × 3 route sets.
| Condition | Result | Notes |
|---|---|---|
| Normal floor | 4/4 complete | worst position error 0.37 m |
| Slip, correction on | 3/4 complete | one stop at leg 9: heading 45–46° against a 40° limit, 0.14 m position error |
| Slip, correction off | 2/3 complete | one stop at leg 4: overshoot 0.48–0.61 m |
- Tour time: +1.8 % (normal), +2.2 % (slip).
- Station heading: worst 38° of the 40° limit.
- Message: with correction the robot finished more runs and overshot much less. The one failure is a heading-tolerance miss, not a position failure.

## 10. Problems solved (Section 11; pick 3 to tell)
1. Odometry drift on ice → correction from the IMU estimate.
2. The ground-speed estimate latched at a wrong value → latch breaker and energy bound.
3. Goals ending in obstacles → goal snap.
4. Old routes continuing after a new one was sent → route_id pre-emption.
5. Screenshots of Gazebo/RViz are blocked on Wayland → used virtual camera sensors for Gazebo (problem 10).

## 11. Limitations (say these before they ask; Section 12)
- Simulation only; no real-robot slip test.
- Patch friction is fixed (μ = 0.04); real floors vary.
- Leg-12 aborts on the slip floor and the slowdown at S7 were not investigated.
- Few runs (nine in total), so the results are indicative, not statistical.
- `acc_slip` is unused.

## 12. Likely questions and answers
- **Why use the IMU, not wheel odometry?** Wheels spin on ice, and the IMU measures real body motion.
- **How do you know slip is happening?** Wheel speed and estimated ground speed diverge, and the ratio is above the threshold for several samples (hysteresis).
- **Does IMU integration drift?** Yes. That is why it is blended in a complementary filter, with zero-velocity updates when stopped and an energy bound.
- **Why did the slip-on run fail once?** The robot stopped at leg 9 because the heading was 45–46° against a 40° limit, while the position was only 0.14 m off. The failure is in the goal-heading tolerance, not in localisation.
- **Is slip-off worse?** It overshot 0.48–0.61 m and aborted at leg 4. The sample is small, so I describe it as a trend.
- **What would you do next?** Test on the real robot, vary μ, and tune the heading approach near goals.

## 13. Suggested flow with page numbers
Cover → Intro (1) → Review 1 vs 2 table (2) → Robot hardware (3) → Slip world (4) → Controller (5) → Ground Station (6) → Algorithms (7) → How to run (8) → Results (10) → Problems (11) → Limits and Conclusion (12–13).
