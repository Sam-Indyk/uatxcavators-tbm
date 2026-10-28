"""DN600 spindle mount + cutterhead + hydraulic drive, rev H (detailed model) with assembly sequence.
Design as rev H (build_revH.py); this file adds catalogue-style detail, the drive adapter, coupling and motor,
seal-purge line, anti-roll fins, welds, fixtures for the assembly animation, and the step list.
Drive: Poclain MS18 shaft motor, 2,812 cc/rev (44.71 Nm/bar, 17.9 kNm max), 2A50 bearing support, W90x3x28 spline.
Motor flange pattern, pilot and body diameters are placeholders until the certified drawing (pilot Ø282 and spline
from the catalogue; 8 x M20 on Ø335 assumed).
Axis +X rearward, X = 0 at ring 1 front face. Units mm. Visualisation model; Fusion 360 is the model of record.
"""
import paths  # noqa: F401  (UTF-8 stdout, output folders)
import json, math, sys
import cadquery as cq
import build_opts as bo
import detail_lib as dl

V3 = cq.Vector
r = lambda d: d / 2.0
ring, revolve, rotx, comp, pt, radial, dirv, cyl = dl.ring, dl.revolve, dl.rotx, dl.comp, dl.pt, dl.radial, dl.dirv, dl.cyl
cyl_x, cyl_r, holes, dowels = bo.cyl_x, bo.cyl_r, bo.holes, bo.dowels
SH_ID, SH_OD = bo.SH_ID, bo.SH_OD
W = lambda s: cq.Workplane("XY").newObject([s])

# ---------------- positions ----------------
T_R1, CB = 110.0, 35.0
L = 400.0
x23f = 70.0; c23f = x23f + 44
x_col = x23f + 88                     # collar 158..173
x_bk = x_col + 15                     # backing ring 173..188
x29 = x_bk + 15                       # 29328N 188..248
x_sh = x29 + 60                       # shoulder 248..278
x23r = c23f + L - 44                  # 470
x_mb = x23r + 88                      # MB28 558..560
x_nut = x_mb + 2                      # KM28 560..585
x_rear = 615.0
R_TUBE, R_GRV, LAND, R_REC = 159.0, 148.0, 20.0, 137.0
X_ARM_B = -133.0; X_ARM_F = X_ARM_B - 50.8
X_LA0, X_LA1 = -133.0, -83.0
SH_X0 = X_ARM_B + 5.0; SH_X1 = SH_X0 + 1285.0
R_PIPE = 245.0
ARM_ANGS = [i * 45.0 for i in range(8)]
X_SHAFT_END = 715.0
# drive
X_AD0, X_AD1 = 615.0, 877.0           # adapter: cartridge face .. motor flange face
X_H1, X_J1, X_SP, X_J2, X_H2 = 660.0, 720.0, 725.0, 730.0, 765.0
X_MOT = X_AD1                          # motor mounting face
A_PURGE, X_PURGE0, X_PURGE1 = 30.0, 125.0, 600.0   # seal-purge port angle and line ends (line lies in an OD groove)
FIN_ANGS = (30.0, 90.0, 270.0, 330.0)              # anti-roll fins: 1, 3, 9, 11 o'clock
FIN_X0, FIN_X1, FIN_H, FIN_T = 150.0, 1140.0, 70.0, 20.0


def sector(x0, x1, r0, r1, a_mid, half):
    pts = [(0, 0)] + [(1.6 * r1 * math.cos(math.radians(a_mid - half + 2 * half * i / 16)),
                       1.6 * r1 * math.sin(math.radians(a_mid - half + 2 * half * i / 16))) for i in range(17)]
    w = cq.Workplane("YZ").workplane(offset=x0).polyline(pts).close().extrude(x1 - x0)
    return w.intersect(ring(x0, x1, r0, r1))


# ======================= SHELL WELDMENT =======================
shell = ring(SH_X0, SH_X1, r(SH_ID), r(SH_OD))
r1 = revolve([(0, 202), (0, r(SH_ID) - 0.5), (T_R1, r(SH_ID) - 0.5), (T_R1, 161.25), (T_R1 - 2, 159.25), (CB + 2, 159.25),
              (CB, 161.25), (CB, 197), (CB - 3, 200), (2, 200)])
r1 = holes(r1, CB - 1, 26, 370, 10.2, 16, phase=11.25)
for a in (0, 180):
    r1 = r1.cut(cyl_x(CB - 1, 27, 185, a, 16))
    r1 = r1.cut(cyl_x(-1, T_R1 + 2, R_PIPE, a, 77))
for a in (90, 270):
    r1 = r1.cut(cyl_x(-1, T_R1 + 2, 225, a, 12))
weld = revolve([(0, r(SH_ID)), (-14, r(SH_ID)), (0, r(SH_ID) - 14)])
pipes = None
pipe_welds = []
for a in (0, 180):
    p = cyl_x(0, SH_X1, R_PIPE, a, 76.1).cut(cyl_x(-1, SH_X1 + 2, R_PIPE, a, 65))
    pipes = p if pipes is None else pipes.union(p)
    r1 = r1.cut(W(cq.Solid.makeCone(44.5, 38.5, 6.0, pt(-0.01, R_PIPE, a), V3(1, 0, 0))))     # 45 deg bevel at the front for the seal weld
    cone = cq.Solid.makeCone(44.5, 38.5, 6.0, pt(0, R_PIPE, a), V3(1, 0, 0))
    pipe_welds.append(W(cone).cut(cyl_x(-1, 10, R_PIPE, a, 76.1)).val())
pipe_welds = comp(pipe_welds)
sad = None
for sgn in (1, -1):
    b = cq.Workplane("YZ").workplane(offset=950).center(268 * sgn, 0).rect(26, 90).extrude(20)
    b = b.cut(cyl_x(949, 22, R_PIPE, 0 if sgn > 0 else 180, 76.2))
    sad = b if sad is None else sad.union(b)
taps = None
for a in (90, 270):
    t = cyl_x(T_R1, 120, 225, a, 12).cut(cyl_x(T_R1 - 1, 122, 225, a, 8))
    taps = t if taps is None else taps.union(t)
legs = comp([cyl(pt(T_R1, 255, a), V3(1, 0, 0), 30, SH_X1 - T_R1) for a in (40, 160, 280)])

