import json,re,statistics as st
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_LEFT,TA_RIGHT
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether,PageBreak,Preformatted
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PI
F="/usr/share/fonts/truetype/liberation/"
for n,f in [("Serif","LiberationSerif-Regular"),("Serif-B","LiberationSerif-Bold"),("Serif-I","LiberationSerif-Italic"),("Serif-BI","LiberationSerif-BoldItalic"),("Mono","LiberationMono-Regular")]:
    pdfmetrics.registerFont(TTFont(n,F+f+".ttf"))
pdfmetrics.registerFontFamily("Serif",normal="Serif",bold="Serif-B",italic="Serif-I",boldItalic="Serif-BI")
S="/tmp/claude-1000/-home-sailakshmi-agilex/80964e52-a16b-4d32-81fe-b938023fbc80/scratchpad/"
IMG=S+"rv/img/"; UP=S+"upd/"; PP=S+"paper/"
OUT="/home/sailakshmi/agilex/docs/ROS_Report_Review2_Sailakshmi.pdf"
P=json.load(open(S+"runs/patrol.json")); X=json.load(open(S+"rv/extra.json"))
# ---------- data ----------
def cond(c):
    runs=[P[f"{c}_{i}"] for i in (1,2,3)]
    ok=[l for r in runs for l in r["legs"] if l.get("ok")]
    done=[r for r in runs if len(r["legs"])==20 and all(l.get("ok") for l in r["legs"])]
    return dict(runs=runs,n=len(done),te_mean=st.mean(l["truth"] for l in ok),te_max=max(l["truth"] for l in ok),ae_mean=st.mean(l["amcl"] for l in ok),ae_max=max(l["amcl"] for l in ok),
     ye_mean=st.mean(l["yaw"] for l in ok),ye_max=max(l["yaw"] for l in ok),walls=[r["wall"] for r in runs],ret=sum(l["retries"] for r in runs for l in r["legs"]),legs=[sum(1 for l in r["legs"] if l.get("ok")) for r in runs])
N,SO,SF=cond("normal"),cond("slip_on"),cond("slip_off")
f2=lambda x:f"{x:.2f}"
stations=[l["yaw"] for r in list(P.values())+list(X.values()) for l in r["legs"] if l["name"].startswith(("STATION","Home")) and l.get("ok")]
st_max=max(stations); st_n=len(stations)
def tour(tag):
    rows=[];tot=None
    for l in open(S+f"runs/{tag}.out"):
        m=re.match(r"S(\d) goal\(([-\d.]+),([-\d.]+)\) status (\w+) driven ([\d.]+) m optimal ([\d.]+) m \((\+?-?\d+)%\) time (\d+)s arrival err ([\d.]+) m",l)
        if m: rows.append(dict(k=int(m[1]),st=m[4],drv=float(m[5]),opt=float(m[6]),pct=int(m[7].replace('+-','-').replace('+','')),t=int(m[8]),err=float(m[9])))
        m=re.match(r"TOTAL driven ([\d.]+) optimal ([\d.]+)",l)
        if m: tot=(float(m[1]),float(m[2]))
    return rows,tot
TN,TNt=tour("tour_normal"); TS,TSt=tour("tour_slip_on")
# ---------- styles ----------
def sty(size=10.5,lead=None,align=TA_JUSTIFY,font="Serif",**k): return ParagraphStyle("x",fontName=font,fontSize=size,leading=lead or size*1.42,alignment=align,**k)
base=sty(10.3,14.8,spaceAfter=6)
TTL=sty(19,23,TA_CENTER,"Serif-B",spaceAfter=6)
SUB=sty(11.5,14,TA_CENTER,spaceAfter=3)
PART=sty(16,20,TA_LEFT,"Serif-B",spaceBefore=4,spaceAfter=6,textColor=colors.HexColor("#1F3A5F"))
H1=sty(11.5,14.5,TA_CENTER,"Serif-B",spaceBefore=12,spaceAfter=6,keepWithNext=1)
H2=sty(10.8,13.5,TA_LEFT,"Serif-BI",spaceBefore=6,spaceAfter=3,keepWithNext=1)
CAP=sty(8.8,12.5,TA_CENTER,spaceBefore=4,spaceAfter=10)
TC=sty(8.2,11.6,TA_LEFT); TCB=sty(8.2,11.6,TA_LEFT,"Serif-B")
BUL=sty(10.3,14.4,TA_JUSTIFY,leftIndent=14,bulletIndent=3,spaceAfter=2.5)
CODE=sty(7.8,9.4,TA_LEFT,"Mono",leftIndent=6,spaceAfter=6,backColor=colors.HexColor("#F3F3F3"),borderPadding=4)
REF=sty(9,11,TA_LEFT,leftIndent=18,firstLineIndent=-18,spaceAfter=2.5)
def p(t,s=base): return Paragraph(t,s)
def bl(t): return Paragraph(t,BUL,bulletText="•")
import os
PF=os.path.dirname(os.path.abspath(__file__))+'/pages.json'
PAGES={}
OLD=json.load(open(PF)) if os.path.exists(PF) else {}
class Doc(BaseDocTemplate):
    def afterFlowable(self,fl):
        if isinstance(fl,Paragraph):
            n=fl.style.name
            if fl.style is H1: PAGES[fl.getPlainText()]=self.page
def h1(t): return Paragraph(t,H1)
def h2(t): return Paragraph(t,H2)
FIG_ORDER=["cad","gzciv","rvlid","rvnav","rvslam","patrol","tf","rqt","gstel","slamtb","gztop","gzobl","gzhub","gzrob","rvs1","rvs2","gsflat","gsoff","arch","rqtslip","slipint","flow","gson","gsgoal","route","errn","err3","time","legs","p1","p2","p3"]
fig_seen=[]
def FN(k): return FIG_ORDER.index(k)+1
def fig(path,w,key,cap):
    fig_seen.append(key); assert FIG_ORDER[len(fig_seen)-1]==key,(key,len(fig_seen))
    w=min(w*1.12,15.8*cm) if key not in ("arch","flow","route","slamtb","rqt","cad","p3") else min(w*1.1,15.8*cm)
    iw,ih=PI.open(path).size
    cap_h=21.5*cm if key=="arch" else 20.5*cm
    if w*ih/iw>cap_h: w=cap_h*iw/ih
    im=Image(path,width=w,height=w*ih/iw)
    t=Table([[im]],colWidths=[w+2],style=TableStyle([("BOX",(0,0),(-1,-1),0.6,colors.HexColor("#555555")),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    return KeepTogether([t,Paragraph(f"<b>Fig. {FN(key)}.</b> {cap}",CAP)])
tabn=[0]
def tab(rows,widths,cap,head=1,size=None):
    tabn[0]+=1
    cs,hs=(TC,TCB) if not size else (sty(size,size*1.5,TA_LEFT),sty(size,size*1.5,TA_LEFT,"Serif-B"))
    data=[[ (c if not isinstance(c,str) else Paragraph(c,hs if i<head else cs)) for c in row] for i,row in enumerate(rows)]
    sc=min(1,15.8*cm/sum(widths)); widths=[w*sc for w in widths]
    t=Table(data,colWidths=widths,repeatRows=head)
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.black),("BACKGROUND",(0,0),(-1,head-1),colors.HexColor("#F2F2F2")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3)]))
    return [Paragraph(f"<b>Table {tabn[0]}.</b> {cap}",sty(8.8,12.5,TA_CENTER,spaceBefore=5,spaceAfter=4,keepWithNext=1)),t,Spacer(1,8)]
def fimg(name,scale=0.24):
    iw,ih=PI.open(IMG+name).size; return Image(IMG+name,width=iw*scale,height=ih*scale)
W=17.0*cm
story=[]
# ================= title =================
CT=sty(14,18,TA_CENTER,"Serif-B",spaceAfter=4); CN=sty(11.5,15,TA_CENTER,spaceAfter=3)
ORG=colors.HexColor("#C0501E")
tt=Table([[Paragraph("AGILEX SCOUT MINI NAVIGATION USING ROS 2<br/>WITH WHEEL-SLIP SIMULATION AND CORRECTION<br/>(SECOND REVIEW)",sty(15,19,TA_CENTER,"Serif-B",textColor=ORG))]],colWidths=[14.5*cm])
tt.setStyle(TableStyle([("ROUNDEDCORNERS",[12,12,12,12]),("BOX",(0,0),(-1,-1),0.7,colors.HexColor("#777777")),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10)]))
CB=sty(13,17,TA_CENTER,"Serif-B")
story+=[Spacer(1,0.3*cm),Paragraph("RA23E01 &ndash; ROBOT OPERATING SYSTEM",sty(13,17,TA_CENTER,"Serif-B")),Spacer(1,0.4*cm),tt,Spacer(1,1.8*cm),
 Paragraph("Submitted By:",CB),Spacer(1,0.4*cm),Paragraph("SAILAKSHMI BT (2024511019)",CB),Spacer(1,1.8*cm),Paragraph("BACHELOR OF ENGINEERING",CB),Paragraph("<i>in</i>",sty(13,17,TA_CENTER)),Paragraph("ROBOTICS AND AUTOMATION",CB),Spacer(1,0.8*cm),
 Image(S+"rv/logo.png",width=5.6*cm,height=5.6*cm),Spacer(1,1.0*cm),
 Paragraph("DEPARTMENT OF PRODUCTION TECHNOLOGY<br/>MADRAS INSTITUTE OF TECHNOLOGY<br/>ANNA UNIVERSITY - CHENNAI 600044",sty(12.5,16,TA_CENTER,"Serif-B")),PageBreak(),
 Spacer(1,1*cm),Paragraph("BONAFIDE CERTIFICATE",sty(13,17,TA_CENTER,"Serif-B",spaceAfter=14)),
 p("Certified that this project report &ldquo;AgileX Scout Mini Navigation using ROS 2 with Wheel-Slip Simulation and Correction (Second Review)&rdquo; is the Bonafide work of Sailakshmi BT (2024511019) who carried out the project work under my supervision.",sty(11,15,TA_LEFT)),
 Spacer(1,5*cm),Paragraph("SIGNATURE",sty(10.5,13,TA_RIGHT,"Serif-B",spaceAfter=22)),Paragraph("SUPERVISOR",sty(10.5,13,TA_RIGHT,"Serif-B")),PageBreak()]
