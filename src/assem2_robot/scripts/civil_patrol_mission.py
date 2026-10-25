#!/usr/bin/env python3
"""
AgileX Scout Mini - Civil Engineering Multi-Room Autonomous Patrol Mission
Navigates across the 20m x 16m Civil Architectural Facility:
- Foyer & Atrium (Base) -> Central Corridor -> Materials Testing Lab -> 
  Conference Hall -> CAD & Robotics Studio -> Archives Vault -> Geotechnical Lab
"""

import time
import math
import rclpy
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

    print("\n" + "=" * 75)
    print("🏛️  AgileX Scout Mini: Civil Facility Multi-Room Autonomous Patrol")
    print("   Environment: 20m x 16m Civil Architectural Engineering Layout")
    print("=" * 75)

    # Wait until Nav2 is active
    print("[CIVIL PATROL] ⏳ Waiting for Nav2 navigation stack to become active...")
    navigator.waitUntilNav2Active()
    print("[CIVIL PATROL] ✅ Nav2 is ACTIVE and ready for autonomous mission!\n")

    # Defined Civil Stations (Unobstructed Free-Space Coordinates)
    stations = [
        {
            "name": "Station 1: Main Entrance Foyer & Atrium (Home)",
            "x": 0.0, "y": -3.8, "yaw": 90.0, "wait": 3.0,
            "desc": "Reception & AMR Staging Dock"
        },
        {
            "name": "Station 2: Central Arterial Corridor Hub",
            "x": 0.0, "y": 0.0, "yaw": 0.0, "wait": 2.0,
            "desc": "2.4m Main Building Thoroughfare"
        },
        {
            "name": "Station 3: Structural Materials & Concrete Testing Lab",
            "x": -7.0, "y": 3.5, "yaw": 90.0, "wait": 4.0,
            "desc": "Concrete Compression & Specimen Analysis Bay"
        },
        {
            "name": "Station 4: Civil Seminar & Executive Conference Hall",
            "x": 0.0, "y": 3.0, "yaw": 90.0, "wait": 3.0,
            "desc": "Central Meeting & Presentation Area"
        },
        {
            "name": "Station 5: BIM, CAD & Robotics Computing Studio",
            "x": 7.0, "y": 3.5, "yaw": 90.0, "wait": 4.0,
            "desc": "Digital Twin & Structural Simulation Workstations"
        },
        {
            "name": "Station 6: Department Archives & Equipment Vault",
            "x": 4.5, "y": -4.8, "yaw": 0.0, "wait": 3.0,
            "desc": "Surveying Equipment & Blueprint Storage"
        },
        {
            "name": "Station 7: Geotechnical Survey & Soil Mechanics Lab",
            "x": -4.5, "y": -5.0, "yaw": 180.0, "wait": 4.0,
            "desc": "Soil Core Sampling & Geotechnical Testing Rig"
        },
    ]

    patrol_round = 1

    try:
        while rclpy.ok():
            print(f"\n🔄 ==================== Starting Civil Patrol Loop #{patrol_round} ====================")
            
            for station in stations:
                print(f"\n🚀 [PATROL] Heading to: {station['name']}")
                print(f"   Zone: {station['desc']} | Target: ({station['x']:.2f}, {station['y']:.2f})")
                
                goal_pose = create_pose(navigator, station['x'], station['y'], station['yaw'])
                navigator.goToPose(goal_pose)

                step = 0
                while not navigator.isTaskComplete():
                    feedback = navigator.getFeedback()
                    if feedback and step % 6 == 0:
                        dist = feedback.distance_remaining
                        print(f"   📍 Distance to {station['name'].split(':')[1].strip()}: {dist:.2f} m | Navigating...")
                    time.sleep(0.5)
                    step += 1

                result = navigator.getResult()
                if result == TaskResult.SUCCEEDED:
                    print(f"   ✅ Successfully arrived at {station['name']}!")
                    print(f"   ⏳ Performing site inspection for {station['wait']:.0f} seconds...")
                    time.sleep(station['wait'])
                elif result == TaskResult.CANCELED:
                    print(f"   ⚠️ Navigation to {station['name']} was canceled.")
                elif result == TaskResult.FAILED:
                    print(f"   ❌ Path blocked or navigation failed at {station['name']}. Proceeding to next station...")

            patrol_round += 1

    except KeyboardInterrupt:
        print("\n🛑 Civil patrol mission interrupted by user. Stopping navigation...")
        navigator.cancelTask()

    navigator.lifecycleShutdown()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
