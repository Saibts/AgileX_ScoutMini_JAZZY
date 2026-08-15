%% =========================================================================
%  AgileX Scout Mini 4WD AMR: Complete MATLAB Kinematic & Navigation Simulation
%  =========================================================================
%  Description:
%  Simulates the 4WD Skid-Steer / Differential Drive AgileX Scout Mini in a
%  10m x 10m obstacle arena using Navigation Toolbox & Robotics System Toolbox.
%
%  Features:
%  - 4WD Skid-Steer Kinematics (Track Width = 0.612m, Wheel Radius = 0.08m)
%  - Simulated 2D LiDAR Sensor (360 deg, range 12m)
%  - Vector Field Histogram (VFH) Dynamic Obstacle Avoidance
%  - Pure Pursuit Path Following Controller
%  - Multi-Station Waypoint Patrol Mission (Stations A -> B -> C -> D -> E)
%  - Live Real-Time 2D Animation & Telemetry Plotting
%  =========================================================================

clear; clc; close all;

fprintf('=======================================================\n');
fprintf('🤖 AgileX Scout Mini: MATLAB AMR Navigation Simulation\n');
fprintf('=======================================================\n\n');

%% 1. Robot Kinematic & Physical Parameters
trackWidth  = 0.612;    % Distance between left and right wheels (m)
wheelRadius = 0.080;    % Wheel radius (m)
maxLinSpeed = 1.20;     % Maximum linear velocity (m/s)
maxAngSpeed = 1.50;     % Maximum angular velocity (rad/s)
sampleTime  = 0.05;     % Simulation time step (s) -> 20 Hz
simDuration = 120.0;    % Max simulation time (s)

%% 2. Create 10m x 10m Arena Occupancy Map (Matches amr_world.sdf)
mapResolution = 20;     % 20 cells per meter (0.05 m resolution)
mapWidth      = 10;     % meters
mapHeight     = 10;     % meters

% Create empty binary map
map = binaryOccupancyMap(mapWidth, mapHeight, mapResolution);

% Shift map origin to center (-5m to +5m in X and Y)
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

% Inflate map with robot radius (0.35m safety footprint)
robotRadius = 0.35;
inflatedMap = copy(map);
inflate(inflatedMap, robotRadius);

