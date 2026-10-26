#!/usr/bin/env bash
# ==============================================================================
# AgileX Scout Mini AMR — Autonomous Nav2 Mission with 1080p Screen Recording
# ==============================================================================
# 1. Starts a CLEAN Gazebo Harmonic + Nav2 + RViz2 + Ground Station session
#    (the mission assumes the robot starts at the world origin)
# 2. Waits for Nav2 to be fully active, tiles the windows for the camera
# 3. Records the desktop to MP4 (H.264) while the closed-loop Nav2 mission runs:
#    Conference Hall -> CAD Studio -> Materials Lab -> home, every arrival
#    verified against Gazebo ground truth
# 4. Saves the video and the mission report, exits with the mission's exit code
#
# Usage: ./run_patrol_and_record.sh [output.mp4] [--keep]   (--keep leaves the sim running)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

OUTPUT_VIDEO="$SCRIPT_DIR/recordings/agilex_civil_patrol_demo.mp4"
KEEP=false
for arg in "$@"; do
    case "$arg" in
        --keep) KEEP=true ;;
        *.mp4)  OUTPUT_VIDEO="$arg" ;;
    esac
done
REPORT="${OUTPUT_VIDEO%.mp4}_report.txt"
SIM_LOG="${OUTPUT_VIDEO%.mp4}_sim.log"
mkdir -p "$(dirname "$OUTPUT_VIDEO")"

echo "======================================================================"
echo "🎬 AgileX Scout Mini: Autonomous Nav2 Mission + Video Recording"
echo "   Video:  $OUTPUT_VIDEO"
echo "   Report: $REPORT"
echo "======================================================================"

export ROS_DOMAIN_ID=19
export ROS_LOCALHOST_ONLY=1
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
source /opt/ros/jazzy/setup.bash
source "$SCRIPT_DIR/install/setup.bash"

kill_sim() {
    for n in gz ruby parameter_bridge rviz2 robot_state_publisher ekf_node component_container_isolated; do
        killall -9 "$n" 2>/dev/null || true
    done
    # GUI runs as a python3 process, so it is not matched by name
    for p in $(ps -eo pid,cmd | grep "[a]ssem2_robot/civil_interactive_nav" | awk '{print $1}'); do
        kill -9 "$p" 2>/dev/null || true
    done
    killall -9 ros2 2>/dev/null || true
}

REC_PID=""
SIM_PID=""
cleanup() {
    if [ -n "$REC_PID" ] && kill -0 "$REC_PID" 2>/dev/null; then
        kill -INT "$REC_PID" 2>/dev/null || true
        wait "$REC_PID" 2>/dev/null || true
    fi
    if [ "$KEEP" = false ]; then
        kill_sim
        [ -n "$SIM_PID" ] && kill -9 "$SIM_PID" 2>/dev/null || true
    fi
    python3 "$SCRIPT_DIR/scripts/arrange_windows.py" --raise-terminal 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM

echo "🧹 [1/5] Stopping stale simulation processes..."
kill_sim
sleep 3

echo "🚀 [2/5] Starting Gazebo, Nav2, RViz2 and Ground Station..."
nohup setsid bash "$SCRIPT_DIR/run_civil_nav.sh" > "$SIM_LOG" 2>&1 < /dev/null &
SIM_PID=$!

echo "⏳ Waiting for Nav2 lifecycle to become active..."
if ! timeout 150 bash -c "until grep -q 'Managed nodes are active' '$SIM_LOG'; do sleep 2; done"; then
    echo "❌ Nav2 did not become active within 150 s (see $SIM_LOG)"
    exit 3
fi

echo "🪟 [3/5] Arranging windows for the camera..."
for _ in 1 2 3 4 5 6; do
    python3 "$SCRIPT_DIR/scripts/arrange_windows.py" && break
    sleep 2
done
sleep 3

echo "🎥 [4/5] Recording desktop..."
python3 "$SCRIPT_DIR/scripts/record_screen.py" --output "$OUTPUT_VIDEO" --fps 24 &
REC_PID=$!
sleep 3

echo "🤖 [5/5] Running closed-loop Nav2 mission..."
ros2 run assem2_robot civil_nav2_mission 2>&1 | grep --line-buffered -v -E "RTPS|deprecated|localhost_only" | tee "$REPORT"
MISSION_RC=${PIPESTATUS[0]}

echo "⏳ Capturing final frames..."
sleep 4
kill -INT "$REC_PID" 2>/dev/null || true
wait "$REC_PID" 2>/dev/null || true
REC_PID=""

echo ""
echo "======================================================================"
if [ "$MISSION_RC" -eq 0 ] && [ -s "$OUTPUT_VIDEO" ]; then
    echo "✅ MISSION SUCCESS — video saved: $OUTPUT_VIDEO ($(du -h "$OUTPUT_VIDEO" | cut -f1))"
else
    echo "❌ MISSION FAILED (exit $MISSION_RC) — see $REPORT and $SIM_LOG"
fi
echo "======================================================================"
exit "$MISSION_RC"
