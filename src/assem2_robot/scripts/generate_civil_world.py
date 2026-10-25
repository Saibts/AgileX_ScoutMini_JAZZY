#!/usr/bin/env python3
"""
Civil Architectural World & 2D Occupancy Map Generator for AgileX Scout Mini.
Generates:
1. src/assem2_robot/worlds/civil_world.sdf (Gazebo Harmonic 3D World)
2. src/assem2_robot/maps/civil_map.pgm & civil_map.yaml (Nav2 2D Occupancy Grid)
3. docs/images/civil_blueprint.png (High-resolution architectural drawing)
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

MAP_RES = 0.05  # 5 cm per pixel
WORLD_X_MIN, WORLD_X_MAX = -11.0, 11.0  # 22 m total
WORLD_Y_MIN, WORLD_Y_MAX = -9.0, 9.0    # 18 m total
ORIGIN_X, ORIGIN_Y = WORLD_X_MIN, WORLD_Y_MIN

MAP_W = int(round((WORLD_X_MAX - WORLD_X_MIN) / MAP_RES))  # 440 px
MAP_H = int(round((WORLD_Y_MAX - WORLD_Y_MIN) / MAP_RES))  # 360 px

# Coordinate conversion from world meters to map pixel (u, v) with (0,0) at bottom-left
def world_to_map(x, y):
    u = int(round((x - ORIGIN_X) / MAP_RES))
    v = int(round((y - ORIGIN_Y) / MAP_RES))
    return u, v

# Convert to image coordinate (row 0 is top)
def world_to_img(x, y):
    u, v = world_to_map(x, y)
    return u, MAP_H - 1 - v

# Define all structural boxes: [name, x, y, z, size_x, size_y, size_z, material_r, g, b]
WALLS = [
    # Perimeter
    ("wall_ext_north", 0.0, 8.0, 0.6, 20.2, 0.2, 1.2, 0.28, 0.32, 0.38),
    ("wall_ext_south", 0.0, -8.0, 0.6, 20.2, 0.2, 1.2, 0.28, 0.32, 0.38),
    ("wall_ext_west", -10.0, 0.0, 0.6, 0.2, 16.0, 1.2, 0.28, 0.32, 0.38),
    ("wall_ext_east", 10.0, 0.0, 0.6, 0.2, 16.0, 1.2, 0.28, 0.32, 0.38),

    # North Corridor Wall (y = +1.2), with doors at x in [-6.5, -5.3], [-0.7, 0.7], [5.3, 6.5]
    ("wall_n_corr_w", -8.25, 1.2, 0.6, 3.5, 0.2, 1.2, 0.45, 0.50, 0.55),
    ("wall_n_corr_mw", -3.0, 1.2, 0.6, 4.6, 0.2, 1.2, 0.45, 0.50, 0.55),
    ("wall_n_corr_me", 3.0, 1.2, 0.6, 4.6, 0.2, 1.2, 0.45, 0.50, 0.55),
    ("wall_n_corr_e", 8.25, 1.2, 0.6, 3.5, 0.2, 1.2, 0.45, 0.50, 0.55),

    # South Corridor Wall (y = -1.2), doors at [-6.5, -5.3], Open Atrium [-2.0, 2.0], [5.3, 6.5]
    ("wall_s_corr_w", -8.25, -1.2, 0.6, 3.5, 0.2, 1.2, 0.45, 0.50, 0.55),
    ("wall_s_corr_mw", -3.65, -1.2, 0.6, 3.3, 0.2, 1.2, 0.45, 0.50, 0.55),
    ("wall_s_corr_me", 3.65, -1.2, 0.6, 3.3, 0.2, 1.2, 0.45, 0.50, 0.55),
    ("wall_s_corr_e", 8.25, -1.2, 0.6, 3.5, 0.2, 1.2, 0.45, 0.50, 0.55),

    # North Wing Partitions (x = -2.5 and x = +2.5), doors at y in [4.0, 5.2]
    ("wall_part_n_w_low", -2.5, 2.6, 0.6, 0.2, 2.8, 1.2, 0.50, 0.55, 0.60),
    ("wall_part_n_w_high", -2.5, 6.6, 0.6, 0.2, 2.8, 1.2, 0.50, 0.55, 0.60),
    ("wall_part_n_e_low", 2.5, 2.6, 0.6, 0.2, 2.8, 1.2, 0.50, 0.55, 0.60),
    ("wall_part_n_e_high", 2.5, 6.6, 0.6, 0.2, 2.8, 1.2, 0.50, 0.55, 0.60),

    # South Wing Partitions (x = -2.5 and x = +2.5), doors at y in [-5.2, -4.0]
    ("wall_part_s_w_low", -2.5, -6.6, 0.6, 0.2, 2.8, 1.2, 0.50, 0.55, 0.60),
    ("wall_part_s_w_high", -2.5, -2.6, 0.6, 0.2, 2.8, 1.2, 0.50, 0.55, 0.60),
    ("wall_part_s_e_low", 2.5, -6.6, 0.6, 0.2, 2.8, 1.2, 0.50, 0.55, 0.60),
    ("wall_part_s_e_high", 2.5, -2.6, 0.6, 0.2, 2.8, 1.2, 0.50, 0.55, 0.60),

    # Reinforced Concrete Columns (RCC Structural Pillars)
    ("rcc_col_nw", -6.0, 4.6, 0.6, 0.45, 0.45, 1.2, 0.35, 0.35, 0.40),
    ("rcc_col_ne", 6.0, 4.6, 0.6, 0.45, 0.45, 1.2, 0.35, 0.35, 0.40),
    ("rcc_col_sw", -6.0, -4.6, 0.6, 0.45, 0.45, 1.2, 0.35, 0.35, 0.40),
    ("rcc_col_se", 6.0, -4.6, 0.6, 0.45, 0.45, 1.2, 0.35, 0.35, 0.40),
    ("atrium_col_l", -2.0, -1.2, 0.6, 0.35, 0.35, 1.2, 0.35, 0.35, 0.40),
    ("atrium_col_r", 2.0, -1.2, 0.6, 0.35, 0.35, 1.2, 0.35, 0.35, 0.40),

    # Furniture / Civil Equipment Obstacles
    ("conf_table", 0.0, 5.2, 0.38, 2.4, 1.2, 0.75, 0.55, 0.38, 0.22),
    ("mat_bench", -7.5, 5.8, 0.38, 2.2, 0.9, 0.75, 0.30, 0.45, 0.55),
    ("mat_press", -5.0, 2.6, 0.4, 1.0, 1.0, 0.8, 0.40, 0.42, 0.45),
    ("cad_island", 7.5, 5.8, 0.38, 2.2, 0.9, 0.75, 0.25, 0.40, 0.50),
    ("cad_rig", 5.0, 2.6, 0.4, 1.0, 1.0, 0.8, 0.38, 0.40, 0.45),
    ("archive_rack_1", 7.2, -6.0, 0.45, 2.0, 0.8, 0.9, 0.50, 0.45, 0.35),
    ("archive_rack_2", 7.2, -3.0, 0.45, 2.0, 0.8, 0.9, 0.50, 0.45, 0.35),
    ("geotech_bench", -7.2, -6.0, 0.38, 2.0, 0.8, 0.75, 0.45, 0.40, 0.30),
    ("soil_rig", -5.0, -2.8, 0.4, 1.0, 1.0, 0.8, 0.35, 0.40, 0.35),
    ("reception_desk", 0.0, -6.5, 0.45, 2.6, 0.7, 0.9, 0.60, 0.40, 0.25),
]

CYLINDERS = [
    # Circular Corridor Architectural Columns (30 cm diameter structural posts)
    ("corr_col_w", -4.0, 0.0, 0.6, 0.15, 1.2, 0.35, 0.35, 0.40),
    ("corr_col_e", 4.0, 0.0, 0.6, 0.15, 1.2, 0.35, 0.35, 0.40),
]


def generate_sdf(output_path):
    sdf_content = """<?xml version="1.0" ?>
