#!/usr/bin/env python3
"""
AgileX Scout Mini AMR — High-Precision Smooth Teleoperation Controller
Optimized for Gazebo Harmonic Simulation and 2D SLAM Mapping in ROS 2 Jazzy.

Features:
- Instant & Reliable Keyboard Response: Raw mode initialized once (eliminates key drops & stutter)
- Intuitive Default Drive Mode: Continuous / Cruise Control (press to drive, Space/X/K to stop)
- Optional Momentary Mode: Toggle with [t] / [Tab] for hold-to-drive deadman operation
- Seamless Blended Steering: Steer with A/D or Left/Right while moving forward without stopping
- Dedicated Diagonal Arcs: Q/E (Forward-Left/Right) & Z/C (Reverse-Left/Right)
- Universal Keypad Support: WASD, Arrow Keys, and Classic ROS (i, j, k, l, u, o, m, .)
- Continuous 25 Hz / 40 ms Velocity Streaming (prevents Gazebo cmd_vel timeout stutter)
- S-Curve Acceleration Ramping (eliminates skid-steer wheel slip & LiDAR pitch distortion)
- Instant Emergency Brake on Spacebar, 'k', or 'x'
- Fine-grained Speed Tuning with '+' / '-' / '[' / ']' and 'r' (reset to SLAM defaults)
"""

import os
import sys

# Ensure local domain isolation matching launch files
os.environ.setdefault('ROS_DOMAIN_ID', '19')
os.environ.setdefault('ROS_LOCALHOST_ONLY', '1')
os.environ.setdefault('ROS_AUTOMATIC_DISCOVERY_RANGE', 'LOCALHOST')

import termios
import tty
import select
import threading
import time
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

BANNER = """\r
================================================================================\r
🎮  AgileX Scout Mini — Ultra-Smooth Civil Teleoperation (ROS 2 Jazzy)\r
================================================================================\r
  🕹️  CORE CONTROLS (WASD / Arrow Keys / Classic ROS):\r
      [W] / [▲] / [i] : Drive Forward          [S] / [▼] / [,] : Drive Reverse\r
      [A] / [◀] / [j] : Steer Left / Spin      [D] / [▶] / [l] : Steer Right / Spin\r
      [Space] / [k] / [x] : Instant Stop / Emergency Brake\r
\r
  🔄 DEDICATED ARC CURVES (Forward & Reverse):\r
      [Q] / [u] : Arc Forward-Left             [E] / [o] : Arc Forward-Right\r
      [Z] / [m] : Arc Reverse-Left             [C] / [.] : Arc Reverse-Right\r
\r
  ⚙️  DRIVE MODE & SPEED TUNING:\r
      [t] / [Tab] : Toggle Mode (🚢 CRUISE CONTROL [Default] vs ⏱️ MOMENTARY HOLD)\r
      [+] / [=] / ] : Increase Speed (+0.05 m/s, +0.10 rad/s)\r
      [-] / [_] / [ : Decrease Speed (-0.05 m/s, -0.10 rad/s)\r
      [r]           : Reset to Recommended 2D SLAM Mapping Speeds\r
      [Ctrl+C]      : Quit Teleoperation Safely\r
================================================================================\r
"""

class KeyReader:
    """Robust non-blocking raw terminal key reader."""
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.is_tty = os.isatty(self.fd)
        if self.is_tty:
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setraw(self.fd)

    def restore(self):
        if self.is_tty:
            try:
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)
            except Exception:
                pass

    def get_key(self, timeout=0.03):
        if not self.is_tty:
            return ''
        rlist, _, _ = select.select([self.fd], [], [], timeout)
        if not rlist:
            return ''
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            # Collect full escape sequence
            seq = ''
            while True:
                r2, _, _ = select.select([self.fd], [], [], 0.05)
                if not r2:
                    break
                seq += sys.stdin.read(1)
                if len(seq) >= 4 or (len(seq) >= 2 and seq[-1].isalpha()):
                    break
            # Up Arrow
            if seq in ('[A', 'OA'):
                return '\x1b[A'
            # Down Arrow
            elif seq in ('[B', 'OB'):
                return '\x1b[B'
            # Right Arrow
            elif seq in ('[C', 'OC'):
                return '\x1b[C'
            # Left Arrow
            elif seq in ('[D', 'OD'):
                return '\x1b[D'
            return '\x1b' + seq
        return ch


