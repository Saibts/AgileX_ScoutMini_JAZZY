#!/usr/bin/env bash
# ==============================================================================
# AgileX Scout Mini 4WD AMR — Smooth Keyboard Teleoperation Controller
# ==============================================================================
# Supports WASD, Arrow Keys, and Classic ROS keys with smooth 20 Hz streaming.

export ROS_DOMAIN_ID=19
export ROS_LOCALHOST_ONLY=1
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST

source /opt/ros/jazzy/setup.bash
if [ -f "$HOME/agilex/install/setup.bash" ]; then
    source "$HOME/agilex/install/setup.bash"
fi

python3 "$HOME/agilex/src/assem2_robot/scripts/civil_teleop.py"
