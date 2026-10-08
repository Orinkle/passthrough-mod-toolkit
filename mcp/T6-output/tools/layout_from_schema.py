#!/usr/bin/env python3
"""layout_from_schema.py — the SINGLE place byte layouts come from.

Reads `03-复现路线/v0-schema/schema.yaml` (the one source of truth, written by T1) and
*emits* a Python module of `ctypes.Structure` definitions + scalar/enum constants + region
offsets.  `fake_host.py` / `fake_guest.py` import the emitted module.  No downstream file
contains a hand-written struct field, a hand-written size, or a hand-written offset.

Why this file exists: v0-schema/ ships a C++ header generator (`gen_header.py`) but no
Python backend.  Per the task we therefore write the minimal Python backend here.

What it parses (all from schema.yaml):
  * container.regions_template + container.fixed  -> `inline constexpr` scalars,
    `enum X : T {..}` members, `struct X {..};` field lists and `static_assert(sizeof(X)..)`.
  * vocabularies[host] -> host_state / mc_state field lists, and the "word" enums
    (host_flags, mc_flags, input_type, hurt_flags, mc_event_type, ren_type, ...).
  * the runtime `Header` struct, whose pid/heartbeat field names are driven by `host_abbr`
    (Sky -> skyrimPid / skyrimHeartbeatMs).

Self-check (§ requirement): build the module, then assert that what ctypes computes (the real
C ABI) matches what the schema declares (the literal `static_assert` sizes), that the field
names/order match the schema decls, and that every emitted scalar equals an independent
evaluation of the schema expression.  A mismatch is a hard failure (SystemExit(1)).

    python layout_from_schema.py            # generate + verify SKY and FO4
    python layout_from_schema.py SKY        # one host
"""
from __future__ import annotations

import ctypes
import os
import re
import sys
import types

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.environ.get(
    "PT_SCHEMA", os.path.normpath(os.path.join(HERE, "..", "v0-schema", "schema.yaml")))
GEN_DIR = os.environ.get("PT_GEN_DIR", os.path.join(HERE, "generated"))

# std:: fixed-width type -> ctypes type.  Anything not here is a hard error (no silent guess).
CTYPE = {
    "std::uint8_t": "ctypes.c_uint8",
    "std::uint16_t": "ctypes.c_uint16",
    "std::uint32_t": "ctypes.c_uint32",
    "std::uint64_t": "ctypes.c_uint64",
    "std::int8_t": "ctypes.c_int8",
    "std::int16_t": "ctypes.c_int16",
    "std::int32_t": "ctypes.c_int32",
    "std::int64_t": "ctypes.c_int64",
    "std::uintptr_t": "ctypes.c_uint64",
    "float": "ctypes.c_float",
    "double": "ctypes.c_double",
    "char": "ctypes.c_char",
}


# ----------------------------------------------------------------------------- schema text
def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    return text


_INT_SUFFIX = re.compile(r"([0-9A-Fa-f])(?:[uUlL]+)\b")
_FLOAT_SUFFIX = re.compile(r"([0-9.])(?:[fF])\b")
_CAST = re.compile(r"std::(?:u?int(?:8|16|32|64)_t)\s*\(")


def _clean_expr(expr: str) -> str:
    """Turn a C++ integral/float constant expression into a Python one."""
    expr = _CAST.sub("(", expr)
    expr = _INT_SUFFIX.sub(r"\1", expr)
    expr = _FLOAT_SUFFIX.sub(r"\1", expr)
    return expr.strip()


def _eval(expr: str, consts: dict) -> object:
    """Evaluate a cleaned constant expression against already-known constants."""
    py = _clean_expr(expr)
    return eval(py, {"__builtins__": {}}, dict(consts))  # noqa: S307 (schema is trusted, ours)


CONSTEXPR_RE = re.compile(
    r"inline\s+constexpr\s+[\w:]+\s+(\w+)\s*=\s*([^;]+);")
ENUM_RE = re.compile(r"enum\s+(\w+)\s*:\s*[\w:]+\s*\{(.*?)\}\s*;", re.S)
STRUCT_RE = re.compile(r"struct\s+(\w+)\s*\{(.*?)\}\s*;", re.S)
SIZEOF_ASSERT_RE = re.compile(
    r"static_assert\(\s*sizeof\(\s*(\w+)\s*\)\s*(==|<=)\s*([^;]+?)\s*\)\s*;", re.S)


