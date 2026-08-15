#!/usr/bin/env python3

import time
import math
import rclpy
from rclpy.duration import Duration
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


def create_pose(navigator, x, y, yaw_degrees):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.position.z = 0.0

    # Convert yaw from degrees to quaternion
    yaw_rad = math.radians(yaw_degrees)
    pose.pose.orientation.z = math.sin(yaw_rad / 2.0)
    pose.pose.orientation.w = math.cos(yaw_rad / 2.0)
    return pose


def main():
    rclpy.init()
    navigator = BasicNavigator()

    print("\n" + "="*65)
    print("🤖 AgileX Scout Mini: Autonomous AMR Multi-Station Patrol Mission")
    print("="*65)

    # Wait until Nav2 is fully active
    print("[AMR PATROL] ⏳ Waiting for Nav2 stack to become active...")
    navigator.waitUntilNav2Active()
    print("[AMR PATROL] ✅ Nav2 is ACTIVE and ready!\n")

    # Define Patrol Stations inside the 10m x 10m Arena
    stations = [
        {"name": "Station A (Docking / Charging Base)", "x": 0.0, "y": 0.0, "yaw": 0.0, "wait": 2.0},
        {"name": "Station B (Loading Zone)", "x": 1.5, "y": 1.5, "yaw": 90.0, "wait": 3.0},
        {"name": "Station C (Inspection Point)", "x": -1.5, "y": 1.5, "yaw": 180.0, "wait": 2.0},
        {"name": "Station D (Unloading Area)", "x": -1.5, "y": -1.5, "yaw": -90.0, "wait": 3.0},
        {"name": "Station E (Perimeter Checkpoint)", "x": 1.5, "y": -1.5, "yaw": 0.0, "wait": 2.0},
    ]

    patrol_count = 1

    try:
        while rclpy.ok():
            print(f"\n🔄 --- Starting Patrol Loop #{patrol_count} ---")
            
            for station in stations:
                print(f"\n🚀 [PATROL] Heading to {station['name']} -> ({station['x']:.1f}, {station['y']:.1f})...")
                goal_pose = create_pose(navigator, station['x'], station['y'], station['yaw'])
                
                navigator.goToPose(goal_pose)

                i = 0
                while not navigator.isTaskComplete():
                    feedback = navigator.getFeedback()
                    if feedback and i % 5 == 0:
                        distance_remaining = feedback.distance_remaining
                        print(f"   📍 Distance remaining: {distance_remaining:.2f} m | Navigating autonomously...")
                    time.sleep(0.5)
                    i += 1

                result = navigator.getResult()
                if result == TaskResult.SUCCEEDED:
                    print(f"   ✅ Arrived at {station['name']}!")
                    print(f"   ⏳ Waiting {station['wait']:.0f} seconds (Simulating Operation)...")
                    time.sleep(station['wait'])
                elif result == TaskResult.CANCELED:
                    print(f"   ⚠️ Navigation to {station['name']} was canceled.")
                elif result == TaskResult.FAILED:
                    print(f"   ❌ Navigation to {station['name']} failed! Attempting recovery to next station...")

            patrol_count += 1

    except KeyboardInterrupt:
        print("\n🛑 Patrol mission interrupted by user. Canceling active goal...")
        navigator.cancelTask()

    navigator.lifecycleShutdown()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
