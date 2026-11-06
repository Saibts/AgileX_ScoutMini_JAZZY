#!/usr/bin/env bash
# One command: rebuild, open Gazebo + RViz + Ground Station (slip world), then run the patrol.
# Usage: ./run_slip_demo.sh [--no-mission] [slip_correction:=false]
cd "$HOME/agilex" || exit 1
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select assem2_robot 2>&1 | tail -1
MISSION=1; ARGS=()
for a in "$@"; do [ "$a" = "--no-mission" ] && MISSION=0 || ARGS+=("$a"); done
WORLD="$HOME/agilex/install/assem2_robot/share/assem2_robot/worlds/civil_world_slip.sdf"
if [ "$MISSION" = 1 ]; then
  (
    export ROS_DOMAIN_ID=19 ROS_LOCALHOST_ONLY=1
    source /opt/ros/jazzy/setup.bash; source "$HOME/agilex/install/setup.bash"
    sleep 20
    until ros2 topic echo --once /amcl_pose >/dev/null 2>&1; do sleep 3; done
    sleep 5
    ros2 run assem2_robot civil_nav2_mission
  ) &
fi
./run_civil_nav.sh world:="$WORLD" "${ARGS[@]}"
