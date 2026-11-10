import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Rectangle,Circle
fig=plt.figure(figsize=(6.4,9.0),dpi=290); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,100); ax.set_ylim(0,140); ax.axis("off")
NAVY="#1F2A44"; RED="#B22222"; BLUE="#1B9AC4"
def box(cx,cy,w,h,t,fc="#F4F4F4",ec=NAVY,fs=7.2,tc=NAVY,lw=1.2,bold_first=True):
    ax.add_patch(FancyBboxPatch((cx-w/2,cy-h/2),w,h,boxstyle="round,pad=0,rounding_size=1.2",fc=fc,ec=ec,lw=lw,zorder=3))
    lines=t.split("\n")
    for i,l in enumerate(lines):
        y=cy+(len(lines)-1)/2*2.1-i*2.1
        ax.text(cx,y,l,ha="center",va="center",fontsize=fs if i==0 else fs-0.9,fontweight="bold" if i==0 else "normal",color=tc,zorder=4)
def cluster(x0,y0,x1,y1,t,ec=NAVY,ls="-",lw=1.8,fs=8):
    ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fc="none",ec=ec,lw=lw,ls=ls,zorder=1)); ax.text(x0+1.2,y1-1.8,t,fontsize=fs,fontweight="bold",color=ec if ec!=NAVY else NAVY,va="center",zorder=2)
def arrow(pts,c=NAVY,ls="-",lw=1.2,head=True):
    for a,b in zip(pts[:-2],pts[1:-1]): ax.plot([a[0],b[0]],[a[1],b[1]],color=c,lw=lw,ls=ls,zorder=2)
    a,b=pts[-2],pts[-1]
    ax.annotate("",xy=b,xytext=a,arrowprops=dict(arrowstyle="-|>" if head else "-",color=c,lw=lw,ls=ls,shrinkA=0,shrinkB=0),zorder=2)
def num(x,y,n,c=NAVY):
    ax.add_patch(Circle((x,y),1.35,fc=c,ec="white",lw=0.8,zorder=6)); ax.text(x,y,str(n),color="white",fontsize=6.2,fontweight="bold",ha="center",va="center",zorder=7)
def lab(x,y,t,c=NAVY,ha="left",fs=6.3): ax.text(x,y,t,fontsize=fs,color=c,ha=ha,va="center",zorder=5,bbox=dict(fc="white",ec="none",pad=0.6))
C=[14,38,62,86]; W=21; H=8
cluster(1,122,99,138,"Gazebo Harmonic   (civil_world_slip.sdf, Scout Mini URDF)",lw=2.4)
G="#CFE8CF"
box(C[0],130,W,H,"LiDAR\n/scan 20 Hz",G); box(C[1],130,W,H,"IMU\n/imu 100 Hz",G); box(C[2],130,W,H,"RGB-D camera\n/camera 30 Hz",G); box(C[3],130,W,H,"DiffDrive\nwheels, /odom 50 Hz",G)
cluster(1,5,99,118,"ROS 2 Jazzy",lw=2.4)
box(14,108,W+2,8,"robot_state_publisher\nTF from URDF","#EEEEEE")
box(50,108,26,8,"ros_gz_bridge\ntopic bridge","#D9C8F5")
cluster(2,73,98,100,"State estimation",ec=BLUE,ls="--",lw=1.6)
box(C[0],86,W,H,"map_server\ncivil_map",G); box(C[1],86,W,H,"AMCL\nscan vs map","#C5CCF2"); box(C[2],86,W,H,"EKF (20 Hz)\n/odom_corrected + IMU","#C5CCF2")
box(C[3],86,W,H,"slip_control (new)\ndetect, limit, correct","#E8A0A0",ec=RED,tc="#7A1010",lw=2.2)
cluster(2,26,98,68,"Nav2 navigation stack",ec=BLUE,ls="--",lw=1.6)
box(C[0],56,W,H,"BT navigator\nNavigateToPose","#F6C6D0"); box(C[1],56,W,H,"Planner\nSmac 2D (A*)","#F6C6D0"); box(C[2],56,W,H,"Controller\nshim + pure pursuit","#F9D9A8"); box(C[3],56,W,H,"Velocity smoother\n0.7 m/s, 1.0 rad/s","#F9D9A8")
box(C[1],36,W,H,"Behaviours\nspin, back up, wait","#BFE8E0"); box(C[2],36,W,H,"Costmaps\ninputs /scan, /map",G); box(C[3],36,W,H,"Collision monitor\npass-through","#D5DAE0")
box(14,12,26,8,"Ground Station\nPyQt5, camera, slip panel","#D9C8F5"); ax.add_patch(Circle((50,12),4,fc="white",ec=NAVY,lw=1.2,zorder=3)); ax.text(50,12,"Operator",fontsize=6.5,ha="center",va="center",zorder=4,fontweight="bold")
# 1 sensors -> bridge
for x in C[:3]: arrow([(x,126),(x,121)],head=False)
arrow([(C[0],121),(50,121),(50,112)]); num(30,121,1); lab(53,121,"/scan  /imu  /camera  /clock")
# 12 bridge -> DiffDrive
arrow([(63,108),(93,108),(93,126)],c=RED,lw=1.8); num(78,108,12,RED); lab(80,110.5,"/cmd_vel_safe",RED)