def tocrows():
    rows=[[Paragraph("<b>S.No</b>",sty(8.5,10,TA_CENTER)),Paragraph("<b>TOPICS</b>",sty(8.5,10,TA_CENTER)),Paragraph("<b>PAGE</b>",sty(8.5,10,TA_CENTER))]]
    c=sty(8.5,10,TA_CENTER); l=sty(8.5,10,TA_LEFT,"Serif-B")
    ks=list(OLD.keys()); n=0
    for k in ks:
        if k.startswith("Appendix ") and k!="Appendix A. Key parameters": continue
        n+=1; m=re.match(r"(\d+)\. (.*)",k)
        rows.append([Paragraph(str(n),c),Paragraph(m.group(2) if m else ("Appendices (A to D)" if k.startswith("Appendix") else k),l),Paragraph(str(OLD[k]),c)])
    t=Table(rows,colWidths=[1.6*cm,10.5*cm,1.9*cm]); t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.6,colors.black),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),("VALIGN",(0,0),(-1,-1),"MIDDLE")])); return t
story+=[Paragraph("TABLE OF CONTENTS:",sty(10,13,TA_CENTER,"Serif-B",spaceAfter=18)),tocrows(),PageBreak(),
 Paragraph("Abstract",sty(11,14,TA_CENTER,"Serif-B",spaceAfter=8)),
 p("This report presents the second review of the AgileX Scout Mini simulation in ROS 2 Jazzy and Gazebo Harmonic: wheel slip on a low-friction floor, a software slip controller, direct shortest-path goal sending in the Ground Station, and a new set of measurements. "
   "A second world with three flush patches of friction &mu; = 0.04 makes the wheels slip; a slip_control node estimates the true ground speed from the IMU, detects slip, limits the wheel command, holds the heading and publishes corrected odometry for the EKF. The report also records the drive motors, actuators and sensors of the real and simulated robot."),
 p(f"Nine planned patrol runs of 20 legs (three per condition) and two extra runs were made. On the normal floor all four runs completed 20 of 20 legs with ground-truth errors up to {f2(N['te_max'])} m. On the slip floor with the correction on, 3 of 4 runs completed; without it, 2 of 3 completed and the robot overshot the corridor hub in all three runs. "
   f"Two route tours showed driven distances within +{100*(TNt[0]/TNt[1]-1):.1f} % (normal) and +{100*(TSt[0]/TSt[1]-1):.1f} % (slip floor) of the shortest grid path. All results are from simulation."),PageBreak(),
 h1("1. Introduction"),
 p("The first review presented the Scout Mini navigating a 20 m &times; 16 m civil facility with six rooms in Gazebo. A SolidWorks model was converted to URDF (28 kg, four driven wheels), the facility and its occupancy map were generated, and Nav2 (EKF, AMCL, Smac 2D planner, regulated pure pursuit) drove the robot through the rooms from a PyQt5 Ground Station. One recorded 23-leg patrol reached 23 of 23 legs with a mean ground-truth error of 0.25 m. In that work the floor always gave good grip, so the robot could not lose traction, and the Ground Station split every click into door-aligned waypoints."),
 p("The second review asks what happens when the floor does not give grip and whether the robot still takes the shortest route. A real robot meets wet or polished patches; when a wheel slips, the wheel odometry counts distance that was never travelled and localisation drifts. The objectives of the second review are:"),
 bl("to add a second world with low-friction patches and to show wheel slip;"),
 bl("to estimate the true speed, detect slip and correct it (traction limiting, heading hold, odometry correction) in a slip_control node, with a switch to turn the correction off for comparison;"),
 bl("to show slip in the Ground Station and to send each click as one direct shortest-path goal with pre-emption;"),
 bl("to record the motors, actuators and sensors of the robot;"),
 bl("to measure everything again: nine patrol runs, two extra runs and route tours, with each number traced to a log file."),
 p("Section 2 lists what changed since the first review. Sections 3 to 6 describe the robot with its Gazebo and RViz2 views, the slip world, the slip controller and the Ground Station; Section 7 gives the algorithms used for slip handling and for goal and mission management; Section 8 explains how to run the simulation; Section 9 gives the method; Section 10 the results; Sections 11 to 13 the problems solved, limitations and conclusion."),
 PageBreak()]
# ================= REVIEW 2 =================
story+=[h1("2. Work Done Since the First Review"),
 p("The table compares the two reviews. The robot model, the facility, localisation and the Nav2 stack of the first review are unchanged in kind; the floor, the slip control, the click routing and the measurements are new. The second review asked three questions: (1) does navigation still work when the floor has patches of very low friction; (2) can a software slip controller reduce the damage; and (3) does the robot take the shortest route when the user clicks a goal in another room? While answering them, the Nav2 configuration, the Ground Station and the patrol script were changed, and everything was measured again."),
 tab([["Item","First review","Second review"],
  ["Floor","Uniform floor, &mu; = 0.25 wheels on good grip","Second world with three flush low-friction patches (&mu; = 0.04); slip controller added"],
  ["Click routing","Each click split into door-aligned waypoints","One direct NavigateToPose goal; the Smac 2D planner chooses the shortest path"],
  ["Pre-emption","Several clicks were needed","route_id counter: a new click drops the old route at once"],
  ["Goal handling","Goal could be rejected near walls","Goal snapped &ge; 0.55 m from obstacles; goal held within 0.30 m for 6 s counts as reached"],
  ["Nav2 costs","cost_travel_multiplier 2.0","cost_travel_multiplier 1.0 (planner minimises distance)"],
  ["Goal tolerance","yaw_goal_tolerance 0.35 rad","yaw_goal_tolerance 3.14 rad (position only; no spin on arrival)"],
  ["Patrol","23 legs, one recorded run","20 legs (three corridor via-point legs removed, see note below), nine planned runs plus two extra runs"],
  ["Launcher","Stale slip_control processes could survive between runs","run_civil_nav.sh stops slip_control at start-up and clean-up"]],[3.0*cm,5.6*cm,8.4*cm],"Changes between the first and the second review."),
 p("<b>Why the patrol has 20 legs instead of 23.</b> The three removed legs were the extra corridor via-points (corridor at the CAD door, hub westbound, corridor at the Materials door) that had been added in the first review so that the robot followed door-aligned lanes. In the second review the click routing was changed to one direct goal per click, with the Smac 2D planner choosing the shortest path (Section 6). Those three via-points then only forced a stop and a turn in the corridor, and the following West-lane waypoints already put the robot on the same lane, so they added distance and time without changing the visited rooms. The three legs were removed; all three rooms and the stations are still visited. The patrol is therefore not a shortened route but the same route without the redundant corridor stops, and its results must not be compared leg-for-leg with the earlier 23-leg run."),
 h1("3. The robot: drive motors, actuators and sensors"),h2("A. Drive system of the real Scout Mini"),
 p("The values below were read from public manufacturer and reseller pages on 10 November 2026. They differ between sources and none was checked on a physical robot; they are given for comparison with the simulated model, which does not model the motors electrically."),
 *tab([["Item","Published value","Note"],
  ["Drive layout","4WD skid-steer, independent drive of each wheel","Turns in place (turning radius 0)"],
  ["Drive motors","DC brushless, 4 &times; 150 W","Manufacturer manual; one reseller lists 4 &times; 250 W hub motors for the standard-wheel version, so the sources disagree"],
  ["Wheel position sensing","Hall encoder","Listed by one reseller only"],
  ["Battery","24 V, 15 Ah lithium","Runtime about 3 h unloaded and about 1 h at full payload (reseller figure)"],
  ["Payload","10 kg over long distances, up to 50 kg for short distances","Manufacturer documentation"],
  ["Maximum speed","10 km/h (about 2.8 m/s)","Other sources quote 2.7&ndash;3.0 m/s"],
  ["Mass","20 kg (sellers list 20&ndash;26 kg)","Depends on configuration"],
  ["Control input","Not listed in the sources consulted","Simulation: /cmd_vel (geometry_msgs/Twist) from teleoperation or Nav2"]],[3.2*cm,5.4*cm,8.4*cm],"Drive system of the real Scout Mini (published values)."),
 h2("B. Actuators in the simulation"),
 p("Each of the four wheels is driven by a continuous joint (j1 and j2 on the left, j3 and j4 on the right). The Gazebo DiffDrive system turns the velocity command (v, &omega;) into wheel joint velocities, so the wheels follow the command rigidly: there is no motor current, torque curve, gearbox or battery model. This is why slip has to be created by lowering the floor friction (Section 4) and why the slip controller limits the command instead of the motor current."),
 *tab([["Parameter","Value","Source"],
  ["Wheel joints","j1 and j2 on the left side, j3 and j4 on the right side (as configured in DiffDrive); type continuous","Assem2.SLDASM.urdf"],
  ["Joint limits","effort 40, velocity 25 rad/s; joint damping 0.1, joint friction 0.1","URDF"],
  ["Wheel radius / separation","0.08 m / 0.612 m (skid-steer treated as an equivalent differential drive)","DiffDrive plugin"],
  ["Plugin speed limits","&plusmn;2.5 m/s linear, &plusmn;3.5 rad/s angular","DiffDrive plugin"],
  ["Plugin acceleration limits","&plusmn;4.0 m/s&sup2; linear, &plusmn;6.0 rad/s&sup2; angular","DiffDrive plugin"],
  ["Command timeout","0.5 s (the robot stops if no command arrives)","DiffDrive plugin"],
  ["Wheel contact","&mu;<sub>1</sub> = &mu;<sub>2</sub> = 0.25; k<sub>p</sub> = 10<super>6</super>, k<sub>d</sub> = 100, min depth 0.001","URDF Gazebo tags"],
  ["Odometry and joint states","/odom at 50 Hz (odom &rarr; base_footprint); /joint_states at 50 Hz","DiffDrive and JointStatePublisher plugins"]],[3.5*cm,10.0*cm,3.5*cm],"Actuators of the simulated robot."),
 p("<b>Examples.</b> For straight driving the wheel angular speed is v/r: 7.5 rad/s at the Nav2 cruise speed of 0.6 m/s and 8.75 rad/s at the smoother limit of 0.7 m/s. In a turn at v = 0.6 m/s and &omega; = 1.0 rad/s the outer wheels turn at (v + &omega;b/2)/r = 11.3 rad/s and the inner wheels at 4.0 rad/s. The URDF joint velocity limit of 25 rad/s equals 2.0 m/s at the rim, below the 2.5 m/s plugin limit; whether Gazebo enforces the URDF limit was not tested, and it does not matter for navigation, which is limited to 0.7 m/s."),
 p("<b>Command path.</b> Nav2 controller &rarr; velocity smoother &rarr; /cmd_vel &rarr; slip_control &rarr; /cmd_vel_safe &rarr; ros_gz_bridge &rarr; Gazebo DiffDrive &rarr; wheel joints. With the correction switched off, slip_control passes the command through unchanged."),
 h2("C. Sensors in the simulation"),
 p("All sensors are Gazebo sensors defined in the URDF and bridged to ROS 2 by ros_gz_bridge. Noise values are those written in the URDF."),
 *tab([["Sensor","Gazebo type, topic, frame","Rate","Range, field of view, resolution","Noise","Used by"],
  ["2D LiDAR","gpu_lidar, /scan, lidar_link","20 Hz","720 samples over &minus;&pi;..&pi; (0.5&deg; steps); 0.12&ndash;16 m; range resolution 0.01 m","Gaussian, &sigma; = 0.01 m","AMCL, local and global costmaps, SLAM Toolbox (mapping mode)"],
  ["IMU","imu, /imu, imu_link","100 Hz","3-axis gyroscope and 3-axis accelerometer","Gyro &sigma; = 0.0002 rad/s; accelerometer &sigma; = 0.017 m/s&sup2; per axis","EKF (yaw rate); slip_control (acceleration, yaw rate)"],
  ["RGB-D camera","rgbd_camera, /camera (colour as /camera/image_raw), camera_optical_frame","30 Hz","640 &times; 480, R8G8B8; field of view 80&deg; (1.396 rad); depth 0.1&ndash;10 m","None set in the URDF","Ground Station view only (not used by Nav2)"],
  ["Wheel odometry","DiffDrive, /odom, odom &rarr; base_footprint","50 Hz","Integrates the commanded wheel motion","None (ideal wheels; slip changes the true motion, not the reading)","EKF; slip_control"]],[2.0*cm,3.2*cm,1.2*cm,3.8*cm,3.0*cm,3.8*cm],"Sensors of the simulated robot.",size=7.8),
 p("<b>Why these sensors.</b> The LiDAR gives range data for localisation and obstacle marking; AMCL ignores returns closer than 0.55 m so that the robot body is not matched against the map. The IMU gives the yaw rate (wheel-derived yaw drifts on a skid-steer base; about 60&ndash;65 % of the commanded yaw was measured before the IMU was fused) and the accelerations used by the slip estimator. Wheel odometry gives the short-term motion estimate; on a slippery floor it over-reports, which is the error slip_control corrects. The camera is not used for navigation."),
 p("<b>Sensor fusion.</b> The EKF runs at 20 Hz in 2D mode: forward speed from wheel odometry (from /odom_corrected when the slip controller is active) and yaw rate from the IMU, publishing odom &rarr; base_footprint. AMCL (1000&ndash;4000 particles, likelihood-field model, &sigma;<sub>hit</sub> = 0.20 m) publishes map &rarr; odom from /scan and the map.")]
