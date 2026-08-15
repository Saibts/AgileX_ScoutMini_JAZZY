%% =========================================================================
%  AgileX Scout Mini AMR: Simscape Multibody Physical Simulation Loader
%  =========================================================================
%  Description:
%  Initializes workspace variables (smiData), configures CAD STEP geometry
%  paths, sets up 4WD Skid-Steer physical parameters, and launches the
%  SolidWorks-imported Simscape Multibody model (Assem2.slx).
%
%  Physical Parameters:
%  - Robot Mass: ~30 kg (Chassis: 27.6 kg, Wheels: 4 x 1.19 kg)
%  - Track Width (W): 0.612 m
%  - Wheel Radius (R): 0.080 m
%  - Hub Motor Max Speed: 360 RPM
%  - Max Drive Torque: 17.5 Nm per wheel
%
%  Requirements:
%  - MATLAB R2022b or later
%  - Simscape Multibody Toolbox
%  - Simulink
%  =========================================================================

clear; clc;
fprintf('===================================================================\n');
fprintf('🤖 AgileX Scout Mini: Simscape Multibody Physical Simulation Loader\n');
fprintf('===================================================================\n\n');

% Determine script directory
simscapeDir = fileparts(mfilename('fullpath'));
cd(simscapeDir);
addpath(simscapeDir);

fprintf('1. Loading CAD Mass & Inertia Data (Assem2_DataFile.m)...\n');
if exist('Assem2_DataFile.m', 'file')
    Assem2_DataFile;
    fprintf('   ✅ smiData structure initialized successfully with %d bodies & %d joints.\n', ...
        numel(smiData.Solid), numel(smiData.RevoluteJoint));
else
    error('Assem2_DataFile.m not found in %s', simscapeDir);
end

% Check CAD STEP files
stepFiles = {'W_Default_sldprt.STEP', 'chassis_top_Default_sldprt.STEP', 'up_Default_sldprt.STEP'};
allStepExist = true;
for i = 1:numel(stepFiles)
    if ~exist(stepFiles{i}, 'file')
        allStepExist = false;
        warning('CAD STEP file missing: %s', stepFiles{i});
    end
end
if allStepExist
    fprintf('2. Verified CAD STEP 3D Geometries: %d files ready.\n', numel(stepFiles));
end

% Set up kinematics & physical constants for Simulink blocks
assignin('base', 'TRACK_WIDTH', 0.612);      % Effective track width (meters)
assignin('base', 'WHEEL_RADIUS', 0.080);     % Outer wheel radius (meters)
assignin('base', 'MAX_WHEEL_TORQUE', 17.5);  % Max in-hub motor torque (Nm)
assignin('base', 'MAX_WHEEL_RPM', 360.0);    % Max wheel rotational speed (RPM)
assignin('base', 'ROBOT_MASS', 30.0);        % Total robot mass (kg)

fprintf('\n3. Opening Simulink Model (Assem2.slx)...\n');
modelName = 'Assem2';
if exist([modelName '.slx'], 'file')
    load_system(modelName);
    open_system(modelName);
    fprintf('   ✅ %s.slx opened in Simulink Mechanics Explorer!\n\n', modelName);
    fprintf('-------------------------------------------------------------------\n');
    fprintf('💡 Quick Tips:\n');
    fprintf(' • Press Ctrl+T or click "Run" in Simulink to simulate 3D dynamics.\n');
    fprintf(' • The 3D Mechanics Explorer visualizer will display the robot body,\n');
    fprintf('   wheel suspension, and gravity responses.\n');
    fprintf(' • To actuate wheels, provide velocity or torque signals to the\n');
    fprintf('   Revolute Joint blocks (j1..j4).\n');
    fprintf('-------------------------------------------------------------------\n');
else
    error('Model file %s.slx not found in %s', modelName, simscapeDir);
end