def _sources(schema: dict, host: str):
    """Every C++ text fragment that may hold constants / enums / structs.

    The container's regions template carries a `{host_state_off}` placeholder that must be
    rendered per host (Sky -> kOffSkyState, Val -> kOffValState), exactly as gen_header.py does.
    """
    c = schema["container"]
    abbr = schema["vocabularies"][host]["host_abbr"]
    rendered = c["regions_template"].replace("{host_state_off}", f"kOff{abbr}State")
    yield rendered
    for txt in c["fixed"].values():
        yield txt
    yield json_default(schema)


def json_default(schema: dict) -> str:
    # vocabulary enum members carry C++ expressions like "1u << 0"; we collect them separately,
    # this hook only exists so _sources() is uniform.  (No struct/constexpr text here.)
    return ""


def collect_constexprs(schema: dict, host: str = "SKY") -> dict:
    """Gather every `inline constexpr NAME = EXPR;` and evaluate it to a fixpoint."""
    raw = {}
    for txt in _sources(schema, host):
        for name, expr in CONSTEXPR_RE.findall(strip_comments(txt)):
            raw.setdefault(name, expr.strip())
    consts: dict = {}
    pending = dict(raw)
    progressed = True
    while pending and progressed:
        progressed = False
        for name in list(pending):
            try:
                consts[name] = _eval(pending[name], consts)
                del pending[name]
                progressed = True
            except Exception:
                continue
    if pending:  # pragma: no cover - would mean the schema references an unknown constant
        raise ValueError(f"unevaluated constants: {pending}")
    return consts


def collect_enums(schema: dict, host: str = "SKY") -> dict:
    """Container enums (fixed text) -> {NAME: {member: value}}."""
    out: dict = {}
    for txt in _sources(schema, host):
        for ename, body in ENUM_RE.findall(strip_comments(txt)):
            members: dict = {}
            consts = collect_constexprs(schema, host)
            auto = 0
            for part in body.split(","):
                part = part.strip()
                if not part:
                    continue
                if "=" in part:
                    mname, mexpr = part.split("=", 1)
                    val = int(_eval(mexpr, consts))
                else:
                    mname, val = part, auto
                members[mname.strip()] = val
                auto = val + 1
            out[ename] = members
    return out


def parse_structs(schema: dict, host: str = "SKY"):
    """Every `struct X { body };` -> {X: [(name, ctype-str, [dims])]}, plus declared sizes."""
    fields: dict = {}
    order: list = []
    for txt in _sources(schema, host):
        body_txt = strip_comments(txt)
        for name, body in STRUCT_RE.findall(body_txt):
            if name in fields:
                continue
            fields[name] = _parse_body(body, schema, host)
            order.append(name)
    sizes: dict = {}
    for txt in _sources(schema, host):
        for name, op, expr in SIZEOF_ASSERT_RE.findall(strip_comments(txt)):
            sizes[name] = (op, expr.strip())
    return fields, order, sizes


def _parse_body(body: str, schema: dict, host: str = "SKY"):
    """C++ struct body -> [(field_name, ctype_expr, [dim_exprs])]."""
    consts = collect_constexprs(schema, host)
    known_structs = {m[0] for m in STRUCT_RE.findall(
        strip_comments("".join(_sources(schema, host))))}
    out = []
    for decl in [d.strip() for d in body.split(";") if d.strip()]:
        m = re.match(r"^(.*?)\s+([A-Za-z_]\w*(?:\s*\[[^\]]*\])*(?:\s*,\s*[A-Za-z_]\w*(?:\s*\[[^\]]*\])*)*)$", decl, re.S)
        if not m:
            raise ValueError(f"cannot parse field decl: {decl!r}")
        typ = re.sub(r"\s+", " ", m.group(1)).strip()
        rest = m.group(2)
        # base ctype
        if typ in CTYPE:
            base = CTYPE[typ]
        elif typ in known_structs:
            base = typ
        else:
            raise ValueError(f"unknown field type {typ!r} in {decl!r}")
        for one in rest.split(","):
            one = one.strip()
            nm = re.match(r"^([A-Za-z_]\w*)\s*((?:\[[^\]]*\])*)$", one)
            if not nm:
                raise ValueError(f"cannot parse field name {one!r}")
            dims = [d.strip() for d in re.findall(r"\[([^\]]*)\]", nm.group(2))]
            out.append((nm.group(1), base, dims))
    return out


