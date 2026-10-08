"""backends/java.py — schema -> Java protocol constants (mirrors SkyCraft's Proto.java).

Java has no value types, so we emit a final class of offset/size constants and enum
values, exactly as Proto.java does, plus seqlock/SPSC helper skeletons. Field offsets
come from plan.build_plan (ctypes-computed, ABI-equivalent to the C++ layout).
No MIT code is copied: this is generated from schema.yaml + the vocabulary.
"""
import re


def _hex(v):
    return "0x%x" % v


def _const_name(k):
    # kOffHeader -> OFF_HEADER ; kCollisionRingBytes -> COLLISION_RING_BYTES
    s = k[1:] if k.startswith("k") else k
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).upper()


def _upper_camel(field):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", field).upper()


def _fmt_int(v):
    return _hex(v) if v >= 0x100 or v < 0 else str(v)


def generate(schema, vocab):
    from .. import plan
    p = plan.build_plan(schema, vocab)
    abbr = p["abbr"]
    prefix = p["prefix"]
    ns = p["namespace"]
    java_pkg = ns.replace("::", ".")
    L = []
    L.append(f"package {java_pkg};")
    L.append("")
    L.append("/**")
    L.append(" * Generated passthrough protocol constants (schema.yaml + vocabulary).")
    L.append(" * Field offsets are ABI-equivalent to the C++ fixed blocks; all multi-byte values little-endian.")
    L.append(" */")
    L.append("public final class Proto {")
    L.append("\tprivate Proto() {}")
    L.append("")
    L.append(f"\tpublic static final int MAGIC = {_fmt_int(p['scalars'][0][1])};")
    L.append(f"\tpublic static final int VERSION = {p['scalars'][1][1]};")
    L.append(f'\tpublic static final String MAPPING_NAME = "{plan.c_escape(p["scalars"][2][1])}";')
    L.append(f"\tpublic static final double UNITS_PER_BLOCK = {p['scalars'][3][1]};")
    L.append("")

    # region / ring offset constants
    for name, val, kind in p["scalars"][4:]:
        if name in ("kOffHeader", "kOffSkyState", "kOffValState", "kOffMcState",
                    "kOffOverlayCtl", "kOffOverlaySlotHdr", "kOffWaterGrid",
                    "kOffInputRing", "kOffCollisionRing", "kOffOverlayPixels",
                    "kMaxOverlayW", "kMaxOverlayH", "kOverlaySlotBytes", "kOverlaySlots",
                    "kOffActorTable", "kOffEventRing", "kOffWorldEntities", "kOffRenderRing",
                    "kMappingBytes", "kCollisionRingBytes", "kRenderRingBytes",
                    "kWaterGridSize", "kNoWater", "kMaxActors", "kMaxWorldEntities",
                    "kOverlayDirty", "kInputRingEntries", "kEventRingEntries",
                    "kInputRingHeadOff", "kInputRingTailOff", "kInputRingDataOff",
                    "kEventRingHeadOff", "kEventRingTailOff", "kEventRingDataOff",
                    "kColRingHeadOff", "kColRingTailOff", "kColRingDataOff", "kColRingDataBytes",
                    "kRenRingHeadOff", "kRenRingTailOff", "kRenRingDataOff", "kRenRingDataBytes"):
            cn = _const_name(name)
            if kind == "long":
                L.append(f"\tpublic static final long {cn} = {_hex(val)}L;")
            elif kind == "double":
                L.append(f"\tpublic static final double {cn} = {val};")
            else:
                L.append(f"\tpublic static final int {cn} = {_fmt_int(int(val))};")
    L.append("")

    # struct size + per-field offset constants for every struct (mirrors Proto.java,
    # which lays out H_/SS_/MS_/AT_/ER_/WE_/RR_/CR_ offset words by hand).
    for name, flds, tot, mx in p["structs"]:
        L.append(f"\tpublic static final long {name.upper()}_BYTES = {_hex(tot)}L;")
        for fn, ct, off, sz in flds:
            L.append(f"\tpublic static final long {name.upper()}_{_upper_camel(fn)} = {_hex(off)}L;")
        L.append("")
    if p["ground_grid"] is not None:
        L.append(f"\tpublic static final int kGroundGrid = {p['ground_grid']};")
        L.append("")

    # enums
    for ename, under, members in p["enums"]:
        for mname, val in members:
            if val is None:
                continue
            L.append(f"\tpublic static final int {mname} = {_fmt_int(val)};")
    L.append("")

    # seqlock / SPSC skeletons (extra vs Proto.java; reported in the diff)
    L.append("\t// seqlock read: even, stable seq; returns false while a writer is mid-update.")
    L.append("\tpublic static boolean seqlockRead(java.nio.ByteBuffer buf, long seqOff) {")
    L.append("\t\tint s0 = buf.getInt((int) seqOff);")
    L.append("\t\tif ((s0 & 1) != 0) return false;")
    L.append("\t\tint s1 = buf.getInt((int) seqOff);")
    L.append("\t\treturn s0 == s1;")
    L.append("\t}")
    L.append("")
    L.append("\t// SPSC ring: power-of-two data region; head/tail are u64 at headOff/tailOff.")
    L.append("\tpublic static int ringProduce(java.nio.ByteBuffer buf, long headOff,")
    L.append("\t\t\tlong dataOff, long dataBytes, byte[] payload) {")
    L.append("\t\tlong head = buf.getLong((int) headOff);")
    L.append("\t\tlong pos = head & (dataBytes - 1);")
    L.append("\t\tbuf.position((int) (dataOff + pos));")
    L.append("\t\tbuf.put(payload);")
    L.append("\t\tbuf.putLong((int) headOff, head + payload.length);")
    L.append("\t\treturn payload.length;")
    L.append("\t}")
    L.append("}")
    out = "\n".join(L) + "\n"
    return out, None
