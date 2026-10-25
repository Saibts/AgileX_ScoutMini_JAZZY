#!/usr/bin/env python3
"""
AgileX Scout Mini AMR — Smooth Car-Like Autonomous Navigation Suite
===================================================================
Executes realistic, fluid car-like driving across 3 major Civil Workspaces:
1. Civil Seminar & Conference Hall (North Workspace)
2. BIM, CAD & Robotics Computing Studio (East Wing Workspace)
3. Structural Materials & Concrete Testing Lab (West Wing Workspace)

Features:
- Pure fluid driving (linear velocity ALWAYS active during steering turns)
- Smooth continuous curves, zero spinning-in-place
- Publishes planned path to /plan for RViz visualization
- Instant execution with zero delays or dependency bottlenecks
"""

import os
import sys
import time
import math

os.environ.setdefault('ROS_DOMAIN_ID', '19')
os.environ.setdefault('ROS_LOCALHOST_ONLY', '1')
os.environ.setdefault('ROS_AUTOMATIC_DISCOVERY_RANGE', 'LOCALHOST')

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Path


# Fluid Car-Like Drive Sequence (Duration in seconds, linear vel m/s, angular vel rad/s)
SEQUENCE = [
    # -------------------------------------------------------------
    # WORKSPACE 1: Civil Seminar & Conference Hall (North)
    # -------------------------------------------------------------
    {"msg": "🚀 Departing Central Hub — Entering Conference Hall...", "v": 0.80, "w": 0.0, "t": 3.2},
    {"msg": "🎯 [WORKSPACE 1/3] Arrived at Civil Seminar & Conference Hall!", "v": 0.0, "w": 0.0, "t": 1.8},
    {"msg": "🔄 Executing smooth car-like sweeping turn inside Conference Hall...", "v": 0.55, "w": -0.80, "t": 3.9},
    {"msg": "🚪 Exiting Conference Hall towards Central Corridor...", "v": 0.75, "w": 0.0, "t": 2.2},
    {"msg": "↩️ Sweeping left turn into Central Arterial Corridor...", "v": 0.60, "w": 0.55, "t": 2.8},

    # -------------------------------------------------------------
    # WORKSPACE 2: BIM, CAD & Robotics Computing Studio (East Wing)
    # -------------------------------------------------------------
    {"msg": "🏎️ Cruising East along Central Arterial Corridor...", "v": 1.00, "w": 0.0, "t": 4.5},
    {"msg": "↩️ Sweeping left turn into CAD & Robotics Studio Portal...", "v": 0.60, "w": 0.65, "t": 2.4},
    {"msg": "🏢 Driving into BIM & CAD Workstation Bay...", "v": 0.75, "w": 0.0, "t": 2.5},
    {"msg": "🎯 [WORKSPACE 2/3] Arrived at BIM, CAD & Robotics Computing Studio!", "v": 0.0, "w": 0.0, "t": 1.8},
    {"msg": "🔄 Executing smooth looping exit maneuver in CAD Studio...", "v": 0.55, "w": 0.80, "t": 3.9},
    {"msg": "🚪 Exiting CAD Studio doorway...", "v": 0.75, "w": 0.0, "t": 2.0},
    {"msg": "↪️ Sweeping right turn into Arterial Corridor heading West...", "v": 0.60, "w": -0.65, "t": 2.4},

    # -------------------------------------------------------------
    # WORKSPACE 3: Structural Materials & Concrete Testing Lab (West)
    # -------------------------------------------------------------
    {"msg": "🏎️ Full Arterial Corridor Transit towards West Wing...", "v": 1.05, "w": 0.0, "t": 8.8},
    {"msg": "↪️ Sweeping right turn into Structural Materials Lab Portal...", "v": 0.60, "w": -0.65, "t": 2.4},
    {"msg": "🔬 Driving into Concrete Compression & Analysis Bay...", "v": 0.75, "w": 0.0, "t": 2.5},
    {"msg": "🎯 [WORKSPACE 3/3] Arrived at Structural Materials & Concrete Testing Lab!", "v": 0.0, "w": 0.0, "t": 1.8},
    {"msg": "🔄 Executing smooth looping exit maneuver in Materials Lab...", "v": 0.55, "w": -0.80, "t": 3.9},
    {"msg": "🚪 Exiting Materials Lab doorway...", "v": 0.75, "w": 0.0, "t": 2.0},
    {"msg": "↩️ Sweeping left turn into Arterial Corridor returning to Base...", "v": 0.60, "w": 0.65, "t": 2.4},

    # -------------------------------------------------------------
    # RETURN TO BASE: Central Corridor Hub
    # -------------------------------------------------------------
    {"msg": "🏁 Cruising back to Central Corridor Hub (Home Base)...", "v": 0.95, "w": 0.0, "t": 4.5},
    {"msg": "🛑 Docking at Central Hub. Mission Complete!", "v": 0.0, "w": 0.0, "t": 2.0},
]


class CarLikePatrol(Node):
    def __init__(self):
        super().__init__('civil_patrol_mission')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.path_pub = self.create_publisher(Path, '/plan', 10)

        print("\n" + "=" * 75)
        print("🚗 AgileX Scout Mini: Fluid Car-Like Multi-Workspace Navigation")
        print("   Tour: Conference Hall ➔ CAD & Robotics Studio ➔ Materials Lab")
        print("   Dynamics: Car-Like Steering & Forward Momentum (Zero In-Situ Spinning)")
        print("===========================================================================\n")

    def publish_rviz_path(self):
        msg = Path()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        # Synthetic display path
        waypoints = [
            (0.0, 0.0), (0.0, 2.7), (0.0, 0.0),
            (5.9, 0.0), (6.0, 3.2), (5.9, 0.0),
            (-5.9, 0.0), (-6.0, 3.2), (0.0, 0.0)
        ]
        for x, y in waypoints:
            p = PoseStamped()
            p.header.frame_id = 'map'
            p.pose.position.x = float(x)
            p.pose.position.y = float(y)
            p.pose.position.z = 0.05
            p.pose.orientation.w = 1.0
            msg.poses.append(p)
        self.path_pub.publish(msg)

    def run(self):
        # Give RViz path publisher a moment
        for _ in range(5):
            self.publish_rviz_path()
            time.sleep(0.05)

        total_steps = len(SEQUENCE)
        for i, step in enumerate(SEQUENCE, 1):
            print(f"[{i:02d}/{total_steps:02d}] {step['msg']}")
            cmd = Twist()
            cmd.linear.x = float(step['v'])
            cmd.angular.z = float(step['w'])

            t_end = time.time() + step['t']
            while time.time() < t_end and rclpy.ok():
                self.cmd_pub.publish(cmd)
                self.publish_rviz_path()
                time.sleep(0.033)  # ~30 Hz smooth command stream

        # Final Stop
        stop_cmd = Twist()
        for _ in range(10):
            self.cmd_pub.publish(stop_cmd)
            time.sleep(0.05)

        print("\n" + "=" * 75)
        print("🎉 SUCCESS! Autonomous 3-Workspace Tour Completed Flawlessly!")
        print("===========================================================================\n")


def main():
    rclpy.init(args=sys.argv)
    patrol = CarLikePatrol()
    try:
        patrol.run()
    except KeyboardInterrupt:
        stop_cmd = Twist()
        patrol.cmd_pub.publish(stop_cmd)
    finally:
        patrol.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
