import subprocess,math,time,os,sys
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np, cv2
O="/tmp/claude-1000/-home-sailakshmi-agilex/80964e52-a16b-4d32-81fe-b938023fbc80/scratchpad/gzshots/"
CAMS={
 "top_north":(0,0,27,1.5708,1.5708,1.25),
 "robot_patches":(0,-2.6,2.6,1.5708,0.55,1.15),
 "robot_side":(-2.6,-1.6,1.7,0.62,0.38,1.0),
 "hub_wide":(0,-7.5,6.5,1.5708,0.52,1.25),
}
def sdf(n,x,y,z,yaw,p,fov):
    return f'''<sdf version="1.9"><model name="cam_{n}"><static>true</static><pose>{x} {y} {z} 0 {p} {yaw}</pose><link name="l"><sensor name="c" type="camera"><camera><horizontal_fov>{fov}</horizontal_fov><image><width>1600</width><height>1000</height><format>R8G8B8</format></image><clip><near>0.1</near><far>80</far></clip></camera><always_on>1</always_on><update_rate>2</update_rate><visualize>false</visualize><topic>cam_{n}</topic></sensor></link></model></sdf>'''
for n,(x,y,z,yaw,p,fov) in CAMS.items():
    s=sdf(n,x,y,z,yaw,p,fov).replace('"','\\"')
    r=subprocess.run(["gz","service","-s","/world/amr_world/create","--reqtype","gz.msgs.EntityFactory","--reptype","gz.msgs.Boolean","--timeout","5000","--req",f'sdf: "{s}"'],capture_output=True,text=True); print(n,r.stdout.strip(),r.stderr.strip()[:100],flush=True)
bridges=[f"/cam_{n}@sensor_msgs/msg/Image[gz.msgs.Image" for n in CAMS]
bp=subprocess.Popen(["ros2","run","ros_gz_bridge","parameter_bridge"]+bridges,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
rclpy.init(); node=Node("capcam"); got={}
def mk(n):
    def cb(m):
        if n in got: return
        a=np.frombuffer(bytes(m.data),dtype=np.uint8).reshape(m.height,m.width,3)
        cv2.imwrite(O+n+".png",cv2.cvtColor(a,cv2.COLOR_RGB2BGR)); got[n]=1; print("saved",n,flush=True)
    return cb
for n in CAMS: node.create_subscription(Image,f"/cam_{n}",mk(n),1)
t=time.time()
while time.time()-t<40 and len(got)<len(CAMS): rclpy.spin_once(node,timeout_sec=0.2)
bp.terminate()
