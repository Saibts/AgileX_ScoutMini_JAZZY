%% =========================================================================
%  AgileX Scout Mini AMR: Master Simulation Suite Launcher
%  =========================================================================
%  Local Root: /home/sailakshmi/agilex/matlab
%  =========================================================================

function run_amr_matlab_suite()
    clear; clc;
    
    % Ensure all subdirectories are in MATLAB search path
    suiteDir = fileparts(mfilename('fullpath'));
    addpath(suiteDir);
    addpath(fullfile(suiteDir, 'simscape'));
    cd(suiteDir);

    fprintf('===================================================================\n');
    fprintf('🚜 AGILEX SCOUT MINI AMR: MASTER SIMULATION SUITE\n');
    fprintf('===================================================================\n\n');
    fprintf('Select a simulation module to run:\n\n');
    fprintf(' [1] 🚜 4WD Skid-Steer Physical Dynamics & Telemetry Simulation\n');
    fprintf(' [2] 🏗️ SolidWorks Simscape Multibody 3D Physics (Assem2.slx)\n');
    fprintf(' [3] 🤖 Autonomous Patrol & 2D LiDAR Obstacle Avoidance Simulation\n');
    fprintf(' [4] 🎮 Interactive Keyboard Teleoperation & Click-to-Navigate GUI\n');
    fprintf(' [5] 🌲 3D RigidBodyTree URDF Model & Kinematic Tree Visualizer\n');
    fprintf(' [6] 🌐 ROS 2 Jazzy & Gazebo Harmonic Live Bridge\n');
    fprintf(' [0] ❌ Exit\n\n');
    
    choice = input('Enter your choice (0-6) [default: 1]: ');
    if isempty(choice)
        choice = 1;
    end
    
    switch choice
        case 1
            fprintf('\n▶️ Launching 4WD AMR Physical Dynamics Simulation...\n\n');
            scout_mini_dynamics_sim();
        case 2
            fprintf('\n▶️ Launching SolidWorks Simscape Multibody Simulation...\n\n');
            simulate_solidworks_amr();
        case 3
            fprintf('\n▶️ Launching Autonomous Patrol & LiDAR Simulation...\n\n');
            scout_mini_kinematics_sim;
        case 4
            fprintf('\n▶️ Launching Interactive Teleoperation GUI...\n\n');
            scout_mini_teleop_gui;
        case 5
            fprintf('\n▶️ Launching 3D RigidBodyTree URDF Visualizer...\n\n');
            import_scout_mini_urdf;
        case 6
            fprintf('\n▶️ Launching ROS 2 Jazzy Bridge...\n\n');
            scout_mini_ros2_bridge;
        case 0
            fprintf('Exiting suite. Happy simulating!\n');
        otherwise
            warning('Invalid choice. Running default 4WD Physical Dynamics Simulation.');
            scout_mini_dynamics_sim();
    end
end
