"""Collision audit of the assembly animation: replays every step's motion (same kinematics as the viewer)
and reports any moving part that passes through another visible part at intermediate positions.
Pairs that already overlap in the finished state (threads in tapped holes etc.) are ignored."""
import importlib, math, os, sys, json
import cadquery as cq
A = importlib.import_module(os.environ.get("ASM", "asm_revI"))   # ASM=asm_revH replays the Rev H sequence
from paths import AUDIT
M = A.M
V3 = cq.Vector
groups, steps = A.groups, A.steps
pg = A.ag
SHAPES = {k: (p[2].val() if len(p[2].vals()) == 1 else cq.Compound.makeCompound(p[2].vals())) for k, p in M.parts.items()}
BB = {k: s.BoundingBox() for k, s in SHAPES.items()}
TOL = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5      # cm3


def ease(u):
    return 2 * u * u if u < 0.5 else 1 - (-2 * u + 2) ** 2 / 2


def rotz(v, th):
    a = math.radians(th)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a), v[2])


def lerp_pose(a, b, u, pivot):
    c = (pivot, 0, 0)
    pa = [x + y for x, y in zip(rotz(c, a["th"]), a["t"])]
    pb = [x + y for x, y in zip(rotz(c, b["th"]), b["t"])]
    th = a["th"] + (b["th"] - a["th"]) * u
    p = [x + (y - x) * u for x, y in zip(pa, pb)]
    rc = rotz(c, th)
    return {"th": th, "t": [p[i] - rc[i] for i in range(3)]}


# states after each step
gp = {g: v["init"] for g, v in groups.items()}
vis = {k: False for k in M.parts}
states = [(dict(gp), dict(vis))]
for s in steps:
    for g, w in s["moves"].items():
        gp[g] = w[-1]
    for keys, _ in s["add"]:
        for k in keys:
            vis[k] = True
    for k, _ in s["remove"]:
        vis[k] = False
    states.append((dict(gp), dict(vis)))


def world_bb(k, pose, off):
    b = BB[k]
    pts = [rotz((x, y, z), pose["th"]) for x in (b.xmin, b.xmax) for y in (b.ymin, b.ymax) for z in (b.zmin, b.zmax)]
    pts = [(p[0] + pose["t"][0] + off[0], p[1] + pose["t"][1] + off[1], p[2] + pose["t"][2] + off[2]) for p in pts]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def overlap(b1, b2, m=0.0):
    return all(b1[0][i] < b2[1][i] - m and b2[0][i] < b1[1][i] - m for i in range(3))


def placed(k, pose, off):
    s = SHAPES[k].rotate(V3(0, 0, 0), V3(0, 0, 1), pose["th"])
    return s.translate(V3(pose["t"][0] + off[0], pose["t"][1] + off[1], pose["t"][2] + off[2]))


def ivol(a, b):
    try:
        return a.intersect(b).Volume() / 1000.0
    except Exception:
        return -1.0


final_gp, final_vis = states[-1]
final_overlap = {}


def final_ov(a, b):
    key = tuple(sorted((a, b)))
    if key not in final_overlap:
        final_overlap[key] = ivol(placed(a, final_gp[pg[a]], (0, 0, 0)), placed(b, final_gp[pg[b]], (0, 0, 0)))
    return final_overlap[key]


report = []
for k_, s in enumerate(steps, start=1):
    (gp0, vis0), (gp1, vis1) = states[k_ - 1], states[k_]
    adds = {kk: w for keys, w in s["add"] for kk in keys}
    rems = {kk: w for kk, w in s["remove"]}
    moving_groups = set(s["moves"])
    if not adds and not moving_groups and not rems:
        continue
    dist = max([math.hypot(*w) for w in adds.values()] + [math.hypot(*w) for w in rems.values()] + [0.0])
    for g, w in s["moves"].items():
        pts = [gp0[g]] + w
        for p_, q_ in zip(pts, pts[1:]):
            dist = max(dist, math.dist(p_["t"], q_["t"]) + abs(q_["th"] - p_["th"]) * math.pi / 180 * 1000)
    nsamp = int(min(90, max(6, dist / 15)))
    for u in [(i + 0.5) / nsamp for i in range(nsamp)]:
        gpose = {}
        for g, p0 in gp0.items():
            w = s["moves"].get(g)
            if not w:
                gpose[g] = p0
                continue
            pts = [p0] + w
            m = len(pts) - 1
            x = u * m
            seg = min(int(x), m - 1)
            gpose[g] = lerp_pose(pts[seg], pts[seg + 1], ease(x - seg), groups[g]["pivot"])
        visible = [kk for kk in M.parts if vis1.get(kk) or (kk in rems)]
        offs = {}
        for kk in visible:
            if kk in adds:
                offs[kk] = [c * (1 - ease(u)) for c in adds[kk]]
            elif kk in rems:
                offs[kk] = [c * ease(u) for c in rems[kk]]
            else:
                offs[kk] = [0, 0, 0]
        movers = [kk for kk in visible if kk in adds or kk in rems or pg[kk] in moving_groups]
        for a in movers:
            ba = world_bb(a, gpose[pg[a]], offs[a])
            for b in visible:
                if b == a:
                    continue
                # parts moving rigidly together cannot collide
                same = (pg[a] == pg[b] and a not in adds and b not in adds and a not in rems and b not in rems)
                if same:
                    continue
                if pg[a] in moving_groups and pg[b] in moving_groups and a not in adds and b not in adds \
                        and s["moves"][pg[a]] == s["moves"][pg[b]] and groups[pg[a]]["pivot"] == groups[pg[b]]["pivot"]:
                    continue
                if b in movers and b < a:
                    continue
                bb_ = world_bb(b, gpose[pg[b]], offs[b])
                if not overlap(ba, bb_, 0.5):
                    continue
                v = ivol(placed(a, gpose[pg[a]], offs[a]), placed(b, gpose[pg[b]], offs[b]))
                if v > TOL and v > final_ov(a, b) + TOL:
                    report.append((k_, s["title"], u, a, b, round(v, 1)))
    print(f"step {k_:2d} done, hits so far {len(report)}", flush=True)

seen = {}
for k_, t, u, a, b, v in report:
    key = (k_, a, b)
    prev = seen.get(key, (0.0, t))[0]
    seen[key] = (max(prev, v), t)
print("\nCOLLISIONS (step, title, parts, max cm3):")
for (k_, a, b), (v, t) in sorted(seen.items(), key=lambda x: x[0]):
    print(f"  {k_:2d} {t:32s} {a:12s} x {b:12s} {v:8.1f}")
out = sys.argv[2] if len(sys.argv) > 2 else str(AUDIT / "audit_result.json")
json.dump([list(k) + [v[0], v[1]] for k, v in seen.items()], open(out, "w"))