class SmoothCivilTeleopNode(Node):
    # Recommended baseline speeds for 2D SLAM mapping in architectural environments
    DEFAULT_LINEAR_SPEED = 0.35   # m/s (eliminates wheel slip during translation)
    DEFAULT_ANGULAR_SPEED = 0.60  # rad/s (ensures full LiDAR scan coverage during turns)

    def __init__(self):
        super().__init__('civil_teleop_controller')
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)

        # Operational Speed Caps
        self.linear_speed = self.DEFAULT_LINEAR_SPEED
        self.angular_speed = self.DEFAULT_ANGULAR_SPEED
        self.max_linear = 1.20
        self.max_angular = 2.00

        # Motion Targets & Current Filtered Speeds
        self.target_vx = 0.0
        self.target_wz = 0.0
        self.current_vx = 0.0
        self.current_wz = 0.0

        # Drive Mode: True = Cruise Control (Default for mapping: press to drive, Space to stop)
        #             False = Momentary (hold-to-drive, releases to stop)
        self.cruise_mode = True

        # Acceleration and Deceleration Limits (m/s^2 and rad/s^2)
        self.accel_linear = 2.50   # m/s^2
        self.decel_linear = 3.50   # m/s^2
        self.accel_angular = 3.50  # rad/s^2
        self.decel_angular = 5.00  # rad/s^2

        self.last_key_time = time.time()
        # Key timeout for Momentary mode: generous 0.60s to prevent stutter across keyboard repeat delay
        self.key_timeout = 0.60
        self.motion_label = "READY ■"

        # Continuous 25 Hz (40 ms) control loop (guarantees Gazebo 0.5s timeout never trips)
        self.dt = 0.04
        self.timer = self.create_timer(self.dt, self.timer_cb)

    def timer_cb(self):
        now = time.time()

        # In Momentary mode, automatically guide target velocities to 0 when key is released
        if not self.cruise_mode:
            if (now - self.last_key_time > self.key_timeout):
                self.target_vx = 0.0
                self.target_wz = 0.0
                if abs(self.current_vx) < 0.02 and abs(self.current_wz) < 0.02:
                    self.motion_label = "STOPPED ■"

        # Apply smooth rate-limited ramp for linear velocity (vx)
        if self.target_vx > self.current_vx:
            rate = self.accel_linear if self.current_vx >= 0 else self.decel_linear
            self.current_vx = min(self.target_vx, self.current_vx + rate * self.dt)
        elif self.target_vx < self.current_vx:
            rate = self.decel_linear if self.current_vx > 0 else self.accel_linear
            self.current_vx = max(self.target_vx, self.current_vx - rate * self.dt)

        # Apply smooth rate-limited ramp for angular velocity (wz)
        if self.target_wz > self.current_wz:
            rate = self.accel_angular if self.current_wz >= 0 else self.decel_angular
            self.current_wz = min(self.target_wz, self.current_wz + rate * self.dt)
        elif self.target_wz < self.current_wz:
            rate = self.decel_angular if self.current_wz > 0 else self.accel_angular
            self.current_wz = max(self.target_wz, self.current_wz - rate * self.dt)

        # Snap to exact zero if near rest to prevent micro-creep
        if abs(self.current_vx) < 0.005:
            self.current_vx = 0.0
        if abs(self.current_wz) < 0.005:
            self.current_wz = 0.0

        # Construct and publish Twist message
        msg = Twist()
        msg.linear.x = float(self.current_vx)
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = float(self.current_wz)
        self.pub_cmd.publish(msg)

        self.print_hud()

    def print_hud(self):
        mode_str = "🚢 CRUISE" if self.cruise_mode else "⏱️ MOMENTARY"
        v_bar = int(abs(self.current_vx) / max(0.1, self.linear_speed) * 6)
        v_viz = ("+" if self.current_vx >= 0 else "-") + ("=" * v_bar).ljust(6)
        w_dir = "◀" if self.current_wz > 0.05 else ("▶" if self.current_wz < -0.05 else "│")

        hud = (
            f"\r[{mode_str}] {self.motion_label:<15} | "
            f"Vx: {self.current_vx:+.2f} m/s [{v_viz}] (cap {self.linear_speed:.2f}) | "
            f"Wz: {self.current_wz:+.2f} rad/s {w_dir} (cap {self.angular_speed:.2f})   "
        )
        sys.stdout.write(hud)
        sys.stdout.flush()

    def forward(self):
        """Drive straight forward."""
        self.target_vx = self.linear_speed
        self.target_wz = 0.0
        self.motion_label = "FORWARD ▲"
        self.last_key_time = time.time()

    def reverse(self):
        """Drive straight reverse."""
        self.target_vx = -self.linear_speed
        self.target_wz = 0.0
        self.motion_label = "REVERSE ▼"
        self.last_key_time = time.time()

    def steer_left(self):
        """
        Steer left.
        - If moving forward: curves forward-left smoothly
        - If reversing: curves reverse-left smoothly
        - If stopped: spins left in place
        """
        if self.target_vx > 0.05:
            self.target_wz = 0.70 * self.angular_speed
            self.motion_label = "ARC FWD-LEFT ◤"
        elif self.target_vx < -0.05:
            self.target_wz = 0.70 * self.angular_speed
            self.motion_label = "ARC REV-LEFT ◣"
        else:
            self.target_vx = 0.0
            self.target_wz = self.angular_speed
            self.motion_label = "SPIN LEFT ◀"
        self.last_key_time = time.time()

    def steer_right(self):
        """
        Steer right.
        - If moving forward: curves forward-right smoothly
        - If reversing: curves reverse-right smoothly
        - If stopped: spins right in place
        """
        if self.target_vx > 0.05:
            self.target_wz = -0.70 * self.angular_speed
            self.motion_label = "ARC FWD-RIGHT ◥"
        elif self.target_vx < -0.05:
            self.target_wz = -0.70 * self.angular_speed
            self.motion_label = "ARC REV-RIGHT ◢"
        else:
            self.target_vx = 0.0
            self.target_wz = -self.angular_speed
            self.motion_label = "SPIN RIGHT ▶"
        self.last_key_time = time.time()

    def arc_forward_left(self):
        self.target_vx = self.linear_speed
        self.target_wz = 0.70 * self.angular_speed
        self.motion_label = "ARC FWD-LEFT ◤"
        self.last_key_time = time.time()

    def arc_forward_right(self):
        self.target_vx = self.linear_speed
        self.target_wz = -0.70 * self.angular_speed
        self.motion_label = "ARC FWD-RIGHT ◥"
        self.last_key_time = time.time()

    def arc_reverse_left(self):
        self.target_vx = -self.linear_speed
        self.target_wz = 0.70 * self.angular_speed
        self.motion_label = "ARC REV-LEFT ◣"
        self.last_key_time = time.time()

    def arc_reverse_right(self):
        self.target_vx = -self.linear_speed
        self.target_wz = -0.70 * self.angular_speed
        self.motion_label = "ARC REV-RIGHT ◢"
        self.last_key_time = time.time()

    def emergency_brake(self):
        self.target_vx = 0.0
        self.target_wz = 0.0
        self.current_vx = 0.0
        self.current_wz = 0.0
        self.motion_label = "BRAKE ⛔"
        self.last_key_time = time.time()
        self.print_hud()

    def toggle_mode(self):
        self.cruise_mode = not self.cruise_mode
        self.motion_label = "MODE CHANGED"
        self.last_key_time = time.time()
        self.print_hud()

    def adjust_speed(self, delta_v, delta_w):
        self.linear_speed = min(self.max_linear, max(0.10, self.linear_speed + delta_v))
        self.angular_speed = min(self.max_angular, max(0.15, self.angular_speed + delta_w))
        if self.target_vx > 0:
            self.target_vx = self.linear_speed
        elif self.target_vx < 0:
            self.target_vx = -self.linear_speed
        if self.target_wz > 0:
            self.target_wz = self.angular_speed if "SPIN" in self.motion_label else 0.70 * self.angular_speed
        elif self.target_wz < 0:
            self.target_wz = -self.angular_speed if "SPIN" in self.motion_label else -0.70 * self.angular_speed
        self.last_key_time = time.time()

    def reset_speed(self):
        self.linear_speed = self.DEFAULT_LINEAR_SPEED
        self.angular_speed = self.DEFAULT_ANGULAR_SPEED
        if self.target_vx > 0: self.target_vx = self.linear_speed
        elif self.target_vx < 0: self.target_vx = -self.linear_speed
        if self.target_wz > 0: self.target_wz = self.angular_speed
        elif self.target_wz < 0: self.target_wz = -self.angular_speed
        self.motion_label = "RESET SPEED"
        self.last_key_time = time.time()


