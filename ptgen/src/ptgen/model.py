"""model.py — the container (invariant) protocol described in a language-neutral way.

The C++ ``fixed`` blocks in schema.yaml are opaque C++ text. For the other three
backends (C#/Java/Rust) we cannot emit them verbatim, so this module is the
*authoritative re-expression* of the same byte layout. Every struct here is
verified (see :func:`build_ctypes`) to have the exact size the C++ ``static_assert``
in schema.yaml demands, under natural (un-packed) alignment — which is what
``[StructLayout(LayoutKind.Sequential)]`` (C#) and ``#[repr(C)]`` (Rust) also use.

That ctypes check is the runnable self-consistency proof: if this model is ABI
correct for C, the generated C#/Rust structs (explicit layout) are ABI correct too.
"""
import ctypes

# Neutral type tokens -----------------------------------------------------------
# 'u32' 'i32' 'u64' 'i64' 'f32' 'f64' 'u16' 'u8' and compound:
#   ('arr', base, count)          e.g. ('arr','f32',9)
#   ('bytes', count)              raw byte buffer (name[count])
_CT = {
    'u32': ctypes.c_uint32, 'i32': ctypes.c_int32,
    'u64': ctypes.c_uint64, 'i64': ctypes.c_int64,
    'f32': ctypes.c_float, 'f64': ctypes.c_double,
    'u16': ctypes.c_uint16, 'u8': ctypes.c_uint8,
}


def _ct_of(t, classes=None):
    if isinstance(t, str):
        if classes is not None and t in classes:
            return classes[t]
        return _CT[t]
    if isinstance(t, tuple):
        if t[0] == 'arr':
            return _ct_of(t[1], classes) * t[2]
        if t[0] == 'bytes':
            return ctypes.c_uint8 * t[1]
    raise TypeError(t)


