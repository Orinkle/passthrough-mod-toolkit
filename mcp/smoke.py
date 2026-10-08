#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smoke.py — drive server.py over real stdio JSON-RPC and record request/response pairs.

Produces smoke_log.jsonl (one {"request": ..., "response": ...} per line) for REPORT.md.
No network, no games. Run:
    <python> smoke.py

ids 1-12 are the original baseline (incl. the 4 safety refusals, which must stay REFUSED).
ids 13+ are the new evidence for the three gaps found by the newbie usability experiment:
    13 pt_schema_describe                        -> contract + annotated schema.template.yaml
    14 pt_schema_validate(header_path=<real>)    -> custom-host round-trip, diff 0
    15 pt_schema_validate(header_path, bad schema)-> per-line diff diagnostics (literal/id)
    16 pt_schema_validate(order as string list)  -> STRUCTURED error (no bare AttributeError)
    17 pt_scaffold(host=teardown)                -> own-id skeleton (never aliased to SKY)
    18 pt_schema_describe(<URL>)                 -> REFUSED (new tool is behind the same gate)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)                                   # .../03-复现路线
PL = os.path.dirname(LAB)                                     # .../passthrough-lab
PY = sys.executable
LOG = os.path.join(HERE, "smoke_log.jsonl")

REAL_HEADER = os.path.join(PL, "90-源码", "SkyCraft", "protocol", "skycraft_protocol.h")
PROBE = os.path.join(HERE, ".work", "_probe")
BAD_SCHEMA = os.path.join(PROBE, "order_as_string_list.yaml")
PERTURBED = os.path.join(PROBE, "perturbed_container.yaml")


def make_fixtures():
    """Two fixture schemas that exercise the new error/diagnostic paths (written under .work/)."""
    import yaml
    os.makedirs(PROBE, exist_ok=True)

    bad = {
        "schema_version": 1,
        "container": {
            "includes": ["#include <cstdint>"],
            "regions_template": "inline constexpr int kOff{host_state_off} = 1;\n",
            "fixed": {},
            "order": ["header", "host_state"],          # <-- string list: the old crash
        },
        "vocabulary_schema": {"required": ["a"], "optional": ["b"]},   # <-- {required,optional}
        "vocabularies": {"TEARDOWN": {"namespace": "n"}},
    }
    with open(BAD_SCHEMA, "w", encoding="utf-8") as f:
        yaml.safe_dump(bad, f, sort_keys=False, allow_unicode=True)

    with open(os.path.join(LAB, "v0-schema", "schema.yaml"), encoding="utf-8") as f:
        base = yaml.safe_load(f)
    c = base["container"]["fixed"]
    c["coltype"] = c["coltype"].replace("kColClear = 1", "kColClear = 9")     # a literal change
    c["colregion"] = c["colregion"].replace("maxX", "mxX")                    # an identifier change
    with open(PERTURBED, "w", encoding="utf-8") as f:
        yaml.safe_dump(base, f, sort_keys=False, width=100, allow_unicode=True)


