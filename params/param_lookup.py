#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
param_lookup.py — PTmodmaker 参数库 CLI 查询
=============================================
按宿主 / 复用档过滤，输出带出处的表格。

用法：
    python param_lookup.py [--host NAME] [--color green|yellow|red] [--all]

  --host  子串匹配宿主名（大小写不敏感），如 --host skyrim / --host valheim
  --color 按复用档过滤：green(🟢) / yellow(🟡) / red(🔴)
  --all   列出全部参数（默认无参数时即等价 --all，并附种子骨架数）

读 params.yaml（与本脚本同目录）。
"""
import argparse
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML：pip install pyyaml")

HERE = os.path.dirname(os.path.abspath(__file__))
PARAMS_YAML = os.path.join(HERE, "params.yaml")

SYM = {"green": "🟢", "yellow": "🟡", "red": "🔴"}


def load():
    with open(PARAMS_YAML, encoding="utf-8") as f:
        return yaml.safe_load(f)


def short_src(rec):
    repo = rec.get("source_repo") or "-"
    doc = rec.get("source_doc") or "-"
    commit = (rec.get("source_commit") or "")[:10] or "-"
    return "%s@%s (%s)" % (repo, commit, doc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", help="子串匹配宿主名（大小写不敏感）")
    ap.add_argument("--color", choices=["green", "yellow", "red"], help="复用档过滤")
    ap.add_argument("--all", action="store_true", help="列出全部参数")
    args = ap.parse_args()

    doc = load()
    seeds = doc.get("seeds", [])
    params = doc.get("params", [])

    host = (args.host or "").lower()
    color = args.color

    rows = []
    for p in params:
        if host and host not in (p.get("host") or "").lower():
            continue
        if color and p.get("reuse_level") != color:
            continue
        rows.append(p)

    # ----- 表格输出 -----
    print("PTmodmaker 参数库查询")
    print("筛选: host=%s  color=%s" % (args.host or "*", color or "*"))
    print("-" * 100)
    hdr = "%-9s %-26s %-22s %-34s %-7s %-5s" % (
        "档", "宿主", "参数", "值", "证据", "实机")
    print(hdr)
    print("-" * 100)
    for r in rows:
        lvl = r.get("reuse_level", "?")
        sym = SYM.get(lvl, "?")
        value = str(r.get("value", ""))
        if len(value) > 34:
            value = value[:31] + "..."
        print("%-9s %-26s %-22s %-34s %-7s %-5s" % (
            "%s%s" % (sym, lvl[0].upper()),
            (r.get("host") or "")[:26],
            (r.get("param") or "")[:22],
            value,
            r.get("evidence", "?"),
            "Y" if r.get("verified_on_hardware") else "N",
        ))
    print("-" * 100)
    print("命中参数 %d 条（种子骨架另有 %d 条，loader 多待补）" % (len(rows), len(seeds)))

    # ----- 命中行的完整出处（避免表格截断丢失信息）-----
    if rows:
        print()
        print("== 命中参数完整出处 ==")
        for r in rows:
            dnp = " [⚠ 不可默认打包]" if r.get("do_not_package") else ""
            print("• %s | %s%s" % (r.get("id"), short_src(r), dnp))
            if r.get("notes"):
                print("    %s" % r["notes"])


if __name__ == "__main__":
    main()
