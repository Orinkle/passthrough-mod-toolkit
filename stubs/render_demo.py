#!/usr/bin/env python3
"""render_demo.py — turn demo_trace.json into deterministic ANSI terminal text.

This is the README "30-second demo": the whole passthrough proof is visible as text, with no
game, no engine, no GUI.  Deterministic: same demo_trace.json -> byte-identical output.

    python render_demo.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

G = "\033[32m"     # green  - guest / alive
R = "\033[31m"     # red    - frozen / invalid / wall
B = "\033[34m"     # blue   - floor
Y = "\033[33m"     # yellow - guest head / highlight
D = "\033[2m"      # dim
E = "\033[0m"


def timeline(trace, key, invert=False, width=64):
    """A fixed-width bar: '#' when key is truthy (invert flips it), '.' otherwise."""
    if not trace:
        return ""
    n = len(trace)
    step = max(1, n // width)
    marks = trace[::step][:width]
    out = []
    for r in marks:
        v = bool(r.get(key))
        good = (not v) if invert else v
        out.append((G + "#" + E) if good else (R + "." + E))
    return "".join(out)


def render_wall(trace, wall_x, wall_h, floor_y):
    xmin, xmax = -2.0, 12.0
    ymin, ymax = -1.0, 8.0
    Wc, Hc = 64, 20
    grid = [[" "] * Wc for _ in range(Hc)]

    def px(x):
        return min(Wc - 1, max(0, int((x - xmin) / (xmax - xmin) * (Wc - 1))))

    def py(y):
        return min(Hc - 1, max(0, int((ymax - y) / (ymax - ymin) * (Hc - 1))))

    fy = py(floor_y)
    for cx in range(Wc):
        grid[fy][cx] = B + "~" + E
    wx = px(wall_x)
    for cy in range(py(wall_h), py(0.0) + 1):
        grid[cy][wx] = R + "#" + E
    last = None
    for r in trace:
        cx, cy = px(r["x"]), py(r["y"])
        grid[cy][cx] = (R + "x" + E) if r.get("blocked") else (G + "o" + E)
        last = (cx, cy)
    if last:
        grid[last[1]][last[0]] = Y + "@" + E
    lines = [f"  side view   {G}o{E}/@=guest  {R}#{E}=wall(x={wall_x})  {B}~{E}=floor"]
    for row in grid:
        lines.append("  |" + "".join(row) + "|")
    return "\n".join(lines)


def main():
    path = os.path.join(HERE, "demo_trace.json")
    if not os.path.exists(path):
        print("demo_trace.json not found — run run_demo.py first", file=sys.stderr)
        return 1
    d = json.load(open(path, encoding="utf-8"))
    p = d["params"]
    S = d["scenarios"]
    out = []
    out.append("=" * 78)
    out.append(" PTmodmaker unified passthrough stubs - demo trace  (no game, no engine)")
    out.append("=" * 78)
    out.append(f" transport       : {p['transport']}")
    out.append(f" mapping bytes   : {p['map_bytes']}   units_per_block={p['units_per_block']}")
    cc = d.get("crosscheck_other_binding", {})
    if cc.get("present"):
        out.append(f" cross-check     : {cc['structs_compared']} struct sizes vs another "
                   f"generator's binding -> {'AGREE' if cc.get('agree') else 'MISMATCH'}")
    out.append("")

    a = S["a_heartbeat_timeout"]
    out.append(f"[a] heartbeat timeout   host killed @ {a['host_killed_at_s']}s")
    out.append(f"    guest froze={a['guest_froze']}  stayed frozen to exit="
               f"{a['stayed_frozen_to_exit']}  exit={a['guest_exit_code']}  "
               f"stderr={a['guest_stderr']!r}")
    out.append(f"    alive/frozen  t=0 .. {a['trace'][-1]['t']:.1f}s   "
               f"{D}green = host alive, red = frozen{E}")
    out.append("    " + timeline(a["trace"], "frozen", invert=True))
    out.append(f"    => {'PASS' if a['passed'] else 'FAIL'}")

    b = S["b_epoch_invalidation"]
    out.append("")
    out.append(f"[b] epoch invalidation  {b['old_epoch']} -> {b['new_epoch']}  "
               f"(host restart)")
    out.append(f"    session discards={b['session_discards']}  invalid ticks={b['invalid_ticks']}  "
               f"teleports={b['teleports_total']} (late={b['late_teleports']})  "
               f"max tick dx={b['max_single_tick_dx']}")
    out.append(f"    epoch-sensitive  t=0 .. {b['trace'][-1]['t']:.1f}s   "
               f"{D}green = epoch valid, red = stale epoch discarded{E}")
    out.append("    " + timeline(b["trace"], "epoch_valid"))
    out.append(f"    => {'PASS' if b['passed'] else 'FAIL'}")

    c = S["c_steep_wall"]
    out.append("")
    out.append(f"[c] steep wall          wall at x={c['wall_x']} h={c['wall_height']}  "
               f"slope={c['wall_slope_deg']}deg (walkable limit {c['walkable_limit_deg']}deg)")
    out.append(f"    guest max x={c['guest_max_x']}  max y={c['guest_max_y']}  "
               f"crossed={c['crossed_wall']}  climbed={c['climbed_wall']}  "
               f"blocked ticks={c['blocked_ticks']}")
    out.append(render_wall(c["trace"], c["wall_x"], c["wall_height"], 0.0))
    out.append(f"    => {'PASS' if c['passed'] else 'FAIL'}")

    out.append("")
    v = d["verdict"]
    line = "verdict: " + "  ".join(f"{k}={'PASS' if v[k] else 'FAIL'}" for k in ("a", "b", "c"))
    line += "   OVERALL=" + ("PASS" if d["passed"] else "FAIL")
    out.append(line)
    out.append("=" * 78)
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