# 4 slip world
story+=[h2("D. Software nodes and topics"),
 *tab([["Node or program","Package or file","Role"],
  ["ros_gz_bridge","ros_gz_bridge","Bridges /clock, /scan, /imu, /odom, /camera/image_raw and /joint_states; subscribes to /cmd_vel_safe"],
  ["robot_state_publisher","robot_state_publisher","Publishes the URDF kinematic tree and wheel joint transforms"],
  ["ekf_node","robot_localization","Fuses wheel speed and IMU yaw rate; publishes /odometry/filtered and odom&rarr;base_footprint"],
  ["map_server, amcl","nav2_map_server, nav2_amcl","Serve the occupancy map and publish map&rarr;odom"],
  ["planner, controller, smoother, bt_navigator","Nav2","Smac 2D A* planner, rotation-shim and regulated pure pursuit controller, velocity smoother, behaviour-tree navigator"],
  ["slip_control","assem2_robot/scripts","Slip estimation, traction limiter, heading hold, /odom_corrected"],
  ["civil_interactive_nav.py","assem2_robot/scripts","PyQt5 Ground Station: camera view, map, click-to-navigate, slip panel, emergency stop"],
  ["civil_nav2_mission.py, nav_tour_test.py","assem2_robot/scripts","20-leg patrol with ground-truth verification; route-efficiency tour"],
  ["generate_civil_world.py, generate_slip_world.py","assem2_robot/scripts","Generate the facility world and the slip world"]],[4.2*cm,3.6*cm,8.0*cm],"Nodes and programs of the system."),
 h2("E. Gazebo and RViz2 views"),
 p("The figures below show the model and the simulation as built and used in the first stage, on the normal floor: the SolidWorks assembly, the facility in Gazebo, the sensor data and costmaps in RViz2, SLAM mapping, the transform tree and the node graph. The Gazebo window could not be captured during the slip runs of this review because the Wayland desktop blocks screen capture (problem 10 in Section 11); the slip floor is therefore shown through Gazebo camera renders, RViz2 window grabs (through XWayland) and Ground Station screenshots in Sections 4 and 6."),
 fig(S+"rv/shots/solidworks_amr_cad_assembly.jpg",12*cm,"cad","SolidWorks assembly of the robot (chassis, upper deck, four wheels, URDF export set-up) before conversion to URDF."),
 fig(S+"rv/shots/screenshot_gazebo_harmonic_civil.jpg",14*cm,"gzciv","The civil facility in Gazebo Harmonic with the robot, the entity tree and the world panel."),
 fig(S+"rv/shots/screenshot_rviz2_lidar_pointcloud.jpg",14*cm,"rvlid","RViz2 with the LiDAR scan (blue sector) beside the Gazebo view; the terminal shows /scan message rates."),
 fig(S+"rv/shots/screenshot_rviz2_robot_model.jpg",11.5*cm,"rvnav","RViz2 Nav2 view in the first 10 m arena: inflated costmap, obstacles and the controller's sampled trajectories (green)."),
 fig(S+"rv/shots/screenshot_rviz2_slam_civil_tracing.jpg",14*cm,"rvslam","RViz2 on the civil map with the robot, the LiDAR scan and its driven trace (green)."),
 fig(S+"rv/shots/gazebo_rviz_patrol_navigation.jpg",14*cm,"patrol","Autonomous patrol: Gazebo (left), RViz2 (bottom) and the patrol terminal reporting distance remaining."),
 fig(S+"rv/shots/screenshot_tf2_frames_tree.jpg",14*cm,"tf","Transform tree: map, odom, base_footprint, base_link and the wheel, LiDAR, IMU and camera frames."),
 fig(S+"rv/shots/screenshot_rqt_graph_topics.jpg",11*cm,"rqt","rqt_graph of the running ROS 2 nodes and topics (first-stage system, before slip_control)."),
 fig(S+"rv/shots/screenshot_ground_station_telemetry.jpg",14*cm,"gstel","Ground Station with telemetry and technical data panel, camera view and architectural map."),
 fig(S+"rv/shots/screenshot_slam_toolbox_map.jpg",9.5*cm,"slamtb","Occupancy grid built with SLAM Toolbox in the first stage (mapping only; not evaluated here)."),
]
story+=[h1("4. The slip world"),
 p("A second world, civil_world_slip.sdf, is generated from the civil world by generate_slip_world.py. It is the same facility with three flush low-friction patches. A patch has &mu; = 0.04, against &mu; = 0.25 for the wheels, so it can supply only a very small acceleration:"),
 p("<i>a</i><sub>max</sub> = &mu; <i>g</i> = 0.04 &times; 9.81 &asymp; 0.39 m/s&sup2; on a patch, against 0.25 &times; 9.81 &asymp; 2.5 m/s&sup2; that the wheels can be commanded to deliver on dry floor.",sty(10.3,13,TA_CENTER,spaceAfter=6)),
 *tab([["Patch","Centre (x, y) [m]","Size (x &times; y) [m]","&mu;"],["Conference Hall doorway (north)","(0.0, 2.3)","1.2 &times; 1.8","0.04"],["East corridor","(1.1, 0.0)","1.0 &times; 2.4","0.04"],["West corridor","(&minus;1.1, 0.0)","1.0 &times; 2.4","0.04"]],[6.2*cm,3.8*cm,4.4*cm,2.6*cm],"Low-friction patches of the slip world (verified in civil_world_slip.sdf)."),
 p("The patches had to be flush with the floor: a first version with raised tiles stopped the robot at the 3 mm edge (problem 1 in Section 11). The generator therefore removes the collision of the ground plane, lays floor tiles around holes of the patch size and fills the holes with the low-friction patches. The corridor patches lie between the corridor hub and the columns and cover the full corridor width, so that turns at the doors happen on dry floor and the robot is already straight on the ice (problem 13). Because the Gazebo wheels follow velocity commands rigidly, slip occurs whenever the commanded acceleration exceeds what the floor supplies. With the correction off, the wheels then turn faster than the body moves (Fig. {gsoff}: wheels 0.48 m/s, ground 0.40 m/s, slip 16 %), the odometry counts distance that was never travelled, and the EKF and AMCL believe the robot is farther along than it is.".format(gsoff=FN("gsoff"))),
 p("The four Gazebo views below were rendered from the slip world itself (correction on, robot at the corridor hub). The Gazebo window cannot be captured from the desktop, so virtual camera sensors were placed in the running world (script gz_cams.py) and their images saved; the blue areas are the three low-friction patches."),
 fig(S+"rv/shots/gz_top.png",14*cm,"gztop","Slip world from above, north at the top: the facility with its six rooms, the robot at the corridor hub and the three blue low-friction patches (north doorway above the robot, east and west corridor patches beside it)."),
 fig(S+"rv/shots/gz_oblique.png",14*cm,"gzobl","Oblique Gazebo view of the whole slip world."),
 fig(S+"rv/shots/gz_hub.png",14*cm,"gzhub","The corridor hub seen from the south: the robot on dry floor with the three patches around it."),
 fig(S+"rv/shots/gz_robot.png",14*cm,"gzrob","The Scout Mini model in front of the north doorway patch, with the east and west corridor patches on either side."),
 p("RViz2 views of the same slip world are given next. They were grabbed with xwd from the RViz2 window, which runs under XWayland; the windows of Gazebo itself could not be grabbed, which is why its views above come from camera sensors. RViz2 shows the occupancy map and costmaps (black), the LiDAR scan, the robot model, the planned path and the TF frames. The slip patches are flush with the floor and carry no map or costmap marking, so they are not visible in RViz2; this is why the slip controller has to detect slip from motion."),
 fig(S+"rv/shots/rviz_slip_start.png",10.5*cm,"rvs1","RViz2 in the slip world at start: robot at the corridor hub, LiDAR scan on the walls and costmap around the posts. The panel shows the display tree and the Orbit view."),
 fig(S+"rv/shots/rviz_slip_north.png",10.5*cm,"rvs2","RViz2 while the robot drove through the north doorway to a goal at (0, 2.6) over the north slip patch; the thin line ahead of the robot is the Nav2 plan. The goal succeeded; /slip/active stayed false, so no slip was detected on that run."),
 fig(IMG+"p24_0.png",9.5*cm,"gsflat","Ground Station on the slip floor: the blue patch in the Conference Hall doorway is visible in the camera view and as a hatched box on the map (earlier corridor-patch positions)."),
 fig(IMG+"p25_0.png",13*cm,"gsoff","Correction OFF on the Conference Hall patch: wheels 0.48 m/s, ground speed 0.40 m/s, slip 16 %, traction 100 % (no limiting)."),
 p("A first straight-line test on an earlier, slipperier floor (&mu; = 0.02) gave a position error of +1.12 m with the correction off, against +0.04 m with it on.")]