<!-- ============================================================================== -->
<!-- Civil Architectural Engineering Building Simulation World (Gazebo Harmonic)   -->
<!-- Compatible with ROS 2 Jazzy & AgileX Scout Mini AMR Autonomous Navigation     -->
<!-- Reference: NIST Standard Civil Facility / Architectural Multi-Room Benchmark  -->
<!-- ============================================================================== -->
<sdf version="1.8">
  <world name="amr_world">
    <physics name="5ms" type="ignored">
      <max_step_size>0.005</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <!-- Essential Gazebo Harmonic System Plugins -->
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics" />
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands" />
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster" />
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu" />

    <!-- Lighting -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>2 2 15 0 0 0</pose>
      <diffuse>0.92 0.92 0.90 1</diffuse>
      <specular>0.25 0.25 0.25 1</specular>
      <attenuation>
        <range>1000</range>
        <constant>0.9</constant>
        <linear>0.01</linear>
        <quadratic>0.001</quadratic>
      </attenuation>
      <direction>-0.4 0.2 -0.9</direction>
    </light>

    <!-- Civil Floor Ground Plane -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>40 40</size>
            </plane>
          </geometry>
          <surface>
            <friction>
              <ode>
                <mu>1.0</mu>
                <mu2>1.0</mu2>
              </ode>
            </friction>
          </surface>
        </collision>
        <visual name="visual">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>40 40</size>
            </plane>
          </geometry>
          <material>
            <ambient>0.82 0.85 0.88 1</ambient>
            <diffuse>0.82 0.85 0.88 1</diffuse>
            <specular>0.15 0.15 0.15 1</specular>
          </material>
        </visual>
      </link>
    </model>