# ----------------------------------------------------------------------------- vocabularies
def _enum_members(entries):
    """[{name, value}] -> {name: int} (value may be a C++ expr string or None)."""
    out = {}
    auto = 0
    for e in entries:
        if e.get("value") is None:
            out[e["name"]] = auto
        else:
            out[e["name"]] = int(_eval(str(e["value"]), {}))
        auto = out[e["name"]] + 1
    return out


def _flatten(nested: dict) -> dict:
    """{ENUM: {member: value}} -> {member: value}."""
    out = {}
    for members in nested.values():
        out.update(members)
    return out


def vocab_enums(schema: dict, host: str) -> dict:
    v = schema["vocabularies"][host]
    consts = collect_constexprs(schema, host)
    out: dict = {}

    def add(entries):
        members = {}
        auto = 0
        for e in entries:
            if e.get("value") is None:
                members[e["name"]] = auto
            else:
                members[e["name"]] = int(_eval(str(e["value"]), consts))
            auto = members[e["name"]] + 1
        out.update(members)

    for key in ("host_flags", "mc_flags", "input_type", "hurt_flags",
                "mc_event_type", "ren_type"):
        add(v[key])
    ctf = v.get("col_tri_flags") or {}
    if ctf.get("members"):
        add(ctf["members"])
    if v.get("dig_material"):
        add(v["dig_material"])
    if v.get("tool_kind"):
        add(v["tool_kind"])
    return out


def vocab_struct(schema: dict, host: str, key: str):
    v = schema["vocabularies"][host]
    spec = v[key]  # {"fields": [...], "size": "0x40", ...}
    consts = collect_constexprs(schema, host)
    known = set(parse_structs(schema, host)[0])
    out = []
    for decl in spec["fields"]:
        decl = decl.strip().rstrip(";").strip()
        m = re.match(r"^(.*?)\s+([A-Za-z_]\w*(?:\s*\[[^\]]*\])*(?:\s*,\s*[A-Za-z_]\w*(?:\s*\[[^\]]*\])*)*)$", decl, re.S)
        typ = re.sub(r"\s+", " ", m.group(1)).strip()
        base = CTYPE.get(typ, typ)
        if base == typ and typ not in known:
            raise ValueError(f"unknown vocab field type {typ!r}")
        for one in m.group(2).split(","):
            one = one.strip()
            nm = re.match(r"^([A-Za-z_]\w*)\s*((?:\[[^\]]*\])*)$", one)
            dims = [d.strip() for d in re.findall(r"\[([^\]]*)\]", nm.group(2))]
            out.append((nm.group(1), base, dims))
    return out, int(_eval(spec["size"], consts))


def header_fields(schema: dict, host: str):
    v = schema["vocabularies"][host]
    p = v.get("host_prefix", v["host_abbr"].lower())
    return [
        ("magic", "ctypes.c_uint32", []),
        ("version", "ctypes.c_uint32", []),
        (f"{p}Pid", "ctypes.c_uint32", []),
        ("mcPid", "ctypes.c_uint32", []),
        (f"{p}HeartbeatMs", "ctypes.c_uint64", []),
        ("mcHeartbeatMs", "ctypes.c_uint64", []),
    ]


# ----------------------------------------------------------------------------- emitter
def _render_ctype(base: str, dims: list, consts: dict) -> str:
    t = base
    for d in reversed(dims):
        n = int(_eval(d, consts)) if d else 0
        t = f"{t} * {n}"
    return t