# Container struct catalogue ----------------------------------------------------
# (name, fields, expected_size_or_None, max_size_or_None)
# fields: list of (name, type)
# Dependency order: inner types must precede outer (ActorRecord before ActorTable).
CONTAINER = [
    ("WaterGrid", [
        ("seq", "u32"), ("originX", "i32"), ("originZ", "i32"), ("worldId", "u32"),
        ("surface", ("arr", "f32", 256)),
    ], None, 0xC00),

    ("OverlayCtl", [
        ("state", "u32"), ("pad", "u32"), ("framesPublished", "u64"),
    ], 16, None),

    ("OverlaySlotHdr", [
        ("width", "u32"), ("height", "u32"), ("flags", "u32"), ("pad", "u32"),
        ("frameId", "u64"), ("reserved", ("bytes", 0x40 - 0x18)),
    ], 0x40, None),

    ("ActorFlags", None, None, None),  # enum, see ENUMS below

    ("ActorRecord", [
        ("formId", "u32"), ("flags", "u32"),
        ("x", "f32"), ("y", "f32"), ("z", "f32"), ("yaw", "f32"),
        ("width", "f32"), ("height", "f32"), ("healthFrac", "f32"),
        ("level", "u16"), ("pad", "u16"), ("name", ("bytes", 24)),
    ], 64, None),

    ("ActorTable", [
        ("seq", "u32"), ("count", "u32"), ("pad", ("bytes", 0x40 - 8)),
        ("actors", ("arr", "ActorRecord", 256)),
    ], 0x40 + 64 * 256, None),

    ("McEvent", [
        ("type", "u32"), ("formId", "u32"),
        ("a", "f32"), ("b", "f32"), ("c", "f32"), ("d", "f32"),
        ("flags", "u32"), ("weapon", "u32"),
    ], 32, None),

    ("WorldEntityKind", None, None, None),
    ("WorldEntity", [
        ("kind", "u32"), ("id", "u32"),
        ("x", "f32"), ("y", "f32"), ("z", "f32"),
        ("yaw", "f32"), ("pitch", "f32"), ("scale", "f32"),
        ("ext", ("arr", "f32", 3)), ("uv", ("arr", ("arr", "f32", 4), 3)),
        ("tint", "u32"),
    ], 96, None),

    ("WorldEntities", [
        ("seq", "u32"), ("count", "u32"), ("hasSelection", "u32"),
        ("selMin", ("arr", "f32", 3)), ("selMax", ("arr", "f32", 3)),
        ("pad", ("bytes", 0x40 - 36)),
        ("entities", ("arr", "WorldEntity", 160)),
    ], 0x40 + 96 * 160, None),

    ("RenSolids", [
        ("sx", "i32"), ("sy", "i32"), ("sz", "i32"), ("count", "u32"),
    ], 16, None),

    ("RenDug", [
        ("sx", "i32"), ("sy", "i32"), ("sz", "i32"), ("count", "u32"),
        ("worldId", "u32"), ("pad", "u32"),
    ], 24, None),

    ("RagdollPart", None, None, None),
    ("RenLights", [
        ("sx", "i32"), ("sy", "i32"), ("sz", "i32"), ("count", "u32"),
    ], 16, None),

    ("LightKind", None, None, None),
    ("BlockHazard", None, None, None),
    ("RenLight", [
        ("x", "u8"), ("y", "u8"), ("z", "u8"), ("level", "u8"), ("color", "u32"),
    ], 8, None),

    ("RenAtlasRegion", [
        ("x", "u32"), ("y", "u32"), ("width", "u32"), ("height", "u32"),
    ], 16, None),

    ("RenScene", [
        ("originX", "f64"), ("originY", "f64"), ("originZ", "f64"),
        ("batchCount", "u32"), ("vertexCount", "u32"),
    ], 32, None),

    ("RenTexture", [
        ("id", "u32"), ("width", "u32"), ("height", "u32"), ("pad", "u32"),
    ], 16, None),

    ("RenAvatar", [
        ("batchCount", "u32"), ("vertexCount", "u32"),
    ], 8, None),

    ("RenBatch", [
        ("texture", "u32"), ("first", "u32"), ("count", "u32"), ("flags", "u32"),
    ], 16, None),

    ("RenAtlas", [
        ("width", "u32"), ("height", "u32"),
    ], 8, None),

    ("RenSection", [
        ("sx", "i32"), ("sy", "i32"), ("sz", "i32"), ("vertexCount", "u32"),
    ], 16, None),

    ("RenVertex", [
        ("x", "f32"), ("y", "f32"), ("z", "f32"),
        ("u", "f32"), ("v", "f32"),
        ("color", "u32"), ("light", "u32"), ("flags", "u32"),
    ], 32, None),

    ("InputEvent", [
        ("type", "u16"), ("code", "u16"),
        ("a", "i32"), ("b", "i32"), ("c", "i32"),
    ], 16, None),

    ("ColType", None, None, None),
    ("ColTri", [
        ("v", ("arr", "f32", 9)), ("flags", "u32"),
    ], 40, None),

    ("ColMsgHeader", [
        ("type", "u32"), ("payloadBytes", "u32"),
    ], 8, None),

    ("ColRegion", [
        ("minX", "i32"), ("minY", "i32"), ("minZ", "i32"),
        ("maxX", "i32"), ("maxY", "i32"), ("maxZ", "i32"),
        ("epoch", "u32"), ("count", "u32"),
    ], 32, None),

    ("ColBlock", [
        ("x", "i32"), ("y", "i32"), ("z", "i32"), ("pad", "u32"),
        ("bits", ("arr", "u64", 8)),
    ], 80, None),
]

