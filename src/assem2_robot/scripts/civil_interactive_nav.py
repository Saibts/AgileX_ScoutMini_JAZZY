#!/usr/bin/env python3
"""
AgileX Scout Mini 4WD AMR — Civil Architectural Interactive Ground Station
==========================================================================
Precision Telemetry, Live Robot First-Person POV, and Point-to-Navigate Map.
Strictly compliant with the AgileX Scout Mini technical datasheet.
"""

import os
import sys
import math
import time
import threading
import numpy as np
import cv2

# ROS 2
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry, Path, OccupancyGrid
from sensor_msgs.msg import Image, LaserScan
from nav2_msgs.action import NavigateToPose
import tf2_ros

# PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QImage, QPolygonF
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QCheckBox, QFrame, QGroupBox, QStatusBar, QMessageBox
)

# World & Occupancy Grid Extents
ORIGIN_X = -11.0
ORIGIN_Y = -9.0
MAP_RES = 0.05
MAP_W = 440
MAP_H = 360

# Architectural Zoned Rooms
ROOMS = [
    {"name": "Entrance Foyer & Atrium", "xmin": -2.5, "xmax": 2.5, "ymin": -8.0, "ymax": -1.2, "color": QColor(30, 110, 70, 70)},
    {"name": "Central Arterial Corridor", "xmin": -10.0, "xmax": 10.0, "ymin": -1.2, "ymax": 1.2, "color": QColor(40, 80, 150, 70)},
    {"name": "Structural Materials Lab", "xmin": -10.0, "xmax": -2.5, "ymin": 1.2, "ymax": 8.0, "color": QColor(140, 60, 40, 70)},
    {"name": "Conference & Seminar Hall", "xmin": -2.5, "xmax": 2.5, "ymin": 1.2, "ymax": 8.0, "color": QColor(100, 50, 130, 70)},
    {"name": "CAD & Robotics Studio", "xmin": 2.5, "xmax": 10.0, "ymin": 1.2, "ymax": 8.0, "color": QColor(30, 120, 120, 70)},
    {"name": "Department Archives Vault", "xmin": 2.5, "xmax": 10.0, "ymin": -8.0, "ymax": -1.2, "color": QColor(130, 100, 30, 70)},
    {"name": "Geotechnical Survey Lab", "xmin": -10.0, "xmax": -2.5, "ymin": -8.0, "ymax": -1.2, "color": QColor(100, 70, 100, 70)},
]

# Quick Pre-configured Civil Stations
STATIONS = [
    {"id": 1, "name": "Station 1: Foyer (Home)", "x": 0.0, "y": -3.5, "yaw": 90.0},
    {"id": 2, "name": "Station 2: Corridor Hub", "x": 0.0, "y": 0.0, "yaw": 0.0},
    {"id": 3, "name": "Station 3: Materials Lab", "x": -6.0, "y": 3.5, "yaw": 90.0},
    {"id": 4, "name": "Station 4: Conference Hall", "x": 0.0, "y": 2.7, "yaw": 90.0},
    {"id": 5, "name": "Station 5: CAD Studio", "x": 6.0, "y": 3.5, "yaw": 90.0},
    {"id": 6, "name": "Station 6: Archives Vault", "x": 5.5, "y": -4.5, "yaw": -90.0},
    {"id": 7, "name": "Station 7: Geotechnical Lab", "x": -5.5, "y": -4.5, "yaw": -90.0},
]


def world_to_map(x, y):
    u = int(round((x - ORIGIN_X) / MAP_RES))
    v = int(round((y - ORIGIN_Y) / MAP_RES))
    r = MAP_H - 1 - v
    c = u
    return r, c


def map_to_world(r, c):
    v = MAP_H - 1 - r
    u = c
    x = ORIGIN_X + u * MAP_RES
    y = ORIGIN_Y + v * MAP_RES
    return x, y


def get_room_name(x, y):
    for room in ROOMS:
        if room["xmin"] <= x <= room["xmax"] and room["ymin"] <= y <= room["ymax"]:
            return room["name"]
    if -10.0 <= x <= 10.0 and -8.0 <= y <= 8.0:
        return "Civil Facility Interior"
    return "Exterior Grounds"