# 5 controller
story+=[h1("5. The slip controller (slip_control)"),h2("A. Where it sits"),
 p("slip_control (scripts/slip_control.py) sits between Nav2 and the wheels. The bridge subscribes to /cmd_vel_safe instead of /cmd_vel, and the node reads Nav2's /cmd_vel, limits it and publishes /cmd_vel_safe. The EKF no longer reads the raw /odom but the corrected odometry /odom_corrected, and it fuses both the forward and the sideways speed; the IMU yaw rate is used as before. These changes are made in civil_simulation.launch.py, which passes the argument slip_correction. Detection runs at the IMU rate (100 Hz) and the command limiter at 50 Hz."),
 fig(S+"arch_mpl.png",13*cm,"arch","Complete architecture with the slip controller, redrawn and checked against civil_simulation.launch.py, the Ground Station code and the running ROS graph (red marks what the slip controller changed or added; numbers give the order of the data flow of the table below)."),
 *tab([["Step","From &rarr; To","Topic or data","What it does"],
  ["1","Gazebo sensors &rarr; ros_gz_bridge","/scan, /imu, /odom, /clock, /camera/image_raw","Sensors and wheel odometry enter ROS 2 (on the slip floor the odometry over-reports on a patch)"],
  ["2","Bridge &rarr; AMCL, EKF, slip_control","/scan to AMCL; /imu to the EKF; /imu and /odom to slip_control","slip_control receives raw wheel odometry and IMU; the EKF still reads the IMU directly"],
  ["3","Map server &rarr; AMCL","/map (civil_map)","Unchanged"],
  ["4","slip_control &rarr; EKF","/odom_corrected (vx and vy)","New: slip-corrected odometry replaces raw /odom as the EKF wheel input"],
  ["5","State estimation &rarr; Nav2","/odometry/filtered; TF odom&rarr;base_footprint, map&rarr;odom","The map pose stays close to the true pose"],
  ["6","Ground Station or mission &rarr; BT navigator","NavigateToPose action (RViz2 uses /goal_pose)","A click is one direct goal that cancels the old route"],
  ["7&ndash;9","BT navigator &rarr; planner &rarr; controller &rarr; smoother &rarr; collision monitor","ComputePathToPose, FollowPath, /plan, /cmd_vel_nav, /cmd_vel_smoothed","Unchanged (the collision monitor is a pass-through)"],
  ["10","Collision monitor &rarr; slip_control","/cmd_vel","Changed: the command no longer goes straight to the bridge"],
  ["11","slip_control &rarr; ros_gz_bridge","/cmd_vel_safe","New: traction limiter and heading hold act while slip is detected"],
  ["12","Bridge &rarr; Gazebo DiffDrive","/cmd_vel_safe","The bridge subscribes to /cmd_vel_safe"],
  ["13","Nav2 and slip_control &rarr; Ground Station","/plan, /odometry/filtered, /camera/image_raw, /scan, /odom, /slip/*","The slip panel shows slip, ground speed, traction and surface"]],[1.3*cm,4.6*cm,5.0*cm,6.1*cm],"Data flow of the architecture with slip control.",size=7.8),
 h2("B. Estimating the true speed and detecting slip"),
 p("Slip means that the wheel speed is not the speed of the body. The IMU does not depend on the wheels, so it provides an independent measurement. The node integrates the forward IMU acceleration (gravity removed using the IMU orientation) into a ground-speed estimate and blends it with the wheel speed in a complementary filter. The blend is used only when the wheel and the IMU agree about the acceleration, so that a spinning wheel cannot pull the estimate along; a zero-velocity update is applied only when the wheels, the accelerometer and the gyroscope are all quiet; and the estimate is kept below an energy bound. Slip is the difference between wheel speed and estimate."),
 *tab([["Parameter","Value","Purpose"],["Slip enter threshold","|v<sub>wheel</sub> &minus; v<sub>ground</sub>| &gt; 0.15 m/s for 0.05 s","Declares slip; avoids false alarms from noise"],["Slip exit threshold","below 0.06 m/s","Clears the slip flag"],["Fusion gate","0.05 m/s (and acceleration agreement)","Prevents a spinning wheel from corrupting the estimate"],["Latch breaker","body steady for 0.5 s while slip is still flagged","Resets the estimate to the wheel speed so slip does not stay on"],["Energy bound","|v<sub>est</sub>| &le; v<sub>peak</sub> + 0.05 m/s; v<sub>peak</sub> decays at 0.3 m/s&sup2;","Stops integration drift from running away"]],[3.6*cm,7.2*cm,6.2*cm],"Detection parameters (defaults of slip_control.py)."),
 p("Fig. "+str(FN("rqtslip"))+" shows the same data flow as rqt_graph reports it on the running slip world: slip_control sits between the collision monitor (/cmd_vel) and the bridge (/cmd_vel_safe), reads /imu and /odom, and publishes /odom_corrected for the EKF."),
 fig(S+"rv/shots/rqt_graph_slip_world.png",11*cm,"rqtslip","rqt_graph of the running slip world (Nodes/Topics (all), correction on). The graph was produced by rqt_graph itself from the live ROS 2 system and laid out top to bottom for the page; /tf, action, bond and parameter topics and the Nav2 helper nodes are hidden. The slip path is /cmd_vel &rarr; slip_control &rarr; /cmd_vel_safe &rarr; ros_gz_bridge, and /odom_corrected feeds the EKF."),
 *tab([["Step","Formula","Meaning"],
  ["Gravity removal","a = a<sub>imu</sub> &minus; g &middot; 2(q<sub>x</sub>q<sub>z</sub> &minus; q<sub>w</sub>q<sub>y</sub>); &nbsp; a<sub>lp</sub> &larr; a<sub>lp</sub> + 0.3 (a &minus; a<sub>lp</sub>)","Removes the gravity leaked into the forward axis by pitch and roll, then smooths it"],
  ["Ground speed","v<sub>est</sub> &larr; v<sub>est</sub> + (a<sub>lp</sub> &minus; a<sub>bias</sub>) dt","Integrates the IMU acceleration; independent of the wheels"],
  ["Blending (no slip)","v<sub>est</sub> &larr; v<sub>est</sub> + min(3.0 G dt, 1) (v<sub>w</sub> &minus; v<sub>est</sub>); &nbsp; G = exp(&minus;(d/0.05)&sup2;) &middot; exp(&minus;((a<sub>w</sub> &minus; a<sub>lp</sub> + a<sub>bias</sub>)/0.4)&sup2;); &nbsp; d = v<sub>w</sub> &minus; v<sub>est</sub>","Pulls the estimate to the wheels only while wheel and IMU agree about speed and acceleration"],
  ["Energy bound","v<sub>peak</sub> = max(|v<sub>w</sub>|, v<sub>peak</sub> &minus; 0.3 dt); &nbsp; |v<sub>est</sub>| &le; v<sub>peak</sub> + 0.05","The body cannot be faster than the fastest recent wheel speed"],
  ["Slip speed and ratio","&Delta;v = v<sub>w</sub> &minus; v<sub>est</sub>; &nbsp; s = &Delta;v / max(|v<sub>w</sub>|, 0.2), &minus;1 &le; s &le; 1","Example: (0.35 &minus; 0.19)/0.35 &asymp; 46 %, as in the Ground Station of Fig. "+str(FN("gson"))]],[3.2*cm,8.0*cm,4.6*cm],"Estimation formulas (as implemented; v<sub>w</sub> wheel speed, v<sub>est</sub> estimated ground speed, a acceleration, G blending weight).",size=7.8),
 h2("C. Correcting the slip"),
 p("Once slip is detected, four actions are taken (Fig. {f}):".format(f=FN("slipint"))),
 fig(IMG+"p29_4.png",13*cm,"slipint","Inside slip_control: the ground speed is estimated from the IMU and the wheel speed, slip is flagged, the wheel command is limited and corrected odometry is published."),
 *tab([["Action","What it does","Reason"],
  ["1. Traction limiter","While slipping, and for 0.6 s afterwards, the wheel command is clamped to v<sub>ground</sub> &plusmn; 0.12 m/s and can never exceed the larger of the request and the current output; the angular acceleration limit is halved (6.0 to 3.0 rad/s&sup2;); the linear limit stays at 4.0 m/s&sup2; (a slip limit of 0.8 m/s&sup2; is declared in the code but not used)","Like traction control in a car: less torque lets the wheels grip again"],
  ["2. Heading hold","The IMU yaw rate is fed back (gain 0.4, limit &plusmn;0.6 rad/s)","Uneven grip makes the robot veer; this steers it back"],
  ["3. Sideways slip","Lateral speed v<sub>y</sub> is integrated from the IMU lateral acceleration minus the turning term, and pulled to zero when the tyres grip","Wheel odometry cannot see a sideways slide"],
  ["4. Odometry correction","/odom_corrected carries the wheel speed with the slip removed (dead-bands 0.04 m/s for v<sub>x</sub> and 0.03 m/s for v<sub>y</sub>) and the sideways speed; the EKF uses it","The map pose stays close to the true pose, so Nav2 and AMCL keep working"]],[3.0*cm,8.6*cm,5.4*cm],"The four correction actions."),
 p("<i>Formulas as implemented: traction limiter v<sub>out</sub> = clamp(v<sub>cmd</sub>, v<sub>est</sub> &minus; 0.12, v<sub>est</sub> + 0.12); heading hold &Delta;&omega; = clamp(0.4(&omega;<sub>cmd</sub> &minus; &omega;<sub>imu</sub>), &minus;0.6, +0.6); sideways speed v<sub>y</sub> integrates (a<sub>y</sub> &minus; a<sub>y,bias</sub> &minus; &omega; v<sub>est</sub>); speed correction removes the part of |&Delta;v| above 0.04 m/s without changing sign.</i>",sty(9,14,TA_LEFT)),
 h2("D. Switching and monitoring"),
 p("The correction is switched off with the launch argument slip_correction:=false. The node then still estimates and publishes the slip but does not change the commands or the odometry. It publishes /slip/active, /slip/ratio, /slip/traction_scale and /slip/ground_speed_est, and a latched topic /slip/correction_enabled so that the Ground Station shows which mode is running. The control loop is shown in Fig. {f}: the traction limiter acts only while slip is detected and for 0.6 s afterwards, whereas the heading hold and the odometry correction run all the time; the heading hold only adds a yaw-rate correction (at most 0.6 rad/s) and the odometry correction removes only speed differences above the 0.04 m/s dead-band.".format(f=FN("flow"))),
 fig(S+"flow_mpl.png",14.4*cm,"flow","Flowchart of the control loop with the slip controller, checked against slip_control.py: only the traction limiter depends on the slip decision; the heading hold and the odometry correction run all the time (when the correction is switched on).")]
