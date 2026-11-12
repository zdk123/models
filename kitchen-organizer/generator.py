import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import scriptcontext as sc
import math

# Kitchen Organizer Generator Script
print("=" * 60)
print("KITCHEN ORGANIZER GENERATOR")
print("=" * 60)

# Delete all existing objects to start fresh
print("\n[1/8] Clearing workspace...")
rs.Command("_SelAll _Delete", False)

# DIMENSIONS (in mm)
base_width = 206.0
base_depth = 83.0
base_height = 75.0
wall_thickness = 5.0
sponge_slot_width = 36.0
fillet_radius = 3.0
rib_spacing = 8.0
rib_depth = 1.5

# STEP 1: Create outer shell base box
print("\n[2/8] Creating outer shell base...")
base_corner = [0, 0, 0]
base_box = rs.AddBox([
    base_corner,
    [base_width, 0, 0],
    [base_width, base_depth, 0],
    [0, base_depth, 0],
    [0, 0, base_height],
    [base_width, 0, base_height],
    [base_width, base_depth, base_height],
    [0, base_depth, base_height]
])

# Fillet the vertical edges
print("   Adding rounded corners...")
edges = rs.DuplicateEdgeCurves(base_box)
box_edges = []
for edge_crv in edges:
    start = rs.CurveStartPoint(edge_crv)
    end = rs.CurveEndPoint(edge_crv)
    if abs(start[2] - end[2]) > 0.1:  # Vertical edges
        box_edges.append(edge_crv)
    rs.DeleteObject(edge_crv)

# Get edge indices for filleting
outer_shell = rs.coercebrep(base_box)
edge_indices = []
for i in range(outer_shell.Edges.Count):
    edge = outer_shell.Edges[i]
    line = edge.EdgeCurve
    start_pt = line.PointAtStart
    end_pt = line.PointAtEnd
    if abs(start_pt.Z - end_pt.Z) > 0.1:
        edge_indices.append(i)

if edge_indices:
    filleted = rg.Brep.CreateFilletEdges(outer_shell, edge_indices, [fillet_radius] * len(edge_indices), [fillet_radius] * len(edge_indices), rg.BlendType.Fillet, rg.RailType.DistanceFromEdge, 0.01)
    if filleted and len(filleted) > 0:
        rs.DeleteObject(base_box)
        base_box = sc.doc.Objects.AddBrep(filleted[0])

# STEP 2: Create hollow interior by shelling
print("\n[3/8] Creating hollow interior...")
inner_width = base_width - 2 * wall_thickness
inner_depth = base_depth - 2 * wall_thickness
inner_height = base_height - wall_thickness

inner_corner = [wall_thickness, wall_thickness, wall_thickness]
inner_box = rs.AddBox([
    inner_corner,
    [wall_thickness + inner_width, wall_thickness, wall_thickness],
    [wall_thickness + inner_width, wall_thickness + inner_depth, wall_thickness],
    [wall_thickness, wall_thickness + inner_depth, wall_thickness],
    [wall_thickness, wall_thickness, base_height],
    [wall_thickness + inner_width, wall_thickness, base_height],
    [wall_thickness + inner_width, wall_thickness + inner_depth, base_height],
    [wall_thickness, wall_thickness + inner_depth, base_height]
])

base_box = rs.BooleanDifference(base_box, inner_box, delete_input=True)[0]

# STEP 3: Create compartment dividers
print("\n[4/8] Adding interior divider walls...")

# Divider 1: Separates large sponge compartment (left half)
divider1_x = wall_thickness + inner_width * 0.5
divider1 = rs.AddBox([
    [divider1_x - wall_thickness/2, wall_thickness, wall_thickness],
    [divider1_x + wall_thickness/2, wall_thickness, wall_thickness],
    [divider1_x + wall_thickness/2, wall_thickness + inner_depth, wall_thickness],
    [divider1_x - wall_thickness/2, wall_thickness + inner_depth, wall_thickness],
    [divider1_x - wall_thickness/2, wall_thickness, base_height],
    [divider1_x + wall_thickness/2, wall_thickness, base_height],
    [divider1_x + wall_thickness/2, wall_thickness + inner_depth, base_height],
    [divider1_x - wall_thickness/2, wall_thickness + inner_depth, base_height]
])

