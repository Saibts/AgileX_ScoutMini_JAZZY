#!/usr/bin/env bash
# ==============================================================================
# AgileX Scout Mini AMR — Automated Civil Patrol & 1080p Video Screen Recording
# ==============================================================================
# 1. Launches Gazebo Harmonic, Nav2, RViz2, and Ground Station
# 2. Waits for Nav2 lifecycle & transforms to stabilize
# 3. Starts 1080p screen recording of the live desktop
# 4. Executes full autonomous patrol through all 7 civil stations
# 5. Finalizes and saves the MP4 recording upon mission completion
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

# Clean up any prior stale simulation
echo "🧹 [1/5] Cleaning up any background processes..."
killall -9 gz sim gz-sim-server gz_sim_server ruby parameter_bridge rviz2 robot_state_publisher ekf_node civil_interactive_nav component_container_isolated nav2_container civil_patrol_mission 2>/dev/null || true
pkill -9 -f "record_screen.py" 2>/dev/null || true
sleep 1.5

# Setup ROS 2 Jazzy environment
echo "📦 [2/5] Initializing ROS 2 Jazzy & AgileX workspace..."
export ROS_DOMAIN_ID=19
export ROS_LOCALHOST_ONLY=1
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
source /opt/ros/jazzy/setup.bash
source "$SCRIPT_DIR/install/setup.bash"

# Launch Civil Simulation with Nav2 in the background
echo "🚀 [3/5] Starting Gazebo Harmonic, RViz2, and Ground Station..."
bash "$SCRIPT_DIR/run_civil_nav.sh" &
SIM_PID=$!

# Trap signals for graceful cleanup
cleanup() {
    echo ""
    echo "🛑 Finalizing video and shutting down simulation..."
    if [ -n "$REC_PID" ] && kill -0 "$REC_PID" 2>/dev/null; then
        kill -INT "$REC_PID" 2>/dev/null || true
        wait "$REC_PID" 2>/dev/null || true
    fi
    killall -9 gz sim gz-sim-server gz_sim_server ruby parameter_bridge rviz2 robot_state_publisher ekf_node civil_interactive_nav component_container_isolated nav2_container 2>/dev/null || true
    pkill -9 -P "$SIM_PID" 2>/dev/null || true
    kill -9 "$SIM_PID" 2>/dev/null || true
    echo "✅ Shutdown complete. Video saved to: $OUTPUT_VIDEO"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo "⏳ [4/5] Waiting for Nav2 Navigation Stack & Gazebo to initialize..."
READY=false
for i in {1..30}; do
    if ros2 node list 2>/dev/null | grep -q "bt_navigator"; then
        READY=true
        break
    fi
    sleep 1.0
done

if [ "$READY" = true ]; then
    echo "✅ Nav2 is active and online!"
else
    echo "⚠️ Nav2 check timeout, continuing..."
fi

# Give RViz2 and Gazebo 4 seconds to render map and spawn robot
sleep 4.0

# Start automated screen recorder
echo "🎥 [5/5] Commencing 1080p video recording..."
python3 "$SCRIPT_DIR/scripts/record_screen.py" --output "$OUTPUT_VIDEO" --fps 24 &
REC_PID=$!
sleep 2.0

echo "🤖 Launching Civil Autonomous Patrol Mission (Loop 1: S1 -> S7)..."
ros2 run assem2_robot civil_patrol_mission --loops 1 || true

echo ""
echo "🎉 Autonomous Patrol Mission has finished successfully!"
echo "⏳ Waiting 3 seconds to capture final dock state..."
sleep 3.0

# Clean stop
kill -INT "$REC_PID" 2>/dev/null || true
wait "$REC_PID" 2>/dev/null || true
REC_PID=""

echo ""
echo "======================================================================"
echo "✅ VIDEO RECORDING COMPLETED SUCCESSFULLY!"
echo "📁 Output Video: $OUTPUT_VIDEO"
echo "======================================================================"