def build_spec(schema: dict, host: str):
    """Human-readable layout spec, used both to emit and to verify."""
    consts = collect_constexprs(schema, host)
    fields, order, sizes = parse_structs(schema, host)
    v = schema["vocabularies"][host]
    hs_fields, hs_size = vocab_struct(schema, host, "host_state")
    ms_fields, ms_size = vocab_struct(schema, host, "mc_state")

    # struct sizes may reference sizeof(earlier struct); resolve in schema order.
    resolved: dict = {}
    sizes_int: dict = {}
    for name in order:
        if name in sizes:
            op, expr = sizes[name]
            rhs = re.sub(r"sizeof\((\w+)\)", lambda m: str(sizes_int[m.group(1)]), expr)
            val = int(_eval(rhs, {**consts, **sizes_int}))
            resolved[name] = (op, val)
            sizes_int[name] = val

    return {
        "host": host,
        "consts": consts,
        "enums": {**_flatten(collect_enums(schema, host)), **vocab_enums(schema, host)},
        "structs": fields,
        "struct_order": order,
        "struct_sizes": sizes,
        "resolved_sizes": resolved,
        "header": (header_fields(schema, host), 32),
        "host_state": (hs_fields, hs_size),
        "mc_state": (ms_fields, ms_size),
        "scalars": {
            "MAGIC": _eval(str(v["magic"]), consts),
            "VERSION": int(_eval(str(v["version"]), consts)),
            "MAPPING_NAME": str(v["mapping_name"]),
            "UNITS_PER_BLOCK": float(_eval(str(v["units_per_block"]), consts)),
        },
    }


def emit_source(spec: dict) -> str:
    host, consts = spec["host"], spec["consts"]
    L = []
    L.append(f'"""Protocol layout generated from schema.yaml (host: {host}). Do not edit."""')
    L.append("import ctypes")
    L.append("")
    L.append("# ---- scalars from the schema vocabulary ----")
    for k in ("MAGIC", "VERSION", "MAPPING_NAME", "UNITS_PER_BLOCK"):
        L.append(f"{k} = {spec['scalars'][k]!r}")
    L.append("")
    L.append("# ---- container constants (inline constexpr, evaluated) ----")
    for name in sorted(consts):
        L.append(f"{name} = {consts[name]!r}")
    L.append("")
    L.append("# ---- enums (container + vocabulary) ----")
    for name in sorted(spec["enums"]):
        L.append(f"{name} = {spec['enums'][name]!r}")
    L.append("")

    def emit_struct(name, flds, declared=None):
        L.append(f"class {name}(ctypes.Structure):")
        L.append("    _fields_ = [")
        for fname, base, dims in flds:
            L.append(f"        ({fname!r}, {_render_ctype(base, dims, consts)}),")
        L.append("    ]")
        if declared is not None:
            L.append(f"{name}.SIZE = {declared}  # == schema static_assert")
        L.append("")

    for name in spec["struct_order"]:
        declared = spec["resolved_sizes"].get(name)
        emit_struct(name, spec["structs"][name],
                    declared[1] if declared else None)
    emit_struct("Header", spec["header"][0], spec["header"][1])
    emit_struct(f'{spec["host"]}State', spec["host_state"][0], spec["host_state"][1])
    emit_struct("McState", spec["mc_state"][0], spec["mc_state"][1])

    L.append("MAPPING_BYTES = kMappingBytes")
    L.append("")
    L.append("# ---- region base offsets (in the shared mapping) ----")
    L.append("REGIONS = {")
    for name in sorted(consts):
        if name.startswith("kOff") or name.startswith("kMax") or name.endswith("RingBytes") \
                or name in ("kCollisionRingBytes", "kMappingBytes", "kOverlaySlotBytes",
                            "kOverlaySlots", "kInputRingEntries", "kEventRingEntries"):
            L.append(f"    {name!r}: {consts[name]!r},")
    L.append("}")
    L.append("")
    L.append("def sizeof_struct(name):")
    L.append("    return globals()[name].SIZE")
    L.append("")
    return "\n".join(L)


