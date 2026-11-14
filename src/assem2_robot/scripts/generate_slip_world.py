#!/usr/bin/env python3
"""Create worlds/civil_world_slip.sdf: civil_world.sdf with flush low-friction floor patches.

Usage: python3 generate_slip_world.py [src.sdf] [dst.sdf]

The default floor collision (one big plane, mu = 1.0) is removed and replaced by flush ground
tiles (top surface at z = 0) that leave rectangular holes where the low-friction patches go.
Patches are flush too, so the robot rolls onto them without climbing a lip (a raised box with
mu = 0.04 cannot be climbed by a skid-steer base - the wheels just spin at the edge).
"""
import os
import re
import sys

PKG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HALF = 20.0     # floor half-size (m), matches the 40 x 40 ground plane
DEPTH = 0.2     # collision box thickness, top face at z = 0
# name, cx, cy, size_x, size_y, mu
PATCHES = [
    # Conference Hall doorway run (the patrol crosses it twice); spawn point stays on dry floor
    ('slip_patch_north', 0.0, 2.3, 1.2, 1.8, 0.04),
    # East / west corridor patches, between the hub and the corridor posts at x = +-4. They span
    # the full corridor width (both wheel sides get the same grip, no yaw moment from a partial
    # patch) and leave about 2.2 m of dry floor before the posts, so a heading error picked up
    # on the ice (where the robot cannot steer) can be corrected before the tight post chicane.
    ('slip_patch_east', 1.1, 0.0, 1.0, 2.4, 0.04),
    ('slip_patch_west', -1.1, 0.0, 1.0, 2.4, 0.04),
]


def subtract(rect, hole):
    """rect/hole = (x0, y0, x1, y1). Returns the pieces of rect not covered by hole."""
    x0, y0, x1, y1 = rect
    hx0, hy0, hx1, hy1 = hole
    if hx0 >= x1 or hx1 <= x0 or hy0 >= y1 or hy1 <= y0:
        return [rect]
    out = []
    if hy0 > y0: out.append((x0, y0, x1, hy0))                            # below
    if hy1 < y1: out.append((x0, hy1, x1, y1))                            # above
    ym0, ym1 = max(y0, hy0), min(y1, hy1)
    if hx0 > x0: out.append((x0, ym0, hx0, ym1))                          # left
    if hx1 < x1: out.append((hx1, ym0, x1, ym1))                          # right
    return out


def box(name, x0, y0, x1, y1, mu, visual=False):
    cx, cy, sx, sy = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    vis = ''
    if visual:
        vis = f"""
        <visual name="{name}_v">
          <pose>0 0 {DEPTH / 2 + 0.0015:.4f} 0 0 0</pose>
          <geometry><box><size>{sx:.3f} {sy:.3f} 0.003</size></box></geometry>
          <material><ambient>0.15 0.35 0.75 1</ambient><diffuse>0.15 0.35 0.75 1</diffuse>
            <specular>0.9 0.9 0.9 1</specular></material>
        </visual>"""
    return f"""
      <link name="{name}">
        <pose>{cx:.4f} {cy:.4f} {-DEPTH / 2:.4f} 0 0 0</pose>
        <collision name="{name}_c">
          <geometry><box><size>{sx:.4f} {sy:.4f} {DEPTH}</size></box></geometry>
          <surface><friction><ode><mu>{mu}</mu><mu2>{mu}</mu2></ode></friction></surface>
        </collision>{vis}
      </link>"""


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PKG, 'worlds', 'civil_world.sdf')
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PKG, 'worlds', 'civil_world_slip.sdf')
    with open(src) as f:
        sdf = f.read()

    # 1. drop the plane collision of the ground model (keep its visual)
    start = sdf.index('<model name="ground_plane">')
    c0 = sdf.index('<collision name="collision">', start)
    c1 = sdf.index('</collision>', c0) + len('</collision>')
    sdf = sdf[:c0] + sdf[c1:]

    # 2. flush floor tiles around the patches + the patches themselves
    tiles = [(-HALF, -HALF, HALF, HALF)]
    for _, cx, cy, sx, sy, _ in PATCHES:
        hole = (cx - sx / 2, cy - sy / 2, cx + sx / 2, cy + sy / 2)
        tiles = [t for r in tiles for t in subtract(r, hole)]
    links = ''.join(box(f'floor_{i}', *t, mu=1.0) for i, t in enumerate(tiles))
    links += ''.join(box(n, cx - sx / 2, cy - sy / 2, cx + sx / 2, cy + sy / 2, mu, visual=True)
                     for n, cx, cy, sx, sy, mu in PATCHES)
    model = f"""
    <!-- Flush floor tiles + low-friction slip patches -->
    <model name="slip_floor">
      <static>true</static>{links}
    </model>
"""
    marker = '</world>'
    assert marker in sdf, 'no </world> in source world'
    with open(dst, 'w') as f:
        f.write(sdf.replace(marker, model + '  ' + marker))
    print(f'[OK] wrote {os.path.abspath(dst)} ({len(tiles)} floor tiles, {len(PATCHES)} patches)')


if __name__ == '__main__':
    main()