"""
    # Append Box Walls & Obstacles
    for name, x, y, z, sx, sy, sz, cr, cg, cb in WALLS:
        sdf_content += f"""
    <model name="{name}">
      <static>true</static>
      <pose>{x:.3f} {y:.3f} {z:.3f} 0 0 0</pose>
      <link name="link">
        <collision name="c">
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
        </collision>
        <visual name="v">
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          <material>
            <ambient>{cr:.2f} {cg:.2f} {cb:.2f} 1</ambient>
            <diffuse>{cr:.2f} {cg:.2f} {cb:.2f} 1</diffuse>
            <specular>0.1 0.1 0.1 1</specular>
          </material>
        </visual>
      </link>
    </model>"""

    # Append Cylinder Columns
    for name, x, y, z, radius, length, cr, cg, cb in CYLINDERS:
        sdf_content += f"""
    <model name="{name}">
      <static>true</static>
      <pose>{x:.3f} {y:.3f} {z:.3f} 0 0 0</pose>
      <link name="link">
        <collision name="c">
          <geometry><cylinder><radius>{radius:.3f}</radius><length>{length:.3f}</length></cylinder></geometry>
        </collision>
        <visual name="v">
          <geometry><cylinder><radius>{radius:.3f}</radius><length>{length:.3f}</length></cylinder></geometry>
          <material>
            <ambient>{cr:.2f} {cg:.2f} {cb:.2f} 1</ambient>
            <diffuse>{cr:.2f} {cg:.2f} {cb:.2f} 1</diffuse>
            <specular>0.1 0.1 0.1 1</specular>
          </material>
        </visual>
      </link>
    </model>"""

    # Spawning AgileX Scout Mini AMR Robot at Main Entrance Foyer
    sdf_content += """

    <!-- AgileX Scout Mini AMR Robot Model Spawn (Central Corridor Hub) -->
    <include>
      <uri>package://assem2_robot/urdf/Assem2.SLDASM.urdf</uri>
      <name>assem2_robot</name>
      <pose>0 0 0.02 0 0 1.5707963</pose>
    </include>

  </world>
</sdf>
"""
    with open(output_path, "w") as f:
        f.write(sdf_content)
    print(f"[OK] Generated Gazebo Harmonic World: {output_path}")


def generate_occupancy_grid(pgm_path, yaml_path):
    # Occupancy Grid: 254 = free (white), 0 = occupied (black), 205 = unknown (light grey)
    # Outside building: unknown (205)
    grid = np.full((MAP_H, MAP_W), 205, dtype=np.uint8)

    # Interior building free space: x in [-10.0, 10.0], y in [-8.0, 8.0]
    u_min, v_min = world_to_map(-10.0, -8.0)
    u_max, v_max = world_to_map(10.0, 8.0)
    # Image coords (r0 = top = max y, r1 = bottom = min y)
    r_top = MAP_H - 1 - v_max
    r_bot = MAP_H - 1 - v_min
    grid[r_top:r_bot, u_min:u_max] = 254  # Free space inside building

    # Stamp box walls onto grid (0 = occupied)
    for name, x, y, z, sx, sy, sz, cr, cg, cb in WALLS:
        hw_x = sx / 2.0
        hw_y = sy / 2.0
        u0, v0 = world_to_map(x - hw_x, y - hw_y)
        u1, v1 = world_to_map(x + hw_x, y + hw_y)
        
        # Clamp to bounds
        u0 = max(0, min(MAP_W - 1, u0))
        u1 = max(0, min(MAP_W - 1, u1))
        v0 = max(0, min(MAP_H - 1, v0))
        v1 = max(0, min(MAP_H - 1, v1))

        r0 = MAP_H - 1 - v1
        r1 = MAP_H - 1 - v0
        grid[r0:r1 + 1, u0:u1 + 1] = 0

    # Stamp cylinder columns onto grid
    for name, x, y, z, radius, length, cr, cg, cb in CYLINDERS:
        rad_px = int(round(radius / MAP_RES))
        u_c, v_c = world_to_map(x, y)
        r_c = MAP_H - 1 - v_c
        for dr in range(-rad_px, rad_px + 1):
            for dc in range(-rad_px, rad_px + 1):
                if dr * dr + dc * dc <= rad_px * rad_px:
                    r = r_c + dr
                    c = u_c + dc
                    if 0 <= r < MAP_H and 0 <= c < MAP_W:
                        grid[r, c] = 0

    # Save PGM image
    img = Image.fromarray(grid, mode='L')
    img.save(pgm_path)
    print(f"[OK] Generated 2D Occupancy Grid Image: {pgm_path}")

    # Generate YAML metadata
    yaml_content = f"""image: {os.path.basename(pgm_path)}