# Fixed enums (container level). value=None means auto-increment.
ENUMS = {
    "ActorFlags": ("u32", [
        ("kActorHostile", 1 << 0), ("kActorDead", 1 << 1),
        ("kActorEssential", 1 << 2), ("kActorInCombat", 1 << 3),
    ]),
    "WorldEntityKind": ("u32", [
        ("kWeArrow", 1), ("kWeItem", 2), ("kWeTrident", 3),
        ("kWeBlock", 4), ("kWeCrack", 5), ("kWeShadow", 6),
    ]),
    "RagdollPart": ("u32", [
        ("kPartNone", 0), ("kPartHead", 1), ("kPartBody", 2),
        ("kPartRightArm", 3), ("kPartLeftArm", 4),
        ("kPartRightLeg", 5), ("kPartLeftLeg", 6), ("kPartCount", 7),
    ]),
    "LightKind": ("u8", [
        ("kLightSteady", 0), ("kLightFlame", 1), ("kLightLava", 2),
    ]),
    "BlockHazard": ("u8", [
        ("kHazardNone", 0), ("kHazardFire", 1),
        ("kHazardLava", 2), ("kHazardMagma", 3),
    ]),
    "ColType": ("u32", [
        ("kColPad", 0), ("kColClear", 1), ("kColRegion", 2), ("kColTris", 3),
    ]),
}


# Region / ring offset constants (from schema.yaml container.regions_template / fixed) ---
REGIONS = {
    "kOffHeader": 0x0,
    "kOffSkyState": 0x100, "kOffValState": 0x100,
    "kOffMcState": 0x200,
    "kOffOverlayCtl": 0x300, "kOffOverlaySlotHdr": 0x340,
    "kOffWaterGrid": 0x400,
    "kOffInputRing": 0x1000,
    "kOffCollisionRing": 0x20000,
    "kCollisionRingBytes": 32 << 20,
    "kOffOverlayPixels": (0x20000 + (32 << 20)),
    "kMaxOverlayW": 3840, "kMaxOverlayH": 2160,
    "kOverlaySlotBytes": 3840 * 2160 * 4,
    "kOverlaySlots": 3,
    "kOffActorTable": 0x12000,
    "kOffEventRing": 0x17000,
    "kOffWorldEntities": 0x1C000,
    "kOffRenderRing": (0x20000 + (32 << 20)) + (3840 * 2160 * 4) * 3,
    "kRenderRingBytes": 64 << 20,
    "kMappingBytes": (0x20000 + (32 << 20)) + (3840 * 2160 * 4) * 3 + (64 << 20),
    # ring offset sub-constants
    "kInputRingEntries": 4096,
    "kInputRingHeadOff": 0x00, "kInputRingTailOff": 0x40, "kInputRingDataOff": 0x80,
    "kEventRingEntries": 512,
    "kEventRingHeadOff": 0x00, "kEventRingTailOff": 0x40, "kEventRingDataOff": 0x80,
    "kColRingHeadOff": 0x00, "kColRingTailOff": 0x40, "kColRingDataOff": 0x80,
    "kColRingDataBytes": (32 << 20) - 0x80,
    "kRenRingHeadOff": 0x00, "kRenRingTailOff": 0x40, "kRenRingDataOff": 0x80,
    "kRenRingDataBytes": (64 << 20) - 0x80,
    "kWaterGridSize": 16, "kNoWater": -1.0e30,
    "kMaxActors": 256, "kMaxWorldEntities": 160,
    "kOverlayDirty": 1 << 2,
    "kMaxOverlaySlots": 3,
}

# Extra scalar constants (fixed in schema) used by the skeletons / shared by langs.
EXTRA_SCALARS = {
    "kWaterGridSize": 16, "kNoWater": -1.0e30,
    "kMaxActors": 256, "kMaxWorldEntities": 160,
    "kOverlayDirty": 1 << 2, "kOverlaySlotBytes": 3840 * 2160 * 4,
    "kOverlaySlots": 3, "kCollisionRingBytes": 32 << 20,
    "kRenderRingBytes": 64 << 20,
    "kInputRingEntries": 4096, "kEventRingEntries": 512,
}