# 6 ground station
story+=[h1("6. The Ground Station: slip panel and direct routing"),
 p("<b>Slip panel.</b> The Ground Station shows a Wheel Slip Monitor: a slip percentage bar, wheel speed against ground speed, the traction scale, the surface under the robot (&ldquo;normal floor&rdquo; or &ldquo;LOW-FRICTION&rdquo; with the zone name) and a button explaining the correction. The label reads &ldquo;GRIP OK&rdquo;, &ldquo;SLIP DETECTED &ndash; traction control + odometry correction&rdquo; or, when the correction is off, &ldquo;SLIP DETECTED &ndash; correction OFF (monitor only)&rdquo;. The three patches are drawn on the map as blue hatched boxes. The first version of the label said &ldquo;correction ACTIVE&rdquo; even when it was off; the latched topic /slip/correction_enabled fixed this."),
 fig(IMG+"p31_0.png",11.5*cm,"gson","The same patch with the correction ON: slip detected at 45 %; the wheel command is cut to 0.35 m/s against a ground speed of 0.19 m/s and traction is reduced to 64 %."),
 p("<b>Click-to-navigate by the shortest path.</b> The robot chose long routes between rooms and a click often needed several tries, on both floors. The earlier fix split each click into door-aligned waypoints (door, corridor lane, door, target); this forced detours along the corridor, and a new click could be ignored while an old route was still running. The Ground Station now sends one NavigateToPose goal and the Smac 2D planner finds the shortest path through the doorways. Each click increments a route counter (route_id); an older route notices that it was superseded and stops without cancelling the new goal, so one click is enough. The clicked point is moved to the nearest cell at least 0.55 m from obstacles so that Nav2 does not reject or abort it, and a goal the robot has stayed within 0.30 m of for 6 s is cancelled and counted as reached. The emergency stop cancels the route. In Nav2, cost_travel_multiplier is 1.0 and yaw_goal_tolerance 3.14 rad, so the planner minimises distance and the robot does not spin to a final heading."),
 fig(IMG+"p35_0.png",11.5*cm,"gsgoal","Ground Station with a goal in the Conference Hall; the green line is the path planned by Nav2.")]
# 7 method
ACODE=ParagraphStyle("ac",fontName="Mono",fontSize=7.2,leading=8.9,leftIndent=4,backColor=colors.HexColor("#F3F3F3"),borderPadding=5,spaceBefore=3,spaceAfter=10)
def alg(n,title,code,note=None):
    out=[KeepTogether([Paragraph(f"<b>Algorithm {n}.</b> {title}",sty(9.5,12,TA_LEFT,"Serif",spaceBefore=6,spaceAfter=3)),Preformatted(code.strip("\n"),ACODE)])]
    if note: out.append(p(note))
    return out
