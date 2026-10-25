#!/usr/bin/env bash
# ==============================================================================
# AgileX Scout Mini AMR — Automated Civil Patrol & 1080p Video Screen Recording
# ==============================================================================
# 1. Detects or launches Gazebo Harmonic, Nav2, RViz2, and Ground Station
# 2. Starts 1080p screen recording of the live desktop
# 3. Executes deterministic multi-room patrol through all 7 civil stations
# 4. Finalizes and saves the MP4 recording upon mission completion
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

OUTPUT_VIDEO="${1:-$SCRIPT_DIR/recordings/agilex_civil_patrol_demo.mp4}"
mkdir -p "$(dirname "$OUTPUT_VIDEO")"

echo "======================================================================"
echo "🎬 AgileX Scout Mini: Automated Patrol & Video Recording Suite"
echo "   Output Video: $OUTPUT_VIDEO"
echo "======================================================================"

# Setup ROS 2 Jazzy environment
export ROS_DOMAIN_ID=19
export ROS_LOCALHOST_ONLY=1
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
source /opt/ros/jazzy/setup.bash
source "$SCRIPT_DIR/install/setup.bash"

ALREADY_RUNNING=false
SIM_PID=""

if pgrep -f "gz sim" > /dev/null; then
    ALREADY_RUNNING=true
    echo "⚡ Detected existing active simulation session on desktop. Reusing live session!"
else
    echo "🧹 [1/4] Cleaning up any background processes..."
    killall -9 gz sim gz-sim-server gz_sim_server ruby parameter_bridge rviz2 robot_state_publisher ekf_node civil_interactive_nav component_container_isolated nav2_container civil_patrol_mission 2>/dev/null || true
    pkill -9 -f "record_screen.py" 2>/dev/null || true
    sleep 1.0

    echo "🚀 [2/4] Starting Gazebo Harmonic, RViz2, and Ground Station..."
    bash "$SCRIPT_DIR/run_civil_nav.sh" &
    SIM_PID=$!

    echo "⏳ Waiting for simulation and odometry to initialize..."
    sleep 8.0
fi

# Trap signals for graceful cleanup
cleanup() {
    echo ""
    echo "🛑 Finalizing video recording..."
    if [ -n "$REC_PID" ] && kill -0 "$REC_PID" 2>/dev/null; then
        kill -INT "$REC_PID" 2>/dev/null || true
        wait "$REC_PID" 2>/dev/null || true
    fi
    if [ "$ALREADY_RUNNING" = false ] && [ -n "$SIM_PID" ]; then
        killall -9 gz sim gz-sim-server gz_sim_server ruby parameter_bridge rviz2 robot_state_publisher ekf_node civil_interactive_nav component_container_isolated nav2_container 2>/dev/null || true
        pkill -9 -P "$SIM_PID" 2>/dev/null || true
        kill -9 "$SIM_PID" 2>/dev/null || true
    fi
    echo "✅ Video finalized and saved to: $OUTPUT_VIDEO"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start automated screen recorder
echo "🎥 [3/4] Commencing 1080p desktop video recording..."
python3 "$SCRIPT_DIR/scripts/record_screen.py" --output "$OUTPUT_VIDEO" --fps 24 &
REC_PID=$!
sleep 2.0

echo "🤖 [4/4] Launching Civil Autonomous Patrol Mission (Visiting all 7 stations)..."
ros2 run assem2_robot civil_patrol_mission --loops 1 || true

echo ""
echo "🎉 Autonomous Patrol Mission has finished successfully!"
echo "⏳ Waiting 3 seconds to capture final dock state..."
sleep 3.0

# Stop recorder cleanly
kill -INT "$REC_PID" 2>/dev/null || true
wait "$REC_PID" 2>/dev/null || true
REC_PID=""

echo ""
echo "======================================================================"
echo "✅ VIDEO RECORDING COMPLETED SUCCESSFULLY!"
echo "📁 Saved to: $OUTPUT_VIDEO"
echo "======================================================================"
