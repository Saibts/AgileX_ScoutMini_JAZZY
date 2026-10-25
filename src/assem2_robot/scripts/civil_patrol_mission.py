#!/usr/bin/env python3
"""
AgileX Scout Mini - Civil Engineering Multi-Room Autonomous Patrol Mission
Navigates across the 20m x 16m Civil Architectural Facility:
- Foyer & Atrium (Base) -> Central Corridor -> Materials Testing Lab -> 
  Conference Hall -> CAD & Robotics Studio -> Archives Vault -> Geotechnical Lab
"""

import sys
import os
import time
import math

# Local ROS domain isolation matching launch files
os.environ.setdefault('ROS_DOMAIN_ID', '19')
os.environ.setdefault('ROS_LOCALHOST_ONLY', '1')
os.environ.setdefault('ROS_AUTOMATIC_DISCOVERY_RANGE', 'LOCALHOST')

import rclpy
from rclpy.parameter import Parameter
from rclpy.time import Time
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


def create_pose(navigator, x, y, yaw_degrees):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    # Zero timestamp tells ROS TF to use the latest available transform
    pose.header.stamp = Time(seconds=0, nanoseconds=0).to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.position.z = 0.0

    # Convert yaw from degrees to quaternion
    yaw_rad = math.radians(yaw_degrees)
    pose.pose.orientation.x = 0.0
    pose.pose.orientation.y = 0.0
    pose.pose.orientation.z = math.sin(yaw_rad / 2.0)
    pose.pose.orientation.w = math.cos(yaw_rad / 2.0)
    return pose


def main():
    rclpy.init(args=sys.argv)
    navigator = BasicNavigator()

    # Synchronize simulation clock with Gazebo
    if not navigator.has_parameter('use_sim_time'):
        navigator.declare_parameter('use_sim_time', True)
    else:
        navigator.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, True)])

    print("\n" + "=" * 75)
    print("🏛️  AgileX Scout Mini: Civil Facility Multi-Room Autonomous Patrol")
    print("   Environment: 20m x 16m Civil Architectural Engineering Layout")
    print("===========================================================================")

    # Wait until Nav2 is active
    print("[CIVIL PATROL] ⏳ Waiting for Nav2 navigation stack to become active...")
    navigator.waitUntilNav2Active()
    print("[CIVIL PATROL] ✅ Nav2 is ACTIVE and ready for autonomous mission!\n")

    # Clear initial costmap artifacts
    try:
        navigator.clearAllCostmaps()
        time.sleep(0.5)
    except Exception:
        pass

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
                
                max_retries = 2
                arrived = False

                for attempt in range(max_retries + 1):
                    navigator.goToPose(goal_pose)

                    step = 0
                    while not navigator.isTaskComplete():
                        feedback = navigator.getFeedback()
                        if feedback and step % 4 == 0:
                            dist = feedback.distance_remaining
                            print(f"   📍 Distance: {dist:.2f} m | Navigating autonomously...")
                        time.sleep(0.5)
                        step += 1

                    result = navigator.getResult()
                    if result == TaskResult.SUCCEEDED:
                        print(f"   ✅ Successfully arrived at {station['name']}!")
                        print(f"   ⏳ Performing site inspection for {station['wait']:.0f} seconds...")
                        time.sleep(station['wait'])
                        arrived = True
                        break
                    elif result == TaskResult.CANCELED:
                        print(f"   ⚠️ Navigation to {station['name']} was canceled.")
                        break
                    else:
                        if attempt < max_retries:
                            print(f"   ⚠️ Path obstructed, clearing costmaps and retrying ({attempt+1}/{max_retries})...")
                            try:
                                navigator.clearAllCostmaps()
                            except Exception:
                                pass
                            time.sleep(1.5)
                        else:
                            print(f"   ❌ Could not reach {station['name']} after retries. Proceeding to next station...")

            patrol_round += 1

    except KeyboardInterrupt:
        print("\n🛑 Civil patrol mission interrupted by user. Stopping navigation...")
        try:
            navigator.cancelTask()
        except Exception:
            pass

    try:
        navigator.destroy_node()
        rclpy.shutdown()
    except Exception:
        pass


if __name__ == '__main__':
    main()