# ======================= CARTRIDGE =======================
cart = revolve([
    (0, R_REC), (0, R_TUBE - 1), (1, R_TUBE), (LAND, R_TUBE), (LAND, R_GRV), (CB, R_GRV), (CB, R_TUBE), (x_rear - 2, R_TUBE),
    (x_rear, R_TUBE - 2), (x_rear, 126), (x_rear - 1, 125), (465, 125), (465, 126), (x_sh + 30, 126), (x_sh + 30, 102),
    (x_sh, 102), (x_sh, 120.5), (x29, 120.5), (x29, 126), (x_col, 126), (x_col, 125), (10, 125), (10, R_REC),
])
cart = holes(cart, 10, 16, 262, 5.0, 12, phase=15)
for a in (90, 270):
    cart = cart.cut(cyl_x(x_sh - 1, 32, 111, a, 12))
cart = holes(cart, x_rear - 25, 26, 280, 14.0, 12)
for a in (15, 135, 255):
    cart = cart.cut(cyl_x(x_rear - 21, 22, 140, a, 16))
for a in (45, 135, 225, 315):
    cart = cart.cut(cyl_r(10, a, 146, 161, 16))
cart = cart.cut(ring(70, 76, 154, 159.5))
cart = cart.cut(cyl_x(6, 120, 142.5, A_PURGE, 5)).cut(cyl_r(X_PURGE0, A_PURGE, 140, 161, 5)).cut(cyl_r(27, A_PURGE, 124, 145, 5))
groove = rotx(cq.Workplane("XY").box(X_PURGE1 + 8 - (X_PURGE0 - 8), 12, 14).translate(((X_PURGE0 + X_PURGE1) / 2, 150 + 6, 0)), A_PURGE)
cart = cart.cut(groove)                                                    # 14 wide x 9 deep groove for the purge line
oring = ring(70.5, 75.5, 154.5, 159.2)
purge_line = rotx(cq.Workplane("XY").newObject([cyl(V3(X_PURGE0 + 6, 154.5, 0), V3(1, 0, 0), 8, X_PURGE1 - X_PURGE0 - 12)]), A_PURGE)
purge_fit = comp([rotx(cq.Workplane("XY").box(12, 8.4, 12).translate((xx, 150.2 + 4.2, 0)), A_PURGE).val() for xx in (X_PURGE0, X_PURGE1)])
# anti-roll fins on the shield OD
def fin(a):
    rf, rr = FIN_H / math.tan(math.radians(30)), FIN_H / math.tan(math.radians(45))
    R0 = r(SH_OD)
    f = (cq.Workplane("XY").polyline([(FIN_X0, R0), (FIN_X0 + rf, R0 + FIN_H), (FIN_X1 - rr, R0 + FIN_H), (FIN_X1, R0)])
         .close().extrude(FIN_T).translate((0, 0, -FIN_T / 2)))
    for sg in (1, -1):                                                       # knife edge at the leading end
        f = f.cut(W(dl.prism([(FIN_X0 - 0.1, R0 - 1, sg * 0.6), (FIN_X0 - 0.1, R0 - 1, sg * (FIN_T / 2 + 0.2)), (FIN_X0 + 35, R0 - 1, sg * (FIN_T / 2 + 0.2))], (0, FIN_H + 3, 0))))
    return rotx(f, a)
fins = {a: fin(a) for a in FIN_ANGS}
fin_welds = comp([rotx(W(dl.line_fillet((FIN_X0 + 16, r(SH_OD), sg * FIN_T / 2), (FIN_X1 - 9, r(SH_OD), sg * FIN_T / 2), (0, 1, 0), (0, 0, sg), 8)), a).val()
                  for a in FIN_ANGS for sg in (1, -1)])

# split flange: two halves split at 3 and 9 o'clock (plane y = 0)
sfl = revolve([(0, 159.2), (0, 199.9), (CB - 4, 199.9), (CB, 195.9), (CB, R_GRV + 0.2), (LAND, R_GRV + 0.2), (LAND, 159.2)])
sfl = holes(sfl, -1, CB + 2, 370, 13.5, 16, phase=11.25)
for i in range(16):
    sfl = sfl.cut(cyl_x(-1, 14, 185, 11.25 + 22.5 * i, 20))
for a in (0, 180):
    sfl = sfl.cut(cyl_x(-1, CB + 2, 185, a, 16))
for a in (45, 135, 225, 315):
    sfl = sfl.cut(cyl_r(10, a, 146, 201, 16))
split_screws = []
for z in (172.0, -172.0):
    s = dl.shcs(V3(15, 20, z), V3(0, -1, 0), 10, 40)
    split_screws.append(s)
    sfl = sfl.cut(W(cyl(V3(15, -25, z), V3(0, 1, 0), 10.5, 45))).cut(W(cyl(V3(15, 20, z), V3(0, 1, 0), 17, 100)))   # counterbore open to the OD
split_screws = comp(split_screws)
kerf = cq.Workplane("XY").box(CB + 4, 3.0, 420).translate((CB / 2, 0, 0))
sfl = sfl.cut(kerf)
halfA = sfl.intersect(cq.Workplane("XY").box(200, 500, 500).translate((CB / 2, 250, 0)))
halfB = sfl.intersect(cq.Workplane("XY").box(200, 500, 500).translate((CB / 2, -250, 0)))
pins = comp([cyl(pt(10, 146, a), radial(a), 16, 53.5) for a in (45, 135, 225, 315)])
flange_screws = dl.axial_screws(13, 370, 12, 16, 45, phase=11.25)
fl_dowels = dowels(5, 55, 370, (0, 180))

# seal carrier, seals, lanterns
carrier = revolve([(0, 86), (0, R_REC - 0.5), (9.4, R_REC - 0.5), (9.4, 124.8), (69, 124.8), (70, 123.8), (70, 112), (69, 112),
                   (69, 100), (8, 100), (8, 86)])
carrier = carrier.cut(ring(-1, 8, 101, 109)).cut(ring(-1, 8, 115, 123))
carrier = holes(carrier, -1, 12, 262, 6.6, 12, phase=15)
carrier = holes(carrier, -1, 3.4, 262, 12, 12, phase=15)
carrier = carrier.cut(cyl_r(27, 30, 99, 126, 6))
carrier = carrier.cut(ring(14, 18, 122, 125)).cut(ring(36, 40, 122, 125))       # O-rings either side of the purge port
seal_case, seal_lip, seal_spring = [], [], []
for xs in (8.0, 31.0, 54.0):
    c_, l_, s_ = dl.lip_seal(xs)
    seal_case.append(c_); seal_lip.append(l_); seal_spring.append(s_)
