#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_from_awesome.py
====================
PTmodmaker 参数库 V0 种子生成器。

从 awesome-game-mashups 的 projects.json 中筛出 `approach` 含
"passthrough" 或 "shared memory" 的条目，为每条生成参数库**骨架**记录：
    host / guest / license / repo / loader(待补) / evidence=repo / verified_on_hardware=false

对其中 **MIT 许可** 的条目，调用 `gh` 取默认分支 HEAD commit SHA。
取不到就如实记 null + 失败原因，**绝不编造 SHA**。

用法：
    python seed_from_awesome.py [--projects PATH] [--out PATH]
默认从 _PROVENANCE 同目录读取 projects.json，写出到 ./seeds.yaml。

依赖：PyYAML、已认证的 gh CLI。
"""
import argparse
import json
import subprocess
import sys
import os

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML：pip install pyyaml")

DEFAULT_PROJECTS = "/home/zjk/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/01-样本池/_data/awesome-game-mashups.projects.json"

# 任务给定的硬约束：本项目零实机验证
VERIFIED = False


def gh(*args):
    try:
        out = subprocess.run(
            ["gh"] + list(args),
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode != 0:
            return None, (out.stderr or "gh exit %d" % out.returncode).strip()
        return out.stdout.strip(), None
    except Exception as exc:  # noqa: BLE001
        return None, "gh error: %s" % exc


def repo_slug(source_url):
    """https://github.com/owner/repo -> owner/repo"""
    if not source_url:
        return None
    s = source_url.rstrip("/")
    if s.endswith(".git"):
        s = s[:-4]
    marker = "github.com/"
    i = s.find(marker)
    if i < 0:
        return None
    return s[i + len(marker):]


def fetch_sha(repo):
    """返回 (sha, note)。失败时 sha=None。"""
    if not repo:
        return None, "no repo slug"
    branch, err = gh("api", "repos/%s" % repo, "--jq", ".default_branch")
    if branch is None:
        return None, "default_branch fetch failed: %s" % err
    sha, err = gh("api", "repos/%s/commits/%s" % (repo, branch), "--jq", ".sha")
    if sha is None:
        return None, "HEAD sha fetch failed (branch=%s): %s" % (branch, err)
    return sha, None


def keep(r):
    a = (r.get("approach") or "").lower()
    return ("passthrough" in a) or ("shared memory" in a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default=DEFAULT_PROJECTS)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "seeds.yaml"))
    args = ap.parse_args()

    with open(args.projects, encoding="utf-8") as f:
        data = json.load(f)

    selected = [r for r in data if keep(r)]
    selected.sort(key=lambda r: r.get("id", ""))

    seeds = []
    for r in selected:
        repo = repo_slug(r.get("source"))
        lic = r.get("license")
        rec = {
            "id": r.get("id"),
            "name": r.get("name"),
            "host": r.get("host"),
            "guest": r.get("guest"),
            "license": lic,
            "repo": repo,
            "source_url": r.get("source"),
            # loader 在骨架阶段一律待补（真空洞清单的来源之一）
            "loader": None,
            "loader_hint": (r.get("approach") or "")[:160],
            "category": r.get("category"),
            "status": r.get("status"),
            "evidence": "repo",
            "verified_on_hardware": VERIFIED,
        }
        if lic and str(lic).upper() == "MIT":
            sha, note = fetch_sha(repo)
            rec["source_commit"] = sha
            rec["sha_fetch_note"] = note  # None 表示成功
        else:
            rec["source_commit"] = None
            rec["sha_fetch_note"] = "non-MIT / no license -> 未拉 SHA"
        seeds.append(rec)

    meta = {
        "generated_by": "seed_from_awesome.py",
        "filter": "approach contains 'passthrough' OR 'shared memory'",
        "source_dataset": "bailo167/awesome-game-mashups (CC0-1.0)",
        "count": len(seeds),
        "verified_on_hardware": VERIFIED,
        "note": "骨架记录，具体参数见 params.yaml 的 params 段；loader 待补。",
    }
    doc = {"meta": meta, "seeds": seeds}
    with open(args.out, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)

    # 控制台摘要
    mit = [s for s in seeds if s["license"] and str(s["license"]).upper() == "MIT"]
    ok = [s for s in mit if s["source_commit"]]
    print("筛选到 %d 条（passthrough/shared memory）" % len(seeds))
    print("其中 MIT %d 条，成功取到 SHA %d 条，失败 %d 条"
          % (len(mit), len(ok), len(mit) - len(ok)))
    for s in seeds:
        print("  - %-22s lic=%-5s sha=%s"
              % (s["id"], s["license"], s["source_commit"] or "NONE"))
    print("已写出:", args.out)


if __name__ == "__main__":
    main()
