#!/usr/bin/env python3
"""
=============================================================================
 AgileX Scout Mini AMR: 4WD Skid-Steer Physical Dynamics & Telemetry Simulator
=============================================================================
 Local Path: /home/sailakshmi/agilex/matlab/scout_mini_dynamics_sim.py

 Robot Specifications (AgileX Scout Mini):
 - Total Mass (M): 30.0 kg
 - Yaw Moment of Inertia (Iz): 1.62 kg*m^2
 - Wheel Mass & Radius: m_w = 1.19 kg, R = 0.080 m (160 mm diameter)
 - Track Width (W): 0.612 m | Wheelbase (L): 0.450 m
 - 4WD In-Hub Motors: Rated Torque = 17.5 Nm/wheel, Max Speed = 360 RPM
 - Skid-Steer ICR Slip Parameter: alpha = 1.05
=============================================================================
"""

import numpy as np
import matplotlib.pyplot as plt

def run_simulation(path_type='figure8'):
    print("===================================================================")
    print("🚜 AgileX Scout Mini: 4WD Physical Dynamics & Telemetry Simulation")
    print("===================================================================\n")

    # --- 1. PHYSICAL CONSTANTS (From SolidWorks CAD & AgileX Spec) ---
    M          = 30.0        # Robot chassis + payload mass (kg)
    Iz         = 1.62        # Yaw Moment of Inertia (kg*m^2)
    Iw         = 0.0047      # Single wheel moment of inertia (kg*m^2)
    W          = 0.612       # Effective track width (m)
    L          = 0.450       # Wheelbase (m)
    R          = 0.080       # Tire radius (m)
    alpha      = 1.05        # Skid-steer ICR slip factor
    effW       = W * alpha   # Effective track width with tire scrub
    mu         = 0.15        # Rolling resistance coefficient
    Cd         = 0.50        # Viscous / aerodynamic drag (N*s/m)
    g          = 9.81        # Gravity (m/s^2)
    max_torque = 17.5        # Max in-hub torque per wheel (Nm)
    max_rpm    = 360.0       # Max motor rotational speed (RPM)

    # --- 2. TIME SETUP & REFERENCE PATH GENERATION ---
    dt    = 0.02             # Time step (50 Hz)
    t_end = 25.0             # Duration (s)
    time  = np.arange(0, t_end, dt)
    N     = len(time)

    # Smooth startup profile to avoid unrealistic jerk at t=0
    ramp = np.clip(time / 2.0, 0.0, 1.0)

    if path_type == 'figure8':
        R_path = 3.0
        omega_path = 2 * np.pi / t_end
        x_ref = R_path * np.sin(omega_path * time)
        y_ref = (R_path / 2.0) * np.sin(2 * omega_path * time)
    elif path_type == 'circle':
        R_path = 2.5
        omega_path = 2 * np.pi / t_end
        x_ref = R_path * np.cos(omega_path * time) - R_path
        y_ref = R_path * np.sin(omega_path * time)
    else: # S-curve
        x_ref = 0.3 * time
        y_ref = 1.5 * np.sin(2 * np.pi * time / 12.0)

    # Compute continuous velocity & curvature profiles
    dx_ref  = np.gradient(x_ref, dt)
    dy_ref  = np.gradient(y_ref, dt)
    theta_ref = np.unwrap(np.arctan2(dy_ref, dx_ref))
    v_ref   = np.sqrt(dx_ref**2 + dy_ref**2) * ramp
    omega_ref = np.gradient(theta_ref, dt) * ramp

    # --- 3. STATE INITIALIZATION ---
    # State: [x, y, theta, v, omega, w_FL, w_FR, w_RL, w_RR]
    state = np.zeros(9)
    state[0] = x_ref[0]
    state[1] = y_ref[0]
    state[2] = theta_ref[0]
    state[3] = 0.0           # Starts from rest (smooth realistic acceleration)
    state[4] = 0.0

    # Data logging matrices
    log_state   = np.zeros((9, N))
    log_torques = np.zeros((4, N))
    log_powers  = np.zeros((4, N))
    log_errors  = np.zeros((3, N))
    log_energy  = np.zeros(N)

    # PID & Dynamic Feedback Controller Gains
    Kp_v, Kd_v = 15.0, 4.0
    Kp_w, Kd_w = 20.0, 5.0

    print("1. Integrating 4WD Skid-Steer multi-body physics (50 Hz)...")

    # --- 4. NUMERICAL INTEGRATION LOOP ---
    for k in range(N):
        x_curr, y_curr, th_curr = state[0], state[1], state[2]
        v_curr, w_curr = state[3], state[4]

        # Tracking error in robot frame
        dx_g = x_ref[k] - x_curr
        dy_g = y_ref[k] - y_curr
        e_long = np.cos(th_curr)*dx_g + np.sin(th_curr)*dy_g
        e_lat  = -np.sin(th_curr)*dx_g + np.cos(th_curr)*dy_g
        e_th   = (theta_ref[k] - th_curr + np.pi) % (2*np.pi) - np.pi

        log_errors[:, k] = [e_long, e_lat, e_th]

        # Dynamic velocity controller: compute required linear & angular acceleration
        v_ref_k = v_ref[k]
        w_ref_k = omega_ref[k]
        dv_ref_k = np.gradient(v_ref, dt)[k]
        dw_ref_k = np.gradient(omega_ref, dt)[k]

        a_v_cmd = dv_ref_k + Kp_v * e_long + Kd_v * (v_ref_k - v_curr)
        a_w_cmd = dw_ref_k + Kp_w * e_th + 2.5 * e_lat + Kd_w * (w_ref_k - w_curr)

        # Dynamic Forces: Mass Inertia + Tire Rolling Friction + Drag
        F_total   = M * a_v_cmd + Cd * v_curr + mu * M * g * np.tanh(4.0 * v_curr)
        Tau_total = Iz * a_w_cmd + (mu * M * g * (effW / 2.0)) * np.tanh(4.0 * w_curr)

        # Skid-Steer 4-Wheel Torque Distribution
        F_L = 0.5 * F_total - (Tau_total / effW)
        F_R = 0.5 * F_total + (Tau_total / effW)

        # In-hub individual wheel torques (FL, RL, FR, RR)
        tau_FL = np.clip((F_L / 2.0) * R, -max_torque, max_torque)
        tau_RL = np.clip((F_L / 2.0) * R, -max_torque, max_torque)
        tau_FR = np.clip((F_R / 2.0) * R, -max_torque, max_torque)
        tau_RR = np.clip((F_R / 2.0) * R, -max_torque, max_torque)

        applied_torques = np.array([tau_FL, tau_FR, tau_RL, tau_RR])
        log_torques[:, k] = applied_torques

        # Forward Physical Dynamics Integration
        F_act_L = (tau_FL + tau_RL) / R
        F_act_R = (tau_FR + tau_RR) / R
        F_net   = F_act_L + F_act_R
        Tau_net = (F_act_R - F_act_L) * (effW / 2.0)

        v_dot = (F_net - Cd * v_curr - mu * M * g * np.tanh(4.0 * v_curr)) / M
        w_dot = (Tau_net - (mu * M * g * (effW / 2.0)) * np.tanh(4.0 * w_curr)) / Iz

        v_next  = v_curr + v_dot * dt
        w_next  = w_curr + w_dot * dt
        th_next = th_curr + w_curr * dt
        x_next  = x_curr + (v_curr * np.cos(th_curr)) * dt
        y_next  = y_curr + (v_curr * np.sin(th_curr)) * dt

        # 4-wheel rotational speeds (rad/s) & RPM
        w_wheel_L = (v_next - w_next * (effW / 2.0)) / R
        w_wheel_R = (v_next + w_next * (effW / 2.0)) / R

        # State logging
        state = np.array([x_next, y_next, th_next, v_next, w_next, w_wheel_L, w_wheel_R, w_wheel_L, w_wheel_R])
        log_state[:, k] = state

        # Instantaneous power (W) & kinetic energy (J)
        wheel_speeds = np.array([w_wheel_L, w_wheel_R, w_wheel_L, w_wheel_R])
        log_powers[:, k] = applied_torques * wheel_speeds
        log_energy[k]    = 0.5 * M * v_next**2 + 0.5 * Iz * w_next**2 + 4 * (0.5 * Iw * ((w_wheel_L**2 + w_wheel_R**2)/2))

    print("2. Generating publication-quality telemetry dashboard...")

    # --- 5. 6-PANEL TELEMETRY DASHBOARD ---
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.5))
    fig.canvas.manager.set_window_title("AgileX Scout Mini AMR - Physical Dynamics & Telemetry")

    # Panel 1: 2D Trajectory
    axs[0, 0].plot(x_ref, y_ref, 'k--', linewidth=1.5, label='Reference Trajectory')
    axs[0, 0].plot(log_state[0], log_state[1], 'b-', linewidth=2.2, label='Scout Mini Actual Path')
    axs[0, 0].plot(log_state[0, 0], log_state[1, 0], 'go', markersize=8, label='Start (0,0)')
    axs[0, 0].plot(log_state[0, -1], log_state[1, -1], 'ro', markersize=8, label='End Point')
    axs[0, 0].set_title('2D Trajectory & Path Following', fontsize=12, fontweight='bold')
    axs[0, 0].set_xlabel('X Position (m)')
    axs[0, 0].set_ylabel('Y Position (m)')
    axs[0, 0].axis('equal')
    axs[0, 0].grid(True)
    axs[0, 0].legend(loc='best', frameon=True)

    # Panel 2: Chassis Linear & Angular Velocities
    axs[0, 1].plot(time, log_state[3], 'b-', linewidth=2.0, label='Linear Velocity v (m/s)')
    axs[0, 1].plot(time, v_ref, 'b--', linewidth=1.2, alpha=0.7, label='v Ref')
    axs[0, 1].plot(time, log_state[4], 'r-', linewidth=2.0, label=r'Angular Velocity $\omega$ (rad/s)')
    axs[0, 1].plot(time, omega_ref, 'r--', linewidth=1.2, alpha=0.7, label=r'$\omega$ Ref')
    axs[0, 1].set_title(r'Chassis Velocities: $v(t)$ and $\omega(t)$', fontsize=12, fontweight='bold')
    axs[0, 1].set_xlabel('Time (s)')
    axs[0, 1].set_ylabel('Velocity')
    axs[0, 1].grid(True)
    axs[0, 1].legend(loc='best', frameon=True)

    # Panel 3: 4WD In-Hub Motor Torques
    axs[0, 2].plot(time, log_torques[0], 'b-', linewidth=1.8, label=r'$\tau_{Left}$ (FL, RL)')
    axs[0, 2].plot(time, log_torques[1], 'r-', linewidth=1.8, label=r'$\tau_{Right}$ (FR, RR)')
    axs[0, 2].axhline(max_torque, color='k', linestyle=':', label=f'Rated Limit (±{max_torque} Nm)')
    axs[0, 2].axhline(-max_torque, color='k', linestyle=':')
    axs[0, 2].set_title('4WD In-Hub Motor Torques (Nm)', fontsize=12, fontweight='bold')
    axs[0, 2].set_xlabel('Time (s)')
    axs[0, 2].set_ylabel('Torque (Nm)')
    axs[0, 2].set_ylim([-max_torque - 3, max_torque + 3])
    axs[0, 2].grid(True)
    axs[0, 2].legend(loc='best', frameon=True)

    # Panel 4: 4-Wheel Rotational Speeds (RPM)
    rpm_L = (log_state[5] / (2 * np.pi)) * 60
    rpm_R = (log_state[6] / (2 * np.pi)) * 60
    axs[1, 0].plot(time, rpm_L, 'b-', linewidth=1.8, label='Left Wheels (FL, RL)')
    axs[1, 0].plot(time, rpm_R, 'r-', linewidth=1.8, label='Right Wheels (FR, RR)')
    axs[1, 0].axhline(max_rpm, color='k', linestyle=':', label=f'Max Speed ({max_rpm} RPM)')
    axs[1, 0].set_title('4-Wheel Rotational Speeds (RPM)', fontsize=12, fontweight='bold')
    axs[1, 0].set_xlabel('Time (s)')
    axs[1, 0].set_ylabel('Wheel Speed (RPM)')
    axs[1, 0].grid(True)
    axs[1, 0].legend(loc='best', frameon=True)

    # Panel 5: Electrical / Mechanical Actuation Power
    ax_energy = axs[1, 1]
    ax_power = ax_energy.twinx()
    l1 = ax_energy.plot(time, log_energy, 'm-', linewidth=2.0, label='Kinetic Energy (J)')
    tot_power = np.sum(np.abs(log_powers), axis=0)
    l2 = ax_power.plot(time, tot_power, 'g-', linewidth=1.8, label='Actuation Power (W)')
    ax_energy.set_title('Energy & Actuation Power Dissipation', fontsize=12, fontweight='bold')
    ax_energy.set_xlabel('Time (s)')
    ax_energy.set_ylabel('Kinetic Energy (J)', color='m', fontweight='bold')
    ax_power.set_ylabel('Actuation Power (W)', color='g', fontweight='bold')
    ax_energy.grid(True)
    
    # Combined legend
    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax_energy.legend(lines, labels, loc='upper right', frameon=True)

    # Panel 6: Tracking Errors
    axs[1, 2].plot(time, log_errors[0] * 100, 'b-', linewidth=1.8, label=r'Longitudinal $e_x$ (cm)')
    axs[1, 2].plot(time, log_errors[1] * 100, 'r-', linewidth=1.8, label=r'Lateral $e_y$ (cm)')
    axs[1, 2].plot(time, np.rad2deg(log_errors[2]), 'k-', linewidth=1.5, label=r'Heading $e_\theta$ (deg)')
    axs[1, 2].set_title('Path Tracking Errors', fontsize=12, fontweight='bold')
    axs[1, 2].set_xlabel('Time (s)')
    axs[1, 2].set_ylabel('Error')
    axs[1, 2].grid(True)
    axs[1, 2].legend(loc='best', frameon=True)

    plt.tight_layout()
    print("===================================================================")
    print("✅ Simulation Finished Successfully!")
    print(f" • Peak Speed: {np.max(log_state[3]):.2f} m/s")
    print(f" • Max Wheel Torque: {np.max(np.abs(log_torques)):.2f} Nm (Rated Limit: {max_torque} Nm)")
    print(f" • Max Wheel Speed: {np.max([rpm_L, rpm_R]):.1f} RPM (Limit: {max_rpm} RPM)")
    print(f" • Mean Lateral Error: {np.mean(np.abs(log_errors[1]))*100:.2f} cm")
    print(f" • Mean Heading Error: {np.mean(np.abs(np.rad2deg(log_errors[2]))):.2f}°")
    print("===================================================================\n")
    plt.show()

if __name__ == '__main__':
    run_simulation('figure8')