seal_case, seal_lip, seal_spring = comp(seal_case), comp(seal_lip), comp(seal_spring)
lant = comp([dl.lantern(23, 31, 86, 100), dl.lantern(46, 54, 86, 100)])
shim = ring(9.4, 10, 126, R_REC - 1)
carrier_screws = comp([dl.csk(pt(0, 131, 15 + 30 * i), V3(1, 0, 0), 6, 22) for i in range(12)])

# ======================= SPINDLE + BEARINGS =======================
shaft = revolve([(X_LA0, 0), (X_LA0, 68), (X_LA0 + 2, 70), (x_col, 70), (x_col, 82.5), (x_bk, 82.5), (x_bk, 70),
                 (x_nut + 25, 70), (x_nut + 25, 67), (x_nut + 28, 65), (X_SHAFT_END - 2, 65), (X_SHAFT_END, 63), (X_SHAFT_END, 0)])
shaft = shaft.cut(cyl_x(X_LA0 - 1, 61, 0, 0, 26))                              # M30 nose thread (lift, pull, push-off)
shaft = shaft.cut(cq.Workplane("XY").box(30, 8, 10).translate((x_nut + 12, 68, 0)))   # MB28 tab slot
shaft = shaft.cut(cyl_x(X_SHAFT_END - 40, 41, 0, 0, 17.5))                   # M20 centre thread, drive end
b23f = dl.sph_roller_bearing(x23f)
b23r = dl.sph_roller_bearing(x23r)
b29 = dl.sph_thrust_bearing(x29)
backing = revolve([(x_bk, 70), (x_bk, 95), (x29 - 1, 95), (x29, 94), (x29, 70)])
spacer = ring(x29 + 38.5, x23r, 70, 80)
mb = dl.mb_washer(x_mb, 2.0, 70, 95)
nut = dl.km_nut(x_nut, 25.0, 70, 95)
eye = W(cyl(V3(X_LA0 - 60, 0, 0), V3(1, 0, 0), 30, 120)).union(
    W(cq.Solid.makeTorus(32, 9, V3(X_LA0 - 100, 0, 0), V3(0, 0, 1))))

# ======================= CUTTERHEAD =======================
R_ARM_IN, R_ARM_OUT, W_ARM = 150.0, 310.0, 76.0
TABS = ((190.0, 220.0), (245.0, 275.0))


def arm(ang):
    return rotx(cq.Workplane("YZ").workplane(offset=X_ARM_F).center((R_ARM_IN + R_ARM_OUT) / 2, 0)
                .rect(R_ARM_OUT - R_ARM_IN, W_ARM).extrude(X_ARM_B - X_ARM_F), ang)


def gusset(ang, t=25.0):
    g = (cq.Workplane("XY").polyline([(X_ARM_B, 170), (X_ARM_B, 290), (-8, 175), (-8, 125), (X_LA1, 125), (X_LA1, 170)])
         .close().extrude(t).translate((0, 0, -t / 2)))
    for a, b in TABS:
        g = g.union(cq.Workplane("XY").center((X_ARM_F + X_ARM_B) / 2, (a + b) / 2)
                    .rect(X_ARM_B - X_ARM_F, b - a).extrude(t).translate((0, 0, -t / 2)))
    return rotx(g, ang)


def slots(ang):
    s = None
    for a, b in TABS:
        w = (cq.Workplane("XY").center((X_ARM_F + X_ARM_B) / 2, (a + b) / 2)
             .rect(X_ARM_B - X_ARM_F + 2, b - a + 0.4).extrude(25.4).translate((0, 0, -12.7)))
        s = w if s is None else s.union(w)
    return rotx(s, ang)


def bit(c, ang):
    z0 = W_ARM / 2 - 12.0
    holder = (cq.Workplane("YZ").workplane(offset=X_ARM_F - 20).center(c, z0).rect(30, 24).extrude(20)
              .edges("|X").chamfer(2.0))
    trap = (cq.Workplane("XY").workplane(offset=z0 - 7)
            .polyline([(X_ARM_F - 20, c - 11), (X_ARM_F - 20, c + 11), (X_ARM_F - 42, c + 6.35), (X_ARM_F - 42, c - 6.35)])
            .close().extrude(14))
    return rotx(holder, ang), rotx(trap, ang)


tracks = [(315.0 - 6.35, a, True) for a in (0, 3, 5)]
tracks += [(315.0 - 6.35 - 12.7 * k, (k * 3 + 1) % 8, False) for k in range(1, 22)]
X_CAP1 = X_ARM_F + 30.0
cap_outline = ring(X_ARM_F, X_CAP1, 0, 135).cut(sector(X_ARM_F - 1, X_CAP1 + 1, 118, 140, 0, 22.5)).cut(
    sector(X_ARM_F - 1, X_CAP1 + 1, 112, 140, 135, 22.5))
spider = ring(X_ARM_F, X_ARM_B, 100, 170)
for a in ARM_ANGS:
    spider = spider.union(arm(a))
spider = spider.cut(cap_outline)
spider = holes(spider, X_CAP1, 16, 216, 6.8, 8, phase=22.5)
for a in ARM_ANGS:
    spider = spider.cut(slots(a))
gussets = comp([gusset(a) for a in ARM_ANGS])
hubring = ring(X_LA0, X_LA1, 95, 170)
sleeve = revolve([(X_LA1, 70), (X_LA1, 125), (-8, 125), (-8, 85), (68, 85), (70, 83), (70, 70)])
sleeve = sleeve.union(ring(-8, 6, 103, 107)).union(ring(-8, 6, 117, 121))
# locking assembly 140 x 190 x 50 (B-LOC B400 type): front collar + two taper rings + 12 x M12
la_collar = ring(X_LA0, X_LA0 + 10, 70.5, 94.8)
la_in = revolve([(X_LA0 + 10, 70), (X_LA1, 70), (X_LA1, 78.5), (X_LA0 + 10, 82.5)])
la_out = revolve([(X_LA0 + 10, 82.8), (X_LA1, 78.8), (X_LA1, 95), (X_LA0 + 10, 95)])
la_ring = la_collar.union(la_in).union(la_out)
la_ring = holes(la_ring, X_LA0 - 1, 40, 165, 13, 12)
la_screws = dl.axial_screws(X_LA0, 165, 12, 12, 35)
# welds (head)
hw_ = []
for a in ARM_ANGS:
    for s in (1, -1):
        hw_.append(rotx(W(dl.line_fillet((X_ARM_B, 172, s * 12.5), (X_ARM_B, 286, s * 12.5), (1, 0, 0), (0, 0, s), 12)), a).val())
        hw_.append(rotx(W(dl.line_fillet((X_ARM_B, 170.5, s * 12.5), (X_LA1, 170.5, s * 12.5), (0, 1, 0), (0, 0, s), 8)), a).val())
        hw_.append(rotx(W(dl.line_fillet((X_LA1, 125.5, s * 12.5), (-10, 125.5, s * 12.5), (0, 1, 0), (0, 0, s), 8)), a).val())
