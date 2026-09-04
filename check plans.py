#!/usr/bin/env python3
"""check_plans.py game.jsx

Two checks written after LAYER 310, where four whole floor plans and three
furniture cases had never run and nothing said a word.

  check_dup_case_labels     duplicate `case "x":` at the same depth in one switch.
                            Legal JS. The first one wins and the rest are dead.
  check_plan_reachable      every `kind === "x"` layout branch in makeFloor must be
                            a value floorKind() can actually return, and vice versa.
"""
import re, sys

src = open(sys.argv[1] if len(sys.argv) > 1 else 'game.jsx').read()
lines = src.split('\n')
fails = []

def span(fn_name):
    """line range of a top-level function, by indent-0 def to next indent-0 def"""
    start = next(i for i, l in enumerate(lines) if l.startswith('function %s(' % fn_name))
    for i in range(start + 1, len(lines)):
        if lines[i].startswith('function ') or lines[i].startswith('const '):
            return start, i
    return start, len(lines)

# ---------- check_dup_case_labels ----------
depth, stack, seen = 0, [], 0
for n, l in enumerate(lines, 1):
    for ch in l:
        if ch == '{':
            depth += 1
        elif ch == '}':
            if stack and stack[-1][0] == depth:
                stack.pop()
            depth -= 1
    if re.search(r'\bswitch\s*\(', l):
        stack.append((depth, {}, n))
    if stack:
        for lab in re.findall(r'\bcase\s+"([^"]+)"\s*:', l):
            d, tbl, sn = stack[-1]
            if lab in tbl:
                fails.append('FAIL dup case "%s" in switch at line %d: '
                             'first at line %d, dead copy at line %d'
                             % (lab, sn, tbl[lab], n))
            else:
                tbl[lab] = n
            seen += 1
print('checked %d case labels' % seen)

# ---------- check_plan_reachable ----------
fk0, fk1 = span('floorKind')
returns = set()
for l in lines[fk0:fk1]:
    for m in re.findall(r'return\s+(.+?);', l):
        returns |= set(re.findall(r'"([a-zA-Z_0-9]+)"', m))

mf0, mf1 = span('makeFloor')
branches = {}
for n, l in enumerate(lines[mf0:mf1], mf0 + 1):
    for m in re.findall(r'\bkind === "([a-zA-Z_0-9]+)"', l):
        branches.setdefault(m, n)
# `dense` is a list of plan names, not a layout branch
dense_line = next((n for n, l in enumerate(lines[mf0:mf1], mf0 + 1) if 'const dense' in l), None)

for name, n in sorted(branches.items()):
    if name not in returns:
        fails.append('FAIL layout branch kind === "%s" (line %d) is unreachable: '
                     'floorKind() never returns it' % (name, n))
print('checked %d layout branches against %d floorKind returns'
      % (len(branches), len(returns)))

for f in fails:
    print(f)
print('%d FAIL' % len(fails))
sys.exit(1 if fails else 0)
