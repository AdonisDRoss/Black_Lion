#!/usr/bin/env python3
"""Pre-flight for raven-hook/game.jsx. Every check here exists because the thing it
looks for has actually broken the build at least once."""
import re, sys, os, subprocess, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "raven-hook", "game.jsx")
ASSETS = os.path.join(ROOT, "raven-hook", "assets")
fails, warns = [], []

if not os.path.exists(GAME):
    sys.exit("game.jsx not found at %s" % GAME)
s = open(GAME, encoding="utf-8").read()
print("game.jsx  %.3f MB" % (len(s.encode()) / 1048576))

# 1 -- Safari has refused to load this file over ~2.4 MB before.
mb = len(s.encode()) / 1048576
if mb > 2.4:
    warns.append("size %.3f MB -- Safari has failed to load over ~2.4 MB" % mb)

# 2 -- brace balance, strings/comments/template literals stripped
out, i, n = [], 0, len(s)
while i < n:
    c = s[i]
    if c == "/" and i + 1 < n and s[i+1] == "/":
        j = s.find("\n", i); i = n if j < 0 else j; continue
    if c == "/" and i + 1 < n and s[i+1] == "*":
        j = s.find("*/", i + 2); i = n if j < 0 else j + 2; continue
    if c in "\"'`":
        q = c; i += 1
        while i < n:
            if s[i] == "\\": i += 2; continue
            if s[i] == q: i += 1; break
            i += 1
        continue
    out.append(c); i += 1
t = "".join(out)
bal = (t.count("{") - t.count("}"), t.count("(") - t.count(")"), t.count("[") - t.count("]"))
print("brace balance", bal)
if bal != (0, 0, 0): fails.append("unbalanced %s" % (bal,))

# 3 -- node --check catches syntax; loading MODULE SCOPE catches a duplicate const,
#      which node --check does not and which stops the file loading at all.
open("/tmp/_g.js", "w").write(s)
if subprocess.run(["node", "--check", "/tmp/_g.js"]).returncode != 0:
    fails.append("node --check failed")
try:
    k = s.index("export default function")
    head = "\n".join(l for l in s[:k].split("\n") if not l.startswith("import "))
    open("/tmp/_m.cjs", "w").write(head + "\nmodule.exports={};\n")
    r = subprocess.run(["node", "-e", 'require("/tmp/_m.cjs")'], capture_output=True, text=True)
    if r.returncode != 0:
        fails.append("module scope will not load: " + r.stderr.strip().split("\n")[0])
    else:
        print("module scope loads OK")
except ValueError:
    warns.append("could not locate module scope")

# 4 -- every registered asset path must exist on disk. This is the check that would have
#      caught eight roof plates being registered and drawn by nothing.
paths = sorted(set(re.findall(r'"(assets/[A-Za-z0-9_\-/]+\.(?:png|webp|mp3))"', s)))
tmpl = sorted(set(re.findall(r'"(assets/[a-z]+/)"\s*\+', s)))
if os.path.isdir(ASSETS):
    missing = [p for p in paths if not os.path.exists(os.path.join(ROOT, "raven-hook", p))]
    print("asset paths referenced: %d, missing from repo: %d" % (len(paths), len(missing)))
    for p in missing[:30]: print("   MISSING", p)
    if missing:
        warns.append("%d referenced asset files are not in the repo yet" % len(missing))
else:
    print("asset paths referenced: %d (no assets/ dir here, skipping existence check)" % len(paths))

# 5 -- duplicate `const NAME =` at TRUE module scope (indent 0). Indentation is NOT scope:
#      an earlier version keyed on indent and failed the build on fifty innocent locals that
#      live in different functions. Check 3 (module scope loads) is the authoritative test for
#      this class of bug; this only names the culprit when it fires.
decl = {}
for m2 in re.finditer(r"^const ([A-Za-z_$][\w$]*)\s*=", s, re.M):
    decl.setdefault(m2.group(1), []).append(m2.start())
for nm, at in sorted(decl.items()):
    if len(at) > 1:
        fails.append("duplicate module-scope const %s (%d times) -- file will not load" % (nm, len(at)))
print()
for w in warns: print("WARN ", w)
for f in fails: print("FAIL ", f)
print("\n%s" % ("FAILED" if fails else "OK"))
sys.exit(1 if fails else 0)