hw_ += [dl.ring_fillet(X_ARM_B, 170, 8, +1, +1).val(), dl.ring_fillet(X_LA1, 125, 8, +1, +1).val()]
head_welds = comp(hw_)
cap = holes(holes(cap_outline, X_ARM_F - 1, 32, 216, 9, 8, phase=22.5), X_ARM_F - 1, 5.5, 216, 16, 8, phase=22.5)
cap = holes(cap, X_ARM_F - 1, 20, 60, 10.2, 2, phase=90)                     # M12 jack/pull holes
cone = revolve([(X_ARM_F, 0), (X_ARM_F, 24), (X_ARM_F - 25, 0)])
cap = cap.union(cone)
cone_blades = comp([rotx(cq.Workplane("XY").box(20, 4, 26).translate((X_ARM_F - 12, 0, 13)), 120 * i).val() for i in range(3)])
cap_screws = comp([dl.csk(pt(X_ARM_F, 108, 22.5 + 45 * i), V3(1, 0, 0), 8, 40) for i in range(8)])
sp_holders, sp_carb, cp_holders, cp_carb = [], [], [], []
for c, ai, g in tracks:
    h, t = bit(c, ARM_ANGS[ai])
    if c + 15 <= 135:
        cp_holders.append(h); cp_carb.append(t)
    else:
        sp_holders.append(h); sp_carb.append(t)
sp_holders, sp_carb, cp_holders, cp_carb = comp(sp_holders), comp(sp_carb), comp(cp_holders), comp(cp_carb)

# ======================= DRIVE: ADAPTER, COUPLING, MOTOR =======================
ad_front = revolve([(600, 110), (600, 124.9), (614, 124.9), (615, 125.9), (615, 190), (X_AD0 + 25, 190), (X_AD0 + 25, 110)])
ad_front = holes(ad_front, 599, 45, 280, 17.5, 12)
for a in (15, 135, 255):
    ad_front = ad_front.cut(cyl_x(599, 45, 140, a, 16))
ad_tube = ring(X_AD0 + 25, X_AD1 - 30, 165.1, 177.8)
for a in (90, 270):
    win = cq.Workplane("XY").box(140, 60, 130).translate((735, 171, 0))
    ad_tube = ad_tube.cut(rotx(win, a))
ad_rear = ring(X_AD1 - 30, X_AD1, 141.1, 200)
ad_rear = holes(ad_rear, X_AD1 - 31, 32, 335, 17.5, 8, phase=22.5)
adapter = ad_front.union(ad_tube).union(ad_rear)
ad_welds = comp([dl.ring_fillet(X_AD0 + 25, 177.8, 8, +1, +1), dl.ring_fillet(X_AD1 - 30, 177.8, 8, -1, +1),
                 dl.ring_fillet(X_AD0 + 25, 165.1, 6, +1, -1), dl.ring_fillet(X_AD1 - 30, 165.1, 6, -1, -1)])
ad_screws = dl.axial_screws(X_AD0 + 25, 280, 16, 12, 50, toward=-1)
ad_dowels = comp([cyl(pt(596, 140, a), V3(1, 0, 0), 16, 42) for a in (15, 135, 255)])
# seal-purge supply: connected at the end of the groove line after the module is in, then run to the surface
supply = comp([cyl(pt(X_PURGE1, 158.6, A_PURGE), radial(A_PURGE), 10, 209 - 158.6),
               cq.Solid.makeSphere(5, pt(X_PURGE1, 209, A_PURGE), V3(0, 0, 1), -90, 90, 360),
               cyl(pt(X_PURGE1, 209, A_PURGE), V3(1, 0, 0), 10, 1500 - X_PURGE1)])
# coupling (jaw type): hub 1 on the spindle with an internal locking assembly 130 x 180, elastomer spider, hub 2 on the motor spline
hub1 = ring(X_H1, X_J1, 90, 140)
for i in range(4):
    hub1 = hub1.union(sector(X_J1, X_J1 + 35, 100, 140, 90 * i, 18))
hub1_la = revolve([(X_H1 + 5, 65), (X_H1 + 55, 65), (X_H1 + 55, 76), (X_H1 + 5, 80)]).union(
    revolve([(X_H1 + 5, 80.3), (X_H1 + 55, 76.3), (X_H1 + 55, 90), (X_H1 + 5, 90)]))
hub1_la = holes(hub1_la, X_H1 + 4, 52, 155, 13, 10, phase=18)
hub1_la_screws = dl.axial_screws(X_H1 + 55, 155, 12, 10, 40, phase=18, toward=-1)
spider_el = comp([sector(X_SP, X_SP + 35, 100, 140, 22.5 + 45 * i, 4.5) for i in range(8)])
hub2 = ring(X_H2, 850, 45, 140)
for i in range(4):
    hub2 = hub2.union(sector(X_J2, X_J2 + 35, 100, 140, 45 + 90 * i, 18))
# motor (Poclain MS18 shaft motor, 2A50): placeholder body diameters
mshaft = ring(X_H2 + 2, X_MOT, 0, 41.5)
teeth = comp([rotx(cq.Workplane("XY").box(X_MOT - X_H2 - 2, 3.4, 3.0).translate(((X_H2 + 2 + X_MOT) / 2, 43.0, 0)), 360 / 28 * i).val()
              for i in range(28)])
mot = ring(X_MOT - 6, X_MOT, 46, 140.9)                                     # Ø282 spigot
mot = mot.union(ring(X_MOT, X_MOT + 22, 46, 192.5))
mot = holes(mot, X_MOT - 1, 24, 335, 22, 8, phase=22.5)
mot = mot.union(ring(X_MOT + 22, 990, 0, 150))
for i in range(6):
    mot = mot.union(rotx(cq.Workplane("XY").box(990 - X_MOT - 22, 30, 10).translate(((X_MOT + 22 + 990) / 2, 160, 0)), 60 * i))