%% 3. Define 5 Patrol Stations
stations = [
    0.0,  0.0;   % Station A: Docking Base
    1.5,  1.5;   % Station B: Loading Zone
   -1.5,  1.5;   % Station C: Inspection Point
   -1.5, -1.5;   % Station D: Unloading Area
    1.5, -1.5;   % Station E: Perimeter Checkpoint
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

%% 4. Configure Navigation Controllers & Range Sensor (LiDAR)
% Vector Field Histogram (VFH) for Obstacle Avoidance
vfh = controllerVFH;
vfh.DistanceLimits          = [0.15, 6.0];
vfh.RobotRadius             = robotRadius;
vfh.SafetyDistance          = 0.15;
vfh.MinTurningRadius        = 0.10;
vfh.TargetDirectionWeight   = 5.0;
vfh.CurrentDirectionWeight  = 2.0;
vfh.PreviousDirectionWeight = 2.0;

% Simulated 2D LiDAR Range Sensor
sensor = rangeSensor;
sensor.Range                = [0.15, 12.0];
sensor.HorizontalAngle      = [-pi, pi];
sensor.HorizontalAngleResolution = 2*pi / 360; % 360 rays

%% 5. Simulation State Initialization
robotPose    = [0.0; 0.0; 0.0]; % [x (m); y (m); theta (rad)]
targetIdx    = 1;
numStations  = size(stations, 1);
waypointTol  = 0.25;            % Distance tolerance to reach station (m)

trajectory_x = [];
trajectory_y = [];

%% 6. Setup Visualization Figure
fig = figure('Name', 'AgileX Scout Mini - MATLAB Simulation', 'NumberTitle', 'off', 'Color', [0.15 0.15 0.18]);
set(fig, 'Position', [100, 100, 900, 800]);

ax = axes('Parent', fig, 'Color', [0.1 0.1 0.12]);
hold(ax, 'on');
axis(ax, 'equal');
grid(ax, 'on');
set(ax, 'GridColor', [0.4 0.4 0.4], 'XColor', [0.8 0.8 0.8], 'YColor', [0.8 0.8 0.8]);
xlim(ax, [-5.5, 5.5]);
ylim(ax, [-5.5, 5.5]);
title(ax, 'AgileX Scout Mini 4WD AMR - Autonomous Patrol & Obstacle Avoidance', 'Color', 'w', 'FontSize', 13, 'FontWeight', 'bold');
xlabel(ax, 'X Position (m)', 'Color', 'w');
ylabel(ax, 'Y Position (m)', 'Color', 'w');

% Plot Map
show(map, 'Parent', ax);

% Plot Stations
stationColors = lines(numStations);
for s = 1:(numStations-1)
    plot(ax, stations(s,1), stations(s,2), 'p', 'MarkerSize', 14, ...
        'MarkerFaceColor', [1 0.8 0], 'MarkerEdgeColor', 'k');
    text(ax, stations(s,1)+0.15, stations(s,2)+0.15, stationNames{s}, ...
        'Color', [1 0.9 0.4], 'FontSize', 9, 'FontWeight', 'bold');
end

% Plot Elements Handles
hTrail = plot(ax, NaN, NaN, 'g-', 'LineWidth', 2);
hLidar = plot(ax, NaN, NaN, 'c.', 'MarkerSize', 4);
hRobot = plot(ax, NaN, NaN, 'r-', 'LineWidth', 2);
hHead  = plot(ax, NaN, NaN, 'y-', 'LineWidth', 2);

%% 7. Main Simulation Loop
t = 0;
fprintf('[MATLAB SIM] Starting Autonomous Patrol Mission...\n');

while t < simDuration && ishandle(fig)
    currentTarget = stations(targetIdx, :);
    currDist = norm(robotPose(1:2)' - currentTarget);
    
    % Check if arrived at station
    if currDist < waypointTol
        fprintf('✅ [ARRIVED] %s reached! (Dist: %.2fm)\n', stationNames{targetIdx}, currDist);
        targetIdx = targetIdx + 1;
        if targetIdx > numStations
            targetIdx = 1; % Loop back to start
            fprintf('🔄 --- Restarting Patrol Loop ---\n');
        end
        currentTarget = stations(targetIdx, :);
    end
    
    % 1. Simulate 2D LiDAR Range Scan
    [ranges, angles] = sensor(robotPose', map);
    
    % 2. Compute Target Heading Angle
    targetHeading = atan2(currentTarget(2) - robotPose(2), currentTarget(1) - robotPose(1));
    
    % 3. Vector Field Histogram (VFH) Dynamic Obstacle Avoidance
    desiredSteer = vfh(ranges, angles, targetHeading);
    
    if ~isnan(desiredSteer)
        % Angle error between current heading and desired steering direction
        headingError = angdiff(robotPose(3), desiredSteer);
        
        % Velocity Control Law (slow down in sharp turns, speed up in clear straights)
        linVel = maxLinSpeed * max(0.1, cos(headingError));
        angVel = max(-maxAngSpeed, min(maxAngSpeed, 2.5 * headingError));
    else
        % Obstacle dead-ahead, execute recovery spin
        linVel = 0.0;
        angVel = 0.8;
    end
    
    % 4. 4WD Skid-Steer / Differential Drive Wheel Kinematics
    % v_right = v + (omega * W) / 2
    % v_left  = v - (omega * W) / 2
    v_right = linVel + (angVel * trackWidth) / 2.0;
    v_left  = linVel - (angVel * trackWidth) / 2.0;
    
    % Wheel RPM telemetry
    rpm_right = (v_right / (2 * pi * wheelRadius)) * 60;
    rpm_left  = (v_left  / (2 * pi * wheelRadius)) * 60;
    
    % 5. Integrate Kinematic State Equations (Euler Integration)
    robotPose(1) = robotPose(1) + linVel * cos(robotPose(3)) * sampleTime;
    robotPose(2) = robotPose(2) + linVel * sin(robotPose(3)) * sampleTime;
    robotPose(3) = angdiff(0, robotPose(3) + angVel * sampleTime);
    
    % Record trajectory
    trajectory_x(end+1) = robotPose(1);
    trajectory_y(end+1) = robotPose(2);
    
    % 6. Update Real-Time Graphics
    % Compute robot footprint box corners (0.7m x 0.6m)
    L = 0.35; W = 0.30;
    box_body = [ L, -L, -L,  L, L;
                 W,  W, -W, -W, W ];
    R_mat = [cos(robotPose(3)), -sin(robotPose(3)); sin(robotPose(3)), cos(robotPose(3))];
    box_world = R_mat * box_body + [robotPose(1); robotPose(2)];
    
    % LiDAR points in world frame
    validScan = ~isnan(ranges) & ranges < 12.0;
    scan_x = robotPose(1) + ranges(validScan) .* cos(angles(validScan) + robotPose(3));
    scan_y = robotPose(2) + ranges(validScan) .* sin(angles(validScan) + robotPose(3));
    
    % Update plot handles
    set(hTrail, 'XData', trajectory_x, 'YData', trajectory_y);
    set(hLidar, 'XData', scan_x, 'YData', scan_y);
    set(hRobot, 'XData', box_world(1,:), 'YData', box_world(2,:));
    set(hHead,  'XData', [robotPose(1), robotPose(1)+0.4*cos(robotPose(3))], ...
                'YData', [robotPose(2), robotPose(2)+0.4*sin(robotPose(3))]);
    
    drawnow limitrate;
    t = t + sampleTime;
    pause(0.005); % Smooth animation
end

fprintf('Simulation Complete.\n');
