import os,sys,time
os.environ["QT_QPA_PLATFORM"]="offscreen"
import rclpy
from python_qt_binding.QtWidgets import QApplication
from python_qt_binding.QtCore import QObject
from python_qt_binding.QtGui import QImage,QPainter
from rqt_graph.ros_graph import RosGraph
out=sys.argv[1]
rclpy.init(); node=rclpy.create_node("rqt_shot"); app=QApplication([])
class Ctx(QObject):
    def __init__(s):
        super().__init__(); s.node=node; s.w=None
    def serial_number(s): return 1
    def add_widget(s,w): s.w=w
class FS:
    def value(s,k,d=None,*a,**kw): return d
ctx=Ctx(); g=RosGraph(ctx); w=ctx.w; w.resize(1900,1000); w.show(); g.restore_settings(None,FS())
def spin(sec):
    t=time.time()
    while time.time()-t<sec:
        rclpy.spin_once(node,timeout_sec=0.05); app.processEvents()
spin(3); g._update_rosgraph(); spin(5)
NODEI=".*(slip_control|ros_gz_bridge|ekf_filter_node|amcl|map_server|velocity_smoother|collision_monitor|controller_server|planner_server|bt_navigator$|robot_state_publisher|local_costmap$|global_costmap$|smoother_server).*"
TOPX="-.*(/tf|bond|_action|costmap_raw|footprint|parameter_events|rosout|transition_event|diagnostics|speed_limit|selector|robot_description|initialpose|goal_pose).*"
cb=w.graph_type_combo_box
def render(name,mode,nodef,topf):
    for i in range(cb.count()):
        if cb.itemText(i)==mode: cb.setCurrentIndex(i)
    w.filter_line_edit.setText(nodef); w.topic_filter_line_edit.setText(topf)
    g._refresh_rosgraph(); spin(3); g._fit_in_view(); spin(1)
    w.grab().save(f"{out}_{name}_window.png")
    img=QImage((g._scene.sceneRect().size()*2.0).toSize(),QImage.Format_ARGB32_Premultiplied); img.fill(0xffffffff)
    p=QPainter(img);p.setRenderHint(QPainter.Antialiasing);g._scene.render(p);p.end();img.save(f"{out}_{name}_scene.png"); print(name,img.width(),img.height(),flush=True)
render("all","Nodes/Topics (all)",NODEI,TOPX)
render("nodes","Nodes only",NODEI,TOPX)
render("active","Nodes/Topics (active)",NODEI,TOPX)
# top-to-bottom layout of the same rqt_graph dotcode (portrait page)
w.filter_line_edit.setText(NODEI); w.topic_filter_line_edit.setText(TOPX)
for i in range(cb.count()):
    if cb.itemText(i)=="Nodes/Topics (all)": cb.setCurrentIndex(i)
g._refresh_rosgraph(); spin(2)
dc=g._current_dotcode; open(out+"_all.dot","w").write(dc); print([l for l in dc.split("\n") if "rankdir" in l or "ranksep" in l][:3],flush=True)
dc2=dc.replace("rankdir=LR","rankdir=TB").replace('rankdir="LR"','rankdir="TB"')
if "rankdir" not in dc2: dc2=dc2.replace("{","{\nrankdir=TB;",1)
g._current_dotcode=dc2; g._redraw_graph_view(); spin(2); g._fit_in_view(); spin(1)
w.grab().save(f"{out}_tb_window.png")
img=QImage((g._scene.sceneRect().size()*2.0).toSize(),QImage.Format_ARGB32_Premultiplied); img.fill(0xffffffff)
p=QPainter(img);p.setRenderHint(QPainter.Antialiasing);g._scene.render(p);p.end();img.save(f"{out}_tb_scene.png"); print("tb",img.width(),img.height(),flush=True)