REQUESTS = [
    # --- lifecycle ---
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "smoke", "version": "0"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    # --- 1) schema validate ---
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
     "params": {"name": "pt_schema_validate", "arguments": {}}},
    # --- 2) param lookup ---
    {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
     "params": {"name": "pt_param_lookup", "arguments": {"host": "skyrim", "color": "red"}}},
    {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
     "params": {"name": "pt_param_lookup", "arguments": {"color": "red"}}},
    # --- 3) stub run ---
    {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
     "params": {"name": "pt_stub_run", "arguments": {"scenario": "heartbeat"}}},
    {"jsonrpc": "2.0", "id": 7, "method": "tools/call",
     "params": {"name": "pt_stub_run", "arguments": {"scenario": "all"}}},
    # --- 4) scaffold (registered host: Skyrim -> field-matches SKY) ---
    {"jsonrpc": "2.0", "id": 8, "method": "tools/call",
     "params": {"name": "pt_scaffold", "arguments": {
         "host": "The Elder Scrolls V: Skyrim Special Edition",
         "guest": "Minecraft: Java Edition", "out_dir": ".work/scaffold_demo"}}},
    # --- safety refusals (must be refused) ---
    {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
     "params": {"name": "pt_scaffold", "arguments": {
         "host": "GTA Online", "guest": "Minecraft", "out_dir": ".work/denied1"}}},
    {"jsonrpc": "2.0", "id": 10, "method": "tools/call",
     "params": {"name": "pt_scaffold", "arguments": {
         "host": "Skyrim", "guest": "Minecraft", "out_dir": "ws://10.0.0.5:7777/sync"}}},
    {"jsonrpc": "2.0", "id": 11, "method": "tools/call",
     "params": {"name": "pt_param_lookup", "arguments": {"host": "fivem server 51.83.1.20"}}},
    {"jsonrpc": "2.0", "id": 12, "method": "tools/call",
     "params": {"name": "pt_stub_run", "arguments": {"scenario": "multiplayer"}}},
    # --- NEW: gap A — the schema's schema is now visible; failures are structured ---
    {"jsonrpc": "2.0", "id": 13, "method": "tools/call",
     "params": {"name": "pt_schema_describe", "arguments": {}}},
    # --- NEW: gap B — round-trip a USER-supplied header (the 4th game), with diagnostics ---
    {"jsonrpc": "2.0", "id": 14, "method": "tools/call",
     "params": {"name": "pt_schema_validate", "arguments": {"header_path": REAL_HEADER}}},
    {"jsonrpc": "2.0", "id": 15, "method": "tools/call",
     "params": {"name": "pt_schema_validate",
                "arguments": {"schema_path": PERTURBED, "header_path": REAL_HEADER}}},
    {"jsonrpc": "2.0", "id": 16, "method": "tools/call",
     "params": {"name": "pt_schema_validate", "arguments": {"schema_path": BAD_SCHEMA}}},
    # --- NEW: gap C — scaffold a genuinely new host: own id, skeleton, no alias to SKY ---
    {"jsonrpc": "2.0", "id": 17, "method": "tools/call",
     "params": {"name": "pt_scaffold", "arguments": {
         "host": "teardown", "guest": "Minecraft: Java Edition",
         "out_dir": ".work/scaffold_teardown"}}},
    # --- NEW: the safety gate also covers the new tool ---
    {"jsonrpc": "2.0", "id": 18, "method": "tools/call",
     "params": {"name": "pt_schema_describe", "arguments": {"schema_path": "ws://10.0.0.5:7777/x"}}},
    # --- NEW (minor gap D): an un-recorded host no longer returns a silent empty result ---
    {"jsonrpc": "2.0", "id": 19, "method": "tools/call",
     "params": {"name": "pt_param_lookup", "arguments": {"host": "teardown"}}},
]


def main():
    make_fixtures()
    for d in (".work/scaffold_demo", ".work/scaffold_teardown"):
        shutil.rmtree(os.path.join(HERE, d), ignore_errors=True)

    proc = subprocess.Popen([PY, os.path.join(HERE, "server.py")],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    pairs = []
    for req in REQUESTS:
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        if "id" not in req:                       # notification: no response
            pairs.append({"request": req, "response": None})
            continue
        line = proc.stdout.readline()
        resp = json.loads(line) if line.strip() else None
        pairs.append({"request": req, "response": resp})
    proc.stdin.close()
    proc.wait()

    with open(LOG, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # compact console summary
    for p in pairs:
        req, resp = p["request"], p["response"]
        if "method" not in req:
            continue
        if req["method"] == "tools/call":
            name = req["params"]["name"]
            text = (resp or {}).get("result", {}).get("content", [{}])[0].get("text", "")
            try:
                obj = json.loads(text)
            except Exception:  # noqa: BLE001
                obj = {}
            flag = "REFUSED" if obj.get("refused") else ("ok" if obj.get("ok", True) else "ERR")
            if "matched" in obj:
                extra = "matched=%s" % obj.get("matched")
            elif name == "pt_schema_describe":
                extra = "template+contract" if obj.get("ok") else obj.get("error", "")
            elif name == "pt_schema_validate":
                rt = obj.get("roundtrip", {})
                extra = ("diff=%s" % rt.get("structural_diff") if "structural_diff" in rt
                         else "issues=%s" % len(obj.get("issues", [])))
            elif name == "pt_scaffold":
                extra = "vocab=%s(%s)" % (obj.get("vocab", {}).get("key"),
                                          obj.get("vocab", {}).get("resolution"))
            else:
                extra = obj.get("overall") or obj.get("error") or ""
            print(f"id={req['id']:<2} {name:<20} {flag:<8} {extra}")
        else:
            print(f"id={req.get('id')} {req['method']}")
    print(f"\nlog -> {LOG}")


if __name__ == "__main__":
    main()