mot = mot.union(ring(990, 1000, 0, 175)).union(ring(1000, 1120, 0, 185)).union(ring(1120, 1128, 0, 175))
mot = mot.union(ring(1128, 1225, 0, 140))
for a in (60, 120):
    mot = mot.union(cyl_x(1225, 22, 80, a, 52))
mot = mot.union(cyl_x(1225, 16, 60, 270, 30))
mot_bolts_rear = dl.axial_screws(1120, 165, 16, 12, 10, phase=15, toward=+1)
mot_bolts = dl.axial_screws(X_MOT + 22, 335, 20, 8, 45, phase=22.5, toward=-1)
hoses = comp([cyl(pt(1247, 80, a), V3(1, 0, 0), 34, 260) for a in (60, 120)] + [cyl(pt(1241, 60, 270), V3(1, 0, 0), 20, 266)])

# ======================= THRUST RING (Rev A, docs/thrust-ring.md) =======================
# Launch with no jacking pipes yet: the ring's front face sits on the shield rear end. Front-face register not modelled
# (casing joint drawing open). Saddles and cylinders are built at 12 o'clock (radial +Y, cross-tube axis +Z) and rotated.
TR_X0, TR_T, TR_ID, TR_OD = SH_X1, 76.2, 400.0, 609.6
TR_X1 = TR_X0 + TR_T                                      # rear face
TR_R, TR_ANGS = 260.0, (60.0, 120.0, 240.0, 300.0)        # cylinders at 2, 4, 8, 10 o'clock
SD_U, SD_V, SD_H, SD_SEAT = 144.0, 100.0, 45.5, 65.0      # saddle block tangential x radial x high, seat Ø
X_CT = TR_X1 + 57.5                                       # cross-tube and pin axis
EAR_T, EAR_W, EAR_R, EAR_GAP, EAR_HOLE, EAR_SLOT = 20.0, 80.0, 40.0, 104.0, 39.5, 3.0
CYL_L = 889.0                                             # Chief WT 5 x 24, pin to pin, retracted
t_ring = ring(TR_X0, TR_X1, r(TR_ID), r(TR_OD))


def tr_block():
    b = cq.Workplane("XY").box(SD_H, SD_V, SD_U).translate((TR_X1 + SD_H / 2, TR_R, 0))
    return b.cut(W(cyl(V3(X_CT, TR_R, -SD_U / 2 - 1), V3(0, 0, 1), SD_SEAT, SD_U + 2)))


def tr_ear(z0):
    """lug on the block end: foot fills the seat groove, R40 end, Ø39.5 hole slotted 3 toward the ring"""
    top = TR_X1 + SD_H
    slab = lambda x0, x1, w: cq.Workplane("XY").box(x1 - x0, w, EAR_T).translate(((x0 + x1) / 2, TR_R, z0 + EAR_T / 2))
    disc = lambda xc, dia, ext=0.0: W(cyl(V3(xc, TR_R, z0 - ext), V3(0, 0, 1), dia, EAR_T + 2 * ext))
    e = slab(top, X_CT, EAR_W).union(disc(X_CT, 2 * EAR_R).intersect(slab(X_CT, X_CT + EAR_R, EAR_W)))
    e = e.union(disc(X_CT, SD_SEAT).intersect(slab(top - SD_SEAT / 2, top, SD_SEAT)))
    hole = disc(X_CT, EAR_HOLE, 1).union(disc(X_CT - EAR_SLOT, EAR_HOLE, 1)).union(
        cq.Workplane("XY").box(EAR_SLOT, EAR_HOLE, EAR_T + 2).translate((X_CT - EAR_SLOT / 2, TR_R, z0 + EAR_T / 2)))
    return e.cut(hole)


def tr_welds():
    """8 mm fillet round the block foot, trimmed where the block overhangs the ring OD"""
    x, v0, v1, u = TR_X1, TR_R - SD_V / 2, TR_R + SD_V / 2, SD_U / 2
    w = [dl.line_fillet((x, v0, -u), (x, v0, u), (1, 0, 0), (0, -1, 0), 8), dl.line_fillet((x, v1, -u), (x, v1, u), (1, 0, 0), (0, 1, 0), 8)]
    w += [dl.line_fillet((x, v0, s * u), (x, v1, s * u), (1, 0, 0), (0, 0, s), 8) for s in (1, -1)]
    return comp(w).intersect(ring(x - 1, x + 10, 0, r(TR_OD)))


def jack():
    """Chief WT 5 x 24 envelope: cross tubes Ø63.5 x 101.6 (Ø38.5 pin bore), rod Ø63.5, barrel Ø146.1; gland and barrel lengths approximate"""
    ct = lambda xc: W(cyl(V3(xc, TR_R, -50.8), V3(0, 0, 1), 63.5, 101.6))
    c = ct(X_CT).union(W(cyl(V3(X_CT + 20, TR_R, 0), V3(1, 0, 0), 63.5, 110)))
    c = c.union(W(cyl(V3(X_CT + 110, TR_R, 0), V3(1, 0, 0), 146.1, CYL_L - 125))).union(ct(X_CT + CYL_L))
    for xc in (X_CT, X_CT + CYL_L):
        c = c.cut(W(cyl(V3(xc, TR_R, -51), V3(0, 0, 1), 38.5, 102)))
    return c


t_blocks = comp([rotx(tr_block(), a) for a in TR_ANGS])
t_ears = comp([rotx(tr_ear(z0), a) for a in TR_ANGS for z0 in (EAR_GAP / 2, -EAR_GAP / 2 - EAR_T)])
t_welds = comp([rotx(tr_welds(), a) for a in TR_ANGS])
t_pins = {a: rotx(W(cyl(V3(X_CT, TR_R, -80), V3(0, 0, 1), 38.1, 160)), a) for a in TR_ANGS}
jacks = comp([rotx(jack(), a) for a in TR_ANGS])

# ======================= PARTS =======================
SH, BM, CH, DR, FX = "Shell weldment", "Bearing module", "Cutterhead", "Drive", "Fixture"
P = []   # (key, name, wp, colour, explode dx, viewer group, assembly group)


def add(key, name, wp, col, dx, grp, ag):
    P.append((key, name, wp, col, dx, grp, ag))