class RosWorker(QtCore.QObject):
    """ROS 2 Node background worker with sim_time and lifecycle readiness."""
    image_received = pyqtSignal(np.ndarray)
    pose_received = pyqtSignal(float, float, float, float, float) # x, y, yaw, vx, wz
    path_received = pyqtSignal(list)
    scan_received = pyqtSignal(float)
    nav_status_changed = pyqtSignal(str, float) # status, distance_remaining
    nav_ready_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.node = None
        self.action_client = None
        self.goal_handle = None
        self.distance_remaining = 0.0
        self.nav_status = "INITIALIZING"
        self.nav_ready = False
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.running = True
        self.target_x = None
        self.target_y = None

        # Load civil map for obstacle clearance calculation
        pkg_dir = os.path.expanduser("~/agilex/src/assem2_robot")
        self.map_pgm = os.path.join(pkg_dir, "maps", "civil_map.pgm")
        if os.path.exists(self.map_pgm):
            img = cv2.imread(self.map_pgm, cv2.IMREAD_GRAYSCALE)
            self.map_arr = img
        else:
            self.map_arr = np.full((MAP_H, MAP_W), 254, dtype=np.uint8)

        # Precompute Euclidean Distance Transform for clearance snapping
        free_mask = (self.map_arr == 254).astype(np.uint8)
        self.dist_to_obs = cv2.distanceTransform(free_mask, cv2.DIST_L2, 5) * MAP_RES

    def start(self):
        if not rclpy.ok():
            rclpy.init(args=sys.argv)

        # Initialize node with use_sim_time enabled to match Gazebo simulation clock
        self.node = rclpy.create_node(
            "civil_interactive_nav_gui",
            parameter_overrides=[
                Parameter("use_sim_time", Parameter.Type.BOOL, True)
            ]
        )

        # map<-odom transform: odometry is in the odom frame, while the map, goals and /plan are in map
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self.node)

        # Subscriptions
        self.node.create_subscription(Image, "/camera/image_raw", self.image_cb, 10)
        self.node.create_subscription(Odometry, "/odometry/filtered", self.odom_cb, 10)
        self.node.create_subscription(Path, "/plan", self.plan_cb, 10)
        self.node.create_subscription(LaserScan, "/scan", self.scan_cb, 10)

        # Publishers
        self.goal_pub = self.node.create_publisher(PoseStamped, "/goal_pose", 10)
        self.cmd_vel_pub = self.node.create_publisher(Twist, "/cmd_vel", 10)

        # Nav2 Action Client
        self.action_client = ActionClient(self.node, NavigateToPose, "navigate_to_pose")

        # Spin in background thread
        self.thread = threading.Thread(target=self.spin, daemon=True)
        self.thread.start()

        # Readiness monitor thread
        self.ready_thread = threading.Thread(target=self.monitor_readiness, daemon=True)
        self.ready_thread.start()

    def spin(self):
        while self.running and rclpy.ok():
            rclpy.spin_once(self.node, timeout_sec=0.02)

    def monitor_readiness(self):
        """Monitors Nav2 action server readiness and AMCL convergence."""
        while self.running and rclpy.ok():
            if not self.nav_ready:
                if self.action_client.server_is_ready():
                    self.nav_ready = True
                    self.nav_status = "NAV2 READY"
                    self.nav_status_changed.emit(self.nav_status, 0.0)
                    self.nav_ready_signal.emit(True)
                    break
            time.sleep(0.5)

    def image_cb(self, msg: Image):
        try:
            if msg.encoding in ['rgb8', 'bgr8']:
                channels = 3
            elif msg.encoding == 'mono8':
                channels = 1
            else:
                channels = 3

            arr = np.frombuffer(msg.data, dtype=np.uint8)
            if channels == 3:
                arr = arr.reshape((msg.height, msg.width, 3))
                if msg.encoding == 'rgb8':
                    arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            elif channels == 1:
                arr = arr.reshape((msg.height, msg.width))
                arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)

            self.image_received.emit(arr)
        except Exception:
            pass

    def odom_cb(self, msg: Odometry):
        px = msg.pose.pose.position.x
        py = msg.pose.pose.position.y
        qz = msg.pose.pose.orientation.z
        qw = msg.pose.pose.orientation.w
        yaw = 2.0 * math.atan2(qz, qw)
        vx = msg.twist.twist.linear.x
        wz = msg.twist.twist.angular.z

        # Express the pose in the map frame so the robot marker, goal and /plan share one frame
        try:
            tf = self.tf_buffer.lookup_transform("map", msg.header.frame_id or "odom", rclpy.time.Time()).transform
            tz, tw = tf.rotation.z, tf.rotation.w
            tyaw = 2.0 * math.atan2(tz, tw)
            c, sn = math.cos(tyaw), math.sin(tyaw)
            px, py = (tf.translation.x + c * px - sn * py,
                      tf.translation.y + sn * px + c * py)
            yaw += tyaw
        except Exception:
            return  # map->odom not available yet; don't draw the robot in the wrong frame

        self.robot_x = px
        self.robot_y = py
        self.robot_yaw = yaw

        if self.target_x is not None and self.target_y is not None:
            dist = math.hypot(self.target_x - px, self.target_y - py)
            self.distance_remaining = dist
            if dist < 0.35 and self.nav_status == "NAVIGATING":
                self.nav_status = "ARRIVED"
            self.nav_status_changed.emit(self.nav_status, self.distance_remaining)

        self.pose_received.emit(px, py, yaw, vx, wz)

    def plan_cb(self, msg: Path):
        pts = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]
        self.path_received.emit(pts)

    def scan_cb(self, msg: LaserScan):
        ranges = msg.ranges
        num = len(ranges)
        if num == 0:
            return
        mid = num // 2
        span = int(num * (30.0 / 360.0))
        fwd_ranges = [r for r in ranges[max(0, mid - span):min(num, mid + span)] if msg.range_min < r < msg.range_max]
        min_dist = min(fwd_ranges) if fwd_ranges else 10.0
        self.scan_received.emit(min_dist)

    def get_clearance_at(self, x, y):
        r, c = world_to_map(x, y)
        if 0 <= r < MAP_H and 0 <= c < MAP_W:
            return float(self.dist_to_obs[r, c])
        return 0.0

    def find_nearest_safe_goal(self, x, y, min_clearance=0.32):
        """Intelligent Safe Clearance Snapping to ensure robot never collides."""
        r, c = world_to_map(x, y)
        r = max(0, min(MAP_H - 1, r))
        c = max(0, min(MAP_W - 1, c))

        if self.dist_to_obs[r, c] >= min_clearance:
            return x, y, self.dist_to_obs[r, c]

        safe_indices = np.argwhere(self.dist_to_obs >= min_clearance)
        if len(safe_indices) == 0:
            return x, y, 0.0

        dists = (safe_indices[:, 0] - r) ** 2 + (safe_indices[:, 1] - c) ** 2
        nearest_idx = safe_indices[np.argmin(dists)]
        nr, nc = nearest_idx[0], nearest_idx[1]
        nx, ny = map_to_world(nr, nc)
        return nx, ny, self.dist_to_obs[nr, nc]

    def send_goal(self, x, y, yaw=None):
        """Dispatches Nav2 goal safely via /goal_pose topic with preemption protection."""
        nx, ny, clearance = self.find_nearest_safe_goal(x, y, min_clearance=0.45)
        self.target_x = float(nx)
        self.target_y = float(ny)

        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.node.get_clock().now().to_msg()
        pose.pose.position.x = float(nx)
        pose.pose.position.y = float(ny)
        pose.pose.position.z = 0.0

        if yaw is None:
            # Face toward destination from current position
            dx = nx - self.robot_x
            dy = ny - self.robot_y
            yaw = math.atan2(dy, dx) if (dx * dx + dy * dy) > 0.04 else self.robot_yaw

        yaw_rad = math.radians(yaw) if abs(yaw) > 6.28 else yaw
        pose.pose.orientation.z = math.sin(yaw_rad / 2.0)
        pose.pose.orientation.w = math.cos(yaw_rad / 2.0)

        # Cancel any active action handle first to prevent BehaviorTree crash
        if self.goal_handle is not None:
            try:
                self.goal_handle.cancel_goal_async()
            except Exception:
                pass
            self.goal_handle = None

        # Publish to /goal_pose (handled natively and gracefully by Nav2 bt_navigator)
        self.goal_pub.publish(pose)
        self.nav_status = "NAVIGATING"
        self.nav_status_changed.emit(self.nav_status, math.hypot(nx - self.robot_x, ny - self.robot_y))

        return nx, ny, clearance

    def action_feedback_cb(self, feedback_msg):
        pass

    def goal_response_cb(self, future):
        pass

    def goal_result_cb(self, future):
        pass

    def emergency_stop(self):
        """Immediately stops the robot and cancels goals."""
        self.target_x = None
        self.target_y = None
        if self.goal_handle:
            try:
                self.goal_handle.cancel_goal_async()
            except Exception:
                pass
            self.goal_handle = None
        stop_twist = Twist()
        for _ in range(5):
            self.cmd_vel_pub.publish(stop_twist)
            time.sleep(0.01)
        self.nav_status = "STOPPED"
        self.nav_status_changed.emit(self.nav_status, 0.0)


