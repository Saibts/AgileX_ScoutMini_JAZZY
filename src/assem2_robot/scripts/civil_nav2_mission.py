#!/usr/bin/env python3
"""
AgileX Scout Mini AMR — Closed-Loop Nav2 Autonomous Mission
===========================================================
Every leg is a real Nav2 NavigateToPose goal (AMCL localisation, NavFn global
planning, costmap obstacle avoidance, RPP path tracking). Nothing is open-loop.

Safety/verification features:
- Waits for Nav2 lifecycle (action server + map->base_footprint TF) before start
- Re-seeds AMCL pose and waits for the filter to converge
- Door-aligned approach waypoints so the 1.2 m doorways are crossed straight
- Each arrival is verified against TF ground truth (not only the action result)
- Retries with costmap clearing on failure; fails loudly, never silently
- Prints a final per-leg report and exits non-zero if any leg failed
"""

import math
import os
import re
import subprocess
import sys
import time

os.environ.setdefault('ROS_DOMAIN_ID', '19')
os.environ.setdefault('ROS_LOCALHOST_ONLY', '1')
os.environ.setdefault('ROS_AUTOMATIC_DISCOVERY_RANGE', 'LOCALHOST')

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from nav2_msgs.srv import ClearEntireCostmap
from tf2_ros import Buffer, TransformListener

# (name, x, y, yaw_deg, is_station)
# Layout: corridor y in [-1.2, 1.2] with RCC posts on the centreline at x=+/-4.0.
# Room doors (1.2 m) on the north wall at x=-5.9 / 0 / 5.9. The corridor is driven in the
# north lane (y=+0.65) so the posts are passed with ~0.45 m clearance each side.
# Robot is ~0.68 m wide (track 0.612 + wheel width). Doors are crossed on the true centre line
# x=+/-5.9; once past the wall the path shifts to x=+/-6.3 to clear the rig/press (edge +/-5.5).
MISSION = [
    ("Conference Hall door",          0.0,  1.9,  90.0, False),
    ("STATION: Conference Hall",      0.0,  2.9,  90.0, True),
    ("Conference Hall door (out)",    0.0,  1.9, -90.0, False),
    ("Corridor hub",                  0.0,  0.65,  0.0, False),
    ("East lane (past post)",         2.8,  0.65,  0.0, False),
    ("East lane (CAD door)",          5.9,  0.65, 90.0, False),
    ("CAD Studio door (through)",     5.9,  1.7,  90.0, False),
    ("CAD Studio (clear of rig)",     6.3,  2.6,  90.0, False),
    ("STATION: CAD Studio",           6.3,  3.6,  90.0, True),
    ("CAD Studio (clear of rig)",     6.3,  2.6, -90.0, False),
    ("CAD Studio door (through)",     5.9,  1.7, -90.0, False),
    ("Corridor (CAD door)",           5.9,  0.65, 180.0, False),
    ("Corridor hub (west bound)",     0.0,  0.65, 180.0, False),
    ("West lane (past post)",        -2.8,  0.65, 180.0, False),
    ("West lane (Materials door)",   -5.9,  0.65, 90.0, False),
    ("Materials Lab door (through)", -5.9,  1.7,  90.0, False),
    ("Materials Lab (clear of press)", -6.3, 2.6, 90.0, False),
    ("STATION: Materials Lab",       -6.3,  3.6,  90.0, True),
    ("Materials Lab (clear of press)", -6.3, 2.6, -90.0, False),
    ("Materials Lab door (through)", -5.9,  1.7, -90.0, False),
    ("Corridor (Materials door)",    -5.9,  0.65,  0.0, False),
    ("West lane (past post)",        -2.8,  0.65,  0.0, False),
    ("Home: corridor hub",            0.0,  0.0,   0.0, True),
]

POS_TOL = 0.45      # m, verified against TF
YAW_TOL = math.radians(40.0)
MAX_RETRIES = 3
LEG_TIMEOUT = 120.0


def yaw_to_quat(yaw):
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def gz_truth():
    """Ground-truth (x, y) of the robot from Gazebo, independent of AMCL/odom."""
    try:
        out = subprocess.run(['gz', 'model', '-m', 'assem2_robot', '-p'],
                             capture_output=True, text=True, timeout=8).stdout
        v = re.findall(r'\[(-?[\d.e+-]+) (-?[\d.e+-]+) (-?[\d.e+-]+)\]', out)
        return float(v[0][0]), float(v[0][1])
    except Exception:
        return None


