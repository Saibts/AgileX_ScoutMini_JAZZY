import re,subprocess,collections
txt=open("rqt_info.txt").read().split("=== ")[1:]
drop_nodes=("launch_ros","transform_listener","nav2_container","lifecycle_manager","rclcpp_node","docking_server","route_server","waypoint_follower","behavior_server")
drop_topic=("/clock","/tf","parameter_events","rosout","/bond","_action/","transition_event","/diagnostics")
pubs=collections.defaultdict(set);subs=collections.defaultdict(set)
for blk in txt:
    lines=blk.split("\n");n=lines[0].strip()
    if any(d in n for d in drop_nodes) or not n.startswith("/"): continue
    sec=None
    for l in lines[1:]:
        l=l.rstrip()
        if l.strip().endswith(":") and not l.startswith("    "):
            sec=l.strip()[:-1]; continue
        m=re.match(r"\s+(/\S+): ",l)
        if not m: continue
        t=m.group(1)
        if any(d in t for d in drop_topic): continue
        if sec=="Publishers": pubs[n].add(t)
        elif sec=="Subscribers": subs[n].add(t)
topics=set()
for n in pubs: topics|=pubs[n]
for n in subs: topics|=subs[n]
# keep only topics with at least one pub and one sub among kept nodes
tp={t for t in topics if any(t in pubs[n] for n in pubs) and any(t in subs[n] for n in subs)}
nodes={n for n in list(pubs)+list(subs) if any(t in tp for t in pubs[n]|subs[n])}
colors={"/slip_control":"#E8A0A0","/ros_gz_bridge":"#F5D58A","/ekf_filter_node":"#BFD9F2","/amcl":"#BFD9F2"}
d=['digraph G{rankdir=TB;ranksep=0.55;nodesep=0.3;fontname="Helvetica";node [fontname="Helvetica",fontsize=11];edge [color="#444444",arrowsize=0.7];']
for n in sorted(nodes): d.append(f'"{n}" [shape=ellipse,style=filled,fillcolor="{colors.get(n,"#DDEBDD")}",penwidth={2.2 if n=="/slip_control" else 1}];')
for t in sorted(tp): d.append(f'"{t}" [shape=box,style=filled,fillcolor="#FFFFFF",fontsize=10];')
for n in nodes:
    for t in pubs[n]&tp: d.append(f'"{n}" -> "{t}";')
    for t in subs[n]&tp: d.append(f'"{t}" -> "{n}";')
d.append("}")
open("slipgraph.dot","w").write("\n".join(d))
print(len(nodes),len(tp))
