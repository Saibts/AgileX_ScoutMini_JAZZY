%% =========================================================================
%  AgileX Scout Mini AMR: 4WD Skid-Steer Physical Dynamics & Telemetry Simulator
%  =========================================================================
%  Local Path: /home/sailakshmi/agilex/matlab/scout_mini_dynamics_sim.m
%
%  Robot Specifications (AgileX Scout Mini):
%  - Total Mass (M): 30.0 kg (Chassis: 27.6 kg, 4 Wheels: 4 x 1.19 kg)
%  - Yaw Moment of Inertia (Iz): 1.62 kg*m^2
%  - Single Wheel Inertia (Iw): 0.0047 kg*m^2
%  - Track Width (W): 0.612 m | Wheelbase (L): 0.450 m
%  - Tire Radius (R): 0.080 m (160 mm diameter)
%  - 4WD In-Hub Motors: Rated Torque = 17.5 Nm/wheel, Max Speed = 360 RPM
%  - Skid-Steer ICR Slip Parameter: alpha = 1.05
%  =========================================================================

function scout_mini_dynamics_sim()
    clear; clc; close all;
    fprintf('===================================================================\n');
    fprintf('🚜 AgileX Scout Mini: 4WD Physical Dynamics & Telemetry Simulation\n');
    fprintf('===================================================================\n\n');

    %% 1. PHYSICAL CONSTANTS (From SolidWorks CAD & AgileX Spec)
    params.M         = 30.0;        % Robot mass (kg)
    params.Iz        = 1.62;        % Yaw Moment of Inertia (kg*m^2)
    params.Iw        = 0.0047;      % Wheel MOI (kg*m^2)
    params.W         = 0.612;       % Effective Track width (m)
    params.L         = 0.450;       % Wheelbase (m)
    params.R         = 0.080;       % Tire radius (m)
    params.alpha     = 1.05;        % Skid-steer slip coefficient
    params.effW      = params.W * params.alpha;
    params.mu        = 0.15;        % Rolling resistance coefficient
    params.Cd        = 0.50;        % Viscous drag (N*s/m)
    params.g         = 9.81;        % Gravity (m/s^2)
    params.MaxTorque = 17.5;        % Max torque per wheel (Nm)
    params.MaxRPM    = 360.0;       % Max motor speed (RPM)
    
    %% 2. SIMULATION TIMING & REFERENCE TRAJECTORY
    dt = 0.02;                      % Time step (50 Hz)
    t_end = 25.0;                   % Simulation duration (s)
    time = 0:dt:t_end;
    N = numel(time);
    
    % Smooth startup ramp
    ramp = min(time / 2.0, 1.0);
    
    % Reference Path: Lemniscate Figure-8
    R_path = 3.0;
    omega_path = 2*pi / t_end;
    x_ref = R_path * sin(omega_path * time);
    y_ref = (R_path / 2.0) * sin(2 * omega_path * time);
    
    dx_ref = gradient(x_ref, dt);
    dy_ref = gradient(y_ref, dt);
    theta_ref = unwrap(atan2(dy_ref, dx_ref));
    v_ref = sqrt(dx_ref.^2 + dy_ref.^2) .* ramp;
    omega_ref = gradient(theta_ref, dt) .* ramp;
    
    %% 3. STATE INITIALIZATION
    % State vector: [x; y; theta; v; omega; w_FL; w_FR; w_RL; w_RR]
    state = zeros(9, 1);
    state(1) = x_ref(1);
    state(2) = y_ref(1);
    state(3) = theta_ref(1);
    state(4) = 0.0; % Starts from rest
    state(5) = 0.0;
    
    % Data logs
    log_state   = zeros(9, N);
    log_torques = zeros(4, N);      % [tau_FL, tau_FR, tau_RL, tau_RR]
    log_powers  = zeros(4, N);
    log_errors  = zeros(3, N);      % [e_x, e_y, e_theta]
    log_energy  = zeros(1, N);      % Kinetic Energy (J)
    
    % Controller Gains
    Kp_v = 15.0;  Kd_v = 4.0;
    Kp_w = 20.0;  Kd_w = 5.0;
    
    fprintf('1. Integrating 4WD Skid-Steer physical dynamics (50 Hz)...\n');

    %% 4. MAIN SIMULATION INTEGRATION LOOP
    for k = 1:N
        x_curr  = state(1);
        y_curr  = state(2);
        th_curr = state(3);
        v_curr  = state(4);
        w_curr  = state(5);
        
        % 4.1 Tracking Error in Robot Local Frame
        dx_global = x_ref(k) - x_curr;
        dy_global = y_ref(k) - y_curr;
        
        e_long =  cos(th_curr)*dx_global + sin(th_curr)*dy_global;
        e_lat  = -sin(th_curr)*dx_global + cos(th_curr)*dy_global;
        e_th   = angdiff(th_curr, theta_ref(k));
        
        log_errors(:, k) = [e_long; e_lat; e_th];
        
        % 4.2 Desired Accelerations
        dv_ref_k = gradient_val(v_ref, k, dt);
        dw_ref_k = gradient_val(omega_ref, k, dt);
        
        a_v_cmd = dv_ref_k + Kp_v * e_long + Kd_v * (v_ref(k) - v_curr);
        a_w_cmd = dw_ref_k + Kp_w * e_th + 2.5 * e_lat + Kd_w * (omega_ref(k) - w_curr);
        
        % 4.3 Total Force & Yaw Torque
        F_total   = params.M * a_v_cmd + params.Cd * v_curr + params.mu * params.M * params.g * tanh(4.0 * v_curr);
        Tau_total = params.Iz * a_w_cmd + (params.mu * params.M * params.g * (params.effW / 2.0)) * tanh(4.0 * w_curr);
        
        % 4.4 4WD Skid-Steer Torque Allocation
        F_L = 0.5 * F_total - (Tau_total / params.effW);
        F_R = 0.5 * F_total + (Tau_total / params.effW);
        
        tau_FL = max(-params.MaxTorque, min(params.MaxTorque, (F_L / 2.0) * params.R));
        tau_RL = max(-params.MaxTorque, min(params.MaxTorque, (F_L / 2.0) * params.R));
        tau_FR = max(-params.MaxTorque, min(params.MaxTorque, (F_R / 2.0) * params.R));
        tau_RR = max(-params.MaxTorque, min(params.MaxTorque, (F_R / 2.0) * params.R));
        
        applied_torques = [tau_FL; tau_FR; tau_RL; tau_RR];
        log_torques(:, k) = applied_torques;
        
        % 4.5 Forward Dynamics
        F_act_L = (tau_FL + tau_RL) / params.R;
        F_act_R = (tau_FR + tau_RR) / params.R;
        F_net   = F_act_L + F_act_R;
        Tau_net = (F_act_R - F_act_L) * (params.effW / 2.0);
        
        v_dot = (F_net - params.Cd * v_curr - params.mu * params.M * params.g * tanh(4.0 * v_curr)) / params.M;
        w_dot = (Tau_net - (params.mu * params.M * params.g * (params.effW / 2.0)) * tanh(4.0 * w_curr)) / params.Iz;
        
        v_next  = v_curr + v_dot * dt;
        w_next  = w_curr + w_dot * dt;
        th_next = th_curr + w_curr * dt;
        x_next  = x_curr + (v_curr * cos(th_curr)) * dt;
        y_next  = y_curr + (v_curr * sin(th_curr)) * dt;
        
        % Wheel speeds
        w_wheel_L = (v_next - w_next * (params.effW / 2.0)) / params.R;
        w_wheel_R = (v_next + w_next * (params.effW / 2.0)) / params.R;
        
        state = [x_next; y_next; th_next; v_next; w_next; w_wheel_L; w_wheel_R; w_wheel_L; w_wheel_R];
        log_state(:, k) = state;
        
        log_powers(:, k) = applied_torques .* [w_wheel_L; w_wheel_R; w_wheel_L; w_wheel_R];
        log_energy(k) = 0.5 * params.M * v_next^2 + 0.5 * params.Iz * w_next^2 + ...
                        2 * (0.5 * params.Iw * w_wheel_L^2) + 2 * (0.5 * params.Iw * w_wheel_R^2);
    end
    fprintf('   ✅ Dynamic simulation complete! Plotting 6-panel telemetry dashboard...\n\n');

    %% 5. 6-PANEL TELEMETRY DASHBOARD
    figure('Name', 'AgileX Scout Mini AMR - Physical Dynamics & Telemetry', ...
           'Color', 'w', 'Position', [80, 80, 1350, 850]);
    
    % Panel 1: Trajectory Tracking (XY Plane)
    subplot(2, 3, 1);
    plot(x_ref, y_ref, 'k--', 'LineWidth', 1.5); hold on;
    plot(log_state(1, :), log_state(2, :), 'b-', 'LineWidth', 2.2);
    plot(log_state(1, 1), log_state(2, 1), 'go', 'MarkerFaceColor', 'g', 'MarkerSize', 8);
    plot(log_state(1, end), log_state(2, end), 'ro', 'MarkerFaceColor', 'r', 'MarkerSize', 8);
    grid on; axis equal;
    xlabel('X Position (m)'); ylabel('Y Position (m)');
    title('2D Trajectory & Path Following', 'FontWeight', 'bold');
    legend('Reference Path', 'Scout Mini Actual Path', 'Start', 'End Point', 'Location', 'best');
    
    % Panel 2: Linear & Angular Velocities
    subplot(2, 3, 2);
    plot(time, log_state(4, :), 'b-', 'LineWidth', 2.0); hold on;
    plot(time, v_ref, 'b--', 'LineWidth', 1.2);
    plot(time, log_state(5, :), 'r-', 'LineWidth', 2.0);
    plot(time, omega_ref, 'r--', 'LineWidth', 1.2);
    grid on; xlabel('Time (s)'); ylabel('Velocity');
    title('Chassis Velocities: v(t) & \omega(t)', 'FontWeight', 'bold');
    legend('v (Actual m/s)', 'v (Ref)', '\omega (Actual rad/s)', '\omega (Ref)', 'Location', 'best');
    
    % Panel 3: 4WD In-Hub Motor Torques
    subplot(2, 3, 3);
    plot(time, log_torques(1, :), 'b-', 'LineWidth', 1.8); hold on;
    plot(time, log_torques(2, :), 'r-', 'LineWidth', 1.8);
    yline(params.MaxTorque, 'k:', sprintf('Rated Limit (+%.1f Nm)', params.MaxTorque));
    yline(-params.MaxTorque, 'k:', sprintf('Rated Limit (-%.1f Nm)', params.MaxTorque));
    grid on; xlabel('Time (s)'); ylabel('Torque (Nm)');
    title('4WD In-Hub Motor Torques (Nm)', 'FontWeight', 'bold');
    legend('\tau_{Left} (FL/RL)', '\tau_{Right} (FR/RR)', 'Location', 'best');
    
    % Panel 4: 4-Wheel Rotational Speeds (RPM)
    subplot(2, 3, 4);
    rpm_L = (log_state(6, :) / (2*pi)) * 60;
    rpm_R = (log_state(7, :) / (2*pi)) * 60;
    plot(time, rpm_L, 'b-', 'LineWidth', 1.8); hold on;
    plot(time, rpm_R, 'r-', 'LineWidth', 1.8);
    yline(params.MaxRPM, 'k:', sprintf('Max Speed (%d RPM)', params.MaxRPM));
    grid on; xlabel('Time (s)'); ylabel('Wheel Speed (RPM)');
    title('4-Wheel Rotational Speeds (RPM)', 'FontWeight', 'bold');
    legend('Left Wheels (FL/RL)', 'Right Wheels (FR/RR)', 'Location', 'best');
    
    % Panel 5: Total Kinetic Energy & Power
    subplot(2, 3, 5);
    yyaxis left;
    plot(time, log_energy, 'm-', 'LineWidth', 2.0);
    ylabel('Kinetic Energy (J)');
    yyaxis right;
    total_power = sum(abs(log_powers), 1);
    plot(time, total_power, 'g-', 'LineWidth', 1.8);
    ylabel('Actuation Power (W)');
    grid on; xlabel('Time (s)');
    title('Energy & Actuation Power Dissipation', 'FontWeight', 'bold');
    legend('KE (Joules)', 'Power (Watts)', 'Location', 'best');
    
    % Panel 6: Tracking Errors
    subplot(2, 3, 6);
    plot(time, log_errors(1, :)*100, 'b-', 'LineWidth', 1.8); hold on;
    plot(time, log_errors(2, :)*100, 'r-', 'LineWidth', 1.8);
    plot(time, rad2deg(log_errors(3, :)), 'k-', 'LineWidth', 1.5);
    grid on; xlabel('Time (s)'); ylabel('Error');
    title('Path Tracking Errors', 'FontWeight', 'bold');
    legend('Longitudinal e_x (cm)', 'Lateral e_y (cm)', 'Heading e_\theta (deg)', 'Location', 'best');
    
    fprintf('===================================================================\n');
    fprintf('✅ Simulation Finished Successfully!\n');
    fprintf(' • Peak Speed: %.2f m/s\n', max(log_state(4, :)));
    fprintf(' • Max Wheel Torque: %.2f Nm (Rated Limit: %.1f Nm)\n', max(max(abs(log_torques))), params.MaxTorque);
    fprintf(' • Mean Lateral Error: %.2f cm\n', mean(abs(log_errors(2, :)))*100);
    fprintf(' • Mean Heading Error: %.2f deg\n', mean(abs(rad2deg(log_errors(3, :)))));
    fprintf('===================================================================\n');
end

function val = gradient_val(arr, idx, dt)
    if idx == 1
        val = (arr(2) - arr(1)) / dt;
    elseif idx == numel(arr)
        val = (arr(end) - arr(end-1)) / dt;
    else
        val = (arr(idx+1) - arr(idx-1)) / (2*dt);
    end
end

function d = angdiff(a, b)
    d = mod(b - a + pi, 2*pi) - pi;
end
