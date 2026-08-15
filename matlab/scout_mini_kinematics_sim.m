%% =========================================================================
%  AgileX Scout Mini 4WD AMR: Complete MATLAB Kinematic & Navigation Simulation
%  =========================================================================
%  Description:
%  Simulates the 4WD Skid-Steer / Independent Hub-Drive AgileX Scout Mini in a
%  10m x 10m obstacle arena using Navigation Toolbox & Robotics System Toolbox.
%
%  Features:
%  - Accurate 4WD Skid-Steer Kinematics with ICR slip factor & motor RPM limits
%  - Multi-Station Waypoint Patrol Mission (Stations A -> B -> C -> D -> E -> A)
%  - Simulated 2D LiDAR Raycaster (360 degrees, 12m max range)
%  - Vector Field Histogram (VFH) Dynamic Obstacle Avoidance
%  - Extended Kalman Filter (EKF) fusing Wheel Encoders & IMU Gyroscope
%  - Real-Time Multi-Panel Telemetry HUD & 4-Wheel RPM Gauges
%  =========================================================================

clear; clc; close all;

% Ensure current directory is on MATLAB search path
matlabDir = fileparts(mfilename('fullpath'));
if ~isempty(matlabDir)
    addpath(matlabDir);
end

fprintf('===================================================================\n');
fprintf('🤖 AgileX Scout Mini: 4WD AMR Autonomous Patrol & Kinematics Sim\n');
fprintf('===================================================================\n\n');

%% 1. Create 10m x 10m Arena Occupancy Map (Matches amr_world.sdf)
mapResolution = 20;     % 20 cells per meter (0.05 m grid resolution)
mapWidth      = 10;     % meters
mapHeight     = 10;     % meters

% Create empty binary map
map = binaryOccupancyMap(mapWidth, mapHeight, mapResolution);
map.GridLocationInWorld = [-5, -5];