story+=[h1("7. Algorithms Used"),
 p("This section gives, in pseudo-code, the algorithms of the second review as implemented in slip_control.py, civil_interactive_nav.py and civil_nav2_mission.py, followed by the existing algorithms that were used unchanged. Symbols: v<sub>w</sub> wheel speed from odometry, v<sub>est</sub> estimated ground speed, a<sub>f</sub> filtered forward acceleration, a<sub>b</sub> its bias, &omega;<sub>z</sub> IMU yaw rate, dt the sample period."),
 h2("A. Slip estimation and correction (slip_control)"),
 *alg(1,"Ground-speed estimation (on every IMU sample, 100 Hz)","""
a   <- forward IMU acceleration x sign - gravity leak (from the IMU orientation)
a_f <- a_f + 0.3 (a - a_f)                          # low-pass filter
quiet <- |v_w| < 0.02 and |a_f - a_b| < 0.05 and |w_z| < 0.03
quiet_t <- quiet_t + dt if quiet else 0
if quiet_t > 0.3:                                    # zero-velocity update
    a_b <- a_b + 0.02 (a_f - a_b);  v_est <- v_w
else:
    v_est <- v_est + (a_f - a_b) dt                  # integrate the IMU
    if not slip:                                     # complementary pull to the wheels
        d    <- v_w - v_est
        gate <- exp(-(d/0.05)^2) * exp(-((a_w - a_f + a_b)/0.4)^2)
        v_est <- v_est + min(3.0 gate dt, 1) d
if body steady (|a_f - a_b| < 0.08) for 0.5 s and slip and not quiet:
    v_est <- v_est + min(3 dt, 1) (v_w - v_est)      # latch breaker (IMU drift)
v_peak <- max(|v_w|, v_peak - 0.3 dt)                # energy bound
v_est  <- clamp(v_est, -(v_peak + 0.05), v_peak + 0.05)
""","The gate stops a spinning wheel from pulling the estimate toward the wheel speed: the pull is strong only when the wheel and IMU agree about speed and acceleration."),
 *alg(2,"Slip detection with hysteresis and debounce","""
slip_speed <- v_w - v_est
ratio      <- clamp(slip_speed / max(|v_w|, 0.2), -1, 1)       # published as /slip/ratio
if not slip:
    if |slip_speed| > 0.15:   cand_t <- cand_t + dt
    else:                     cand_t <- 0
    if cand_t >= 0.05:        slip <- True                      # SLIP DETECTED
else if |slip_speed| < 0.06:
    slip <- False;  t_clear <- now                              # GRIP RECOVERED
""","The enter threshold (0.15 m/s) is higher than the exit threshold (0.06 m/s), which prevents the flag from chattering."),
 *alg(3,"Traction limiter and heading hold (control step, 50 Hz)","""
c_v, c_w <- command from Nav2 (0 if older than 0.5 s)
limiting <- slip or (now - t_clear) < 0.6
target_v <- c_v
if limiting:
    target_v <- clamp(c_v, v_est - 0.12, v_est + 0.12)             # wheels may lead the ground by 0.12
    target_v <- clamp(target_v, min(c_v, out_v), max(c_v, out_v))  # never above request or output
out_v <- slew(out_v, target_v, 4.0 m/s^2, dt)
scale <- |out_v| / |c_v|                                          # /slip/traction_scale
w_target <- c_w + clamp(0.4 (c_w - w_z), -0.6, 0.6)               # yaw-rate feedback
out_w <- slew(out_w, w_target, 6.0 (3.0 if limiting) rad/s^2, dt)
publish (out_v, out_w) on /cmd_vel_safe
""","This is traction control in the sense of a car: while the wheels spin, the speed command is held close to the true ground speed so that the tyres return to peak grip, and the heading is held by feeding back the gyro."),
 *alg(4,"Sideways slip estimation (IMU lateral channel)","""
a_y <- lateral IMU acceleration (low-pass, bias a_yb)
if quiet_t > 0.3:  a_yb <- a_yb + 0.02 (a_y - a_yb);  v_y <- 0
else:
    v_y <- v_y + (a_y - a_yb - w_z v_est) dt        # remove the centripetal term
    v_y <- v_y - min(2.0 exp(-(v_y/0.06)^2) dt, 1) v_y   # decays to 0 when the tyres grip
    v_y <- clamp(v_y, -1.5, 1.5)
""",None),
 *alg(5,"Odometry correction and corrected pose (on every /odom message)","""
d <- v_w - v_est
if enabled and |d| > 0.04:
    v <- v_w - sign(d) (|d| - 0.04);  if v v_w < 0: v <- 0     # never flips direction
if enabled and |v_y| > 0.03:  v_y <- v_y - sign(v_y) 0.03
yaw <- yaw + w_z dt                                            # IMU yaw, not wheel yaw
x   <- x + (v cos yaw - v_y sin yaw) dt
y   <- y + (v sin yaw + v_y cos yaw) dt
publish /odom_corrected (v, v_y, w_z, pose); the EKF uses it instead of /odom
""","With the correction switched off (slip_correction:=false) the node publishes the raw speed and passes the command through unchanged, which gave the comparison runs."),
 h2("B. Goal and mission management"),
 *alg(6,"Click-to-navigate with pre-emption (Ground Station)","""
on map click (x, y):
    route_id <- route_id + 1;  my_id <- route_id
    cancel the active NavigateToPose goal
    (gx, gy) <- nearest free cell >= 0.55 m from any obstacle to (x, y)    # goal snap
    send ONE NavigateToPose goal (gx, gy, heading = direction of travel)
    while goal active and my_id == route_id:
        if distance(robot, goal) < 0.30 m for 6 s:  cancel goal; count as reached
    if my_id != route_id:  stop quietly (a newer click owns the robot)
on emergency stop:  route_id <- route_id + 1;  cancel goal;  publish zero velocity
""","The planner (Smac 2D) chooses the shortest path through the doorways; the counter ensures that one click is enough, even if a route is still running."),
 *alg(7,"Patrol leg with closed-loop verification (civil_nav2_mission)","""
for each leg (name, x, y, heading, station) in MISSION:                 # 20 legs
    for attempt in 1..3:
        send NavigateToPose(x, y, heading);  wait up to 120 s
        err_amcl  <- distance(AMCL pose, goal);   err_truth <- distance(Gazebo pose, goal)
        err_yaw   <- |heading error|
        ok <- status == SUCCEEDED and err_amcl <= 0.45 and err_truth <= 0.45
        if station: ok <- ok and err_yaw <= 40 deg
        if ok: break
        clear both costmaps;  retry
    if not ok: stop the run (leg failed)
    if station: wait 2 s
""",None),
 *alg(8,"Route-efficiency measurement (nav_tour_test)","""
for each goal in TOUR:  snap goal >= 0.55 m from obstacles;  send NavigateToPose
    driven  <- sum of |displacement| of the map -> base_footprint transform at about 5 Hz
    optimal <- length of grid A* from the start of the leg (0.30 m clearance, 0.30 m cells)
    excess  <- driven / optimal - 1
""",None),
 h2("C. Existing algorithms used without change"),
 *tab([["Function","Algorithm","Where"],
  ["Skid-steer kinematics","v<sub>L</sub> = v &minus; &omega;b/2, v<sub>R</sub> = v + &omega;b/2, wheel speed = v/r (b = 0.612 m, r = 0.08 m)","Gazebo DiffDrive"],
  ["Global planning","A* on the costmap grid (Smac Planner 2D), cost_travel_multiplier 1.0","Nav2 planner"],
  ["Local control","Rotation shim, then regulated pure pursuit (look-ahead 0.25&ndash;0.60 m, speed 0.60 m/s)","Nav2 controller"],
  ["Velocity smoothing","Acceleration and deceleration limits on the command (0.7 m/s, 1.0 rad/s)","Nav2 velocity smoother"],
  ["Localisation","Adaptive Monte Carlo localisation: particle filter (1000&ndash;4000 particles), likelihood-field laser model","Nav2 AMCL"],
  ["State estimation","Extended Kalman filter, 2D, 20 Hz: vx (wheels or corrected) and yaw rate (IMU)","robot_localization"],
  ["Obstacle handling","Inflated cost layer (0.55 m), local costmap 4 &times; 4 m at 5 Hz, recovery behaviours","Nav2 costmaps and BT"],
  ["Mapping","Graph-based SLAM with scan matching (mapping only)","SLAM Toolbox"]],[3.4*cm,9.4*cm,3.0*cm],"Algorithms used without change in the second review."),
]
story+=[h1("8. How to Run"),
 p("All commands are run from a terminal on Ubuntu 24.04 with ROS 2 Jazzy and Gazebo Harmonic installed. The Gazebo window, RViz2 and the Ground Station open on the desktop; the launch files set ROS_DOMAIN_ID 19 and local-only discovery so that the simulation does not mix with other ROS 2 programs on the network."),
 h2("A. Requirements and build"),
 *tab([["Requirement","Used for"],
  ["ROS 2 Jazzy, ros_gz (bridge, sim), Gazebo Harmonic","Simulation and the topic bridge"],
  ["navigation2, nav2_bringup, nav2_smac_planner","Nav2 navigation stack"],
  ["robot_localization, slam_toolbox","EKF and mapping"],
  ["python3-pyqt5, numpy, matplotlib","Ground Station and test scripts"]],[8.0*cm,7.8*cm],"Software required."),
 Preformatted("git clone https://github.com/Saibts/AgileX_ScoutMini_JAZZY.git ~/agilex\ncd ~/agilex\ngit checkout slip-simulation\nsource /opt/ros/jazzy/setup.bash\ncolcon build --symlink-install     # symlink install: script edits take effect at once\nsource install/setup.bash",ACODE),
 h2("B. Normal floor with the Ground Station"),
 Preformatted("cd ~/agilex\n./run_civil_nav.sh        # stops stale processes, then starts Gazebo, Nav2, RViz2 and the Ground Station",ACODE),
 p("Wait about 40 s until the robot appears in the map. Click a point on the Ground Station map to send one direct goal; click again to replace it; the red button stops the robot. The station buttons S1&ndash;S7 send the robot to the named rooms."),
 h2("C. Slip floor, correction on or off"),
 Preformatted("cd ~/agilex\n./run_slip_demo.sh                          # slip world, correction ON, runs the patrol mission\n./run_slip_demo.sh --no-mission            # same, without the automatic patrol (click goals yourself)\n./run_slip_demo.sh slip_correction:=false  # correction OFF: monitor only, for comparison\n\n# equivalent explicit command\nW=$HOME/agilex/install/assem2_robot/share/assem2_robot/worlds\nros2 launch assem2_robot civil_simulation.launch.py use_nav:=true use_gui:=true \\\n        world:=$W/civil_world_slip.sdf slip_correction:=true",ACODE),
 p("The Wheel Slip Monitor on the Ground Station shows the slip percentage, the wheel and ground speed, the traction scale and the surface under the robot. The three blue hatched boxes on the map are the low-friction patches. The slip topics can be read directly:"),
 Preformatted("ros2 topic echo /slip/active            # True while slip is detected\nros2 topic echo /slip/ratio             # slip ratio, -1 .. 1\nros2 topic echo /slip/traction_scale    # 1.0 = no limiting\nros2 topic echo /slip/correction_enabled   # latched: is the correction ON?",ACODE),
 h2("D. Patrol test, tour and other tools"),
 Preformatted("# patrol with verification (start the simulation first, in another terminal, then wait for localisation)\nsource ~/agilex/install/setup.bash\nros2 run assem2_robot civil_nav2_mission      # 20 legs; prints status, AMCL and ground-truth error\n\n# route-efficiency tour (seven direct goals)\npython3 ~/agilex/src/assem2_robot/scripts/nav_tour_test.py\n\n# keyboard teleoperation and SLAM mapping (first-stage tools)\n./run_teleop.sh\n./run_civil_mapping.sh && ./save_civil_map.sh\n\n# inspect the system\nros2 node list; ros2 topic list; rqt_graph; ros2 run tf2_tools view_frames",ACODE),
 h2("E. Headless runs and common problems"),
 *tab([["Symptom","Cause and remedy"],
  ["Robot does not move or the map pose jumps","Stale processes from an earlier run: run ./run_civil_nav.sh, which stops them first, and do not start two simulations in the same ROS domain"],
  ["Patrol shows 23 legs or ignores a change","The installed script is a copy: rebuild with colcon build --symlink-install"],
  ["Patrol stops at a station with a small position error","The mission checks the station heading within 40&deg; (Section 12)"],
  ["Gazebo or RViz2 cannot be screen-captured","Wayland blocks window capture; use the desktop screenshot tool by hand"],
  ["Slip is not detected on the patches","Check that the slip world was loaded (world:= argument) and that slip_control is running (ros2 node list)"]],[5.4*cm,10.4*cm],"Common problems and remedies."),
 p("For repeated headless tests the simulation was started with use_gui:=false and the mission run from a second script, which started a fresh simulation for every run and stopped all processes at the end (Section 9)."),
]
story+=[h1("9. Experimental method"),h2("A. Patrol test"),
 p("The patrol has 20 goals (legs) through the Conference Hall, the CAD Studio and the Materials Lab and back to the corridor hub (Appendix C lists the legs). Four legs are stations (Conference Hall, CAD Studio, Materials Lab, home) where the robot waits 2 s. The heading of each goal is the direction of travel from the previous waypoint. Each run starts from a freshly launched simulation with AMCL initialised at (0, 0). "
   "A leg succeeds when Nav2 reports success and both the AMCL pose and the Gazebo ground-truth pose are within 0.45 m of the goal; <b>at the four station legs the heading must also be within 40&deg; of the goal heading</b>, as in the original script, while at other legs the heading is only recorded. A failed leg is retried up to three times (costmaps cleared between attempts); a leg that fails all attempts ends the run; a leg times out after 120 s. "
   "Three conditions were run, three times each in the order normal, slip on, slip off (repeated): the normal floor; the slip floor with the correction on; and the slip floor with the correction off. Two earlier runs with the same script are also reported (Section 10-B). Everything ran headless on one computer. Times are wall-clock seconds from the first goal to the end of the run."),
 fig(S+"paper/../fix/route20.png",9.5*cm,"route","The 20-leg patrol on the occupancy map. The blue line joins the waypoints in order and is not the measured path."),
 h2("B. Route-efficiency tour"),
 p("To measure how close driven routes are to the shortest possible, a tour of seven goals (Materials Lab, CAD Studio, Geotechnical Lab, Archives Vault, Conference Hall, Foyer and hub, in that order) was sent as single direct goals, each snapped to at least 0.55 m from obstacles as in the Ground Station. The driven distance is the sum of displacements of the map&rarr;base_footprint transform sampled at about 5 Hz; it is compared with the length of an A* path on the map grid with 0.30 m clearance from the start of each leg. Because the transform comes from the localisation system, the driven distance includes localisation noise. The tour was run once on the normal floor and once on the slip floor with the correction on.")]
# 8 results
rows=[["Leg","Waypoint","Run 1 [m]","Run 2 [m]","Run 3 [m]","Mean AMCL error [m]","Max yaw error [&deg;]"]]
names=[l["name"].replace("STATION: ","Station: ") for l in P["normal_1"]["legs"]]
for k in range(20):
    L=[P[f"normal_{i}"]["legs"][k] for i in (1,2,3)]
    nm=names[k]; bold=nm.startswith(("Station","Home"))
    rows.append([str(k+1),("<b>%s</b>"%nm) if bold else nm]+[f2(l["truth"]) for l in L]+[f2(st.mean(l["amcl"] for l in L)),str(max(l["yaw"] for l in L))])