add("shell", "Shield shell Ø609.6 × 12.7 × 1285", shell, "#8a8f94", 0, SH, "shell")
add("ring1", "Ring 1, 110 thk A572-50, Ø400 × 35 counterbore", r1, "#5f86a8", 0, SH, "shell")
add("weld", "Ring 1 weld, 14 mm fillet from the front", weld, "#c99a3c", 0, SH, "shell")
add("pipes", "Slurry pipes Ø76.1, flush at the plate, 12 + 6", pipes, "#e0e4e8", 0, SH, "shell")
add("pipewelds", "Pipe seal welds, flush at the plate face", pipe_welds, "#c99a3c", 0, SH, "shell")
add("saddles", "Pipe saddles", sad, "#5f86a8", 0, SH, "shell")
add("taps", "Pressure-tap tubes, flush", taps, "#e0e4e8", 0, SH, "shell")
for a_ in FIN_ANGS:
    add(f"fin{int(a_)}", f"Anti-roll fin 20 × 70 × 990 at {int(a_)}°", fins[a_], "#7d93a6", 0, SH, "shell")
add("finwelds", "Fin welds, 2 × 8 mm fillets", fin_welds, "#c99a3c", 0, SH, "shell")
add("legs", "Gauge legs ×3, 1047 (fixture)", legs, "#e07a3c", 0, FX, "shell")
add("tube", "Cartridge tube, seamless 323.9 × 60", cart, "#b8673a", -900, BM, "tube")
add("halfA", "Split flange half A", halfA, "#d08a4a", -900, BM, "tube")
add("halfB", "Split flange half B", halfB, "#c7803f", -900, BM, "tube")
add("splitscrews", "Split-joint screws 2 × M10", split_screws, "#3c3f44", -900, BM, "tube")
for a_ in (45, 135, 225, 315):
    add(f"pin{a_}", f"Anti-rotation pin Ø16 at {a_}°", W(cyl(pt(10, 146, a_), radial(a_), 16, 53.5)), "#e0a030", -900, BM, "tube")
add("oring", "Static O-ring on tube", oring, "#2b2f33", -900, BM, "tube")
add("purge", "Seal-purge line Ø8 in OD groove", purge_line, "#d9c24a", -900, BM, "tube")
add("purgefit", "Purge line fittings (low profile)", purge_fit, "#b59a2e", -900, BM, "tube")
add("flscrews", "Flange screws 16 × M12 10.9", flange_screws, "#3c3f44", -900, BM, "shell")
add("fldowels", "Dowels 2 × Ø16, flange to ring 1", fl_dowels, "#e0a030", -900, BM, "shell")
add("carrier", "Seal carrier", carrier, "#9c5530", -1250, BM, "tube")
add("sealcase", "Lip seals 170 × 200 × 15 ×3: steel case", seal_case, "#6b7076", -1250, BM, "tube")
add("seallip", "Lip seals: NBR lips", seal_lip, "#24272a", -1250, BM, "tube")
add("sealspring", "Lip seals: garter springs", seal_spring, "#b0b5ba", -1250, BM, "tube")
add("lantern", "Lantern rings ×2", lant, "#d9c24a", -1250, BM, "tube")
add("shim", "Carrier shims", shim, "#d9c24a", -1200, BM, "tube")
add("carscrews", "Carrier screws 12 × M6 countersunk", carrier_screws, "#3c3f44", -1250, BM, "tube")
add("hw", "29328N housing washer", b29["hw"], "#4f8a8b", -1000, BM, "tube")
add("shaft", "Spindle Ø140, 4140 QT", shaft, "#c7ccd1", -1500, BM, "rotor")
add("f_ir", "Front 23228: inner ring", b23f["ir"], "#6aa368", -1500, BM, "rotor")
add("f_or", "Front 23228: outer ring", b23f["or"], "#5c9160", -1500, BM, "rotor")
add("f_rol", "Front 23228: rollers 2 × 19", b23f["rollers"], "#aab3bb", -1500, BM, "rotor")
add("f_cage", "Front 23228: cage rings + guide ring", b23f["cage"], "#b88a3a", -1500, BM, "rotor")
add("backing", "Backing ring Ø190", backing, "#9aa0a6", -1500, BM, "rotor")
add("sw", "29328N shaft washer", b29["sw"], "#4f8a8b", -1500, BM, "rotor")
add("t_rol", "29328N rollers ×24", b29["rollers"], "#aab3bb", -1500, BM, "rotor")
add("spacer", "Spacer sleeve", spacer, "#9aa0a6", -1500, BM, "rotor")
add("r_ir", "Rear 23228: inner ring", b23r["ir"], "#6aa368", -1500, BM, "rotor")
add("r_or", "Rear 23228: outer ring", b23r["or"], "#5c9160", -1500, BM, "rotor")
add("r_rol", "Rear 23228: rollers 2 × 19", b23r["rollers"], "#aab3bb", -1500, BM, "rotor")
add("r_cage", "Rear 23228: cage rings + guide ring", b23r["cage"], "#b88a3a", -1500, BM, "rotor")
add("mb", "MB28 lock washer", mb, "#9aa0a6", -1500, BM, "rotor")
add("nut", "KM28 lock nut", nut, "#7d8288", -1500, BM, "rotor")
add("eye", "M30 eye bolt in spindle nose (fixture)", eye, "#e07a3c", -1500, FX, "rotor")
add("spider", "Spider plate 50.8, one waterjet piece", spider, "#8c6bb1", -2300, CH, "head")
add("gussets", "Gussets ×8, 25 thk, tab-and-slot", gussets, "#a58ad0", -2300, CH, "head")
add("hubring", "LA hub ring Ø340 × Ø190 × 50.8", hubring, "#7a5aa1", -2300, CH, "head")
add("sleeve", "Journal sleeve Ø170 + labyrinth rings", sleeve, "#d0a060", -2300, CH, "head")
add("headwelds", "Head welds (12 mm gusset-to-arm, 8 mm hub)", head_welds, "#c99a3c", -2300, CH, "head")
add("holders", "Bit holders ×17 (spider)", sp_holders, "#5a4a7a", -2300, CH, "head")
add("carbide", "Carbide drag bits ×17 (spider)", sp_carb, "#e8d36a", -2300, CH, "head")
add("la", "Locking assembly 140 × 190 × 50", la_ring, "#3f6f8f", -2300, CH, "head")
add("lascrews", "Locking assembly screws 12 × M12", la_screws, "#3c3f44", -2300, CH, "head")
add("cap", "Centre cap 30 thk + cone", cap, "#6a4a91", -2650, CH, "cap")
add("capholders", "Bit holders ×7 (cap)", cp_holders, "#5a4a7a", -2650, CH, "cap")
add("capcarbide", "Carbide drag bits ×7 (cap)", cp_carb, "#e8d36a", -2650, CH, "cap")
add("blades", "Centre cone carbide blades ×3", cone_blades, "#e8d36a", -2650, CH, "cap")
add("capscrews", "Cap screws 8 × M8 countersunk", cap_screws, "#3c3f44", -2650, CH, "cap")
add("adapter", "Drive adapter weldment (bell housing)", adapter, "#7b9fb8", 450, DR, "shell")
add("adwelds", "Adapter welds", ad_welds, "#c99a3c", 450, DR, "shell")
add("adscrews", "Adapter screws 12 × M16 10.9", ad_screws, "#3c3f44", 450, DR, "shell")
add("addowels", "Adapter dowels 3 × Ø16", ad_dowels, "#e0a030", 450, DR, "shell")
add("gsupply", "Seal-purge supply line (to the surface)", supply, "#d9c24a", 450, DR, "shell")
add("hub1", "Coupling hub, spindle side", hub1, "#9aa7b2", 650, DR, "shell")
add("hub1la", "Hub locking assembly 130 × 180", hub1_la, "#3f6f8f", 650, DR, "shell")
add("hub1scr", "Hub locking-assembly screws 10 × M12", hub1_la_screws, "#3c3f44", 650, DR, "shell")
add("elast", "Coupling spider, polyurethane", spider_el, "#c0392b", 750, DR, "shell")
add("hub2", "Coupling hub, motor side (W90 spline bore)", hub2, "#9aa7b2", 850, DR, "shell")
add("mshaft", "Motor shaft W90 × 3 × 28", comp([mshaft, teeth]), "#c7ccd1", 850, DR, "shell")
add("motor", "Hydraulic motor, Poclain MS18 2,812 cc (body approximate)", mot, "#2f6f9f", 850, DR, "shell")
add("mbolts_r", "Motor housing bolts", mot_bolts_rear, "#3c3f44", 850, DR, "shell")
add("mbolts", "Motor screws 8 × M20 10.9", mot_bolts, "#3c3f44", 850, DR, "shell")
add("hoses", "Hoses A, B (3/4 in) + case drain", hoses, "#24272a", 950, DR, "shell")
TR, JK = "Thrust ring", "Jacking cylinders"
add("tring", "Thrust ring 76.2 thk A572-50, Ø609.6 × Ø400 (Rev A)", t_ring, "#5b8c6e", 1100, TR, "shell")
add("tsaddles", "Saddle blocks ×4, 144 × 100 × 45.5, Ø65 seat", t_blocks, "#6f9f80", 1100, TR, "shell")
add("tears", "Saddle ears ×8, 20 × 80, R40, Ø39.5 slotted 3", t_ears, "#82b191", 1100, TR, "shell")
add("tsadwelds", "Saddle welds, 8 mm fillet (none past the ring OD)", t_welds, "#c99a3c", 1100, TR, "shell")
for a_, clk in zip(TR_ANGS, (2, 4, 8, 10)):
    add(f"tpin{int(a_)}", f"Saddle pin Ø38.1 × 160, 4140 HT, {clk} o'clock", t_pins[a_], "#e0a030", 1100, TR, "shell")
