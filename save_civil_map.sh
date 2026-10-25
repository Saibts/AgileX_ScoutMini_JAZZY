#!/usr/bin/env bash
# ==============================================================================
# AgileX Scout Mini 4WD AMR — Save Generated 2D SLAM Civil Map
# ==============================================================================

echo "======================================================================"
echo "💾  AgileX Scout Mini: Saving Civil Floor 2D SLAM Occupancy Grid Map"
echo "======================================================================"

export ROS_DOMAIN_ID=19
export ROS_LOCALHOST_ONLY=1
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
source /opt/ros/jazzy/setup.bash
if [ -f "$HOME/agilex/install/setup.bash" ]; then
    source "$HOME/agilex/install/setup.bash"
fi

MAP_DIR="$HOME/agilex/src/assem2_robot/maps"
mkdir -p "$MAP_DIR"
MAP_NAME="${1:-civil_map}"
OUTPUT_PATH="$MAP_DIR/$MAP_NAME"

echo "⏳ Requesting map save from SLAM Toolbox service..."
ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap "{name: {data: '$OUTPUT_PATH'}}" 2>/dev/null || true

if [ ! -f "${OUTPUT_PATH}.yaml" ] || [ ! -f "${OUTPUT_PATH}.pgm" ]; then
    echo "⏳ Fallback: requesting map via map_saver_cli..."
    ros2 run nav2_map_server map_saver_cli -f "$OUTPUT_PATH" --ros-args -p use_sim_time:=true 2>/dev/null || true
fi

if [ -f "${OUTPUT_PATH}.yaml" ] && [ -f "${OUTPUT_PATH}.pgm" ]; then
    echo ""
    echo "✅ Map successfully saved to:"
    echo "   📄 YAML: ${OUTPUT_PATH}.yaml ($(wc -c < "${OUTPUT_PATH}.yaml") bytes)"
    echo "   🗺️  PGM:  ${OUTPUT_PATH}.pgm ($(wc -c < "${OUTPUT_PATH}.pgm") bytes)"
    echo "======================================================================"
else
    echo "⚠️  Map save could not be completed. Make sure SLAM Toolbox is actively running."
fi
