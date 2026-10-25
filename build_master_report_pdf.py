#!/usr/bin/env python3
"""
build_master_report_pdf.py
Generates the Unified Master Academic Engineering Report for the AgileX Scout Mini AMR.
Combines:
1. The Core Robotics Academic Report (SolidWorks CAD, Kinematics, ROS 2 Jazzy, Gazebo Harmonic, EKF, SLAM, Nav2)
2. The Civil Architectural Multi-Room Environment Report (20x16m facility, math mapping, 7 stations, civil patrol)
3. The Exhaustive Engineering Troubleshooting & Failures Report (All 22 failures, symptoms, causes, solutions)
"""

import os
import sys
import html
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
import shutil
from PIL import Image as PILImage
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Preformatted, Image as RLImage
)
from reportlab.pdfgen import canvas

WORKSPACE = Path("/home/sailakshmi/agilex")
OUTPUT_PDF = WORKSPACE / "FINAL_COMPREHENSIVE_PROJECT_REPORT.pdf"

# Palette
PRIMARY = colors.HexColor("#0F172A")    # Deep Slate / Navy
SECONDARY = colors.HexColor("#0369A1")  # Tech Blue
ACCENT = colors.HexColor("#991B1B")     # Crimson
ACCENT_GREEN = colors.HexColor("#166534")
DARK_TEXT = colors.HexColor("#0F172A")  # Slate 900
MUTED_TEXT = colors.HexColor("#475569") # Slate 600
LIGHT_BG = colors.HexColor("#F8FAFC")   # Slate 50
CODE_BG = colors.HexColor("#F8FAFC")
CODE_BORDER = colors.HexColor("#CBD5E1")
BORDER_COLOR = colors.HexColor("#CBD5E1")
DIVIDER_COLOR = colors.HexColor("#E2E8F0")
HEADER_BG = colors.HexColor("#1E293B")
ERROR_BG = colors.HexColor("#FEF2F2")
FIX_BG = colors.HexColor("#F0FDF4")


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

        # Running header (all pages matching ROS_PROJECT_REPORT_SAILAKSHMI-1.pdf)
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#617488"))
        self.drawRightString(w - 36, h - 24, "RA23E01: Robot Operating System (ROS) | ")

        # Running footer (all pages matching ROS_PROJECT_REPORT_SAILAKSHMI-1.pdf)
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#617488"))
        self.drawString(36, 18, "AgileX Scout Mini 4WD AMR — ROS 2 Jazzy Jalisco & Gazebo Harmonic Simulation")
        if self._pageNumber > 1:
            self.drawRightString(w - 36, 18, f"Page {self._pageNumber} of {page_count}")

        # Outer frame
        self.setStrokeColor(colors.HexColor("#F1F5F9"))
        self.setLineWidth(0.5)
        self.rect(22, 14, w - 44, h - 28)

        self.restoreState()


def get_styles():
    base = getSampleStyleSheet()
    styles = {
        'DocTitle': ParagraphStyle(
            'DocTitle', parent=base['Normal'],
            fontName='Times-Bold', fontSize=18, leading=22,
            textColor=PRIMARY, alignment=1, spaceAfter=5
        ),
        'DocSubtitle': ParagraphStyle(
            'DocSubtitle', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=10, leading=14,
            textColor=SECONDARY, alignment=1, spaceAfter=8
        ),
        'ChapterHeading': ParagraphStyle(
            'ChapterHeading', parent=base['Heading1'],
            fontName='Times-Bold', fontSize=13, leading=16,
            textColor=PRIMARY, spaceBefore=10, spaceAfter=4, keepWithNext=True
        ),
        'SectionHeading': ParagraphStyle(
            'SectionHeading', parent=base['Heading2'],
            fontName='Times-Bold', fontSize=10.5, leading=13.5,
            textColor=SECONDARY, spaceBefore=7, spaceAfter=3, keepWithNext=True
        ),
        'SubSectionHeading': ParagraphStyle(
            'SubSectionHeading', parent=base['Heading3'],
            fontName='Helvetica-Bold', fontSize=8.5, leading=11.5,
            textColor=DARK_TEXT, spaceBefore=5, spaceAfter=2, keepWithNext=True
        ),
        'Body': ParagraphStyle(
            'Body', parent=base['BodyText'],
            fontName='Times-Roman', fontSize=7.8, leading=10.8,
            textColor=DARK_TEXT, spaceAfter=3
        ),
        'BodyBold': ParagraphStyle(
            'BodyBold', parent=base['BodyText'],
            fontName='Times-Bold', fontSize=7.8, leading=10.8,
            textColor=DARK_TEXT, spaceAfter=2
        ),
        'Bullet': ParagraphStyle(
            'Bullet', parent=base['BodyText'],
            fontName='Times-Roman', fontSize=7.6, leading=10.4,
            textColor=DARK_TEXT, leftIndent=12, firstLineIndent=-8, spaceAfter=1.5
        ),
        'TableHead': ParagraphStyle(
            'TableHead', fontName='Helvetica-Bold', fontSize=7.2, leading=9.2, textColor=colors.white, alignment=0
        ),
        'TableCell': ParagraphStyle(
            'TableCell', fontName='Helvetica', fontSize=7.0, leading=9.0, textColor=DARK_TEXT
        ),
        'TableCellBold': ParagraphStyle(
            'TableCellBold', fontName='Helvetica-Bold', fontSize=7.0, leading=9.0, textColor=DARK_TEXT
        ),
        'CodeLine': ParagraphStyle(
            'CodeLine', fontName='Courier', fontSize=6.5, leading=8.2, textColor=colors.HexColor("#0F172A")
        ),
        'CalloutBox': ParagraphStyle(
            'CalloutBox', fontName='Helvetica-Oblique', fontSize=7.6, leading=10.4,
            textColor=DARK_TEXT, backColor=LIGHT_BG, borderColor=SECONDARY,
            borderWidth=0.8, borderPadding=4, spaceBefore=3, spaceAfter=4
        ),
        'CardHeaderTitle': ParagraphStyle(
            'CardHeaderTitle', fontName='Helvetica-Bold', fontSize=8.0, leading=10.5, textColor=colors.white
        ),
        'CardTextError': ParagraphStyle(
            'CardTextError', fontName='Courier-Bold', fontSize=6.8, leading=8.6, textColor=ACCENT
        ),
        'CardTextReason': ParagraphStyle(
            'CardTextReason', fontName='Helvetica', fontSize=7.4, leading=9.8, textColor=DARK_TEXT
        ),
        'CardTextFix': ParagraphStyle(
            'CardTextFix', fontName='Helvetica', fontSize=7.4, leading=9.8, textColor=ACCENT_GREEN
        ),
    }
    return styles



def make_figure_flowable(img_path, title, caption, fig_num_str, pw):
    img_path = str(img_path)
    if not os.path.exists(img_path):
        print(f"Warning: image path {img_path} not found")
        return []
    try:
        with PILImage.open(img_path) as im:
            orig_w, orig_h = im.size
        aspect = orig_h / orig_w
        target_w = pw - 16
        target_h = target_w * aspect
        if target_h > 3.4 * inch:
            target_h = 3.4 * inch
            target_w = target_h / aspect
            
        rl_img = RLImage(img_path, width=target_w, height=target_h)
        
        title_p = Paragraph(f"<b>FIGURE {fig_num_str}: {title.upper()}</b>", ParagraphStyle(
            'FigTitle', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=SECONDARY, alignment=1, spaceAfter=3
        ))
        caption_p = Paragraph(f"<i>{caption}</i>", ParagraphStyle(
            'FigCap', fontName='Helvetica', fontSize=7.2, leading=9.5, textColor=DARK_TEXT, alignment=1, spaceBefore=3
        ))
        
        t_fig = Table([[title_p], [rl_img], [caption_p]], colWidths=[pw])
        t_fig.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
            ('BOX', (0,0), (-1,-1), 0.8, SECONDARY),
            ('INNERGRID', (0,0), (-1,-1), 0, colors.transparent),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        return [Spacer(1, 4), t_fig, Spacer(1, 6)]
    except Exception as e:
        print(f"Error loading figure {img_path}: {e}")
        return []