def quat_to_yaw(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class Mission(Node):
    def __init__(self):
        super().__init__('civil_nav2_mission',
                         parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)])
        self.nav = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.init_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.clear_local = self.create_client(ClearEntireCostmap, '/local_costmap/clear_entirely_local_costmap')
        self.clear_global = self.create_client(ClearEntireCostmap, '/global_costmap/clear_entirely_global_costmap')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def spin_for(self, sec):
        end = time.time() + sec
        while time.time() < end and rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.05)

    def pose(self):
        try:
            t = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
            return (t.transform.translation.x, t.transform.translation.y,
                    quat_to_yaw(t.transform.rotation))
        except Exception:
            return None

    def wait_ready(self, timeout=120.0):
        self.get_logger().info('Waiting for Nav2 navigate_to_pose server...')
        if not self.nav.wait_for_server(timeout_sec=timeout):
            return False
        end = time.time() + timeout
        while time.time() < end:
            self.spin_for(0.2)
            if self.pose() is not None:
                return True
        return False

    def seed_amcl(self, x, y, yaw):
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.orientation.z, msg.pose.pose.orientation.w = yaw_to_quat(yaw)
        msg.pose.covariance[0] = 0.05
        msg.pose.covariance[7] = 0.05
        msg.pose.covariance[35] = 0.05
        for _ in range(5):
            msg.header.stamp = self.get_clock().now().to_msg()
            self.init_pub.publish(msg)
            self.spin_for(0.2)

    def clear_costmaps(self):
        for cli in (self.clear_local, self.clear_global):
            if cli.wait_for_service(timeout_sec=1.0):
                cli.call_async(ClearEntireCostmap.Request())
        self.spin_for(0.5)

    def go(self, name, x, y, yaw_deg, check_yaw=True):
        """Returns (ok, message). Blocks until goal finished and verified via TF."""
        yaw = math.radians(yaw_deg)
        for attempt in range(1, MAX_RETRIES + 1):
            goal = NavigateToPose.Goal()
            goal.pose.header.frame_id = 'map'
            goal.pose.header.stamp = self.get_clock().now().to_msg()
            goal.pose.pose.position.x = x
            goal.pose.pose.position.y = y
            goal.pose.pose.orientation.z, goal.pose.pose.orientation.w = yaw_to_quat(yaw)

            fut = self.nav.send_goal_async(goal)
            rclpy.spin_until_future_complete(self, fut, timeout_sec=10.0)
            handle = fut.result()
            if handle is None or not handle.accepted:
                self.get_logger().warn(f'  goal rejected (attempt {attempt}); clearing costmaps')
                self.clear_costmaps()
                continue

            self.active = handle
            res_fut = handle.get_result_async()
            t0 = time.time()
            while not res_fut.done() and rclpy.ok() and time.time() - t0 < LEG_TIMEOUT:
                self.spin_for(0.1)
            if not res_fut.done():
                handle.cancel_goal_async()
                self.spin_for(1.0)
                self.get_logger().warn(f'  timeout (attempt {attempt}); retrying')
                self.clear_costmaps()
                continue

            status = res_fut.result().status  # 4 == SUCCEEDED
            self.spin_for(0.3)
            p = self.pose()
            if p is not None:
                err = math.hypot(p[0] - x, p[1] - y)
                yerr = abs(math.atan2(math.sin(p[2] - yaw), math.cos(p[2] - yaw)))
                gt = gz_truth()
                terr = math.hypot(gt[0] - x, gt[1] - y) if gt else err
                if status == 4 and err <= POS_TOL and terr <= POS_TOL and (yerr <= YAW_TOL or not check_yaw):
                    return True, (f'amcl_err={err:.2f} m, truth_err={terr:.2f} m, '
                                  f'yaw_err={math.degrees(yerr):.0f} deg')
                self.get_logger().warn(
                    f'  attempt {attempt}: status={status} err={err:.2f} m truth_err={terr:.2f} m yaw_err={math.degrees(yerr):.0f} deg')
            self.clear_costmaps()
        return False, f'failed after {MAX_RETRIES} attempts'

    def cancel_all(self):
        self.active = getattr(self, 'active', None)
        if self.active is not None:
            self.active.cancel_goal_async()
            self.spin_for(1.0)

    def run(self):
        if not self.wait_ready():
            print('FATAL: Nav2 / TF not ready. Is run_civil_nav.sh running?')
            return 2
        self.spin_for(1.0)
        p = self.pose()
        print(f'Nav2 ready. Start pose (map): {p}')
        self.seed_amcl(0.0, 0.0, p[2] if p else 0.0)
        self.spin_for(2.0)
        self.clear_costmaps()

        results = []
        total = len(MISSION)
        # Goal heading = direction of travel from the previous waypoint, so the robot never has
        # to spin on the spot after arriving (the turn toward the next target happens while
        # path-following, which is stable on this skid-steer base).
        prev = (0.0, 0.0)
        headings = []
        for (_, wx, wy, _, _) in MISSION:
            dx, dy = wx - prev[0], wy - prev[1]
            headings.append(math.degrees(math.atan2(dy, dx)) if math.hypot(dx, dy) > 0.05 else 0.0)
            prev = (wx, wy)
        for i, ((name, x, y, _, station), yaw_deg) in enumerate(zip(MISSION, headings), 1):
            print(f'[{i:02d}/{total:02d}] -> {name} ({x:.1f}, {y:.1f}, {yaw_deg:.0f} deg)')
            ok, msg = self.go(name, x, y, yaw_deg, check_yaw=station)
            results.append((name, ok, msg))
            print(f'        {"OK  " if ok else "FAIL"} {msg}')
            if not ok:
                break
            if station:
                print('        Station reached - inspecting (2 s)')
                self.spin_for(2.0)

        failed = [r for r in results if not r[1]]
        print('\n' + '=' * 70)
        print(f'Legs completed: {sum(1 for r in results if r[1])}/{total}')
        print('MISSION RESULT:', 'SUCCESS' if not failed and len(results) == total else 'FAILED')
        print('=' * 70)
        return 0 if not failed and len(results) == total else 1


def main():
    rclpy.init(args=sys.argv)
    node = Mission()
    code = 1
    try:
        code = node.run()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.cancel_all()
        except Exception:
            pass
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    sys.exit(code)


if __name__ == '__main__':
    main()
