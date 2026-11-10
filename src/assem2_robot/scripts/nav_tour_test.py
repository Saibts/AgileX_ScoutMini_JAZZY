#!/usr/bin/env python3
"""Headless navigation tour used for the report results (not installed by CMake).

Usage (simulation already running, Nav2 active, robot at the origin):
    python3 nav_tour_test.py 1,3,4,5,6,7,1
Each number is a station (S1..S7). For every leg it sends a NavigateToPose goal (snapped 0.55 m
from obstacles like the Ground Station), logs status, driven distance (map->base_footprint),
the A* shortest path on civil_map.pgm at 0.30 m clearance, time and arrival error.
"""
import math,sys,time,heapq,rclpy,numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.parameter import Parameter
from nav2_msgs.action import NavigateToPose
from tf2_ros import Buffer,TransformListener
im=np.array(Image.open('/home/sailakshmi/agilex/src/assem2_robot/maps/civil_map.pgm').convert('L'));H=im.shape[0]
d=distance_transform_edt(im>=250)*.05
free=np.argwhere(d>=0.55)
rc=lambda x,y:(H-1-int(round((y+9)/.05)),int(round((x+11)/.05)))
def safe(x,y):
    i=free[np.argmin(((free-list(rc(x,y)))**2).sum(1))];return i[1]*.05-11,(H-1-i[0])*.05-9
def opt(a,b,rad=0.30):
    ok=d>=rad;s,g=rc(*a),rc(*b);q=[(0,s)];best={s:0}
    while q:
        f,u=heapq.heappop(q)
        if u==g:return best[u]*.05
        for dr in(-1,0,1):
            for dc in(-1,0,1):
                if dr==dc==0:continue
                v=(u[0]+dr,u[1]+dc)
                if not ok[v]:continue
                c=best[u]+math.hypot(dr,dc)
                if c<best.get(v,1e9):best[v]=c;heapq.heappush(q,(c+math.hypot(v[0]-g[0],v[1]-g[1]),v))
ST={1:(0,-3.5,90),2:(0,0,0),3:(-6,3.5,90),4:(0,2.7,90),5:(6,3.5,90),6:(5.5,-4.5,-90),7:(-5.5,-4.5,-90)}
rclpy.init();n=Node('tour',parameter_overrides=[Parameter('use_sim_time',Parameter.Type.BOOL,True)])
tb=Buffer();TransformListener(tb,n);ac=ActionClient(n,NavigateToPose,'navigate_to_pose')
def spin(s):
    e=time.time()+s
    while time.time()<e:rclpy.spin_once(n,timeout_sec=0.05)
def pose():
    try:t=tb.lookup_transform('map','base_footprint',rclpy.time.Time());return t.transform.translation.x,t.transform.translation.y
    except Exception:return None
ac.wait_for_server(120)
while pose() is None:spin(.5)
spin(3)
seq=[int(c) for c in sys.argv[1].split(',')]
cur=pose();tot=0;totopt=0
for k in seq:
    x,y,yaw=ST[k];sx,sy=safe(x,y);a=pose()
    o=opt(a,(sx,sy))
    g=NavigateToPose.Goal();g.pose.header.frame_id='map';g.pose.pose.position.x=float(sx);g.pose.pose.position.y=float(sy)
    yr=math.radians(yaw);g.pose.pose.orientation.z=math.sin(yr/2);g.pose.pose.orientation.w=math.cos(yr/2)
    f=ac.send_goal_async(g)
    while not f.done():spin(.05)
    h=f.result();r=h.get_result_async();t0=time.time();L=0;last=pose()
    while not r.done() and time.time()-t0<100:
        spin(.2);p=pose()
        if p:L+=math.dist(p,last);last=p
    st=r.result().status if r.done() else 'TIMEOUT'
    if st=='TIMEOUT':h.cancel_goal_async();spin(1)
    e=math.dist(pose(),(sx,sy));tot+=L;totopt+=o or 0
    print("S%d goal(%.2f,%.2f) status %s driven %.1f m optimal %.1f m (+%.0f%%) time %.0fs arrival err %.2f m"%(k,sx,sy,st,L,o or 0,100*(L/(o or 1)-1),time.time()-t0,e),flush=True)
print("TOTAL driven %.1f optimal %.1f"%(tot,totopt),flush=True)
