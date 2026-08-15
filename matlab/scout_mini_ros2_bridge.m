%% =========================================================================
%  AgileX Scout Mini: MATLAB <-> ROS 2 Jazzy Live Co-Simulation & Control
%  =========================================================================
%  Description:
%  Connects MATLAB directly to the active ROS 2 Jazzy Gazebo simulation.
%  Reads live sensor streams (/odom, /scan, /camera) and publishes /cmd_vel.
%
%  Requirements:
%  - MATLAB with ROS Toolbox
%  - ROS 2 Jazzy running: ros2 launch assem2_robot simulation.launch.py
%  =========================================================================

clear; clc; close all;

fprintf('=======================================================\n');
fprintf('🌐 AgileX Scout Mini: MATLAB <-> ROS 2 Jazzy Bridge\n');
fprintf('=======================================================\n\n');

% Set ROS 2 Domain ID (Default is 0)
setenv('ROS_DOMAIN_ID', '0');

% 1. Create MATLAB ROS 2 Node
fprintf('[1/4] Initializing MATLAB ROS 2 Node...\n');
node = ros2node('/matlab_scout_controller');

% 2. Create Publishers & Subscribers
fprintf('[2/4] Connecting to ROS 2 Topics...\n');
cmdPub = ros2publisher(node, '/cmd_vel', 'geometry_msgs/Twist');
odomSub = ros2subscriber(node, '/odometry/filtered', 'nav_msgs/Odometry');
scanSub = ros2subscriber(node, '/scan', 'sensor_msgs/LaserScan');

cmdMsg = ros2message(cmdPub);

% 3. Setup Visualization Window in MATLAB
fprintf('[3/4] Initializing Real-time Dashboard...\n');
fig = figure('Name', 'AgileX Scout Mini - MATLAB ROS 2 Dashboard', 'Color', [0.15 0.15 0.18]);
ax = axes('Parent', fig, 'Color', [0.1 0.1 0.12]);
hold(ax, 'on'); grid(ax, 'on'); axis(ax, 'equal');
xlim(ax, [-5.5, 5.5]); ylim(ax, [-5.5, 5.5]);
title(ax, 'Live Telemetry from ROS 2 Gazebo Simulation', 'Color', 'w', 'FontSize', 12);
xlabel(ax, 'X (meters)', 'Color', 'w'); ylabel(ax, 'Y (meters)', 'Color', 'w');
set(ax, 'GridColor', [0.4 0.4 0.4], 'XColor', 'w', 'YColor', 'w');

hRobot = plot(ax, 0, 0, 'ro', 'MarkerSize', 10, 'MarkerFaceColor', 'r');
hScan  = plot(ax, NaN, NaN, 'c.', 'MarkerSize', 3);
hPath  = plot(ax, NaN, NaN, 'g-', 'LineWidth', 1.5);

pathX = []; pathY = [];

fprintf('[4/4] Connected! Streaming Live Telemetry (Press Ctrl+C in MATLAB to stop)...\n');

% 4. Main Control & Telemetry Streaming Loop
try
    while ishandle(fig)
        % Receive latest Odometry message
        odomMsg = odomSub.LatestMessage;
        if ~isempty(odomMsg)
            x = odomMsg.pose.pose.position.x;
            y = odomMsg.pose.pose.position.y;
            
            % Quaternion to Yaw
            qw = odomMsg.pose.pose.orientation.w;
            qz = odomMsg.pose.pose.orientation.z;
            yaw = 2 * atan2(qz, qw);
            
            pathX(end+1) = x;
            pathY(end+1) = y;
            
            set(hRobot, 'XData', x, 'YData', y);
            set(hPath,  'XData', pathX, 'YData', pathY);
        end
        
        % Receive latest LaserScan message
        scanMsg = scanSub.LatestMessage;
        if ~isempty(scanMsg) && ~isempty(odomMsg)
            ranges = scanMsg.ranges;
            angles = scanMsg.angle_min : scanMsg.angle_increment : scanMsg.angle_max;
            angles = angles(1:length(ranges));
            
            valid = ranges >= scanMsg.range_min & ranges <= scanMsg.range_max;
            validRanges = ranges(valid);
            validAngles = angles(valid);
            
            lx = x + validRanges .* cos(validAngles + yaw);
            ly = y + validRanges .* sin(validAngles + yaw);
            
            set(hScan, 'XData', lx, 'YData', ly);
        end
        
        drawnow limitrate;
        pause(0.05); % 20 Hz loop
    end
catch ME
    fprintf('Bridge stopped: %s\n', ME.message);
end

% Stop robot before exit
cmdMsg.linear.x = 0.0;
cmdMsg.angular.z = 0.0;
send(cmdPub, cmdMsg);
clear node;
fprintf('Disconnected from ROS 2.\n');