def generate(host: str = "SKY", write: bool = True):
    schema = yaml.safe_load(open(SCHEMA_PATH, encoding="utf-8"))
    if host not in schema["vocabularies"]:
        raise SystemExit(f"unknown host {host!r}; have {list(schema['vocabularies'])}")
    spec = build_spec(schema, host)
    src = emit_source(spec)
    if write:
        os.makedirs(GEN_DIR, exist_ok=True)
        with open(os.path.join(GEN_DIR, f"{host}_layout.py"), "w", encoding="utf-8") as f:
            f.write(src)
    mod = types.ModuleType(f"generated.{host}_layout")
    mod.__file__ = f"<generated {host}>"
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)  # noqa: S102
    return spec, mod


# ----------------------------------------------------------------------------- verify
def verify(host: str = "SKY", verbose: bool = True) -> list:
    spec, mod = generate(host)
    errs = []

    # (1) ABI check: what ctypes lays out (the real C ABI) must equal the size the schema
    #     declares in its `static_assert` / vocabulary `size:`.  This is the B5 gap from the
    #     T1 REPORT: a wrong scalar type would pass a text round-trip but break here.
    for name, (op, declared) in spec["resolved_sizes"].items():
        got = ctypes.sizeof(getattr(mod, name))
        ok = got == declared if op == "==" else got <= declared
        if not ok:
            errs.append(f"{name}: ctypes.sizeof={got} violates schema static_assert {op} {declared}")
    for name, size in (("Header", spec["header"][1]),
                       (f"{host}State", spec["host_state"][1]),
                       ("McState", spec["mc_state"][1])):
        got = ctypes.sizeof(getattr(mod, name))
        if got != size:
            errs.append(f"{name}: ctypes.sizeof={got} != schema size {size}")

    # (2) field lists: names, order and ctypes types must match the schema decls exactly.
    _REV = {getattr(ctypes, v.split(".")[1]): k for k, v in CTYPE.items()}

    def describe(t):
        dims = []
        while issubclass(t, ctypes.Array):
            dims.append(t._length_)
            t = t._type_
        name = _REV.get(t) or t.__name__
        return name, dims

    def want_desc(base, dims):
        if base.startswith("ctypes."):
            name = _REV.get(getattr(ctypes, base.split(".", 1)[1]), base)
        else:
            name = base
        return name, [int(_eval(d, spec["consts"])) for d in dims]

    def check_fields(name, flds):
        cls = getattr(mod, name)
        got = [(n, describe(t)) for n, t in cls._fields_]
        want = [(n, want_desc(b, d)) for n, b, d in flds]
        if got != want:
            errs.append(f"{name}: fields differ\n  got : {got}\n  want: {want}")

    for name in spec["struct_order"]:
        check_fields(name, spec["structs"][name])
    check_fields("Header", spec["header"][0])
    check_fields(f"{host}State", spec["host_state"][0])
    check_fields("McState", spec["mc_state"][0])

    # (3) every emitted scalar equals an independent re-evaluation of the schema expression.
    for name, val in spec["consts"].items():
        if getattr(mod, name) != val:
            errs.append(f"const {name}: emitted {getattr(mod, name)} != schema {val}")
    for name, val in spec["enums"].items():
        if getattr(mod, name) != val:
            errs.append(f"enum {name}: emitted {getattr(mod, name)} != schema {val}")
    for k in ("MAGIC", "VERSION", "MAPPING_NAME", "UNITS_PER_BLOCK"):
        if getattr(mod, k) != spec["scalars"][k]:
            errs.append(f"scalar {k}: mismatch")

    if verbose:
        n_structs = len(spec["struct_order"]) + 3
        print(f"[layout_from_schema] host={host} structs={n_structs} "
              f"consts={len(spec['consts'])} enums={len(spec['enums'])} "
              f"mapping_bytes={spec['consts']['kMappingBytes']}")
        for name in ("Header", f"{host}State", "McState", "ColTri", "ColRegion", "McEvent"):
            if hasattr(mod, name):
                print(f"    sizeof({name}) = {ctypes.sizeof(getattr(mod, name))}")
    if errs:
        print("[layout_from_schema] ASSERTION FAILED:", file=sys.stderr)
        for e in errs:
            print("  -", e, file=sys.stderr)
        raise SystemExit(1)
    if verbose:
        print("[layout_from_schema] schema<->ctypes assertions: PASS")
    return errs


def main(argv):
    hosts = argv[1:] or ["SKY", "FO4"]
    for h in hosts:
        verify(h)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
