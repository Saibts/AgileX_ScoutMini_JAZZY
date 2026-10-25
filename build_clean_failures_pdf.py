#!/usr/bin/env python3
"""
build_clean_failures_pdf.py
Generates the revised Academic Engineering Troubleshooting & Failures Report PDF
WITHOUT any images or screenshots. Strictly text-based failures, root cause analyses,
symptoms, and permanent engineering solutions.
"""

import sys
import html
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

WORKSPACE = Path("/home/sailakshmi/agilex")
OUTPUT_PDF = WORKSPACE / "PROJECT_FAILURES_AND_SOLUTIONS.pdf"

# Palette
PRIMARY = colors.HexColor("#7F1D1D")     # Crimson / Deep Burgundy
SECONDARY = colors.HexColor("#0369A1")   # Deep Tech Blue
ACCENT = colors.HexColor("#9A3412")      # Burnt Amber
DARK_TEXT = colors.HexColor("#0F172A")   # Slate 900
MUTED_TEXT = colors.HexColor("#475569")  # Slate 600
LIGHT_BG = colors.HexColor("#F8FAFC")    # Slate 50
BORDER_COLOR = colors.HexColor("#CBD5E1")# Slate 300
ERROR_BG = colors.HexColor("#FEF2F2")    # Light Red
ERROR_BORDER = colors.HexColor("#F87171")
ERROR_TEXT = colors.HexColor("#991B1B")
FIX_BG = colors.HexColor("#F0FDF4")      # Light Green
FIX_BORDER = colors.HexColor("#4ADE80")
FIX_TEXT = colors.HexColor("#166534")
CARD_HEADER_BG = colors.HexColor("#1E293B") # Dark Slate


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        w, h = self._pagesize

        # Running header (pages 2+)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(PRIMARY)
            self.drawString(40, h - 30, "AgileX Scout Mini AMR — Engineering Troubleshooting & Failure Analysis")
            self.setFont("Helvetica", 8)
            self.setFillColor(MUTED_TEXT)
            self.drawRightString(w - 40, h - 30, "ROS 2 Jazzy | Gazebo Harmonic")
            
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.6)
            self.line(40, h - 34, w - 40, h - 34)

        # Running footer (all pages)
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.6)
        self.line(40, 36, w - 40, 36)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(MUTED_TEXT)
        self.drawString(40, 24, "Candidate: Sailakshmi B.T. (Reg No: 2024511019) | Dept. of Production Technology, MIT Campus, Anna University")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(w - 40, 24, page_str)

        # Outer decorative frame
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.rect(25, 18, w - 50, h - 36)

        self.restoreState()


def get_styles():
    base = getSampleStyleSheet()
    styles = {
        'DocTitle': ParagraphStyle(
            'DocTitle', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=18, leading=22,
            textColor=PRIMARY, alignment=1, spaceAfter=6
        ),
        'DocSubtitle': ParagraphStyle(
            'DocSubtitle', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=10.5, leading=14,
            textColor=DARK_TEXT, alignment=1, spaceAfter=10
        ),
        'SectionHeading': ParagraphStyle(
            'SectionHeading', parent=base['Heading1'],
            fontName='Helvetica-Bold', fontSize=12, leading=15,
            textColor=PRIMARY, spaceBefore=8, spaceAfter=4, keepWithNext=True
        ),
        'Body': ParagraphStyle(
            'Body', parent=base['BodyText'],
            fontName='Helvetica', fontSize=8.2, leading=11.2,
            textColor=DARK_TEXT, spaceAfter=3
        ),
        'BodyBold': ParagraphStyle(
            'BodyBold', parent=base['BodyText'],
            fontName='Helvetica-Bold', fontSize=8.2, leading=11.2,
            textColor=DARK_TEXT, spaceAfter=2
        ),
        'MetaKey': ParagraphStyle(
            'MetaKey', fontName='Helvetica-Bold', fontSize=8, leading=10.5, textColor=DARK_TEXT
        ),
        'MetaVal': ParagraphStyle(
            'MetaVal', fontName='Helvetica', fontSize=8, leading=10.5, textColor=DARK_TEXT
        ),
        'TableHead': ParagraphStyle(
            'TableHead', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.white, alignment=0
        ),
        'TableCell': ParagraphStyle(
            'TableCell', fontName='Helvetica', fontSize=7.2, leading=9.2, textColor=DARK_TEXT
        ),
        'TableCellBold': ParagraphStyle(
            'TableCellBold', fontName='Helvetica-Bold', fontSize=7.2, leading=9.2, textColor=DARK_TEXT
        ),
        # Card styles for failures
        'CardHeaderTitle': ParagraphStyle(
            'CardHeaderTitle', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.white
        ),
        'CardLabelError': ParagraphStyle(
            'CardLabelError', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=ERROR_TEXT
        ),
        'CardTextError': ParagraphStyle(
            'CardTextError', fontName='Courier-Bold', fontSize=7.0, leading=9.0, textColor=ERROR_TEXT
        ),
        'CardLabelReason': ParagraphStyle(
            'CardLabelReason', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=PRIMARY
        ),
        'CardTextReason': ParagraphStyle(
            'CardTextReason', fontName='Helvetica', fontSize=8.0, leading=10.8, textColor=DARK_TEXT
        ),
        'CardLabelFix': ParagraphStyle(
            'CardLabelFix', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=FIX_TEXT
        ),
        'CardTextFix': ParagraphStyle(
            'CardTextFix', fontName='Helvetica', fontSize=8.0, leading=10.8, textColor=FIX_TEXT
        ),
    }
    return styles


