#!/usr/bin/env python3
"""
Motor and torque model for the Scout Mini (4 hub motors, skid steer).

Gazebo's DiffDrive plugin follows a velocity command rigidly: it has no motor, current or
battery. This node adds that missing layer and sits between the slip controller and Gazebo:

  /cmd_vel_safe (slip_control) -> [this node] -> /cmd_vel_motor -> Gazebo DiffDrive
  /odom (wheel speed)          -> [this node]   (the motors see the wheel speed, also while slipping)

Per control step (50 Hz)
  1. Required traction force and yaw moment of the commanded motion
       F = m a + c_rr m g sgn(v) + 0.5 rho Cd A v|v|
       M = Iz alpha + mu_turn m g (L/2) sgn(w)          (skid-steer turning resistance)
  2. Force per side  F_R = F/2 + M/B ,  F_L = F/2 - M/B   (B = wheel separation)
     Torque per wheel (two wheels per side)  tau = F_side r / 2 + tau_fric + b w
  3. Motor limit: current I = tau / kt, back-EMF e = ke w, terminal voltage V = e + R I.
     Available torque  tau_max(w) = kt * min(I_peak, (V_bat - ke |w|) / R).
     If a wheel would exceed it, the acceleration is reduced until it fits (saturated flag).
  4. Gearbox: motor torque = wheel torque / (N eta), motor speed = N * wheel speed. The Scout Mini
     has hub motors that drive the wheel directly, so N = 1 and eta = 1 by default (parameters
     gear_ratio and gear_efficiency allow a geared drive).
  5. Battery: open-circuit voltage falls linearly with the state of charge (25.2 V full to 21.0 V
     empty, 6 cells), terminal voltage V_bat = V_oc - R_int I_bat, so the available torque drops
     when the battery is low or the load is high. Electrical power P = V I per motor, state of
     charge by integration of the battery current.
  6. Traction utilisation  F_total / (mu m g)  for dry floor and for a low-friction patch.

Published
  /motor/torque       Float32MultiArray [left, right] N.m per wheel
  /motor/current      Float32MultiArray [left, right] A per motor
  /motor/power        Float32  total electrical power, W
  /motor/battery_soc  Float32  state of charge, %
  /motor/battery_voltage  Float32  terminal voltage under load, V
  /motor/saturated    Bool     a motor reached its torque limit this step
  /motor/traction_dry, /motor/traction_patch  Float32  force demand / (mu m g)
"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool, Float32, Float32MultiArray


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def sgn(x, eps=0.01):
    return 0.0 if abs(x) < eps else math.copysign(1.0, x)


class MotorModel(Node):
    def __init__(self):
        super().__init__('motor_model')
        P = self.declare_parameter
        # vehicle (mass = sum of the URDF link masses)
        self.m = P('mass', 28.3).value                      # kg
        self.r = P('wheel_radius', 0.08).value              # m
        self.B = P('wheel_separation', 0.612).value         # m
        self.L = P('wheel_base', 0.463).value               # m (front-rear axle distance)
        self.g = 9.81
        self.c_rr = P('rolling_resistance', 0.03).value
        self.mu_turn = P('turning_friction', 0.35).value    # skid-steer lateral scrub coefficient
        self.cdA = P('drag_area', 0.35 * 0.55).value        # Cd * frontal area, m^2
        self.rho = 1.2
        self.Iz = P('yaw_inertia', 1.6).value               # kg m^2
        self.tau_fric = P('joint_friction', 0.1).value      # N.m (URDF joint dynamics)
        self.b_vis = P('joint_damping', 0.1).value          # N.m s/rad
        # hub motor (4 x 150 W DC brushless, 24 V; AgileX SCOUT MINI user manual v1.0.1, section 1.2)
        self.V_nom = P('battery_voltage', 24.0).value       # V nominal (used to derive k_t)
        self.V_full = P('battery_full_voltage', 25.2).value # V, 6 cells x 4.2 V
        self.V_empty = P('battery_empty_voltage', 21.0).value  # V, 6 cells x 3.5 V
        self.R_int = P('battery_internal_resistance', 0.08).value  # ohm (assumed)
        self.N = P('gear_ratio', 1.0).value                 # motor turns per wheel turn (1 = direct-drive hub motor)
        self.eta = P('gear_efficiency', 1.0).value
        self.V_bat = self.V_full
        self.cap_Ah = P('battery_capacity', 15.0).value     # Ah
        self.kt = P('torque_constant', 0.64).value          # N.m/A (= back-EMF constant V s/rad; 24 V / 37.5 rad/s no-load)
        self.R = P('winding_resistance', 0.6).value        # ohm
        self.I_peak = P('peak_current', 23.4).value         # A  (3 x rated)
        self.I_rated = P('rated_current', 7.8).value       # A  (150 W / 30 rad/s = 5.0 N.m rated)
        self.P_idle = P('idle_power', 12.0).value           # W controller + sensors
        self.mu_dry = P('mu_dry', 0.25).value
        self.mu_patch = P('mu_patch', 0.04).value
        self.enforce = P('enforce_limits', True).value
        self.a_max = P('linear_accel_limit', 4.0).value     # m/s2 (same as DiffDrive)
        self.alpha_max = P('angular_accel_limit', 6.0).value
        self.cmd_timeout = P('cmd_timeout', 0.5).value
        self.dt = 0.02

        self.cmd = Twist()
        self.cmd_t = None
        self.out_v = 0.0
        self.out_w = 0.0
        self.prev_v = 0.0
        self.prev_w = 0.0
        self.wl = 0.0            # left wheel angular speed from wheel odometry, rad/s
        self.wr = 0.0
        self.soc = 100.0
        self.energy_Wh = 0.0
        self.charge_Ah = 0.0

        self.create_subscription(Twist, '/cmd_vel_safe', self.on_cmd, 10)
        self.create_subscription(Odometry, '/odom', self.on_odom, 20)
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel_motor', 10)
        self.pub_tau = self.create_publisher(Float32MultiArray, '/motor/torque', 10)
        self.pub_cur = self.create_publisher(Float32MultiArray, '/motor/current', 10)
        self.pub_pow = self.create_publisher(Float32, '/motor/power', 10)
        self.pub_soc = self.create_publisher(Float32, '/motor/battery_soc', 10)
        self.pub_vb = self.create_publisher(Float32, '/motor/battery_voltage', 10)
        self.pub_sat = self.create_publisher(Bool, '/motor/saturated', 10)
        self.pub_dry = self.create_publisher(Float32, '/motor/traction_dry', 10)
        self.pub_patch = self.create_publisher(Float32, '/motor/traction_patch', 10)
        self.create_timer(self.dt, self.step)
        self.create_timer(10.0, self.report)
        self.get_logger().info(
            f'motor_model: m={self.m} kg, r={self.r} m, kt={self.kt} N.m/A, '
            f'tau_peak={self.kt * self.I_peak * self.N:.1f} N.m, tau_rated={self.kt * self.I_rated * self.N:.1f} N.m, gear {self.N}:1, '
            f'enforce_limits={self.enforce}')

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def on_cmd(self, msg):
        self.cmd = msg
        self.cmd_t = self.now()

    def on_odom(self, msg):
        v = msg.twist.twist.linear.x
        w = msg.twist.twist.angular.z
        self.wl = (v - w * self.B / 2.0) / self.r
        self.wr = (v + w * self.B / 2.0) / self.r

    def tau_available(self, omega):
        """Maximum torque at the WHEEL at wheel speed omega (motor current limit, supply voltage, gearbox)."""
        om = self.N * abs(omega)
        i_volt = max(0.0, (self.V_bat - self.kt * om) / self.R)
        return self.kt * min(self.I_peak, i_volt) * self.N * self.eta

    def wheel_torques(self, v, a, w, alpha):
        F = (self.m * a + self.c_rr * self.m * self.g * sgn(v)
             + 0.5 * self.rho * self.cdA * v * abs(v))
        M = self.Iz * alpha + self.mu_turn * self.m * self.g * (self.L / 2.0) * sgn(w, 0.02)
        F_r = F / 2.0 + M / self.B
        F_l = F / 2.0 - M / self.B
        tl = F_l * self.r / 2.0 + self.tau_fric * sgn(self.wl) + self.b_vis * self.wl
        tr = F_r * self.r / 2.0 + self.tau_fric * sgn(self.wr) + self.b_vis * self.wr
        return tl, tr, F

    def step(self):
        dt = self.dt
        fresh = self.cmd_t is not None and (self.now() - self.cmd_t) < self.cmd_timeout
        tv = self.cmd.linear.x if fresh else 0.0
        tw = self.cmd.angular.z if fresh else 0.0

        # desired change of the output command, limited like the DiffDrive plugin
        dv = clamp(tv - self.out_v, -self.a_max * dt, self.a_max * dt)
        dw = clamp(tw - self.out_w, -self.alpha_max * dt, self.alpha_max * dt)
        a = dv / dt
        alpha = dw / dt
        tl, tr, F = self.wheel_torques(self.out_v, a, self.out_w, alpha)

        saturated = False
        if self.enforce:
            # reduce the acceleration until both sides are inside the motor torque limit
            for _ in range(8):
                lim_l = self.tau_available(self.wl)
                lim_r = self.tau_available(self.wr)
                if abs(tl) <= lim_l and abs(tr) <= lim_r:
                    break
                saturated = True
                a *= 0.6
                alpha *= 0.6
                tl, tr, F = self.wheel_torques(self.out_v, a, self.out_w, alpha)
            dv, dw = a * dt, alpha * dt
        self.out_v += dv
        self.out_w += dw
        if not fresh and abs(self.out_v) < 0.005 and abs(self.out_w) < 0.005:
            self.out_v = self.out_w = 0.0

        out = Twist()
        out.linear.x = float(self.out_v)
        out.angular.z = float(self.out_w)
        self.pub_cmd.publish(out)

        # current, electrical power and battery (two motors per side)
        # tl, tr are wheel torques; the motor shaft sees tau / (N eta) at N times the wheel speed
        il, ir = tl / (self.N * self.eta * self.kt), tr / (self.N * self.eta * self.kt)
        pl = 2.0 * (self.kt * self.N * abs(self.wl) + self.R * abs(il)) * abs(il)   # |V I| both motors
        pr = 2.0 * (self.kt * self.N * abs(self.wr) + self.R * abs(ir)) * abs(ir)
        # braking (motor and wheel moving opposite to the torque) returns little energy: counted as 0
        mech_l, mech_r = tl * self.wl, tr * self.wr
        if mech_l < 0:
            pl = 2.0 * self.R * il * il
        if mech_r < 0:
            pr = 2.0 * self.R * ir * ir
        p_tot = pl + pr + self.P_idle
        # battery: current from the open-circuit voltage, then the terminal voltage under load
        v_oc = self.V_empty + (self.V_full - self.V_empty) * self.soc / 100.0
        i_bat = p_tot / max(v_oc, 1.0)
        self.V_bat = max(v_oc - self.R_int * i_bat, 0.0)
        self.charge_Ah += i_bat * dt / 3600.0
        self.energy_Wh += p_tot * dt / 3600.0
        self.soc = clamp(100.0 - 100.0 * self.charge_Ah / self.cap_Ah, 0.0, 100.0)

        self.pub_tau.publish(Float32MultiArray(data=[float(tl), float(tr)]))
        self.pub_cur.publish(Float32MultiArray(data=[float(il), float(ir)]))
        self.pub_pow.publish(Float32(data=float(p_tot)))
        self.pub_soc.publish(Float32(data=float(self.soc)))
        self.pub_vb.publish(Float32(data=float(self.V_bat)))
        self.pub_sat.publish(Bool(data=bool(saturated)))
        weight = self.m * self.g
        self.pub_dry.publish(Float32(data=float(abs(F) / (self.mu_dry * weight))))
        self.pub_patch.publish(Float32(data=float(abs(F) / (self.mu_patch * weight))))
        self.last = (tl, tr, il, ir, p_tot)

    def report(self):
        if hasattr(self, 'last'):
            tl, tr, il, ir, p = self.last
            self.get_logger().info(
                f'torque L/R {tl:+.2f}/{tr:+.2f} N.m, current {il:+.1f}/{ir:+.1f} A, '
                f'power {p:.0f} W, battery {self.soc:.2f} % at {self.V_bat:.2f} V ({self.energy_Wh:.2f} Wh used)')


def main():
    rclpy.init()
    node = MotorModel()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.pub_cmd.publish(Twist())
            node.destroy_node()
        except Exception:
            pass
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
