%% =========================================================================
%  AgileX Scout Mini: MATLAB <-> ROS 2 Jazzy Live Co-Simulation & Control
%  =========================================================================
%  Description:
%  Connects MATLAB directly to the live ROS 2 Jazzy Gazebo Harmonic simulation.
%  Subscribes to live sensor streams (/odometry/filtered, /scan, /imu,
%  /joint_states) and publishes /cmd_vel velocity commands with interactive
%  real-time telemetry.
%
%  Requirements:
%  - MATLAB with ROS Toolbox
%  - ROS 2 Jazzy running: ros2 launch assem2_robot simulation.launch.py
%  =========================================================================

clear; clc; close all;

% Ensure current directory is on MATLAB search path
matlabDir = fileparts(mfilename('fullpath'));
if ~isempty(matlabDir)
    addpath(matlabDir);
end

fprintf('===================================================================\n');
fprintf('🌐 AgileX Scout Mini: MATLAB <-> ROS 2 Jazzy Live Co-Simulation\n');
fprintf('===================================================================\n\n');

% Set ROS 2 Domain ID (Default is 0)
if isempty(getenv('ROS_DOMAIN_ID'))
    setenv('ROS_DOMAIN_ID', '0');
end

% 1. Create MATLAB ROS 2 Node
fprintf('[1/4] Initializing MATLAB ROS 2 Node...\n');
try
    node = ros2node('/matlab_scout_bridge');
catch ME
    error('Failed to create ROS 2 Node. Make sure ROS Toolbox is installed.\nError: %s', ME.message);
end

% 2. Create Publishers & Subscribers
fprintf('[2/4] Connecting to ROS 2 Topics...\n');
cmdPub   = ros2publisher(node, '/cmd_vel', 'geometry_msgs/Twist');
odomSub  = ros2subscriber(node, '/odometry/filtered', 'nav_msgs/Odometry');
scanSub  = ros2subscriber(node, '/scan', 'sensor_msgs/LaserScan');
imuSub   = ros2subscriber(node, '/imu', 'sensor_msgs/Imu');
jointSub = ros2subscriber(node, '/joint_states', 'sensor_msgs/JointState');

cmdMsg = ros2message(cmdPub);

% 3. Setup Multi-Panel Visualization Dashboard
fprintf('[3/4] Initializing Real-time Dashboard...\n');
fig = figure('Name', 'AgileX Scout Mini - MATLAB ROS 2 Live Dashboard', ...
             'NumberTitle', 'off', 'Color', [0.12 0.12 0.15], ...
             'Position', [60, 60, 1150, 720]);

% Arena Map Axes
axMap = subplot(3, 3, [1 2 4 5 7 8], 'Parent', fig);
hold(axMap, 'on'); grid(axMap, 'on'); axis(axMap, 'equal');
xlim(axMap, [-5.5, 5.5]); ylim(axMap, [-5.5, 5.5]);
title(axMap, 'Live Telemetry from Gazebo Harmonic / ROS 2 Jazzy', ...
      'Color', 'w', 'FontSize', 12, 'FontWeight', 'bold');
xlabel(axMap, 'X Position (meters)', 'Color', 'w');
ylabel(axMap, 'Y Position (meters)', 'Color', 'w');
set(axMap, 'Color', [0.08 0.08 0.10], 'GridColor', [0.3 0.3 0.35], 'XColor', 'w', 'YColor', 'w');

hRobot = plot(axMap, 0, 0, 'ro', 'MarkerSize', 10, 'MarkerFaceColor', 'r');
hScan  = plot(axMap, NaN, NaN, 'c.', 'MarkerSize', 3);
hPath  = plot(axMap, NaN, NaN, 'g-', 'LineWidth', 1.6);
hHead  = plot(axMap, NaN, NaN, 'y-', 'LineWidth', 2.5);

pathX = []; pathY = [];

% Telemetry Panel 1: Speeds
axSpeed = subplot(3, 3, 3, 'Parent', fig);
set(axSpeed, 'Color', [0.08 0.08 0.10], 'XColor', 'w', 'YColor', 'w');
speedCats = categorical({'Linear v', 'Angular \omega'});
speedCats = reordercats(speedCats, {'Linear v', 'Angular \omega'});
hBarSpeed = bar(axSpeed, speedCats, [0 0], 'FaceColor', [0.9 0.6 0.2]);
ylim(axSpeed, [-3.0, 3.0]); title(axSpeed, 'EKF Velocity', 'Color', 'w'); grid(axSpeed, 'on');

% Telemetry Panel 2: 4-Wheel Speeds
axWheels = subplot(3, 3, 6, 'Parent', fig);
set(axWheels, 'Color', [0.08 0.08 0.10], 'XColor', 'w', 'YColor', 'w');
wheelCats = categorical({'w1 (FR)', 'w2 (FL)', 'w3 (RR)', 'w4 (RL)'});
wheelCats = reordercats(wheelCats, {'w1 (FR)', 'w2 (FL)', 'w3 (RR)', 'w4 (RL)'});
hBarWheels = bar(axWheels, wheelCats, [0 0 0 0], 'FaceColor', [0.2 0.7 0.9]);
ylim(axWheels, [-360, 360]); title(axWheels, 'Wheel Speeds (RPM)', 'Color', 'w'); grid(axWheels, 'on');