% Add Perimeter Boundary Walls
setOccupancy(map, [-5.0:0.05:5.0;  5.0*ones(1, 201)]', 1); % North Wall
setOccupancy(map, [-5.0:0.05:5.0; -5.0*ones(1, 201)]', 1); % South Wall
setOccupancy(map, [ 5.0*ones(1, 201); -5.0:0.05:5.0]', 1); % East Wall
setOccupancy(map, [-5.0*ones(1, 201); -5.0:0.05:5.0]', 1); % West Wall

% Add Obstacles (Matching Gazebo amr_world.sdf)
% Pillar 1 (Cylinder at [2.0, 2.0], radius 0.35m)
[xP1, yP1] = meshgrid(-0.35:0.05:0.35, -0.35:0.05:0.35);
circMask1 = (xP1.^2 + yP1.^2) <= 0.35^2;
setOccupancy(map, [2.0 + xP1(circMask1), 2.0 + yP1(circMask1)], 1);

% Pillar 2 (Cylinder at [-2.0, -2.0], radius 0.35m)
setOccupancy(map, [-2.0 + xP1(circMask1), -2.0 + yP1(circMask1)], 1);

% Box Obstacle 1 at [2.5, -2.0] (0.8m x 1.2m)
[xB1, yB1] = meshgrid(-0.4:0.05:0.4, -0.6:0.05:0.6);
setOccupancy(map, [2.5 + xB1(:), -2.0 + yB1(:)], 1);

% Box Obstacle 2 at [-2.5, 2.0] (1.0m x 1.0m)
[xB2, yB2] = meshgrid(-0.5:0.05:0.5, -0.5:0.05:0.5);
setOccupancy(map, [-2.5 + xB2(:), 2.0 + yB2(:)], 1);

% Center Barrier at [0.0, 2.8] (2.0m x 0.3m)
[xBar, yBar] = meshgrid(-1.0:0.05:1.0, -0.15:0.05:0.15);
setOccupancy(map, [0.0 + xBar(:), 2.8 + yBar(:)], 1);

% Inflate map with safety radius
robotRadius = 0.35;
inflatedMap = copy(map);
inflate(inflatedMap, robotRadius);

%% 2. Instantiate AgileX Scout Mini Robot Model
initPose = [0.0; 0.0; 0.0]; % [x, y, theta]
robot = ScoutMiniRobot(initPose);

sampleTime  = 0.05;     % Simulation time step (s) -> 20 Hz
simDuration = 150.0;    % Max simulation duration (s)

%% 3. Define 5 Patrol Stations
stations = [
    0.0,  0.0;   % Station A: Docking Base
    2.5,  2.5;   % Station B: Loading Zone
   -2.5,  2.5;   % Station C: Inspection Point
   -2.5, -2.5;   % Station D: Unloading Area
    2.5, -2.5;   % Station E: Perimeter Checkpoint
    0.0,  0.0    % Return to Station A
];

stationNames = {
    'Station A (Docking Base)', ...
    'Station B (Loading Zone)', ...
    'Station C (Inspection Point)', ...
    'Station D (Unloading Area)', ...
    'Station E (Perimeter Checkpoint)', ...
    'Station A (Docking Base)'
};

numStations  = size(stations, 1);
targetIdx    = 1;
waypointTol  = 0.30;    % Distance tolerance to consider station reached (m)

%% 4. Configure Navigation Controllers
% Check if Navigation Toolbox controllerVFH is available, otherwise use custom VFH
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

%% 5. Setup Multi-Panel Visualization HUD
fig = figure('Name', 'AgileX Scout Mini - MATLAB Simulation & Telemetry HUD', ...
             'NumberTitle', 'off', 'Color', [0.12 0.12 0.15], ...
             'Position', [50, 50, 1200, 750]);

% --- Main Arena Map Axes (Left, Large) ---
axMap = subplot(3, 3, [1 2 4 5 7 8], 'Parent', fig);
hold(axMap, 'on');
axis(axMap, 'equal');
grid(axMap, 'on');
set(axMap, 'Color', [0.08 0.08 0.10], 'GridColor', [0.3 0.3 0.35], ...
    'XColor', [0.8 0.8 0.8], 'YColor', [0.8 0.8 0.8]);
xlim(axMap, [-5.5, 5.5]);
ylim(axMap, [-5.5, 5.5]);
title(axMap, 'AgileX Scout Mini 4WD AMR - 2D Arena & Live 360° LiDAR Scan', ...
      'Color', 'w', 'FontSize', 12, 'FontWeight', 'bold');
xlabel(axMap, 'X Position (meters)', 'Color', 'w');
ylabel(axMap, 'Y Position (meters)', 'Color', 'w');

% Show Arena Map
show(map, 'Parent', axMap);

% Plot Patrol Waypoints
for s = 1:(numStations-1)
    plot(axMap, stations(s,1), stations(s,2), 'p', 'MarkerSize', 14, ...
        'MarkerFaceColor', [1 0.8 0], 'MarkerEdgeColor', 'k');
    text(axMap, stations(s,1)+0.15, stations(s,2)+0.15, sprintf('S%d: %s', s, stationNames{s}), ...
        'Color', [1 0.9 0.4], 'FontSize', 8, 'FontWeight', 'bold');
end

% Graphic Plot Handles
hTrailGT  = plot(axMap, NaN, NaN, 'g-', 'LineWidth', 1.8, 'DisplayName', 'Ground Truth Path');
hTrailEKF = plot(axMap, NaN, NaN, 'm--', 'LineWidth', 1.2, 'DisplayName', 'EKF Estimated Path');
hLidar    = plot(axMap, NaN, NaN, 'c.', 'MarkerSize', 4, 'DisplayName', 'LiDAR Point Cloud');
hTarget   = plot(axMap, NaN, NaN, 'ro', 'MarkerSize', 10, 'LineWidth', 2, 'DisplayName', 'Target Waypoint');

% Robot Body & 4 Wheels
hBody     = fill(axMap, NaN, NaN, [0.8 0.2 0.2], 'FaceAlpha', 0.85, 'EdgeColor', 'w', 'LineWidth', 1.5);
hWheels   = cell(4, 1);
for i = 1:4
    hWheels{i} = fill(axMap, NaN, NaN, [0.2 0.2 0.2], 'FaceAlpha', 0.95, 'EdgeColor', [0.9 0.8 0.1], 'LineWidth', 1.2);
end
hHeading  = plot(axMap, NaN, NaN, 'y-', 'LineWidth', 2.5);

% --- Telemetry Panel 1: 4-Wheel RPMs (Top Right) ---
axRPM = subplot(3, 3, 3, 'Parent', fig);
set(axRPM, 'Color', [0.08 0.08 0.10], 'XColor', 'w', 'YColor', 'w');
wheelLabels = categorical({'FL (w1)', 'FR (w2)', 'RL (w3)', 'RR (w4)'});
wheelLabels = reordercats(wheelLabels, {'FL (w1)', 'FR (w2)', 'RL (w3)', 'RR (w4)'});
hBarRPM = bar(axRPM, wheelLabels, [0 0 0 0], 'FaceColor', [0.2 0.7 0.9]);
ylim(axRPM, [-360, 360]);
title(axRPM, '4-Wheel In-Hub Motor RPM', 'Color', 'w', 'FontSize', 10);
ylabel(axRPM, 'Speed (RPM)', 'Color', 'w');
grid(axRPM, 'on');

% --- Telemetry Panel 2: Linear & Angular Speeds (Middle Right) ---
axSpeed = subplot(3, 3, 6, 'Parent', fig);
set(axSpeed, 'Color', [0.08 0.08 0.10], 'XColor', 'w', 'YColor', 'w');
speedLabels = categorical({'Linear v (m/s)', 'Angular \omega (rad/s)'});
speedLabels = reordercats(speedLabels, {'Linear v (m/s)', 'Angular \omega (rad/s)'});
hBarSpeed = bar(axSpeed, speedLabels, [0 0], 'FaceColor', [0.9 0.6 0.2]);
ylim(axSpeed, [-3.0, 3.0]);
title(axSpeed, 'Robot Body Velocity', 'Color', 'w', 'FontSize', 10);
grid(axSpeed, 'on');

% --- Telemetry Panel 3: EKF Error & Navigation Status (Bottom Right) ---
axHUD = subplot(3, 3, 9, 'Parent', fig);
set(axHUD, 'Color', [0.08 0.08 0.10], 'XColor', 'none', 'YColor', 'none');
title(axHUD, '📋 Real-Time Mission Telemetry', 'Color', 'w', 'FontSize', 10);
hHUDText = text(axHUD, 0.05, 0.5, '', 'Color', 'w', 'FontSize', 9, 'FontName', 'Consolas');

%% 6. Main Simulation & Control Loop
t = 0;
fprintf('[MATLAB SIM] Starting Autonomous Patrol Mission...\n');

while t < simDuration && ishandle(fig)
    currentTarget = stations(targetIdx, :);
    currDist = norm(robot.Pose(1:2)' - currentTarget);
    
    % 1. Waypoint Check & Station Transition
    if currDist < waypointTol
        fprintf('✅ [ARRIVED] %s reached! (Dist: %.2fm)\n', stationNames{targetIdx}, currDist);
        targetIdx = targetIdx + 1;
        if targetIdx > numStations
            targetIdx = 1;
            fprintf('🔄 --- Restarting Patrol Mission Loop ---\n');
        end
        currentTarget = stations(targetIdx, :);
    end
    
    % 2. Simulate 2D LiDAR Range Scan
    [ranges, angles] = robot.simulateLidar(map);
    
    % 3. Navigation & Dynamic Obstacle Avoidance
    targetHeading = atan2(currentTarget(2) - robot.Pose(2), currentTarget(1) - robot.Pose(1));
    
    if hasVFH
        desiredSteer = vfh(ranges, angles, targetHeading);
    else
        % Fallback potential field steering
        minFrontRange = min(ranges(abs(angles) < pi/4));
        if minFrontRange < 0.6
            desiredSteer = robot.Pose(3) + 0.8; % Spin away from obstacle
        else
            desiredSteer = targetHeading;
        end
    end
    
    if ~isnan(desiredSteer)
        headingError = angdiff(robot.Pose(3), desiredSteer);
        % Velocity Law: slow down in sharp turns, drive fast on clear paths
        v_cmd     = robot.MaxLinearSpeed * max(0.15, cos(headingError));
        omega_cmd = max(-robot.MaxAngularSpeed, min(robot.MaxAngularSpeed, 2.5 * headingError));
    else
        % Recovery maneuver when blocked
        v_cmd     = 0.0;
        omega_cmd = 1.0;
    end
    
    % 4. Step Robot Simulation (Kinematics, Motor Speeds, EKF Sensor Fusion)
    robot.step(v_cmd, omega_cmd, sampleTime, map);
    
    % 5. Update Graphics & Real-Time HUD
    % Robot Footprint Polygon
    [polyX, polyY] = robot.getFootprintPolygon();
    set(hBody, 'XData', polyX, 'YData', polyY);
    
    % 4 Wheels
    wheelPolys = robot.getWheelPolygons();
    for i = 1:4
        set(hWheels{i}, 'XData', wheelPolys{i}(1, :), 'YData', wheelPolys{i}(2, :));
    end
    
    % Heading Vector
    set(hHeading, 'XData', [robot.Pose(1), robot.Pose(1) + 0.45 * cos(robot.Pose(3))], ...
                  'YData', [robot.Pose(2), robot.Pose(2) + 0.45 * sin(robot.Pose(3))]);
    
    % Trajectory Trails
    set(hTrailGT,  'XData', robot.TrajectoryGT(:, 1),  'YData', robot.TrajectoryGT(:, 2));
    set(hTrailEKF, 'XData', robot.TrajectoryEKF(:, 1), 'YData', robot.TrajectoryEKF(:, 2));
    
    % Active Target Marker
    set(hTarget, 'XData', currentTarget(1), 'YData', currentTarget(2));
    
    % LiDAR Point Cloud
    validScan = ranges < robot.LidarMaxRange;
    if any(validScan)
        scanX = robot.Pose(1) + ranges(validScan) .* cos(angles(validScan) + robot.Pose(3));
        scanY = robot.Pose(2) + ranges(validScan) .* sin(angles(validScan) + robot.Pose(3));
        set(hLidar, 'XData', scanX, 'YData', scanY);
    end
    
    % Telemetry Bar Charts
    set(hBarRPM,   'YData', robot.WheelRPMs);
    set(hBarSpeed, 'YData', [robot.Velocity(1), robot.Velocity(2)]);
    
    % HUD Information Text
    ekfError = norm(robot.Pose(1:2) - robot.EKFPose(1:2));
    hudStr = sprintf([ ...
        '⏱️ Time:       %.1f s\n' ...
        '🎯 Target:     %s\n' ...
        '📍 Pose (GT):  [%.2f, %.2f, %.2f°]\n' ...
        '🧭 Pose (EKF): [%.2f, %.2f, %.2f°]\n' ...
        '📏 EKF Error:  %.3f m\n' ...
        '⚡ Lin Vel:    %.2f m/s\n' ...
        '🔄 Ang Vel:    %.2f rad/s\n' ...
        '⚙️ RPMs:       FL:%.0f  FR:%.0f\n' ...
        '               RL:%.0f  RR:%.0f'], ...
        t, stationNames{targetIdx}, ...
        robot.Pose(1), robot.Pose(2), rad2deg(robot.Pose(3)), ...
        robot.EKFPose(1), robot.EKFPose(2), rad2deg(robot.EKFPose(3)), ...
        ekfError, robot.Velocity(1), robot.Velocity(2), ...
        robot.WheelRPMs(1), robot.WheelRPMs(2), robot.WheelRPMs(3), robot.WheelRPMs(4));
    set(hHUDText, 'String', hudStr);
    
    drawnow limitrate;
    t = t + sampleTime;
    pause(0.005);
end

fprintf('Simulation Complete.\n');
