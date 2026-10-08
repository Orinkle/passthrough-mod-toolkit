"""backends/python.py — schema -> Python ctypes protocol module.

This is what the fake host/guest stubs import. The layouts are generated from schema.yaml
(via the ABI model), so the Python side shares the EXACT byte layout of the C++/C#/Rust
headers. There are NO hand-written offsets: every struct, offset and region constant below
comes from the model, which is ctypes-verified to match the C++ static_assert sizes.
This is the concrete proof that "schema is the single source of truth".

Emits, in order: scalar constants, an OFFSETS table (per struct, per field), enums,
ctypes.Structure classes (field order == C++), and seqlock/SPSC skeletons.
"""
import ctypes
from .. import plan as _plan, model as _model


_CT = {'u32': 'ctypes.c_uint32', 'i32': 'ctypes.c_int32', 'u64': 'ctypes.c_uint64',
       'i64': 'ctypes.c_int64', 'f32': 'ctypes.c_float', 'f64': 'ctypes.c_double',
       'u16': 'ctypes.c_uint16', 'u8': 'ctypes.c_uint8'}


def _py_type(tok, struct_names):
    if isinstance(tok, str):
        return _CT.get(tok, tok)
    if isinstance(tok, tuple):
        if tok[0] == 'bytes':
            return f"ctypes.c_uint8 * {tok[1]}"
        if tok[0] == 'arr':
            return f"{_py_type(tok[1], struct_names)} * {tok[2]}"
    raise TypeError(tok)


def _dedupe_scalars(pairs):
    seen = {}
    order = []
    for name, val, kind in pairs:
        if name not in seen:
            order.append(name)
        seen[name] = (val, kind)
    return [(n, seen[n][0], seen[n][1]) for n in order]


def generate(schema, vocab):
    p = _plan.build_plan(schema, vocab)
    abbr = p["abbr"]
    struct_names = {n for n, *_ in p["structs"]}
    scalars = _dedupe_scalars(p["scalars"])
    L = []
    L.append('"""Protocol bindings generated from schema.yaml (host: %s). Do not edit by hand."""' % abbr)
    L.append("import ctypes")
    L.append("")
    L.append("# ---- scalar constants ----")
    L.append(f"MAGIC = {scalars[0][1]}")
    L.append(f"VERSION = {scalars[1][1]}")
    L.append(f"MAPPING_NAME = {scalars[2][1]!r}  # escaped for Python")
    L.append(f"UNITS_PER_BLOCK = {scalars[3][1]}")
    for name, val, kind in scalars[4:]:
        L.append(f"{name} = {val}")
    L.append("")
    L.append("# ---- enums ----")
    for ename, under, members in p["enums"]:
        for mname, val in members:
            if val is None:
                continue
            L.append(f"{mname} = {val}")
    L.append("")
    L.append("# ---- struct offsets + sizes (bytes; ABI-equivalent to the C++ header) ----")
    L.append("OFFSETS = {")
    for sname, flds, tot, mx in p["structs"]:
        L.append(f"    {sname!r}: {{")
        for fn, tok, off, sz in flds:
            L.append(f"        {fn!r}: {off},")
        L.append("    },")
    L.append("}")
    L.append("SIZES = {")
    for sname, flds, tot, mx in p["structs"]:
        L.append(f"    {sname!r}: {tot},")
    L.append("}")
    L.append("")

    # forward-declare struct name list so nested arrays resolve
    for sname, flds, tot, mx in p["structs"]:
        L.append(f"class {sname}(ctypes.Structure):")
        L.append("    _fields_ = [")
        for fn, tok, off, sz in flds:
            L.append(f"        ({fn!r}, {_py_type(tok, struct_names)}),")
        L.append("    ]")
        L.append(f"{sname}.SIZE = {tot}  # verified == C++ static_assert")
        L.append("")

    L.append("MAPPING_BYTES = kMappingBytes")
    L.append("")
    L.append("# ---- region base offsets (in the shared mapping) ----")
    L.append("REGIONS = {")
    for name, val, kind in scalars[4:]:
        if name.startswith(("kOff", "kInputRing", "kEventRing", "kColRing", "kRenRing", "kMax", "kCollision")):
            L.append(f"    {name!r}: {val},")
    L.append("}")
    L.append("")
    L.append("def sizeof_struct(name):")
    L.append("    return globals()[name].SIZE")
    L.append("")
    L.append("def offsetof(struct_type, field):")
    L.append("    return getattr(struct_type, field).offset")
    L.append("")
    L.append("# ---- seqlock skeleton (u32 seq at base+0, struct body at base+8) ----")
    L.append("def seqlock_read(base_addr, struct_type):")
    L.append('    """Return a live view of struct_type at base_addr+8, or None if a writer is mid-update."""')
    L.append("    seq_p = ctypes.cast(base_addr, ctypes.POINTER(ctypes.c_uint32))")
    L.append("    for _ in range(1 << 20):")
    L.append("        s0 = seq_p[0]")
    L.append("        if s0 & 1:")
    L.append("            continue  # writer mid-update")
    L.append("        out = struct_type.from_address(base_addr + 8)")
    L.append("        if seq_p[0] == s0:")
    L.append("            return out  # even and stable")
    L.append("    return None")
    L.append("")
    L.append("def seqlock_write(base_addr, struct_type, value):")
    L.append('    """Publish value into struct_type at base_addr+8 under the odd/even seq protocol."""')
    L.append("    seq_p = ctypes.cast(base_addr, ctypes.POINTER(ctypes.c_uint32))")
    L.append("    seq_p[0] += 1  # -> odd (writer active)")
    L.append("    ctypes.memmove(base_addr + 8, ctypes.byref(value), ctypes.sizeof(struct_type))")
    L.append("    seq_p[0] += 1  # -> even (stable)")
    L.append("")
    L.append("# ---- SPSC ring skeleton (power-of-two data region) ----")
    L.append("def ring_produce(base_addr, head_off, data_off, data_bytes, payload):")
    L.append("    head_p = ctypes.cast(base_addr + head_off, ctypes.POINTER(ctypes.c_uint64))")
    L.append("    head = head_p[0]")
    L.append("    mask = data_bytes - 1")
    L.append("    if (head & mask) + len(payload) > data_bytes:")
    L.append("        return False  # no room (simple bound)")
    L.append("    ctypes.memmove(base_addr + data_off + (head & mask), payload, len(payload))")
    L.append("    head_p[0] = head + len(payload)")
    L.append("    return True")
    L.append("")
    L.append("def ring_consume(base_addr, tail_off, head_off, data_off, data_bytes, n):")
    L.append("    tail_p = ctypes.cast(base_addr + tail_off, ctypes.POINTER(ctypes.c_uint64))")
    L.append("    head_p = ctypes.cast(base_addr + head_off, ctypes.POINTER(ctypes.c_uint64))")
    L.append("    tail, head = tail_p[0], head_p[0]")
    L.append("    if tail + n > head:")
    L.append("        return None")
    L.append("    mask = data_bytes - 1")
    L.append("    buf = ctypes.create_string_buffer(n)")
    L.append("    ctypes.memmove(buf, base_addr + data_off + (tail & mask), n)")
    L.append("    tail_p[0] = tail + n")
    L.append("    return buf.raw")
    out = "\n".join(L) + "\n"
    return out, None
