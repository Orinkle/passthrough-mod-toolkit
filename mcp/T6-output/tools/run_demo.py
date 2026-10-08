#!/usr/bin/env python3
"""run_demo.py — one command, three self-validation scenarios (a / b / c).  NO game.

Each scenario runs a real fake_host process + a real fake_guest process that share one
memory mapping (see fake_host.py for why the transport is a shared mapping).  We kill the
host, restart it, or give it a wall, and check the guest's behaviour.  Everything the guest
records goes into `demo_trace.json`, which `render_demo.py` turns into the 30-second demo.

    python run_demo.py
"""
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
INTERP = "/home/zjk/.workbuddy/binaries/python/envs/default/bin/python"
sys.path.insert(0, HERE)

import layout_from_schema as L            # noqa: E402
from fake_host import (P, MAP_BYTES, WALL_X, WALL_H, PLAYER_R, MAX_SLOPE_DEG)  # noqa: E402

LINK = os.path.join(HERE, "_link.bin")


def new_link():
    fd = os.open(LINK, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
    os.ftruncate(fd, MAP_BYTES)
    os.close(fd)


def spawn(prog, *args):
    return subprocess.Popen([INTERP, os.path.join(HERE, prog), "--link", LINK, *args],
                            cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def read_trace(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                out.append(json.loads(ln))
    return out


def read_summary(path):
    p = path + ".summary"
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {}


# --------------------------------------------------------------------------- scenarios
def scenario_a():
    """a) heartbeat timeout: kill the host; the guest must freeze safely and exit clean."""
    new_link()
    gtrace = os.path.join(HERE, "_a_guest.jsonl")
    host = spawn("fake_host.py", "--seconds", "30")
    time.sleep(0.2)                                   # let the host publish first
    guest = spawn("fake_guest.py", "--seconds", "5", "--trace", gtrace)
    time.sleep(1.8)
    kill_t = time.time()
    host.terminate()
    host.wait()
    _, gerr = guest.communicate()                     # runs to its 5 s
    rc = guest.returncode
    tr = read_trace(gtrace)
    froze = [r for r in tr if r.get("frozen")]
    last_alive = max((i for i, r in enumerate(tr) if not r.get("frozen")), default=-1)
    stayed = last_alive < len(tr) - 1 and all(r.get("frozen") for r in tr[last_alive + 1:])
    passed = bool(froze) and stayed and rc == 0 and gerr.strip() == ""
    return {"host_killed_at_s": 1.8, "guest_froze": bool(froze),
            "frozen_ticks": len(froze), "stayed_frozen_to_exit": stayed,
            "guest_exit_code": rc, "guest_stderr": gerr.strip(), "crashed": rc != 0,
            "passed": passed, "trace": tr}


def scenario_b():
    """b) epoch invalidation: restart the host with a new epoch; stale data must be dropped."""
    new_link()
    gtrace = os.path.join(HERE, "_b_guest.jsonl")
    host1 = spawn("fake_host.py", "--seconds", "30", "--epoch", "1")
    time.sleep(0.2)
    guest = spawn("fake_guest.py", "--seconds", "6", "--trace", gtrace)
    time.sleep(1.8)
    host1.terminate()
    host1.wait()
    time.sleep(0.3)
    host2 = spawn("fake_host.py", "--seconds", "30", "--epoch", "2")
    _, gerr = guest.communicate()
    rc = guest.returncode
    host2.terminate()
    host2.wait()
    tr = read_trace(gtrace)
    summ = read_summary(gtrace)
    invalid = [r for r in tr if not r.get("epoch_valid", True)]
    teleports = [r["t"] for r in tr if r.get("teleported")]
    late_teleports = [t for t in teleports if t > 0.5]      # join teleport at ~t=0 is fine
    max_dx = 0.0
    for i in range(1, len(tr)):
        max_dx = max(max_dx, abs(tr[i]["x"] - tr[i - 1]["x"]))
    discards = summ.get("session_discards", 0)
    passed = (bool(invalid) and discards >= 1 and not late_teleports
              and max_dx < 0.5 and rc == 0 and gerr.strip() == "")
    return {"old_epoch": 1, "new_epoch": 2,
            "saw_epoch_invalid": bool(invalid), "invalid_ticks": len(invalid),
            "session_discards": discards,
            "teleports_total": len(teleports), "late_teleports": late_teleports,
            "max_single_tick_dx": round(max_dx, 3),
            "guest_exit_code": rc, "guest_stderr": gerr.strip(),
            "passed": passed, "trace": tr}


def scenario_c():
    """c) >50deg wall: a steeper-than-walkable AABB must act as a solid, un-climbable wall."""
    new_link()
    gtrace = os.path.join(HERE, "_c_guest.jsonl")
    host = spawn("fake_host.py", "--seconds", "30", "--wall")
    time.sleep(0.2)
    guest = spawn("fake_guest.py", "--seconds", "6", "--trace", gtrace)
    _, gerr = guest.communicate()
    rc = guest.returncode
    host.terminate()
    host.wait()
    tr = read_trace(gtrace)
    summ = read_summary(gtrace)
    max_x = max((r["x"] for r in tr), default=0.0)
    max_y = max((r["y"] for r in tr), default=0.0)
    crossed = any(r["x"] > WALL_X for r in tr)
    climbed = max_y > WALL_H
    blocked_ticks = summ.get("blocked_ticks", 0)
    passed = (not crossed) and (not climbed) and (max_x <= WALL_X - PLAYER_R + 0.3) \
        and blocked_ticks > 0 and rc == 0 and gerr.strip() == ""
    return {"wall_x": WALL_X, "wall_height": WALL_H,
            "wall_slope_deg": summ.get("wall_slope_deg"),
            "walkable_limit_deg": MAX_SLOPE_DEG,
            "guest_max_x": round(max_x, 3), "guest_max_y": round(max_y, 3),
            "crossed_wall": crossed, "climbed_wall": climbed,
            "blocked_ticks": blocked_ticks, "guest_exit_code": rc,
            "guest_stderr": gerr.strip(), "passed": passed, "trace": tr}


# --------------------------------------------------------------------------- cross-check
def crosscheck_other_binding():
    """Compare struct sizes with a *different* generator's binding (protocol_sky.py), if any.

    Independent evidence that two generators reading the same schema agree on the ABI.
    """
    try:
        import protocol_sky  # the other agent's generated Python binding, if present
    except Exception:
        return {"present": False}
    diffs = []
    for name in dir(P):
        o = getattr(protocol_sky, name, None)
        m = getattr(P, name, None)
        if isinstance(m, type) and issubclass(m, ctypes.Structure) and isinstance(o, type):
            if ctypes.sizeof(m) != ctypes.sizeof(o):
                diffs.append(f"{name}: {ctypes.sizeof(m)} vs {ctypes.sizeof(o)}")
    return {"present": True, "module": getattr(protocol_sky, "__file__", "?"),
            "structs_compared": sum(1 for n in dir(P)
                                    if isinstance(getattr(P, n), type)
                                    and issubclass(getattr(P, n), ctypes.Structure)),
            "size_mismatches": diffs, "agree": not diffs}


def main():
    L.verify("SKY")                       # schema<->ctypes assertions; hard-fails on mismatch

    out = {
        "params": {
            "interpreter": INTERP,
            "schema": os.path.normpath(os.path.join(HERE, "..", "v0-schema", "schema.yaml")),
            "transport": "shared memory mapping (MAP_SHARED over a file)",
            "map_bytes": MAP_BYTES,
            "units_per_block": getattr(P, "UNITS_PER_BLOCK", None),
            "wall": {"x": WALL_X, "height": WALL_H, "walkable_limit_deg": MAX_SLOPE_DEG},
        },
        "crosscheck_other_binding": crosscheck_other_binding(),
        "scenarios": {
            "a_heartbeat_timeout": scenario_a(),
            "b_epoch_invalidation": scenario_b(),
            "c_steep_wall": scenario_c(),
        },
    }
    out["verdict"] = {
        "a": out["scenarios"]["a_heartbeat_timeout"]["passed"],
        "b": out["scenarios"]["b_epoch_invalidation"]["passed"],
        "c": out["scenarios"]["c_steep_wall"]["passed"],
    }
    out["passed"] = all(out["verdict"].values())

    with open(os.path.join(HERE, "demo_trace.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)

    cleanup()

    for k, v in out["verdict"].items():
        print(f"  scenario {k}: {'PASS' if v else 'FAIL'}")
    print("  OVERALL:", "PASS" if out["passed"] else "FAIL")
    return 0 if out["passed"] else 1


def cleanup():
    """Drop the big per-scenario scratch files; demo_trace.json holds the traces we keep."""
    for fn in os.listdir(HERE):
        if fn.startswith("_") and (fn.endswith(".jsonl") or fn.endswith(".summary")
                                   or fn.endswith(".bin")):
            try:
                os.remove(os.path.join(HERE, fn))
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
