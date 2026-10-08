#!/usr/bin/env python3
"""negative_control.py — prove each self-validation test CAN fail (i.e. is load-bearing).

For each scenario we copy this folder to a temp dir, disable exactly the one guard the
scenario is supposed to test, and re-run run_demo.py there.  If the scenario then goes
FAIL, the guard is what makes it pass — the test is not vacuous.

    python negative_control.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
# Same rule as run_demo.py: inherit the caller's interpreter unless PT_PY is set.
INTERP = os.environ.get("PT_PY") or sys.executable

# (scenario, guest source patch: old -> new)
CONTROLS = [
    ("a_heartbeat_timeout",
     "host_alive = bool(host_beat) and (now_ms - host_beat) < HEARTBEAT_TIMEOUT_MS",
     "host_alive = True  # NEGATIVE CONTROL: never see the host die"),
    ("b_epoch_invalidation",
     "epoch_valid = False",
     "epoch_valid = True  # NEGATIVE CONTROL: never invalidate on a restart"),
    ("c_steep_wall",
     "if ang <= MAX_SLOPE_DEG:",
     "if ang <= 100.0:  # NEGATIVE CONTROL: everything is walkable"),
]


def run_case(script_old, script_new):
    tmp = tempfile.mkdtemp(prefix="pt_neg_")
    try:
        for fn in os.listdir(HERE):
            src = os.path.join(HERE, fn)
            if fn.startswith("_") or fn.endswith(".jsonl") or fn.endswith(".summary") \
                    or fn == "negative_control.py":
                continue
            dst = os.path.join(tmp, fn)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        gp = os.path.join(tmp, "fake_guest.py")
        text = open(gp, encoding="utf-8").read()
        assert script_old in text, f"patch anchor not found: {script_old!r}"
        open(gp, "w", encoding="utf-8").write(text.replace(script_old, script_new))
        stale = os.path.join(tmp, "demo_trace.json")
        if os.path.exists(stale):
            os.remove(stale)
        env = dict(os.environ, PT_SCHEMA=os.path.normpath(
            os.path.join(HERE, "..", "v0-schema", "schema.yaml")))
        p = subprocess.run([INTERP, os.path.join(tmp, "run_demo.py")],
                           cwd=tmp, capture_output=True, text=True, env=env)
        if p.returncode not in (0, 1):            # 1 == some scenario failed, which is the point
            raise RuntimeError(f"neg-control run crashed:\n{p.stderr[-2000:]}")
        return json.load(open(os.path.join(tmp, "demo_trace.json"), encoding="utf-8"))["verdict"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ok = True
    for scen, old, new in CONTROLS:
        verdict = run_case(old, new)
        flipped = verdict[scen.split("_")[0]] is False
        print(f"  disable-guard for {scen:24s} -> verdict={verdict}  "
              f"{'OK (test is load-bearing)' if flipped else '*** TEST IS VACUOUS ***'}")
        ok = ok and flipped
    print("NEGATIVE CONTROL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
