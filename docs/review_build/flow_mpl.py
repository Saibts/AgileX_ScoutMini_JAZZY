import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Polygon
fig=plt.figure(figsize=(6.6,8.6),dpi=280); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,100); ax.set_ylim(0,130); ax.axis("off")
K="#222222"
def box(cx,cy,w,h,t,fc="#EEEEEE",fs=7.6):
    ax.add_patch(FancyBboxPatch((cx-w/2,cy-h/2),w,h,boxstyle="round,pad=0,rounding_size=1.6",fc=fc,ec="#444444",lw=1.3,zorder=3))
    L=t.split("\n")
    for i,l in enumerate(L): ax.text(cx,cy+(len(L)-1)/2*2.7-i*2.7,l,ha="center",va="center",fontsize=fs,zorder=4,color="black")
def arr(p,q,lw=1.4):
    ax.annotate("",xy=q,xytext=p,arrowprops=dict(arrowstyle="-|>",color=K,lw=lw,shrinkA=0,shrinkB=0),zorder=2)
def line(p,q): ax.plot([p[0],q[0]],[p[1],q[1]],color=K,lw=1.4,zorder=2)
X=50
box(X,123,86,7.5,"1. Nav2 command /cmd_vel (v_cmd, ω_cmd)\nfrom the collision monitor, after the velocity smoother","#FFE6C8")
box(X,111,86,7.5,"2. slip_control reads the command, the wheel speed v_w (/odom)\nand the IMU (acceleration, yaw rate)")
box(X,99,86,7.5,"3. IMU acceleration (gravity removed) is integrated into the ground\nspeed v_est; blended with v_w only while they agree")
box(X,87.5,86,6,"4. Slip speed Δv = v_w - v_est     slip ratio s = Δv / max(|v_w|, 0.2)")
for a,b in [(119.2,114.8),(107.2,102.8),(95.2,90.7)]: arr((X,a),(X,b))
# diamond
cy=72; ax.add_patch(Polygon([(X,cy+9),(X+34,cy),(X,cy-9),(X-34,cy)],closed=True,fc="#FFF0B8",ec="#8A7420",lw=1.4,zorder=3))
ax.text(X,cy+1.6,"5. Limiting?  |Δv| > 0.15 m/s for 0.05 s",ha="center",va="center",fontsize=7.4,zorder=4)
ax.text(X,cy-1.8,"(clears below 0.06 m/s; held 0.6 s after)",ha="center",va="center",fontsize=6.8,zorder=4)
arr((X,84.5),(X,cy+9.2))
# branches
box(78,52,40,13,"6a. Traction limiter\nv_target = clamp(v_cmd, v_est ± 0.12)\nnever above request or current output\nangular accel limit halved","#F8D4D4",fs=6.9)
box(22,52,40,13,"6a'. No limiting\nv_target = v_cmd","#DCEBD2",fs=7.2)
line((X+34,cy),(78,cy)); arr((78,cy),(78,58.7)); ax.text(82,cy-6,"yes",fontsize=7.2)
line((X-34,cy),(22,cy)); arr((22,cy),(22,58.7)); ax.text(14,cy-6,"no",fontsize=7.2)
# merge
line((78,45.5),(78,41.5)); line((22,45.5),(22,41.5)); line((22,41.5),(78,41.5)); arr((X,41.5),(X,38.2))
box(X,33,90,10,"6b. Always: heading hold  ω_out = ω_cmd + clamp(0.4 (ω_cmd - ω_imu), ±0.6)\nslew-limit (4.0 m/s², 6.0 rad/s²)  →  publish /cmd_vel_safe (50 Hz)","#F8D4D4",fs=7.1)
box(X,19.5,90,12,"6c. Always, on every /odom message: odometry correction\nif |Δv| > 0.04:  v_corr = v_w - sign(Δv)(|Δv| - 0.04)   (never flips direction)\nsideways speed v_y from the IMU lateral channel  →  /odom_corrected","#F8D4D4",fs=7.0)
ax.text(X,26.4,"in parallel with 6b",fontsize=6.4,ha="center",color="#555555",style="italic",bbox=dict(fc="white",ec="none",pad=0.4),zorder=5)
box(X,6,90,8,"7. /cmd_vel_safe drives the Gazebo wheels near peak grip; /odom_corrected goes\nto the EKF; AMCL keeps the map pose;  8. next control cycle","#DCEBD2",fs=7.1)
arr((X,13.5),(X,10.2))
fig.savefig("flow_mpl.png",dpi=280,facecolor="white")
