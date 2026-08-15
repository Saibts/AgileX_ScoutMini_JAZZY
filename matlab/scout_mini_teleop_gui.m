%% =========================================================================
%  AgileX Scout Mini 4WD AMR: Interactive Teleoperation & Goal Dispatcher GUI
%  =========================================================================
%  Description:
%  Interactive MATLAB dashboard allowing direct keyboard teleoperation (W/A/S/D)
%  or click-to-navigate autonomous waypoint dispatching in the obstacle arena.
%
%  Controls:
%  - [W] or [↑] : Accelerate Forward
%  - [S] or [↓] : Accelerate Backward
%  - [A] or [←] : Turn Left (Skid-Steer Spin in place)
%  - [D] or [→] : Turn Right (Skid-Steer Spin in place)
%  - [SPACE]    : Emergency Stop / Active Brake
%  - [MOUSE]    : Click anywhere on the map to dispatch autonomous goal
%  - [M]        : Toggle between MANUAL and AUTONOMOUS Navigation modes
%  =========================================================================

clear; clc; close all;

% Ensure current directory is on MATLAB search path
matlabDir = fileparts(mfilename('fullpath'));
if ~isempty(matlabDir)
    addpath(matlabDir);
end

fprintf('===================================================================\n');
fprintf('🎮 AgileX Scout Mini: Interactive Teleoperation & Goal GUI\n');
fprintf('===================================================================\n\n');

%% 1. Initialize Arena Map
map = binaryOccupancyMap(10, 10, 20);
map.GridLocationInWorld = [-5, -5];

