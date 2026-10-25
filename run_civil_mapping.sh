#!/usr/bin/env bash
# ==============================================================================
# AgileX Scout Mini 4WD AMR — Clean Launcher for Civil Floor 2D SLAM Mapping
# ==============================================================================

echo "======================================================================"
echo "🗺️  AgileX Scout Mini: Starting Civil Floor 2D SLAM Mapping Mode"
echo "======================================================================"

echo "🧹 [1/3] Terminating any stale background simulation processes..."
killall -9 gz sim gz-sim-server gz_sim_server ruby parameter_bridge rviz2 robot_state_publisher ekf_node civil_interactive_nav async_slam_toolbox_node 2>/dev/null || true
sleep 1.0

echo "📦 [2/3] Sourcing ROS 2 Jazzy and AgileX installation environment..."
export ROS_DOMAIN_ID=19
export ROS_LOCALHOST_ONLY=1
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
source /opt/ros/jazzy/setup.bash
if [ -f "$HOME/agilex/install/setup.bash" ]; then
    source "$HOME/agilex/install/setup.bash"
fi

cleanup() {
    echo ""
    echo "🛑 Shutting down Civil SLAM Simulation cleanly..."
    killall -9 gz sim gz-sim-server gz_sim_server ruby parameter_bridge rviz2 robot_state_publisher ekf_node civil_interactive_nav async_slam_toolbox_node 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "🚀 [3/3] Launching Civil Simulation with SLAM Toolbox..."
ros2 launch assem2_robot civil_simulation.launch.py use_slam:=true "$@"