rows.append(["","<b>All legs</b>"]+[f2(st.mean(l["truth"] for l in P[f"normal_{i}"]["legs"])) for i in (1,2,3)]+[f2(N["ae_mean"]),str(N["ye_max"])])
nx=X["normal_x"]; sx=X["slip_on_x"]
nxt=[l["truth"] for l in nx["legs"] if l.get("ok")]
story+=[h1("10. Results"),h2("A. Normal floor (20-leg patrol)"),
 *tab(rows,[1.0*cm,5.6*cm,1.9*cm,1.9*cm,1.9*cm,2.4*cm,2.3*cm],"Ground-truth arrival error per leg, three normal-floor runs (bold = station legs).",size=7.8),
 p(f"All three runs completed all 20 legs without any retry, in {min(N['walls'])}&ndash;{max(N['walls'])} s. Arrival errors against ground truth averaged {f2(N['te_mean'])} m and never exceeded {f2(N['te_max'])} m (limit 0.45 m); the mean AMCL error was {f2(N['ae_mean'])} m. The mean heading error at arrival was {N['ye_mean']:.0f}&deg; and the maximum {N['ye_max']}&deg; (at a non-station leg, where heading is not checked). An additional normal-floor run made earlier with the same script also completed 20 of 20 legs ({nx['wall']} s, worst error {max(nxt):.2f} m)."),
 fig(UP+"fig_norm.png",13.5*cm,"errn","Arrival error at each leg of the three normal-floor runs (dots) and their mean (line)."),
 h2("B. All runs of the final configuration")]
allrows=[["Condition","Runs made","Completed 20/20","Not completed","Wall time of completed runs [s]"],
 ["Normal floor","4 (3 planned + 1 earlier)","4",'&ndash;',", ".join(str(w) for w in sorted(N["walls"]+[nx["wall"]]))],
 ["Slip floor, correction ON","4 (3 planned + 1 earlier)","3","1 stopped at leg 9 (CAD Studio station): heading error 45&ndash;46&deg; against the 40&deg; limit on all three attempts, position error 0.14 m",", ".join(str(w) for w in SO["walls"])],
 ["Slip floor, correction OFF","3","2","1 stopped at leg 4 after 44 s: the robot overshot the corridor hub by 0.61, 0.51 and 0.48 m (limit 0.45 m)",", ".join(str(w) for w in SF["walls"] if w>100)]]
story+=[*tab(allrows,[3.0*cm,3.0*cm,2.2*cm,6.5*cm,2.3*cm],"Every run made with the final navigation configuration and the mission script of this report."),
 p(f"The slip-floor run with the correction on that stopped at leg 9 is not a navigation failure: the robot was within 0.14 m of the goal, but Nav2 no longer controls the final heading (yaw tolerance 3.14 rad), so the station heading check is passed or failed by chance. Over the {st_n} station arrivals that passed, the heading error was up to {st_max}&deg; against the 40&deg; limit, so the check is satisfied with little margin, and one of the four slip-floor-ON station arrivals at leg 9 failed it. This is a weakness of the test, not of the robot, and it is discussed in Section 12."),
 h2("C. Slip floor: correction ON compared with OFF")]
cmp=[["Measure","Correction OFF","Correction ON"],
  ["Wheel command on a patch","Passes unchanged; wheels spin","Clamped to ground speed &plusmn; 0.12 m/s; traction scale reduced (64 % in Fig. "+str(FN("gson"))+")"],
  ["Odometry","Raw wheel odometry over-reports","Slip-corrected /odom_corrected (vx and vy)"],
  ["Planned runs completed",f"{SF['n']} of 3 (legs reached: {', '.join(map(str,SF['legs']))})",f"{SO['n']} of 3 (legs reached: {', '.join(map(str,SO['legs']))})"],
  ["Mean / worst arrival error (truth)",f"{f2(SF['te_mean'])} / {f2(SF['te_max'])} m",f"{f2(SO['te_mean'])} / {f2(SO['te_max'])} m"],
  ["Leg 4 (corridor hub), first arrival","Overshot the 0.45 m limit in 3 of 3 runs (0.46&ndash;0.61 m)","Within the limit in 3 of 3 runs"],
  ["Retries (attempts repeated)",f"{SF['ret']} (all at leg 4)",f"{SO['ret']} (all at leg 12, aborted by Nav2)"],
  ["Wall time of completed runs [s]","213, 243","300, 335, 402 (mean 346, against 220 on the normal floor)"]]
story+=[*tab(cmp,[4.6*cm,6.0*cm,6.4*cm],"Correction OFF against ON in the planned nine-run set."),
 fig(UP+"fig_err.png",15.5*cm,"err3","Ground-truth arrival error at each leg in the three conditions. Lines are the mean over the runs that reached the leg; dots are single runs."),
 fig(UP+"fig_time.png",15.5*cm,"time","Wall-clock time of the nine planned patrol runs; the hatched bar is the run with the correction off that stopped at leg 4."),
 fig(UP+"fig_legs.png",14*cm,"legs","Legs completed (of 20) in each planned patrol run."),
 p(f"With the correction on, all three planned runs completed and the worst arrival error was lower ({f2(SO['te_max'])} m against {f2(SF['te_max'])} m). The clearest difference is leg 4: with the correction off the robot slid past the corridor hub in all three runs after leaving the Conference Hall doorway patch. The correction costs time: the completed runs took 300&ndash;402 s against 198&ndash;251 s on the normal floor, and leg 12 (the west lane past the post, across both corridor patches) was aborted by Nav2 once or twice in every run before it succeeded on a retry; the cause was not investigated. With three runs per condition the difference in completion (3 of 3 against 2 of 3) is not statistically significant; the leg-4 overshoot, in all three uncorrected runs and in none of the others, is the more reliable signal."),
 h2("D. Route efficiency")]
def trows(R,t):
    nm={1:"Foyer",2:"Hub",3:"Materials Lab",4:"Conference Hall",5:"CAD Studio",6:"Archives Vault",7:"Geotechnical Lab"}
    rr=[["Goal","Status","Driven [m]","Optimal [m]","Excess","Time [s]","Arrival error [m]"]]
    for r in R: rr.append([f"S{r['k']} {nm[r['k']]}",r['st'],f"{r['drv']:.1f}",f"{r['opt']:.1f}",f"{r['pct']:+d} %",str(r['t']),f2(r['err'])])
    rr.append(["<b>Total</b>","","%.1f"%t[0],"%.1f"%t[1],"%+.1f %%"%(100*(t[0]/t[1]-1)),"",""]); return rr
story+=[*tab(trows(TN,TNt),[3.6*cm,1.6*cm,2.2*cm,2.3*cm,2.0*cm,1.8*cm,3.0*cm],"Route-efficiency tour, normal floor (status 4 = Nav2 reported success).",size=7.8),
 *tab(trows(TS,TSt),[3.6*cm,1.6*cm,2.2*cm,2.3*cm,2.0*cm,1.8*cm,3.0*cm],"Route-efficiency tour, slip floor with the correction on.",size=7.8),
 p(f"Every goal was reached on both floors and the driven distance was between &minus;3 % and +6 % of the grid reference per leg and +{100*(TNt[0]/TNt[1]-1):.1f} % ({TNt[0]:.1f} m against {TNt[1]:.1f} m) over the whole normal-floor tour and +{100*(TSt[0]/TSt[1]-1):.1f} % on the slip floor. Negative values are possible because the reference keeps 0.30 m from obstacles and the measured distance comes from a sampled, filtered pose. Route length is therefore not the reason for the longer slip-floor patrol times. On the slip floor the Geotechnical Lab leg (S7) needed 67 s against 33 s for almost the same distance, so the extra time was spent driving slowly or pausing; this was not analysed."),
 h2("E. Earlier slip results (recorded with earlier code and patch layouts)"),
 *tab([["Measure","Correction OFF","Correction ON"],["Earlier 23-goal patrol, earlier layouts","3, 3, 3 and 21 legs (4 runs; none complete)","23, 21, 23, 23, 21, 21 and 5 (7 runs; 3 complete)"],["Final layout, single 23-goal run","3 of 23","23 of 23"],["Largest map-pose error in an earlier-layout capture run","3.9 m","1.6 m"],["Straight-line test on the &mu; = 0.02 floor","+1.12 m","+0.04 m"]],[6.4*cm,5.3*cm,5.3*cm],"Earlier results, kept for reference. They came from the first recorded runs with earlier code and layouts and could not be repeated; they agree in direction with the new runs."),
 p("One further normal-floor run of the earlier 23-leg patrol, repeated on 10 November with the final Nav2 parameters, completed 23 of 23 legs in 193 s (worst truth error 0.32 m); it ran a stale installed copy of the script, which is why it had 23 legs.")]
# 9 problems
prob=[["#","Problem","Root cause","Fix"],
["1","Robot stopped at the edge of a patch","Raised tiles: a low-grip skid-steer robot cannot climb the edge; wheels spin and odometry keeps counting","Flush floor tiles with patch holes"],
["2","Edits of slip_control.py had no effect","CMake installs a copy of the script","colcon build --symlink-install after every edit"],
["3","Slip reported while stopped; correction stuck on","Estimate biased low after a stop (fusion pull, zero-velocity update while sliding, IMU drift)","Gated fusion, zero-velocity update only when quiet, latch breaker, energy bound"],
["4","Wheel speed ran away to 1.44 m/s","clamp(cmd, v_est &minus; m, v_est + m) could raise the command above the request","Target bounded between the request and the current output"],
["5","Robot slid sideways with no change in odometry","Wheel odometry cannot see lateral slip","Lateral speed estimated from the IMU and fused in the EKF"],
["6","Believed position drifted from the truth","Early version: wheel odometry over-reported on slip","Slip-corrected odometry in the EKF"],
["7","The argument world:= was ignored","The launch file used a fixed world path","The launch file uses the world argument"],
["8","Leftover Gazebo, RViz and static_transform_publisher processes corrupted TF","Processes of earlier runs were still running","Each run in its own process group, stopped by PID; checked before the next run"],
["9","Clicking a goal sent the robot elsewhere or failed; several clicks needed","Door-aligned waypoints forced long routes and a new click was ignored during a route","Single direct goal with route_id pre-emption"],
["10","Screenshots were black","Wayland does not allow screen capture by mss, PIL or the desktop D-Bus","Ground Station rendered off-screen with Qt; Gazebo through camera sensors; RViz2 window grabbed with xwd (XWayland)"],
["11","Panel said &ldquo;correction ACTIVE&rdquo; with the correction off","The GUI could not tell the mode","Latched /slip/correction_enabled topic"],
["12","Identical runs gave different results","Contact physics is not repeatable","Not fixed; all runs are reported"],
["13","Robot slid sideways into a corridor post","Heading error carried onto ice, where the robot cannot steer; the post leaves about 0.02 m clearance","Corridor patches moved to the dry hub side and made full width"],
["14","A second test simulation changed the results of the one already open","The launch file forced ROS_DOMAIN_ID 19","The launch file keeps an exported ROS_DOMAIN_ID; tests run in their own domain"],
["15","Patrol stalled for 120 s at the east door, three times","A forced goal heading made the robot rotate in place (bang-bang &plusmn;0.6 rad/s); runs also used a stale installed script","Forced heading removed and script rebuilt; discarded runs not reported"],
["16","Early theory (uneven grip) did not explain the slides","Real cause was heading error carried onto ice (problem 13)","Traced with recordings of true pose, command and path"],
["17","<b>New.</b> <i>ros2 run civil_nav2_mission</i> ran an old 23-leg script","The installed copy is not a symlink and was not rebuilt after the source changed","colcon build --symlink-install; check the installed file against the source before runs"],
["18","<b>New.</b> A run stopped at a station with the robot 0.14 m from the goal","Mission requires station heading &le; 40&deg; but Nav2 yaw tolerance is 3.14 rad, so heading is uncontrolled","Open: use a tighter yaw tolerance only on station goals, or check position only (13)"]]
story+=[h1("11. Problems solved"),
 p("Problems 1&ndash;16 were found while adding and testing slip; problems 17 and 18 were found on 10 November while re-measuring. Each is listed with its cause and fix, in the style of the first review."),
 *tab(prob,[0.8*cm,4.6*cm,6.0*cm,5.6*cm],"Problems met in the second review.",size=7.8),
 fig(IMG+"p36_1.png",11*cm,"p1","Problem 1: with the raised patch edge the true robot (black) stops at y = 1.57 m against the edge, while its odometry (orange, dashed) keeps counting and drifts to 2.88 m."),
 fig(IMG+"p36_0.png",11*cm,"p2","Problem 6: map-pose error in an early run before the correction was added in its final form; it passes the 0.45 m tolerance at about 45 s and reaches 1.34 m at 53 s."),
 fig(IMG+"p37_0.png",9.5*cm,"p3","Problem 13: old layout (a), the robot stops with a front corner on the post; final layout (b), the patch lies between the hub and the post and the true path stays clear.")]