# 2 bridge -> state estimation bus
arrow([(50,104),(50,100.5)],head=False); ax.plot([38,86],[100.5,100.5],color=NAVY,lw=1.2,zorder=2)
arrow([(38,100.5),(38,90)]); arrow([(62,100.5),(62,90)]); arrow([(89,100.5),(89,90)],c=RED)
num(44,100.5,2); lab(46,102.7,"/scan to AMCL   /imu to EKF   /imu, /odom to slip_control",fs=5.9)
# 11 slip -> bridge
arrow([(83,90),(83,104),(63,104)],c=RED,lw=1.8); num(83,96,11,RED); lab(65,105.4,"/cmd_vel_safe",RED,fs=5.8)
# 3 map -> AMCL ; 4 slip -> EKF
arrow([(24.5,86),(27.5,86)]); num(26,89.5,3); lab(26,82.2,"/map",ha="center",fs=5.8)
arrow([(75.5,86),(72.5,86)],c=RED,lw=1.8); num(74,89.5,4,RED); lab(74,82.2,"/odom_corrected",RED,ha="center",fs=5.6)
# 5 estimation -> Nav2
arrow([(38,82),(38,68.2)]); arrow([(62,82),(62,68.2)])
num(50,75.5,5); lab(10,70.8,"/odometry/filtered, TF odom to base_footprint (EKF);  TF map to odom (AMCL)",fs=5.5)
# nav chain
arrow([(24.5,56),(27.5,56)]); num(26,59.5,7); arrow([(48.5,56),(51.5,56)]); lab(41,52.2,"/plan",fs=5.8)
arrow([(72.5,56),(75.5,56)]); num(74,59.5,8); lab(64.5,52.2,"/cmd_vel_nav",fs=5.4)
arrow([(86,52),(86,40)]); num(86,46,9); lab(84.5,46,"/cmd_vel_smoothed",ha="right",fs=5.4)
# 10 collision -> slip
arrow([(96.5,36),(97.5,36),(97.5,86),(96.5,86)],c=RED,lw=1.8); num(97.5,60,10,RED); lab(96.5,63.8,"/cmd_vel",RED,ha="right",fs=5.8)
# 6 GS -> BT (straight) , operator
arrow([(14,16),(14,52)]); num(14,28,6); lab(15.5,32,"NavigateToPose\n(action goal)",fs=5.8)
arrow([(46,12),(27,12)],head=True); lab(36.5,14.3,"click, stations, E-stop",ha="center",fs=5.6)
arrow([(60,26),(60,22),(27,22),(27,16)],c=NAVY,ls="--",lw=1.0); num(44,22,13); lab(32,24.4,"/plan, /odometry/filtered, /camera/image_raw, /scan, /odom, /slip/*",fs=5.6)
lab(50,6.8,"Numbers give the order of the data flow (data-flow table).  Red = added or changed by the slip controller.",RED,ha="center",fs=6.3)
fig.savefig("arch_mpl.png",dpi=250,facecolor="white")
