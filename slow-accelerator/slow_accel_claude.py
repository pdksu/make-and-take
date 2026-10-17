#!/usr/bin/env python3
"""
Slow-accelerator disc generator (laser cut SVG, mm units).

Geometry:
  - Outer circle: OD 100 mm
  - Bore: BORE_D mm diameter.
  - 3 centering nubs, 120 deg apart, bulging inward to a
    BORE_D - NUB_INTERFERENCE_D mm contact circle -- nubs crush
    slightly and self-center the ring on the rod.
  - 3 glue-pocket indentations, interleaved 60 deg from the nubs,
    bulging OUTWARD past the bore circle -- small reservoirs that
    hold adhesive instead of squeezing it all out.
  - A mask-only score circle around the nubs+indentations zone: cut
    through the masking paper only (not the plastic/plywood), so
    peeling the mask leaves a crisp, deliberate glue-area boundary
    instead of a torn edge.
  - Inside that boundary, small raster-etched patches straddling each
    indentation roughen the surface there for better glue grip.

Nubs and indentations are both drawn as arcs of a small circle whose
center sits off the bore circle, so each one blends smoothly into the
bore with no sharp corners (no stress risers, easy for the laser).
Nubs: circle center OUTSIDE the bore, near intersection taken (bulge
in). Indentations: circle center INSIDE the bore, far intersection
taken (bulge out).

KERF: all dimensions below are FINISHED sizes. If your cutter does
not auto-compensate, set KERF to your beam width; internal cuts
(bore/nubs/indentations) are shrunk and the outer circle grown by
KERF/2 per side. The mask-only score and etch patches are left at
nominal size -- kerf on a paper-only/raster pass is negligible.

Cut order: the laser sequences operations by color, ascending
#RRGGBB hex value (smallest first) -- GROUP_ORDER below is the actual
cut sequence and must stay consistent with that sort, same convention
as sundial/generate_gnomon_holder.py. The outer-cut color was changed
from blue to near-white for exactly this reason: blue (#0000FF =
255) sorts numerically BEFORE red (#FF0000 = 16,711,680), which would
cut the outer boundary first and let the disc float free before the
bore/nubs/indentations are even cut.
"""
import math

# ---------------- parameters (mm) ----------------
OD = 98.0                    # disc outer diameter
BORE_D = 12.70                # bore diameter (glue gap zone)
NUB_INTERFERENCE_D = 0.625    # diametral interference between the nub-tip circle and BORE_D.
                              # Lower = looser fit. Bracket so far: 0.80 too tight, 0.675 a tiny bit
                              # too tight, 0.55 a little loose -- 0.625 narrows in from the 0.55-0.675
                              # bracket -- retest physically and adjust from here.
NUB_TIP_D = BORE_D - NUB_INTERFERENCE_D   # diameter of the circle the 3 nub tips touch
N_NUBS = 3
NUB_R = 2.0                   # radius of the small circle forming each nub

INDENT_DEPTH = 0.75            # how far each glue-pocket indentation bulges OUTWARD past BORE_D/2 (mm) -- doubled
INDENT_R = 3.0                # radius of the small circle forming each indentation (mm) -- doubled
N_INDENTS = 3                 # interleaved with the nubs, offset by 180/N_NUBS degrees

MASK_SCORE_D = BORE_D + 3.0          # diameter of the paper-only score circle enclosing the
                                     # nubs+indentations zone (same offset the old full-ring etch used)
ETCH_PATCH_MARGIN_DEG = 3.0          # extra angular margin each adhesion-etch patch gets beyond its
                                     # indentation's own blend angle, on each side (deg)
ETCH_PATCH_STEP_DEG = 0.5           # sampling resolution for the etch patch's arc edges

KERF = 0.0                    # beam width; 0 if your software compensates
CANVAS = 110.0                # square canvas, mm
STEP_DEG = 0.2                # sampling resolution for the bore path

