import os
import docx
from docx.shared import Inches, Pt, RGBColor, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_assignment_docx(output_path):
    doc = docx.Document()
    
    # Set standard ISO A4 margins
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(20)
    section.bottom_margin = Mm(20)
    section.left_margin = Mm(20)
    section.right_margin = Mm(20)
    
    # Configure Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)
    
    # Header Banner Table
    banner_table = doc.add_table(rows=1, cols=1)
    banner_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    banner_table.autofit = False
    banner_table.columns[0].width = Mm(170)
    cell = banner_table.cell(0, 0)
    set_cell_background(cell, "7A1C28")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("DEPARTMENT OF PRODUCTION TECHNOLOGY\nMADRAS INSTITUTE OF TECHNOLOGY, ANNA UNIVERSITY")
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("COURSE: RA23E01 – ROBOT OPERATING SYSTEM (ROS)\nACADEMIC PROJECT ASSIGNMENT & THEORY EVALUATION REVIEW")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(13)
    r2.font.bold = True
    r2.font.color.rgb = RGBColor(0xF5, 0xC5, 0x42)
    
    doc.add_paragraph()
    
    # Student Metadata Table
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    meta_table.columns[0].width = Mm(50)
    meta_table.columns[1].width = Mm(120)
    
    metadata = [
        ("Student Name / Roll No:", "SAILAKSHMI B T  (Roll No: 2024511019)"),
        ("Degree & Branch:", "Bachelor of Engineering – Robotics and Automation"),
        ("Project Reference:", "AgileX Scout Mini 4WD AMR (ROS 2 Jazzy / Gazebo Harmonic)"),
        ("Evaluation Date / Venue:", "Monday, 26th October 2026 | Robotics & Automation Lab")
    ]
    for row_idx, (k, v) in enumerate(metadata):
        c0, c1 = meta_table.cell(row_idx, 0), meta_table.cell(row_idx, 1)
        set_cell_background(c0, "F0F4F8")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 60, 60, 100, 100)
        set_cell_margins(c1, 60, 60, 100, 100)
        
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(k)
        r0.font.bold = True
        r0.font.size = Pt(10)
        
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.size = Pt(10)
        if "SAILAKSHMI" in v or "AgileX" in v:
            r1.font.bold = True
            
    doc.add_paragraph()
    
    # Instructions Box
    inst_table = doc.add_table(rows=1, cols=1)
    inst_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    inst_table.columns[0].width = Mm(170)
    c_inst = inst_table.cell(0, 0)
    set_cell_background(c_inst, "FFF9E6")
    set_cell_margins(c_inst, 100, 100, 140, 140)
    p_inst = c_inst.paragraphs[0]
    r_inst = p_inst.add_run("ASSIGNMENT MANDATE:\n")
    r_inst.bold = True
    r_inst.font.color.rgb = RGBColor(0x8A, 0x5D, 0x00)
    r_inst_body = p_inst.add_run(
        "This submission covers the three syllabus evaluation modules specifically mapped to the AgileX Scout Mini 4WD AMR project: "
        "(1) Installation of ROS 2 Jazzy & Gazebo Harmonic, (2) SolidWorks URDF Export, Kinematic Import & Model Hardening, and "
        "(3) Project Migration from ROS 1/Gazebo Classic to ROS 2 Jazzy/Harmonic. A comprehensive 30-Question Multiple Choice Question (MCQ) "
        "bank with answer keys and in-depth technical rationale is appended for the same-day theory evaluation test."
    )
    r_inst_body.font.size = Pt(9.5)
    
    doc.add_paragraph()
    
    def add_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x7A, 0x1C, 0x28)
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
        return p

    # TOPIC 1
    add_heading_1("TOPIC 1: INSTALLATION OF ROS (ROS 2 JAZZY JALISCO & GAZEBO HARMONIC)")
    add_heading_2("1.1 Host Operating System & Target Architecture")
    p = doc.add_paragraph(
        "The project is deployed on Ubuntu 24.04 LTS (Noble Numbat, 64-bit x86_64 architecture). "
        "Ubuntu 24.04 is the official Tier-1 target operating system for ROS 2 Jazzy Jalisco (released May 2024, with standard LTS support through May 2029). "
        "Unlike earlier Ubuntu releases that paired with Gazebo Classic (Gazebo 11), Ubuntu 24.04 and ROS 2 Jazzy retire Gazebo Classic entirely, "
        "mandating the modern Gazebo Harmonic (gz-sim8) simulation engine."
    )
    
    add_heading_2("1.2 Step-by-Step Installation Procedure")
    p = doc.add_paragraph()
    p.add_run("Step 1: Set Locale (UTF-8 Verification)\n").bold = True
    p.add_run(
        "locale  # check for UTF-8\n"
        "sudo apt update && sudo apt install locales\n"
        "sudo locale-gen en_US en_US.UTF-8\n"
        "sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8\n"
        "export LANG=en_US.UTF-8"
    )
    p.paragraph_format.left_indent = Mm(5)
    
    p = doc.add_paragraph()
    p.add_run("Step 2: Enable Ubuntu Universe Repository & Setup GPG Keyring\n").bold = True
    p.add_run(
        "sudo apt install software-properties-common curl -y\n"
        "sudo add-apt-repository universe\n"
        "sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg\n"
        "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main\" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null"
    )
    p.paragraph_format.left_indent = Mm(5)

    p = doc.add_paragraph()
    p.add_run("Step 3: Install ROS 2 Jazzy Desktop and Build Utilities\n").bold = True
    p.add_run(
        "sudo apt update\n"
        "sudo apt install -y ros-jazzy-desktop python3-colcon-common-extensions python3-rosdep python3-argcomplete\n"
        "sudo rosdep init && rosdep update"
    )
    p.paragraph_format.left_indent = Mm(5)

    p = doc.add_paragraph()
    p.add_run("Step 4: Install Gazebo Harmonic & ROS-Gazebo Bridge\n").bold = True
    p.add_run(
        "sudo apt install -y ros-jazzy-ros-gz gz-harmonic\n"
        "sudo apt install -y ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox ros-jazzy-robot-localization"
    )
    p.paragraph_format.left_indent = Mm(5)

    add_heading_2("1.3 Environment Configuration & DDS Middleware Setup")
    p = doc.add_paragraph(
        "To ensure seamless multi-terminal execution and prevent ROS 2 loopback network storms (encountered in Failure #6), "
        "the shell configuration (~/.bashrc) must be configured with explicit Domain ID, RMW implementation, and Gazebo model paths:"
    )
    p_code = doc.add_paragraph()
    p_code.add_run(
        "source /opt/ros/jazzy/setup.bash\n"
        "source ~/agilex/install/setup.bash\n"
        "export ROS_DOMAIN_ID=42\n"
        "export RMW_IMPLEMENTATION=rmw_fastrtps_cpp\n"
        "export GZ_SIM_RESOURCE_PATH=~/agilex/src/assem2_robot/models:$GZ_SIM_RESOURCE_PATH\n"
        "export FASTRTPS_DEFAULT_PROFILES_FILE=~/agilex/fastdds_no_multicast.xml"
    )
    p_code.paragraph_format.left_indent = Mm(5)
    
    # TOPIC 2
    add_heading_1("TOPIC 2: URDF FILE IMPORT, KINEMATIC MODELING & HARDENING")
    add_heading_2("2.1 Mechanical CAD Origin & SolidWorks to URDF (SW2URDF) Pipeline")
    p = doc.add_paragraph(
        "The physical Scout Mini was modeled as a high-precision 3D CAD assembly in SolidWorks Premium 2023 (assem2.SLDASM). "
        "The assembly encompasses the aluminum monocoque chassis, four high-torque brushless in-hub DC motors, rubber tires, "
        "a 2D LiDAR mount, 6-axis IMU housing, and front RGB-D camera fixture. The SolidWorks URDF Exporter plugin was used to "
        "generate the initial robot description package."
    )
    
    add_heading_2("2.2 Critical Import Errors & Applied Hardening Solutions")
    p = doc.add_paragraph(
        "The raw exporter output cannot be executed directly in ROS 2 Jazzy. The following systematic hardening steps were implemented:"
    )
    
    hardening_items = [
        ("1. Linux Case Sensitivity & Path Fixing (Failures #2, #3):", 
         "Linux ext4 filesystems are case-sensitive. The exporter generated 'Assem2.urdf' referencing Windows paths like 'C:\\...\\assem2.SLDASM'. All file references were normalized to lowercase and converted to standard ROS package URIs: 'package://assem2_robot/meshes/w1.STL'."),
        ("2. Joint Kinematic Classification (Failure #4):", 
         "The SW exporter defaults mated concentric components to 'fixed' joints. Consequently, RViz and Gazebo treated wheels as rigid body extensions of the chassis. All four wheel joints (j1_fl, j2_rl, j3_fr, j4_rr) were converted to type='continuous' with rotation defined along the lateral Y-axis (axis xyz='0 1 0')."),
        ("3. Coordinate Frame Alignment with ROS REP-103 (Failure #13):", 
         "SolidWorks standard assemblies place +Y as the vertical axis and +Z towards the operator. In ROS REP-103, mobile robots require +X forward, +Y left, and +Z up. A 90-degree spatial correction was introduced so that positive linear velocities (cmd_vel.linear.x > 0) drive the vehicle forward rather than crab-walking sideways."),
        ("4. Massless 'base_footprint' Root Link Insertion (Failure #10):", 
         "The Kinematics and Dynamics Library (KDL) tree parser in ROS 2 robot_state_publisher rejects trees where the root link has inertia or mass. A virtual, massless 'base_footprint' link was created at the ground contact plane (Z = 0.0 m), connected to 'base_link' (elevated at axle height Z = 0.080 m) via a static fixed joint."),
        ("5. Gazebo ODE Contact Physics & Friction Properties (Failure #7):", 
         "Skid-steer 4WD robots require specific contact friction to allow controlled lateral skidding while providing longitudinal traction. The URDF was augmented with Gazebo physics tags: Coulomb friction coefficients mu1=1.0 (tangential), mu2=1.0 (transverse), contact stiffness kp=1e7, and damping kd=1e2.")
    ]
    for title, desc in hardening_items:
        p_item = doc.add_paragraph()
        r_t = p_item.add_run(f"{title} ")
        r_t.bold = True
        r_t.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
        p_item.add_run(desc)
        p_item.paragraph_format.left_indent = Mm(4)

    # TOPIC 3
    add_heading_1("TOPIC 3: PROJECT MIGRATION (ROS 1 / GAZEBO CLASSIC TO ROS 2 JAZZY & GAZEBO HARMONIC)")
    add_heading_2("3.1 Key Architectural Differences Across Generations")
    
    diff_table = doc.add_table(rows=7, cols=3)
    diff_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    diff_table.columns[0].width = Mm(40)
    diff_table.columns[1].width = Mm(65)
    diff_table.columns[2].width = Mm(65)
    
    diff_data = [
        ("Subsystem", "Legacy Architecture (ROS 1 / Classic)", "Modern Architecture (ROS 2 Jazzy / Harmonic)"),
        ("Communications & Middleware", "Centralized roscore XML-RPC master", "Decentralized DDS (FastDDS / CycloneDDS)"),
        ("Simulation Engine", "Gazebo Classic (libgazebo_ros_diff_drive.so)", "Gazebo Harmonic (gz-sim8) via ros_gz_bridge"),
        ("Build System", "catkin_make / catkin build (CMake 2.8+)", "colcon build --symlink-install (ament_cmake / python)"),
        ("Node Architecture", "Continuous loop rospy / roscpp", "Managed rclcpp / rclpy Lifecycle Nodes (configure/activate)"),
        ("Navigation Architecture", "move_base monolithic stack", "Nav2 with BT Navigator, Costmap2D, DWB Controller"),
        ("Coordinate Transforms", "tf package (legacy broadcast)", "tf2_ros with tf2_geometry_msgs & message filters")
    ]
    for r_idx, row in enumerate(diff_data):
        for c_idx, val in enumerate(row):
            c = diff_table.cell(r_idx, c_idx)
            set_cell_margins(c, 50, 50, 80, 80)
            p_c = c.paragraphs[0]
            r_c = p_c.add_run(val)
            if r_idx == 0:
                set_cell_background(c, "1B365D")
                r_c.font.bold = True
                r_c.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                r_c.font.size = Pt(9.5)
            else:
                set_cell_background(c, "F9FBFD" if r_idx % 2 == 0 else "FFFFFF")
                r_c.font.size = Pt(9)
                if c_idx == 0:
                    r_c.font.bold = True

    add_heading_2("3.2 Simulation Migration: Gazebo Harmonic & ros_gz_bridge")
    p = doc.add_paragraph(
        "In ROS 2 Jazzy, Gazebo plugins do not directly link to ROS topics. Instead, Gazebo Harmonic runs natively on Ignition/GZ Transport topics, "
        "and the bidirectional ros_gz_bridge translates messages between ROS 2 DDS and Gazebo Harmonic protobuf protocols. "
        "The Scout Mini utilizes gz::sim::systems::DiffDrive to actuate all 4 wheels and publishes standard /odom and TF transforms."
    )
    
    add_heading_2("3.3 Nav2 & SLAM Toolbox Lifecycle Node Migration")
    p = doc.add_paragraph(
        "Under ROS 2 Jazzy, SLAM Toolbox and Nav2 nodes are state-machine managed lifecycle nodes. Unlike ROS 1 where starting a node immediately "
        "started publication, ROS 2 nodes start in an 'Unconfigured' state and must transition through 'Configuring' and 'Activating' (Failure #18). "
        "The project launch architecture coordinates this transition via the nav2_lifecycle_manager to ensure map publishers are live before path planning begins."
    )

    # THEORY MCQ QUESTION BANK
    doc.add_page_break()
    add_heading_1("THEORY EVALUATION: 30 MULTIPLE CHOICE QUESTIONS (MCQ) & ANSWER KEY")
    p_mcq_intro = doc.add_paragraph(
        "This question bank is structured across the three core evaluation topics with comprehensive technical rationales directly mapped to the AgileX Scout Mini implementation."
    )
    p_mcq_intro.runs[0].font.italic = True
    
    mcq_questions = [
        # TOPIC 1: ROS 2 Installation & Environment (10 Qs)
        ("Q1", "Which Ubuntu LTS version is the official Tier-1 host operating system for ROS 2 Jazzy Jalisco?",
         ["A) Ubuntu 20.04 LTS (Focal Fossa)", "B) Ubuntu 22.04 LTS (Jammy Jellyfish)", "C) Ubuntu 24.04 LTS (Noble Numbat)", "D) Ubuntu 24.10 (Oracular Oriole)"],
         "C", "ROS 2 Jazzy Jalisco is paired natively with Ubuntu 24.04 LTS (Noble Numbat), released in May 2024 with 5-year LTS support."),
        
        ("Q2", "What is the primary function of the command 'sudo rosdep init && rosdep update' during ROS 2 setup?",
         ["A) Compiles workspace C++ source files", "B) Initializes and queries package dependency databases for system libraries", "C) Generates URDF kinematic models", "D) Starts the Gazebo Harmonic physics server"],
         "B", "rosdep inspects package.xml manifests and installs underlying OS/system dependencies required by ROS packages."),
        
        ("Q3", "Why is the environment variable 'RMW_IMPLEMENTATION=rmw_fastrtps_cpp' configured in ROS 2?",
         ["A) To select FastDDS as the underlying Data Distribution Service middleware", "B) To accelerate Gazebo raytracing physics", "C) To convert STL meshes to DAE format", "D) To switch Python rclpy scripts to multithreaded executors"],
         "A", "RMW specifies the ROS Middleware interface; rmw_fastrtps_cpp instructs ROS 2 to communicate using eProsima FastDDS."),

        ("Q4", "What occurs if two independent ROS 2 workstations share the same local network subnet without unique ROS_DOMAIN_ID settings?",
         ["A) The Linux kernel disables loopback interface lo", "B) Colcon build fails with a linker error", "C) DDS multicast discovery automatically interconnects topics, causing cross-talk and node interference", "D) Gazebo simulation freezes immediately"],
         "C", "DDS nodes on the same Domain ID discover each other over UDP multicast, resulting in unintended topic cross-talk."),

        ("Q5", "Which modern physics simulation engine replaces the retired Gazebo Classic (Gazebo 11) in ROS 2 Jazzy on Ubuntu 24.04?",
         ["A) Gazebo Harmonic (gz-sim8)", "B) Webots 2021", "C) V-REP / CoppeliaSim", "D) Gazebo Fortress (gz-sim6)"],
         "A", "Gazebo Harmonic (gz-sim8) is the long-term support release officially integrated with ROS 2 Jazzy Jalisco."),

        ("Q6", "What is the role of the ROS 2 package 'ros_gz_bridge' in an autonomous robot simulation?",
         ["A) Directly generates SolidWorks CAD part files", "B) Bidirectionally translates ROS 2 DDS messages and Gazebo Harmonic protobuf transport packets", "C) Computes inverse kinematics for robot arms", "D) Replaces the Linux system network driver"],
         "B", "ros_gz_bridge provides translation between ROS 2 topic message types and Gazebo native transport protocols."),

        ("Q7", "Why is '--symlink-install' strongly recommended when running 'colcon build' during robot development?",
         ["A) It shrinks URDF mesh file sizes", "B) It symlinks Python scripts and launch files into the install space, eliminating the need to re-compile on every edit", "C) It prevents Gazebo contact friction crashes", "D) It encrypts network traffic"],
         "B", "Symlink installation references source Python scripts and configs directly, drastically accelerating iteration and conserving disk space."),

        ("Q8", "In ROS 2, which command is used to verify that the active ROS environment is successfully loaded in the current terminal?",
         ["A) ros2 topic list", "B) printenv | grep ROS", "C) gz sim -v 4", "D) colcon test"],
         "B", "Printing environment variables filtered by 'ROS' displays ROS_DISTRO, ROS_VERSION, and RMW settings."),

        ("Q9", "What is the purpose of configuring a custom 'fastdds.xml' profile file with UDP multicast disabled on loopback?",
         ["A) To reduce CPU overheating during SolidWorks rendering", "B) To eliminate high-frequency network storms and socket buffer overflows on local-only simulations", "C) To convert LiDAR Laserscan into PointCloud2", "D) To force continuous wheel joints to rotate"],
         "B", "On Linux loopback interfaces, FastDDS multicast can trigger packet storms; disabling multicast forces clean unicast communication."),

        ("Q10", "Which tool is used to resolve and install missing package dependencies prior to building a ROS 2 workspace?",
         ["A) ament_flake8", "B) rosdep install --from-paths src --ignore-src -r -y", "C) apt search ros-jazzy-all", "D) git submodule update"],
         "B", "This rosdep command automatically identifies and installs all prerequisites declared in the workspace package.xml files."),

        # TOPIC 2: URDF & Kinematic Import (10 Qs)
        ("Q11", "According to ROS REP-103 standard conventions, what are the coordinate axis directions for an Autonomous Mobile Robot?",
         ["A) +X: Right, +Y: Forward, +Z: Up", "B) +X: Forward, +Y: Left, +Z: Up", "C) +X: Forward, +Y: Down, +Z: Right", "D) +X: Backward, +Y: Up, +Z: Left"],
         "B", "ROS REP-103 strictly defines the robot body frame as +X forward, +Y left, and +Z upward."),

        ("Q12", "Why must the wheels of the AgileX Scout Mini be defined as joint type='continuous' instead of 'revolute' in the URDF?",
         ["A) Revolute joints do not support friction parameters", "B) Continuous joints allow unbounded 360-degree rotation without upper and lower angular limits", "C) Revolute joints cannot link to base_link", "D) Gazebo rejects continuous joints"],
         "B", "Drive wheels rotate continuously without mechanical travel stops; continuous joints have no angular bounds."),

        ("Q13", "What fatal error occurs in KDL (Kinematics and Dynamics Library) if the root link of the URDF contains mass or inertia?",
         ["A) Gazebo Harmonic segmentation faults", "B) robot_state_publisher issues a warning and fails to build the kinematic chain", "C) The robot spawns upside-down", "D) LiDAR Laserscan rays invert"],
         "B", "KDL requires the kinematic root link to be massless and inertialess; hence 'base_footprint' is placed as the root."),

        ("Q14", "What is the primary function of the virtual link 'base_footprint' in mobile robot navigation?",
         ["A) Houses the camera optical sensor", "B) Represents the 2D planar projection of the robot chassis directly on the ground plane (Z = 0.0)", "C) Stores the battery discharge curve", "D) Connects the 4 wheels together rigidly"],
         "B", "base_footprint provides a zero-elevation ground-plane projection used by Nav2 costmaps and 2D footprint collision models."),

        ("Q15", "When importing a SolidWorks assembly onto a Linux workstation, why do mesh references like 'package://Assem2/meshes/W1.stl' frequently fail?",
         ["A) SolidWorks files cannot be read on Linux", "B) Linux ext4 filesystems are strictly case-sensitive, so case discrepancies cause FileNotFoundError", "C) Gazebo only accepts OBJ format", "D) Meshes must be under 1 KB"],
         "B", "Linux ext4 treats 'Assem2' and 'assem2' as distinct; case mismatches between URDF strings and filesystem paths cause broken visual links."),

        ("Q16", "What is the consequence of failing to define the '<axis xyz=\"0 1 0\"/>' tag in a wheel joint definition?",
         ["A) The wheel will be deleted upon simulation startup", "B) The simulation engine defaults to rotation about the X-axis (roll), causing erratic movement or locking", "C) The LiDAR will stop rotating", "D) The camera will lose color data"],
         "B", "Without an explicit rotation axis, the physics engine defaults to (1, 0, 0), rotating the tire transversely into the chassis."),

        ("Q17", "In the 4WD skid-steer inverse kinematics formula, why is an empirical coefficient (alpha > 1.0) applied to the track width?",
         ["A) To account for motor electrical resistance", "B) To compensate for lateral tire scrubbing and wheel slip during skid-steering turns", "C) To correct for battery voltage sag", "D) To double the robot's forward linear velocity"],
         "B", "Skid-steer vehicles cannot turn without dragging their wheels laterally; the effective track width exceeds the geometric track width."),

        ("Q18", "What role do the '<mu1>' and '<mu2>' tags play in the Gazebo URDF extension for Scout Mini wheels?",
         ["A) Define the ambient light reflection of the tire", "B) Define Coulomb friction coefficients in the primary and secondary contact directions", "C) Set the collision mesh decimation factor", "D) Calibrate the wheel encoder tick resolution"],
         "B", "mu1 and mu2 define longitudinal and lateral friction parameters essential for realistic skid-steer tractive contact."),

        ("Q19", "Why did the Scout Mini initially spawn 23 cm buried into the Gazebo ground plane after SolidWorks export?",
         ["A) The gravity vector was set to -20 m/s^2", "B) The CAD origin was located on the chassis top plate rather than the bottom tire contact patch", "C) The tire mass was set to zero", "D) The floor plane had collision disabled"],
         "B", "SolidWorks assembly origin was on the top deck; elevating the root coordinate frame by the ground offset resolved the burial."),

        ("Q20", "Which ROS 2 node is responsible for parsing the URDF and broadcasting static and dynamic transforms across the TF tree?",
         ["A) rviz2", "B) robot_state_publisher", "C) joint_state_broadcaster", "D) slam_toolbox"],
         "B", "robot_state_publisher reads the robot_description URDF and joint_states to publish forward kinematic TF transforms."),

        # TOPIC 3: Project Migration & Architecture (10 Qs)
        ("Q21", "What major architectural shift distinguishes ROS 2 communication from legacy ROS 1?",
         ["A) Removal of roscore in favor of decentralized DDS discovery", "B) Mandatory use of XML-RPC protocols", "C) Elimination of publisher-subscriber patterns", "D) Enforcement of single-threaded execution"],
         "A", "ROS 2 replaces the centralized roscore master with decentralized peer-to-peer DDS discovery."),

        ("Q22", "In migrating from Gazebo Classic to Gazebo Harmonic, which plugin replaces the legacy 'libgazebo_ros_diff_drive.so'?",
         ["A) gz::sim::systems::DiffDrive", "B) gazebo_plugins::AckermannDrive", "C) roscpp::DifferentialPlugin", "D) ign_ros2_control::DriveModule"],
         "A", "Gazebo Harmonic utilizes gz::sim::systems::DiffDrive configured within the SDF/URDF world or model description."),

        ("Q23", "Why does SLAM Toolbox in ROS 2 Jazzy fail to publish maps if executed using standard ROS 1 launch idioms?",
         ["A) ROS 2 Jazzy requires C++11 instead of C++17", "B) SLAM Toolbox is implemented as a managed Lifecycle Node that requires explicit state transitions to 'active'", "C) 2D LiDAR data is incompatible with ROS 2", "D) Nav2 forbids 2D occupancy mapping"],
         "B", "Managed lifecycle nodes do not publish active topics until transitioned through 'configure' and 'activate' states."),

        ("Q24", "What tool is used in modern ROS 2 migration to inspect the unbroken kinematic transform hierarchy?",
         ["A) ros2 run tf2_tools view_frames", "B) gz model --tree", "C) colcon graph", "D) catkin_find"],
         "A", "view_frames generates a visual graph PDF confirming the complete transform tree from map -> odom -> base_footprint."),

        ("Q25", "How is sensor fusion implemented in the Scout Mini to overcome skid-steer odometry rotational drift?",
         ["A) By doubling wheel motor current", "B) Using the robot_localization Extended Kalman Filter (EKF) fusing raw wheel odometry with 100 Hz IMU yaw velocity", "C) Disabling the front two wheels in software", "D) Limiting robot travel to straight lines"],
         "B", "The EKF fuses 100 Hz gyroscope angular rates with wheel odometry, bounding rotational slip error from 120 deg down to < 2 deg."),

        ("Q26", "What is the primary build tool used in ROS 2 workspaces to replace 'catkin_make'?",
         ["A) cmake --build", "B) colcon build", "C) rosmake", "D) bazel run"],
         "B", "colcon (collective construction) is the universal build utility for ROS 2 workspaces."),

        ("Q27", "In ROS 2 Python nodes (rclpy), how has parameter declaration changed compared to ROS 1 rospy?",
         ["A) Parameters can no longer be used in Python", "B) Parameters must be explicitly declared using 'self.declare_parameter()' before being retrieved", "C) Parameters are stored in environment variables only", "D) All parameters are hardcoded in the kernel"],
         "B", "ROS 2 enforces explicit schema declaration via declare_parameter() before get_parameter() can read them."),

        ("Q28", "Which Nav2 module is responsible for loading and executing Behavior Trees for navigation planning and recovery behaviors?",
         ["A) bt_navigator", "B) costmap_2d", "C) amcl", "D) rviz2"],
         "A", "bt_navigator coordinates navigation tasks by traversing Behavior Tree XML logic trees."),

        ("Q29", "What was the cause of timestamp flickering and TF buffer extrapolation errors in early simulation runs (Failure #17)?",
         ["A) Dual concurrent /clock topic publishers from both Gazebo and a redundant ROS bridge", "B) GPU driver overheating", "C) Low Wi-Fi signal strength", "D) Corrupted STL mesh geometry"],
         "A", "Having two nodes publishing conflicting /clock simulation timestamps causes TF buffers to detect non-monotonic time leaps."),

        ("Q30", "In the Nav2 Python 3 navigation API, what method is called to poll action progress asynchronously without blocking the GUI thread?",
         ["A) navigator.isTaskComplete()", "B) time.sleep(10)", "C) rospy.spin()", "D) sys.exit()"],
         "A", "navigator.isTaskComplete() enables non-blocking status polling, allowing Qt ground station interfaces to remain responsive.")
    ]
    
    for q_code, q_text, options, ans, rationale in mcq_questions:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(8)
        p_q.paragraph_format.space_after = Pt(2)
        r_qc = p_q.add_run(f"[{q_code}] ")
        r_qc.bold = True
        r_qc.font.color.rgb = RGBColor(0x7A, 0x1C, 0x28)
        r_qt = p_q.add_run(q_text)
        r_qt.bold = True
        
        for opt in options:
            p_opt = doc.add_paragraph(opt)
            p_opt.paragraph_format.left_indent = Mm(6)
            p_opt.paragraph_format.space_after = Pt(1)
            
        p_ans = doc.add_paragraph()
        p_ans.paragraph_format.left_indent = Mm(6)
        p_ans.paragraph_format.space_after = Pt(4)
        r_ans = p_ans.add_run(f"Correct Answer: Option {ans}\n")
        r_ans.bold = True
        r_ans.font.color.rgb = RGBColor(0x00, 0x66, 0x22)
        r_rat = p_ans.add_run(f"Technical Rationale: {rationale}")
        r_rat.font.italic = True
        r_rat.font.size = Pt(9.5)
        
    # Signature / Submission Footer
    doc.add_paragraph()
    footer_table = doc.add_table(rows=1, cols=2)
    footer_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    footer_table.columns[0].width = Mm(85)
    footer_table.columns[1].width = Mm(85)
    
    cf0 = footer_table.cell(0, 0)
    cf1 = footer_table.cell(0, 1)
    set_cell_margins(cf0, 100, 100, 100, 100)
    set_cell_margins(cf1, 100, 100, 100, 100)
    
    pf0 = cf0.paragraphs[0]
    pf0.add_run("Candidate Signature:\n\n___________________________\nSAILAKSHMI B T (2024511019)\nDate: 26/10/2026")
    pf0.runs[0].font.size = Pt(9.5)
    
    pf1 = cf1.paragraphs[0]
    pf1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pf1.add_run("Faculty Evaluator Signature:\n\n___________________________\nDepartment of Production Technology\nAnna University, MIT Campus")
    pf1.runs[0].font.size = Pt(9.5)
    
    doc.save(output_path)
    print(f"Successfully generated DOCX assignment at: {output_path}")

create_assignment_docx("/home/sailakshmi/Downloads/ROS_ASSIGNMENT_SAILAKSHMI_2024511019.docx")
