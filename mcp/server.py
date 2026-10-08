#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PTmodmaker MCP server — zero-dependency, hand-written JSON-RPC over stdio.

Why hand-written: the official `mcp` Python SDK is NOT installed in this environment and we
are not allowed to install it from the network. The stdio transport of MCP is just
line-delimited JSON-RPC 2.0 (with an optional Content-Length framing we also tolerate), so a
~0-dependency implementation is both simpler to audit and a selling point of this toolkit.

What it exposes (5 tools):
    pt_schema_validate   validate schema.yaml + round-trip the 3 real headers OR a user header
    pt_schema_describe   the *contract* of a schema.yaml + an annotated schema.template.yaml
    pt_param_lookup      query the CC0 parameter library (with provenance & evidence level)
    pt_stub_run          run the fake-host/fake-guest stub scenarios (NO game)
    pt_scaffold          emit an adapter skeleton for a host/guest pair

Error discipline (see `pt_error`/`exception_issue`): NO tool ever lets a raw exception escape.
Every failure is a structured `result` payload with `isError:true` and an `issues[]` list whose
items each carry {path, expected, got, hint}; the traceback (when there is one) is written to
stderr only, never into the protocol result.

Safety: every call passes through a tool-level interceptor (see `screen`). Any input that
smells of online / multiplayer / anti-cheat / a server address is REFUSED before any work is
done. This is a hard gate, not documentation: there is a real precedent in this project where
automatic input injection almost typed keystrokes into a GTA Online landing page.

