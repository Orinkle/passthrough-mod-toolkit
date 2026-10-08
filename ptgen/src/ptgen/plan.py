"""plan.py — build a language-neutral render plan from schema + vocabulary.

The plan is what every non-C++ backend consumes. Field offsets are taken from ctypes
(which uses the same natural alignment as C/C++/C#-sequential/Rust-#[repr(C)]), so the
generated constants/offsets are guaranteed ABI-equivalent to the C++ layout.
"""
import ctypes
from . import model


def _ct_of(t, classes=None):
    return model._ct_of(t, classes)


ALIGN = {'u32': 4, 'i32': 4, 'u64': 8, 'i64': 8, 'f32': 4, 'f64': 8, 'u16': 2, 'u8': 1}
SIZE = {'u32': 4, 'i32': 4, 'u64': 8, 'i64': 8, 'f32': 4, 'f64': 8, 'u16': 2, 'u8': 1}


def _type_size_align(tok, table):
    if isinstance(tok, str):
        if tok in SIZE:
            return SIZE[tok], ALIGN[tok]
        if tok in table:
            return table[tok]
        raise KeyError(tok)
    if isinstance(tok, tuple):
        if tok[0] == 'bytes':
            return tok[1], 1
        if tok[0] == 'arr':
            esz, ea = _type_size_align(tok[1], table)
            return esz * tok[2], ea
    raise TypeError(tok)


def _layout(fields, table):
    """fields: list of (name, ctype_token). Returns (offsets, size, align)."""
    offs = {}
    cur = 0
    align = 1
    for fn, tok in fields:
        sz, al = _type_size_align(tok, table)
        if cur % al:
            cur += al - (cur % al)
        offs[fn] = cur
        cur += sz
        align = max(align, al)
    if cur % align:
        cur += align - (cur % align)
    return offs, cur, align


def unescape_c(s):
    """Interpret the C-source escaping the vocabulary stores for `mapping_name`.

    schema.yaml keeps `mapping_name` in C++ *source* form (``Local\\\\SkyCraft_v1``) so the
    C++ backend can emit it verbatim. Every other backend needs the logical string (one
    backslash) before re-escaping it with its own literal rules.
    """
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            out.append(s[i + 1])
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def c_escape(s):
    """Escape a string for use inside a C-family double-quoted literal.

    The shared-memory mapping name is a Windows name such as ``Local\\SkyCraft_v1``;
    emitted verbatim into C#/Java/Rust it would be an invalid escape (``\\S``) and fail
    to compile. C++ keeps it verbatim on purpose (byte-identical to the hand-written
    header), but every other backend must escape the backslash.
    """
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_plan(schema, vocab):
    classes, sizes = model.build_ctypes()
    abbr = vocab["host_abbr"]
    prefix = vocab["host_prefix"]

    # --- scalar constants ---------------------------------------------------
    scalars = []  # (name, value, kind)  kind: int|long|double|str
    scalars.append(("kMagic", int(vocab["magic"], 0), "int"))
    scalars.append(("kVersion", int(vocab["version"]), "int"))
    scalars.append(("kMappingName", unescape_c(vocab["mapping_name"]), "str"))
    scalars.append(("kUnitsPerBlock", float(vocab["units_per_block"]), "double"))
    for k, v in model.REGIONS.items():
        kind = "long" if isinstance(v, int) and abs(v) >= (1 << 31) else ("double" if isinstance(v, float) else "int")
        scalars.append((k, v, kind))
    for k, v in model.EXTRA_SCALARS.items():
        kind = "long" if isinstance(v, int) and abs(v) >= (1 << 31) else "int"
        scalars.append((k, v, kind))
    # REGIONS and EXTRA_SCALARS overlap (e.g. kWaterGridSize, kNoWater): dedupe by name,
    # first occurrence wins. Without this Rust emits a duplicate `pub const` (a hard error)
    # and the second copy of kNoWater would even get the wrong type (i32 for a f64 value).
    _seen = set()
    _uniq = []
    for item in scalars:
        if item[0] not in _seen:
            _seen.add(item[0])
            _uniq.append(item)
    scalars = _uniq

    # --- enums --------------------------------------------------------------
    enums = []  # (name, underlying, [(member, value_or_None)])
    for ename, (under, members) in model.ENUMS.items():
        enums.append((ename, under, [(m[0], model.eval_value(m[1])) for m in members]))
    # variable enums from vocabulary
    for key, tname, under in (
        ("host_flags", f"{abbr}Flags", "u32"),
        ("mc_flags", "McFlags", "u32"),
        ("input_type", "InputType", "u16"),
        ("hurt_flags", "HurtFlags", "u32"),
        ("mc_event_type", "McEventType", "u32"),
        ("ren_type", "RenType", "u32"),
    ):
        members = vocab.get(key) or []
        enums.append((tname, under, [(m["name"], model.eval_value(m["value"])) for m in members]))
    # col_tri_flags
    ctf = vocab.get("col_tri_flags")
    if ctf:
        enums.append(("ColTriFlags", "u32", [(m["name"], model.eval_value(m["value"])) for m in ctf["members"]]))
        if ctf.get("has_shift"):
            enums.append(("ColTriShift", "u32", [("kTriMaterialShift", 8)]))
    if vocab.get("dig_material"):
        enums.append(("DigMaterial", "u8", [(m["name"], model.eval_value(m["value"])) for m in vocab["dig_material"]]))
    if vocab.get("tool_kind"):
        enums.append(("ToolKind", "u32", [(m["name"], model.eval_value(m["value"])) for m in vocab["tool_kind"]]))

    # --- structs ------------------------------------------------------------
    structs = []  # (name, [(fname, ctype, offset, size)], total, max)

    struct_table = {}  # name -> (size, align)
    for name, fields, exact, mx in model.CONTAINER:
        if fields is None:
            continue
        parsed = [(fn, ft) for fn, ft in fields]
        offs, sz, al = _layout(parsed, struct_table)
        struct_table[name] = (sz, al)
        flds = [(fn, ft, offs[fn], _type_size_align(ft, struct_table)[0]) for fn, ft in parsed]
        structs.append((name, flds, sz, mx))

    def add_struct(name, parsed):
        offs, sz, al = _layout(parsed, struct_table)
        struct_table[name] = (sz, al)
        flds = [(fn, ft, offs[fn], _type_size_align(ft, struct_table)[0]) for fn, ft in parsed]
        structs.append((name, flds, sz, None))

    # Header (fixed neutral)
    hparsed = model.parse_field_lines([
        "std::uint32_t magic;", "std::uint32_t version;",
        f"std::uint32_t {prefix}Pid;", "std::uint32_t mcPid;",
        f"std::uint64_t {prefix}HeartbeatMs;", "std::uint64_t mcHeartbeatMs;"])
    add_struct("Header", hparsed)

    # HostState
    hs = vocab["host_state"]
    add_struct(f"{abbr}State", model.parse_field_lines(hs["fields"]))

    # McState
    ms = vocab["mc_state"]
    add_struct("McState", model.parse_field_lines(ms["fields"]))

    return {
        "abbr": abbr, "prefix": prefix,
        "namespace": vocab["namespace"],
        "scalars": scalars, "enums": enums, "structs": structs,
        "host_state_size": hs["size"], "mc_state_size": ms["size"],
        "ground_grid": hs.get("ground_grid"),
    }