# Divider 2: Splits right half into medium and small compartments
divider2_y = wall_thickness + inner_depth * 0.6
divider2 = rs.AddBox([
    [divider1_x + wall_thickness/2, divider2_y - wall_thickness/2, wall_thickness],
    [wall_thickness + inner_width, divider2_y - wall_thickness/2, wall_thickness],
    [wall_thickness + inner_width, divider2_y + wall_thickness/2, wall_thickness],
    [divider1_x + wall_thickness/2, divider2_y + wall_thickness/2, wall_thickness],
    [divider1_x + wall_thickness/2, divider2_y - wall_thickness/2, base_height],
    [wall_thickness + inner_width, divider2_y - wall_thickness/2, base_height],
    [wall_thickness + inner_width, divider2_y + wall_thickness/2, base_height],
    [divider1_x + wall_thickness/2, divider2_y + wall_thickness/2, base_height]
])

base_box = rs.BooleanUnion([base_box, divider1, divider2], delete_input=True)[0]

# STEP 4: Add diamond drainage pattern on bottom
print("\n[5/8] Adding diamond drainage mesh pattern...")

diamond_size = 8.0
diamond_hole_size = 4.0
drain_depth = wall_thickness * 0.7

drainage_cutters = []
start_x = wall_thickness + diamond_size
start_y = wall_thickness + diamond_size
end_x = wall_thickness + inner_width - diamond_size
end_y = wall_thickness + inner_depth - diamond_size

row = 0
y_pos = start_y
while y_pos < end_y:
    x_offset = (diamond_size / 2) if (row % 2 == 1) else 0
    x_pos = start_x + x_offset
    while x_pos < end_x:
        diamond_pts = [
            [x_pos, y_pos + diamond_hole_size/2, wall_thickness - drain_depth],
            [x_pos + diamond_hole_size/2, y_pos, wall_thickness - drain_depth],
            [x_pos, y_pos - diamond_hole_size/2, wall_thickness - drain_depth],
            [x_pos - diamond_hole_size/2, y_pos, wall_thickness - drain_depth],
            [x_pos, y_pos + diamond_hole_size/2, wall_thickness - drain_depth]
        ]
        diamond_curve = rs.AddPolyline(diamond_pts)
        if diamond_curve:
            diamond_surface = rs.AddPlanarSrf(diamond_curve)
            if diamond_surface:
                diamond_solid = rs.ExtrudeSurface(diamond_surface, rs.AddLine([0,0,0], [0,0,wall_thickness]))
                if diamond_solid:
                    drainage_cutters.append(diamond_solid)
                rs.DeleteObject(diamond_surface)
            rs.DeleteObject(diamond_curve)
        x_pos += diamond_size
    y_pos += diamond_size * 0.866  # Staggered rows
    row += 1

if drainage_cutters:
    base_box = rs.BooleanDifference(base_box, drainage_cutters, delete_input=True)[0]

# STEP 5: Add narrow sponge slot extension
print("\n[6/8] Adding narrow sponge slot extension...")

slot_extension_depth = 30.0
slot_inner_width = sponge_slot_width - 2 * wall_thickness
slot_height = base_height

# Outer extension box
slot_outer = rs.AddBox([
    [0, base_depth, 0],
    [sponge_slot_width, base_depth, 0],
    [sponge_slot_width, base_depth + slot_extension_depth, 0],
    [0, base_depth + slot_extension_depth, 0],
    [0, base_depth, slot_height],
    [sponge_slot_width, base_depth, slot_height],
    [sponge_slot_width, base_depth + slot_extension_depth, slot_height],
    [0, base_depth + slot_extension_depth, slot_height]
])

# Inner cavity for slot
slot_inner = rs.AddBox([
    [wall_thickness, base_depth + wall_thickness, wall_thickness],
    [wall_thickness + slot_inner_width, base_depth + wall_thickness, wall_thickness],
    [wall_thickness + slot_inner_width, base_depth + slot_extension_depth, wall_thickness],
    [wall_thickness, base_depth + slot_extension_depth, wall_thickness],
    [wall_thickness, base_depth + wall_thickness, slot_height],
    [wall_thickness + slot_inner_width, base_depth + wall_thickness, slot_height],
    [wall_thickness + slot_inner_width, base_depth + slot_extension_depth, slot_height],
    [wall_thickness, base_depth + slot_extension_depth, slot_height]
])

slot_outer = rs.BooleanDifference(slot_outer, slot_inner, delete_input=True)[0]

# Fillet the slot extension vertical edges
slot_brep = rs.coercebrep(slot_outer)
slot_edge_indices = []
for i in range(slot_brep.Edges.Count):
    edge = slot_brep.Edges[i]
    line = edge.EdgeCurve
    start_pt = line.PointAtStart
    end_pt = line.PointAtEnd
    if abs(start_pt.Z - end_pt.Z) > 0.1:
        slot_edge_indices.append(i)