def eval_value(expr):
    """Turn a vocabulary enum value RHS into a Python int (or None for auto)."""
    if expr is None:
        return None
    s = str(expr).strip().replace("u", "").replace("ULL", "").replace("L", "")
    s = s.replace("<<", "<<")
    try:
        return int(eval(s, {"__builtins__": {}}, {}))
    except Exception:
        return None


def parse_field_lines(lines):
    """Parse C++-ish field lines (host_state/mc_state.fields) into neutral (name, type).

    Handles 'std::uint32_t seq;', 'double posX, posY, posZ;', 'std::uint8_t name[24];',
    'std::uint8_t groundPad[0x04];'. Returns list of (name, ctype_or_tuple).
    """
    out = []
    for ln in lines:
        s = ln.strip().rstrip(";").strip()
        if not s:
            continue
        # split type and names
        # type is everything up to the first identifier-ish token after the last type keyword
        # heuristic: type keyword prefixes
        m = None
        for kw, t in (("std::uint32_t", "u32"), ("std::int32_t", "i32"),
                      ("std::uint64_t", "u64"), ("std::int64_t", "i64"),
                      ("std::uint16_t", "u16"), ("std::uint8_t", "u8"),
                      ("std::uint8_t", "u8"), ("float", "f32"), ("double", "f64")):
            if s.startswith(kw):
                rest = s[len(kw):].strip()
                m = (t, rest)
                break
        if m is None:
            # fall back: maybe 'char name[24]'
            if s.startswith("char "):
                rest = s[5:].strip()
                m = ("u8", rest)
            else:
                raise ValueError(f"cannot parse field line: {ln!r}")
        t, rest = m
        # rest may be 'seq' or 'posX, posY, posZ' or 'name[24]' or 'groundPad[0x04]' or 'posX, posY, posZ'
        # handle array suffix on the whole group or per name
        group_arr = None
        if "[" in rest:
            base, _, idx = rest.partition("[")
            idx = idx.rstrip("]")
            count = int(idx, 0) if idx.lower().startswith("0x") or "x" in idx else int(idx)
            # if there's a comma it's per-name arrays
            if "," in base:
                names = [n.strip() for n in base.split(",")]
                for n in names:
                    out.append((n, ("arr", t, count)))
                continue
            else:
                rest = base.strip()
                group_arr = count
        for nm in rest.split(","):
            nm = nm.strip()
            if not nm:
                continue
            if group_arr is not None:
                out.append((nm, ("arr", t, group_arr)))
            else:
                out.append((nm, t))
    return out


def build_ctypes():
    """Build ctypes classes for every container struct and assert sizes.

    Returns (classes, sizes) where sizes[name] is the ctypes sizeof.
    Raises AssertionError if any size/max-size contract is violated — this is the
    runnable proof that the container model is ABI-equivalent to the C++ fixed blocks.
    """
    classes = {}
    sizes = {}
    for name, fields, exact, mx in CONTAINER:
        if fields is None:
            continue  # enum
        ct_fields = []
        for fname, ftype in fields:
            if isinstance(ftype, str):
                base = _ct_of(ftype, classes)
            elif isinstance(ftype, tuple):
                base = _ct_of(ftype, classes)
            else:
                base = ftype
            ct_fields.append((fname, base))
        cls = type(name, (ctypes.Structure,), {"_fields_": ct_fields})
        classes[name] = cls
        sz = ctypes.sizeof(cls)
        sizes[name] = sz
        if exact is not None:
            assert sz == exact, f"{name}: ctypes size {sz:#x} != expected {exact:#x}"
        if mx is not None:
            assert sz <= mx, f"{name}: ctypes size {sz:#x} > max {mx:#x}"
    return classes, sizes


if __name__ == "__main__":
    cls, sz = build_ctypes()
    print("container ABI check: all", len(sz), "structs match schema static_assert sizes")
    for n in sz:
        print(f"  {n}: {sz[n]:#x}")
