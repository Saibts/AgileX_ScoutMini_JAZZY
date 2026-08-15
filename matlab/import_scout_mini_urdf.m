%% =========================================================================
%  AgileX Scout Mini: Import URDF into MATLAB RigidBodyTree & 3D Visualizer
%  =========================================================================
%  Description:
%  Imports the URDF model of the AgileX Scout Mini into MATLAB, parses the
%  joint/link kinematic hierarchy, and renders the 3D model.
%
%  Requirements:
%  - MATLAB Robotics System Toolbox or Simscape Multibody
%  =========================================================================

clear; clc; close all;

fprintf('=======================================================\n');
fprintf('🤖 AgileX Scout Mini: MATLAB URDF Import & 3D Display\n');
fprintf('=======================================================\n\n');

% Path to the URDF file
currentDir = fileparts(mfilename('fullpath'));
projectRoot = fileparts(currentDir);
urdfPath = fullfile(projectRoot, 'src', 'assem2_robot', 'urdf', 'Assem2.SLDASM.urdf');

if ~exist(urdfPath, 'file')
    error('URDF file not found at: %s', urdfPath);
end

fprintf('Loading URDF from: %s\n', urdfPath);

% 1. Import robot as RigidBodyTree
robot = importrobot(urdfPath);
robot.DataFormat = 'row';
robot.Gravity = [0, 0, -9.81];

% 2. Display Robot Information in Command Window
fprintf('\n--- 📋 Robot Model Kinematic Summary ---\n');
showdetails(robot);

% 3. Visualize 3D Robot in MATLAB Figure
fig = figure('Name', 'AgileX Scout Mini - 3D RigidBodyTree', 'Color', 'w');
ax = axes('Parent', fig);
show(robot, 'Parent', ax, 'Visuals', 'on', 'Collisions', 'off');
title(ax, 'AgileX Scout Mini 4WD AMR (MATLAB RigidBodyTree)', 'FontSize', 12, 'FontWeight', 'bold');
view(ax, 3);
grid(ax, 'on');
axis(ax, 'equal');

fprintf('\n✅ 3D Model successfully loaded and displayed in MATLAB!\n');