% Boundaries
setOccupancy(map, [-5:0.05:5;  5*ones(1, 201)]', 1);
setOccupancy(map, [-5:0.05:5; -5*ones(1, 201)]', 1);
setOccupancy(map, [ 5*ones(1, 201); -5:0.05:5]', 1);
setOccupancy(map, [-5*ones(1, 201); -5:0.05:5]', 1);

% Obstacles
[xP1, yP1] = meshgrid(-0.35:0.05:0.35, -0.35:0.05:0.35);
circMask = (xP1.^2 + yP1.^2) <= 0.35^2;
setOccupancy(map, [2.0 + xP1(circMask),  2.0 + yP1(circMask)], 1);
setOccupancy(map, [-2.0 + xP1(circMask), -2.0 + yP1(circMask)], 1);

[xB1, yB1] = meshgrid(-0.4:0.05:0.4, -0.6:0.05:0.6);
setOccupancy(map, [2.5 + xB1(:), -2.0 + yB1(:)], 1);
[xB2, yB2] = meshgrid(-0.5:0.05:0.5, -0.5:0.05:0.5);
setOccupancy(map, [-2.5 + xB2(:), 2.0 + yB2(:)], 1);

robotRadius = 0.35;
inflatedMap = copy(map);
inflate(inflatedMap, robotRadius);

%% 2. Instantiate Robot & Controller
robot = ScoutMiniRobot([0; 0; 0]);
hasVFH = exist('controllerVFH', 'class') == 8;
if hasVFH
    vfh = controllerVFH;
    vfh.DistanceLimits          = [0.15, 5.0];
    vfh.RobotRadius             = robotRadius;
    vfh.SafetyDistance          = 0.15;
    vfh.MinTurningRadius        = 0.05;
    vfh.TargetDirectionWeight   = 5.0;
    vfh.CurrentDirectionWeight  = 2.0;
    vfh.PreviousDirectionWeight = 2.0;
end

%% 3. Global Control State Variables
global keyCmd mode goalPoint isRunning
keyCmd.v     = 0.0;
keyCmd.omega = 0.0;
mode         = 'MANUAL'; % 'MANUAL' or 'AUTO'
goalPoint    = [0, 0];
isRunning    = true;

%% 4. Setup GUI Window
fig = figure('Name', 'AgileX Scout Mini - Interactive Teleop & Mission GUI', ...
             'NumberTitle', 'off', 'Color', [0.12 0.12 0.15], ...
             'Position', [80, 80, 1100, 700], ...
             'KeyPressFcn', @onKeyPress, ...
             'KeyReleaseFcn', @onKeyRelease, ...
             'CloseRequestFcn', @onClose);

axMap = subplot(3, 3, [1 2 4 5 7 8], 'Parent', fig);
hold(axMap, 'on'); axis(axMap, 'equal'); grid(axMap, 'on');
set(axMap, 'Color', [0.08 0.08 0.10], 'GridColor', [0.3 0.3 0.35], ...
    'XColor', 'w', 'YColor', 'w');
xlim(axMap, [-5.5, 5.5]); ylim(axMap, [-5.5, 5.5]);
title(axMap, '🎮 Click on Map to set Goal | Use [W/A/S/D] to Drive | [M] to Toggle Mode', ...
      'Color', 'y', 'FontSize', 11, 'FontWeight', 'bold');
xlabel(axMap, 'X (m)', 'Color', 'w'); ylabel(axMap, 'Y (m)', 'Color', 'w');

show(map, 'Parent', axMap);
set(fig, 'WindowButtonDownFcn', @(src, evt) onMapClick(axMap));

% Graphic Handles
hTrail  = plot(axMap, NaN, NaN, 'g-', 'LineWidth', 1.8);
hLidar  = plot(axMap, NaN, NaN, 'c.', 'MarkerSize', 4);
hGoal   = plot(axMap, NaN, NaN, 'yp', 'MarkerSize', 16, 'MarkerFaceColor', 'y', 'MarkerEdgeColor', 'k');
hBody   = fill(axMap, NaN, NaN, [0.8 0.2 0.2], 'FaceAlpha', 0.85, 'EdgeColor', 'w', 'LineWidth', 1.5);
hHead   = plot(axMap, NaN, NaN, 'y-', 'LineWidth', 2.5);

hWheels = cell(4, 1);
for i = 1:4
    hWheels{i} = fill(axMap, NaN, NaN, [0.2 0.2 0.2], 'FaceAlpha', 0.95, 'EdgeColor', [0.9 0.8 0.1], 'LineWidth', 1.2);
end

% Telemetry: 4-Wheel RPMs
axRPM = subplot(3, 3, 3, 'Parent', fig);
set(axRPM, 'Color', [0.08 0.08 0.10], 'XColor', 'w', 'YColor', 'w');
wheelCats = categorical({'FL', 'FR', 'RL', 'RR'});
wheelCats = reordercats(wheelCats, {'FL', 'FR', 'RL', 'RR'});
hBarRPM = bar(axRPM, wheelCats, [0 0 0 0], 'FaceColor', [0.2 0.7 0.9]);
ylim(axRPM, [-360, 360]); title(axRPM, 'Wheel RPMs', 'Color', 'w'); grid(axRPM, 'on');

% Telemetry: Speeds
axSpeed = subplot(3, 3, 6, 'Parent', fig);
set(axSpeed, 'Color', [0.08 0.08 0.10], 'XColor', 'w', 'YColor', 'w');
speedCats = categorical({'Lin v (m/s)', 'Ang \omega (rad/s)'});
speedCats = reordercats(speedCats, {'Lin v (m/s)', 'Ang \omega (rad/s)'});
hBarSpeed = bar(axSpeed, speedCats, [0 0], 'FaceColor', [0.9 0.6 0.2]);
ylim(axSpeed, [-3.0, 3.0]); title(axSpeed, 'Velocity', 'Color', 'w'); grid(axSpeed, 'on');

% HUD Text
axHUD = subplot(3, 3, 9, 'Parent', fig);
set(axHUD, 'Color', [0.08 0.08 0.10], 'XColor', 'none', 'YColor', 'none');
title(axHUD, 'Status HUD', 'Color', 'w');
hHUD = text(axHUD, 0.05, 0.5, '', 'Color', 'w', 'FontSize', 9, 'FontName', 'Consolas');

dt = 0.05;
fprintf('Teleop GUI active! Press keys in the figure window to drive.\n');

%% 5. Real-Time Teleoperation Loop
while isRunning && ishandle(fig)
    % 1. Sensor Simulation
    [ranges, angles] = robot.simulateLidar(map);
    
    % 2. Determine Command Velocities based on Mode
    if strcmp(mode, 'MANUAL')
        v_target     = keyCmd.v;
        omega_target = keyCmd.omega;
    else
        % Autonomous Goal Tracking with VFH
        distToGoal = norm(robot.Pose(1:2)' - goalPoint);
        if distToGoal < 0.25
            v_target = 0.0;
            omega_target = 0.0;
        else
            targetHeading = atan2(goalPoint(2) - robot.Pose(2), goalPoint(1) - robot.Pose(1));
            if hasVFH
                desiredSteer = vfh(ranges, angles, targetHeading);
            else
                desiredSteer = targetHeading;
            end
            
            if ~isnan(desiredSteer)
                headingErr = angdiff(robot.Pose(3), desiredSteer);
                v_target = robot.MaxLinearSpeed * max(0.1, cos(headingErr));
                omega_target = max(-robot.MaxAngularSpeed, min(robot.MaxAngularSpeed, 2.5 * headingErr));
            else
                v_target = 0.0;
                omega_target = 1.0;
            end
        end
    end
    
    % 3. Step Robot Kinematics & EKF
    robot.step(v_target, omega_target, dt, map);
    
    % 4. Update Graphic Renders
    [polyX, polyY] = robot.getFootprintPolygon();
    set(hBody, 'XData', polyX, 'YData', polyY);
    
    wheelPolys = robot.getWheelPolygons();
    for i = 1:4
        set(hWheels{i}, 'XData', wheelPolys{i}(1, :), 'YData', wheelPolys{i}(2, :));
    end
    
    set(hHead,  'XData', [robot.Pose(1), robot.Pose(1) + 0.45 * cos(robot.Pose(3))], ...
                'YData', [robot.Pose(2), robot.Pose(2) + 0.45 * sin(robot.Pose(3))]);
    set(hTrail, 'XData', robot.TrajectoryGT(:, 1), 'YData', robot.TrajectoryGT(:, 2));
    
    if strcmp(mode, 'AUTO')
        set(hGoal, 'XData', goalPoint(1), 'YData', goalPoint(2));
    else
        set(hGoal, 'XData', NaN, 'YData', NaN);
    end
    
    validScan = ranges < robot.LidarMaxRange;
    if any(validScan)
        scanX = robot.Pose(1) + ranges(validScan) .* cos(angles(validScan) + robot.Pose(3));
        scanY = robot.Pose(2) + ranges(validScan) .* sin(angles(validScan) + robot.Pose(3));
        set(hLidar, 'XData', scanX, 'YData', scanY);
    end
    
    set(hBarRPM,   'YData', robot.WheelRPMs);
    set(hBarSpeed, 'YData', [robot.Velocity(1), robot.Velocity(2)]);
    
    hudStr = sprintf([ ...
        '🕹️ Mode:      %s\n' ...
        '📍 Pose:      [%.2f, %.2f, %.1f°]\n' ...
        '⚡ Speed:     v: %.2f | \\omega: %.2f\n' ...
        '⚙️ RPMs:      FL:%.0f  FR:%.0f\n' ...
        '              RL:%.0f  RR:%.0f'], ...
        mode, robot.Pose(1), robot.Pose(2), rad2deg(robot.Pose(3)), ...
        robot.Velocity(1), robot.Velocity(2), ...
        robot.WheelRPMs(1), robot.WheelRPMs(2), robot.WheelRPMs(3), robot.WheelRPMs(4));
    set(hHUD, 'String', hudStr);
    
    drawnow limitrate;
    pause(0.02);
end

%% Helper Callback Functions
function onKeyPress(~, evt)
    global keyCmd mode
    switch evt.Key
        case {'w', 'uparrow'}
            keyCmd.v = 1.2;
        case {'s', 'downarrow'}
            keyCmd.v = -0.8;
        case {'a', 'leftarrow'}
            keyCmd.omega = 1.8;
        case {'d', 'rightarrow'}
            keyCmd.omega = -1.8;
        case 'space'
            keyCmd.v = 0.0;
            keyCmd.omega = 0.0;
        case 'm'
            if strcmp(mode, 'MANUAL')
                mode = 'AUTO';
            else
                mode = 'MANUAL';
            end
    end
end

function onKeyRelease(~, evt)
    global keyCmd
    switch evt.Key
        case {'w', 's', 'uparrow', 'downarrow'}
            keyCmd.v = 0.0;
        case {'a', 'd', 'leftarrow', 'rightarrow'}
            keyCmd.omega = 0.0;
    end
end

function onMapClick(ax)
    global goalPoint mode
    coords = get(ax, 'CurrentPoint');
    goalPoint = [coords(1, 1), coords(1, 2)];
    mode = 'AUTO';
    fprintf('📍 New Goal Dispatched: [%.2f, %.2f] -> Switched to AUTO mode\n', goalPoint(1), goalPoint(2));
end

function onClose(src, ~)
    global isRunning
    isRunning = false;
    delete(src);
end