def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=38,
        rightMargin=38,
        topMargin=42,
        bottomMargin=42
    )
    w_page, h_page = A4
    printable_w = w_page - (38 + 38)

    styles = get_styles()
    story = []

    # Title Block
    story.append(Spacer(1, 6))
    story.append(Paragraph("ANNA UNIVERSITY — MIT CAMPUS, CHENNAI", ParagraphStyle('Inst', fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=MUTED_TEXT, alignment=1)))
    story.append(Paragraph("DEPARTMENT OF PRODUCTION TECHNOLOGY", ParagraphStyle('Dept', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=SECONDARY, alignment=1, spaceAfter=8)))
    story.append(Paragraph("AGILEX SCOUT MINI AMR SIMULATION", styles['DocTitle']))
    story.append(Paragraph("Engineering Troubleshooting, Failure Analysis & Root Cause Case Study<br/><b>Technical Log of All 22 System Anomalies, Error Signatures, Root Causes & Engineering Solutions</b>", styles['DocSubtitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=4, spaceAfter=8))

    # Metadata Table
    meta = [
        [Paragraph("<b>Course & Subject:</b>", styles['MetaKey']), Paragraph("M.E. Mechatronics / RA23E01: Robot Operating System (ROS)", styles['MetaVal']),
         Paragraph("<b>Candidate Name:</b>", styles['MetaKey']), Paragraph("Sailakshmi B.T. (Reg No: 2024511019)", styles['MetaVal'])],
        [Paragraph("<b>Target Robot Platform:</b>", styles['MetaKey']), Paragraph("AgileX Scout Mini 4-Wheel Skid-Steer AMR", styles['MetaVal']),
         Paragraph("<b>Software Ecosystem:</b>", styles['MetaKey']), Paragraph("Ubuntu 24.04 LTS | ROS 2 Jazzy | Gazebo Harmonic", styles['MetaVal'])],
        [Paragraph("<b>Document Scope:</b>", styles['MetaKey']), Paragraph("Rigorous failure logs, root cause diagnostics, and engineering fixes across CAD, physics, DDS, EKF, and Nav2.", styles['MetaVal']),
         Paragraph("<b>Format Specification:</b>", styles['MetaKey']), Paragraph("Exhaustive Text-Based Troubleshooting Log (Zero Screenshots)", styles['MetaVal'])],
    ]
    col_w = [printable_w * 0.18, printable_w * 0.32, printable_w * 0.18, printable_w * 0.32]
    t_meta = Table(meta, colWidths=col_w)
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 8))

    # Executive Overview
    overview_text = (
        "<b>Executive Engineering Summary:</b> In advanced mobile robotics, transitioning a mechanical SolidWorks CAD "
        "assembly into a fully validated autonomous simulation within ROS 2 Jazzy Jalisco and Gazebo Harmonic (`gz-sim8`) "
        "presents complex multi-domain challenges. The AgileX Scout Mini project encountered <b>22 distinct system failures</b> "
        "spanning Linux operating system standards, SolidWorks kinematic joint exports, ODE contact physics micro-collisions, "
        "network multicast routing, sensor frame transformations, Extended Kalman Filter fusion, and ROS 2 Jazzy Nav2 lifecycle "
        "management. This document provides an exhaustive, text-based engineering post-mortem: every failure is paired with its exact "
        "error traceback, in-depth root cause analysis explaining the underlying theoretical mechanism, and the permanent applied solution."
    )
    story.append(Paragraph(overview_text, styles['Body']))
    story.append(Spacer(1, 6))

    # Master Failure Index Table
    story.append(Paragraph("Summary Matrix of All 22 System Anomalies & Engineering Root Causes", styles['SectionHeading']))
    
    matrix_data = [
        [Paragraph("<b>#</b>", styles['TableHead']),
         Paragraph("<b>Domain</b>", styles['TableHead']),
         Paragraph("<b>Failure Phenomenon</b>", styles['TableHead']),
         Paragraph("<b>Primary Root Cause / Failure Reason</b>", styles['TableHead'])],
    ]

    domain_map = {
        1: "ROS 2 Build", 2: "OS / File", 3: "URDF / Mesh", 4: "Kinematics", 5: "Visualization",
        6: "Network / DDS", 7: "ODE Physics", 8: "Architecture", 9: "Kinematics", 10: "KDL Kinematics",
        11: "Simulation", 12: "Build System", 13: "Coordinate REP", 14: "Physics Dynamics", 15: "Sensors",
        16: "Localization", 17: "Time / Clock", 18: "ROS Lifecycle", 19: "TF Buffer", 20: "Localization",
        21: "Nav2 Stack", 22: "Mission Control"
    }

    raw_failures = [
        {
            "id": 1,
            "title": "ROS 2 Package Naming Convention Failure (ValueError)",
            "domain": "ROS 2 Build",
            "symptom": "ValueError: 'assem2.robot' is not a valid package name. InvalidFrontendLaunchFileError.",
            "cause": "The initial directory and package inherited the SolidWorks assembly notation 'assem2.robot'. In ROS 2, ament and Python packaging rules strictly enforce that package names must contain only lowercase alphanumeric characters and underscores. Periods ('.') and hyphens ('-') are illegal characters that cause parsing errors in ament_python and colcon.",
            "fix": "Standardized the package name across package.xml, CMakeLists.txt, launch scripts, and URDF references to 'assem2_robot'."
        },
        {
            "id": 2,
            "title": "Linux Ext4 Case-Sensitivity & File Resolution (FileNotFoundError)",
            "domain": "OS / File",
            "symptom": "FileNotFoundError: [Errno 2] No such file or directory: '.../urdf/assem2.SLDASM.urdf'",
            "cause": "Windows and SolidWorks are case-insensitive, but Linux Ext4 file systems are strictly case-sensitive. SolidWorks exported the file with a capitalized 'A' (Assem2.SLDASM.urdf), while the ROS 2 launch script referenced lowercase 'assem2.SLDASM.urdf'. Additionally, CMakeLists.txt lacked an install(DIRECTORY urdf ...) macro, omitting the files from install/.",
            "fix": "Synchronized launch file paths to exact casing 'Assem2.SLDASM.urdf' and added 'install(DIRECTORY urdf DESTINATION share/${PROJECT_NAME})' in CMakeLists.txt."
        },
        {
            "id": 3,
            "title": "Broken Mesh URI Resolution & Invisible Robot in RViz",
            "domain": "URDF / Mesh",
            "symptom": "Could not load resource [package://Assem2.SLDASM/meshes/base_link.STL]. Robot links were completely invisible in RViz2 and Gazebo.",
            "cause": "The SolidWorks URDF exporter hardcoded the export assembly workspace directory name ('Assem2.SLDASM') into all <mesh filename=\"package://...\"> tags. When the package was standardized to 'assem2_robot', all mesh file lookups failed because the package name in the URI did not exist in the ROS environment.",
            "fix": "Executed a global regex substitution across Assem2.SLDASM.urdf replacing 'package://Assem2.SLDASM/' with 'package://assem2_robot/', restoring 100% mesh visual rendering."
        },
        {
            "id": 4,
            "title": "SolidWorks Fixed Wheel Joints & Missing TF Transforms",
            "domain": "Kinematics",
            "symptom": "RViz warning: 'No transform from [w1] to [base_link]'. Robot wheels appeared frozen or detached from the chassis body.",
            "cause": "The SolidWorks URDF exporter defaulted unconstrained or mated rotational components to type='fixed' joints instead of type='continuous'. Since fixed joints have 0 degrees of freedom, joint_state_publisher ignores them and never broadcasts dynamic wheel TF transforms across /tf.",
            "fix": "Modified URDF joints j1, j2, j3, and j4 to type='continuous' with explicit rotation axis <axis xyz='1 0 0'/>, allowing joint_state_publisher to compute and broadcast active wheel transforms."
        },
        {
            "id": 5,
            "title": "Empty RViz Fixed Frame Dropdown & Blank Display",
            "domain": "Visualization",
            "symptom": "Opening RViz showed a blank black viewport. The Fixed Frame dropdown was completely empty, and manually typing base_link reported 'Frame does not exist'.",
            "cause": "RViz launched with a blank default layout lacking the RobotModel display plugin. Furthermore, by default RViz RobotModel searches for a local URDF file on disk instead of subscribing to the live ROS 2 /robot_description topic broadcast by robot_state_publisher.",
            "fix": "Authored a pre-configured display.rviz configuration file with Fixed Frame set to odom/map, RobotModel subscribed to /robot_description, and integrated LaserScan, PointCloud2, and TF visualizers."
        },
        {
            "id": 6,
            "title": "DDS Network Multicast Failures & Missing Odometry Packets",
            "domain": "Network / DDS",
            "symptom": "Console spam: 'Exception sending a multicast message: Network is unreachable'. Odometry updates dropped intermittently and nodes failed discovery.",
            "cause": "The default FastDDS discovery mechanism attempted to broadcast peer discovery multicast packets across external network interfaces (such as unconfigured Wi-Fi or cellular adapters). When operating offline or on restricted university subnets, multicast packets were dropped.",
            "fix": "Set ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST and exported ROS_LOCALHOST_ONLY=1, restricting all DDS participant discovery and RTPS transport exclusively to the local loopback interface (127.0.0.1)."
        },
        {
            "id": 7,
            "title": "Wheel 3 (j3) Infinite Spinning Physics Bug at Rest",
            "domain": "ODE Physics",
            "symptom": "When robot spawned at rest (cmd_vel = 0), wheels 1, 2, and 4 stayed motionless, but Wheel 3 (j3 / w3) spun continuously at maximum velocity, violently oscillating the chassis.",
            "cause": "Three compounding root causes: 1) The SolidWorks export omitted the <axis> tag inside joint j3; 2) Zero joint damping and zero friction existed in the URDF; 3) The initial DiffDrive plugin only controlled joints j1 and j2, leaving j3 completely unpowered and unbraked. ODE micro-collisions with the ground accelerated the frictionless, unconstrained joint into an infinite energy amplification loop.",
            "fix": "Added <axis xyz='-1 0 0'/>, injected <dynamics damping='0.1' friction='0.1'/>, and grouped all 4 wheels into the Gazebo DiffDrive plugin (<left_joint>j2</left_joint><left_joint>j4</left_joint><right_joint>j1</right_joint><right_joint>j3</right_joint>) so active braking torque is applied at zero velocity."
        },
        {
            "id": 8,
            "title": "ROS 2 Humble to Jazzy / Gazebo Classic to Harmonic Shift",
            "domain": "Architecture",
            "symptom": "gazebo_ros plugins failed to compile and launch. Terminal error: 'gazebo: command not found'.",
            "cause": "Ubuntu 24.04 (Noble) and ROS 2 Jazzy completely retired Gazebo Classic (gazebo11). The simulation engine shifted to Gazebo Harmonic (gz-sim8), requiring the new ros_gz_bridge architecture rather than legacy libgazebo_ros_diff_drive.so C++ libraries.",
            "fix": "Replaced legacy C++ .so plugins with native Gazebo Harmonic systems: gz::sim::systems::DiffDrive, gz::sim::systems::Sensors (gpu_lidar), and configured ros_gz_bridge parameter_bridge for topic translation."
        },
        {
            "id": 9,
            "title": "Robot Sunken 23 cm Below RViz Ground Grid",
            "domain": "Kinematics",
            "symptom": "In RViz, the robot appeared half-buried beneath the grid floor (Z < 0), with the ground plane slicing through the middle of the chassis body.",
            "cause": "SolidWorks placed the coordinate origin at the top cover plate of the chassis. Wheel axle height was located at Z = -0.1469m, and tire radius was 0.08m, placing ground contact at Z = -0.2269m. With zero coordinate offset, the top cover sat on the floor plane.",
            "fix": "Introduced root link 'base_footprint' with fixed joint offset xyz='-0.10185 0.16662 0.2269', lifting the chassis so all 4 tires sit flush on the ground at Z = 0.00m."
        },
        {
            "id": 10,
            "title": "KDL Parser Warning on Root Link Mass and Inertia",
            "domain": "KDL Kinematics",
            "symptom": "Warning: 'The root link base_link has an inertia specified in the URDF, but KDL does not support a root link with an inertia.'",
            "cause": "The Kinematics and Dynamics Library (KDL) tree algorithm utilized by robot_state_publisher mathematically requires the root link of a kinematic chain to be massless and inertialess. SolidWorks exported base_link as the root while attaching the entire 18 kg chassis mass to it.",
            "fix": "Established 'base_footprint' (a dummy link with 0 mass and no <inertial> tag) as the kinematic root, attaching base_link as its child via a fixed transform."
        },
        {
            "id": 11,
            "title": "Gazebo Duplicate Spawning ('Two Bots' Collision Bug)",
            "domain": "Simulation",
            "symptom": "Launching simulation showed two colliding robot models superimposed on top of each other (assem2_robot and assem2_robot_0), causing explosive physics contacts.",
            "cause": "The ros_gz_sim create node defaults to allow_renaming: true. If a previous simulation run was interrupted or crashed without killing background gz processes, the new launch spawned a duplicate instance and renamed it.",
            "fix": "Added '-allow_renaming false' to the create node arguments, explicit spawning coordinates (Z=0.02m), and configured cleanup scripts (pkill -9 -f 'ros_gz|gz sim') to terminate stale instances."
        },
        {
            "id": 12,
            "title": "Disk Storage Footprint Management on Limited Partition",
            "domain": "Build System",
            "symptom": "System warnings: primary Linux partition rapidly running low on free disk space (< 30 GB available).",
            "cause": "Standard colcon build copies entire binary trees and STL meshes into both build/ and install/ directories, duplicating large assets. Additionally, Gazebo simulation logs and core dumps accumulated gigabytes of unmonitored data.",
            "fix": "Used 'colcon build --symlink-install' to create symbolic links instead of duplicating files, cleaned Gazebo log caches, and enforced a strict .gitignore, compressing the repository footprint to ~3.3 MB."
        },
        {
            "id": 13,
            "title": "Teleoperation Heading Mismatch (+Y CAD Heading vs +X ROS Heading)",
            "domain": "Coordinate REP",
            "symptom": "Sending linear velocity (+X) made the robot drive sideways; turning commands rotated about an unexpected lateral axis.",
            "cause": "In SolidWorks, the CAD designer aligned the front bumper with the +Y axis. ROS standard REP-103 strictly requires +X as forward, +Y as left, and +Z as upward.",
            "fix": "Applied a +90° (+1.5708 rad) yaw rotation in base_footprint_joint: origin rpy='0 0 1.5707963', aligning the CAD bumper perfectly with the ROS forward direction."
        },
        {
            "id": 14,
            "title": "Wheel Rotation Axis Inversion & Direction Discrepancy",
            "domain": "Physics Dynamics",
            "symptom": "In Gazebo physics, commanding positive linear velocity (+X) caused the robot to roll backward, while RViz showed forward odometry.",
            "cause": "The CAD export assigned right-hand rule axes to wheel continuous joints that opposed the physical forward rotation direction of the wheels.",
            "fix": "Calibrated wheel joint axes: set <axis xyz='1 0 0'/> for left wheels (j1, j2) and <axis xyz='-1 0 0'/> for right wheels (j3, j4), synchronizing physics with kinematics."
        },
        {
            "id": 15,
            "title": "RGB-D Camera Inversion (Mounted on Rear Instead of Front)",
            "domain": "Sensors",
            "symptom": "RViz camera feed showed the arena behind the robot rather than the forward path.",
            "cause": "Due to the CAD origin orientation, the physical front bumper was located at negative Y in CAD coordinates (Y = -0.355m). An initial positive offset mounted the sensor on the rear bumper.",
            "fix": "Mounted camera_mount_joint at xyz='-0.16662 -0.355 0.065' with rpy='0 0 -1.5708', placing the camera squarely on the physical front bumper facing forward."
        },
        {
            "id": 16,
            "title": "Severe Skid-Steer Rotational Odometry Drift",
            "domain": "Localization",
            "symptom": "After executing a 360° turn, raw wheel odometry reported only 240° of rotation (a 120° heading error). In RViz, laser scans smeared and distorted.",
            "cause": "Skid-steering relies on physical tire slipping and scrubbing against the ground. In-hub wheel encoders only measure wheel rotations, completely missing lateral scrubbing and kinematic track width expansion.",
            "fix": "Implemented an Extended Kalman Filter (robot_localization ekf_node) fusing raw wheel odometry (/odom) with the 100Hz rate gyroscope from the 6-axis IMU (/imu), yielding drift-free heading on /odometry/filtered."
        },
        {
            "id": 17,
            "title": "Dual /clock Publisher Timestamp Oscillations & TF Jitter",
            "domain": "Time / Clock",
            "symptom": "RViz displays flickered rapidly. TF buffer reported timestamps jumping backward in time and transform lookups failed.",
            "cause": "Both ros_gz_sim (gz_sim.launch.py) and the parameter_bridge were publishing to the /clock topic with slight microsecond phase offsets, creating competing simulation clocks.",
            "fix": "Removed the duplicate clock bridge from parameter_bridge arguments, leaving gz_sim as the single authoritative source of simulation time."
        },
        {
            "id": 18,
            "title": "SLAM Toolbox Lifecycle State Unconfigured Error",
            "domain": "ROS Lifecycle",
            "symptom": "SLAM node spawned but failed to publish /map or /tf. Node reported an unconfigured lifecycle state.",
            "cause": "In ROS 2 Jazzy, SLAM Toolbox is implemented as a Managed Lifecycle Node. Starting the raw node binary leaves it in the 'Unconfigured' state without transitioning to 'Active'.",
            "fix": "Included the official 'online_async_launch.py' with 'autostart: true', which uses nav2_lifecycle_manager to automatically transition SLAM to the 'Active' state."
        },
        {
            "id": 19,
            "title": "RViz 'Frame [odom] does not exist' on Base Simulation Launch",
            "domain": "TF Buffer",
            "symptom": "RViz showed red TF transform errors on startup whenever SLAM or Nav2 were not enabled.",
            "cause": "RViz default Fixed Frame was set to 'map', which only exists when SLAM or AMCL are active.",
            "fix": "Configured default Fixed Frame to 'odom' in display.rviz, and ensured the EKF node automatically publishes the odom -> base_footprint transform."
        },
        {
            "id": 20,
            "title": "AMCL Initial Pose Frame Mismatch",
            "domain": "Localization",
            "symptom": "AMCL failed to initialize particles; laser scans did not align with pre-mapped walls.",
            "cause": "The initial pose was published in the 'odom' frame instead of the global 'map' frame.",
            "fix": "Set global_frame_id: 'map', odom_frame_id: 'odom', and configured set_initial_pose: true with initial coordinates (x=0, y=0, yaw=0) in nav2_params.yaml."
        },
        {
            "id": 21,
            "title": "ROS 2 Jazzy Nav2 Behavior Tree Navigator Architecture Shift",
            "domain": "Nav2 Stack",
            "symptom": "bt_navigator threw schema errors on startup: 'navigators parameter must be a list of plugins'.",
            "cause": "ROS 2 Jazzy refactored Nav2's bt_navigator parameters: the older single-navigator configuration was replaced with a modular plugin dictionary structure.",
            "fix": "Updated nav2_params.yaml to the official Jazzy format: navigators: ['navigate_to_pose', 'navigate_through_poses'] with their respective plugin definitions."
        },
        {
            "id": 22,
            "title": "Autonomous Patrol Mission Feedback & Telemetry Supervision",
            "domain": "Mission Control",
            "symptom": "Early patrol scripts hung indefinitely if navigation goal failed to compute a path around blocked stations.",
            "cause": "BasicNavigator required explicit polling of isTaskComplete() and handling of TaskResult.FAILED to transition safely to subsequent waypoints.",
            "fix": "Implemented feedback polling loop at 2Hz reading distance_remaining, with automatic recovery fallback on TaskResult.FAILED."
        }
    ]

    for f in raw_failures:
        matrix_data.append([
            Paragraph(f"<b>#{f['id']}</b>", styles['TableCellBold']),
            Paragraph(f['domain'], styles['TableCell']),
            Paragraph(f['title'], styles['TableCellBold']),
            Paragraph(f['cause'][:110] + "...", styles['TableCell'])
        ])

    t_matrix = Table(matrix_data, colWidths=[printable_w * 0.06, printable_w * 0.18, printable_w * 0.36, printable_w * 0.40])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), CARD_HEADER_BG),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_matrix)
    story.append(PageBreak())

    # Detailed Failure Cases (Exclusively Text-Based)
    story.append(Paragraph("Detailed Chronological Failure Cases, Root Cause Diagnostics & Solutions", styles['SectionHeading']))
    story.append(Paragraph("The following sections record each engineering failure in full technical depth, detailing the exact failure symptoms, underlying root causes, and permanent solutions.", styles['Body']))
    story.append(Spacer(1, 6))

    for f in raw_failures:
        card_elements = []

        # Card Title Table (Dark Header Bar)
        header_table = Table([[
            Paragraph(f"<b>FAILURE CASE #{f['id']}: {f['title'].upper()}</b>", styles['CardHeaderTitle']),
            Paragraph(f"<font color='#94A3B8'>DOMAIN:</font> <b>{f['domain']}</b>", ParagraphStyle('Dom', fontName='Helvetica', fontSize=8, leading=10, textColor=colors.white, alignment=2))
        ]], colWidths=[printable_w * 0.75, printable_w * 0.25])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), CARD_HEADER_BG),
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        card_elements.append(header_table)

        # Card Content Rows
        content_data = [
            [
                Paragraph("<b>Observed Error Symptom / Diagnostic Traceback:</b>", styles['CardLabelError']),
                Paragraph(html.escape(f['symptom']), styles['CardTextError'])
            ],
            [
                Paragraph("<b>Root Cause Analysis (Failure Reason):</b>", styles['CardLabelReason']),
                Paragraph(html.escape(f['cause']), styles['CardTextReason'])
            ],
            [
                Paragraph("<b>Applied Permanent Engineering Solution:</b>", styles['CardLabelFix']),
                Paragraph(html.escape(f['fix']), styles['CardTextFix'])
            ],
        ]

        t_card = Table(content_data, colWidths=[printable_w * 0.28, printable_w * 0.72])
        t_card.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), ERROR_BG),
            ('BACKGROUND', (0,1), (-1,1), colors.white),
            ('BACKGROUND', (0,2), (-1,2), FIX_BG),
            ('BOX', (0,0), (-1,-1), 0.8, BORDER_COLOR),
            ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#E2E8F0")),
            ('PADDING', (0,0), (-1,-1), 4.5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        card_elements.append(t_card)
        card_elements.append(Spacer(1, 7))

        story.append(KeepTogether(card_elements))

    print(f"Building Clean Failures Report PDF (No Images): {OUTPUT_PDF}...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Success! {OUTPUT_PDF} generated successfully.")


if __name__ == '__main__':
    build_pdf()
