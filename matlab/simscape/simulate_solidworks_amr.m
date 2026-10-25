%% =========================================================================
%  AgileX Scout Mini AMR: SolidWorks Simscape Multibody Physical Simulation
%  =========================================================================
%  Reference:
%  - SolidWorks Imported Multibody Assembly: Assem2.slx / Assem2.xml
%  - CAD Mass, Center of Mass & Inertia Data: Assem2_DataFile.m
%  - Dynamics Reference: DocScanner 23 Aug 2026 10-00.pdf (Lagrangian Dynamics)
%  =========================================================================

function simulate_solidworks_amr()
    clear; clc;
    fprintf('===================================================================\n');
    fprintf('🏗️ AgileX Scout Mini: SolidWorks Simscape Multibody Simulation\n');
    fprintf('===================================================================\n\n');

    % 1. Setup paths
    simscapeDir = fileparts(mfilename('fullpath'));
    cd(simscapeDir);
    addpath(simscapeDir);

    % 2. Load SolidWorks CAD Parameters
    fprintf('1. Loading CAD Mass & Inertia Data (Assem2_DataFile.m)...\n');
    if exist('Assem2_DataFile.m', 'file')
        Assem2_DataFile;
        fprintf('   ✅ Loaded %d Solid Bodies and %d Revolute Joints.\n', ...
            numel(smiData.Solid), numel(smiData.RevoluteJoint));
        fprintf('   • Solid 1 (Wheel):      Mass = %.3f kg\n', smiData.Solid(1).mass);
        fprintf('   • Solid 2 (Chassis):    Mass = %.3f kg\n', smiData.Solid(2).mass);
        fprintf('   • Solid 3 (Upper Mount): Mass = %.3f kg\n\n', smiData.Solid(3).mass);
    else
        error('❌ Assem2_DataFile.m not found in %s', simscapeDir);
    end

    % 3. Assign Physical Parameters to MATLAB Workspace
    assignin('base', 'smiData', smiData);
    assignin('base', 'TRACK_WIDTH', 0.612);      % 612 mm
    assignin('base', 'WHEEL_RADIUS', 0.080);     % 80 mm
    assignin('base', 'MAX_WHEEL_TORQUE', 17.5);  % 17.5 Nm
    assignin('base', 'MAX_WHEEL_RPM', 360.0);    % 360 RPM
    assignin('base', 'ROBOT_MASS', 30.0);        % 30 kg
    assignin('base', 'GRAVITY_ACCEL', 9.81);     % 9.81 m/s^2

    % 4. Open and Configure Simulink Model
    modelName = 'Assem2';
    fprintf('2. Opening Simscape Multibody Model (%s.slx)...\n', modelName);
    
    if exist([modelName '.slx'], 'file')
        load_system(modelName);
        open_system(modelName);
        fprintf('   ✅ Opened %s.slx in Simulink & Mechanics Explorer!\n\n', modelName);
        
        fprintf('-------------------------------------------------------------------\n');
        fprintf('🎮 HOW TO RUN IN SIMULINK:\n');
        fprintf(' 1. Click "Run" (▶) or press Ctrl+T in Simulink.\n');
        fprintf(' 2. The 3D Mechanics Explorer will pop up showing the 3D CAD Scout Mini.\n');
        fprintf(' 3. The 4 wheel joints (j1, j2, j3, j4) are mapped to Revolute Joint blocks.\n');
        fprintf(' 4. You can provide torque or velocity signals to simulate:\n');
        fprintf('    • Straight driving (All 4 wheels same direction)\n');
        fprintf('    • Skid-steer pivot turn (Left wheels reverse, Right wheels forward)\n');
        fprintf('    • Ramp climbing and suspension response under gravity\n');
        fprintf('-------------------------------------------------------------------\n');
    else
        error('❌ Model file %s.slx not found in %s', modelName, simscapeDir);
    end
end