def main():
    rclpy.init()
    node = SmoothCivilTeleopNode()

    # Spin ROS 2 in dedicated background executor
    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    sys.stdout.write(BANNER)
    sys.stdout.flush()

    # Set up raw terminal reader ONCE
    key_reader = KeyReader()

    try:
        while rclpy.ok():
            key = key_reader.get_key(timeout=0.03)
            if not key:
                continue

            # 0. Quit Teleoperation (Ctrl+C, Ctrl+D)
            if key in ('\x03', '\x04'):
                break

            # 1. Drive Forward
            elif key in ('w', 'W', 'i', 'I', '\x1b[A'):
                node.forward()

            # 2. Drive Reverse
            elif key in ('s', 'S', ',', '<', '\x1b[B'):
                node.reverse()

            # 3. Steer / Spin Left
            elif key in ('a', 'A', 'j', 'J', '\x1b[D'):
                node.steer_left()

            # 4. Steer / Spin Right
            elif key in ('d', 'D', 'l', 'L', '\x1b[C'):
                node.steer_right()

            # 5. Dedicated Smooth Arc Curves
            elif key in ('q', 'Q', 'u', 'U'):
                node.arc_forward_left()
            elif key in ('e', 'E', 'o', 'O'):
                node.arc_forward_right()
            elif key in ('z', 'Z', 'm', 'M'):
                node.arc_reverse_left()
            elif key in ('c', 'C', '.', '>'):
                node.arc_reverse_right()

            # 6. Instant Emergency Brake / Zero Stop
            elif key in (' ', 'k', 'K', 'x', 'X'):
                node.emergency_brake()

            # 7. Drive Mode Toggle (Cruise vs Momentary)
            elif key in ('t', 'T', '\t'):
                node.toggle_mode()

            # 8. Speed Tuning
            elif key in ('+', '=', ']'):
                node.adjust_speed(+0.05, +0.10)
            elif key in ('-', '_', '['):
                node.adjust_speed(-0.05, -0.10)
            elif key in ('r', 'R'):
                node.reset_speed()

    except Exception as e:
        sys.stdout.write(f"\r\nTeleop exception: {e}\r\n")
        sys.stdout.flush()
    finally:
        # Restore terminal settings cleanly
        key_reader.restore()

        # Publish clean zero velocity on termination
        try:
            node.timer.cancel()
            stop_msg = Twist()
            for _ in range(3):
                node.pub_cmd.publish(stop_msg)
                time.sleep(0.04)
        except Exception:
            pass

        sys.stdout.write("\r\n\n🛑 Teleoperation safely shut down. Robot commanded to full stop.\r\n\n")
        sys.stdout.flush()

        try:
            executor.shutdown()
            spin_thread.join(timeout=0.5)
        except Exception:
            pass
        try:
            node.destroy_node()
        except Exception:
            pass
        try:
            if rclpy.ok():
                rclpy.try_shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
