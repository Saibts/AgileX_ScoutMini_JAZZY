#!/usr/bin/env python3
"""
Wheel-slip detection, traction control and odometry correction for the Scout Mini.

Pipeline
  /cmd_vel (planner / teleop)  ->  [this node]  ->  /cmd_vel_safe  -> Gazebo DiffDrive
  /odom (wheel odometry) + /imu ->  [this node]  ->  /odom_corrected -> EKF

Detection
  The wheel odometry speed v_w over-reports when wheels spin on a low-friction surface.
  A ground-speed estimate v_est is built from the IMU longitudinal acceleration
  (complementary filter: IMU integrated, pulled toward v_w only while NOT slipping).
  slip_speed = v_w - v_est ; slip ratio = slip_speed / max(|v_w|, v_floor).
  Hysteresis (enter/exit thresholds + debounce) flags slip.

Correction
  1. Traction control: while slipping, the command scale is reduced and acceleration is
     limited, so wheel torque drops until grip returns; the scale recovers slowly after.
  2. Yaw-rate feedback: the commanded yaw rate is compared to the IMU gyro and the
     difference is fed back, which cancels sideways/yaw slip drift.
  3. Odometry correction: /odom_corrected carries v_est instead of v_w during slip and
     the IMU yaw, so the EKF is not fed the wheel-spin distance.
"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from std_msgs.msg import Bool, Float32


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def slew(current, target, max_rate, dt):
    step = max_rate * dt
    return current + clamp(target - current, -step, step)


class SlipControl(Node):
    def __init__(self):
        super().__init__('slip_control')
        P = self.declare_parameter
        self.enable = P('enable_correction', True).value
        # IMU mounting: which IMU axis is the robot's forward axis, and its sign
        self.acc_axis = P('imu_forward_axis', 'x').value
        self.acc_sign = P('imu_forward_sign', 1.0).value
        self.slip_enter = P('slip_enter_speed', 0.15).value      # m/s wheel-vs-ground
        self.slip_exit = P('slip_exit_speed', 0.06).value
        self.debounce = P('slip_debounce', 0.05).value           # s
        self.fuse_gain = P('fusion_gain', 3.0).value             # 1/s pull of v_est to v_w
        self.ratio_floor = P('ratio_speed_floor', 0.2).value
        self.slip_margin = P('allowed_wheel_lead', 0.12).value   # m/s wheel may lead ground while limited
        self.hold_time = P('traction_hold_time', 0.6).value      # s to keep limiting after slip clears
        self.acc_normal = P('linear_accel_limit', 4.0).value
        self.acc_slip = P('linear_accel_limit_slip', 0.8).value
        self.ang_acc = P('angular_accel_limit', 6.0).value
        self.yaw_kp = P('yaw_feedback_gain', 0.4).value
        self.yaw_corr_max = P('yaw_feedback_max', 0.6).value
        self.cmd_timeout = P('cmd_timeout', 0.5).value
        self.odom_deadband = P('odom_correction_deadband', 0.04).value  # m/s ignored as IMU noise
        self.fuse_gate = P('fusion_gate_width', 0.05).value             # m/s: trust IMU beyond this
        self.use_gravity_comp = P('gravity_compensation', True).value
        self.lat_sign = P('imu_lateral_sign', 1.0).value        # +1: IMU y axis points to the robot's left
        self.lat_gain = P('lateral_pull_gain', 2.0).value       # 1/s: sideways speed decays to 0 when gripping
        self.lat_gate = P('lateral_gate_width', 0.06).value     # m/s
        self.lat_deadband = P('lateral_deadband', 0.03).value   # m/s ignored as IMU noise

        self.cmd = Twist()
        self.cmd_time = None
        self.out_v = 0.0
        self.out_w = 0.0
        self.scale = 1.0
        self.v_w = 0.0
        self.v_est = 0.0
        self.acc_bias = 0.0
        self.acc_lp = 0.0
        self.gz = 0.0
        self.slip = False
        self.slip_candidate_t = 0.0
        self.quiet_t = 0.0
        self.steady_t = 0.0
        self.v_peak = 0.0
        self.vy = 0.0
        self.ay_lp = 0.0
        self.ay_bias = 0.0
        self.odom_prev_t = None
        self.a_w = 0.0
        self.slip_clear_t = -1e9
        self.last_imu_t = None
        self.have_odom = False
        self.have_imu = False
        # corrected pose (integrated from corrected speed + IMU yaw)
        self.px = self.py = self.yaw = 0.0
        self.yaw0_set = False

        self.create_subscription(Twist, '/cmd_vel', self.on_cmd, 10)
        self.create_subscription(Odometry, '/odom', self.on_odom, 20)
        self.create_subscription(Imu, '/imu', self.on_imu, 50)
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel_safe', 10)
        self.pub_odom = self.create_publisher(Odometry, '/odom_corrected', 20)
        self.pub_ratio = self.create_publisher(Float32, '/slip/ratio', 10)
        self.pub_active = self.create_publisher(Bool, '/slip/active', 10)
        self.pub_scale = self.create_publisher(Float32, '/slip/traction_scale', 10)
        self.pub_vest = self.create_publisher(Float32, '/slip/ground_speed_est', 10)
        # latched so a late-starting UI still learns whether correction is active
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        self.pub_enabled = self.create_publisher(Bool, '/slip/correction_enabled', latched)
        self.pub_enabled.publish(Bool(data=bool(self.enable)))
        self.dt_ctrl = 0.02
        self.create_timer(self.dt_ctrl, self.control_step)
        self.get_logger().info(
            f'slip_control up: correction={"ON" if self.enable else "OFF (monitor only)"}, '
            f'imu axis={self.acc_axis} sign={self.acc_sign:+.0f}')

    # ---------------------------------------------------------------- inputs
    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def on_cmd(self, msg):
        self.cmd = msg
        self.cmd_time = self.now()

    def on_odom(self, msg):
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        v = msg.twist.twist.linear.x
        if self.odom_prev_t is not None and 0.0 < t - self.odom_prev_t < 0.2:
            a_raw = (v - self.v_w) / (t - self.odom_prev_t)
            self.a_w += 0.25 * (a_raw - self.a_w)
        self.odom_prev_t = t
        self.v_w = v
        self.last_odom = msg
        if not self.have_odom:
            self.have_odom = True
        self.publish_corrected_odom(msg)

    def on_imu(self, msg):
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        a = msg.linear_acceleration.x if self.acc_axis == 'x' else msg.linear_acceleration.y
        a *= self.acc_sign
        self.gz = msg.angular_velocity.z
        if self.last_imu_t is None:
            self.last_imu_t = t
            return
        dt = t - self.last_imu_t
        self.last_imu_t = t
        if dt <= 0.0 or dt > 0.2:
            return
        self.have_imu = True
        if self.use_gravity_comp:
            # remove the gravity component leaked into the forward axis by chassis pitch/roll
            q = msg.orientation
            if q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z > 0.5:
                r_row = (2 * (q.x * q.z - q.w * q.y) if self.acc_axis == 'x'
                         else 2 * (q.y * q.z + q.w * q.x))
                a -= self.acc_sign * 9.81 * r_row
        self.acc_lp += 0.3 * (a - self.acc_lp)

        # Zero-velocity update only when wheels, accelerometer AND gyro all agree the robot is
        # at rest (wheels stopped alone does not mean stopped: the robot may still be sliding).
        quiet = (abs(self.v_w) < 0.02 and abs(self.acc_lp - self.acc_bias) < 0.05
                 and abs(self.gz) < 0.03)
        self.quiet_t = self.quiet_t + dt if quiet else 0.0
        if self.quiet_t > 0.3:
            self.acc_bias += 0.02 * (self.acc_lp - self.acc_bias)
            self.v_est = self.v_w
        else:
            self.v_est += (self.acc_lp - self.acc_bias) * dt
            if not self.slip:
                # pull toward wheel speed, but less and less as they disagree (early slip)
                # ... and only while wheel acceleration agrees with the IMU: if the wheels
                # accelerate/brake much harder than the body, they are slipping, not measuring
                d = self.v_w - self.v_est
                gate = (math.exp(-(d / self.fuse_gate) ** 2)
                        * math.exp(-((self.a_w - self.acc_lp + self.acc_bias) / 0.4) ** 2))
                self.v_est += clamp(self.fuse_gain * gate * dt, 0.0, 1.0) * d

        # A real slip needs the ground speed to still be changing. If the body has stopped
        # accelerating for 0.5 s yet wheel and IMU speeds still disagree, that is IMU drift,
        # not slip: re-converge the estimate to the wheels so the error cannot latch.
        if abs(self.acc_lp - self.acc_bias) < 0.08:
            self.steady_t += dt
        else:
            self.steady_t = 0.0
        if self.slip and self.steady_t > 0.5 and self.quiet_t <= 0.3:
            self.v_est += clamp(3.0 * dt, 0.0, 1.0) * (self.v_w - self.v_est)

        # Energy bound: the body can never be faster than the fastest recent wheel speed
        # (the peak decays no faster than the slowest realistic sliding deceleration).
        self.v_peak = max(abs(self.v_w), self.v_peak - 0.3 * dt)
        self.v_est = clamp(self.v_est, -(self.v_peak + 0.05), self.v_peak + 0.05)

        # --- lateral (sideways) slip: integrate lateral acceleration, remove the centripetal term
        ay = self.lat_sign * msg.linear_acceleration.y
        self.ay_lp += 0.3 * (ay - self.ay_lp)
        if self.quiet_t > 0.3:
            self.ay_bias += 0.02 * (self.ay_lp - self.ay_bias)
            self.vy = 0.0
        else:
            self.vy += (self.ay_lp - self.ay_bias - self.gz * self.v_est) * dt
            gate_y = math.exp(-(self.vy / self.lat_gate) ** 2)   # grip => no sideways motion
            self.vy -= clamp(self.lat_gain * gate_y * dt, 0.0, 1.0) * self.vy
            self.vy = clamp(self.vy, -1.5, 1.5)

        # --- slip detection with hysteresis + debounce
        slip_speed = self.v_w - self.v_est
        if not self.slip:
            if abs(slip_speed) > self.slip_enter:
                self.slip_candidate_t += dt
                if self.slip_candidate_t >= self.debounce:
                    self.slip = True
                    self.get_logger().warn(
                        f'SLIP detected: wheel {self.v_w:+.2f} m/s vs ground {self.v_est:+.2f} m/s')
            else:
                self.slip_candidate_t = 0.0
        elif abs(slip_speed) < self.slip_exit:
            self.slip = False
            self.slip_clear_t = self.now()
            self.slip_candidate_t = 0.0
            self.get_logger().info('Grip recovered')

        ratio = clamp(slip_speed / max(abs(self.v_w), self.ratio_floor), -1.0, 1.0)
        self.pub_ratio.publish(Float32(data=float(ratio)))
        self.pub_active.publish(Bool(data=self.slip))
        self.pub_vest.publish(Float32(data=float(self.v_est)))

    # --------------------------------------------------------------- outputs
    def publish_corrected_odom(self, msg):
        out = Odometry()
        out.header = msg.header
        out.child_frame_id = msg.child_frame_id
        v = self.v_w
        if self.enable:
            d = self.v_w - self.v_est
            if abs(d) > self.odom_deadband:
                # remove the wheel-spin part (beyond sensor noise); never flip direction
                v = self.v_w - math.copysign(abs(d) - self.odom_deadband, d)
                if v * self.v_w < 0.0:
                    v = 0.0
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if not hasattr(self, '_odom_t'):
            self._odom_t = stamp
            self.px = msg.pose.pose.position.x
            self.py = msg.pose.pose.position.y
            q = msg.pose.pose.orientation
            self.yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        dt = clamp(stamp - self._odom_t, 0.0, 0.2)
        self._odom_t = stamp
        wz = self.gz if self.have_imu else msg.twist.twist.angular.z
        vy = 0.0
        if self.enable and abs(self.vy) > self.lat_deadband:
            vy = self.vy - math.copysign(self.lat_deadband, self.vy)
        self.yaw += wz * dt
        self.px += (v * math.cos(self.yaw) - vy * math.sin(self.yaw)) * dt
        self.py += (v * math.sin(self.yaw) + vy * math.cos(self.yaw)) * dt
        out.pose.pose.position.x = self.px
        out.pose.pose.position.y = self.py
        out.pose.pose.orientation.z = math.sin(self.yaw / 2)
        out.pose.pose.orientation.w = math.cos(self.yaw / 2)
        out.pose.covariance = msg.pose.covariance
        out.twist.twist.linear.x = v
        out.twist.twist.linear.y = vy
        out.twist.twist.angular.z = wz
        out.twist.covariance = list(msg.twist.covariance)
        out.twist.covariance[7] = 0.02      # vy variance (IMU-derived, noisier than wheels)
        self.pub_odom.publish(out)

    def control_step(self):
        dt = self.dt_ctrl
        fresh = self.cmd_time is not None and (self.now() - self.cmd_time) < self.cmd_timeout
        cv = self.cmd.linear.x if fresh else 0.0
        cw = self.cmd.angular.z if fresh else 0.0

        if not self.enable:
            out = Twist()
            out.linear.x, out.angular.z = cv, cw
            self.pub_cmd.publish(out)
            return

        # Traction control (ABS / TCS style): while slipping, and briefly afterwards, the
        # wheel speed command may lead the estimated ground speed by only a small margin.
        # The wheels then stay near peak grip, so the robot accelerates (or brakes) as hard
        # as the surface allows without spinning or locking.
        limiting = self.slip or (self.now() - self.slip_clear_t) < self.hold_time
        target_v = cv
        if limiting:
            target_v = clamp(cv, self.v_est - self.slip_margin, self.v_est + self.slip_margin)
            # the limiter may only hold back or release a brake; it must never spin the
            # wheels faster than both the command and the current output (no runaway if
            # the ground-speed estimate is wrong)
            target_v = clamp(target_v, min(cv, self.out_v), max(cv, self.out_v))
        self.out_v = slew(self.out_v, target_v, self.acc_normal, dt)
        self.scale = clamp(abs(self.out_v) / abs(cv), 0.0, 1.0) if abs(cv) > 0.05 else 1.0

        # yaw-rate feedback (cancels yaw drift from lateral slip)
        w_target = cw
        if self.have_imu and fresh:
            w_target += clamp(self.yaw_kp * (cw - self.gz), -self.yaw_corr_max, self.yaw_corr_max)
        w_acc = self.ang_acc * (0.5 if limiting else 1.0)
        self.out_w = slew(self.out_w, w_target, w_acc, dt)
        if not fresh and abs(self.out_w) < 0.01:
            self.out_w = 0.0

        out = Twist()
        out.linear.x = float(self.out_v)
        out.angular.z = float(self.out_w)
        self.pub_cmd.publish(out)
        self.pub_scale.publish(Float32(data=float(self.scale)))


def main():
    rclpy.init()
    node = SlipControl()
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
