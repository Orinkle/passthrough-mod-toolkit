#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t6_driver.py — 复用 smoke.py 的 JSON-RPC over stdio 协议，但给出可自定义的请求序列。

用法:
    <python> t6_driver.py requests.json out.jsonl

其中 requests.json 是一个 JSON 数组，元素形如:
    {"jsonrpc":"2.0","id":1,"method":"tools/call",
     "params":{"name":"pt_scaffold","arguments":{...}}}

本脚本不修改 v2-mcp/ 下任何既有文件；只在 T6-output/ 下写日志。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_MCP = os.path.dirname(HERE)            # v2-mcp/
SERVER = os.path.join(REPO_MCP, "server.py")
PY = sys.executable


def main() -> int:
    req_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "requests.json")
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "t6_log.jsonl")

    with open(req_path, "r", encoding="utf-8") as f:
        requests = json.load(f)

    proc = subprocess.Popen([PY, SERVER],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    pairs = []
    for req in requests:
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        if "id" not in req:
            pairs.append({"request": req, "response": None})
            continue
        line = proc.stdout.readline()
        resp = json.loads(line) if line.strip() else None
        pairs.append({"request": req, "response": resp})
    proc.stdin.close()
    proc.wait()

    with open(out_path, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # 控制台摘要
    for p in pairs:
        req, resp = p["request"], p["response"]
        m = req.get("method")
        if m == "tools/call":
            name = req["params"]["name"]
            args = req["params"]["arguments"]
            text = (resp or {}).get("result", {}).get("content", [{}])[0].get("text", "")
            try:
                obj = json.loads(text)
            except Exception:  # noqa: BLE001
                obj = {"_raw": text[:200]}
            is_err = (resp or {}).get("result", {}).get("isError", False)
            flag = "REFUSED" if obj.get("refused") else ("ERROR" if is_err else "ok")
            extra = obj.get("overall") or obj.get("error") or (
                "matched=%s" % obj.get("matched") if "matched" in obj else "")
            print(f"id={req.get('id')} {name:<20} {flag:<8} args={json.dumps(args, ensure_ascii=False)[:70]} | {extra}")
        else:
            print(f"id={req.get('id')} {m}")
    print(f"\nlog -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