# 10 discussion
story+=[h1("12. Discussion and limitations"),
 p("<b>What the measurements show.</b> On the normal floor the final configuration completed every run with ground-truth errors below 0.37 m. On the slip floor the correction kept all three planned runs complete, and its main visible effect was preventing the overshoot at leg 4. It slowed the patrol by about 1.6 times, and leg 12 needed retries in every run. The shortest-path change gave driven distances within about 2 % of the grid reference over a seven-goal tour."),
 p("<b>Limitations.</b>"),
 bl("Three planned runs per condition (two extra runs on the normal and slip-ON floors); contact physics is not exactly repeatable. Completion rates (3 of 3 against 2 of 3) are not statistically significant."),
 bl("Simulation only. The slip patches are of our own design and their placement affects the results. The real robot's motor and battery behaviour is not modelled."),
 bl("<b>Heading at the stations is not controlled</b> (yaw tolerance 3.14 rad) yet the patrol checks it within 40&deg;; one of the slip-ON runs failed that check at a position 0.14 m from the goal, and the passing stations reached up to 38&deg;. The pass rate therefore understates how reliably the robot reaches the position."),
 bl("Tour distances come from the localisation pose, not ground truth. The extra time on slip legs (S7: 67 s against 33 s) and the leg-12 aborts were not investigated."),
 bl("Not evaluated in the second review: keyboard teleoperation, SLAM mapping and the 10 m obstacle arena (not re-run after the final changes), moving obstacles, and the real robot."),
 h1("13. Conclusion and future work"),
 p(f"The Scout Mini model navigates a 20-leg patrol on a normal floor in {min(N['walls'])}&ndash;{max(N['walls'])} s per run with arrival errors below {f2(N['te_max'])} m. On a floor with three very slippery patches, the slip controller kept all three planned runs complete, while without it two of three completed and the robot slid past a goal in every run. Direct goal sending with route pre-emption replaced door-aligned routing, and the driven routes were within about 2 % of the shortest grid paths. The results come from a small number of simulated runs."),
 p("<b>Future work:</b> repeat the patrol many more times and over several patch layouts; investigate the leg-12 aborts; control or ignore the heading at stations (for example a tighter yaw tolerance only on station goals, or a position-only check); calibrate the odometry for skid-steer slip; use NavigateThroughPoses for smoother motion; monitor AMCL covariance instead of ground truth; and repeat the tests on the physical Scout Mini.")]
# Appendices
story+=[PageBreak(),h1("Appendix A. Key parameters"),
 *tab([["Item","Value (file)"],
 ["Planner","nav2_smac_planner::SmacPlanner2D, tolerance 0.25 m, max planning time 2 s, cost_travel_multiplier 1.0 (nav2_params.yaml)"],
 ["Controller","RotationShimController (angular_dist_threshold 0.52 rad) &rarr; RegulatedPurePursuit, desired speed 0.60 m/s, look-ahead 0.25&ndash;0.60 m"],
 ["Goal checker","xy_goal_tolerance 0.20 m, yaw_goal_tolerance 3.14 rad"],
 ["Costmaps","resolution 0.05 m, inflation radius 0.55 m, footprint 0.66 &times; 0.70 m, local window 4 &times; 4 m (5 Hz), global 1 Hz"],
 ["Velocity smoother","max 0.70 m/s and 1.0 rad/s; accel 1.0 m/s&sup2;, 6.0 rad/s&sup2;; decel &minus;1.5 m/s&sup2;, &minus;6.0 rad/s&sup2;; collision monitor polygon disabled"],
 ["AMCL","1000&ndash;4000 particles, laser range 0.55&ndash;16 m, &sigma;<sub>hit</sub> 0.20, z<sub>hit</sub> 0.9, z<sub>rand</sub> 0.05, &alpha;<sub>1</sub> 0.30 and &alpha;<sub>2..5</sub> 0.10"],
 ["EKF","20 Hz, 2D; odom vx and IMU yaw rate (ekf.yaml); /odom_corrected with slip control"],
 ["slip_control","enter 0.15 m/s, exit 0.06 m/s, debounce 0.05 s, wheel lead 0.12 m/s, hold 0.6 s, linear accel 4.0 m/s&sup2; (0.8 declared, unused), angular accel 6.0 (3.0 while limiting) rad/s&sup2;, yaw gain 0.4, yaw limit 0.6 rad/s, dead-bands 0.04 / 0.03 m/s"],
 ["Slip patches","three flush patches, &mu; = 0.04 (civil_world_slip.sdf)"],
 ["Mission checks","position within 0.45 m by AMCL and ground truth; station heading within 40&deg;; 3 attempts per leg; 120 s per leg"]],[3.4*cm,13.6*cm],"Parameters used in the experiments."),
 h1("Appendix B. Reproducing the results"),
 Preformatted("cd ~/agilex && colcon build --symlink-install    # installs the 20-leg mission\n"
 "W=$HOME/agilex/install/assem2_robot/share/assem2_robot/worlds\n\n"
 "# normal floor (second terminal runs the mission)\n./run_civil_nav.sh\nros2 run assem2_robot civil_nav2_mission\n\n"
 "# slip floor, correction on / off\n"
 "ros2 launch assem2_robot civil_simulation.launch.py use_nav:=true \\\n    world:=$W/civil_world_slip.sdf slip_correction:=true\n"
 "ros2 launch assem2_robot civil_simulation.launch.py use_nav:=true \\\n    world:=$W/civil_world_slip.sdf slip_correction:=false",CODE),
 p("The tour is scripts/nav_tour_test.py. The raw mission logs, tour logs, per-leg data (patrol.json) and the scripts that built this report are in docs/experiment_logs/ and docs/review_build/."),
 h1("Appendix C. The 20 patrol legs")]
legs=[]
src=open("/home/sailakshmi/agilex/src/assem2_robot/scripts/civil_nav2_mission.py").read().split("MISSION = [")[1].split("\n]")[0]
for m in re.finditer(r'\("([^"]*)",\s*(-?[\d.]+),\s*(-?[\d.]+),\s*(-?[\d.]+),\s*(True|False)\)',src): legs.append(m.groups())
assert len(legs)==20
story+=[*tab([["Leg","Waypoint","x [m]","y [m]","Station (2 s, heading checked)"]]+[[str(i+1),n,x,y,"yes" if s=="True" else ""] for i,(n,x,y,h,s) in enumerate(legs)],[1.2*cm,7.0*cm,2.2*cm,2.2*cm,4.4*cm],"Waypoints of the patrol (civil_nav2_mission.py).",size=7.8),
 h1("Appendix D. Results of every planned run, leg by leg")]
hdr=["Leg","N1","N2","N3","ON1","ON2","ON3","OFF1","OFF2","OFF3"]
rows=[hdr]
for k in range(20):
    r=[str(k+1)]
    for c in ("normal","slip_on","slip_off"):
        for i in (1,2,3):
            L=P[f"{c}_{i}"]["legs"]
            if k<len(L) and L[k].get("ok"): r.append(f2(L[k]["truth"])+("*" if L[k]["retries"] else ""))
            elif k<len(L): r.append("fail")
            else: r.append("&ndash;")
    rows.append(r)
story+=[*tab(rows,[1.1*cm]+[1.7*cm]*9,"Ground-truth arrival error [m] per leg for the nine planned runs (N = normal, ON/OFF = slip floor with correction on/off; * = needed a retry; fail = leg failed all attempts; &ndash; = not reached).",size=7.8)]
def foot(cv,doc):
    cv.setLineWidth(0.8); cv.rect(0.85*cm,0.85*cm,A4[0]-1.7*cm,A4[1]-1.7*cm)
    cv.setFont("Serif",10); cv.drawCentredString(A4[0]/2,1.6*cm,str(doc.page))
doc=Doc(OUT,pagesize=A4,leftMargin=2.5*cm,rightMargin=2.5*cm,topMargin=2.2*cm,bottomMargin=2.4*cm,title="AgileX Scout Mini Navigation using ROS 2 (Second Review)",author="Sailakshmi BT")
doc.addPageTemplates([PageTemplate(id="p",frames=[Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,id="f")],onPage=foot)])
fl=[]
for x in story:
    fl.extend(x) if isinstance(x,list) else fl.append(x)
doc.build(fl); json.dump(PAGES,open(PF,'w')); print("built",doc.page,"pages")