% Telemetry Panel 3: Status HUD
axHUD = subplot(3, 3, 9, 'Parent', fig);
set(axHUD, 'Color', [0.08 0.08 0.10], 'XColor', 'none', 'YColor', 'none');
title(axHUD, 'ROS 2 Stream Telemetry', 'Color', 'w');
hHUD = text(axHUD, 0.05, 0.5, '', 'Color', 'w', 'FontSize', 9, 'FontName', 'Consolas');

fprintf('[4/4] Connected! Streaming Live Telemetry (Close figure to disconnect)...\n');

%% 4. Main Telemetry Streaming & Control Loop
try
    while ishandle(fig)
        % 1. Process Odometry
        odomMsg = odomSub.LatestMessage;
        x = 0; y = 0; yaw = 0; linV = 0; angW = 0;
        
        if ~isempty(odomMsg)
            x = odomMsg.pose.pose.position.x;
            y = odomMsg.pose.pose.position.y;
            
            % Quaternion to Euler Yaw
            qw = odomMsg.pose.pose.orientation.w;
            qz = odomMsg.pose.pose.orientation.z;
            qx = odomMsg.pose.pose.orientation.x;
            qy = odomMsg.pose.pose.orientation.y;
            
            siny_cosp = 2 * (qw * qz + qx * qy);
            cosy_cosp = 1 - 2 * (qy * qy + qz * qz);
            yaw = atan2(siny_cosp, cosy_cosp);
            
            linV = odomMsg.twist.twist.linear.x;
            angW = odomMsg.twist.twist.angular.z;
            
            pathX(end+1) = x;
            pathY(end+1) = y;
            
            set(hRobot, 'XData', x, 'YData', y);
            set(hHead,  'XData', [x, x + 0.45 * cos(yaw)], 'YData', [y, y + 0.45 * sin(yaw)]);
            set(hPath,  'XData', pathX, 'YData', pathY);
            set(hBarSpeed, 'YData', [linV, angW]);
        end
        
        % 2. Process LaserScan
        scanMsg = scanSub.LatestMessage;
        if ~isempty(scanMsg) && ~isempty(odomMsg)
            ranges = scanMsg.ranges;
            angles = scanMsg.angle_min : scanMsg.angle_increment : scanMsg.angle_max;
            angles = angles(1:min(length(ranges), length(angles)));
            ranges = ranges(1:length(angles));
            
            valid = ranges >= scanMsg.range_min & ranges <= scanMsg.range_max;
            validRanges = ranges(valid);
            validAngles = angles(valid);
            
            lx = x + validRanges .* cos(validAngles + yaw);
            ly = y + validRanges .* sin(validAngles + yaw);
            
            set(hScan, 'XData', lx, 'YData', ly);
        end
        
        % 3. Process Joint States (Wheel RPMs)
        jointMsg = jointSub.LatestMessage;
        wheelRPMs = [0, 0, 0, 0];
        if ~isempty(jointMsg) && numel(jointMsg.velocity) >= 4
            wheelRPMs = (jointMsg.velocity(1:4) / (2 * pi)) * 60;
            set(hBarWheels, 'YData', wheelRPMs);
        else
            % Estimate wheel RPM from linear & angular speed
            trackWidth = 0.612; wheelRadius = 0.080;
            vR = linV + (angW * trackWidth) / 2.0;
            vL = linV - (angW * trackWidth) / 2.0;
            rpmR = (vR / (2 * pi * wheelRadius)) * 60;
            rpmL = (vL / (2 * pi * wheelRadius)) * 60;
            set(hBarWheels, 'YData', [rpmR, rpmL, rpmR, rpmL]);
        end
        
        % 4. Update HUD Text
        hudStr = sprintf([ ...
            '🌐 ROS 2 Domain: %s\n' ...
            '📍 Pose:       [%.2f, %.2f, %.1f°]\n' ...
            '⚡ Lin Speed:   %.2f m/s\n' ...
            '🔄 Ang Speed:   %.2f rad/s\n' ...
            '🛰️ Scan Points: %d\n' ...
            '⚙️ Avg RPM:     %.0f'], ...
            getenv('ROS_DOMAIN_ID'), x, y, rad2deg(yaw), ...
            linV, angW, sum(valid), mean(abs(wheelRPMs)));
        set(hHUD, 'String', hudStr);
        
        drawnow limitrate;
        pause(0.04); % ~25 Hz loop
    end
catch ME
    fprintf('Bridge stopped: %s\n', ME.message);
end

% Safety Stop robot on exit
try
    cmdMsg.linear.x = 0.0;
    cmdMsg.angular.z = 0.0;
    send(cmdPub, cmdMsg);
catch
end

clear node;
fprintf('Disconnected from ROS 2.\n');