add("jcyl", "Chief WT 5 × 24 ×4, retracted 889 (envelope)", jacks, "#a83232", 1400, JK, "shell")

parts = {p[0]: p for p in P}


def vol(a, b):
    try:
        return round(a.intersect(b).val().Volume() / 1000.0, 2)
    except Exception as e:
        return f"ERR {type(e).__name__}"


if __name__ == "__main__" and "--check" in sys.argv:
    g = lambda k: parts[k][2]
    rot = comp([g(k) for k in ("shaft", "f_ir", "backing", "sw", "spacer", "r_ir", "mb", "nut")])
    stat = comp([g(k) for k in ("tube", "f_or", "hw", "r_or", "carrier")])
    head = comp([g(k) for k in ("spider", "gussets", "hubring", "sleeve")])
    pairs = {
        "f_rol/f_or": ("f_rol", "f_or"), "f_rol/f_ir": ("f_rol", "f_ir"), "f_cage/f_or": ("f_cage", "f_or"), "f_cage/f_rol": ("f_cage", "f_rol"),
        "t_rol/sw": ("t_rol", "sw"), "t_rol/hw": ("t_rol", "hw"), "t_rol/tube": ("t_rol", "tube"), "sw/hw": ("sw", "hw"),
        "r_rol/r_or": ("r_rol", "r_or"), "f_or/tube": ("f_or", "tube"), "r_or/tube": ("r_or", "tube"), "hw/tube": ("hw", "tube"),
        "spacer/hw": ("spacer", "hw"), "spacer/t_rol": ("spacer", "t_rol"), "nut/tube": ("nut", "tube"), "mb/nut": ("mb", "nut"),
        "shaft/tube": ("shaft", "tube"), "sealcase/carrier": ("sealcase", "carrier"), "seallip/sleeve": ("seallip", "sleeve"),
        "halfA/ring1": ("halfA", "ring1"), "halfA/tube": ("halfA", "tube"), "halfB/tube": ("halfB", "tube"), "halfA/halfB": ("halfA", "halfB"),
        "splitscrews/halfB_shank_in_thread": ("splitscrews", "halfB"), "pins/tube": ("pin45", "tube"), "pins/halfA": ("pin45", "halfA"), "pipewelds/ring1": ("pipewelds", "ring1"), "pipewelds/pipes": ("pipewelds", "pipes"),
        "flscrews/halfA": ("flscrews", "halfA"), "tube/ring1": ("tube", "ring1"), "purge/ring1": ("purge", "ring1"), "purge/tube": ("purge", "tube"), "purgefit/tube": ("purgefit", "tube"), "purgefit/ring1": ("purgefit", "ring1"),
        "spider/gussets": ("spider", "gussets"), "gussets/hubring": ("gussets", "hubring"), "gussets/sleeve": ("gussets", "sleeve"),
        "headwelds/pipes": ("headwelds", "pipes"), "la/shaft": ("la", "shaft"), "la/hubring": ("la", "hubring"), "cap/spider": ("cap", "spider"),
        "capholders/spider": ("capholders", "spider"), "holders/cap": ("holders", "cap"), "lascrews/cap": ("lascrews", "cap"),
        "sleeve/carrier": ("sleeve", "carrier"), "sleeve/carscrews": ("sleeve", "carscrews"), "headwelds/carrier": ("headwelds", "carrier"),
        "headwelds/carscrews": ("headwelds", "carscrews"), "headwelds/halfA": ("headwelds", "halfA"), "gussets/halfA": ("gussets", "halfA"),
        "adapter/tube": ("adapter", "tube"), "adapter/pipes": ("adapter", "pipes"), "adapter/gsupply": ("adapter", "gsupply"), "gsupply/tube": ("gsupply", "tube"), "gsupply/pipes": ("gsupply", "pipes"), "fin30/shell": ("fin30", "shell"), "fin90/shell": ("fin90", "shell"), "finwelds/shell": ("finwelds", "shell"),
        "adapter/hub1": ("adapter", "hub1"), "adscrews/hub1": ("adscrews", "hub1"), "adscrews/tube_thread": ("adscrews", "tube"),
        "hub1/shaft": ("hub1", "shaft"), "hub1la/shaft": ("hub1la", "shaft"), "hub1/elast": ("hub1", "elast"), "hub2/elast": ("hub2", "elast"),
        "hub1/hub2": ("hub1", "hub2"), "hub2/adapter": ("hub2", "adapter"), "mshaft/hub2": ("mshaft", "hub2"), "motor/adapter": ("motor", "adapter"),
        "motor/pipes": ("motor", "pipes"), "motor/saddles": ("motor", "saddles"), "motor/shell": ("motor", "shell"), "hoses/pipes": ("hoses", "pipes"),
        
        "gsupply/saddles": ("gsupply", "saddles"), "gsupply/motor": ("gsupply", "motor"), "hub1scr/hub2": ("hub1scr", "hub2"),
        "legs/pipes": ("legs", "pipes"), "legs/saddles": ("legs", "saddles"), "legs/taps": ("legs", "taps"), "eye/shaft": ("eye", "shaft"),
        "mbolts/motor": ("mbolts", "motor"),
        "tring/shell": ("tring", "shell"), "tring/pipes": ("tring", "pipes"), "tring/motor": ("tring", "motor"), "tring/hoses": ("tring", "hoses"),
        "tring/gsupply": ("tring", "gsupply"), "tsaddles/tring": ("tsaddles", "tring"), "tears/tsaddles": ("tears", "tsaddles"),
        "tsadwelds/tring": ("tsadwelds", "tring"), "tsadwelds/tsaddles": ("tsadwelds", "tsaddles"), "tpin60/tears": ("tpin60", "tears"),
        "jcyl/tring": ("jcyl", "tring"), "jcyl/tsaddles": ("jcyl", "tsaddles"), "jcyl/tears": ("jcyl", "tears"), "jcyl/tpin60": ("jcyl", "tpin60"),
        "jcyl/hoses": ("jcyl", "hoses"), "jcyl/gsupply": ("jcyl", "gsupply"), "tsaddles/gsupply": ("tsaddles", "gsupply"),
    }
    out = {k: vol(g(a), g(b)) for k, (a, b) in pairs.items()}
    print(json.dumps(out, indent=0))
    masses = {}
    for k, name, wp, col, dx, grp, ag in P:
        masses[grp] = masses.get(grp, 0) + wp.val().Volume() * 7.85e-6
    print({k: round(v, 1) for k, v in masses.items()})
    print("motor kg", round(g("motor").val().Volume() * 7.85e-6, 1), "23228 kg", round(sum(g(k).val().Volume() for k in ("f_ir", "f_or", "f_rol", "f_cage")) * 7.85e-6, 1))
    print("overall bit tip to motor rear", 1225 - (X_ARM_F - 42), "to hose end", 1247 + 260 - (X_ARM_F - 42), "motor past shield rear", 1225 - SH_X1)
    kg = lambda *ks: round(sum(g(k).val().Volume() if len(g(k).vals()) == 1 else sum(v.Volume() for v in g(k).vals()) for k in ks) * 7.85e-6, 1)
    print("thrust ring kg: ring", kg("tring"), "saddle blocks", kg("tsaddles"), "ears", kg("tears"), "welds", kg("tsadwelds"),
          "pins", kg(*[f"tpin{int(a)}" for a in TR_ANGS]), "| cylinder envelope", kg("jcyl"), "(catalogue 4 × 52.6 = 210.4)")
    # interface with the shield rear (no jacking pipes)
    print(f"thrust ring x = {TR_X0:.1f} to {TR_X1:.1f}, cross-tube axis x = {X_CT:.1f}, cylinder cap-end pin x = {X_CT + CYL_L:.1f}")
    print(f"slurry pipe bores R{R_PIPE - 32.5:.1f}–{R_PIPE + 32.5:.1f} at 12 and 6 end at x = {SH_X1:.0f}; ring annulus R{r(TR_ID):.1f}–{r(TR_OD):.1f} covers both")
    print(f"seal-purge supply Ø10 at R209 (R204–214, {A_PURGE:.0f}°) runs to x = 1500 through the ring annulus (bore R{r(TR_ID):.0f})")
    print(f"motor body R140 / port bosses R106 / hoses R97 max inside the ring bore R{r(TR_ID):.0f}: clearance {r(TR_ID) - 140:.0f} / {r(TR_ID) - 106:.0f} / {r(TR_ID) - 97:.0f}")
    v_edge = math.sqrt(r(TR_OD) ** 2 - (SD_U / 2) ** 2) - TR_R
    print(f"saddle block outer face R{TR_R + SD_V / 2:.1f} vs ring OD R{r(TR_OD):.1f}: overhang {TR_R + SD_V / 2 - r(TR_OD):.1f} at mid-width, "
          f"{math.hypot(TR_R + SD_V / 2, SD_U / 2) - r(TR_OD):.1f} at the corners")
    L_w = SD_U + 2 * (v_edge + SD_V / 2)
    s_w = 47.5e3 / (L_w * 0.707 * 8)
    print(f"saddle fillet on the ring face: {L_w:.1f} of {2 * (SD_U + SD_V):.0f} perimeter; retract 47.5 kN: {s_w:.1f} MPa vs 145, FoS {145 / s_w:.2f}")
