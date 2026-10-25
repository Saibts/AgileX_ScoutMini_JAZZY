#!/usr/bin/env python3
"""
Publication-Quality Academic PDF Report Generator for Civil Architectural Mapping
AgileX Scout Mini 4WD Autonomous Mobile Robot (ROS 2 Jazzy & Gazebo Harmonic)
Student: Sailakshmi BT (Reg: 2024511019)
Department of Production Technology, MIT Campus, Anna University, Chennai
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# ==============================================================================
# COLOR PALETTE (Academic Deep Navy & Professional Slate)
# ==============================================================================
COLOR_PRIMARY = colors.HexColor('#0B2545')      # Deep Navy
COLOR_SECONDARY = colors.HexColor('#134074')    # Medium Navy / Slate Blue
COLOR_ACCENT = colors.HexColor('#118AB2')       # Teal Cyan
COLOR_DARK_TEXT = colors.HexColor('#1D2A44')    # Charcoal
COLOR_LIGHT_BG = colors.HexColor('#F4F7FA')     # Off-white / Cool Grey
COLOR_BORDER = colors.HexColor('#D1D5DB')       # Light Border Grey
COLOR_MUTED = colors.HexColor('#64748B')        # Slate Grey
COLOR_SUCCESS = colors.HexColor('#0F766E')      # Dark Teal Success

PAGE_WIDTH, PAGE_HEIGHT = A4  # 595.27 x 841.89 pt


# ==============================================================================
# TWO-PASS NUMBERED CANVAS (Running Headers, Footers, Page Borders & Total Count)
# ==============================================================================
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

    def draw_page_decorations(self, total_pages):
        self.saveState()

        # 1. Double Page Border
        self.setStrokeColor(COLOR_PRIMARY)
        self.setLineWidth(1.2)
        self.rect(20, 20, PAGE_WIDTH - 40, PAGE_HEIGHT - 40)
        self.setLineWidth(0.4)
        self.rect(23, 23, PAGE_WIDTH - 46, PAGE_HEIGHT - 46)

        # 2. Running Header (Pages 2+)
        if self._pageNumber > 1:
            self.setFont('Helvetica-Bold', 7.5)
            self.setFillColor(COLOR_SECONDARY)
            self.drawString(36, PAGE_HEIGHT - 32, "AGILEX SCOUT MINI AMR — CIVIL ARCHITECTURAL MAPPING & AUTONOMOUS NAVIGATION")
            self.setFont('Helvetica', 7.5)
            self.setFillColor(COLOR_MUTED)
            self.drawRightString(PAGE_WIDTH - 36, PAGE_HEIGHT - 32, "ROS 2 JAZZY & GAZEBO HARMONIC")

            self.setStrokeColor(COLOR_BORDER)
            self.setLineWidth(0.5)
            self.line(36, PAGE_HEIGHT - 35, PAGE_WIDTH - 36, PAGE_HEIGHT - 35)

        # 3. Running Footer (All Pages)
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 33, PAGE_WIDTH - 36, 33)

        self.setFont('Helvetica', 7.5)
        self.setFillColor(COLOR_MUTED)
        self.drawString(36, 23, "Anna University (MIT Campus)")
        self.drawCentredString(PAGE_WIDTH / 2.0, 23, "Student: Sailakshmi BT (Reg: 2024511019)")
        self.drawRightString(PAGE_WIDTH - 36, 23, f"Page {self._pageNumber} of {total_pages}")

        self.restoreState()


# ==============================================================================
# REPORT BUILDER FUNCTION
# ==============================================================================
def build_pdf(output_pdf_path):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_univ_style = ParagraphStyle(
        'UnivHeader',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        alignment=1,
        textColor=COLOR_PRIMARY
    )

    title_doc_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        alignment=1,
        textColor=COLOR_PRIMARY,
        spaceBefore=6,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=COLOR_SECONDARY,
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'Header1',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=COLOR_PRIMARY,
        spaceBefore=12,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        fontName='Helvetica-Bold',
        fontSize=10.2,
        leading=13,
        textColor=COLOR_SECONDARY,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        fontName='Times-Roman',
        fontSize=9.2,
        leading=12.6,
        textColor=COLOR_DARK_TEXT,
        alignment=4,  # Justified
        spaceBefore=0,
        spaceAfter=4
    )

    body_bold = ParagraphStyle(
        'BodyBoldCustom',
        parent=body_style,
        fontName='Times-Bold'
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=14,
        bulletIndent=5,
        spaceAfter=2
    )

    caption_style = ParagraphStyle(
        'FigCaption',
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10.5,
        alignment=1,
        textColor=COLOR_MUTED,
        spaceBefore=3,
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        fontName='Courier',
        fontSize=7.5,
        leading=9.8,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=0,
        spaceAfter=0
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=10.5,
        alignment=1,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        fontName='Times-Roman',
        fontSize=8.0,
        leading=10.2,
        textColor=COLOR_DARK_TEXT
    )

    table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=table_cell_style,
        alignment=1
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        fontName='Times-Roman',
        fontSize=8.8,
        leading=12.0,
        textColor=colors.HexColor('#0C4A6E')
    )

    story = []

    # --------------------------------------------------------------------------
    # COVER / HEADER BLOCK
    # --------------------------------------------------------------------------
    logo_path = "/home/sailakshmi/215-2155967_transparent-university-icon-png-anna-university-chennai-logo.png"
    if os.path.exists(logo_path):
        img = RLImage(logo_path, width=48, height=48)
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1, 4))

    story.append(Paragraph("ANNA UNIVERSITY, CHENNAI — 600 025", title_univ_style))
    story.append(Paragraph("DEPARTMENT OF PRODUCTION TECHNOLOGY — MIT CAMPUS", ParagraphStyle(
        'SubDept', fontName='Helvetica-Bold', fontSize=9.5, leading=12, alignment=1, textColor=COLOR_SECONDARY
    )))
    story.append(Spacer(1, 4))

    story.append(Paragraph("TECHNICAL DOCUMENTATION REPORT", title_doc_style))
    story.append(Paragraph(
        "<b>Civil Architectural Mapping, Simulation Environment & Nav2 Autonomous Navigation</b><br/>"
        "Platform: AgileX Scout Mini 4WD AMR (ROS 2 Jazzy Jalisco & Gazebo Harmonic)",
        subtitle_style
    ))

    # Student & Project Metadata Box
    meta_data = [
        [
            Paragraph("<b>Student Name:</b>", table_cell_style), Paragraph("Sailakshmi B T", table_cell_style),
            Paragraph("<b>Project Code:</b>", table_cell_style), Paragraph("RA23C02 / AMR-2026", table_cell_style)
        ],
        [
            Paragraph("<b>Register Number:</b>", table_cell_style), Paragraph("2024511019", table_cell_style),
            Paragraph("<b>ROS Distribution:</b>", table_cell_style), Paragraph("ROS 2 Jazzy Jalisco", table_cell_style)
        ],
        [
            Paragraph("<b>Department:</b>", table_cell_style), Paragraph("Production Technology (Robotics)", table_cell_style),
            Paragraph("<b>Simulation Engine:</b>", table_cell_style), Paragraph("Gazebo Harmonic (Gz Sim 8.9)", table_cell_style)
        ],
        [
            Paragraph("<b>Robot Model:</b>", table_cell_style), Paragraph("AgileX Scout Mini 4WD Skid-Steer", table_cell_style),
            Paragraph("<b>Perception Suite:</b>", table_cell_style), Paragraph("2D LiDAR + IMU + RGB-D Camera", table_cell_style)
        ],
    ]
    meta_table = Table(meta_data, colWidths=[90, 165, 95, 173])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.8, COLOR_PRIMARY),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # --------------------------------------------------------------------------
    # SECTION 1: EXECUTIVE SUMMARY & ARCHITECTURAL SCOPE
    # --------------------------------------------------------------------------
    story.append(Paragraph("1. Executive Summary & Design Scope", h1_style))
    story.append(Paragraph(
        "Autonomous Mobile Robots (AMRs) deployed in industrial warehousing, structural health inspection, and civil facility "
        "patrol require spatial environments that closely model realistic civil architectural geometries. The standard synthetic "
        "test arena (10m &times; 10m enclosure with arbitrary pillars) lacks the structural features needed to evaluate complex "
        "multi-room path planning. This engineering milestone transitions the <b>AgileX Scout Mini AMR</b> simulation into a "
        "full-scale <b>Civil & Structural Engineering Research Facility</b> measuring <b>20.0 m &times; 16.0 m</b> (total footprint 320 m<sup>2</sup>).",
        body_style
    ))
    story.append(Paragraph(
        "The environment incorporates reinforced concrete (RCC) column grids, standard 1.2 m commercial doorways, a central "
        "arterial corridor, and multi-departmental zones. Simultaneously, interconnecting room doorways establish an internal "
        "circulation loop (maze-like topology) that tests ROS 2 Nav2 global replanning, AMCL particle filter localization, and "
        "DWB dynamic obstacle avoidance when primary corridor thoroughfares are obstructed.",
        body_style
    ))

    # Callout Box: Design Reference
    callout_data = [[Paragraph(
        "<b>Reference Standard:</b> Engineered according to the <b>NIST Standard Test Facility for Mobile Robots (NIST SP 1083 / ASTM E2521)</b> "
        "and architectural floor plan guidelines. Features full backward compatibility with the existing AgileX Scout Mini ROS 2 stack.",
        callout_style
    )]]
    callout_table = Table(callout_data, colWidths=[523])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F9FF')),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_ACCENT),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 6))

    # --------------------------------------------------------------------------
    # SECTION 2: ARCHITECTURAL SPATIAL GEOMETRY & ZONING
    # --------------------------------------------------------------------------
    story.append(Paragraph("2. Architectural Spatial Layout & Dimensional Specifications", h1_style))
    story.append(Paragraph(
        "The structural layout divides the 320 m<sup>2</sup> civil facility into 7 functional zones interconnected by a 2.4 m "
        "arterial thoroughfare and specialized doorways. Dimensions conform strictly to commercial and industrial building standards:",
        body_style
    ))

    facility_specs = [
        [Paragraph("Architectural Feature", table_header_style), Paragraph("Coordinates / Bounds", table_header_style), Paragraph("Dimensions (L &times; W &times; H)", table_header_style), Paragraph("Engineering Rationale", table_header_style)],
        [Paragraph("Outer Perimeter Walls", table_cell_style), Paragraph("X: [-10, 10], Y: [-8, 8]", table_cell_style), Paragraph("20.0 m &times; 16.0 m &times; 1.2 m", table_cell_style), Paragraph("Heavy structural boundary with 0.2m CMU thickness.", table_cell_style)],
        [Paragraph("Central Arterial Corridor", table_cell_style), Paragraph("X: [-10, 10], Y: [-1.2, 1.2]", table_cell_style), Paragraph("20.0 m &times; 2.4 m &times; 1.2 m", table_cell_style), Paragraph("ADA-compliant wide hallway for bidirectional AMR transit.", table_cell_style)],
        [Paragraph("Entrance Foyer & Atrium", table_cell_style), Paragraph("X: [-2.5, 2.5], Y: [-8, -1.2]", table_cell_style), Paragraph("5.0 m &times; 6.8 m &times; 1.2 m", table_cell_style), Paragraph("4.0m open archway to corridor; AMR Home Docking Base.", table_cell_style)],
        [Paragraph("Materials & Concrete Lab", table_cell_style), Paragraph("X: [-10, -2.5], Y: [1.2, 8]", table_cell_style), Paragraph("7.5 m &times; 6.8 m &times; 1.2 m", table_cell_style), Paragraph("Concrete compression specimen test bay & workbenches.", table_cell_style)],
        [Paragraph("Civil Conference Hall", table_cell_style), Paragraph("X: [-2.5, 2.5], Y: [1.2, 8]", table_cell_style), Paragraph("5.0 m &times; 6.8 m &times; 1.2 m", table_cell_style), Paragraph("Seminar room with 2.4m &times; 1.2m central table.", table_cell_style)],
        [Paragraph("BIM, CAD & Robotics Studio", table_cell_style), Paragraph("X: [2.5, 10], Y: [1.2, 8]", table_cell_style), Paragraph("7.5 m &times; 6.8 m &times; 1.2 m", table_cell_style), Paragraph("Digital twin workstation island & rapid prototyping rig.", table_cell_style)],
        [Paragraph("Archives & Equipment Vault", table_cell_style), Paragraph("X: [2.5, 10], Y: [-8, -1.2]", table_cell_style), Paragraph("7.5 m &times; 6.8 m &times; 1.2 m", table_cell_style), Paragraph("Heavy-duty surveying instrument & document racks.", table_cell_style)],
        [Paragraph("Geotechnical Survey Lab", table_cell_style), Paragraph("X: [-10, -2.5], Y: [-8, -1.2]", table_cell_style), Paragraph("7.5 m &times; 6.8 m &times; 1.2 m", table_cell_style), Paragraph("Soil mechanics testing bench & core sample press.", table_cell_style)],
        [Paragraph("Structural RCC Columns", table_cell_style), Paragraph("Grid: X=&plusmn;6m, Y=&plusmn;4.6m", table_cell_style), Paragraph("0.45 m &times; 0.45 m &times; 1.2 m", table_cell_style), Paragraph("Reinforced columns serving as natural LiDAR landmarks.", table_cell_style)],
        [Paragraph("Corridor Columns (Cylindrical)", table_cell_style), Paragraph("X = -4.0 m, +4.0 m, Y = 0", table_cell_style), Paragraph("&empty; 0.50 m &times; 1.2 m height", table_cell_style), Paragraph("Chicane obstacles testing local path deviation.", table_cell_style)],
        [Paragraph("Doorways & Portals", table_cell_style), Paragraph("Room Entrance Portals", table_cell_style), Paragraph("Width: 1.2 m - 1.4 m clear", table_cell_style), Paragraph("Scout Mini (0.612m width) clears with >0.29m safety margin.", table_cell_style)],
    ]
    fac_table = Table(facility_specs, colWidths=[105, 110, 118, 190])
    fac_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('BOX', (0, 0), (-1, -1), 0.8, COLOR_PRIMARY),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(fac_table)
    story.append(Spacer(1, 6))

    # Blueprint Image Flowable
    blueprint_img_path = "/home/sailakshmi/agilex/docs/images/civil_blueprint.png"
    if os.path.exists(blueprint_img_path):
        bp_img = RLImage(blueprint_img_path, width=470, height=250)
        bp_img.hAlign = 'CENTER'
        story.append(bp_img)
        story.append(Paragraph("Figure 1: Architectural Civil Engineering Blueprint showing 7 Zoned Departments, 2.4m Arterial Corridor, Structural RCC Column Grid, and Nav2 Waypoint Inspection Stations (#1 to #7).", caption_style))
        story.append(Spacer(1, 4))

    # Waypoint Topology Table to complete Page 2
    wp_summary_data = [
        [Paragraph("Waypoint ID", table_header_style), Paragraph("Facility Location", table_header_style), Paragraph("Coordinates (X, Y)", table_header_style), Paragraph("Heading & Inspection Activity", table_header_style)],
        [Paragraph("<b>WP 1</b>", table_cell_style), Paragraph("Main Entrance Foyer & Atrium", table_cell_style), Paragraph("(0.00, &minus;3.80) m", table_cell_center), Paragraph("Yaw 90&deg; (+Y) &bull; AMR Base Docking & Charging Port", table_cell_style)],
        [Paragraph("<b>WP 2</b>", table_cell_style), Paragraph("Central Arterial Corridor Hub", table_cell_style), Paragraph("(0.00, 0.00) m", table_cell_center), Paragraph("Yaw 0&deg; (+X) &bull; Main 2.4m Thoroughfare Intersection", table_cell_style)],
        [Paragraph("<b>WP 3</b>", table_cell_style), Paragraph("Structural Materials Testing Lab", table_cell_style), Paragraph("(&minus;7.00, 3.50) m", table_cell_center), Paragraph("Yaw 90&deg; (+Y) &bull; Compression Testing & Workbenches", table_cell_style)],
        [Paragraph("<b>WP 4</b>", table_cell_style), Paragraph("Civil Seminar & Conference Hall", table_cell_style), Paragraph("(0.00, 3.00) m", table_cell_center), Paragraph("Yaw 90&deg; (+Y) &bull; Central Presentation & Meeting Area", table_cell_style)],
        [Paragraph("<b>WP 5</b>", table_cell_style), Paragraph("BIM, CAD & Robotics Computing Studio", table_cell_style), Paragraph("(7.00, 3.50) m", table_cell_center), Paragraph("Yaw 90&deg; (+Y) &bull; Structural Analysis & Prototyping Rig", table_cell_style)],
        [Paragraph("<b>WP 6</b>", table_cell_style), Paragraph("Department Archives & Storage Vault", table_cell_style), Paragraph("(4.50, &minus;4.80) m", table_cell_center), Paragraph("Yaw 0&deg; (+X) &bull; Surveying Equipment & Blueprint Storage", table_cell_style)],
        [Paragraph("<b>WP 7</b>", table_cell_style), Paragraph("Geotechnical Survey & Soil Mechanics Lab", table_cell_style), Paragraph("(&minus;4.50, &minus;5.00) m", table_cell_center), Paragraph("Yaw 180&deg; (&minus;X) &bull; Soil Core Sampling Rig & Shear Bay", table_cell_style)],
    ]
    wp_sum_table = Table(wp_summary_data, colWidths=[70, 145, 95, 213])
    wp_sum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_SECONDARY),
        ('BOX', (0, 0), (-1, -1), 0.8, COLOR_SECONDARY),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(wp_sum_table)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # SECTION 3: MATHEMATICAL MAPPING PIPELINE & TRINARY ENCODING
    # --------------------------------------------------------------------------
    story.append(Paragraph("3. Mathematical Mapping Pipeline & Generator Logic", h1_style))
    story.append(Paragraph(
        "To achieve millimetric synchronization between physical Gazebo collision boxes and the Nav2 static costmap layer, "
        "the 2D occupancy grid was generated via mathematical coordinate transformations using "
        "<b>src/assem2_robot/scripts/generate_civil_world.py</b>.",
        body_style
    ))

    story.append(Paragraph("3.1 Continuous-to-Discrete Transformation Formulation", h2_style))
    story.append(Paragraph(
        "The physical simulation bounds encompass <i>X</i> &isin; [&minus;11.0, 11.0] m (span 22.0 m) and <i>Y</i> &isin; [&minus;9.0, 9.0] m "
        "(span 18.0 m) to ensure exterior safety margins around the outer structural perimeter walls. With a grid resolution of "
        "&Delta; = 0.05 m/pixel (5 cm/pixel), the bitmap resolution is computed as:",
        body_style
    ))

    # Formula Box
    formula_text = [
        [Paragraph(
            "<b>Width:</b> <i>W</i><sub>px</sub> = (<i>X</i><sub>max</sub> &minus; <i>X</i><sub>min</sub>) / &Delta; = (11.0 &minus; (&minus;11.0)) / 0.05 = <b>440 pixels</b><br/>"
            "<b>Height:</b> <i>H</i><sub>px</sub> = (<i>Y</i><sub>max</sub> &minus; <i>Y</i><sub>min</sub>) / &Delta; = (9.0 &minus; (&minus;9.0)) / 0.05 = <b>360 pixels</b><br/>"
            "<b>Map Origin:</b> [<i>X</i><sub>0</sub>, <i>Y</i><sub>0</sub>, <i>Z</i><sub>0</sub>] = [<b>&minus;11.000, &minus;9.000, 0.000</b>] m<br/>"
            "<b>Continuous-to-Discrete Projection:</b><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<i>u</i> = round((<i>x</i><sub>w</sub> &minus; <i>X</i><sub>0</sub>) / &Delta;), &nbsp;&nbsp;&nbsp;&nbsp;<i>v</i> = round((<i>y</i><sub>w</sub> &minus; <i>Y</i><sub>0</sub>) / &Delta;)<br/>"
            "<b>Image Matrix Coordinate (Row 0 at Top):</b><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Row = (<i>H</i><sub>px</sub> &minus; 1) &minus; <i>v</i>, &nbsp;&nbsp;&nbsp;&nbsp;Col = <i>u</i>",
            code_style
        )]
    ]
    formula_table = Table(formula_text, colWidths=[523])
    formula_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.8, COLOR_SECONDARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(formula_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("3.2 Trinary Occupancy State Representation", h2_style))
    story.append(Paragraph(
        "The generated 2D grid conforms strictly to ROS 2 standard occupancy specifications (<code>nav_msgs/msg/OccupancyGrid</code>):",
        body_style
    ))
    story.append(Paragraph("&bull; <b>Free Navigable Space (Pixel Value 254):</b> Represents open corridors and room floors with 0% obstacle probability.", bullet_style))
    story.append(Paragraph("&bull; <b>Occupied Structural Obstacles (Pixel Value 0):</b> Represents perimeter walls, interior partitions, RCC columns, and fixed equipment.", bullet_style))
    story.append(Paragraph("&bull; <b>Unknown Unexplored Space (Pixel Value 205):</b> Represents regions outside the building perimeter (&gt; 10 m).", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("3.3 Metadata Specification (civil_map.yaml)", h2_style))

    yaml_box = [[Paragraph(
        "image: civil_map.pgm<br/>"
        "mode: trinary<br/>"
        "resolution: 0.0500<br/>"
        "origin: [-11.000, -9.000, 0.000000]<br/>"
        "negate: 0<br/>"
        "occupied_thresh: 0.65<br/>"
        "free_thresh: 0.25",
        code_style
    )]]
    y_table = Table(yaml_box, colWidths=[523])
    y_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.6, COLOR_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(y_table)
    story.append(Spacer(1, 6))

    # --------------------------------------------------------------------------
    # SECTION 4: GAZEBO HARMONIC 3D PHYSICAL SIMULATION
    # --------------------------------------------------------------------------
    story.append(Paragraph("4. Gazebo Harmonic 3D Physical Simulation (civil_world.sdf)", h1_style))
    story.append(Paragraph(
        "The 3D physical world was authored in SDFormat 1.8 inside <b>src/assem2_robot/worlds/civil_world.sdf</b>. "
        "It integrates Gazebo Harmonic physics stepping, rendering plugins, and direct URDF model spawning.",
        body_style
    ))

    gz_plugins_data = [
        [Paragraph("Gazebo Harmonic System Plugin", table_header_style), Paragraph("C++ Class / Shared Object", table_header_style), Paragraph("Functional Role in Simulation", table_header_style)],
        [Paragraph("Physics System", table_cell_style), Paragraph("gz::sim::systems::Physics", table_cell_style), Paragraph("Computes rigid-body dynamics with 5ms step size and real-time factor 1.0.", table_cell_style)],
        [Paragraph("User Commands", table_cell_style), Paragraph("gz::sim::systems::UserCommands", table_cell_style), Paragraph("Handles interactive GUI controls, model dragging, and spawn events.", table_cell_style)],
        [Paragraph("Scene Broadcaster", table_cell_style), Paragraph("gz::sim::systems::SceneBroadcaster", table_cell_style), Paragraph("Broadcasts entity state poses and visual geometry to the GUI client.", table_cell_style)],
        [Paragraph("Sensors System", table_cell_style), Paragraph("gz::sim::systems::Sensors", table_cell_style), Paragraph("Executes Ogre2 rendering pipeline for 2D LiDAR rays and RGB-D depth clouds.", table_cell_style)],
        [Paragraph("IMU System", table_cell_style), Paragraph("gz::sim::systems::Imu", table_cell_style), Paragraph("Calculates 100 Hz angular velocities and linear accelerations with Gaussian noise.", table_cell_style)],
    ]
    gz_table = Table(gz_plugins_data, colWidths=[120, 150, 253])
    gz_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_SECONDARY),
        ('BOX', (0, 0), (-1, -1), 0.8, COLOR_SECONDARY),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(gz_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1 Robot Model Inclusion & Spawn Calibration", h2_style))
    story.append(Paragraph(
        "The AgileX Scout Mini AMR URDF (<b>urdf/Assem2.SLDASM.urdf</b>) is embedded directly into <b>civil_world.sdf</b>:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<code>&lt;include&gt;&lt;uri&gt;package://assem2_robot/urdf/Assem2.SLDASM.urdf&lt;/uri&gt;"
        "&lt;pose&gt;0 0 0.02 0 0 0&lt;/pose&gt;&lt;/include&gt;</code><br/>"
        "Spawning the robot at <b>(0.0, 0.0, 0.02, yaw=0.0)</b> positions it directly at the Central Arterial Corridor Hub. "
        "This perfectly matches the Nav2 AMCL initial pose configuration, ensuring instant particle convergence without manual pose setting in RViz.",
        body_style
    ))

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # SECTION 5: ROS 2 NAV2 AUTONOMOUS NAVIGATION STACK
    # --------------------------------------------------------------------------
    story.append(Paragraph("5. ROS 2 Nav2 Navigation Stack Architecture & Tuning", h1_style))
    story.append(Paragraph(
        "The autonomous navigation system utilizes the industry-standard <b>Nav2 (Navigation 2)</b> stack running on ROS 2 Jazzy. "
        "It integrates global path planning, local reactive trajectory control, and probabilistic localization.",
        body_style
    ))

    # TF Tree Flowable
    tf_data = [
        [Paragraph("Coordinate Frame", table_header_style), Paragraph("Parent Frame", table_header_style), Paragraph("Broadcaster Node", table_header_style), Paragraph("Function & Calibration", table_header_style)],
        [Paragraph("map", table_cell_style), Paragraph("— (Root Frame)", table_cell_style), Paragraph("nav2_amcl", table_cell_style), Paragraph("Global earth-fixed map frame referencing the 2D occupancy grid.", table_cell_style)],
        [Paragraph("odom", table_cell_style), Paragraph("map", table_cell_style), Paragraph("robot_localization", table_cell_style), Paragraph("Smooth continuous odometry frame fused by Extended Kalman Filter.", table_cell_style)],
        [Paragraph("base_footprint", table_cell_style), Paragraph("odom", table_cell_style), Paragraph("robot_localization", table_cell_style), Paragraph("2D planar projection of chassis on the ground plane (Z=0).", table_cell_style)],
        [Paragraph("base_link", table_cell_style), Paragraph("base_footprint", table_cell_style), Paragraph("robot_state_publisher", table_cell_style), Paragraph("Chassis center calibrated with RPY (0, 0, &minus;90&deg;) for REP-103 alignment.", table_cell_style)],
        [Paragraph("lidar_link", table_cell_style), Paragraph("base_link", table_cell_style), Paragraph("robot_state_publisher", table_cell_style), Paragraph("Mounted on upper deck (Z=0.36m); broadcasts 360&deg; laser scan points.", table_cell_style)],
        [Paragraph("imu_link", table_cell_style), Paragraph("base_link", table_cell_style), Paragraph("robot_state_publisher", table_cell_style), Paragraph("Internal 6-axis IMU providing orientation & angular velocities.", table_cell_style)],
        [Paragraph("camera_optical_frame", table_cell_style), Paragraph("camera_link", table_cell_style), Paragraph("robot_state_publisher", table_cell_style), Paragraph("Front bumper RGB-D camera optical frame for depth cloud projection.", table_cell_style)],
    ]
    tf_table = Table(tf_data, colWidths=[90, 80, 110, 243])
    tf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('BOX', (0, 0), (-1, -1), 0.8, COLOR_PRIMARY),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tf_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("5.1 Nav2 Algorithmic Parameters & Tuning", h2_style))
    story.append(Paragraph(
        "Parameters configured in <b>src/assem2_robot/config/nav2_params.yaml</b> ensure smooth traversal through doorways and corridors:",
        body_style
    ))
    story.append(Paragraph("&bull; <b>AMCL Particle Filter:</b> Differential motion model (&alpha;<sub>1..4</sub> = 0.2) accommodating 4WD skid-steer wheel slip. Particle count dynamically varies between 500 (steady-state tracking) and 2000 (recovery mode).", bullet_style))
    story.append(Paragraph("&bull; <b>Global Costmap Inflation:</b> Set to inflation radius <i>r</i><sub>inf</sub> = 0.55 m with cost scaling factor 3.0. This prevents the robot from clipping doorway frame corners while maintaining navigable corridors.", bullet_style))
    story.append(Paragraph("&bull; <b>Global Path Planner (NavFn):</b> Uses Dijkstra's wavefront expansion algorithm to compute the shortest collision-free path across hallway networks.", bullet_style))
    story.append(Paragraph("&bull; <b>Local Controller (DWBLocalPlanner):</b> Computes candidate trajectory arcs evaluating PathAlign (weight: 32.0), GoalAlign (weight: 24.0), and BaseObstacle (weight: 0.02) to produce skid-steer twist commands on <code>/cmd_vel</code>.", bullet_style))

    story.append(Spacer(1, 6))

    # --------------------------------------------------------------------------
    # SECTION 6: AUTONOMOUS MULTI-ROOM PATROL MISSION
    # --------------------------------------------------------------------------
    story.append(Paragraph("6. Autonomous Multi-Room Patrol Mission (civil_patrol_mission.py)", h1_style))
    story.append(Paragraph(
        "The automated mission executor at <b>src/assem2_robot/scripts/civil_patrol_mission.py</b> uses the ROS 2 "
        "<code>nav2_simple_commander.robot_navigator.BasicNavigator</code> API to sequentially navigate through all 7 civil zones:",
        body_style
    ))

    patrol_stations_data = [
        [Paragraph("Station ID & Name", table_header_style), Paragraph("Target (X, Y)", table_header_style), Paragraph("Heading (Yaw)", table_header_style), Paragraph("Dwell", table_header_style), Paragraph("Inspection Activity Description", table_header_style)],
        [Paragraph("<b>Station 1:</b> Main Entrance Foyer", table_cell_style), Paragraph("(0.00, -3.80)", table_cell_center), Paragraph("90.0&deg; (+Y)", table_cell_center), Paragraph("3.0 s", table_cell_center), Paragraph("AMR Staging Dock; greets visitors at reception atrium.", table_cell_style)],
        [Paragraph("<b>Station 2:</b> Central Corridor Hub", table_cell_style), Paragraph("(0.00, 0.00)", table_cell_center), Paragraph("0.0&deg; (+X)", table_cell_center), Paragraph("2.0 s", table_cell_center), Paragraph("2.4m Main Building Arterial Corridor traffic inspection.", table_cell_style)],
        [Paragraph("<b>Station 3:</b> Structural Materials Lab", table_cell_style), Paragraph("(-7.00, 3.50)", table_cell_center), Paragraph("90.0&deg; (+Y)", table_cell_center), Paragraph("4.0 s", table_cell_center), Paragraph("Concrete compression specimen test bay monitoring.", table_cell_style)],
        [Paragraph("<b>Station 4:</b> Civil Conference Hall", table_cell_style), Paragraph("(0.00, 3.00)", table_cell_center), Paragraph("90.0&deg; (+Y)", table_cell_center), Paragraph("3.0 s", table_cell_center), Paragraph("Central meeting hall & presentation zone inspection.", table_cell_style)],
        [Paragraph("<b>Station 5:</b> CAD & Robotics Studio", table_cell_style), Paragraph("(7.00, 3.50)", table_cell_center), Paragraph("90.0&deg; (+Y)", table_cell_center), Paragraph("4.0 s", table_cell_center), Paragraph("Digital twin workstation & structural simulation bay.", table_cell_style)],
        [Paragraph("<b>Station 6:</b> Archives & Storage Vault", table_cell_style), Paragraph("(4.50, -4.80)", table_cell_center), Paragraph("0.0&deg; (+X)", table_cell_center), Paragraph("3.0 s", table_cell_center), Paragraph("Document archives & surveying instrument inventory check.", table_cell_style)],
        [Paragraph("<b>Station 7:</b> Geotechnical Survey Lab", table_cell_style), Paragraph("(-4.50, -5.00)", table_cell_center), Paragraph("180.0&deg; (-X)", table_cell_center), Paragraph("4.0 s", table_cell_center), Paragraph("Soil mechanics shear testing rig & core sample inspection.", table_cell_style)],
    ]
    p_table = Table(patrol_stations_data, colWidths=[130, 75, 65, 45, 208])
    p_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('BOX', (0, 0), (-1, -1), 0.8, COLOR_PRIMARY),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(p_table)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # SECTION 7: LAUNCH ARCHITECTURE & FILE SEPARATION
    # --------------------------------------------------------------------------
    story.append(Paragraph("7. Launch Architecture & File Separation", h1_style))
    story.append(Paragraph(
        "To ensure complete system stability, the launch configuration has been separated into dedicated launch descriptions. "
        "The original simulation is preserved unaltered, while the new civil environment runs through its own launcher:",
        body_style
    ))

    launch_data = [
        [Paragraph("Launch File", table_header_style), Paragraph("Relative Workspace Path", table_header_style), Paragraph("Target World & Map", table_header_style), Paragraph("Operational Role", table_header_style)],
        [Paragraph("<b>Normal Simulation</b>", table_cell_style), Paragraph("src/assem2_robot/launch/simulation.launch.py", table_cell_style), Paragraph("amr_world.sdf<br/>amr_world_map.yaml", table_cell_style), Paragraph("Original 10m &times; 10m obstacle arena for baseline kinematics and EKF verification.", table_cell_style)],
        [Paragraph("<b>Normal Backup</b>", table_cell_style), Paragraph("src/assem2_robot/launch/simulation.launch.py.backup", table_cell_style), Paragraph("amr_world.sdf<br/>amr_world_map.yaml", table_cell_style), Paragraph("Exact byte-for-byte backup of the verified normal simulation launcher.", table_cell_style)],
        [Paragraph("<b>Civil Simulation</b>", table_cell_style), Paragraph("src/assem2_robot/launch/civil_simulation.launch.py", table_cell_style), Paragraph("civil_world.sdf<br/>civil_map.yaml", table_cell_style), Paragraph("New 20m &times; 16m Civil Architectural Facility with Nav2 multi-room navigation.", table_cell_style)],
    ]
    l_table = Table(launch_data, colWidths=[100, 150, 110, 163])
    l_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_SECONDARY),
        ('BOX', (0, 0), (-1, -1), 0.8, COLOR_SECONDARY),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(l_table)
    story.append(Spacer(1, 8))

    # --------------------------------------------------------------------------
    # SECTION 8: COMPLETE COMMAND EXECUTION GUIDE
    # --------------------------------------------------------------------------
    story.append(Paragraph("8. Complete Terminal Command Execution Guide", h1_style))
    story.append(Paragraph(
        "Follow these terminal commands to compile, launch, teleoperate, and autonomously navigate the Scout Mini AMR:",
        body_style
    ))

    cmd_box = [[Paragraph(
        "<b># Step 1: Build the Workspace & Source Environment</b><br/>"
        "cd ~/agilex<br/>"
        "source /opt/ros/jazzy/setup.bash<br/>"
        "colcon build --symlink-install<br/>"
        "source install/setup.bash<br/><br/>"
        "<b># Step 2: Launch the Civil Architectural Simulation with Nav2 (Terminal 1)</b><br/>"
        "ros2 launch assem2_robot civil_simulation.launch.py use_nav:=true<br/><br/>"
        "<b># Step 3: Run the Autonomous Multi-Room Patrol Mission (Terminal 2)</b><br/>"
        "cd ~/agilex &amp;&amp; source install/setup.bash<br/>"
        "ros2 run assem2_robot civil_patrol_mission<br/><br/>"
        "<b># Step 4: (Alternative) Run Manual Point-and-Click Navigation in RViz2</b><br/>"
        "1. Click the '2D Goal Pose' button on the RViz top toolbar (or press 'G').<br/>"
        "2. Click anywhere inside any room (e.g., Materials Lab or CAD Studio) and drag the green arrow.<br/>"
        "3. The robot will plan global paths through corridors and navigate autonomously.<br/><br/>"
        "<b># Step 5: (Fallback) Run the Normal Original 10m x 10m Simulation</b><br/>"
        "ros2 launch assem2_robot simulation.launch.py",
        code_style
    )]]
    c_table = Table(cmd_box, colWidths=[523])
    c_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.8, COLOR_PRIMARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(c_table)
    story.append(Spacer(1, 8))

    # --------------------------------------------------------------------------
    # SECTION 9: CONCLUSION & VERIFICATION
    # --------------------------------------------------------------------------
    story.append(Paragraph("9. Verification & Conclusion", h1_style))
    story.append(Paragraph(
        "The Civil Architectural Simulation Environment successfully demonstrates the full operational readiness of the "
        "AgileX Scout Mini AMR under ROS 2 Jazzy Jalisco and Gazebo Harmonic: "
        "<br/>1. <b>Structural Realism:</b> Fully realized 320 m<sup>2</sup> facility adhering to civil architectural standards. "
        "<br/>2. <b>Millimetric Sensor Alignment:</b> Synchronized 0.05m 2D occupancy grid with active 360&deg; LiDAR and RGB-D point clouds. "
        "<br/>3. <b>Autonomous Navigation:</b> Drift-free EKF odometry, AMCL localization, global A*/Dijkstra path planning, and DWB trajectory tracking across 7 multi-room stations. "
        "<br/>4. <b>Operational Safety:</b> Clean file separation preserving the original normal simulation while introducing the advanced civil facility.",
        body_style
    ))

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Successfully built Academic PDF Report: {output_pdf_path}")


if __name__ == "__main__":
    out_pdf = "/home/sailakshmi/agilex/CIVIL_MAP_ENGINEERING_REPORT.pdf"
    build_pdf(out_pdf)