Run:  <python> server.py        (speaks JSON-RPC on stdin/stdout)
"""
from __future__ import annotations

import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback

# ----------------------------------------------------------------------------- paths
HERE = os.path.dirname(os.path.abspath(__file__))                 # .../03-复现路线/v2-mcp (lab) or <repo>/mcp
LAB = os.path.dirname(HERE)                                       # .../03-复现路线 (lab) or <repo> root
PL = os.path.dirname(LAB)                                         # .../passthrough-lab (lab only)


def _dir(*candidates):
    """First existing directory wins — the same file runs in both the lab tree
    (v0-schema/, v1-stubs/, 90-源码/) and the assembled repo layout
    (schema/, params/, ptgen/, stubs/, headers/)."""
    for c in candidates:
        if os.path.isdir(c):
            return c
    return candidates[0]


V0_SCHEMA_DIR = _dir(os.path.join(LAB, "schema"), os.path.join(LAB, "v0-schema"))
SCHEMA_YAML = os.path.join(V0_SCHEMA_DIR, "schema.yaml")
V0_PARAMS_DIR = _dir(os.path.join(LAB, "params"), os.path.join(LAB, "v0-params"))
PARAMS_YAML = os.path.join(V0_PARAMS_DIR, "params.yaml")
PARAM_LOOKUP = os.path.join(V0_PARAMS_DIR, "param_lookup.py")
V1_PTGEN_SRC = _dir(os.path.join(LAB, "ptgen", "src"), os.path.join(LAB, "v1-ptgen", "src"))
V1_STUBS = _dir(os.path.join(LAB, "stubs"), os.path.join(LAB, "v1-stubs"))
# Reference headers: assembled repo ships <repo>/headers/ (SkyCraft + FalloutCraft
# only, same relative layout as 90-源码/, minus ValCraft which is not redistributed).
SRC90 = _dir(os.path.join(LAB, "headers"), os.path.join(PL, "90-源码"))

# The interpreter that runs this server also drives every subprocess (PyYAML 6.0.3 lives here).
PY = os.environ.get("PT_PY") or sys.executable

# All scratch/outputs live under v2-mcp/.work so that v0-*/ and v1-*/ are NEVER written to.
WORK = os.path.join(HERE, ".work")

SERVER_NAME = "ptmodmaker-mcp"
SERVER_VERSION = "0.2.0"
DEFAULT_PROTOCOL = "2024-11-05"
SUPPORTED_PROTOCOLS = ("2024-11-05", "2025-03-26", "2025-06-18")

# Evidence vocabulary, per the project's house rule.
E_MEASURED = "已实测"
E_CLAIMED = "据项目自述"
E_INFER = "推断"


# ============================================================================= security
# Tool-level interceptor. This is enforced in code, before a tool runs; it is not a note in a doc.
DENY_KEYWORDS = [
    "online", "multiplayer", "multi-player", "coop", "co-op", "gtao", "gta online",
    "gta_online", "fivem", "ragemp", "alt:v", "matchmaking", "match-making", "mmo",
    "dedicated server", "listen server", "server address", "server ip", "server host",
    "anticheat", "anti-cheat", "battleye", "easyanticheat", "easy anti-cheat",
    "netcode", "lan game", "realms", "server.jar",
]
RE_URL = re.compile(r"\b[a-z][a-z0-9+.\-]*://", re.I)
RE_IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
RE_DOMAIN = re.compile(
    r"\b[a-z0-9][a-z0-9\-]*(?:\.[a-z0-9\-]+)*\.(?:com|net|org|io|gg|co|ru|cn|dev|tv|app|xyz|link|site|online)\b",
    re.I)
RE_HOSTPORT = re.compile(r"\b(?:localhost|[a-z0-9][a-z0-9.\-]*):\d{2,5}\b", re.I)

PRECEDENT = (
    "本项目的真实事故先例：passthrough 桥会把一侧的输入事件自动注入另一侧，开发中曾差点把"
    "合成出来的击键打进 GTA Online 的落地页（联机/在线服务）。因此任何联机、多人、反作弊或"
    "指向服务端地址的输入都在工具层被直接拒绝。"
)
REFUSAL_DOCTRINE = (
    "PTmodmaker 只面向「单机 / 本地」passthrough：两个游戏各自单机运行、只经本地 IPC 交换数据。"
    "它不为联机/多人/反作弊环境提供任何脚手架。"
)


def _walk_strings(obj, path="$"):
    """Yield (path, string_value) for every string in a nested structure."""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _walk_strings(v, f"{path}[{i}]")


def screen(tool_name: str, args: dict) -> dict | None:
    """Return a refusal dict if `args` trips the safety gate, else None."""
    hits = []
    for path, s in _walk_strings(args):
        low = s.lower()
        for kw in DENY_KEYWORDS:
            if kw in low:
                hits.append({"field": path, "value": s, "reason": f"含联机/多人语义 '{kw}'"})
                break
        else:
            if RE_URL.search(s):
                hits.append({"field": path, "value": s, "reason": "指向服务端地址（URL scheme）"})
            elif RE_IPV4.search(s):
                hits.append({"field": path, "value": s, "reason": "指向服务端地址（IPv4）"})
            elif RE_HOSTPORT.search(s):
                hits.append({"field": path, "value": s, "reason": "指向服务端地址（host:port）"})
            elif RE_DOMAIN.search(s):
                hits.append({"field": path, "value": s, "reason": "指向服务端地址（域名）"})
    if not hits:
        return None
    return {
        "tool": tool_name,
        "refused": True,
        "gate": "safety/network-multiplayer",
        "reason": "输入命中联机/多人/反作弊/服务端地址规则，已在工具层拒绝执行（未做任何工作）。",
        "hits": hits,
        "precedent": PRECEDENT,
        "doctrine": REFUSAL_DOCTRINE,
        "evidence_level": E_MEASURED,
    }


# ============================================================================= helpers
def _run(cmd, env=None, timeout=180):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(cmd, capture_output=True, text=True, env=e, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def _py(*args, env=None, timeout=180):
    return _run([PY, *args], env=env, timeout=timeout)


def _load_yaml(path):
    import yaml  # PyYAML 6.0.3 in the pinned interpreter; no network needed
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _json_default(o):
    # YAML parses `pulled_on` etc. into datetime.date; keep the output valid JSON.
    import datetime
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return str(o)


def text_result(payload, is_error=False):
    return {
        "content": [{"type": "text",
                     "text": json.dumps(payload, ensure_ascii=False, indent=2,
                                        default=_json_default)}],
        "isError": bool(is_error),
    }


# ============================================================================= structured errors
# House rule (gap A of the newbie usability experiment): a validation failure must NEVER be a
# bare exception string. It is a structured payload whose `issues[]` says exactly which node of
# the input is wrong, what was expected, what was found, and how to fix it.
def issue(path, expected, got, hint):
    return {"path": path, "expected": expected, "got": got, "hint": hint}


def got_of(value):
    """A short, JSON-safe description of an arbitrary value for the `got` field."""
    if value is None:
        return "null"
    if isinstance(value, dict):
        return f"mapping(keys={list(value)[:6]})"
    if isinstance(value, (list, tuple)):
        return f"list(len={len(value)})"
    return f"{type(value).__name__}:{value!r}"[:120]


def pt_error(tool, issues, message=None, **extra):
    """A structured, non-raising tool failure."""
    if isinstance(issues, dict):
        issues = [issues]
    payload = {
        "tool": tool,
        "ok": False,
        "error": message or (issues[0]["hint"] if issues else "校验失败"),
        "issues": issues,
        "evidence_level": E_MEASURED,
    }
    payload.update(extra)
    return payload


def exception_issue(e):
    """Turn an uncaught exception into one structured issue (traceback goes to stderr)."""
    tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    print(f"[ptmodmaker-mcp] handler raised:\n{tb}", file=sys.stderr, flush=True)
    return issue(
        path="$",
        expected="工具正常返回（不抛异常）",
        got=f"{type(e).__name__}: {e}",
        hint="这是工具内部缺陷（请把 stderr 的 traceback 一并反馈）；输入本身可能触发了未覆盖的分支。",
    )


def _fresh_workdir(tag):
    os.makedirs(WORK, exist_ok=True)
    return tempfile.mkdtemp(prefix=f"{tag}-", dir=WORK)


def _cleanup(path):
    """Best-effort scratch cleanup. MUST NOT raise.

    This host enforces a bulk-delete guard that raises SystemExit(1) (not an Exception) when a
    single turn deletes too many files. A cleanup failure must never turn a successful tool call
    into an error, so we swallow BaseException here (and leave the scratch dir behind).
    """
    if not path or not os.path.isdir(path):
        return
    try:
        shutil.rmtree(path)
    except BaseException as e:  # noqa: BLE001  (SystemExit from the env's safe-delete guard)
        print(f"[ptmodmaker-mcp] 清理 {path} 被环境 bulk-delete 守卫阻止（{type(e).__name__}）；"
              "已忽略（不影响工具结果）。", file=sys.stderr, flush=True)


# ============================================================================= tools
# ----------------------------------------------------------------- schema contract facts
# These are the two "hidden contracts" the newbie experiment could only find by crashing and
# bisecting. They are now (a) stated in the tool descriptions, (b) returned by
# pt_schema_describe, and (c) enforced as structured issues instead of a bare AttributeError.
ORDER_KINDS = ("regions", "var", "fixed", "optional")
VAR_KEYS = {"header", "host_flags", "host_state", "mc_flags", "mc_state", "input_type",
            "hurt_flags", "mc_event_type", "ren_type", "col_tri_flags", "dig_material",
            "tool_kind"}
OPTIONAL_KEYS = {"ren_dug", "dig_material", "tool_kind"}

CONTRACT_FACTS = [
    "container.order 必须是 **mapping 的列表**（每项 {kind, key?}）；写成字符串列表会在旧版里"
    "直接崩成 AttributeError: 'str' object has no attribute 'get'。",
    "vocabulary_schema 的 **顶层键名就是每份 vocabulary 的必填字段名**；值只是给人读的说明。",
]


# ----------------------------------------------------------------- structure validation
def _validate_schema_structure(schema):
    """Return (issues, warnings, info). Never raises: every failure is a structured issue."""
    issues, warnings = [], []
    if not isinstance(schema, dict):
        return ([issue("$", "mapping（schema.yaml 顶层）", got_of(schema),
                       "schema.yaml 顶层必须是 YAML mapping。")], [], {})

    for key in ("schema_version", "container", "vocabulary_schema", "vocabularies"):
        if key not in schema:
            issues.append(issue(f"$.{key}", "必填顶层键", "缺失",
                                f"顶层必须包含 {key}（完整字段见 pt_schema_describe）。"))

    # ---- container ------------------------------------------------------------
    container = schema.get("container")
    if not isinstance(container, dict):
        issues.append(issue("$.container", "mapping", got_of(container),
                            "container 是「不变骨架」，必须是 mapping。"))
        container = {}

    inc = container.get("includes", None)
    if inc is None:
        issues.append(issue("$.container.includes", "list[str]（每项是一条 #include 原文）",
                            "缺失", "必填。例：['#include <cstdint>']。"))
    elif not isinstance(inc, list) or any(not isinstance(x, str) for x in inc):
        bad = next((x for x in inc if not isinstance(x, str)), None) if isinstance(inc, list) else inc
        issues.append(issue("$.container.includes", "list[str]", got_of(inc),
                            "includes 是**字符串**列表（每条是一整行 #include，原样输出），"
                            "例如 ['#include <cstdint>']；**不是** mapping 列表。"
                            + (f" 首个非法项：{got_of(bad)}" if bad is not None else "")))

    rt = container.get("regions_template", None)
    if not isinstance(rt, str):
        issues.append(issue("$.container.regions_template",
                            "str（C++ 原文，用 {host_state_off} 占位宿主状态区基址）", got_of(rt),
                            "必填。regions 段的 C++ 文本，`{host_state_off}` 会被替换成 kOff<Abbr>State。"))

    fx = container.get("fixed", None)
    if not isinstance(fx, dict):
        issues.append(issue("$.container.fixed", "mapping[name -> C++ 原文]", got_of(fx),
                            "必填。每个 fixed 块是一段原样输出的 C++ 文本。"))

    order = container.get("order", None)
    if not isinstance(order, list) or any(not isinstance(it, dict) for it in order):
        bad = None
        if isinstance(order, list):
            bad = next((x for x in order if not isinstance(x, dict)), None)
        issues.append(issue(
            "$.container.order", "list[mapping]（每项 {kind, key?}）", got_of(order),
            "必填。order 必须是 **mapping 列表**，不是字符串列表，例如 "
            "[{'kind':'regions'}, {'kind':'var','key':'host_state'}, "
            "{'kind':'fixed','key':'coltri'}]。kind ∈ regions/var/fixed/optional，除 regions 外都要带 key。"
            + (f" 首个非 mapping 项：{got_of(bad)}" if bad is not None else "")))
    else:
        fixed_keys = set(fx) if isinstance(fx, dict) else set()
        for i, it in enumerate(order):
            k = it.get("kind")
            if k not in ORDER_KINDS:
                issues.append(issue(f"$.container.order[{i}].kind", "/".join(ORDER_KINDS),
                                    got_of(k), "order 项的 kind 取值非法。"))
                continue
            key = it.get("key")
            if k != "regions" and not key:
                issues.append(issue(f"$.container.order[{i}].key", "必填（kind != regions）", "缺失",
                                    f"kind={k} 的 order 项必须给出 key。"))
            elif k == "var" and key not in VAR_KEYS:
                issues.append(issue(f"$.container.order[{i}].key",
                                    f"∈ {sorted(VAR_KEYS)}", got_of(key),
                                    "var 槽位只能引用已知的变量 key（见 pt_schema_describe）。"))
            elif k == "fixed" and key not in fixed_keys:
                issues.append(issue(f"$.container.order[{i}].key", "container.fixed 中已定义的键",
                                    got_of(key), f"fixed 槽位引用了不存在的块 {key!r}；"
                                                 f"已定义：{sorted(fixed_keys)[:8]}…"))
            elif k == "optional" and key not in OPTIONAL_KEYS:
                issues.append(issue(f"$.container.order[{i}].key", f"∈ {sorted(OPTIONAL_KEYS)}",
                                    got_of(key), "optional 槽位只支持 ren_dug/dig_material/tool_kind。"))

    # ---- vocabulary_schema: TOP-LEVEL KEYS ARE THE REQUIRED VOCAB FIELD NAMES ----
    vs = schema.get("vocabulary_schema", None)
    if not isinstance(vs, dict) or not vs:
        issues.append(issue("$.vocabulary_schema", "mapping（顶层键名即词表必填字段名）", got_of(vs),
                            "必填。**顶层键名就是每份 vocabulary 的必填字段名**，值只是说明文本；"
                            "不要写成 {required:[...], optional:[...]}——那会让工具反过来要求你的词表"
                            "拥有名为 'required'/'optional' 的字段。"))

    vocabs = schema.get("vocabularies", None)
    if not isinstance(vocabs, dict) or not vocabs:
        issues.append(issue("$.vocabularies", "mapping（非空）", got_of(vocabs),
                            "必填；每个键是一份宿主词表。"))
        vocabs = {}

    req_vkeys = list(vs) if isinstance(vs, dict) else []
    optional_declared = {it.get("key") for it in order
                         if isinstance(it, dict) and it.get("kind") == "optional"} \
        if isinstance(order, list) else set()
    required_vkeys = [k for k in req_vkeys if k not in optional_declared]
    for name, v in vocabs.items():
        if not isinstance(v, dict):
            issues.append(issue(f"$.vocabularies.{name}", "mapping（词表）", got_of(v),
                                "每份词表必须是 mapping。"))
            continue
        for k in required_vkeys:
            if k not in v:
                issues.append(issue(f"$.vocabularies.{name}.{k}",
                                    "必填（由 vocabulary_schema 的顶层键名定义）", "缺失",
                                    f"词表 {name!r} 缺字段 {k!r}；vocabulary_schema 的顶层键名就是"
                                    "必填字段名。"))
        if v.get("__scaffold_status__") == "skeleton":
            warnings.append(issue(f"$.vocabularies.{name}", "已实现的词表（非骨架）",
                                  "__scaffold_status__=skeleton",
                                  "⚠ 这是 pt_scaffold 生成的**骨架词表**：结构齐全 ≠ 可用。"
                                  "请按 TODO-MEASURE.md 实测 🔴 项填真值，再把 __scaffold_status__ "
                                  "改为 implemented。"))

    info = {"vocabularies": list(vocabs), "required_vocab_fields": required_vkeys,
            "order_kinds": list(ORDER_KINDS), "var_keys": sorted(VAR_KEYS)}
    return issues, warnings, info


# ----------------------------------------------------------------- diff classification
_IDENT_RE = re.compile(r"[A-Za-z_]\w*")
_NUM_RE = re.compile(r"\b(?:0[xX][0-9A-Fa-f]+|\d+\.?\d*(?:[fFuUlL]+)?)\b")
CATEGORY_HINT = {
    "identifier": "标识符不同（结构体/枚举成员/字段/namespace 命名）——核对词表里的名字与大小写。",
    "literal": "字面量不同（数值/常量/static_assert 尺寸/枚举值）——核对词表数值。",
    "identifier+literal": "标识符与字面量同时不同——先对齐命名，再对齐数值。",
    "structure_order": "结构或声明顺序不同（行数或顺序不一致）——核对 container.order 与 fixed 块。",
}


def _norm_lines(text):
    out = []
    for ln in text.splitlines():
        i = ln.find("//")
        s = re.sub(r"\s+", " ", (ln[:i] if i >= 0 else ln)).strip()
        if s:
            out.append(s)
    return out


def _line_category(a, b):
    ids_a, ids_b = set(_IDENT_RE.findall(a)), set(_IDENT_RE.findall(b))
    lit_a, lit_b = set(_NUM_RE.findall(a)), set(_NUM_RE.findall(b))
    if ids_a != ids_b and lit_a == lit_b:
        return "identifier"
    if lit_a != lit_b and ids_a == ids_b:
        return "literal"
    if ids_a != ids_b and lit_a != lit_b:
        return "identifier+literal"
    return "structure_order"


def _classify_diff(orig, gen, limit=60):
    """Per-line structural diff, each line classified identifier / literal / structure_order."""
    sm = difflib.SequenceMatcher(a=orig, b=gen, autojunk=False)
    counts = {"identifier": 0, "literal": 0, "identifier+literal": 0, "structure_order": 0}
    items = []

    def push(no, cat, expected, got):
        counts[cat] = counts.get(cat, 0) + 1
        if len(items) < limit:
            items.append({"line": no, "category": cat, "expected": expected[:160],
                          "got": got[:160], "hint": CATEGORY_HINT.get(cat, "")})

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                push(i1 + k + 1, _line_category(orig[i1 + k], gen[j1 + k]),
                     orig[i1 + k], gen[j1 + k])
        else:
            for k in range(max(i2 - i1, j2 - j1)):
                a = orig[i1 + k] if i1 + k < i2 else "∅（原头缺少这一行）"
                b = gen[j1 + k] if j1 + k < j2 else "∅（生成多出这一行）"
                push((i1 + k + 1) if i1 + k < i2 else (j1 + k + 1), "structure_order", a, b)
    return sum(counts.values()), counts, items


# ----------------------------------------------------------------- custom-header round-trip
def _roundtrip_custom(schema_path, header_path):
    """extract -> generate -> structural diff for a USER-SUPPLIED header (gap B)."""
    rt = {"mode": "custom-header", "isolated": True, "exit_code": None, "ok": False,
          "harness": "v0-schema/extract_vocab.py + gen_header.py（隔离镜像副本）",
          "header_path": header_path, "schema_path": schema_path}
    if not os.path.exists(header_path):
        rt["issues"] = [issue("$.header_path", "存在的文件路径", "不存在",
                              f"找不到你传入的协议头：{header_path}")]
        return rt
    wd = _fresh_workdir("hdr")
    try:
        mirror = os.path.join(wd, "mirror")
        os.makedirs(mirror, exist_ok=True)
        for fn in ("extract_vocab.py", "gen_header.py"):
            shutil.copy2(os.path.join(V0_SCHEMA_DIR, fn), os.path.join(mirror, fn))
        vocab_y = os.path.join(wd, "extracted_vocab.yaml")
        gen_h = os.path.join(wd, "regenerated.h")
        rc1, o1, e1 = _py(os.path.join(mirror, "extract_vocab.py"),
                          "--header", header_path, "--out", vocab_y, timeout=120)
        rt["extract"] = {"exit_code": rc1, "stdout": o1.strip(), "stderr": e1.strip() or None}
        if rc1 != 0 or not os.path.exists(vocab_y):
            tail = (e1.strip().splitlines() or [""])[-1]
            rt["issues"] = [issue("$.header_path", "可被 extract_vocab.py 解析的协议头",
                                  f"extract 退出码 {rc1}", tail or "提取失败，见 extract.stderr")]
            return rt
        rc2, o2, e2 = _py(os.path.join(mirror, "gen_header.py"), "--schema", schema_path,
                          "--vocab", vocab_y, "--out", gen_h, timeout=120)
        rt["generate"] = {"exit_code": rc2, "stdout": o2.strip(), "stderr": e2.strip() or None}
        rt["exit_code"] = rc2
        if rc2 != 0 or not os.path.exists(gen_h):
            tail = (e2.strip().splitlines() or [""])[-1]
            rt["issues"] = [issue("$.schema_path", "container 能表达这份协议头",
                                  f"gen_header 退出码 {rc2}", tail or "生成失败，见 generate.stderr")]
            return rt
        with open(header_path, encoding="utf-8") as f:
            orig = _norm_lines(f.read())
        with open(gen_h, encoding="utf-8") as f:
            gen = _norm_lines(f.read())
        total, counts, items = _classify_diff(orig, gen)
        rt["ok"] = (total == 0)
        rt["structural_diff"] = total
        rt["counts_by_category"] = counts
        rt["lines"] = {"original": len(orig), "regenerated": len(gen)}
        rt["diagnostics"] = items
        rt["conclusion"] = ("PASS: 这份协议头被 schema 的 container 完整复现（structural diff = 0）。"
                            if total == 0 else
                            f"FAIL: structural diff = {total}；逐行差异与分类见 diagnostics"
                            f"（counts_by_category）。")
    except Exception as e:  # noqa: BLE001
        rt["issues"] = [exception_issue(e)]
    finally:
        _cleanup(wd)
    return rt


# ----------------------------------------------------------------- built-in 3-host round-trip
def _roundtrip_builtin(schema_path):
    rt = {"harness": "v0-schema/verify_roundtrip.py（隔离镜像副本）",
          "isolated": True, "exit_code": None, "hosts": {}, "conclusion": None}
    wd = None
    try:
        wd = _fresh_workdir("schema")
        mirror = os.path.join(wd, "mirror")
        v0m = os.path.join(mirror, "03-复现路线", "v0-schema")
        s90 = os.path.join(mirror, "90-源码")
        os.makedirs(v0m, exist_ok=True)
        for fn in ("extract_vocab.py", "gen_header.py", "verify_roundtrip.py"):
            shutil.copy2(os.path.join(V0_SCHEMA_DIR, fn), os.path.join(v0m, fn))
        headers = [
            ("SkyCraft/protocol/skycraft_protocol.h", "SkyCraft/protocol"),
            ("FalloutCraft/skycraft_protocol.h", "FalloutCraft"),
            ("ValCraft/protocol/valcraft_protocol.h", "ValCraft/protocol"),
        ]
        for rel, _d in headers:
            src = os.path.join(SRC90, rel)
            if not os.path.exists(src):
                continue  # ValCraft header is not redistributed (no LICENSE); verify prints SKIPPED
            dst = os.path.join(s90, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

        gen = os.path.join(v0m, "generated")
        rc, out, errtxt = _py(os.path.join(v0m, "verify_roundtrip.py"),
                              "--schema", schema_path, "--keep-gen", gen, timeout=180)
        rt["exit_code"] = rc
        rt["stdout"] = out.strip().splitlines()
        if errtxt.strip():
            rt["stderr"] = errtxt.strip().splitlines()
        for line in out.splitlines():
            m = re.match(r"\s*(SKY|FO4|VAL)\s*\(([^)]*)\):\s*structural diff = (\d+)", line)
            if m:
                key, lic, diff = m.group(1), m.group(2).strip(), int(m.group(3))
                rt["hosts"][key] = {
                    "license": lic, "structural_diff": diff,
                    "pass_target": key in ("SKY", "FO4") and diff == 0,
                }
        rt["conclusion"] = ("PASS: both MIT hosts round-trip to zero structural difference."
                            if rc == 0 else "FAIL: a MIT host did not round-trip to zero.")
        if rc != 0 and not errtxt.strip():
            rt["note"] = "非零退出"
    except Exception as e:  # noqa: BLE001
        rt["issues"] = [exception_issue(e)]
    finally:
        if wd:
            _cleanup(wd)
    return rt


# ----------------------------------------------------------------- pt_schema_validate
def pt_schema_validate(args):
    tool = "pt_schema_validate"
    schema_path = args.get("schema_path") or SCHEMA_YAML
    if not os.path.isabs(schema_path):
        schema_path = os.path.normpath(os.path.join(LAB, schema_path))
    header_path = args.get("header_path")
    if header_path and not os.path.isabs(header_path):
        header_path = os.path.normpath(os.path.join(HERE, header_path))

    if not os.path.exists(schema_path):
        return pt_error(tool, issue("$.schema_path", "存在的文件路径", "不存在",
                                    f"schema 不存在: {schema_path}（相对路径按 03-复现路线/ 解析）"),
                        schema_path=schema_path)
    try:
        schema = _load_yaml(schema_path)
    except Exception as e:  # noqa: BLE001
        return pt_error(tool, issue("$.schema_path", "合法 YAML 文件", f"{type(e).__name__}: {e}",
                                    "YAML 解析失败；检查缩进/制表符与重复键。"),
                        schema_path=schema_path)

    issues, warnings, info = _validate_schema_structure(schema)
    structure = {"ok": not issues, "issues": issues, "warnings": warnings,
                 "summary": info, "issue_count": len(issues)}

    # round-trip: a user header when given, else the 3 built-in real headers
    if header_path:
        rt = _roundtrip_custom(schema_path, header_path)
    else:
        rt = _roundtrip_builtin(schema_path)
    rt_issues = rt.get("issues") or []
    rt_ok = bool(rt.get("ok")) if header_path else (rt.get("exit_code") == 0)

    payload = {
        "tool": tool,
        "ok": structure["ok"] and rt_ok and not rt_issues,
        "schema_path": schema_path,
        "header_path": header_path,
        "structure": structure,
        "roundtrip": rt,
        "evidence_level": E_MEASURED if rt.get("exit_code") is not None else E_INFER,
        "does_not": [
            "不校验 C++ 表达式/别名的语义正确性——只做结构键检查，语义交给 round-trip 实际生成来暴露。",
            "不修改 schema，也不写 v0-*：round-trip 在 v2-mcp/.work 下的隔离镜像中执行。",
            "不启动任何游戏。",
        ],
    }
    if not payload["ok"]:
        all_issues = list(issues) + list(rt_issues)
        if not rt_ok and not rt_issues:
            all_issues.append(issue("$.roundtrip", "structural diff = 0",
                                    f"structural_diff = {rt.get('structural_diff')}",
                                    "round-trip 未归零；若传了 header_path，请看 roundtrip.diagnostics。"))
        payload["issues"] = all_issues
        if not payload.get("error"):
            payload["error"] = (all_issues[0]["hint"] if all_issues else "校验失败")
    return payload


# ----------------------------------------------------------------- pt_schema_describe
SCHEMA_TEMPLATE = '''# ============================================================================
# schema.template.yaml — PTmodmaker 词表骨架（带注释起点，由 pt_schema_describe 返回）
#
# 怎么用：container 通常**不要动**（它是「不变骨架」，所有宿主共用）；你只需要在
# vocabularies 里加一份属于你宿主的词表，然后 pt_scaffold / pt_schema_validate 就会用它。
#
# 两条「隐藏契约」——新手实验里只能靠崩溃 + 二分才试出来，现在写在这里：
#   ① container.order 必须是 **mapping 的列表**（每项 {kind, key?}）。
#      写成字符串列表会崩：AttributeError: 'str' object has no attribute 'get'。
#      而 container.includes 相反，必须是 **字符串列表**（每条是一整行 #include 原文）。
#   ② vocabulary_schema 的 **顶层键名 = 每份 vocabulary 的必填字段名**；值只是说明文本。
#      不要写成 {required: [...], optional: [...]}，否则工具会反过来要求你的词表
#      拥有名为 "required"/"optional" 的字段。
# ============================================================================
schema_version: 1

container:
  # ① includes：**字符串**列表，每项是一整行 #include，原样输出。
  includes:
  - '#include <cstdint>'

  # regions_template：一段 C++ 文本；`{host_state_off}` 会被替换成 kOff<host_abbr>State。
  regions_template: |
    inline constexpr std::uint64_t kOffHeader = 0x0;
    inline constexpr std::uint64_t {host_state_off} = 0x100;
    inline constexpr std::uint64_t kOffMcState = 0x200;
    inline constexpr std::uint64_t kOffInputRing = 0x1000;
    inline constexpr std::uint64_t kOffCollisionRing = 0x20000;
    inline constexpr std::uint64_t kCollisionRingBytes = 32ull << 20;
    inline constexpr std::uint64_t kMappingBytes = kOffCollisionRing + kCollisionRingBytes;

  # fixed：name -> 一段原样输出的 C++ 文本（结构体 / 枚举 / 常量 / static_assert）。
  fixed:
    inputevent: |
      struct InputEvent
      {
        std::uint16_t type;
        std::uint16_t code;
        std::int32_t  a;
        std::int32_t  b;
        std::int32_t  c;
      };
      static_assert(sizeof(InputEvent) == 16);

  # ① order：**mapping 列表**。kind ∈ regions / var / fixed / optional；
  #    除 regions 外，每一项都要带 key。
  order:
  - kind: regions
  - kind: var
    key: header
  - kind: var
    key: host_state
  - kind: var
    key: mc_state
  - kind: fixed
    key: inputevent

# ② vocabulary_schema：**顶层键名就是每份 vocabulary 的必填字段名**，值是给人读的说明。
vocabulary_schema:
  namespace: C++ namespace, e.g. mygame::proto
  host_abbr: 'Host | MyHost  (drives HostState/MyHostState names and Header pid/heartbeat fields)'
  host_prefix: lowercase prefix in Header field names, e.g. mygame -> mygamePid
  magic: hex literal, e.g. 0x4D594741
  version: integer
  mapping_name: wchar string, e.g. Local\\MyGame_v1
  units_per_block: double literal, e.g. 1.0
  host_flags: 'enum members [{name, value}]  (value is the RHS expr, e.g. ''1u << 0'', or null)'
  host_state: '{ fields: [decl lines], size: ''0x40'', ground_grid: null|int }'
  mc_flags: enum members [{name, value}]
  mc_state: '{ fields: [decl lines], size: ''0xC8'' }'
  input_type: enum members [{name, value}]
  hurt_flags: enum members [{name, value}]
  mc_event_type: enum members [{name, value}]
  ren_type: enum members [{name, value}]

# vocabularies：每个键 = 一份宿主词表（键名大小写不敏感地用于 ptgen --host）。
vocabularies:
  MYHOST:
    namespace: mygame::proto
    host_abbr: MyHost
    host_prefix: mygame
    magic: '0x4D594741'
    version: 1
    mapping_name: Local\\MyGame_v1
    units_per_block: '1.0'
    host_flags:
    - name: kMyHostInGame
      value: 1u << 0
    host_state:
      fields:
      - std::uint32_t seq;
      - std::uint32_t flags;
      - double        posX, posY, posZ;
      - float         yaw, pitch;
      size: '0x40'
      ground_grid: null
    mc_flags:
    - name: kMcInWorld
      value: 1u << 0
    mc_state:
      fields:
      - std::uint32_t seq;
      - std::uint32_t flags;
      - double        x, y, z;
      - float         yaw, pitch;
      size: '0xC8'
    input_type:
    - name: kInKey
      value: '1'
    hurt_flags:
    - name: kHurtMelee
      value: 1u << 0
    mc_event_type:
    - name: kEvHitActor
      value: '1'
    ren_type:
    - name: kRenPad
      value: '0'
'''


def pt_schema_describe(args):
    """Return the schema *contract* (types / required / meaning) + an annotated template."""
    tool = "pt_schema_describe"
    schema_path = args.get("schema_path")
    observed = None
    if schema_path:
        if not os.path.isabs(schema_path):
            schema_path = os.path.normpath(os.path.join(LAB, schema_path))
        if not os.path.exists(schema_path):
            return pt_error(tool, issue("$.schema_path", "存在的文件路径", "不存在",
                                        f"schema 不存在: {schema_path}"), schema_path=schema_path)
        try:
            schema = _load_yaml(schema_path)
        except Exception as e:  # noqa: BLE001
            return pt_error(tool, issue("$.schema_path", "合法 YAML", f"{type(e).__name__}: {e}",
                                        "YAML 解析失败。"), schema_path=schema_path)
        issues, warnings, info = _validate_schema_structure(schema)
        container = (schema or {}).get("container") if isinstance(schema, dict) else {}
        observed = {
            "schema_path": schema_path,
            "structure_ok": not issues,
            "issues": issues, "warnings": warnings, "summary": info,
            "container_keys": sorted(container) if isinstance(container, dict) else None,
            "vocabularies": list((schema or {}).get("vocabularies") or {})
            if isinstance(schema, dict) else [],
        }

    return {
        "tool": tool,
        "ok": True,
        "template_filename": "schema.template.yaml",
        "hidden_contracts": CONTRACT_FACTS,
        "contract": {
            "top_level": {
                "schema_version": "integer（当前为 1）",
                "container": "mapping —— 不变骨架，所有宿主共用；见下",
                "vocabulary_schema": "mapping —— 顶层键名 = 每份 vocabulary 的必填字段名",
                "vocabularies": "mapping[name -> 词表] —— 一个宿主一份；键名即 ptgen --host 的取值",
            },
            "container.includes": {
                "type": "list[str]（必填）",
                "meaning": "原样输出的 #include 行，每条是一整行字符串",
                "example": ["#include <cstdint>"],
                "pitfall": "写成 mapping 列表会生成失败（TypeError: expected str instance, dict found）",
            },
            "container.regions_template": {
                "type": "str（必填）",
                "meaning": "regions 段的 C++ 文本；占位符 {host_state_off} -> kOff<host_abbr>State",
            },
            "container.fixed": {
                "type": "mapping[name -> str]（必填，可为空 mapping）",
                "meaning": "每个 fixed 块是一段原样输出的 C++ 文本（结构体/枚举/常量/static_assert）",
            },
            "container.order": {
                "type": "list[mapping]（必填）",
                "meaning": "声明顺序：工具按 order 逐项输出 fixed 块与变量槽位",
                "item": {"kind": "regions|var|fixed|optional", "key": "除 regions 外必填"},
                "example": [{"kind": "regions"}, {"kind": "var", "key": "header"},
                            {"kind": "fixed", "key": "coltri"}],
                "pitfall": "写成字符串列表会崩：AttributeError: 'str' object has no attribute 'get'"
                           "（旧版就是这样暴露契约的）",
            },
            "vocabulary_schema": {
                "type": "mapping（必填，非空）",
                "meaning": "**顶层键名就是每份 vocabulary 的必填字段名**；值只是给人读的说明文本",
                "pitfall": "别写成 {required: [...], optional: [...]}——那会让工具要求你的词表里"
                           "存在名为 'required'/'optional' 的字段",
            },
            "vocabulary_fields": {
                "namespace": "C++ namespace（str）",
                "host_abbr": "宿主缩写，驱动 <Abbr>State / <Abbr>Flags 与 offset 常量名（str）",
                "host_prefix": "Header 里 pid/heartbeat 字段前缀，如 skyrim -> skyrimPid（str，"
                               "v0 schema 未在 vocabulary_schema 声明但生成器实际必需）",
                "magic": "魔数（十六进制字面量，str）",
                "version": "版本（int）",
                "mapping_name": "共享内存映射名，如 Local\\SkyCraft_v1（str）",
                "units_per_block": "每方块单位数（double 字面量，str）",
                "host_state / mc_state": "{fields:[C++ 声明行], size:'0x40'}；size 必须与 "
                                          "static_assert 一致",
                "host_flags / mc_flags / input_type / hurt_flags / mc_event_type / ren_type":
                    "[{name, value}]；value 是 RHS 表达式（'1u << 0'）或 null（自动递增）",
                "col_tri_flags": "{members:[{name,value}], has_shift:bool}（可选）",
                "dig_material": "null 或 [{name,value}]（可选）",
                "ren_dug": "bool（可选）",
                "tool_kind": "null 或 [{name,value}]（可选）",
            },
            "order_var_keys": sorted(VAR_KEYS),
            "order_optional_keys": sorted(OPTIONAL_KEYS),
        },
        "template": SCHEMA_TEMPLATE,
        "observed": observed,
        "evidence_level": E_MEASURED,
        "evidence_note": "契约来自对 v0-schema/gen_header.py + v1-ptgen/backends/cpp.py 的实现阅读"
                         "与对照实测：includes=字符串列表可用、写成 mapping 列表使 gen_header 失败；"
                         "order 写成字符串列表则触发 AttributeError（已复现）。",
        "does_not": [
            "不修改任何 schema；只返回契约说明与模板文本。",
            "不替你填词表——每个字段的真值（尤其 host_state/mc_state 的字段与 size）必须由你按自查。",
            "不校验给定 schema 的语义（只给结构 issues/warnings）；语义交给 pt_schema_validate 的 round-trip。",
        ],
    }


# ----------------------------------------------------------------- pt_param_lookup
def pt_param_lookup(args):
    host = args.get("host")
    color = args.get("color")
    if color not in (None, "green", "yellow", "red"):
        return pt_error("pt_param_lookup",
                        issue("$.color", "green | yellow | red", got_of(color),
                              "color 只能是 green/yellow/red（green 可直搬 / yellow 需复核 / "
                              "red 必须实测）。"))

    cmd = [PY, PARAM_LOOKUP]
    if host:
        cmd += ["--host", host]
    if color:
        cmd += ["--color", color]
    rc, out, err = _py(*cmd, timeout=60)

    # Structured records, filtered with the same semantics as param_lookup.py.
    data = _load_yaml(PARAMS_YAML)
    params = data.get("params", [])
    h = (host or "").lower()
    records = []
    for p in params:
        if h and h not in (p.get("host") or "").lower():
            continue
        if color and p.get("reuse_level") != color:
            continue
        records.append({
            "id": p.get("id"),
            "host": p.get("host"),
            "guest": p.get("guest"),
            "param": p.get("param"),
            "value": p.get("value"),
            "unit": p.get("unit"),
            "reuse_level": p.get("reuse_level"),
            "evidence": p.get("evidence"),
            "source": {
                "repo": p.get("source_repo"),
                "commit": (p.get("source_commit") or "")[:12] or None,
                "doc": p.get("source_doc"),
            },
            "verified_on_hardware": bool(p.get("verified_on_hardware")),
            "do_not_package": bool(p.get("do_not_package")),
            "notes": p.get("notes"),
        })

    counts = {"green": 0, "yellow": 0, "red": 0}
    for r in records:
        if r["reuse_level"] in counts:
            counts[r["reuse_level"]] += 1

    # Gap D (a minor finding of the same experiment): an empty result used to be silent, and the
    # newbie had to guess from library.seed_count why nothing matched. Say it out loud.
    host_known = True
    if h:
        host_known = any(h in (p.get("host") or "").lower() for p in params)

    payload = {
        "tool": "pt_param_lookup",
        "filter": {"host": host, "color": color},
        "library": data.get("meta"),
        "cli_exit_code": rc,
        "cli_output": out.strip(),
        "matched": len(records),
        "counts_by_color": counts,
        "records": records,
        "host_found": host_known if h else None,
        "evidence_level": E_CLAIMED,
        "evidence_note": "库自述：全部参数 verified_on_hardware=false；每条记录的 evidence 字段给出"
                         " repo/doc/inference 三档之一。do_not_package=true 的条目不可默认打包。",
        "does_not": [
            "不验证参数真值——库中无任何实机验证数值（verified_on_hardware 一律 false）。",
            "不提供代码片段；无出处参数不入库。",
            "不联网重新拉取上游仓库。",
        ],
    }
    if h and not host_known:
        payload["note"] = (f"宿主 {host!r} **未收录**在这个种子库里（matched=0 不是查询出错）。"
                           "库只有 9 款已做过的游戏；接新宿主时可复用参数为 0，"
                           "全部宿主侧数值都要走 TODO-MEASURE.md 的 🔴 实测清单。")
    elif h and not records:
        payload["note"] = (f"宿主 {host!r} 在库里有记录，但当前 filter"
                           f"（color={color!r}）下没有命中。")
    return payload


# ----------------------------------------------------------------- pt_stub_run
SCENARIOS = {
    "heartbeat": ("a", "heartbeat_timeout"),
    "epoch": ("b", "epoch_invalidation"),
    "collision_wall": ("c", "steep_wall"),
}
STUB_FILES = [
    "layout_from_schema.py", "fake_host.py", "fake_guest.py",
    "run_demo.py", "negative_control.py", "render_demo.py",
]


def _stub_iso_copy(tag):
    """Copy the v1-stubs harness into an isolated workdir (v1-* must stay untouched)."""
    wd = _fresh_workdir(tag)
    for fn in STUB_FILES:
        shutil.copy2(os.path.join(V1_STUBS, fn), os.path.join(wd, fn))
    return wd


def pt_stub_run(args):
    scenario = args.get("scenario") or "all"
    if scenario not in ("heartbeat", "epoch", "collision_wall", "all"):
        return pt_error("pt_stub_run",
                        issue("$.scenario", "heartbeat | epoch | collision_wall | all",
                              got_of(scenario),
                              "scenario 只能是 heartbeat/epoch/collision_wall/all。"))

    wd = _stub_iso_copy("stub")
    env = {"PT_SCHEMA": SCHEMA_YAML, "PT_GEN_DIR": os.path.join(wd, "generated")}
    try:
        results = {}
        verdict = {}
        if scenario == "all":
            rc, out, err = _py(os.path.join(wd, "run_demo.py"), env=env, timeout=180)
            tracep = os.path.join(wd, "demo_trace.json")
            trace = json.load(open(tracep, encoding="utf-8")) if os.path.exists(tracep) else {}
            sc = trace.get("scenarios", {})
            mapping = {
                "heartbeat": "a_heartbeat_timeout",
                "epoch": "b_epoch_invalidation",
                "collision_wall": "c_steep_wall",
            }
            for name, key in mapping.items():
                s = sc.get(key, {})
                s = {k: v for k, v in s.items() if k != "trace"}
                results[name] = s
                verdict[name] = bool(s.get("passed"))
            overall = bool(trace.get("passed"))
            stdout_lines = out.strip().splitlines()
        else:
            drv = os.path.join(wd, "_drv.py")
            with open(drv, "w", encoding="utf-8") as f:
                f.write(
                    "import sys, os, json\n"
                    "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n"
                    "import run_demo as R\n"
                    "fn = {'heartbeat': R.scenario_a, 'epoch': R.scenario_b,"
                    " 'collision_wall': R.scenario_c}[sys.argv[1]]\n"
                    "res = fn(); res.pop('trace', None)\n"
                    "R.cleanup()\n"
                    "print('@@RESULT@@' + json.dumps({'scenario': sys.argv[1], 'result': res}))\n"
                )
            rc, out, err = _py(drv, scenario, env=env, timeout=180)
            payload = None
            stdout_lines = []
            for line in out.splitlines():
                if line.startswith("@@RESULT@@"):
                    payload = json.loads(line[len("@@RESULT@@"):])
                else:
                    stdout_lines.append(line)
            if payload is None:
                return {"tool": "pt_stub_run", "ok": False, "scenario": scenario,
                        "error": "桩驱动未产出结果", "stdout": out, "stderr": err}
            results[scenario] = payload["result"]
            verdict[scenario] = bool(payload["result"].get("passed"))
            overall = all(verdict.values())
        return {
            "tool": "pt_stub_run",
            "scenario": scenario,
            "ok": True,
            "transport": "共享内存映射（MAP_SHARED over a file）——非真游戏，非真 IPC 驱动",
            "results": results,
            "verdict": verdict,
            "overall": "PASS" if overall else "FAIL",
            "stdout": stdout_lines,
            "stderr": err.strip() if err.strip() else None,
            "exit_code": rc,
            "evidence_level": E_MEASURED,
            "evidence_note": "假桩进程（fake_host/fake_guest）真实执行；但这证明的是协议与状态机，"
                             "不是真游戏集成。",
            "does_not": [
                "不启动任何真游戏；宿主/客侧都是 Python 假桩。",
                "不测真引擎的插件加载、反作弊、画面合成或显卡路径。",
                "不写 v1-stubs：每次在 v2-mcp/.work 下的隔离副本中运行。",
            ],
        }
    finally:
        _cleanup(wd)


# ----------------------------------------------------------------- pt_scaffold
# Gap C (newbie experiment): scaffolding a NEW host used to (a) hardcode `SKY` in the generated
# tools, (b) take no `schema_path`, and (c) silently fall back to *another host's* vocabulary.
# The closed loop is broken if any of those is true. So now:
#   * we NEVER alias and NEVER fall back to "the first vocabulary";
#   * an unregistered host gets its OWN id and an explicitly-marked skeleton vocabulary
#     (`__scaffold_status__: skeleton`), written to out_dir/schema.yaml;
#   * the generated tools reference that own id and fail READABLY ("未实现宿主适配器")
#     instead of raising `unknown host 'SKY'`.

def _derive_host_id(host):
    s = re.sub(r"[^0-9A-Za-z]+", "_", (host or "").strip()).strip("_")
    if not s:
        s = "NEWHOST"
    if s[0].isdigit():
        s = "H_" + s
    return s


def _camel(s):
    parts = [p for p in re.split(r"[^0-9A-Za-z]+", s or "") if p]
    return "".join(p[:1].upper() + p[1:] for p in parts) or "NewHost"


def _host_magic(key):
    h = 0
    for ch in key.encode("utf-8"):
        h = (h * 131 + ch) & 0xFFFFFFFF
    return "0x%08X" % (h or 1)


def _field_match(v, hl):
    prefix = str((v or {}).get("host_prefix") or "").lower()
    ns = str((v or {}).get("namespace") or "").lower().split("::")[0]
    for val in (prefix, ns):
        if val and (val in hl or (len(hl) >= 4 and hl in val)):
            return val
    return None


def _resolve_vocab(schema, host):
    """Return (vocab_key, resolution, is_new_host). No alias, no silent default (gap C)."""
    vocabs = schema.get("vocabularies") or {}
    h = (host or "").strip()
    hl = h.lower()
    for k in vocabs:
        if hl == k.lower():
            return k, "schema-key-match", False
    for k, v in vocabs.items():
        m = _field_match(v, hl)
        if m:
            return k, f"schema-field-match({m})", False
    return _derive_host_id(h), "new-host (own id; never aliased to a built-in)", True


def _pick_flag(members, needles, default):
    for m in members or []:
        nm = (m or {}).get("name", "")
        if any(n.lower() in nm.lower() for n in needles):
            return nm
    if members:
        return members[0].get("name", default)
    return default


def _skeleton_vocab(key):
    abbr = _camel(key)
    prefix = re.sub(r"[^0-9A-Za-z]", "", key).lower() or "host"
    return {
        "__scaffold_status__": "skeleton",
        "__scaffold_note__": ("pt_scaffold 生成的骨架词表：字段/枚举是**占位**，"
                              "必须按 TODO-MEASURE.md 实测后替换真值，"
                              "再把 __scaffold_status__ 改为 implemented。"),
        "__scaffold_missing__": [
            "host_state.fields / size —— 你宿主的状态字段与 static_assert 尺寸（🔴 必须实测）",
            "mc_state.fields / size —— 客侧状态字段与尺寸（🔴 必须实测）",
            "host_flags / mc_flags / input_type / hurt_flags / mc_event_type / ren_type —— "
            "各枚举的成员名与取值（🔴 必须实测）",
            "magic / version / mapping_name / units_per_block —— 协议标识与单位；"
            "取值约定见 schema.template.yaml",
            "host_prefix / host_abbr / namespace —— 标识符命名（驱动 Header 字段名与 <Abbr>State 名）",
        ],
        "namespace": "ptmodmaker::proto",
        "host_abbr": abbr,
        "host_prefix": prefix,
        "magic": _host_magic(key),
        "version": 1,
        "mapping_name": "Local\\%s_v1" % abbr,
        "units_per_block": "1.0",
        "host_flags": [
            {"name": "k%sInGame" % abbr, "value": "1u << 0"},
            {"name": "k%sMenuOpen" % abbr, "value": "1u << 1"},
            {"name": "k%sLoading" % abbr, "value": "1u << 2"},
        ],
        "host_state": {
            "fields": ["std::uint32_t seq;", "std::uint32_t flags;",
                       "std::uint32_t worldId;", "std::uint32_t collisionEpoch;",
                       "double        posX, posY, posZ;", "float         yaw, pitch;",
                       "std::uint8_t  pad[0x10];"],
            "size": "0x40", "ground_grid": None,
        },
        "mc_flags": [
            {"name": "kMcInWorld", "value": "1u << 0"},
            {"name": "kMcScreenOpen", "value": "1u << 1"},
            {"name": "kMcOnGround", "value": "1u << 2"},
        ],
        "mc_state": {
            "fields": ["std::uint32_t seq;", "std::uint32_t flags;",
                       "double        x, y, z;", "float         yaw, pitch;",
                       "float         eyeHeight;", "std::uint32_t teleportAck;",
                       "std::uint8_t  pad[0x98];"],
            "size": "0xC8",
        },
        "input_type": [
            {"name": "kInKey", "value": "1"},
            {"name": "kInMouseButton", "value": "2"},
            {"name": "kInReleaseAll", "value": "6"},
        ],
        "hurt_flags": [{"name": "kHurtMelee", "value": "1u << 0"}],
        "mc_event_type": [{"name": "kEvHitActor", "value": "1"},
                          {"name": "kEvPlayerDied", "value": "2"}],
        "ren_type": [{"name": "kRenPad", "value": "0"}, {"name": "kRenClearAll", "value": "3"}],
        # var slot in the v0 container order -> required for the cpp backend.
        "col_tri_flags": {"members": [{"name": "kTriTerrain", "value": "1u << 0"}],
                          "has_shift": True},
        # optional slots: present here as null/false so the skeleton is explicit, not silent.
        "dig_material": None,
        "ren_dug": False,
        "tool_kind": None,
    }


def _dump_yaml(obj, path, header_lines=()):
    import yaml
    with open(path, "w", encoding="utf-8") as f:
        for h in header_lines:
            f.write("# " + h + "\n")
        yaml.safe_dump(obj, f, sort_keys=False, width=100, allow_unicode=True)


HOST_PREFLIGHT_SRC = '''#!/usr/bin/env python3
"""host_preflight.py — generated by pt_scaffold for host '{KEY}'.

