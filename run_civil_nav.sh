#!/usr/bin/env bash
# ==============================================================================
# AgileX Scout Mini 4WD AMR — Clean Launcher for Civil Autonomous Navigation
# ==============================================================================
# 1. Kills any lingering/stale background simulation processes (preventing clock jumps)
# 2. Sources ROS 2 Jazzy and AgileX workspace setup
# 3. Launches Gazebo Harmonic, Nav2 Stack, RViz2, and Interactive Ground Station
# ==============================================================================

echo "======================================================================"
echo "🏛️  AgileX Scout Mini: Starting Civil Floor Autonomous Navigation"
echo "======================================================================"

# Clean up any stale simulation or bridge processes
echo "🧹 [1/3] Terminating any stale background simulation processes..."
killall -9 gz sim gz-sim-server gz_sim_server ruby parameter_bridge rviz2 robot_state_publisher ekf_node civil_interactive_nav component_container_isolated nav2_container 2>/dev/null || true
pkill -9 -f "ros2 launch" 2>/dev/null || true
# The ground station runs as a python3 process, so killall-by-name never matched it
for p in $(ps -eo pid,cmd | grep "[a]ssem2_robot/civil_interactive_nav" | awk '{print $1}'); do kill -9 "$p" 2>/dev/null || true; done
sleep 1.5

# Source ROS 2 Jazzy and local workspace
echo "📦 [2/3] Sourcing ROS 2 Jazzy and AgileX installation environment..."
export ROS_DOMAIN_ID=19
export ROS_LOCALHOST_ONLY=1
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_SIM_RESOURCE_PATH="$HOME/agilex/install/assem2_robot/share:$HOME/agilex/install/assem2_robot/share/assem2_robot:$GZ_SIM_RESOURCE_PATH"
export IGN_GAZEBO_RESOURCE_PATH="$HOME/agilex/install/assem2_robot/share:$HOME/agilex/install/assem2_robot/share/assem2_robot:$IGN_GAZEBO_RESOURCE_PATH"
source /opt/ros/jazzy/setup.bash
if [ -f "$HOME/agilex/install/setup.bash" ]; then
    source "$HOME/agilex/install/setup.bash"
else
    echo "⚠️ Warning: $HOME/agilex/install/setup.bash not found. Building first..."
    cd "$HOME/agilex" && colcon build --symlink-install && source "$HOME/agilex/install/setup.bash"
fi

# Trap Ctrl+C (SIGINT) to ensure clean shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down Civil Simulation and Ground Station cleanly..."
    killall -9 gz sim gz-sim-server gz_sim_server ruby parameter_bridge rviz2 robot_state_publisher ekf_node civil_interactive_nav component_container_isolated nav2_container 2>/dev/null || true
    pkill -9 -f "ros2 launch" 2>/dev/null || true
    for p in $(ps -eo pid,cmd | grep "[a]ssem2_robot/civil_interactive_nav" | awk '{print $1}'); do kill -9 "$p" 2>/dev/null || true; done
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "🚀 [3/3] Launching Civil Simulation with Nav2 and Interactive Ground Station..."
ros2 launch assem2_robot civil_simulation.launch.py use_nav:=true use_gui:=true "$@"