class RobotPovWidget(QWidget):
    """Renders Robot POV Camera stream with Head-Up Display (HUD)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(480, 360)
        self.current_frame = None
        self.vx = 0.0
        self.wz = 0.0
        self.min_dist = 10.0
        self.nav_status = "INITIALIZING"
        self.dist_remaining = 0.0
        self.radar_angle = 0.0

        # Radar sweep animation timer for standby
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.on_anim_tick)
        self.anim_timer.start(50)

    def on_anim_tick(self):
        if self.current_frame is None:
            self.radar_angle = (self.radar_angle + 6.0) % 360.0
            self.update()

    def update_frame(self, frame_bgr):
        self.current_frame = frame_bgr
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()

        if self.current_frame is not None:
            rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            ih, iw, _ = rgb.shape
            qimg = QImage(rgb.data, iw, ih, 3 * iw, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            scaled = pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            sx = (scaled.width() - w) // 2
            sy = (scaled.height() - h) // 2
            painter.drawPixmap(0, 0, scaled, sx, sy, w, h)
        else:
            # High-tech standby radar view
            painter.fillRect(0, 0, w, h, QColor(10, 16, 26))
            cx, cy = w // 2, h // 2
            painter.setPen(QPen(QColor(25, 45, 70), 1))
            for rad in [40, 80, 120, 160]:
                painter.drawEllipse(QPointF(cx, cy), rad, rad)
            painter.drawLine(cx - 180, cy, cx + 180, cy)
            painter.drawLine(cx, cy - 180, cx, cy + 180)

            # Sweeping beam
            rad_rad = math.radians(self.radar_angle)
            sweep_x = cx + 160 * math.cos(rad_rad)
            sweep_y = cy + 160 * math.sin(rad_rad)
            painter.setPen(QPen(QColor(0, 220, 255, 180), 2))
            painter.drawLine(cx, cy, int(sweep_x), int(sweep_y))

            painter.setPen(QColor(0, 220, 255))
            painter.setFont(QFont("Arial", 11, QFont.Bold))
            painter.drawText(0, cy - 30, w, 30, Qt.AlignCenter, "🎥 AgileX Scout Mini: Front Eye Active")
            painter.setFont(QFont("Monospace", 9))
            painter.setPen(QColor(160, 190, 220))
            painter.drawText(0, cy + 5, w, 25, Qt.AlignCenter, "Awaiting Camera Stream on /camera/image_raw...")

        # HUD Top Banner
        painter.fillRect(0, 0, w, 34, QColor(8, 14, 22, 210))
        painter.setPen(QColor(0, 230, 255))
        painter.setFont(QFont("Monospace", 9, QFont.Bold))
        painter.drawText(12, 22, "👁️ ROBOT POV (FRONT CAMERA) | 640x480 @ 30Hz")

        # Nav Status Pill
        pill_color = QColor(0, 180, 80) if "NAVIGATING" in self.nav_status or "READY" in self.nav_status else QColor(220, 140, 30)
        if any(x in self.nav_status for x in ["STOPPED", "FAILED", "REJECTED"]):
            pill_color = QColor(220, 50, 50)
        painter.fillRect(w - 190, 6, 180, 22, pill_color)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.drawText(w - 190, 6, 180, 22, Qt.AlignCenter, f"{self.nav_status}")

        # Central Crosshairs
        cx, cy = w // 2, h // 2
        painter.setPen(QPen(QColor(0, 255, 200, 160), 1, Qt.DashLine))
        painter.drawLine(cx - 35, cy, cx + 35, cy)
        painter.drawLine(cx, cy - 35, cx, cy + 35)
        painter.drawEllipse(QPointF(cx, cy), 16, 16)

        # HUD Bottom Banner: Speed & Obstacle Clearance
        painter.fillRect(0, h - 52, w, 52, QColor(8, 14, 22, 210))
        painter.setPen(QColor(220, 235, 250))
        painter.setFont(QFont("Monospace", 9))
        painter.drawText(15, h - 31, f"Speed: {self.vx:+.2f} m/s | Turn: {self.wz:+.2f} rad/s")

        clr_color = QColor(0, 255, 120)
        if self.min_dist < 0.8:
            clr_color = QColor(255, 60, 60)
        elif self.min_dist < 1.5:
            clr_color = QColor(255, 200, 40)

        painter.setPen(clr_color)
        painter.setFont(QFont("Monospace", 9, QFont.Bold))
        painter.drawText(15, h - 12, f"Front Clearance: {self.min_dist:.2f} m")

        if self.dist_remaining > 0.05:
            painter.setPen(QColor(0, 220, 255))
            painter.drawText(w - 200, h - 20, f"Remaining: {self.dist_remaining:.2f} m")


class CivilMapWidget(QWidget):
    """Renders interactive Civil Floor Environment Map using actual occupancy grid."""
    point_clicked = pyqtSignal(float, float)

    def __init__(self, ros_worker: RosWorker, parent=None):
        super().__init__(parent)
        self.ros_worker = ros_worker
        self.setMinimumSize(480, 360)

        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.trace_points = []
        self.path_points = []
        self.target_x = None
        self.target_y = None

        # Build high-contrast map pixmap from civil_map.pgm
        self.map_pixmap = self.generate_map_pixmap(ros_worker.map_arr)

    def generate_map_pixmap(self, map_arr):
        """Generates an architectural blueprint pixmap from the 2D occupancy grid."""
        h, w = map_arr.shape
        rgba = np.zeros((h, w, 4), dtype=np.uint8)

        # Free space (254) -> Blueprint Navy Floor
        free = (map_arr == 254)
        rgba[free] = [18, 32, 54, 255]

        # Obstacles (0) -> Crisp Solid Architectural White
        occ = (map_arr == 0)
        rgba[occ] = [230, 240, 255, 255]

        # Unknown / Outside building (205) -> Dark Deep Space
        unk = (map_arr != 0) & (map_arr != 254)
        rgba[unk] = [10, 16, 28, 255]

        qimg = QImage(rgba.data, w, h, 4 * w, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimg)

    def set_robot_pose(self, x, y, yaw):
        self.robot_x = x
        self.robot_y = y
        self.robot_yaw = yaw
        if not self.trace_points:
            self.trace_points.append((x, y))
        else:
            lx, ly = self.trace_points[-1]
            if (x - lx)**2 + (y - ly)**2 > 0.0025:  # Every 5 cm
                self.trace_points.append((x, y))
                if len(self.trace_points) > 5000:
                    self.trace_points.pop(0)
        self.update()

    def set_path(self, path):
        self.path_points = path
        self.update()

    def set_target(self, x, y):
        self.target_x = x
        self.target_y = y
        self.update()

    def map_to_widget(self, wx, wy):
        ww = self.width()
        wh = self.height()
        u = (wx - ORIGIN_X) / 22.0 * ww
        v = (1.0 - (wy - ORIGIN_Y) / 18.0) * wh
        return u, v

    def widget_to_map(self, px, py):
        ww = self.width()
        wh = self.height()
        wx = ORIGIN_X + (px / ww) * 22.0
        wy = ORIGIN_Y + (1.0 - (py / wh)) * 18.0
        return wx, wy

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            wx, wy = self.widget_to_map(event.x(), event.y())
            self.point_clicked.emit(wx, wy)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()

        # 1. Render actual architectural occupancy map
        painter.drawPixmap(0, 0, w, h, self.map_pixmap)

        # 2. Draw Subtle Coordinate Grid
        painter.setPen(QPen(QColor(35, 60, 95, 100), 1, Qt.DotLine))
        for x in range(-10, 11, 2):
            px, _ = self.map_to_widget(x, 0)
            painter.drawLine(int(px), 0, int(px), h)
        for y in range(-8, 9, 2):
            _, py = self.map_to_widget(0, y)
            painter.drawLine(0, int(py), w, int(py))

        # 3. Draw Zoned Room Overlays & Labels
        for room in ROOMS:
            rx0, ry1 = self.map_to_widget(room["xmin"], room["ymax"])
            rx1, ry0 = self.map_to_widget(room["xmax"], room["ymin"])
            painter.fillRect(int(rx0), int(ry1), int(rx1 - rx0), int(ry0 - ry1), room["color"])

            # Room label
            painter.setPen(QColor(190, 220, 255, 200))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.drawText(int(rx0 + 8), int(ry1 + 18), room["name"])

        # 4. Draw Stations Markers
        for st in STATIONS:
            spx, spy = self.map_to_widget(st["x"], st["y"])
            painter.setBrush(QBrush(QColor(0, 200, 255, 140)))
            painter.setPen(QPen(QColor(0, 240, 255), 1))
            painter.drawEllipse(QPointF(spx, spy), 5, 5)
            painter.setFont(QFont("Arial", 7, QFont.Bold))
            painter.setPen(QColor(230, 245, 255))
            painter.drawText(int(spx + 7), int(spy + 4), f"S{st['id']}")

        # 5. Draw Nav2 Planned Trajectory (/plan), trimmed so it starts at the robot
        if len(self.path_points) > 1:
            d2 = [(px - self.robot_x) ** 2 + (py - self.robot_y) ** 2 for px, py in self.path_points]
            ni = min(range(len(d2)), key=d2.__getitem__)
            if d2[ni] < 1.5 ** 2:
                pts = [(self.robot_x, self.robot_y)] + self.path_points[ni + 1:]
                painter.setPen(QPen(QColor(0, 255, 140, 230), 2, Qt.SolidLine))
                for i in range(len(pts) - 1):
                    p0x, p0y = self.map_to_widget(*pts[i])
                    p1x, p1y = self.map_to_widget(*pts[i + 1])
                    painter.drawLine(int(p0x), int(p0y), int(p1x), int(p1y))

        # 6. Draw Active Target Waypoint
        if self.target_x is not None:
            tpx, tpy = self.map_to_widget(self.target_x, self.target_y)
            painter.setBrush(QBrush(QColor(255, 60, 60, 80)))
            painter.setPen(QPen(QColor(255, 70, 70), 2))
            painter.drawEllipse(QPointF(tpx, tpy), 14, 14)
            painter.drawEllipse(QPointF(tpx, tpy), 4, 4)
            painter.drawLine(int(tpx - 18), int(tpy), int(tpx + 18), int(tpy))
            painter.drawLine(int(tpx), int(tpy - 18), int(tpx), int(tpy + 18))


        # Minimal Position & Heading Pointer (Replaces bulky bot model)
        rpx, rpy = self.map_to_widget(self.robot_x, self.robot_y)
        painter.setBrush(QBrush(QColor(0, 255, 200, 220)))
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.drawEllipse(QPointF(rpx, rpy), 4.5, 4.5)
        hx = rpx + 12 * math.cos(self.robot_yaw)
        hy = rpy - 12 * math.sin(self.robot_yaw)
        painter.setPen(QPen(QColor(0, 255, 200), 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(int(rpx), int(rpy), int(hx), int(hy))

        # Top Header
        painter.fillRect(0, 0, w, 30, QColor(8, 14, 22, 210))
        painter.setPen(QColor(210, 235, 255))
        painter.setFont(QFont("Monospace", 9, QFont.Bold))
        painter.drawText(12, 20, "🗺️ CIVIL ARCHITECTURAL MAP [CLICK-TO-NAVIGATE]")


class CivilGroundStation(QMainWindow):
    """Main Application Window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AgileX Scout Mini 4WD AMR — Civil Floor Architectural Ground Station")
        self.resize(1400, 850)

        # ROS 2 Worker
        self.ros_worker = RosWorker()

        # Build UI
        self.init_ui()

        # Connections
        self.ros_worker.image_received.connect(self.pov_widget.update_frame)
        self.ros_worker.pose_received.connect(self.on_pose_received)
        self.ros_worker.path_received.connect(self.map_widget.set_path)
        self.ros_worker.scan_received.connect(self.on_scan_received)
        self.ros_worker.nav_status_changed.connect(self.on_nav_status_changed)
        self.ros_worker.nav_ready_signal.connect(self.on_nav_ready)

        self.map_widget.point_clicked.connect(self.on_map_point_clicked)

        # Start ROS 2
        self.ros_worker.start()

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0B111A; color: #E0E8F0; }
            QLabel { color: #D0DCF0; font-family: 'Segoe UI', Arial; }
            QGroupBox {
                border: 1px solid #24354D; border-radius: 6px;
                margin-top: 10px; font-weight: bold; color: #60A5FA;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton {
                background-color: #16243A; color: #E0EEFF; border: 1px solid #2B456C;
                border-radius: 4px; padding: 6px 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #203657; border-color: #00B0FF; }
            QPushButton:pressed { background-color: #0E1B2E; }
            QCheckBox { color: #C0D0E5; font-weight: bold; }
            QCheckBox::indicator { width: 16px; height: 16px; }
            QStatusBar { background-color: #070B12; color: #A0B5D0; font-family: 'Monospace'; }
        """)

        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(8)

        # 1. Header Bar
        header = QFrame()
        header.setStyleSheet("background-color: #101B2B; border: 1px solid #1E3048; border-radius: 6px; padding: 4px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 4, 10, 4)

        title = QLabel("🏛️ AGILEX SCOUT MINI 4WD AMR — CIVIL ARCHITECTURAL TELEMETRY & POINT-TO-NAVIGATE")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet("color: #00E0FF;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        specs_btn = QPushButton("📋 Datasheet Specs")
        specs_btn.clicked.connect(self.show_datasheet_dialog)
        h_layout.addWidget(specs_btn)
        main_layout.addWidget(header)

        # 2. Dual Viewports (Left: POV, Right: Map)
        viewports_layout = QHBoxLayout()
        viewports_layout.setSpacing(10)

        self.pov_widget = RobotPovWidget()
        pov_group = QGroupBox("Robot First-Person POV (Front Camera)")
        pov_layout = QVBoxLayout(pov_group)
        pov_layout.setContentsMargins(6, 14, 6, 6)
        pov_layout.addWidget(self.pov_widget)
        viewports_layout.addWidget(pov_group, stretch=5)

        self.map_widget = CivilMapWidget(self.ros_worker)
        map_group = QGroupBox("Civil Floor Environment Map (Click-to-Navigate)")
        map_layout = QVBoxLayout(map_group)
        map_layout.setContentsMargins(6, 14, 6, 6)
        map_layout.addWidget(self.map_widget)
        viewports_layout.addWidget(map_group, stretch=6)

        main_layout.addLayout(viewports_layout, stretch=1)

        # 3. Controls & Station Buttons
        controls_group = QGroupBox("Autonomous Navigation Controls & Civil Department Stations")
        ctrl_layout = QVBoxLayout(controls_group)
        ctrl_layout.setContentsMargins(8, 12, 8, 8)
        ctrl_layout.setSpacing(6)

        stations_layout = QHBoxLayout()
        stations_layout.setSpacing(6)
        for st in STATIONS:
            btn = QPushButton(f"S{st['id']}: {st['name'].split(':')[1].strip()}")
            btn.clicked.connect(lambda checked, s=st: self.on_station_clicked(s))
            stations_layout.addWidget(btn)
        ctrl_layout.addLayout(stations_layout)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        actions_layout.addStretch()

        patrol_btn = QPushButton("🚀 Run Full Autonomous Patrol Loop")
        patrol_btn.setStyleSheet("background-color: #163624; color: #4ADE80; border-color: #276742;")
        patrol_btn.clicked.connect(self.run_patrol_loop)
        actions_layout.addWidget(patrol_btn)

        stop_btn = QPushButton("🛑 EMERGENCY STOP")
        stop_btn.setStyleSheet("background-color: #421616; color: #F87171; border-color: #7A2828;")
        stop_btn.clicked.connect(self.on_emergency_stop)
        actions_layout.addWidget(stop_btn)

        ctrl_layout.addLayout(actions_layout)
        main_layout.addWidget(controls_group)

        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Initializing simulation & Nav2 stack... Please wait.")

    def on_pose_received(self, x, y, yaw, vx, wz):
        self.map_widget.set_robot_pose(x, y, yaw)
        self.pov_widget.vx = vx
        self.pov_widget.wz = wz
        self.pov_widget.update()

    def on_scan_received(self, min_dist):
        self.pov_widget.min_dist = min_dist
        self.pov_widget.update()

    def on_nav_status_changed(self, status, dist_remaining):
        self.pov_widget.nav_status = status
        self.pov_widget.dist_remaining = dist_remaining
        if status != "NAVIGATING":
            self.map_widget.set_path([])
        self.pov_widget.update()

    def on_nav_ready(self, ready):
        if ready:
            self.status_bar.showMessage("✅ Nav2 Stack & AMCL Ready! Click anywhere on the map to navigate.", 6000)

    def on_map_point_clicked(self, x, y):
        self.map_widget.set_path([])
        nx, ny, clr = self.ros_worker.send_goal(x, y)
        self.map_widget.set_target(nx, ny)
        room = get_room_name(nx, ny)
        self.status_bar.showMessage(
            f"🚀 [GOAL DISPATCHED] Navigating to: ({nx:.2f}, {ny:.2f}) in {room} (Safety Clearance: {clr:.2f}m)", 5000
        )

    def on_station_clicked(self, station):
        nx, ny, clr = self.ros_worker.send_goal(station["x"], station["y"], yaw=station["yaw"])
        self.map_widget.set_target(nx, ny)
        self.status_bar.showMessage(f"🚀 [STATION GOAL] Dispatched to {station['name']} at ({nx:.2f}, {ny:.2f})", 5000)

    def run_patrol_loop(self):
        self.status_bar.showMessage("🚀 [PATROL] Initiating autonomous patrol loop at Station 1...", 4000)
        self.on_station_clicked(STATIONS[0])

    def on_emergency_stop(self):
        self.ros_worker.emergency_stop()
        self.map_widget.set_target(None, None)
        self.status_bar.showMessage("🛑 [EMERGENCY STOP] All drive commands halted and Nav2 goals cancelled.", 5000)

    def show_datasheet_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("AgileX Scout Mini 4WD AMR — Technical Datasheet Specifications")
        msg.setStyleSheet("background-color: #101B2B; color: #D0DCF0;")
        text = """<h3>AgileX Scout Mini 4WD Autonomous Mobile Robot (AMR)</h3>
<p><b>Mechanical & Drive Train Specifications:</b></p>
<ul>
  <li><b>Drive Mode:</b> 4-Wheel In-Wheel Brushless DC Hub Motors (Skid-Steer / Diff-Drive)</li>
  <li><b>Dimensions (L x W x H):</b> 612 mm × 580 mm × 245 mm</li>
  <li><b>Wheelbase:</b> 390 mm (0.390 m)</li>
  <li><b>Track Width (Wheel Separation):</b> 612 mm (0.612 m)</li>
  <li><b>Wheel Diameter:</b> 160 mm (Radius: 80 mm)</li>
  <li><b>Chassis Mass:</b> 22.0 kg | Wheel Mass: 1.5 kg × 4 | <b>Total: 28.0 kg</b></li>
  <li><b>Ground Clearance:</b> 107 mm | <b>Max Climbing Angle:</b> 30°</li>
  <li><b>Turning Radius:</b> 0.0 m (In-situ 360° Zero-Radius Skid-Steer Rotation)</li>
</ul>
<p><b>Kinematic & Navigation Limits (Configured in Nav2):</b></p>
<ul>
  <li><b>Max Linear Velocity (v_max):</b> 2.0 m/s rated (Corridor tuned: 0.80 m/s)</li>
  <li><b>Max Angular Velocity (w_max):</b> 3.0 rad/s rated (Corridor tuned: 2.00 rad/s)</li>
  <li><b>Max Linear Acceleration (a_max):</b> 2.5 m/s²</li>
  <li><b>Max Angular Acceleration:</b> 3.5 rad/s²</li>
  <li><b>Footprint Bounding Box:</b> [[0.35, 0.30], [0.35, -0.30], [-0.35, -0.30], [-0.35, 0.30]]</li>
  <li><b>Doorway Navigation Clearance:</b> Costmap inflation (0.50m - 0.52m) optimized for standard 1.2m doors</li>
</ul>"""
        msg.setText(text)
        msg.exec_()

    def closeEvent(self, event):
        self.ros_worker.running = False
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CivilGroundStation()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