Why this file exists (gap C of the newbie experiment): when a scaffolded project was run for a
host that is not implemented, the old harness died with the cryptic, WRONG message
`unknown host 'SKY'`.  This preflight turns the two real failure modes into a human message:

  * the host has no vocabulary in the schema at all            -> how to add one
  * the vocabulary is still the pt_scaffold SKELETON           -> exactly what is left to measure

It exits with code 2 (distinct from a scenario FAIL of 1) and never prints a traceback.
"""
import os
import sys

HOST = "{KEY}"
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEMA = os.path.normpath(os.path.join(HERE, "..", "schema.yaml"))


def schema_path():
    return os.environ.get("PT_SCHEMA") or DEFAULT_SCHEMA


def _fail(title, body):
    print("=" * 78, file=sys.stderr)
    print(f"[{{HOST}}] {{title}}", file=sys.stderr)
    for line in body:
        print(("  " + line) if line else "", file=sys.stderr)
    print("=" * 78, file=sys.stderr)
    raise SystemExit(2)


def check():
    p = schema_path()
    if not os.path.exists(p):
        _fail("未实现宿主适配器：找不到 schema.yaml。",
              [f"期望路径: {{p}}",
               "设置 PT_SCHEMA 指向你的 schema.yaml，或把骨架放在上面的默认位置。"])
    import yaml
    schema = yaml.safe_load(open(p, encoding="utf-8")) or {{}}
    vocabs = schema.get("vocabularies") or {{}}
    if HOST not in vocabs:
        _fail(f"未实现宿主适配器：schema 里没有 host '{{HOST}}' 的词表。",
              [f"schema   : {{p}}",
               f"已有词表 : {{list(vocabs)}}",
               "",
               "缺的就是「一张词表」。请在 vocabularies 下加一份键为 "
               f"{{HOST!r}} 的词表（字段契约见 schema.template.yaml / pt_schema_describe）。"])
    v = vocabs[HOST]
    if v.get("__scaffold_status__") == "skeleton":
        missing = v.get("__scaffold_missing__") or []
        _fail(f"未实现宿主适配器：host '{{HOST}}' 的词表仍是 pt_scaffold 生成的骨架（占位值）。",
              [f"schema : {{p}}",
               "本脚手架不臆造宿主词表——「填一张词表」正是接新宿主的固定成本，必须由你给真值。",
               ""] +
              ["要补的东西："] + [f"- {{m}}" for m in missing] + [
               "",
               "步骤：",
               f"  1) 按 TODO-MEASURE.md 实测其中的 🔴 项；",
               f"  2) 把真值写进 schema.yaml 的 vocabularies.{{HOST}}；",
               "  3) 把 __scaffold_status__ 改为 implemented（或删掉该键）；",
               "  4) 重跑本脚本。"])
    return p


if __name__ == "__main__":
    check()
    print(f"[{{HOST}}] preflight OK: vocabulary present and implemented.")
'''


def _render_tools(tools_dir, key, vocab):
    """Rewrite the copied stub harness so it references `key`, never the built-in SKY."""
    abbr = str(vocab.get("host_abbr") or _camel(key))
    prefix = str(vocab.get("host_prefix") or abbr.lower())
    in_game = _pick_flag(vocab.get("host_flags"), ("inGame", "ingame", "game"),
                         "k%sInGame" % abbr)
    subs = [
        ('"SKY"', '"%s"' % key),                       # L.generate("SKY") / L.verify("SKY")
        ('["SKY", "FO4"]', '["%s"]' % key),            # layout_from_schema main() default
        ("SKYState", "%sState" % key),                 # P.SKYState -> P.<key>State
        ("SKY_N", "HOST_N"),
        ("P.kOffSkyState", "P.kOff%sState" % abbr),
        ("P.kSkyInGame", "P.%s" % in_game),
        ("hdr.skyrimPid", "hdr.%sPid" % prefix),
        ("hdr.skyrimHeartbeatMs", "hdr.%sHeartbeatMs" % prefix),
        ('os.path.join(HERE, "..", "v0-schema", "schema.yaml")',
         'os.path.join(HERE, "..", "schema.yaml")'),
    ]
    touched = {}
    for fn in STUB_FILES:
        p = os.path.join(tools_dir, fn)
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        n = 0
        for a, b in subs:
            n += txt.count(a)
            txt = txt.replace(a, b)
        if fn == "run_demo.py":
            old = 'def main():\n    L.verify("%s")' % key
            new = ('def main():\n    import host_preflight\n'
                   '    host_preflight.check()   # 可读地失败，而不是 unknown host\n'
                   '    L.verify("%s")' % key)
            if old in txt:
                txt = txt.replace(old, new)
                n += 1
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
        touched[fn] = n
    with open(os.path.join(tools_dir, "host_preflight.py"), "w", encoding="utf-8") as f:
        f.write(HOST_PREFLIGHT_SRC.format(KEY=key))
    return touched


def _todo_measure(host, guest):
    data = _load_yaml(PARAMS_YAML)
    params = data.get("params", [])
    h = (host or "").lower()
    g = (guest or "").lower()
    reds = [p for p in params if p.get("reuse_level") == "red"]
    # Prefer a host match; fall back to guest, then to the whole library. Never mix games needlessly.
    host_matched = [p for p in reds if h and
                    (h in (p.get("host") or "").lower() or
                     (p.get("host") or "").lower() in h)]
    guest_matched = [p for p in reds if g and
                     (g in (p.get("guest") or "").lower() or
                      (p.get("guest") or "").lower() in g)]
    if host_matched:
        chosen, scope = host_matched, "按宿主匹配"
    elif guest_matched:
        chosen, scope = guest_matched, "按客侧匹配（宿主未命中）"
    else:
        chosen, scope = reds, "全库（宿主/客侧均未命中，列出全部 🔴）"
    return chosen, scope, data.get("meta", {})


def pt_scaffold(args):
    tool = "pt_scaffold"
    host = (args.get("host") or "").strip()
    guest = (args.get("guest") or "").strip()
    out_dir = args.get("out_dir") or ""
    schema_path = args.get("schema_path") or SCHEMA_YAML
    if not os.path.isabs(schema_path):
        schema_path = os.path.normpath(os.path.join(LAB, schema_path))
    if not host or not guest or not out_dir:
        missing = [n for n, v in (("host", host), ("guest", guest), ("out_dir", out_dir)) if not v]
        return pt_error(tool, issue("$.%s" % missing[0], "非空字符串", "缺失",
                                    "host / guest / out_dir 均为必填。"), missing=missing)
    if not os.path.isabs(out_dir):
        out_dir = os.path.normpath(os.path.join(HERE, out_dir))
    if not os.path.exists(schema_path):
        return pt_error(tool, issue("$.schema_path", "存在的文件路径", "不存在",
                                    f"schema 不存在: {schema_path}（相对路径按 03-复现路线/ 解析）"))
    try:
        schema = _load_yaml(schema_path)
    except Exception as e:  # noqa: BLE001
        return pt_error(tool, issue("$.schema_path", "合法 YAML", f"{type(e).__name__}: {e}",
                                    "schema 解析失败。"), schema_path=schema_path)
    if not isinstance(schema, dict):
        return pt_error(tool, issue("$.schema_path", "mapping（schema.yaml 顶层）",
                                    got_of(schema), "schema.yaml 顶层必须是 mapping。"))

    vocab_key, match_kind, is_new = _resolve_vocab(schema, host)

    # Materialise the schema the scaffold will use (self-contained inside out_dir).
    os.makedirs(out_dir, exist_ok=True)
    effective = schema
    if is_new:
        effective = dict(schema)
        vocabs = dict(effective.get("vocabularies") or {})
        vocabs[vocab_key] = _skeleton_vocab(vocab_key)
        effective["vocabularies"] = vocabs
    eff_schema_path = os.path.join(out_dir, "schema.yaml")
    _dump_yaml(effective, eff_schema_path, header_lines=[
        "=" * 74,
        "schema.yaml — 由 pt_scaffold 生成（%s ← %s）" % (host, guest),
        "来源 schema: %s" % schema_path,
        "词表解析   : %s (%s)" % (vocab_key, match_kind),
        ("注意：%s 的这份词表是**骨架**（占位值），不是可用的宿主适配器。" % vocab_key)
        if is_new else "词表来自你提供的 schema，未做任何 alias。",
        "契约与模板：调用 pt_schema_describe。",
        "=" * 74,
    ])

    vocab = (effective.get("vocabularies") or {}).get(vocab_key) or {}

    # 1) protocol/ — real ptgen output, for THIS host's id
    proto_dir = os.path.join(out_dir, "protocol")
    os.makedirs(proto_dir, exist_ok=True)
    env = {"PYTHONPATH": V1_PTGEN_SRC + os.pathsep + os.environ.get("PYTHONPATH", "")}
    gens = {}
    for lang in ("cpp", "python"):
        rc, out, err = _py("-m", "ptgen", "--schema", eff_schema_path, "--lang", lang,
                           "--out", proto_dir, "--host", vocab_key, env=env, timeout=120)
        gens[lang] = {"exit_code": rc, "stdout": out.strip(), "stderr": err.strip() or None}

    # 2) tools/ — the fake-stub harness, rewritten to reference THIS host's id
    tools_dir = os.path.join(out_dir, "tools")
    os.makedirs(tools_dir, exist_ok=True)
    for fn in STUB_FILES:
        shutil.copy2(os.path.join(V1_STUBS, fn), os.path.join(tools_dir, fn))
    rewrites = _render_tools(tools_dir, vocab_key, vocab)

    # 3) TODO-MEASURE.md — red params pulled straight from params.yaml (never hard-coded)
    reds, scope, meta = _todo_measure(host, guest)
    lines = [
        f"# TODO-MEASURE — {host} ← {guest}",
        "",
        "> 本文件由 `pt_scaffold` 从 `v0-params/params.yaml` 自动筛出 **🔴 必须实测** 档参数生成。",
        "> 这些数值**不存在可复用的真值**，必须在真机上实测标定后才可写入本适配器。",
        f"> 筛选范围：{scope}；命中 {len(reds)} 条。",
        "",
    ]
    for caveat in meta.get("caveats", []):
        lines.append(f"> ⚠ {caveat}")
    lines += ["", "## 待实测项", ""]
    for r in reds:
        src = "%s@%s (%s)" % (r.get("source_repo") or "-",
                              (r.get("source_commit") or "-")[:10],
                              r.get("source_doc") or "-")
        dnp = "  `do_not_package`" if r.get("do_not_package") else ""
        lines += [
            f"- [ ] **{r.get('id')}** — `{r.get('param')}`",
            f"  - 宿主/客侧: {r.get('host')} ← {r.get('guest')}",
            f"  - 现值: `{r.get('value')}`" + (f"（单位: {r.get('unit')}）" if r.get('unit') else ""),
            f"  - 证据档: **{r.get('evidence')}**（实机验证: {bool(r.get('verified_on_hardware'))}）{dnp}",
            f"  - 出处: {src}",
        ]
        if r.get("notes"):
            lines.append(f"  - 备注: {r['notes']}")
        lines.append("")
    if is_new:
        lines += [
            f"## 本宿主的词表骨架（{vocab_key}）必须先补完",
            "",
            "> `pt_scaffold` **没有**也不会替你臆造宿主词表——那是接新宿主的固定成本。",
            "> 下面这些字段当前是**占位值**，必须在 `schema.yaml` 的 "
            f"`vocabularies.{vocab_key}` 里换成实测真值：",
            "",
        ]
        for m in vocab.get("__scaffold_missing__", []):
            lines.append(f"- [ ] {m}")
        lines += [
            "",
            f"> 改完后把 `vocabularies.{vocab_key}.__scaffold_status__` 改为 `implemented`，",
            "> 再跑 `python tools/run_demo.py`（它会先做 preflight）。",
            "",
        ]
    lines += [
        "## 明确不做（🔴）",
        "",
        "- ❌ 不生成宿主侧 natives / SDK 调用代码（如 SKSE / F4SE / 内存 hook）——",
        "  这部分依赖真机上的脚本名、函数签名与偏移，**只能实测**，本脚手架拒绝臆造。",
        "- ❌ 不猜测 yaw/pitch 表达式、碰撞策略、合成挂点或宿主几何。",
        "",
    ]
    with open(os.path.join(out_dir, "TODO-MEASURE.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # 4) README.md — template
    readme = f"""# passthrough 适配器骨架 — {host} ← {guest}

