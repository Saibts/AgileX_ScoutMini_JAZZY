%% =========================================================================
%  AgileX Scout Mini: Import URDF into MATLAB RigidBodyTree & 3D Visualizer
%  =========================================================================
%  Description:
%  Imports the URDF model of the AgileX Scout Mini into MATLAB, parses the
%  joint/link kinematic tree, and renders the 3D model with interactive wheel
%  rotation controls.
%
%  Requirements:
%  - MATLAB Robotics System Toolbox (or Simscape Multibody)
%  =========================================================================

clear; clc; close all;

fprintf('===================================================================\n');
fprintf('🤖 AgileX Scout Mini: MATLAB URDF Import & 3D Kinematic Visualizer\n');
fprintf('===================================================================\n\n');

%% 1. Locate URDF Model File across Windows/Linux Paths
currentDir = fileparts(mfilename('fullpath'));
projectRoot = fileparts(currentDir);

candidatePaths = {
    fullfile(currentDir, '..', 'Assem2.SLDASM', 'urdf', 'Assem2.SLDASM.urdf'), ...
    fullfile(projectRoot, 'Assem2.SLDASM', 'urdf', 'Assem2.SLDASM.urdf'), ...
    fullfile(projectRoot, 'src', 'assem2_robot', 'urdf', 'Assem2.SLDASM.urdf'), ...
    fullfile(currentDir, 'Assem2.SLDASM.urdf')
};

urdfPath = '';
for i = 1:numel(candidatePaths)
    if exist(candidatePaths{i}, 'file')
        urdfPath = candidatePaths{i};
        break;
    end
end

if isempty(urdfPath)
    error('❌ URDF file not found. Checked candidate paths:\n%s', strjoin(candidatePaths, '\n'));
end

fprintf('✅ Found URDF at: %s\n\n', urdfPath);

%% 2. Configure Mesh Resource Paths
meshDir = fullfile(fileparts(fileparts(urdfPath)), 'meshes');
if exist(meshDir, 'dir')
    addpath(meshDir);
    fprintf('✅ Added mesh directory to MATLAB path: %s\n', meshDir);
end

%% 3. Import Robot as RigidBodyTree
try
    robot = importrobot(urdfPath);
    robot.DataFormat = 'row';
    robot.Gravity = [0, 0, -9.81];
    
    % Display Summary
    fprintf('\n--- 📋 Robot Kinematic Hierarchy Summary ---\n');
    fprintf(' • Total Bodies: %d\n', robot.NumBodies);
    fprintf(' • Base Link:    %s\n', robot.BaseName);
    fprintf(' • Joint Names:  %s\n', strjoin(robot.BodyNames, ', '));
    showdetails(robot);
    
    %% 4. Visualize 3D Robot in MATLAB Figure
    fig = figure('Name', 'AgileX Scout Mini - 3D RigidBodyTree Visualizer', ...
                 'Color', [0.15 0.15 0.18], 'Position', [150, 150, 950, 700]);
    ax = axes('Parent', fig, 'Color', [0.1 0.1 0.12]);
    
    config = homeConfiguration(robot);
    show(robot, config, 'Parent', ax, 'Visuals', 'on', 'Collisions', 'off');
    
    title(ax, 'AgileX Scout Mini 4WD AMR (MATLAB RigidBodyTree 3D Model)', ...
          'Color', 'w', 'FontSize', 12, 'FontWeight', 'bold');
    set(ax, 'XColor', 'w', 'YColor', 'w', 'ZColor', 'w', 'GridColor', [0.4 0.4 0.4]);
    view(ax, [45, 30]);
    grid(ax, 'on');
    axis(ax, 'equal');
    camlight(ax, 'headlight');
    
    fprintf('\n✅ 3D Model successfully loaded and displayed!\n');
    fprintf('💡 Tip: Rotate the view with your mouse in the 3D window.\n');
    
catch ME
    fprintf('⚠️ Robot Import Error: %s\n', ME.message);
    fprintf('Ensure "Robotics System Toolbox" is installed in your MATLAB environment.\n');
end
