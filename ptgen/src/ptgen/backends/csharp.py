"""backends/csharp.py — schema -> C# protocol (structs with explicit layout).

Structs use [StructLayout(LayoutKind.Sequential)] (natural alignment, matching C++),
arrays use [MarshalAs(UnmanagedType.ByValArray, SizeConst=...)] so they are inlined
and Marshal.SizeOf equals the C++ sizeof. A CheckLayout() asserts every size; this is
the self-consistency proof (no MIT reference exists for C#: structural comparison only,
not byte-verified). NOT compiled here (no C# toolchain) -> marked 推断 / 未验证.
"""
import re
from .. import plan as _plan


_CS = {'u32': 'uint', 'i32': 'int', 'u64': 'ulong', 'i64': 'long',
       'f32': 'float', 'f64': 'double', 'u16': 'ushort', 'u8': 'byte'}


def _cs_type(tok, struct_names):
    if isinstance(tok, str):
        if tok in _CS:
            return _CS[tok]
        if tok in struct_names:
            return tok
        return tok
    if isinstance(tok, tuple):
        if tok[0] == 'bytes':
            return f"byte[{tok[1]}]"
        if tok[0] == 'arr':
            return _cs_type(tok[1], struct_names)
    raise TypeError(tok)


def _cs_field_decl(fn, tok, struct_names):
    if isinstance(tok, tuple) and tok[0] == 'arr':
        inner = _cs_type(tok[1], struct_names)
        return f"    [MarshalAs(UnmanagedType.ByValArray, SizeConst={tok[2]})] public {inner}[] {fn};"
    if isinstance(tok, tuple) and tok[0] == 'bytes':
        return f"    [MarshalAs(UnmanagedType.ByValArray, SizeConst={tok[1]})] public byte[] {fn};"
    return f"    public {_cs_type(tok, struct_names)} {fn};"


def generate(schema, vocab):
    p = _plan.build_plan(schema, vocab)
    abbr = p["abbr"]
    ns = p["namespace"].replace("::", ".")
    struct_names = {n for n, *_ in p["structs"]}
    L = []
    L.append("using System;")
    L.append("using System.Runtime.InteropServices;")
    L.append("")
    L.append(f"namespace {ns}")
    L.append("{")
    L.append("    // Generated passthrough protocol (schema.yaml + vocabulary).")
    L.append("    // Structs are LayoutKind.Sequential (natural alignment, ABI-equivalent to C++).")
    L.append("    public static class Proto")
    L.append("    {")
    L.append(f"        public const uint Magic = {p['scalars'][0][1]};")
    L.append(f"        public const uint Version = {p['scalars'][1][1]};")
    L.append(f'        public const string MappingName = "{_plan.c_escape(p["scalars"][2][1])}";')
    L.append(f"        public const double UnitsPerBlock = {p['scalars'][3][1]};")
    for name, val, kind in p["scalars"][4:]:
        if kind == "long":
            L.append(f"        public const long {name} = {val}L;")
        elif kind == "double":
            L.append(f"        public const double {name} = {val};")
        else:
            L.append(f"        public const int {name} = {val};")
    L.append("")

    # enums
    flags_enums = {f"{abbr}Flags", "McFlags", "ColTriFlags"}
    for ename, under, members in p["enums"]:
        cs_under = _CS.get(under, "uint")
        tag = "[Flags]\n    " if ename in flags_enums else ""
        L.append(f"    {tag}public enum {ename} : {cs_under}")
        L.append("    {")
        last = len(members) - 1
        for i, (mname, val) in enumerate(members):
            comma = "," if i < last else ""
            if val is None:
                L.append(f"        {mname}{comma}")
            else:
                L.append(f"        {mname} = {val}{comma}")
        L.append("    }")
        L.append("")

    # structs
    for sname, flds, tot, mx in p["structs"]:
        L.append(f"    [StructLayout(LayoutKind.Sequential)]")
        L.append(f"    public struct {sname}")
        L.append("    {")
        for fn, tok, off, sz in flds:
            L.append(_cs_field_decl(fn, tok, struct_names))
        L.append("    }")
        L.append("")

    # layout self-check (call Proto.CheckLayout() once at startup)
    L.append("    public static void CheckLayout()")
    L.append("    {")
    for sname, flds, tot, mx in p["structs"]:
        # assert the ACTUAL struct size (== C++ sizeof); `mx`, where present, is a
        # C++ upper-bound contract (WaterGrid: sizeof <= 0xC00) and is not the sizeof.
        L.append(f"        if (Marshal.SizeOf<{sname}>() != {tot}) throw new Exception(\"size mismatch {sname}\");")
    L.append("    }")
    L.append("}")
    L.append("}")
    out = "\n".join(L) + "\n"

    # companion: seqlock / SPSC skeleton (C# style)
    sync = (
        "using System;\nusing System.Runtime.InteropServices;\n"
        f"namespace {ns}\n{{\n"
        "    public static class Sync\n    {\n"
        "        // seqlock read over a pinned byte[] base at byte offset seqOff.\n"
        "        public static bool SeqlockRead(byte[] buf, int seqOff)\n"
        "        {\n"
        "            int s0 = BitConverter.ToInt32(buf, seqOff);\n"
        "            if ((s0 & 1) != 0) return false;\n"
        "            int s1 = BitConverter.ToInt32(buf, seqOff);\n"
        "            return s0 == s1;\n"
        "        }\n"
        "        public static void RingProduce(byte[] buf, int headOff, int dataOff, int dataBytes, byte[] payload)\n"
        "        {\n"
        "            long head = BitConverter.ToInt64(buf, headOff);\n"
        "            int pos = (int)(head & (dataBytes - 1));\n"
        "            Array.Copy(payload, 0, buf, dataOff + pos, payload.Length);\n"
        "            head += payload.Length;\n"
        "            Array.Copy(BitConverter.GetBytes(head), 0, buf, headOff, 8);\n"
        "        }\n"
        "    }\n}\n"
    )
    return out, sync