由 `pt_scaffold`（PTmodmaker）生成。**这是骨架，不是可用成品。**

## 五件东西（桥）中，本骨架覆盖了哪些

| # | 组件 | 本骨架状态 |
|---|------|-----------|
| ① | 客侧 mod（guest） | 🧱 占位：`protocol/` 里有生成好的协议头，逻辑需你写 |
| ② | 宿主侧插件（host） | ❌ **未生成**——见 `TODO-MEASURE.md` 的「明确不做」 |
| ③ | 传输层（约定） | ✅ 来自 schema：共享内存映射（`Local\\\\...` 命名），协议头即约定 |
| ④ | 画面合成器 | ❌ 未生成（依赖真机渲染路径） |
| ⑤ | 启动器 | 🧱 占位：`tools/` 是可跑的假桩自测 harness |

## 生成物

- `schema.yaml` — 本骨架**自带的** schema（container 为共用不变骨架；vocab = `{vocab_key}`）。
  `tools/` 与 `protocol/` 都只读这一份，**不再依赖 `v0-schema/`**。
- `protocol/` — `ptgen` 依据上面的 schema 为宿主 `{vocab_key}` 生成的多语言协议头。
- `tools/` — 假桩 harness（`fake_host.py` / `fake_guest.py` / `run_demo.py` / …）。**不启动真游戏**。
  其中 `host_preflight.py` 会在跑场景前先做**可读**的「宿主适配器是否就绪」检查。
