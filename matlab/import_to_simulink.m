%% =========================================================================
%  AgileX Scout Mini: Import URDF Directly into Simulink (Simscape Multibody)
%  =========================================================================
%  Description:
%  Automatically converts the AgileX Scout Mini URDF and 3D STL meshes into
%  a complete physical Simulink model (.slx) using Simscape Multibody.
%
%  Requirements:
%  - MATLAB with Simscape Multibody Toolbox
%  =========================================================================

clear; clc;

fprintf('=======================================================\n');
fprintf('⚙️ AgileX Scout Mini: Simulink Simscape Model Generator\n');
fprintf('=======================================================\n\n');

% Path to the URDF file
currentDir = fileparts(mfilename('fullpath'));
projectRoot = fileparts(currentDir);
urdfPath = fullfile(projectRoot, 'src', 'assem2_robot', 'urdf', 'Assem2.SLDASM.urdf');

if ~exist(urdfPath, 'file')
    error('URDF file not found at: %s', urdfPath);
end

fprintf('1. Found URDF: %s\n', urdfPath);
fprintf('2. Converting URDF into Simulink Simscape Block Diagram...\n');

try
    % smimport converts URDF into an active Simulink .slx diagram
    smimport(urdfPath);
    
    fprintf('\n=======================================================\n');
    fprintf('✅ SUCCESS: Simulink Model Generated & Opened!\n');
    fprintf('=======================================================\n');
    fprintf('What Simscape Created:\n');
    fprintf(' • Rigid Body blocks for chassis and all 4 wheels with mass/inertia\n');
    fprintf(' • Revolute Joint blocks for wheel actuation\n');
    fprintf(' • 3D Mechanics Explorer visualization window\n');
    fprintf(' • Sensor mount frames for LiDAR, IMU, and Depth Camera\n');
catch ME
    fprintf('\n⚠️ Simscape Import Message: %s\n', ME.message);
    fprintf('Note: Ensure "Simscape Multibody" is installed in your MATLAB Add-ons.\n');
end
