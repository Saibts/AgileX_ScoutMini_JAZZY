import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Times-Roman", 8)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 842 - 36, "DEPARTMENT OF PRODUCTION TECHNOLOGY | MIT CAMPUS, ANNA UNIVERSITY")
            self.drawRightString(595 - 54, 842 - 36, "RA23E01 - ROS PROJECT ASSIGNMENT & THEORY REVIEW")
            self.setStrokeColor(colors.HexColor("#7A1C28"))
            self.setLineWidth(0.75)
            self.line(54, 842 - 40, 595 - 54, 842 - 40)
            
        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 45, 595 - 54, 45)
        self.drawString(54, 32, "Candidate: SAILAKSHMI B T (2024511019) - B.E. Robotics & Automation")
        self.drawRightString(595 - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf(filename="/home/sailakshmi/Downloads/ROS_ASSIGNMENT_SAILAKSHMI_2024511019.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=55
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=15,
        alignment=1, # Center
        textColor=colors.white
    )
    sub_title_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#F5C542")
    )
    h1 = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=11.5,
        leading=14,
        textColor=colors.HexColor("#7A1C28"),
        spaceBefore=10,
        spaceAfter=4
    )
    h2 = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#1B365D"),
        spaceBefore=7,
        spaceAfter=3
    )
    body = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#222222"),
        spaceAfter=4
    )
    code = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1A1A1A")
    )
    
    story = []
    
    # Header Banner
    header_content = [
        [Paragraph("DEPARTMENT OF PRODUCTION TECHNOLOGY<br/>MADRAS INSTITUTE OF TECHNOLOGY, ANNA UNIVERSITY", title_style)],
        [Paragraph("COURSE: RA23E01 – ROBOT OPERATING SYSTEM (ROS)<br/>ACADEMIC PROJECT ASSIGNMENT & THEORY EVALUATION REVIEW", sub_title_style)]
    ]
    t_head = Table(header_content, colWidths=[495])
    t_head.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#7A1C28")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 8))
    
    # Metadata Table
    meta_data = [
        [Paragraph("<b>Student Name / Roll No:</b>", body), Paragraph("<b>SAILAKSHMI B T</b>  (Roll No: <b>2024511019</b>)", body)],
        [Paragraph("<b>Degree & Branch:</b>", body), Paragraph("Bachelor of Engineering – Robotics and Automation", body)],
        [Paragraph("<b>Project Reference:</b>", body), Paragraph("<b>AgileX Scout Mini 4WD AMR</b> (ROS 2 Jazzy & Gazebo Harmonic)", body)],
        [Paragraph("<b>Evaluation Date / Venue:</b>", body), Paragraph("Monday, 26th October 2026 | Robotics & Automation Lab", body)]
    ]
    t_meta = Table(meta_data, colWidths=[145, 350])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#F0F4F8")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 6))
    
    # Notice banner
    mandate_p = Paragraph(
        "<b>ASSIGNMENT MANDATE:</b> Covers the 3 mandatory evaluation topics mapped to the AgileX Scout Mini project: "
        "(1) Installation of ROS 2 Jazzy, (2) URDF Model Import & Kinematic Hardening, and (3) Project Migration from ROS 1/Classic. "
        "Followed by a comprehensive 30-Question MCQ Question Bank with detailed answer keys for the Monday theory test.", body
    )
    t_man = Table([[mandate_p]], colWidths=[495])
    t_man.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF9E6")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#F5C542")),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_man)
    story.append(Spacer(1, 8))
    
    # TOPIC 1
    story.append(Paragraph("TOPIC 1: INSTALLATION OF ROS (ROS 2 JAZZY JALISCO & GAZEBO HARMONIC)", h1))
    story.append(Paragraph("<b>1.1 Host Operating System & Target Architecture:</b>", h2))
    story.append(Paragraph(
        "The project is deployed on <b>Ubuntu 24.04 LTS (Noble Numbat, 64-bit x86_64)</b>, the official Tier-1 platform for <b>ROS 2 Jazzy Jalisco</b> (LTS May 2024 – May 2029). "
        "Ubuntu 24.04 completely retires Gazebo Classic (Gazebo 11), mandating the next-generation <b>Gazebo Harmonic (gz-sim8)</b> simulation engine.", body
    ))
    
    story.append(Paragraph("<b>1.2 Terminal Installation Sequence:</b>", h2))
    code_text = (
        "# 1. Locale Configuration (UTF-8)<br/>"
        "sudo apt update && sudo apt install -y locales && sudo locale-gen en_US en_US.UTF-8<br/>"
        "sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && export LANG=en_US.UTF-8<br/><br/>"
        "# 2. Software Repositories & ROS GPG Keyring<br/>"
        "sudo apt install -y software-properties-common curl && sudo add-apt-repository universe<br/>"
        "sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg<br/>"
        "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main\" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null<br/><br/>"
        "# 3. Desktop Installation & Dependencies<br/>"
        "sudo apt update && sudo apt install -y ros-jazzy-desktop python3-colcon-common-extensions python3-rosdep python3-argcomplete<br/>"
        "sudo rosdep init && rosdep update<br/><br/>"
        "# 4. Gazebo Harmonic & Navigation Stacks<br/>"
        "sudo apt install -y gz-harmonic ros-jazzy-ros-gz ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox ros-jazzy-robot-localization"
    )
    t_code = Table([[Paragraph(code_text, code)]], colWidths=[495])
    t_code.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F6F8FA")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_code)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>1.3 Environment & FastDDS Middleware Tuning:</b>", h2))
    story.append(Paragraph(
        "To avoid loopback socket storms encountered during development (Failure #6), the environment is locked to <code>RMW_IMPLEMENTATION=rmw_fastrtps_cpp</code> "
        "with a dedicated <code>ROS_DOMAIN_ID=42</code> and unicast XML profiles in <code>~/.bashrc</code>.", body
    ))
    
    # TOPIC 2
    story.append(Spacer(1, 6))
    story.append(Paragraph("TOPIC 2: URDF FILE IMPORT, KINEMATIC MODELING & HARDENING", h1))
    story.append(Paragraph("<b>2.1 CAD to URDF Workflow & Applied Engineering Fixes:</b>", h2))
    story.append(Paragraph(
        "The physical AgileX Scout Mini was designed in SolidWorks 2023 (<code>assem2.SLDASM</code>) and exported using the SW2URDF plugin. "
        "Direct imports into modern ROS 2 fail due to five fundamental incompatibilities that required manual kinematic hardening:", body
    ))
    
    hardening_pts = [
        "<b>1. Case Sensitivity & Mesh Resolution:</b> Normalized case-discrepancies (e.g. <code>assem2.SLDASM</code>) and re-routed Windows drive paths to ROS package URIs: <code>package://assem2_robot/meshes/...</code>.",
        "<b>2. Joint Classification:</b> Changed mated concentric wheel assemblies from <code>type=\"fixed\"</code> to <code>type=\"continuous\"</code> with rotation along the lateral Y-axis (<code>axis xyz=\"0 1 0\"</code>).",
        "<b>3. REP-103 Alignment:</b> Corrected CAD +Y orientation to the standard mobile robotics frame: <b>+X Forward, +Y Left, +Z Up</b>.",
        "<b>4. Massless 'base_footprint' Root:</b> Solved KDL tree builder rejection by creating a massless, inertialess <code>base_footprint</code> at the ground contact plane (Z=0.0) as the kinematic root parent of <code>base_link</code>.",
        "<b>5. ODE Contact Physics:</b> Configured Gazebo wheel surface tags (<code>&lt;mu1&gt;1.0&lt;/mu1&gt;</code>, <code>&lt;mu2&gt;1.0&lt;/mu2&gt;</code>, <code>&lt;kp&gt;1e7&lt;/kp&gt;</code>) to model tire traction and slip."
    ]
    for pt in hardening_pts:
        story.append(Paragraph(f"• {pt}", body))
        
    # TOPIC 3
    story.append(Spacer(1, 6))
    story.append(Paragraph("TOPIC 3: PROJECT MIGRATION (ROS 1/CLASSIC TO ROS 2 JAZZY/HARMONIC)", h1))
    story.append(Paragraph("<b>3.1 Paradigm Comparison Table:</b>", h2))
    
    mig_data = [
        [Paragraph("<b>Subsystem</b>", body), Paragraph("<b>Legacy (ROS 1 / Classic)</b>", body), Paragraph("<b>Modern (ROS 2 Jazzy / Harmonic)</b>", body)],
        [Paragraph("Middleware", body), Paragraph("Centralized roscore master", body), Paragraph("Decentralized DDS (FastDDS / CycloneDDS)", body)],
        [Paragraph("Physics Simulation", body), Paragraph("Gazebo Classic (libgazebo_ros_diff_drive)", body), Paragraph("Gazebo Harmonic (gz-sim8) via ros_gz_bridge", body)],
        [Paragraph("Build Pipeline", body), Paragraph("catkin_make / catkin build", body), Paragraph("colcon build --symlink-install (ament_cmake)", body)],
        [Paragraph("Node Execution", body), Paragraph("Unmanaged rospy.spin() loops", body), Paragraph("Managed Lifecycle Nodes (Unconfigured->Active)", body)],
        [Paragraph("Navigation Stack", body), Paragraph("move_base monolithic stack", body), Paragraph("Nav2 (Behavior Trees, Costmap2D, DWB)", body)],
        [Paragraph("Odometry Filtering", body), Paragraph("Raw wheel encoders (120° yaw drift)", body), Paragraph("robot_localization EKF (fusing IMU @ 100 Hz)", body)]
    ]
    t_mig = Table(mig_data, colWidths=[95, 195, 205])
    t_mig.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1B365D")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_mig)
    story.append(Spacer(1, 8))
    
    # THEORY MCQS
    story.append(PageBreak())
    story.append(Paragraph("THEORY EVALUATION: 30 MULTIPLE CHOICE QUESTIONS (MCQ) & ANSWER KEY", h1))
    story.append(Paragraph("<i>Comprehensive theory exam preparation covering all three syllabus modules mapped to the AgileX Scout Mini project.</i>", body))
    story.append(Spacer(1, 6))
    
    # Read MCQs from script definitions
    from generate_assignment_docs import create_assignment_docx # or just re-list
    # Let's import the 30 mcqs directly
    import re
    with open('/home/sailakshmi/agilex/generate_assignment_docs.py') as f:
        src = f.read()
        
    import ast
    # Extract mcq_questions
    start_idx = src.find("mcq_questions = [")
    end_idx = src.find("\n    for q_code, q_text, options, ans, rationale in mcq_questions:")
    mcq_block = src[start_idx:end_idx]
    loc = {}
    exec(mcq_block, {}, loc)
    mcqs = loc['mcq_questions']
    
    for q_code, q_text, options, ans, rationale in mcqs:
        q_p = Paragraph(f"<b>[{q_code}] {q_text}</b>", ParagraphStyle('Q', parent=body, fontName='Times-Bold', textColor=colors.HexColor("#1B365D"), spaceBefore=4, spaceAfter=2))
        opt_ps = [Paragraph(opt, ParagraphStyle('Opt', parent=body, leftIndent=12, spaceAfter=1)) for opt in options]
        ans_p = Paragraph(f"<b>Correct Answer: Option {ans}</b> | <i>Rationale: {rationale}</i>", ParagraphStyle('A', parent=body, fontName='Times-Roman', textColor=colors.HexColor("#006622"), leftIndent=12, spaceAfter=5))
        
        q_elements = [q_p] + opt_ps + [ans_p]
        story.append(KeepTogether(q_elements))
        
    # Signature Footer Table
    story.append(Spacer(1, 10))
    sig_data = [
        [Paragraph("<b>Candidate Signature:</b><br/><br/>___________________________<br/><b>SAILAKSHMI B T (2024511019)</b><br/>Date: 26/10/2026", body),
         Paragraph("<b>Faculty Evaluator Signature:</b><br/><br/>___________________________<br/>Department of Production Technology<br/>Anna University, MIT Campus", body)]
    ]
    t_sig = Table(sig_data, colWidths=[245, 250])
    t_sig.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#999999")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9F9F9")),
        ('PADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(KeepTogether([t_sig]))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF assignment at: {filename}")

if __name__ == "__main__":
    build_pdf()