if slot_edge_indices:
    filleted_slot = rg.Brep.CreateFilletEdges(slot_brep, slot_edge_indices, [fillet_radius] * len(slot_edge_indices), [fillet_radius] * len(slot_edge_indices), rg.BlendType.Fillet, rg.RailType.DistanceFromEdge, 0.01)
    if filleted_slot and len(filleted_slot) > 0:
        rs.DeleteObject(slot_outer)
        slot_outer = sc.doc.Objects.AddBrep(filleted_slot[0])

# Union with main body
base_box = rs.BooleanUnion([base_box, slot_outer], delete_input=True)[0]

# STEP 6: Add ribbed/fluted exterior
print("\n[7/8] Adding ribbed exterior texture...")

rib_width = 1.5
rib_count_width = int((base_width - 2 * wall_thickness) / rib_spacing)
rib_count_depth = int((base_depth - 2 * wall_thickness) / rib_spacing)

ribs = []

# Vertical ribs on front and back faces
for i in range(rib_count_width):
    x_pos = wall_thickness + (i + 0.5) * rib_spacing
    
    # Front face rib
    rib_front = rs.AddBox([
        [x_pos - rib_width/2, 0, 0],
        [x_pos + rib_width/2, 0, 0],
        [x_pos + rib_width/2, rib_depth, 0],
        [x_pos - rib_width/2, rib_depth, 0],
        [x_pos - rib_width/2, 0, base_height],
        [x_pos + rib_width/2, 0, base_height],
        [x_pos + rib_width/2, rib_depth, base_height],
        [x_pos - rib_width/2, rib_depth, base_height]
    ])
    if rib_front:
        ribs.append(rib_front)
    
    # Back face rib
    rib_back = rs.AddBox([
        [x_pos - rib_width/2, base_depth - rib_depth, 0],
        [x_pos + rib_width/2, base_depth - rib_depth, 0],
        [x_pos + rib_width/2, base_depth, 0],
        [x_pos - rib_width/2, base_depth, 0],
        [x_pos - rib_width/2, base_depth - rib_depth, base_height],
        [x_pos + rib_width/2, base_depth - rib_depth, base_height],
        [x_pos + rib_width/2, base_depth, base_height],
        [x_pos - rib_width/2, base_depth, base_height]
    ])
    if rib_back:
        ribs.append(rib_back)

# Horizontal ribs on left and right faces
for i in range(rib_count_depth):
    y_pos = wall_thickness + (i + 0.5) * rib_spacing
    
    # Left face rib
    rib_left = rs.AddBox([
        [0, y_pos - rib_width/2, 0],
        [rib_depth, y_pos - rib_width/2, 0],
        [rib_depth, y_pos + rib_width/2, 0],
        [0, y_pos + rib_width/2, 0],
        [0, y_pos - rib_width/2, base_height],
        [rib_depth, y_pos - rib_width/2, base_height],
        [rib_depth, y_pos + rib_width/2, base_height],
        [0, y_pos + rib_width/2, base_height]
    ])
    if rib_left:
        ribs.append(rib_left)
    
    # Right face rib
    rib_right = rs.AddBox([
        [base_width - rib_depth, y_pos - rib_width/2, 0],
        [base_width, y_pos - rib_width/2, 0],
        [base_width, y_pos + rib_width/2, 0],
        [base_width - rib_depth, y_pos + rib_width/2, 0],
        [base_width - rib_depth, y_pos - rib_width/2, base_height],
        [base_width, y_pos - rib_width/2, base_height],
        [base_width, y_pos + rib_width/2, base_height],
        [base_width - rib_depth, y_pos + rib_width/2, base_height]
    ])
    if rib_right:
        ribs.append(rib_right)

if ribs:
    base_box = rs.BooleanUnion([base_box] + ribs, delete_input=True)[0]

# STEP 7: Final cleanup and selection
print("\n[8/8] Finalizing organizer...")

rs.SelectObject(base_box)

print("\n" + "=" * 60)
print("ORGANIZER COMPLETE!")
print("=" * 60)
print(f"Dimensions: {base_width}mm x {base_depth + 30}mm x {base_height}mm")
print(f"Wall thickness: {wall_thickness}mm")
print(f"Features: Rounded corners, ribbed exterior, drainage mesh, sponge slot")
print("\nThe organizer is now selected and ready for export.")
print("=" * 60)