- `TODO-MEASURE.md` — 必须先实测的 🔴 参数清单（含出处）。
- `README.md` — 本文件。

## 跑自测（不启动游戏）

```bash
python tools/run_demo.py
```

- 若 `{vocab_key}` 的词表仍是骨架，你会看到一条**可读的**「未实现宿主适配器」提示
  （列出还缺什么、怎么补），而不是 `unknown host '...'`。
- 也可以用 `PT_SCHEMA=/abs/path/to/your/schema.yaml PT_HOST={vocab_key} python tools/run_demo.py`
  指向你自己的 schema。

## 覆盖面说明

- vocab 解析: `{vocab_key}`（{match_kind}）
- 生成后端: cpp, python
- 安全: 本脚手架拒绝一切联机/多人/反作弊/服务端地址输入。
"""
    with open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    manifest = sorted(
        os.path.relpath(os.path.join(dp, fn), out_dir)
        for dp, _dn, fns in os.walk(out_dir) for fn in fns
    )
    warnings = []
    if is_new:
        warnings.append(
            f"宿主 {host!r} 未在你的 schema 中注册：**没有** alias 到任何内置宿主；"
            f"已用你宿主的 id {vocab_key!r} 生成一份**骨架词表**（占位值）。"
            f"接新宿主的固定成本就是「填这张词表」：补完 schema.yaml 的 vocabularies.{vocab_key} "
            f"再把 __scaffold_status__ 改为 implemented。")
    if gens.get("cpp", {}).get("exit_code") != 0:
        warnings.append(f"ptgen cpp 失败: {gens.get('cpp')}")

    return {
        "tool": tool,
        "ok": True,
        "host": host,
        "guest": guest,
        "out_dir": out_dir,
        "schema_path": schema_path,
        "schema_used": eff_schema_path,
        "vocab": {"key": vocab_key, "resolution": match_kind, "is_new_host": is_new,
                  "marker": vocab.get("__scaffold_status__")},
        "generated": {
            "protocol": gens,
            "tools": STUB_FILES + ["host_preflight.py"],
            "tool_host_rewrites": rewrites,
            "todo_measure": {"red_count": len(reds), "scope": scope},
        },
        "manifest": manifest,
        "warnings": warnings,
        "evidence_level": E_MEASURED,
        "does_not": [
            "❌ 不生成宿主侧 natives / SDK 调用代码（SKSE/F4SE/内存 hook）——这依赖真机脚本名、"
            "函数签名与偏移，属 🔴 必须实测，本工具拒绝臆造。",
            "❌ 不生成画面合成器（依赖真机渲染路径）。",
            "❌ 不生成可用成品：客侧 mod 与启动器仅为占位骨架。",
            "❌ 不为联机/多人/反作弊环境生成任何东西（工具层拦截）。",
            "❌ 不写 v0-*/v1-*：protocol 由 ptgen 直接生成到 out_dir，tools 为拷贝后按宿主 id 重写。",
            "❌ 不 alias / 不回退到内置宿主词表：未注册宿主只会拿到自己 id 的**骨架**词表。",
        ],
    }


# ============================================================================= tool registry
TOOLS = {
    "pt_schema_validate": {
        "fn": pt_schema_validate,
        "schema": {
            "type": "object",
            "properties": {
                "schema_path": {
                    "type": "string",
                    "description": "schema.yaml 路径（绝对或相对 03-复现路线/）。默认 v0-schema/schema.yaml。",
                },
                "header_path": {
                    "type": "string",
                    "description": "可选。你自己宿主的真实协议头（.h）。传入后走 extract→generate"
                                   "→结构化 diff 的同一套流程，并为新宿主返回逐行差异诊断"
                                   "（按 标识符/字面量/结构顺序 分类），不再只对内置 3 宿主跑。",
                },
            },
            "additionalProperties": False,
        },
        "description": (
            "校验一份 schema.yaml 的**结构**，并做 extract→generate→structural-diff 的 round-trip，"
            "返回每个宿主的**结构性 diff 数**；失败时一定是**结构化错误**（issues[] 每项含 "
            "path/expected/got/hint），绝不抛裸异常。\n"
            "输入: {schema_path?（默认 v0-schema/schema.yaml）, header_path?（你自己宿主的真实协议头）}。\n"
            "  - 不传 header_path：对内置三份真实头（SkyCraft/FO4/ValCraft）跑 round-trip。\n"
            "  - 传了 header_path：对你的宿主跑同一套流程（extract_vocab → gen_header → 归一化 diff），"
            "diff≠0 时返回逐行差异摘要并按 标识符(identifier)/字面量(literal)/结构顺序(structure_order) "
            "分类（roundtrip.diagnostics + counts_by_category）。**这是「接第 4 款游戏」能自证的地方。**\n"
            "输出: {ok, schema_path, header_path, structure:{ok,issues[],warnings[],summary,issue_count}, "
            "roundtrip:{mode,exit_code,hosts|diagnostics,counts_by_category,conclusion}, evidence_level, does_not}。\n"
            "**两条隐藏契约（旧版只在崩溃时暴露，现在写在这里）**：\n"
            "  ① `container.order` 必须是 **mapping 的列表**（每项 {kind, key?}，"
            "kind ∈ regions/var/fixed/optional）——写成字符串列表旧版会崩成 "
            "`AttributeError: 'str' object has no attribute 'get'`。"
            "注意 `container.includes` **相反**，必须是**字符串列表**（每条是一整行 #include；"
            "写成 mapping 列表会让 gen_header 报 TypeError）。\n"
            "  ② `vocabulary_schema` 的**顶层键名就是每份 vocabulary 的必填字段名**；值只是说明文本。"
            "不要写成 {required:[...], optional:[...]}，否则工具会反过来要求你的词表拥有名为 "
            "'required'/'optional' 的字段。（完整契约 + 带注释模板：调 pt_schema_describe。）\n"
            f"证据档: {E_MEASURED}（真跑 extract/gen_header；SKY/FO4 为 MIT，目标 diff=0；"
            "VAL 无 LICENSE，仅作表达力参考，不作为通过/失败判据）。\n"
            "它不会做: 不校验 C++ 表达式的语义正确性（只做结构键检查，语义交给实际生成暴露）；"
            "不修改 schema；不写 v0-*（round-trip 在 v2-mcp/.work 的隔离镜像中跑）；不启动任何游戏。"
        ),
    },
    "pt_schema_describe": {
        "fn": pt_schema_describe,
        "schema": {
            "type": "object",
            "properties": {
                "schema_path": {
                    "type": "string",
                    "description": "可选。传了就顺带体检这份 schema（返回它的结构 issues/warnings）。",
                },
            },
            "additionalProperties": False,
        },
        "description": (
            "返回 **schema.yaml 的契约说明**（每个字段的类型/是否必填/含义），以及一份**带注释的 "
            "`schema.template.yaml`** 作为你写词表的起点。这是「schema 的 schema」——旧版完全缺失，"
            "新手只能靠逆读产物 + 二分反推。\n"
            "输入: {schema_path?（可选，顺带体检这份 schema）}。\n"
            "输出: {ok, template_filename, hidden_contracts[], contract:{top_level, container.includes, "
            "container.regions_template, container.fixed, container.order{type,item,example,pitfall}, "
            "vocabulary_schema{type,meaning,pitfall}, vocabulary_fields, order_var_keys, "
            "order_optional_keys}, template(带注释 YAML 全文), observed?, evidence_level, does_not}。\n"
            "**两条隐藏契约**（也返回在 hidden_contracts 里）：\n"
            "  ① container.order 必须是 **mapping 列表**（{kind, key?}）；container.includes 必须是 "
            "**字符串列表**。\n"
            "  ② vocabulary_schema 的**顶层键名 = 每份 vocabulary 的必填字段名**。\n"
            f"证据档: {E_MEASURED}（契约来自对 gen_header.py / ptgen cpp backend 的实现阅读 + 对照实测："
            "includes=字符串列表可用、=mapping 列表使 gen_header 失败；order=字符串列表触发 AttributeError）。\n"
            "它不会做: 不修改任何 schema；不替你填词表真值；不校验语义（语义交给 pt_schema_validate 的 round-trip）。"
        ),
    },
    "pt_param_lookup": {
        "fn": pt_param_lookup,
        "schema": {
            "type": "object",
            "properties": {
                "host": {"type": "string",
                         "description": "宿主名子串（大小写不敏感），如 skyrim / valheim / gta。"},
                "color": {"type": "string", "enum": ["green", "yellow", "red"],
                          "description": "复用档：green 可直搬 / yellow 需复核 / red 必须实测。"},
            },
            "additionalProperties": False,
        },
        "description": (
            "查询 PTmodmaker 参数库（CC0 种子库），返回带**出处与证据档**的记录。\n"
            "输入: {host?（子串匹配）, color?（green/yellow/red）}。\n"
            "输出: {filter, cli_output（param_lookup.py 原文）, matched, counts_by_color, records:"
            "[{id,host,guest,param,value,unit,reuse_level,evidence,source:{repo,commit,doc},"
            "verified_on_hardware,do_not_package,notes}], library(meta), does_not}。\n"
            f"证据档: {E_CLAIMED}——库中**全部**参数 verified_on_hardware=false；"
            "每条记录的 evidence 为 repo（读源码）/doc（项目自述）/inference（推断）三档之一；"
            "do_not_package=true 者不可默认打包（如 ValCraft 无 LICENSE）。\n"
            "它不会做: 不验证参数真值（本库无实机验证数值）；不提供代码片段（无出处参数不入库）；"
            "不联网重拉上游仓库。"
        ),
    },
    "pt_stub_run": {
        "fn": pt_stub_run,
        "schema": {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "enum": ["heartbeat", "epoch", "collision_wall", "all"],
                    "description": "heartbeat=宿主心跳超时安全冻结；epoch=宿主重启后陈旧数据丢弃；"
                                   "collision_wall=>50° 不可攀爬墙；all=三个都跑。默认 all。",
                }
            },
            "additionalProperties": False,
        },
        "description": (
            "运行假桩（fake_host ↔ fake_guest）场景，验证传输与状态机，**不启动任何游戏**。\n"
            "输入: {scenario: heartbeat|epoch|collision_wall|all}。\n"
            "输出: {scenario, transport, results:{<scenario>:{passed, 关键数值...}}, verdict, overall:"
            "PASS|FAIL, stdout, exit_code, does_not}。关键数值示例：heartbeat→guest_froze/frozen_ticks；"
            "epoch→session_discards/max_single_tick_dx/late_teleports；collision_wall→guest_max_x/"
            "crossed_wall/climbed_wall/blocked_ticks。\n"
            f"证据档: {E_MEASURED}（假桩真实执行；但只证明协议与状态机，不等于真游戏集成）。\n"
            "它不会做: 不启动真游戏；不测真引擎的插件加载/反作弊/画面合成/显卡路径；"
            "不写 v1-stubs（每次在 v2-mcp/.work 的隔离副本中运行）。"
        ),
    },
    "pt_scaffold": {
        "fn": pt_scaffold,
        "schema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "宿主游戏名，如 'The Elder Scrolls V: Skyrim Special Edition' 或新宿主 'teardown'。"},
                "guest": {"type": "string", "description": "客侧游戏名，如 'Minecraft: Java Edition'。"},
                "out_dir": {"type": "string", "description": "输出目录（绝对，或相对 v2-mcp/）。"},
                "schema_path": {"type": "string",
                                "description": "可选。你的 schema.yaml（绝对或相对 03-复现路线/）。"
                                               "默认 v0-schema/schema.yaml。宿主在其中注册了就按它生成；"
                                               "没注册就用你传入的 host 自身 id 生成**骨架词表**"
                                               "（绝不 alias/回退到内置宿主）。"},
            },
            "required": ["host", "guest", "out_dir"],
            "additionalProperties": False,
        },
        "description": (
            "为一个 host↔guest 生成**适配器骨架**（不是可用成品）。\n"
            "输入: {host, guest, out_dir（均必填）, schema_path?}。\n"
            "输出: 目录含 `schema.yaml`（**自带的** schema：共用 container + 本 host 的 vocab）、"
            "`protocol/`（ptgen 为**本 host 的 id** 生成的多语言协议头，如 `teardown.proto.h`）、"
            "`tools/`（假桩 harness 拷贝**并按 host id 重写**，含 `host_preflight.py`）、`README.md`、"
            "`TODO-MEASURE.md`（从 v0-params/params.yaml 现筛的 🔴 必须实测清单，含出处，**非硬编码**）。"
            "返回 {host, guest, out_dir, schema_used, vocab:{key,resolution,is_new_host,marker}, generated:"
            "{protocol,tools,tool_host_rewrites,todo_measure}, manifest, warnings, does_not}。\n"
            "**闭环保证（旧版是断的）**：\n"
            "  - 生成的 `protocol/` 用**你宿主的 id**，不硬编码 SKY；`tools/` 里的运行脚本也引用该 id，"
            "不再出现 `unknown host 'SKY'`。\n"
            "  - 宿主未注册时**绝不 alias / 回退到别家词表**：改用你宿主的 id 生成一份 "
            "`__scaffold_status__: skeleton` 的**骨架词表**；此时 `python tools/run_demo.py` 会给出"
            "**可读的**「未实现宿主适配器」提示（列出缺什么、怎么补），退出码 2。\n"
            "  - **隐藏契约**：`container.order` 必须是 **mapping 列表**（{kind, key?}）、"
            "`vocabulary_schema` 的**顶层键名即词表必填字段名**——这两条旧版只在崩溃时暴露，"
            "现已在 pt_schema_validate / pt_schema_describe 里说明。`container.includes` 则必须是"
            "**字符串列表**（每条一整行 #include）。\n"
            f"证据档: {E_MEASURED}（ptgen 真实生成 + params.yaml 真实筛选）。\n"
            "它不会做: **不生成宿主侧 natives/SDK 调用代码**（SKSE/F4SE/内存 hook）——那依赖真机的"
            "脚本名、函数签名与偏移，是 🔴 必须实测的部分，本工具拒绝臆造；不生成画面合成器；"
            "不生成可用成品（客侧 mod 与启动器仅占位）；不为联机/多人/反作弊环境生成任何东西；"
            "不写 v0-*/v1-*。"
        ),
    },
}


# ============================================================================= JSON-RPC
def _list_tools():
    return [{"name": name, "description": spec["description"], "inputSchema": spec["schema"]}
            for name, spec in TOOLS.items()]


def handle(msg):
    if not isinstance(msg, dict):
        return None
    method = msg.get("method")
    mid = msg.get("id")

    if method == "initialize":
        req = (msg.get("params") or {}).get("protocolVersion")
        ver = req if req in SUPPORTED_PROTOCOLS else DEFAULT_PROTOCOL
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": ver,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }}

    if method in ("notifications/initialized", "notifications/cancelled",
                  "notifications/roots/list_changed"):
        return None

    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": _list_tools()}}

    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        if name not in TOOLS:
            return {"jsonrpc": "2.0", "id": mid, "result": text_result(
                {"ok": False, "error": f"未知工具: {name}", "known": list(TOOLS)}, is_error=True)}
        refused = screen(name, args)
        if refused is not None:
            return {"jsonrpc": "2.0", "id": mid, "result": text_result(refused, is_error=True)}
        # 兜底：任何工具 handler 都不允许把异常泄漏成裸字符串。
        # 结构化 error（issues[]）进 result，traceback 只进 stderr。
        try:
            payload = TOOLS[name]["fn"](args)
        except SystemExit as e:  # a tool must never tear the server down
            print(f"[ptmodmaker-mcp] tool {name} raised SystemExit({e!r})",
                  file=sys.stderr, flush=True)
            payload = pt_error(name, issue("$", "工具正常返回（不退出进程）",
                                           f"SystemExit({e!r})",
                                           "工具内部误用了 SystemExit；这属于工具缺陷。"))
        except Exception as e:  # noqa: BLE001
            payload = pt_error(name, exception_issue(e))
        is_err = bool(isinstance(payload, dict) and payload.get("ok") is False)
        return {"jsonrpc": "2.0", "id": mid, "result": text_result(payload, is_error=is_err)}

    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"Method not found: {method}"}}


def _iter_messages(stream):
    """Yield raw JSON message strings; tolerate both newline-delimited and Content-Length framing."""
    while True:
        line = stream.readline()
        if not line:
            return
        s = line.strip()
        if not s:
            continue
        if s.lower().startswith("content-length:"):
            try:
                n = int(s.split(":", 1)[1].strip())
            except ValueError:
                continue
            while True:                       # consume the rest of the headers
                h = stream.readline()
                if h in ("\r\n", "\n", ""):
                    break
            yield stream.read(n)
        else:
            yield s


def main():
    out = sys.stdout
    for raw in _iter_messages(sys.stdin):
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            resp = {"jsonrpc": "2.0", "id": None,
                    "error": {"code": -32700, "message": "Parse error"}}
        else:
            resp = handle(msg)
        if resp is not None:
            out.write(json.dumps(resp, ensure_ascii=False) + "\n")
            out.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
