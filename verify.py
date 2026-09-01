#!/usr/bin/env python3
"""verify.py -- check the things that screenshots have been used to check.

Every item here corresponds to a bug that actually shipped in this project. Reading the code
proved nothing repeatedly; this runs it, or cross-references it, and says yes or no.

    python3 verify.py raven-hook/game.jsx
"""
import base64
import io
import json
import os
import re
import subprocess
import sys
import tempfile

FAIL = []
WARN = []


def ok(label, good, detail=""):
    print("  %s  %-52s %s" % ("PASS" if good else "FAIL", label, detail))
    if not good:
        FAIL.append(label)


def warn(label, detail=""):
    print("  WARN  %-52s %s" % (label, detail))
    WARN.append(label)


def load(path):
    return open(path, encoding="utf-8").read()


def module_harness(src, exports):
    """Everything above `export default function` is plain JS with no browser dependencies,
    so it can be required in node. This is what makes real verification possible at all."""
    head = src[:src.index("export default function")]
    head = "\n".join(l for l in head.split("\n") if not l.startswith("import "))
    fd, p = tempfile.mkstemp(suffix=".cjs")
    os.write(fd, (head + "\nmodule.exports = { %s };\n" % ", ".join(exports)).encode())
    os.close(fd)
    return p


def node(script):
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=120)
    if r.returncode:
        return None, (r.stderr or "").strip().split("\n")[-1]
    return r.stdout.strip(), None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "raven-hook/game.jsx"
    root = os.path.dirname(os.path.abspath(path))
    src = load(path)
    assets = os.path.join(root, "assets")

    print("\n=== IRON LION VERIFY ===")
    print("file  %s  %.3f MB  %d lines" % (path, len(src) / 1e6, src.count("\n")))
    tag = re.search(r'const BUILD_TAG = "([^"]+)"', src)
    print("build %s\n" % (tag.group(1) if tag else "?"))

    # ---- 1. it parses, and the three scope checkers agree ----
    print("[1] syntax and scope")
    # node treats .jsx as ESM; copy to .js the way check_all.py does
    fd, tmpjs = tempfile.mkstemp(suffix=".js")
    os.write(fd, src.encode()); os.close(fd)
    r = subprocess.run(["node", "--check", tmpjs], capture_output=True, text=True)
    os.unlink(tmpjs)
    ok("node --check", r.returncode == 0, (r.stderr or "").split("\n")[0][:60])
    for chk in ("check_all.py", "check_nullsafe.py"):
        cp = os.path.join(root, chk)
        if not os.path.exists(cp):
            warn(chk + " not present")
            continue
        r = subprocess.run([sys.executable, cp, path], capture_output=True, text=True)
        ok(chk, r.returncode == 0, (r.stdout or "").strip().split("\n")[-1][:60])

    # ---- 2. every asset key referenced is registered, and every file exists ----
    print("\n[2] assets")
    # ^\s* anchors it to a registration line, not a CSS url(assets/...) inside a style
    reg = dict(re.findall(r'^\s*(\w+): "(assets/[^"]+)"', src, re.M))
    emb = set(re.findall(r'(\w+): "data:image/', src))
    missing_files = [k for k, v in reg.items() if not os.path.exists(os.path.join(root, v))]
    ok("registered files present on disk", not missing_files,
       ("missing: " + " ".join(missing_files[:6])) if missing_files else
       "%d hosted, %d embedded" % (len(reg), len(emb)))

    known = set(reg) | emb
    used = set(re.findall(r'imgs\.current\.(\w+)', src))
    used |= set(re.findall(r'imgs\.current\["(\w+)"\]', src))
    unknown = sorted(u for u in used if u not in known and not u.startswith("_"))
    if unknown:
        # a guarded fallback to a retired key is dead code, not a fault
        warn("imgs.current keys not registered", " ".join(unknown[:8]) + " (check they are guarded)")
    else:
        ok("imgs.current keys all registered", True, "%d keys" % len(used))

    # ---- 3. comic panels ----
    print("\n[3] comic pages")
    mi = src.index("const MISSIONS = [")
    mblk = src[mi:src.index("\n    ];", mi)]
    panels = re.findall(r'img: "(\w+)"', mblk)
    tables = set(re.findall(r'(\w+p_\d): "assets/', src))
    ok("every panel img is in PNL/PN2/DVN", all(p in tables for p in panels),
       "%d panels" % len(panels))
    gone = [p for p in panels if not os.path.exists(os.path.join(assets, p + ".webp"))]
    ok("every panel file exists", not gone, " ".join(gone[:6]))
    arts = len(re.findall(r'art: "', mblk))
    ok("every panel has art AND a description", arts == len(panels),
       "%d img / %d art" % (len(panels), arts))

    # ---- 4. the mission chain resolves ----
    print("\n[4] missions")
    ms = []
    for m in re.finditer(r'id: "(\w+)", title: "([^"]+)"', mblk):
        seg = mblk[m.start():m.start() + 420]
        d = {"id": m.group(1), "title": m.group(2)}
        for k in ("give", "obj", "needs"):
            r2 = re.search(k + r': "(\w+)"', seg)
            d[k] = r2.group(1) if r2 else None
        ms.append(d)
    ids = {x["id"] for x in ms}
    bad_needs = [x["id"] for x in ms if x["needs"] and x["needs"] not in ids]
    ok("every `needs` points at a real mission", not bad_needs, " ".join(bad_needs))
    reach, frontier = set(), [x["id"] for x in ms if not x["needs"]]
    while frontier:
        cur = frontier.pop()
        if cur in reach:
            continue
        reach.add(cur)
        frontier += [y["id"] for y in ms if y["needs"] == cur]
    ok("every mission is reachable from a root", reach == ids,
       "orphans: " + " ".join(sorted(ids - reach)))
    givers = {x["give"] for x in ms}
    ok("givers are MENTOR or SCENE only", givers <= {"MENTOR", "SCENE"}, " ".join(sorted(givers)))

    # ---- 5. weapons ----
    print("\n[5] weapons")
    ki = src.index("const WPN_KIT = {")
    kblk = src[ki:src.index("};", ki)]
    kitted = set(re.findall(r'\["(\w+)", \d+\]', kblk))
    kitted |= set(re.findall(r'\["(\w+)", \d+\]', src[src.index("WPN_KIT_OLD"):
                                                      src.index("WPN_KIT_OLD") + 200]))
    ai = src.index("const WPN = {")
    plates = set(re.findall(r"^      (\w+): \[", src[ai:src.index("const WPN_SCALE", ai)], re.M))
    ok("every kitted weapon has a plate", kitted <= plates,
       " ".join(sorted(kitted - plates)))
    ammo = set(re.findall(r"(\w+): \d+", src[src.index("const WPN_AMMO"):
                                             src.index("const WPN_AMMO") + 700]))
    ok("every plate has an ammo entry", plates <= ammo, " ".join(sorted(plates - ammo)))

    # ---- 6. character sheets: rows vs what the code will index ----
    print("\n[6] character sheets")
    at = src.index("const ACTORTOP = {")
    ablk = src[at:src.index("\n    };", at)]
    sheets = re.findall(r'(\w+):\s*\{ sheet: "(\w+)",\s*lift:[^,]+,\s*types: (\d+), builds: (\d+)',
                        ablk)
    for name, sheet, types, builds in sheets:
        types, builds = int(types), int(builds)
        b64 = re.search(sheet + r': "data:image/\w+;base64,([A-Za-z0-9+/=]+)"', src)
        if b64:
            from PIL import Image
            im = Image.open(io.BytesIO(base64.b64decode(b64.group(1))))
            rows = im.height // 46
        else:
            f = reg.get(sheet)
            if not f or not os.path.exists(os.path.join(root, f)):
                warn("%s sheet %s not found" % (name, sheet))
                continue
            from PIL import Image
            rows = Image.open(os.path.join(root, f)).height // 46
        need = (builds - 1) * types + (types - 1)
        ok("%s: max row %d < %d rows" % (name, need, rows), need < rows, sheet)

    # ---- 7. run the world generator ----
    print("\n[7] world generation (node)")
    try:
        hp = module_harness(src, ["genBuildings", "buildingPlans", "floorKind", "SX", "PITCH",
                                  "CASINO_CELL", "DEN_CELL", "CIVIC", "LEADERS", "N"])
        out, err = node("""
          const M = require(%s);
          const rnd = (() => { let s = 987654321;
            return () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; }; })();
          const gen = (zone, i, j) => M.genBuildings(zone, M.SX(i), M.SX(j),
                                       M.SX(i+1), M.SX(j+1), rnd, i, j);
          const res = {};
          const c = M.CASINO_CELL;
          const kes = gen('neon', c.i, c.j).find(b => b.landmark);
          res.kestrel = kes ? { floors: kes.floors, biz: kes.biz,
                                door: kes.door && kes.door.side,
                                plans: M.buildingPlans(kes).map(p => ({
                                  kind: p.kind,
                                  rooms: p.rooms.map(r => r.k),
                                  props: p.props.length })) } : null;
          res.civic = M.CIVIC.map(cv => {
            const b = gen(null, cv.cell.i, cv.cell.j)[0];
            return { key: cv.key, plan: b ? M.floorKind(b, 0) : null,
                     rooms: b ? M.buildingPlans(b)[0].rooms.map(r => r.k) : [] };
          });
          res.leaders = Object.keys(M.LEADERS).length;
          console.log(JSON.stringify(res));
        """ % json.dumps(hp))
        if err:
            ok("module scope loads in node", False, err[:70])
        else:
            data = json.loads(out)
            k = data["kestrel"]
            ok("Kestrel generates", bool(k),
               "floors=%s biz=%s door=%s" % (k["floors"], k["biz"], k["door"]) if k else "")
            if k:
                want = ["casino", "cardroom", "vip"]
                got = [p["kind"] for p in k["plans"]]
                ok("Kestrel floors are casino/cardroom/vip", got == want, " ".join(got))
                for f, p in enumerate(k["plans"]):
                    ok("  floor %d has a gaming room and props" % f,
                       "gaming" in p["rooms"] and p["props"] > 0,
                       "%d rooms, %d props" % (len(p["rooms"]), p["props"]))
            for cv in data["civic"]:
                ok("civic %s -> %s" % (cv["key"], cv["plan"]),
                   cv["plan"] in ("cityhall", "precinct", "sechq"),
                   ", ".join(cv["rooms"][:5]))
            ok("leaders table", data["leaders"] >= 9, "%d leaders" % data["leaders"])
    except Exception as e:
        ok("world generation", False, str(e)[:70])

    print("\n=== %d FAIL, %d WARN ===" % (len(FAIL), len(WARN)))
    for f in FAIL:
        print("  FAILED: " + f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