mode: trinary
resolution: {MAP_RES:.4f}
origin: [{ORIGIN_X:.3f}, {ORIGIN_Y:.3f}, 0.000000]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
"""
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
    print(f"[OK] Generated Nav2 Map Metadata YAML: {yaml_path}")


def generate_blueprint(blueprint_path):
    IMG_W, IMG_H = 1920, 1200
    MARGIN_X, MARGIN_Y = 160, 140

    BG_COLOR = (12, 28, 48)           # Deep Blueprint Navy Blue
    GRID_COLOR = (24, 48, 76)         # Subtle Blueprint Coordinate Grid
    WALL_COLOR = (240, 245, 255)      # White Architectural Walls
    PARTITION_COLOR = (140, 190, 240) # Cyan Partitions
    COLUMN_COLOR = (255, 200, 80)     # Yellow RCC Columns
    OBSTACLE_COLOR = (100, 160, 210)  # Equipment / Furniture
    TEXT_COLOR = (240, 248, 255)      # Pure White
    ACCENT_COLOR = (70, 220, 180)     # Teal / Mint Green
    WAYPOINT_COLOR = (255, 90, 95)    # Red / Coral Waypoints

    img = Image.new("RGB", (IMG_W, IMG_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    scale_x = (IMG_W - 2 * MARGIN_X) / 22.0
    scale_y = (IMG_H - 2 * MARGIN_Y) / 18.0
    scale = min(scale_x, scale_y)

    center_canvas_x = IMG_W / 2.0
    center_canvas_y = IMG_H / 2.0

    def to_canvas(x, y):
        cx = center_canvas_x + x * scale
        cy = center_canvas_y - y * scale
        return cx, cy

    # Draw Blueprint Grid Lines (every 2 meters)
    for gx in range(-10, 11, 2):
        x0, y0 = to_canvas(gx, -8.5)
        x1, y1 = to_canvas(gx, 8.5)
        draw.line([x0, y0, x1, y1], fill=GRID_COLOR, width=1)
        draw.text((x0 - 10, y0 + 5), f"{gx}m", fill=(70, 110, 150))

    for gy in range(-8, 9, 2):
        x0, y0 = to_canvas(-10.5, gy)
        x1, y1 = to_canvas(10.5, gy)
        draw.line([x0, y0, x1, y1], fill=GRID_COLOR, width=1)
        draw.text((x0 - 35, y0 - 8), f"{gy}m", fill=(70, 110, 150))

    # Draw Structural Walls
    for name, x, y, z, sx, sy, sz, cr, cg, cb in WALLS:
        hw_x = sx / 2.0
        hw_y = sy / 2.0
        p0_x, p0_y = to_canvas(x - hw_x, y + hw_y)
        p1_x, p1_y = to_canvas(x + hw_x, y - hw_y)
        
        if "ext" in name:
            fill_col = WALL_COLOR
            outline_col = (255, 255, 255)
        elif "rcc" in name or "atrium_col" in name:
            fill_col = COLUMN_COLOR
            outline_col = (255, 230, 140)
        elif "wall" in name:
            fill_col = PARTITION_COLOR
            outline_col = (200, 230, 255)
        else:
            fill_col = OBSTACLE_COLOR
            outline_col = (180, 220, 240)

        draw.rectangle([p0_x, p0_y, p1_x, p1_y], fill=fill_col, outline=outline_col, width=2)

    # Draw Cylinder Columns
    for name, x, y, z, radius, length, cr, cg, cb in CYLINDERS:
        cx, cy = to_canvas(x, y)
        r_px = radius * scale
        draw.ellipse([cx - r_px, cy - r_px, cx + r_px, cy + r_px], fill=COLUMN_COLOR, outline=(255, 240, 150), width=2)

    # Draw Room Labels & Functional Zones
    room_annotations = [
        ("MATERIALS TESTING LAB", -6.2, 7.2, ACCENT_COLOR),
        ("CIVIL CONFERENCE HALL", 0.0, 7.2, ACCENT_COLOR),
        ("CAD & ROBOTICS STUDIO", 6.2, 7.2, ACCENT_COLOR),
        ("MAIN CENTRAL CORRIDOR (2.4m)", 0.0, 0.7, (200, 220, 240)),
        ("GEOTECHNICAL SURVEY LAB", -6.2, -7.2, ACCENT_COLOR),
        ("ENTRANCE FOYER & ATRIUM", 0.0, -2.3, (255, 215, 100)),
        ("ARCHIVES & STORAGE VAULT", 6.2, -7.2, ACCENT_COLOR),
    ]

    for label, rx, ry, color in room_annotations:
        cx, cy = to_canvas(rx, ry)
        draw.text((cx - len(label) * 3.8, cy - 8), label, fill=color)

    # Draw Patrol Route & Waypoints in clear unobstructed open floor space
    waypoints = [
        ("WP 1 (Home Foyer)", 0.0, -3.8, 90.0),
        ("WP 2 (Corridor Hub)", 0.0, 0.0, 0.0),
        ("WP 3 (Materials Lab)", -7.0, 3.5, 90.0),
        ("WP 4 (Conference Hall)", 0.0, 3.0, 90.0),
        ("WP 5 (CAD Studio)", 7.0, 3.5, 90.0),
        ("WP 6 (Archives Vault)", 4.5, -4.8, 0.0),
        ("WP 7 (Geotechnical Lab)", -4.5, -5.0, 180.0),
    ]

    wp_canvas_coords = []
    for idx, (name, wx, wy, wyaw) in enumerate(waypoints):
        px, py = to_canvas(wx, wy)
        wp_canvas_coords.append((px, py))
        draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=WAYPOINT_COLOR, outline=(255, 255, 255), width=2)
        draw.text((px + 12, py - 8), f"#{idx+1} {name}", fill=(255, 200, 205))

    # Connect with dashed/solid route line
    for i in range(len(wp_canvas_coords) - 1):
        draw.line([wp_canvas_coords[i], wp_canvas_coords[i+1]], fill=(255, 120, 120), width=2)
    draw.line([wp_canvas_coords[-1], wp_canvas_coords[0]], fill=(255, 120, 120), width=2)

    # Architectural Blueprint Title Block (Bottom Right)
    tb_x0, tb_y0 = IMG_W - 460, IMG_H - 120
    tb_x1, tb_y1 = IMG_W - 30, IMG_H - 20
    draw.rectangle([tb_x0, tb_y0, tb_x1, tb_y1], fill=(16, 36, 60), outline=(100, 150, 200), width=2)
    draw.text((tb_x0 + 15, tb_y0 + 12), "AGILEX SCOUT MINI - CIVIL AMR ENVIRONMENT", fill=(255, 255, 255))
    draw.text((tb_x0 + 15, tb_y0 + 32), "Project: ROS 2 Jazzy & Gazebo Harmonic Simulation", fill=(180, 210, 240))
    draw.text((tb_x0 + 15, tb_y0 + 52), "Civil Facility: 20m x 16m Multi-Room Layout", fill=(180, 210, 240))
    draw.text((tb_x0 + 15, tb_y0 + 72), "Nav2 Map Resolution: 0.05m | Autonomous Patrol Stack", fill=(120, 220, 180))

    img.save(blueprint_path)
    print(f"[OK] Generated Architectural Blueprint PNG: {blueprint_path}")


if __name__ == "__main__":
    pkg_root = "/home/sailakshmi/agilex/src/assem2_robot"
    docs_root = "/home/sailakshmi/agilex/docs/images"
    os.makedirs(docs_root, exist_ok=True)

    sdf_out = os.path.join(pkg_root, "worlds", "civil_world.sdf")
    pgm_out = os.path.join(pkg_root, "maps", "civil_map.pgm")
    yaml_out = os.path.join(pkg_root, "maps", "civil_map.yaml")
    blueprint_out = os.path.join(docs_root, "civil_blueprint.png")

    generate_sdf(sdf_out)
    generate_occupancy_grid(pgm_out, yaml_out)
    generate_blueprint(blueprint_out)
    print("\n🎉 Civil Map Assets Generation Complete!")