def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=38,
        bottomMargin=38
    )
    w_page, h_page = A4
    pw = w_page - 72

    styles = get_styles()
    story = []

    # =========================================================================
    # PAGE 1: COVER PAGE (EXACT MODEL FROM ROS_PROJECT_REPORT_SAILAKSHMI-1.pdf)
    # =========================================================================
    story.append(Spacer(1, 25))
    story.append(Paragraph(
        "END-TO-END DESIGN, KINEMATIC MODELING,<br/>"
        "SIMULATION, AND AUTONOMOUS NAVIGATION OF THE<br/>"
        "AGILEX SCOUT MINI 4WD AMR",
        ParagraphStyle('ExactCoverTitle', fontName='Times-Bold', fontSize=16, leading=21, textColor=colors.HexColor("#933735"), alignment=1, spaceAfter=14)
    ))

    story.append(Paragraph(
        "COURSE CODE: RA23E01 | COURSE: ROBOT OPERATING SYSTEM (ROS)",
        ParagraphStyle('ExactCourse', fontName='Times-Bold', fontSize=12, leading=16, textColor=colors.black, alignment=1, spaceAfter=16)
    ))

    story.append(Paragraph(
        "Submitted by<br/><b>SAILAKSHMI B T – 2024511019</b>",
        ParagraphStyle('ExactSubm', fontName='Times-Bold', fontSize=13, leading=18, textColor=colors.black, alignment=1, spaceAfter=14)
    ))

    story.append(Paragraph(
        "BACHELOR OF ENGINEERING<br/><i>in</i><br/><b>ROBOTICS AND AUTOMATION</b>",
        ParagraphStyle('ExactDeg', fontName='Times-Bold', fontSize=14, leading=18, textColor=colors.black, alignment=1, spaceAfter=12)
    ))

    # Maroon Anna University Emblem Logo
    maroon_logo = str(WORKSPACE / "docs/images/anna_university_maroon_logo.png")
    if os.path.exists(maroon_logo):
        story.append(RLImage(maroon_logo, width=1.65*inch, height=1.65*inch, hAlign='CENTER'))
        story.append(Spacer(1, 12))

    story.append(Paragraph(
        "<i>From SolidWorks Mechanical CAD Modeling to ROS 2 Jazzy & Gazebo Harmonic Simulation, Multi-<br/>"
        "Modal Perception, EKF Sensor Fusion, SLAM Mapping, and Nav2 Waypoint Navigation</i>",
        ParagraphStyle('ExactSubt', fontName='Times-Italic', fontSize=10.5, leading=14.5, textColor=colors.black, alignment=1, spaceAfter=22)
    ))

    story.append(Paragraph(
        "DEPARTMENT OF PRODUCTION TECHNOLOGY<br/>"
        "MADRAS INSTITUTE OF TECHNOLOGY<br/>"
        "ANNA UNIVERSITY - CHENNAI 600044",
        ParagraphStyle('ExactDept', fontName='Times-Bold', fontSize=13, leading=17, textColor=colors.black, alignment=1)
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: BONAFIDE CERTIFICATE (EXACT MODEL FROM ROS_PROJECT_REPORT_SAILAKSHMI-1.pdf)
    # =========================================================================
    story.append(Spacer(1, 35))
    story.append(Paragraph(
        "BONAFIDE CERTIFICATE",
        ParagraphStyle('ExactCertHdr', fontName='Times-Bold', fontSize=17, leading=22, textColor=colors.black, alignment=1, spaceAfter=28)
    ))

    cert_p_text = (
        "Certified that this project report &ldquo;<b>END-TO-END DESIGN, KINEMATIC "
        "MODELING, SIMULATION, AND AUTONOMOUS NAVIGATION OF "
        "THE AGILEX SCOUT MINI 4WD AMR</b>&rdquo; is the Bonafide word of "
        "Sailakshmi B T (2024511019) who carried out the project work under my "
        "supervision."
    )
    story.append(Paragraph(cert_p_text, ParagraphStyle('ExactCertBody', fontName='Times-Roman', fontSize=13, leading=20, textColor=colors.black, spaceAfter=100)))

    sig_data = [
        [Paragraph("<b>SIGNATURE</b>", ParagraphStyle('S1', fontName='Times-Bold', fontSize=11, leading=14, textColor=colors.black)),
         Paragraph("<b>SIGNATURE</b>", ParagraphStyle('S2', fontName='Times-Bold', fontSize=11, leading=14, textColor=colors.black, alignment=2))],
        [Paragraph("<b>HEAD OF THE DEPARTMENT</b>", ParagraphStyle('H1', fontName='Times-Bold', fontSize=11, leading=14, textColor=colors.black)),
         Paragraph("<b>SUPERVISOR</b>", ParagraphStyle('H2', fontName='Times-Bold', fontSize=11, leading=14, textColor=colors.black, alignment=2))]
    ]
    t_sig = Table(sig_data, colWidths=[pw * 0.5, pw * 0.5])
    t_sig.setStyle(TableStyle([
        ('PADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_sig)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: ABSTRACT (EXACT MODEL FROM ROS_PROJECT_REPORT_SAILAKSHMI-1.pdf)
    # =========================================================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("ABSTRACT", ParagraphStyle('ExactAbsHdr', fontName='Times-Bold', fontSize=16, leading=20, textColor=colors.black, alignment=1, spaceAfter=18)))

    abs_p1 = (
        "This project investigates the design, kinematic formulation, state estimation, and autonomous navigation "
        "lifecycle for a 4-Wheel Drive (4WD) skid-steer Autonomous Mobile Robot (AMR) based on the AgileX "
        "Scout Mini platform. To resolve the fundamental challenge of non-linear lateral tire slippage and rapid "
        "odometry degradation inherent to skid-steer kinematics without wheel encoders, a multi-stage engineering "
        "framework was developed in ROS 2 Jazzy Jalisco and Gazebo Harmonic on Ubuntu 24.04 LTS."
    )
    story.append(Paragraph(abs_p1, ParagraphStyle('AbsP1', fontName='Times-Roman', fontSize=11, leading=15.5, textColor=colors.black, alignment=4, spaceAfter=10)))

    abs_p2 = (
        "The physical robot was modeled in SolidWorks with mass moments of inertia, converted into a ROS REP-103 "
        "compliant URDF, and tuned with calibrated contact friction parameters (mu1 = 1.0, mu2 = 0.1). A "
        "sensor suite comprising a 360-degree 2D LiDAR (20 Hz), a 6-Axis IMU (100 Hz), and an RGB-D depth "
        "camera (30 Hz) was integrated. An Extended Kalman Filter (robot_localization) fused wheel velocities "
        "with inertial angular rates, eliminating cumulative rotational drift. Real-time 2D mapping via "
        "slam_toolbox produced 5 cm/pixel metric occupancy grids, while the Nav2 stack—incorporating 3D "
        "Voxel clearance costmaps, AMCL probabilistic particle filter localization, and DWB local trajectory "
        "optimization—executed an autonomous multi-station industrial patrol mission with zero collisions."
    )
    story.append(Paragraph(abs_p2, ParagraphStyle('AbsP2', fontName='Times-Roman', fontSize=11, leading=15.5, textColor=colors.black, alignment=4, spaceAfter=18)))

    kw_text = (
        "<b>Keywords:</b> Autonomous Mobile Robot (AMR), AgileX Scout Mini, ROS 2 Jazzy Jalisco, "
        "Gazebo Harmonic, Skid-Steer Kinematics, EKF Sensor Fusion, SLAM Toolbox, "
        "Nav2 Navigation Stack."
    )
    story.append(Paragraph(kw_text, ParagraphStyle('AbsKW', fontName='Times-Roman', fontSize=10.5, leading=14.5, textColor=colors.black)))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: TABLE OF CONTENTS
    # =========================================================================
    story.append(Spacer(1, 15))
    story.append(Paragraph("Table of Contents", ParagraphStyle('ExactTOCHdr', fontName='Times-Bold', fontSize=16, leading=20, textColor=colors.black, spaceAfter=14)))

    toc_list = [
        "1. Executive Summary & Project Objectives",
        "2. Robot Specifications & Mathematical Skid-Steer Kinematics",
        "3. Mechanical Design & SolidWorks CAD Modeling Pipeline",
        "4. ROS 2 Package Architecture & URDF Model Hardening",
        "5. Physics Engine & Simulation in Gazebo Harmonic (gz-sim8)",
        "6. Multi-Modal Perception Sensor Suite Integration",
        "7. State Estimation & Sensor Fusion via Extended Kalman Filter (EKF)",
        "8. Simultaneous Localization and Mapping (SLAM)",
        "9. Autonomous Navigation Stack (Nav2) Implementation",
        "10. Autonomous Multi-Station Waypoint Patrol Mission (Arena & Civil Facility)",
        "11. Step-by-Step Execution, Results & Verification Log (with Timestamps)",
        "12. Engineering Challenges, Root-Cause Analysis & Solutions Matrix",
        "13. Conclusion & Future Work",
        "14. References & Code Repository (GitHub: https://github.com/Saibts/AgileX_ScoutMini_JAZZY)"
    ]
    for item in toc_list:
        story.append(Paragraph(f"&bull;&nbsp;&nbsp;{item}", ParagraphStyle('TOCItem', fontName='Times-Roman', fontSize=10.5, leading=16, textColor=colors.black, leftIndent=8)))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 1: ROBOT ARCHITECTURE & SOLIDWORKS CAD KINEMATICS
    # =========================================================================
    story.append(Paragraph("1. Robot Mechanical Modeling & Skid-Steer Kinematics", styles['ChapterHeading']))
    story.append(Paragraph(
        "The AgileX Scout Mini is an industrial-grade compact mobile robot utilizing a 4-wheel differential / skid-steer drive mechanism. "
        "Because the wheels do not pivot, lateral steering requires commanding differential angular velocities across the left and right sides, "
        "inducing intentional tire scrubbing against the ground.", styles['Body']))

    kin_table_data = [
        [Paragraph("<b>Parameter</b>", styles['TableHead']), Paragraph("<b>Design Value</b>", styles['TableHead']), Paragraph("<b>Kinematic / Physical Significance</b>", styles['TableHead'])],
        [Paragraph("Chassis Footprint", styles['TableCellBold']), Paragraph("627 mm &times; 549 mm &times; 227 mm", styles['TableCell']), Paragraph("Total envelope of the monocoque chassis assembly", styles['TableCell'])],
        [Paragraph("Track Width (2w)", styles['TableCellBold']), Paragraph("0.612 m (612 mm)", styles['TableCell']), Paragraph("Effective lateral distance between left and right wheel tire centerlines", styles['TableCell'])],
        [Paragraph("Wheelbase (2l)", styles['TableCellBold']), Paragraph("0.452 m (452 mm)", styles['TableCell']), Paragraph("Longitudinal distance between front and rear axle centers", styles['TableCell'])],
        [Paragraph("Wheel Radius (r)", styles['TableCellBold']), Paragraph("0.080 m (80 mm)", styles['TableCell']), Paragraph("Effective rolling radius of heavy-duty rubber tires", styles['TableCell'])],
        [Paragraph("Robot Mass (m)", styles['TableCellBold']), Paragraph("18.0 kg (Unloaded)", styles['TableCell']), Paragraph("Rigid body mass calibrated with low Center of Mass (Z = 0.10 m)", styles['TableCell'])],
        [Paragraph("Max Linear Velocity", styles['TableCellBold']), Paragraph("1.5 m/s", styles['TableCell']), Paragraph("Maximum forward/reverse driving capability under closed-loop control", styles['TableCell'])],
        [Paragraph("Max Angular Velocity", styles['TableCellBold']), Paragraph("2.5 rad/s", styles['TableCell']), Paragraph("In-place skid-steer yaw rate capability", styles['TableCell'])],
    ]
    t_kin = Table(kin_table_data, colWidths=[pw * 0.25, pw * 0.25, pw * 0.50])
    t_kin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.4, DIVIDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 2.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_kin)
    story.append(Spacer(1, 4))

    math_box = (
        "<b>Skid-Steer Kinematic Transformation:</b><br/>"
        "Given commanded robot linear velocity <i>v<sub>x</sub></i> and angular velocity <i>&omega;<sub>z</sub></i>, the required left and right wheel rotational speeds (&omega;<sub>L</sub>, &omega;<sub>R</sub>) are governed by:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>&omega;<sub>L</sub> = (v<sub>x</sub> &minus; &alpha; &middot; w &middot; &omega;<sub>z</sub>) / r</b> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; "
        "<b>&omega;<sub>R</sub> = (v<sub>x</sub> + &alpha; &middot; w &middot; &omega;<sub>z</sub>) / r</b><br/>"
        "where <i>&alpha; &ge; 1.0</i> is the empirical tire scrubbing slip coefficient (&alpha; = 1.05 in simulation). "
        "The coordinate frame strictly follows <b>ROS REP-103</b>: <b>+X Forward</b>, <b>+Y Left</b>, <b>+Z Upward</b>."
    )
    story.append(Paragraph(math_box, styles['CalloutBox']))
    story.append(Spacer(1, 4))
    story.extend(make_figure_flowable(
        WORKSPACE / "docs/images/solidworks_amr_cad_assembly.png",
        "SolidWorks 3D Full Assembly (Assem2.SLDASM)",
        "Complete 3D solid model assembly of the AgileX Scout Mini 4WD AMR in SolidWorks Premium 2023 showing monocoque chassis, top plate, hub motors, and 4 wheels.",
        "1.1", pw
    ))

    # =========================================================================
    # CHAPTER 2: ROS 2 JAZZY & GAZEBO HARMONIC SIMULATION FRAMEWORK
    # =========================================================================
    story.append(Paragraph("2. ROS 2 Jazzy & Gazebo Harmonic Simulation Architecture", styles['ChapterHeading']))
    story.append(Paragraph(
        "Ubuntu 24.04 LTS (Noble Numbat) completely retired Gazebo Classic (gazebo11). The AgileX simulation leverages "
        "<b>Gazebo Harmonic (`gz-sim8`)</b> bridged to <b>ROS 2 Jazzy Jalisco</b> via `ros_gz_bridge`. Bidirectional communication translates "
        "control inputs, transforms, physics states, and sensor telemetry seamlessly without proprietary middleware.", styles['Body']))

    sensor_data = [
        [Paragraph("<b>Subsystem / Sensor</b>", styles['TableHead']), Paragraph("<b>ROS 2 Topic & Message Type</b>", styles['TableHead']), Paragraph("<b>Operational Characteristics</b>", styles['TableHead'])],
        [Paragraph("2D LiDAR (`gpu_lidar`)", styles['TableCellBold']), Paragraph("/scan<br/>sensor_msgs/msg/LaserScan", styles['TableCell']), Paragraph("360&deg; FOV, 720 samples, 20 Hz, 0.15m to 16.0m range. Mounted at Z = 0.36m.", styles['TableCell'])],
        [Paragraph("6-Axis IMU Sensor", styles['TableCellBold']), Paragraph("/imu<br/>sensor_msgs/msg/Imu", styles['TableCell']), Paragraph("100 Hz angular velocity and linear acceleration with Gaussian noise model.", styles['TableCell'])],
        [Paragraph("RGB-D Depth Camera", styles['TableCellBold']), Paragraph("/camera/points<br/>sensor_msgs/msg/PointCloud2", styles['TableCell']), Paragraph("30 Hz structured 3D point cloud for Nav2 3D voxel obstacle clearing.", styles['TableCell'])],
        [Paragraph("4WD DiffDrive Plugin", styles['TableCellBold']), Paragraph("/cmd_vel &rarr; /odom<br/>nav_msgs/msg/Odometry", styles['TableCell']), Paragraph("4-wheel skid-steer actuation with electrical braking at zero velocity.", styles['TableCell'])],
        [Paragraph("Sensor Fusion EKF", styles['TableCellBold']), Paragraph("/odometry/filtered<br/>nav_msgs/msg/Odometry", styles['TableCell']), Paragraph("Fuses raw /odom + /imu at 50 Hz, publishing odom &rarr; base_footprint TF.", styles['TableCell'])],
    ]
    t_sens = Table(sensor_data, colWidths=[pw * 0.28, pw * 0.32, pw * 0.40])
    t_sens.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.4, DIVIDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 2.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_sens)
    story.append(Spacer(1, 4))
    story.extend(make_figure_flowable(
        WORKSPACE / "docs/images/screenshot_gazebo_harmonic_arena.png",
        "Gazebo Harmonic (gz-sim8) Simulation Arena",
        "Gazebo Harmonic window showing AgileX Scout Mini spawned in the 10m x 10m enclosed arena with perimeter walls, cylindrical pillars, and boxes.",
        "2.1", pw
    ))
    story.extend(make_figure_flowable(
        WORKSPACE / "docs/images/screenshot_tf2_frames_tree.png",
        "TF2 Kinematic Transformation Tree",
        "TF tree showing unbroken transform hierarchy from odom -> base_footprint -> base_link -> wheel and sensor links.",
        "2.2", pw
    ))

    # =========================================================================
    # CHAPTER 3: STATE ESTIMATION, SLAM & 10M x 10M ARENA AUTONOMY
    # =========================================================================
    story.append(Paragraph("3. Sensor Fusion (EKF), SLAM Mapping & Nav2 Arena Navigation", styles['ChapterHeading']))
    story.append(Paragraph(
        "<b>Extended Kalman Filter (EKF):</b> Pure wheel odometry in skid-steer robots suffers catastrophic rotational drift "
        "(up to 120&deg; error after a 360&deg; rotation) due to wheel scrubbing. Deploying `robot_localization` in 2D planar mode "
        "fuses wheel velocity measurements with the high-precision 100Hz gyroscope rate from the IMU, yielding drift-free "
        "odometry (`/odometry/filtered`) and stable transforms.", styles['Body']))
    story.append(Paragraph(
        "<b>SLAM & Nav2 Autonomous Stack:</b> Utilizing `slam_toolbox` with Ceres scan-matching generates high-fidelity 2D occupancy "
        "grid maps (`amr_world_map.yaml` at 0.05m/pixel resolution). Nav2 integrates AMCL particle-filter localization, global "
        "costmaps, 3D voxel local costmaps, and DWB local trajectory planners for collision-free waypoint navigation.", styles['Body']))
    story.append(Spacer(1, 4))
    story.extend(make_figure_flowable(
        WORKSPACE / "docs/images/screenshot_rviz2_lidar_pointcloud.png",
        "RViz2 Multi-Modal Perception Displays (LaserScan + PointCloud2)",
        "RViz2 showing 360-degree rainbow LaserScan ray returns and 3D RGB-D depth camera point cloud projected onto surrounding obstacles.",
        "3.1", pw
    ))
    story.extend(make_figure_flowable(
        WORKSPACE / "docs/images/screenshot_slam_toolbox_map.png",
        "2D SLAM Metric Occupancy Grid Map (amr_world_map.pgm)",
        "Completed 2D SLAM occupancy grid map showing clean boundary walls, four internal pillar obstacles, and mapped free space.",
        "3.2", pw
    ))
    story.extend(make_figure_flowable(
        WORKSPACE / "docs/images/screenshot_patrol_mission_sync.png",
        "Autonomous Patrol Multi-Waypoint Execution & Mission Synchronization",
        "Synchronized 3-pane operational trace showing autonomous mission console logging arrival at Station 1 (Foyer: 0.00, -3.80), 3-second site dwell, and real-time distance countdown toward Station 2 (Corridor Hub: 0.00, 0.00), paired with Gazebo Harmonic 3D DART physics and RViz2 navigation costmaps.",
        "3.3", pw
    ))

    # =========================================================================
    # CHAPTER 4: CIVIL ARCHITECTURAL MULTI-ROOM ENVIRONMENT
    # =========================================================================
    story.append(Paragraph("4. Civil Architectural Multi-Room Environment & Navigation", styles['ChapterHeading']))
    story.append(Paragraph(
        "To elevate the project to realistic industrial benchmark standards, a dedicated <b>Civil & Structural Engineering Research Facility</b> "
        "($20.0 m &times; 16.0 m$, total floor area $3320 m&sup2;) was engineered. The world features standard 1.2m doorways, "
        "0.45m square RCC columns, and realistic civil laboratory equipment.", styles['Body']))

    civil_layout_ascii = (
        "+=============================================================================================+\n"
        "|                             NORTH PERIMETER WALL (20.0 m)                                   |\n"
        "|  +------------------------+  +-------------------------+  +------------------------------+  |\n"
        "|  |  STRUCTURAL MATERIALS  |  |      CIVIL SEMINAR      |  |     BIM, CAD & ROBOTICS      |  |\n"
        "|  |   & CONCRETE TESTING   |  |       CONFERENCE        |  |       COMPUTING STUDIO       |  |\n"
        "|  |   (Station 3: -7, 3.5) |  |   (Station 4: 0, 3.0)   |  |     (Station 5: 7, 3.5)      |  |\n"
        "|  +----- [1.2m Door] ------+  +------ [1.4m Door] ------+  +------- [1.2m Door] ----------+  |\n"
        "|                                                                                             |\n"
        "|  <<<<<<<<<<<<<< MAIN CENTRAL ARTERIAL CORRIDOR (Width: 2.4 m, Length: 20.0 m) >>>>>>>>>>>>> |\n"
        "|  [Column @ -4m]                  (Station 2: Hub @ 0, 0)                     [Column @ +4m] |\n"
        "|                                                                                             |\n"
        "|  +----- [1.2m Door] ------+  +====== [4.0m Open Atrium] =+  +------- [1.2m Door] ----------+  |\n"
        "|  |  GEOTECHNICAL SURVEY   |  |   MAIN ENTRANCE FOYER   |  |     DEPARTMENT ARCHIVES      |  |\n"
        "|  |    & SOIL MECHANICS    |  |     (Home Base / S1)    |  |      & EQUIPMENT VAULT       |  |\n"
        "|  |  (Station 7: -4.5, -5) |  |   (Station 1: 0, -3.8)  |  |    (Station 6: 4.5, -4.8)    |  |\n"
        "|  +------------------------+  +-------------------------+  +------------------------------+  |\n"
        "|                             SOUTH PERIMETER WALL (20.0 m)                                   |\n"
        "+=============================================================================================+"
    )
    p_ascii = Preformatted(civil_layout_ascii, styles['CodeLine'])
    t_ascii = Table([[p_ascii]], colWidths=[pw])
    t_ascii.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_ascii)
    story.append(Spacer(1, 4))

    civil_math_text = (
        "<b>Mathematical Mapping Pipeline & Deterministic Raytracing:</b><br/>"
        "To guarantee 100% agreement between Gazebo physical walls and Nav2 costmap pixels, world geometry and 2D grid are synthesized "
        "deterministically via <code>generate_civil_world.py</code>. With bounds $XX &isin; [-11, 11] m, $YY &isin; [-9, 9] m, "
        "and resolution &Delta; = 0.05 m/px, grid dimensions are <b>440 &times; 360 pixels</b>. "
        "Coordinate transforms map world coordinates $(x_w, y_w)$ to discrete grid cells: "
        "<b>u = round((x<sub>w</sub> &minus; X<sub>0</sub>)/&Delta;)</b> and <b>v = round((y<sub>w</sub> &minus; Y<sub>0</sub>)/&Delta;)</b>. "
        "Floor space is encoded as <b>254 (Free)</b>, walls/columns as <b>0 (Occupied)</b>, and outside bounds as <b>205 (Unknown)</b>."
    )
    story.append(Paragraph(civil_math_text, styles['CalloutBox']))
    story.append(Spacer(1, 4))

    # Civil Patrol Station Table
    story.append(Paragraph("<b>Civil Research Facility 7-Station Autonomous Patrol Mission:</b>", styles['SubSectionHeading']))
    patrol_stations = [
        [Paragraph("<b>Station</b>", styles['TableHead']), Paragraph("<b>Zone / Department Description</b>", styles['TableHead']), Paragraph("<b>Coordinates (X, Y, Yaw)</b>", styles['TableHead']), Paragraph("<b>Inspection Task</b>", styles['TableHead'])],
        [Paragraph("Station 1", styles['TableCellBold']), Paragraph("Entrance Foyer & Atrium (Home Base)", styles['TableCell']), Paragraph("(0.0 m, -3.8 m, 90&deg;)", styles['TableCell']), Paragraph("Visitor reception & AMR staging baseline", styles['TableCell'])],
        [Paragraph("Station 2", styles['TableCellBold']), Paragraph("Central Arterial Corridor Hub", styles['TableCell']), Paragraph("(0.0 m, 0.0 m, 0&deg;)", styles['TableCell']), Paragraph("Arterial chicane transit & traffic dispatch", styles['TableCell'])],
        [Paragraph("Station 3", styles['TableCellBold']), Paragraph("Structural Materials & Concrete Lab", styles['TableCell']), Paragraph("(-7.0 m, 3.5 m, 90&deg;)", styles['TableCell']), Paragraph("Compression test specimen monitoring", styles['TableCell'])],
        [Paragraph("Station 4", styles['TableCellBold']), Paragraph("Civil Seminar & Conference Hall", styles['TableCell']), Paragraph("(0.0 m, 3.0 m, 90&deg;)", styles['TableCell']), Paragraph("Environmental acoustics & air quality check", styles['TableCell'])],
        [Paragraph("Station 5", styles['TableCellBold']), Paragraph("BIM, CAD & Robotics Computing Studio", styles['TableCell']), Paragraph("(7.0 m, 3.5 m, 0&deg;)", styles['TableCell']), Paragraph("Digital fabrication & 3D scanner inspection", styles['TableCell'])],
        [Paragraph("Station 6", styles['TableCellBold']), Paragraph("Department Archives & Storage Vault", styles['TableCell']), Paragraph("(4.5 m, -4.8 m, -90&deg;)", styles['TableCell']), Paragraph("Survey instrument inventory check", styles['TableCell'])],
        [Paragraph("Station 7", styles['TableCellBold']), Paragraph("Geotechnical Survey & Soil Mechanics", styles['TableCell']), Paragraph("(-4.5 m, -5.0 m, 180&deg;)", styles['TableCell']), Paragraph("Soil triaxial shear apparatus audit", styles['TableCell'])],
    ]
    t_patrol = Table(patrol_stations, colWidths=[pw * 0.15, pw * 0.35, pw * 0.25, pw * 0.25])
    t_patrol.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.4, DIVIDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_patrol)
    story.append(Spacer(1, 6))
    story.extend(make_figure_flowable(
        WORKSPACE / "docs/images/screenshot_gazebo_harmonic_civil.png",
        "Gazebo Harmonic 3D Multi-Room Civil Architectural Facility Simulation",
        "Gazebo Harmonic perspective view of the 20m x 16m (320 m^2) multi-room civil architectural facility (civil_world.sdf) displaying perimeter boundary walls, arterial corridor, partitioned departmental zones, structural columns, interior equipment, entity tree hierarchy, and AgileX Scout Mini AMR.",
        "4.1", pw
    ))
    story.extend(make_figure_flowable(
        WORKSPACE / "docs/images/screenshot_rviz2_slam_civil_tracing.png",
        "RViz2 Real-Time 2D SLAM Mapping & Filtered Odometry (EKF) Path Tracing",
        "RViz2 visualization showing real-time 2D SLAM occupancy grid mapping, sub-centimeter LaserScan wall returns, and dense Filtered Odometry (EKF) green arrow pose trajectory tracing the robot navigating through corridors and turning into rooms.",
        "4.2", pw
    ))

    # =========================================================================
    # CHAPTER 5: AGILEX SCOUT MINI CIVIL FLOOR GROUND STATION & TELEMETRY
    # =========================================================================
    story.append(Paragraph("5. AgileX Scout Mini Civil Floor Ground Station & Live Telemetry", styles['ChapterHeading']))
    ground_station_text = (
        "To provide centralized command, real-time perception monitoring, and point-to-navigate dispatching, a dedicated "
        "<b>Civil Floor Architectural Ground Station</b> was developed in Python utilizing PySide6/Qt and ROS 2 <code>rclpy</code> "
        "(<code>src/assem2_robot/scripts/civil_interactive_nav.py</code>). "
        "The ground station architecture features:<br/>"
        "&bull; <b>First-Person POV Front Camera Stream:</b> Real-time 640&times;480 @ 30 Hz RGB visual perception feed subscribed to <code>/camera/image_raw</code>, equipped with an augmented crosshair HUD displaying dynamic linear velocity, yaw rate, and forward obstacle clearance (2.60 m baseline).<br/>"
        "&bull; <b>Interactive Point-to-Navigate Map:</b> Click-to-dispatch goal target navigation across the 20m &times; 16m facility with immediate Nav2 action goal generation and green planned path trajectory visualization.<br/>"
        "&bull; <b>7-Station One-Click Dispatch & Autonomous Patrol Loop:</b> Direct push-button navigation to all departmental stations (S1 to S7) and full continuous patrol sequence.<br/>"
        "&bull; <b>Datasheet Specifications Modal Viewer:</b> Pop-up technical dialog verifying robot specifications (28.0 kg total mass, 0.612m track width, 0.390m wheelbase, in-situ 360&deg; zero-radius skid turn, 0.80 m/s tuned corridor velocity, and 0.50m - 0.52m costmap inflation clearance for 1.2m doorways)."
    )
    story.append(Paragraph(ground_station_text, styles['Body']))
    story.append(Spacer(1, 4))
    story.extend(make_figure_flowable(
        WORKSPACE / "docs/images/screenshot_ground_station_telemetry.png",
        "AgileX Scout Mini Civil Floor Ground Station with Live Camera Telemetry & Technical Datasheet Specs",
        "Custom PySide/Qt Ground Station user interface featuring live First-Person POV Front Camera stream (640x480 @ 30Hz), real-time velocity and obstacle clearance telemetry, interactive 7-station floor plan with point-to-navigate dispatching, autonomous patrol loop controls, and the Technical Datasheet Specifications modal displaying physical and Nav2 operational parameters.",
        "5.1", pw
    ))

    # =========================================================================
    # CHAPTER 5: EXHAUSTIVE ENGINEERING TROUBLESHOOTING & 22 FAILURES
    # =========================================================================
    story.append(Paragraph("6. Exhaustive Engineering Troubleshooting & Failure Analysis", styles['ChapterHeading']))
    story.append(Paragraph(
        "Transitioning the robot from mechanical SolidWorks CAD into ROS 2 Jazzy and Gazebo Harmonic exposed "
        "<b>22 critical engineering failures</b> across Linux OS standards, kinematic trees, ODE contact physics, FastDDS network multicasting, "
        "and Nav2 lifecycle management. The summary matrix and detailed failure cases below document the symptoms, root causes, and permanent solutions.", styles['Body']))

    raw_failures = [
        {"id": 1, "domain": "ROS 2 Build", "title": "ROS 2 Package Naming Convention Failure (ValueError)",
         "symptom": "ValueError: 'assem2.robot' is not a valid package name. InvalidFrontendLaunchFileError.",
         "cause": "SolidWorks exported the assembly name as 'assem2.robot'. In ROS 2, ament and Python packaging strictly enforce lowercase alphanumeric characters and underscores only. Periods and hyphens are illegal.",
         "fix": "Standardized the package name across package.xml, CMakeLists.txt, launch scripts, and URDF references to 'assem2_robot'."},
        {"id": 2, "domain": "OS / Filesystem", "title": "Linux Ext4 Case-Sensitivity & File Resolution (FileNotFoundError)",
         "symptom": "FileNotFoundError: [Errno 2] No such file or directory: '.../urdf/assem2.SLDASM.urdf'",
         "cause": "Linux Ext4 is strictly case-sensitive. SolidWorks exported with capital 'A' (Assem2.SLDASM.urdf) while launch file requested lowercase 'assem2'. Additionally, CMakeLists.txt lacked install(DIRECTORY urdf...).",
         "fix": "Synchronized launch file paths to exact casing 'Assem2.SLDASM.urdf' and added 'install(DIRECTORY urdf DESTINATION share/${PROJECT_NAME})' in CMakeLists.txt."},
        {"id": 3, "domain": "URDF / Mesh", "title": "Broken Mesh URI Resolution & Invisible Robot in RViz",
         "symptom": "Could not load resource [package://Assem2.SLDASM/meshes/base_link.STL]. Links were invisible.",
         "cause": "SolidWorks URDF exporter hardcoded the export assembly directory name into mesh tags ('package://Assem2.SLDASM/...'). Renaming the package broke all URI resource lookups.",
         "fix": "Executed a global regex substitution across Assem2.SLDASM.urdf replacing 'package://Assem2.SLDASM/' with 'package://assem2_robot/'."},
        {"id": 4, "domain": "Kinematics", "title": "SolidWorks Fixed Wheel Joints & Missing TF Transforms",
         "symptom": "RViz warning: 'No transform from [w1] to [base_link]'. Robot wheels appeared frozen.",
         "cause": "Exporter defaulted mated wheels to type='fixed' joints. Since fixed joints have 0 DOF, joint_state_publisher ignores them and never broadcasts dynamic wheel TF frames.",
         "fix": "Modified URDF joints j1..j4 to type='continuous' with explicit rotation axis <axis xyz='1 0 0'/>, restoring full dynamic wheel state publishing."},
        {"id": 5, "domain": "Visualization", "title": "Empty RViz Fixed Frame Dropdown & Blank Viewport",
         "symptom": "Opening RViz showed a blank viewport. Fixed Frame dropdown was empty; typing base_link failed.",
         "cause": "RViz launched with a blank default layout lacking RobotModel display plugin, and RobotModel searched for a local URDF file instead of listening to /robot_description topic.",
         "fix": "Authored a pre-configured display.rviz configuration file with Fixed Frame set to odom/map, RobotModel subscribed to /robot_description, and integrated LaserScan and TF visualizers."},
        {"id": 6, "domain": "Network / DDS", "title": "DDS Network Multicast Failures & Missing Odometry Packets",
         "symptom": "Console spam: 'Exception sending a multicast message: Network is unreachable'. Odometry dropped.",
         "cause": "FastDDS discovery attempted to broadcast peer multicast packets across external network adapters when operating offline or on restricted university subnets.",
         "fix": "Set ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST and export ROS_LOCALHOST_ONLY=1, locking DDS communications strictly to local loopback adapter (127.0.0.1)."},
        {"id": 7, "domain": "ODE Physics", "title": "Wheel 3 (j3) Infinite Spinning Physics Bug at Rest",
         "symptom": "When robot was at rest (cmd_vel = 0), Wheel 3 spun continuously at maximum velocity, violently vibrating chassis.",
         "cause": "Compounding bugs: omitted joint axis tag in j3, zero damping/friction in URDF, and initial DiffDrive plugin only controlled j1 and j2, leaving j3 unpowered and unbraked against ground micro-collisions.",
         "fix": "Added <axis xyz='-1 0 0'/>, injected <dynamics damping='0.1' friction='0.1'/>, and grouped all 4 wheels into DiffDrive plugin with active electrical braking torque at zero velocity."},
        {"id": 8, "domain": "Architecture", "title": "ROS 2 Humble to Jazzy / Gazebo Classic to Harmonic Shift",
         "symptom": "gazebo_ros plugins failed to compile and launch. Terminal error: 'gazebo: command not found'.",
         "cause": "Ubuntu 24.04 and ROS 2 Jazzy completely retired Gazebo Classic. The simulation shifted to Gazebo Harmonic (gz-sim8), requiring the new ros_gz_bridge architecture.",
         "fix": "Replaced legacy C++ .so plugins with Gazebo Harmonic native systems: gz::sim::systems::DiffDrive, gpu_lidar, and ros_gz_bridge parameter_bridge."},
        {"id": 9, "domain": "Kinematics", "title": "Robot Sunken 23 cm Below RViz Ground Grid Floor",
         "symptom": "In RViz, robot appeared half-buried beneath grid floor (Z < 0), with ground plane slicing through chassis.",
         "cause": "SolidWorks placed origin at chassis top cover plate (axle height Z = -0.1469m, tire radius 0.08m &rarr; ground at Z = -0.2269m). With zero offset, top cover sat on floor.",
         "fix": "Introduced root link 'base_footprint' with fixed joint offset xyz='-0.10185 0.16662 0.2269', lifting chassis so all 4 tires sit flush on ground at Z = 0.00m."},
        {"id": 10, "domain": "KDL Kinematics", "title": "KDL Parser Warning on Root Link Mass and Inertia",
         "symptom": "Warning: 'The root link base_link has an inertia specified, but KDL does not support root inertia.'",
         "cause": "Kinematics and Dynamics Library (KDL) tree solver mathematically requires root link of a kinematic chain to be massless and inertialess. SolidWorks exported base_link as root with 18kg mass.",
         "fix": "Established 'base_footprint' (dummy link with 0 mass and no <inertial> tag) as kinematic root, attaching base_link as its child via fixed transform."},
        {"id": 11, "domain": "Simulation", "title": "Gazebo Duplicate Spawning ('Two Bots' Collision Bug)",
         "symptom": "Launching simulation showed two colliding robot models superimposed on top of each other, causing explosive contact.",
         "cause": "ros_gz_sim create node defaults to allow_renaming: true. If a previous simulation run crashed without terminating background gz processes, a duplicate was spawned.",
         "fix": "Added '-allow_renaming false' to create node arguments, explicit spawning coordinates (Z=0.02m), and configured process cleanup scripts."},
        {"id": 12, "domain": "Build System", "title": "Disk Storage Footprint Management on Limited Partition",
         "symptom": "System warnings: Linux primary partition rapidly running low on free disk space (< 30 GB available).",
         "cause": "Standard colcon build copies entire binary trees and STL meshes into both build/ and install/ directories, while Gazebo simulation logs accumulated gigabytes of data.",
         "fix": "Used 'colcon build --symlink-install' to create symbolic links instead of duplicating files, and enforced a strict .gitignore, compressing repository footprint to ~3.3 MB."},
        {"id": 13, "domain": "Coordinate REP", "title": "Teleoperation Heading Mismatch (+Y CAD Heading vs +X ROS Heading)",
         "symptom": "Commanding +X linear velocity made robot drive sideways; turning commands rotated about wrong axis.",
         "cause": "In SolidWorks, CAD designer aligned front bumper with +Y axis. ROS standard REP-103 strictly requires +X as forward, +Y as left, and +Z as upward.",
         "fix": "Applied a +90&deg; (+1.5708 rad) yaw rotation in base_footprint_joint: origin rpy='0 0 1.5707963', aligning CAD bumper with ROS forward direction."},
        {"id": 14, "domain": "Physics Dynamics", "title": "Wheel Rotation Axis Inversion & Direction Discrepancy",
         "symptom": "In Gazebo physics, commanding positive velocity caused robot to roll backward, while RViz showed forward motion.",
         "cause": "CAD export assigned right-hand rule axes to wheel continuous joints that opposed the physical forward rotation direction of wheels.",
         "fix": "Calibrated wheel joint axes: set <axis xyz='1 0 0'/> for left wheels (j1, j2) and <axis xyz='-1 0 0'/> for right wheels (j3, j4), synchronizing physics with kinematics."},
        {"id": 15, "domain": "Sensor Framing", "title": "RGB-D Camera Inversion (Mounted on Rear Instead of Front)",
         "symptom": "RViz camera feed showed arena behind robot rather than forward path.",
         "cause": "Due to CAD origin orientation, front bumper was located at negative Y in CAD coordinates (Y = -0.355m). An initial positive offset mounted camera on rear bumper.",
         "fix": "Mounted camera_mount_joint at xyz='-0.16662 -0.355 0.065' with rpy='0 0 -1.5708', placing camera squarely on physical front bumper facing forward."},
        {"id": 16, "domain": "Localization", "title": "Severe Skid-Steer Rotational Odometry Drift",
         "symptom": "After executing a 360&deg; turn, wheel odometry reported only 240&deg; of rotation (120&deg; heading error). Scans smeared.",
         "cause": "Skid-steering relies on tire slipping. In-hub wheel encoders only measure wheel rotations, missing lateral scrubbing and track width expansion.",
         "fix": "Implemented Extended Kalman Filter (robot_localization ekf_node) fusing wheel odometry (/odom) with 100Hz gyroscope from 6-axis IMU (/imu), yielding drift-free /odometry/filtered."},
        {"id": 17, "domain": "Time / Clock", "title": "Dual /clock Publisher Timestamp Oscillations & TF Jitter",
         "symptom": "RViz displays flickered rapidly. TF buffer reported timestamps jumping backward in time and lookups failed.",
         "cause": "Both ros_gz_sim and parameter_bridge published to /clock with microsecond phase offsets, creating competing simulation clocks.",
         "fix": "Removed duplicate clock bridge from parameter_bridge arguments, leaving gz_sim as single authoritative source of simulation time."},
        {"id": 18, "domain": "ROS Lifecycle", "title": "SLAM Toolbox Lifecycle State Unconfigured Error",
         "symptom": "SLAM node spawned but failed to publish /map or /tf. Node reported unconfigured lifecycle state.",
         "cause": "In ROS 2 Jazzy, SLAM Toolbox is a Managed Lifecycle Node. Starting the raw node binary leaves it in 'Unconfigured' state without transitioning to 'Active'.",
         "fix": "Included official 'online_async_launch.py' with 'autostart: true', which uses nav2_lifecycle_manager to automatically transition SLAM to 'Active'."},
        {"id": 19, "domain": "TF Buffer", "title": "RViz 'Frame [odom] does not exist' on Base Simulation Launch",
         "symptom": "RViz showed red TF transform errors on startup whenever SLAM or Nav2 were not enabled.",
         "cause": "RViz default Fixed Frame was set to 'map', which only exists when SLAM or AMCL are active.",
         "fix": "Configured default Fixed Frame to 'odom' in display.rviz, and ensured EKF node automatically publishes odom &rarr; base_footprint transform."},
        {"id": 20, "domain": "Localization", "title": "AMCL Initial Pose Frame Mismatch",
         "symptom": "AMCL failed to initialize particles; laser scans did not align with pre-mapped walls.",
         "cause": "Initial pose was published in 'odom' frame instead of global 'map' frame.",
         "fix": "Set global_frame_id: 'map', odom_frame_id: 'odom', and configured set_initial_pose: true with initial coordinates (x=0, y=0, yaw=0) in nav2_params.yaml."},
        {"id": 21, "domain": "Nav2 Stack", "title": "ROS 2 Jazzy Nav2 Behavior Tree Navigator Architecture Shift",
         "symptom": "bt_navigator threw schema errors on startup: 'navigators parameter must be a list of plugins'.",
         "cause": "ROS 2 Jazzy refactored Nav2's bt_navigator parameters: older single-navigator configuration was replaced with a modular plugin dictionary structure.",
         "fix": "Updated nav2_params.yaml to official Jazzy format: navigators: ['navigate_to_pose', 'navigate_through_poses'] with their respective plugin definitions."},
        {"id": 22, "domain": "Mission Control", "title": "Autonomous Patrol Mission Feedback & Telemetry Supervision",
         "symptom": "Early patrol scripts hung indefinitely if navigation goal failed to compute a path around blocked stations.",
         "cause": "BasicNavigator required explicit polling of isTaskComplete() and handling of TaskResult.FAILED to transition safely to subsequent waypoints.",
         "fix": "Implemented feedback polling loop at 2Hz reading distance_remaining, with automatic recovery fallback on TaskResult.FAILED."}
    ]

    # Summary Table of 22 Failures
    story.append(Spacer(1, 4))
    fail_summary_data = [
        [Paragraph("<b>#</b>", styles['TableHead']), Paragraph("<b>Domain</b>", styles['TableHead']), Paragraph("<b>Failure Anomaly</b>", styles['TableHead']), Paragraph("<b>Primary Root Cause / Failure Reason</b>", styles['TableHead'])],
    ]
    for f in raw_failures:
        fail_summary_data.append([
            Paragraph(f"<b>#{f['id']}</b>", styles['TableCellBold']),
            Paragraph(f['domain'], styles['TableCell']),
            Paragraph(f['title'], styles['TableCellBold']),
            Paragraph(f['cause'][:105] + "...", styles['TableCell'])
        ])
    t_fail_sum = Table(fail_summary_data, colWidths=[pw * 0.06, pw * 0.18, pw * 0.36, pw * 0.40])
    t_fail_sum.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_BG),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.4, DIVIDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 2.2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_fail_sum)
    story.append(Spacer(1, 6))

    # Detailed Cards for Each Failure
    story.append(Paragraph("Detailed Chronological Failure Cases & Engineering Solutions", styles['SectionHeading']))
    for f in raw_failures:
        card = []
        h_tbl = Table([[
            Paragraph(f"<b>CASE #{f['id']}: {f['title'].upper()}</b>", styles['CardHeaderTitle']),
            Paragraph(f"DOMAIN: <b>{f['domain']}</b>", ParagraphStyle('HdrDom', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.white, alignment=2))
        ]], colWidths=[pw * 0.75, pw * 0.25])
        h_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), HEADER_BG),
            ('PADDING', (0,0), (-1,-1), 3),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        card.append(h_tbl)

        content = [
            [Paragraph("<b>Observed Error Symptom:</b>", ParagraphStyle('ELbl', fontName='Helvetica-Bold', fontSize=7.2, leading=9.2, textColor=ACCENT)),
             Paragraph(html.escape(f['symptom']), styles['CardTextError'])],
            [Paragraph("<b>Root Cause / Failure Reason:</b>", ParagraphStyle('RLbl', fontName='Helvetica-Bold', fontSize=7.2, leading=9.2, textColor=PRIMARY)),
             Paragraph(html.escape(f['cause']), styles['CardTextReason'])],
            [Paragraph("<b>Applied Engineering Solution:</b>", ParagraphStyle('FLbl', fontName='Helvetica-Bold', fontSize=7.2, leading=9.2, textColor=ACCENT_GREEN)),
             Paragraph(html.escape(f['fix']), styles['CardTextFix'])],
        ]
        c_tbl = Table(content, colWidths=[pw * 0.28, pw * 0.72])
        c_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), ERROR_BG),
            ('BACKGROUND', (0,1), (-1,1), colors.white),
            ('BACKGROUND', (0,2), (-1,2), FIX_BG),
            ('BOX', (0,0), (-1,-1), 0.8, BORDER_COLOR),
            ('INNERGRID', (0,0), (-1,-1), 0.4, DIVIDER_COLOR),
            ('PADDING', (0,0), (-1,-1), 3.5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        card.append(c_tbl)
        card.append(Spacer(1, 5))
        story.append(KeepTogether(card))

    # =========================================================================
    # CHAPTER 6: CONCLUSION & VERIFICATION
    # =========================================================================
    story.append(Spacer(1, 4))
    story.append(Paragraph("7. Project Conclusion & Verification Summary", styles['ChapterHeading']))
    conclusion_text = (
        "<b>Conclusion:</b> The AgileX Scout Mini 4WD AMR simulation project successfully demonstrates the end-to-end "
        "integration of mechanical CAD design, kinematic calibration, Gazebo Harmonic physics co-simulation, and autonomous navigation "
        "under ROS 2 Jazzy Jalisco. Key engineering milestones achieved include:<br/>"
        "&bull; <b>100% REP-103 Kinematic Compliance:</b> Fully resolved coordinate frame orientations and continuous wheel joints.<br/>"
        "&bull; <b>Drift-Free Sensor Fusion:</b> Eliminated 120&deg; rotational odometry drift via 2D Extended Kalman Filtering.<br/>"
        "&bull; <b>Dual-Environment Validation:</b> Stable autonomous navigation verified across both the 10m &times; 10m obstacle arena and the 20m &times; 16m Civil Architectural Multi-Room Facility.<br/>"
        "&bull; <b>Multi-Station Autonomy:</b> Fully automated inspection patrol missions successfully executed with real-time waypoint feedback and dynamic obstacle evasion.<br/>"
        "&bull; <b>Zero-Defect Troubleshooting:</b> All 22 system anomalies systematically documented, diagnosed, and permanently resolved."
    )
    story.append(Paragraph(conclusion_text, styles['CalloutBox']))
    story.append(Spacer(1, 8))

    story.append(Paragraph("8. References & Code Repository", styles['ChapterHeading']))
    refs = [
        "<b>GitHub Project Repository:</b> <font color='#0369A1'><u>https://github.com/Saibts/AgileX_ScoutMini_JAZZY</u></font>",
        "<b>ROS 2 Documentation (Jazzy Jalisco):</b> https://docs.ros.org/en/jazzy/",
        "<b>Gazebo Harmonic Simulation (gz-sim8):</b> https://gazebosim.org/docs/harmonic/",
        "<b>ROS 2 Navigation Stack (Nav2):</b> https://navigation.ros.org/",
        "<b>SLAM Toolbox (2D Lifelong Mapping):</b> https://github.com/SteveMacenski/slam_toolbox",
        "<b>Robot Localization Package (EKF Sensor Fusion):</b> http://docs.ros.org/en/jazzy/p/robot_localization/",
        "<b>REP-105 Coordinate Frames for Mobile Platforms:</b> https://www.ros.org/reps/rep-0105.html",
        "<b>REP-103 Standard Units and Coordinate Conventions:</b> https://www.ros.org/reps/rep-0103.html"
    ]
    for r in refs:
        story.append(Paragraph(f"&bull;&nbsp;&nbsp;{r}", ParagraphStyle('RefP', fontName='Times-Roman', fontSize=8.5, leading=12, textColor=DARK_TEXT, leftIndent=10, spaceAfter=2)))

    print(f"Building Final Comprehensive Master Report PDF: {OUTPUT_PDF}...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Success! Master Report PDF built ({OUTPUT_PDF.stat().st_size} bytes).")

    # Update user's downloaded PDF in /home/sailakshmi/Downloads/ROS_PROJECT_REPORT_SAILAKSHMI.pdf
    downloads_pdf = Path("/home/sailakshmi/Downloads/ROS_PROJECT_REPORT_SAILAKSHMI.pdf")
    try:
        shutil.copy2(OUTPUT_PDF, downloads_pdf)
        print(f"Successfully updated user downloaded PDF at: {downloads_pdf} ({downloads_pdf.stat().st_size} bytes)")
    except Exception as e:
        print(f"Warning copying to Downloads: {e}")


if __name__ == '__main__':
    build_pdf()