MASK_COLOR = "#00ff00"   # 0x00AA00 =        43,520 -- mask-only score (paper only), cut FIRST
ETCH_COLOR = "#440000"   # 0x993311 =    10,079,505 -- localized adhesion-etch patches (raster), SECOND
BORE_COLOR = "#55ffff"   # 0xFF0000 =    16,711,680 -- bore + nubs + indentations, THIRD
OUTER_COLOR = "#7702FF"  # 0xFFFFF0 =    16,777,200 -- outer perimeter, cut LAST (largest hex value --
                          # keeps stock secured until the end). Near-white rather than pure white so it's
                          # still visible against a white-background preview.
# --------------------------------------------------

cx = cy = CANVAS / 2.0

# kerf compensation: inner cuts smaller, outer cut larger (as drawn)
bore_r = BORE_D / 2.0 - KERF / 2.0
tip_r = NUB_TIP_D / 2.0 - KERF / 2.0
outer_r = OD / 2.0 + KERF / 2.0
indent_tip_r = bore_r + INDENT_DEPTH   # deepest point of each glue-pocket indentation
mask_r = MASK_SCORE_D / 2.0

nub_center_dist = tip_r + NUB_R          # nub circle center OUTSIDE the bore; near point = tip_r
indent_center_dist = indent_tip_r - INDENT_R   # indent circle center INSIDE the bore; far point = indent_tip_r

# angular half-width of each nub on the bore circle (law of cosines)
cos_a = (bore_r**2 + nub_center_dist**2 - NUB_R**2) / (2 * bore_r * nub_center_dist)
alpha = math.degrees(math.acos(cos_a))

# angular half-width of each indentation on the bore circle (same construction, mirrored)
cos_b = (bore_r**2 + indent_center_dist**2 - INDENT_R**2) / (2 * bore_r * indent_center_dist)
beta = math.degrees(math.acos(cos_b))

nub_axes = [90.0 + i * 360.0 / N_NUBS for i in range(N_NUBS)]
indent_axes = [90.0 + 180.0 / N_NUBS + i * 360.0 / N_INDENTS for i in range(N_INDENTS)]

def radius_at(t_deg):
    """Bore boundary radius at central angle t (deg): bore circle, pulled IN by
    any nub circle covering that angle, pushed OUT by any indentation circle
    covering that angle."""
    r = bore_r
    for phi in nub_axes:
        d = (t_deg - phi + 180.0) % 360.0 - 180.0   # signed diff in (-180,180]
        if abs(d) <= alpha:
            s = nub_center_dist * math.sin(math.radians(d))
            under = NUB_R**2 - s**2
            if under >= 0:
                r_nub = nub_center_dist * math.cos(math.radians(d)) - math.sqrt(under)
                r = min(r, r_nub)
    for phi in indent_axes:
        d = (t_deg - phi + 180.0) % 360.0 - 180.0
        if abs(d) <= beta:
            s = indent_center_dist * math.sin(math.radians(d))
            under = INDENT_R**2 - s**2
            if under >= 0:
                r_indent = indent_center_dist * math.cos(math.radians(d)) + math.sqrt(under)
                r = max(r, r_indent)
    return r

# sample the bore path (includes nubs and indentations)
pts = []
t = 0.0
while t < 360.0:
    r = radius_at(t)
    a = math.radians(t)
    pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    t += STEP_DEG

bore_path = "M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in pts) + " Z"

def etch_range(center_deg, half_angle_deg):
    """Angular [lo, hi] for one etch patch -- keep only the increasing-angle
    ("right", in screen terms, since this SVG has no y-flip) side, drop the
    other half entirely. Two indentations always flank the same nub, one on
    each side of it; with a full symmetric patch on each, BOTH ends up
    covering the exact same Y-band as its neighbor (approached from opposite
    X sides -- e.g. the patches at indent@150 and indent@30 span the
    identical y-range), forcing a full-width sweep on every row in that
    shared band. Keeping the same side (here, "right") on every patch is
    the one choice consistent across all of them by the design's 3-fold
    symmetry, and it means no two patches ever land on the same row -- each
    pass only has to travel one patch's own narrow width, not the full
    span between two patches on opposite sides of the disc."""
    return center_deg, center_deg + half_angle_deg

