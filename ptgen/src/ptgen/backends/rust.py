"""backends/rust.py — schema -> Rust protocol (#[repr(C)] structs).

No MIT Rust reference exists (EldenKill is unlicensed); this is written from language
convention and the ABI model. Structs use #[repr(C)] (natural alignment, matching C++),
and each carries a compile-time `assert!(size_of::<T>() == N)` so a Rust build FAILS if
the layout drifts. Rust identifiers that collide with a keyword (e.g. the wire field
`type`) are emitted as raw identifiers (`r#type`) so the field name/layout is preserved.
"""
from .. import plan as _plan

_RS = {'u32': 'u32', 'i32': 'i32', 'u64': 'u64', 'i64': 'i64',
       'f32': 'f32', 'f64': 'f64', 'u16': 'u16', 'u8': 'u8'}

# Rust 2015/2018/2021 keywords that can legally appear as C wire-field names.
_KEYWORDS = {
    "as", "break", "const", "continue", "crate", "dyn", "else", "enum", "extern",
    "false", "fn", "for", "if", "impl", "in", "let", "loop", "match", "mod", "move",
    "mut", "pub", "ref", "return", "self", "Self", "static", "struct", "super",
    "trait", "true", "type", "unsafe", "use", "where", "while", "async", "await",
    "abstract", "become", "box", "do", "final", "macro", "override", "priv",
    "try", "typeof", "unsized", "virtual", "yield",
}


def rs_ident(name):
    """Return a Rust identifier for a wire field name (raw ident on keyword clash)."""
    return f"r#{name}" if name in _KEYWORDS else name


def _rs_type(tok, struct_names):
    if isinstance(tok, str):
        return _RS.get(tok, tok)
    if isinstance(tok, tuple):
        if tok[0] == 'bytes':
            return f"[u8; {tok[1]}]"
        if tok[0] == 'arr':
            return f"[{_rs_type(tok[1], struct_names)}; {tok[2]}]"
    raise TypeError(tok)


def generate(schema, vocab):
    p = _plan.build_plan(schema, vocab)
    abbr = p["abbr"]
    struct_names = {n for n, *_ in p["structs"]}
    L = []
    L.append("// Generated passthrough protocol (schema.yaml + vocabulary).")
    L.append("// #[repr(C)] structs; multi-byte values are little-endian.")
    L.append("// Field names mirror the C++ header even when they are Rust keywords (raw idents).")
    L.append("#![allow(non_upper_case_globals, non_camel_case_types, non_snake_case)]")
    L.append("")
    L.append(f"pub const MAGIC: u32 = {p['scalars'][0][1]};")
    L.append(f"pub const VERSION: u32 = {p['scalars'][1][1]};")
    L.append(f'pub const MAPPING_NAME: &str = "{_plan.c_escape(p["scalars"][2][1])}";')
    L.append(f"pub const UNITS_PER_BLOCK: f64 = {p['scalars'][3][1]};")
    for name, val, kind in p["scalars"][4:]:
        if kind == "long":
            L.append(f"pub const {name}: u64 = {val};")
        elif kind == "double":
            L.append(f"pub const {name}: f64 = {val};")
        else:
            L.append(f"pub const {name}: i32 = {val};")
    L.append("")

    # enums as const blocks
    for ename, under, members in p["enums"]:
        rs_under = _RS.get(under, "u32")
        L.append(f"pub mod {ename.lower()} {{")
        for mname, val in members:
            if val is None:
                continue
            L.append(f"    pub const {mname}: {rs_under} = {val};")
        L.append("}")
        L.append("")

    # structs
    for sname, flds, tot, mx in p["structs"]:
        L.append("#[repr(C)]")
        L.append(f"#[derive(Clone, Copy)]")
        L.append(f"pub struct {sname} {{")
        for fn, tok, off, sz in flds:
            rs_t = _rs_type(tok, struct_names)
            L.append(f"    pub {rs_ident(fn)}: {rs_t},")
        L.append("}")
        # assert the ACTUAL struct size (== C++ sizeof). `mx` (WaterGrid <= 0xC00) is a
        # C++ upper-bound contract, not a sizeof, so it is not used for equality here.
        L.append(f"const _: () = assert!(std::mem::size_of::<{sname}>() == {tot});")
        if mx is not None:
            L.append(f"const _: () = assert!(std::mem::size_of::<{sname}>() <= {mx});")
        L.append("")

    # seqlock / SPSC skeleton
    L.append("// seqlock + SPSC helpers over a &[u8] mapping (offsets from this module).")
    L.append("pub fn seqlock_even(seq: u32) -> bool { seq & 1 == 0 }")
    L.append("pub fn ring_produce(head: u64, data_bytes: u64, n: u64) -> Option<(u64, u64)> {")
    L.append("    let mask = data_bytes - 1;")
    L.append("    if (head & mask) + n > data_bytes { None } else { Some((head & mask, head + n)) }")
    L.append("}")
    out = "\n".join(L) + "\n"
    return out, None