def etch_patch_path(angle_lo, angle_hi, r_outer, step_deg):
    """Filled patch spanning [angle_lo, angle_hi], from the ACTUAL cut
    boundary (radius_at, which already bulges out for the indentation here)
    to r_outer -- built as a sampled polygon (same style as bore_path above).
    Starting at radius_at rather than a flat bore_r skips re-etching the
    pocket that's already cut away, which would otherwise waste laser time
    tracing over open air."""
    angles = []
    a = angle_lo
    while a < angle_hi:
        angles.append(a)
        a += step_deg
    angles.append(angle_hi)
    outer_pts = [(cx + r_outer * math.cos(math.radians(t)), cy + r_outer * math.sin(math.radians(t))) for t in angles]
    inner_pts = [(cx + radius_at(t) * math.cos(math.radians(t)), cy + radius_at(t) * math.sin(math.radians(t))) for t in reversed(angles)]
    pts_patch = outer_pts + inner_pts
    return "M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in pts_patch) + " Z"

etch_patch_half_angle = beta + ETCH_PATCH_MARGIN_DEG
etch_patches = "\n  ".join(
    f'<path d="{etch_patch_path(*etch_range(phi, etch_patch_half_angle), mask_r, ETCH_PATCH_STEP_DEG)}" '
    f'fill="{ETCH_COLOR}" stroke="none"/>'
    for phi in indent_axes
)

svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{CANVAS}mm" height="{CANVAS}mm"
     viewBox="0 0 {CANVAS} {CANVAS}">
  <!-- Slow accelerator disc: OD {OD} mm, bore {BORE_D} mm,
       nub tips on {NUB_TIP_D} mm circle, indentations reaching {2*indent_tip_r:.2f} mm circle.
       Units: 1 user unit = 1 mm.
       Cut order is by color, ascending #RRGGBB hex value (the laser's default sort):
       green (mask-only score, paper only) first, brown (adhesion-etch patches, raster)
       second, red (bore + nubs + indentations) third, near-white (outer) last. -->
  <circle cx="{cx}" cy="{cy}" r="{mask_r}" fill="none" stroke="{MASK_COLOR}" stroke-width="0.1"/>
  {etch_patches}
  <path d="{bore_path}" fill="none" stroke="{BORE_COLOR}" stroke-width="0.1"/>
  <circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="none" stroke="{OUTER_COLOR}" stroke-width="0.1"/>
</svg>
'''

fname = f"svg/slow_accelerator_disc_{OD:.0f}_{str(BORE_D).replace('.', '_')}.svg"
with open(fname, "w") as f:
    f.write(svg)

# sanity report
tips = [radius_at(phi) for phi in nub_axes]
indents = [radius_at(phi) for phi in indent_axes]
print(f"bore radius:          {bore_r:.3f} mm (dia {2*bore_r:.2f})")
print(f"nub tip radius:       {min(tips):.4f} mm (target {tip_r:.3f}), interference {NUB_INTERFERENCE_D:.2f} mm diametral")
print(f"nub angular width:    {2*alpha:.2f} deg each")
print(f"indent tip radius:    {max(indents):.4f} mm (target {indent_tip_r:.3f}), depth {INDENT_DEPTH:.2f} mm radial")
print(f"indent angular width: {2*beta:.2f} deg each")
print(f"mask score radius:    {mask_r:.3f} mm (dia {2*mask_r:.2f})")
print(f"outer radius:         {outer_r:.3f} mm")
print(f"points in bore path:  {len(pts)}")
