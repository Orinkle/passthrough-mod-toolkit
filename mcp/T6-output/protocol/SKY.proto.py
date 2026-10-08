"""Protocol bindings generated from schema.yaml (host: Sky). Do not edit by hand."""
import ctypes

# ---- scalar constants ----
MAGIC = 1129925459
VERSION = 11
MAPPING_NAME = 'Local\\SkyCraft_v1'  # escaped for Python
UNITS_PER_BLOCK = 70.0
kOffHeader = 0
kOffSkyState = 256
kOffValState = 256
kOffMcState = 512
kOffOverlayCtl = 768
kOffOverlaySlotHdr = 832
kOffWaterGrid = 1024
kOffInputRing = 4096
kOffCollisionRing = 131072
kCollisionRingBytes = 33554432
kOffOverlayPixels = 33685504
kMaxOverlayW = 3840
kMaxOverlayH = 2160
kOverlaySlotBytes = 33177600
kOverlaySlots = 3
kOffActorTable = 73728
kOffEventRing = 94208
kOffWorldEntities = 114688
kOffRenderRing = 133218304
kRenderRingBytes = 67108864
kMappingBytes = 200327168
kInputRingEntries = 4096
kInputRingHeadOff = 0
kInputRingTailOff = 64
kInputRingDataOff = 128
kEventRingEntries = 512
kEventRingHeadOff = 0
kEventRingTailOff = 64
kEventRingDataOff = 128
kColRingHeadOff = 0
kColRingTailOff = 64
kColRingDataOff = 128
kColRingDataBytes = 33554304
kRenRingHeadOff = 0
kRenRingTailOff = 64
kRenRingDataOff = 128
kRenRingDataBytes = 67108736
kWaterGridSize = 16
kNoWater = -1e+30
kMaxActors = 256
kMaxWorldEntities = 160
kOverlayDirty = 4
kMaxOverlaySlots = 3

# ---- enums ----
kActorHostile = 1
kActorDead = 2
kActorEssential = 4
kActorInCombat = 8
kWeArrow = 1
kWeItem = 2
kWeTrident = 3
kWeBlock = 4
kWeCrack = 5
kWeShadow = 6
kPartNone = 0
kPartHead = 1
kPartBody = 2
kPartRightArm = 3
kPartLeftArm = 4
kPartRightLeg = 5
kPartLeftLeg = 6
kPartCount = 7
kLightSteady = 0
kLightFlame = 1
kLightLava = 2
kHazardNone = 0
kHazardFire = 1
kHazardLava = 2
kHazardMagma = 3
kColPad = 0
kColClear = 1
kColRegion = 2
kColTris = 3
kSkyInGame = 1
kSkyMenuOpen = 2
kSkyLoading = 4
kMcInWorld = 1
kMcScreenOpen = 2
kMcOnGround = 4
kMcSneaking = 8
kMcSprinting = 16
kMcDead = 32
kMcSwimming = 64
kMcFlying = 128
kInKey = 1
kInMouseButton = 2
kInScroll = 3
kInCursor = 4
kInText = 5
kInReleaseAll = 6
kInHurt = 7
kInOpenMenu = 8
kHurtBlockedInSkyrim = 1
kHurtPowerAttack = 2
kEvHitActor = 1
kEvPlayerDied = 2
kEvExplosion = 3
kEvArrowStuck = 4
kEvSkillUse = 5
kRenPad = 0
kRenAtlas = 1
kRenSection = 2
kRenClearAll = 3
kRenTexture = 4
kRenAvatar = 5
kRenScene = 6
kRenAtlasRegion = 7
kRenLights = 8
kRenSolids = 10
kRenDug = 11
kRenRagdoll = 9
kTriStairHelper = 1
kTriDiggable = 2
kTriGhost = 4
kTriTerrain = 8
kTriMaterialShift = 8
kDigNone = 0
kDigGrass = 1
kDigDirt = 2
kDigStone = 3
kDigCobble = 4
kDigSnow = 5
kDigIce = 6
kDigSand = 7
kDigGravel = 8
kDigMud = 9
kDigOakLog = 10
kDigSpruceLog = 11
kDigBirchLog = 12
kDigPlanks = 13
kDigMetal = 14
kDigGlass = 15
kDigOrganic = 16
kDigCloth = 17
kDigBone = 18
kDigWeb = 19
kDigAsh = 20
kDigBedrock = 21

# ---- struct offsets + sizes (bytes; ABI-equivalent to the C++ header) ----
OFFSETS = {
    'WaterGrid': {
        'seq': 0,
        'originX': 4,
        'originZ': 8,
        'worldId': 12,
        'surface': 16,
    },
    'OverlayCtl': {
        'state': 0,
        'pad': 4,
        'framesPublished': 8,
    },
    'OverlaySlotHdr': {
        'width': 0,
        'height': 4,
        'flags': 8,
        'pad': 12,
        'frameId': 16,
        'reserved': 24,
    },
    'ActorRecord': {
        'formId': 0,
        'flags': 4,
        'x': 8,
        'y': 12,
        'z': 16,
        'yaw': 20,
        'width': 24,
        'height': 28,
        'healthFrac': 32,
        'level': 36,
        'pad': 38,
        'name': 40,
    },
    'ActorTable': {
        'seq': 0,
        'count': 4,
        'pad': 8,
        'actors': 64,
    },
    'McEvent': {
        'type': 0,
        'formId': 4,
        'a': 8,
        'b': 12,
        'c': 16,
        'd': 20,
        'flags': 24,
        'weapon': 28,
    },
    'WorldEntity': {
        'kind': 0,
        'id': 4,
        'x': 8,
        'y': 12,
        'z': 16,
        'yaw': 20,
        'pitch': 24,
        'scale': 28,
        'ext': 32,
        'uv': 44,
        'tint': 92,
    },
    'WorldEntities': {
        'seq': 0,
        'count': 4,
        'hasSelection': 8,
        'selMin': 12,
        'selMax': 24,
        'pad': 36,
        'entities': 64,
    },
    'RenSolids': {
        'sx': 0,
        'sy': 4,
        'sz': 8,
        'count': 12,
    },
    'RenDug': {
        'sx': 0,
        'sy': 4,
        'sz': 8,
        'count': 12,
        'worldId': 16,
        'pad': 20,
    },
    'RenLights': {
        'sx': 0,
        'sy': 4,
        'sz': 8,
        'count': 12,
    },
    'RenLight': {
        'x': 0,
        'y': 1,
        'z': 2,
        'level': 3,
        'color': 4,
    },
    'RenAtlasRegion': {
        'x': 0,
        'y': 4,
        'width': 8,
        'height': 12,
    },
    'RenScene': {
        'originX': 0,
        'originY': 8,
        'originZ': 16,
        'batchCount': 24,
        'vertexCount': 28,
    },
    'RenTexture': {
        'id': 0,
        'width': 4,
        'height': 8,
        'pad': 12,
    },
    'RenAvatar': {
        'batchCount': 0,
        'vertexCount': 4,
    },
    'RenBatch': {
        'texture': 0,
        'first': 4,
        'count': 8,
        'flags': 12,
    },
    'RenAtlas': {
        'width': 0,
        'height': 4,
    },
    'RenSection': {
        'sx': 0,
        'sy': 4,
        'sz': 8,
        'vertexCount': 12,
    },
    'RenVertex': {
        'x': 0,
        'y': 4,
        'z': 8,
        'u': 12,
        'v': 16,
        'color': 20,
        'light': 24,
        'flags': 28,
    },
    'InputEvent': {
        'type': 0,
        'code': 2,
        'a': 4,
        'b': 8,
        'c': 12,
    },
    'ColTri': {
        'v': 0,
        'flags': 36,
    },
    'ColMsgHeader': {
        'type': 0,
        'payloadBytes': 4,
    },
    'ColRegion': {
        'minX': 0,
        'minY': 4,
        'minZ': 8,
        'maxX': 12,
        'maxY': 16,
        'maxZ': 20,
        'epoch': 24,
        'count': 28,
    },
    'ColBlock': {
        'x': 0,
        'y': 4,
        'z': 8,
        'pad': 12,
        'bits': 16,
    },
    'Header': {
        'magic': 0,
        'version': 4,
        'skyrimPid': 8,
        'mcPid': 12,
        'skyrimHeartbeatMs': 16,
        'mcHeartbeatMs': 24,
    },
    'SkyState': {
        'seq': 0,
        'flags': 4,
        'worldId': 8,
        'collisionEpoch': 12,
        'posX': 16,
        'posY': 24,
        'posZ': 32,
        'yaw': 40,
        'pitch': 44,
        'teleportSeq': 48,
        'viewportW': 52,
        'viewportH': 56,
        'gameHour': 60,
    },
    'McState': {
        'seq': 0,
        'flags': 4,
        'x': 8,
        'y': 16,
        'z': 24,
        'yaw': 32,
        'pitch': 36,
        'eyeHeight': 40,
        'sensitivity': 44,
        'teleportAck': 48,
        'guiScale': 52,
        'frameCounter': 56,
        'fovDeg': 64,
        'bobPhase': 68,
        'bobAmount': 72,
        'pad4C': 76,
        'eyeX': 80,
        'eyeY': 88,
        'eyeZ': 96,
        'tickQpc': 104,
        'prevX': 112,
        'prevY': 120,
        'prevZ': 128,
        'curX': 136,
        'curY': 144,
        'curZ': 152,
        'tickEyeO': 160,
        'tickEye': 164,
        'walkDistO': 168,
        'walkDist': 172,
        'bobO': 176,
        'bob': 180,
        'tickMs': 184,
        'tickPad': 188,
        'cameraMode': 192,
        'cameraDistance': 196,
    },
}
SIZES = {
    'WaterGrid': 1040,
    'OverlayCtl': 16,
    'OverlaySlotHdr': 64,
    'ActorRecord': 64,
    'ActorTable': 16448,
    'McEvent': 32,
    'WorldEntity': 96,
    'WorldEntities': 15424,
    'RenSolids': 16,
    'RenDug': 24,
    'RenLights': 16,
    'RenLight': 8,
    'RenAtlasRegion': 16,
    'RenScene': 32,
    'RenTexture': 16,
    'RenAvatar': 8,
    'RenBatch': 16,
    'RenAtlas': 8,
    'RenSection': 16,
    'RenVertex': 32,
    'InputEvent': 16,
    'ColTri': 40,
    'ColMsgHeader': 8,
    'ColRegion': 32,
    'ColBlock': 80,
    'Header': 32,
    'SkyState': 64,
    'McState': 200,
}

class WaterGrid(ctypes.Structure):
    _fields_ = [
        ('seq', ctypes.c_uint32),
        ('originX', ctypes.c_int32),
        ('originZ', ctypes.c_int32),
        ('worldId', ctypes.c_uint32),
        ('surface', ctypes.c_float * 256),
    ]
WaterGrid.SIZE = 1040  # verified == C++ static_assert

class OverlayCtl(ctypes.Structure):
    _fields_ = [
        ('state', ctypes.c_uint32),
        ('pad', ctypes.c_uint32),
        ('framesPublished', ctypes.c_uint64),
    ]
OverlayCtl.SIZE = 16  # verified == C++ static_assert

class OverlaySlotHdr(ctypes.Structure):
    _fields_ = [
        ('width', ctypes.c_uint32),
        ('height', ctypes.c_uint32),
        ('flags', ctypes.c_uint32),
        ('pad', ctypes.c_uint32),
        ('frameId', ctypes.c_uint64),
        ('reserved', ctypes.c_uint8 * 40),
    ]
OverlaySlotHdr.SIZE = 64  # verified == C++ static_assert

class ActorRecord(ctypes.Structure):
    _fields_ = [
        ('formId', ctypes.c_uint32),
        ('flags', ctypes.c_uint32),
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('yaw', ctypes.c_float),
        ('width', ctypes.c_float),
        ('height', ctypes.c_float),
        ('healthFrac', ctypes.c_float),
        ('level', ctypes.c_uint16),
        ('pad', ctypes.c_uint16),
        ('name', ctypes.c_uint8 * 24),
    ]
ActorRecord.SIZE = 64  # verified == C++ static_assert

class ActorTable(ctypes.Structure):
    _fields_ = [
        ('seq', ctypes.c_uint32),
        ('count', ctypes.c_uint32),
        ('pad', ctypes.c_uint8 * 56),
        ('actors', ActorRecord * 256),
    ]
ActorTable.SIZE = 16448  # verified == C++ static_assert

class McEvent(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_uint32),
        ('formId', ctypes.c_uint32),
        ('a', ctypes.c_float),
        ('b', ctypes.c_float),
        ('c', ctypes.c_float),
        ('d', ctypes.c_float),
        ('flags', ctypes.c_uint32),
        ('weapon', ctypes.c_uint32),
    ]
McEvent.SIZE = 32  # verified == C++ static_assert

class WorldEntity(ctypes.Structure):
    _fields_ = [
        ('kind', ctypes.c_uint32),
        ('id', ctypes.c_uint32),
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('yaw', ctypes.c_float),
        ('pitch', ctypes.c_float),
        ('scale', ctypes.c_float),
        ('ext', ctypes.c_float * 3),
        ('uv', ctypes.c_float * 4 * 3),
        ('tint', ctypes.c_uint32),
    ]
WorldEntity.SIZE = 96  # verified == C++ static_assert

class WorldEntities(ctypes.Structure):
    _fields_ = [
        ('seq', ctypes.c_uint32),
        ('count', ctypes.c_uint32),
        ('hasSelection', ctypes.c_uint32),
        ('selMin', ctypes.c_float * 3),
        ('selMax', ctypes.c_float * 3),
        ('pad', ctypes.c_uint8 * 28),
        ('entities', WorldEntity * 160),
    ]
WorldEntities.SIZE = 15424  # verified == C++ static_assert

class RenSolids(ctypes.Structure):
    _fields_ = [
        ('sx', ctypes.c_int32),
        ('sy', ctypes.c_int32),
        ('sz', ctypes.c_int32),
        ('count', ctypes.c_uint32),
    ]
RenSolids.SIZE = 16  # verified == C++ static_assert

class RenDug(ctypes.Structure):
    _fields_ = [
        ('sx', ctypes.c_int32),
        ('sy', ctypes.c_int32),
        ('sz', ctypes.c_int32),
        ('count', ctypes.c_uint32),
        ('worldId', ctypes.c_uint32),
        ('pad', ctypes.c_uint32),
    ]
RenDug.SIZE = 24  # verified == C++ static_assert

class RenLights(ctypes.Structure):
    _fields_ = [
        ('sx', ctypes.c_int32),
        ('sy', ctypes.c_int32),
        ('sz', ctypes.c_int32),
        ('count', ctypes.c_uint32),
    ]
RenLights.SIZE = 16  # verified == C++ static_assert

class RenLight(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_uint8),
        ('y', ctypes.c_uint8),
        ('z', ctypes.c_uint8),
        ('level', ctypes.c_uint8),
        ('color', ctypes.c_uint32),
    ]
RenLight.SIZE = 8  # verified == C++ static_assert

class RenAtlasRegion(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_uint32),
        ('y', ctypes.c_uint32),
        ('width', ctypes.c_uint32),
        ('height', ctypes.c_uint32),
    ]
RenAtlasRegion.SIZE = 16  # verified == C++ static_assert

class RenScene(ctypes.Structure):
    _fields_ = [
        ('originX', ctypes.c_double),
        ('originY', ctypes.c_double),
        ('originZ', ctypes.c_double),
        ('batchCount', ctypes.c_uint32),
        ('vertexCount', ctypes.c_uint32),
    ]
RenScene.SIZE = 32  # verified == C++ static_assert

class RenTexture(ctypes.Structure):
    _fields_ = [
        ('id', ctypes.c_uint32),
        ('width', ctypes.c_uint32),
        ('height', ctypes.c_uint32),
        ('pad', ctypes.c_uint32),
    ]
RenTexture.SIZE = 16  # verified == C++ static_assert

class RenAvatar(ctypes.Structure):
    _fields_ = [
        ('batchCount', ctypes.c_uint32),
        ('vertexCount', ctypes.c_uint32),
    ]
RenAvatar.SIZE = 8  # verified == C++ static_assert

class RenBatch(ctypes.Structure):
    _fields_ = [
        ('texture', ctypes.c_uint32),
        ('first', ctypes.c_uint32),
        ('count', ctypes.c_uint32),
        ('flags', ctypes.c_uint32),
    ]
RenBatch.SIZE = 16  # verified == C++ static_assert

class RenAtlas(ctypes.Structure):
    _fields_ = [
        ('width', ctypes.c_uint32),
        ('height', ctypes.c_uint32),
    ]
RenAtlas.SIZE = 8  # verified == C++ static_assert

class RenSection(ctypes.Structure):
    _fields_ = [
        ('sx', ctypes.c_int32),
        ('sy', ctypes.c_int32),
        ('sz', ctypes.c_int32),
        ('vertexCount', ctypes.c_uint32),
    ]
RenSection.SIZE = 16  # verified == C++ static_assert

class RenVertex(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('u', ctypes.c_float),
        ('v', ctypes.c_float),
        ('color', ctypes.c_uint32),
        ('light', ctypes.c_uint32),
        ('flags', ctypes.c_uint32),
    ]
RenVertex.SIZE = 32  # verified == C++ static_assert

class InputEvent(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_uint16),
        ('code', ctypes.c_uint16),
        ('a', ctypes.c_int32),
        ('b', ctypes.c_int32),
        ('c', ctypes.c_int32),
    ]
InputEvent.SIZE = 16  # verified == C++ static_assert

class ColTri(ctypes.Structure):
    _fields_ = [
        ('v', ctypes.c_float * 9),
        ('flags', ctypes.c_uint32),
    ]
ColTri.SIZE = 40  # verified == C++ static_assert

class ColMsgHeader(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_uint32),
        ('payloadBytes', ctypes.c_uint32),
    ]
ColMsgHeader.SIZE = 8  # verified == C++ static_assert

class ColRegion(ctypes.Structure):
    _fields_ = [
        ('minX', ctypes.c_int32),
        ('minY', ctypes.c_int32),
        ('minZ', ctypes.c_int32),
        ('maxX', ctypes.c_int32),
        ('maxY', ctypes.c_int32),
        ('maxZ', ctypes.c_int32),
        ('epoch', ctypes.c_uint32),
        ('count', ctypes.c_uint32),
    ]
ColRegion.SIZE = 32  # verified == C++ static_assert

class ColBlock(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_int32),
        ('y', ctypes.c_int32),
        ('z', ctypes.c_int32),
        ('pad', ctypes.c_uint32),
        ('bits', ctypes.c_uint64 * 8),
    ]
ColBlock.SIZE = 80  # verified == C++ static_assert

class Header(ctypes.Structure):
    _fields_ = [
        ('magic', ctypes.c_uint32),
        ('version', ctypes.c_uint32),
        ('skyrimPid', ctypes.c_uint32),
        ('mcPid', ctypes.c_uint32),
        ('skyrimHeartbeatMs', ctypes.c_uint64),
        ('mcHeartbeatMs', ctypes.c_uint64),
    ]
Header.SIZE = 32  # verified == C++ static_assert

class SkyState(ctypes.Structure):
    _fields_ = [
        ('seq', ctypes.c_uint32),
        ('flags', ctypes.c_uint32),
        ('worldId', ctypes.c_uint32),
        ('collisionEpoch', ctypes.c_uint32),
        ('posX', ctypes.c_double),
        ('posY', ctypes.c_double),
        ('posZ', ctypes.c_double),
        ('yaw', ctypes.c_float),
        ('pitch', ctypes.c_float),
        ('teleportSeq', ctypes.c_uint32),
        ('viewportW', ctypes.c_uint32),
        ('viewportH', ctypes.c_uint32),
        ('gameHour', ctypes.c_float),
    ]
SkyState.SIZE = 64  # verified == C++ static_assert

class McState(ctypes.Structure):
    _fields_ = [
        ('seq', ctypes.c_uint32),
        ('flags', ctypes.c_uint32),
        ('x', ctypes.c_double),
        ('y', ctypes.c_double),
        ('z', ctypes.c_double),
        ('yaw', ctypes.c_float),
        ('pitch', ctypes.c_float),
        ('eyeHeight', ctypes.c_float),
        ('sensitivity', ctypes.c_float),
        ('teleportAck', ctypes.c_uint32),
        ('guiScale', ctypes.c_uint32),
        ('frameCounter', ctypes.c_uint64),
        ('fovDeg', ctypes.c_float),
        ('bobPhase', ctypes.c_float),
        ('bobAmount', ctypes.c_float),
        ('pad4C', ctypes.c_uint32),
        ('eyeX', ctypes.c_double),
        ('eyeY', ctypes.c_double),
        ('eyeZ', ctypes.c_double),
        ('tickQpc', ctypes.c_int64),
        ('prevX', ctypes.c_double),
        ('prevY', ctypes.c_double),
        ('prevZ', ctypes.c_double),
        ('curX', ctypes.c_double),
        ('curY', ctypes.c_double),
        ('curZ', ctypes.c_double),
        ('tickEyeO', ctypes.c_float),
        ('tickEye', ctypes.c_float),
        ('walkDistO', ctypes.c_float),
        ('walkDist', ctypes.c_float),
        ('bobO', ctypes.c_float),
        ('bob', ctypes.c_float),
        ('tickMs', ctypes.c_float),
        ('tickPad', ctypes.c_uint32),
        ('cameraMode', ctypes.c_uint32),
        ('cameraDistance', ctypes.c_float),
    ]
McState.SIZE = 200  # verified == C++ static_assert

MAPPING_BYTES = kMappingBytes

# ---- region base offsets (in the shared mapping) ----
REGIONS = {
    'kOffHeader': 0,
    'kOffSkyState': 256,
    'kOffValState': 256,
    'kOffMcState': 512,
    'kOffOverlayCtl': 768,
    'kOffOverlaySlotHdr': 832,
    'kOffWaterGrid': 1024,
    'kOffInputRing': 4096,
    'kOffCollisionRing': 131072,
    'kCollisionRingBytes': 33554432,
    'kOffOverlayPixels': 33685504,
    'kMaxOverlayW': 3840,
    'kMaxOverlayH': 2160,
    'kOffActorTable': 73728,
    'kOffEventRing': 94208,
    'kOffWorldEntities': 114688,
    'kOffRenderRing': 133218304,
    'kInputRingEntries': 4096,
    'kInputRingHeadOff': 0,
    'kInputRingTailOff': 64,
    'kInputRingDataOff': 128,
    'kEventRingEntries': 512,
    'kEventRingHeadOff': 0,
    'kEventRingTailOff': 64,
    'kEventRingDataOff': 128,
    'kColRingHeadOff': 0,
    'kColRingTailOff': 64,
    'kColRingDataOff': 128,
    'kColRingDataBytes': 33554304,
    'kRenRingHeadOff': 0,
    'kRenRingTailOff': 64,
    'kRenRingDataOff': 128,
    'kRenRingDataBytes': 67108736,
    'kMaxActors': 256,
    'kMaxWorldEntities': 160,
    'kMaxOverlaySlots': 3,
}

def sizeof_struct(name):
    return globals()[name].SIZE

def offsetof(struct_type, field):
    return getattr(struct_type, field).offset

# ---- seqlock skeleton (u32 seq at base+0, struct body at base+8) ----
def seqlock_read(base_addr, struct_type):
    """Return a live view of struct_type at base_addr+8, or None if a writer is mid-update."""
    seq_p = ctypes.cast(base_addr, ctypes.POINTER(ctypes.c_uint32))
    for _ in range(1 << 20):
        s0 = seq_p[0]
        if s0 & 1:
            continue  # writer mid-update
        out = struct_type.from_address(base_addr + 8)
        if seq_p[0] == s0:
            return out  # even and stable
    return None

def seqlock_write(base_addr, struct_type, value):
    """Publish value into struct_type at base_addr+8 under the odd/even seq protocol."""
    seq_p = ctypes.cast(base_addr, ctypes.POINTER(ctypes.c_uint32))
    seq_p[0] += 1  # -> odd (writer active)
    ctypes.memmove(base_addr + 8, ctypes.byref(value), ctypes.sizeof(struct_type))
    seq_p[0] += 1  # -> even (stable)

# ---- SPSC ring skeleton (power-of-two data region) ----
def ring_produce(base_addr, head_off, data_off, data_bytes, payload):
    head_p = ctypes.cast(base_addr + head_off, ctypes.POINTER(ctypes.c_uint64))
    head = head_p[0]
    mask = data_bytes - 1
    if (head & mask) + len(payload) > data_bytes:
        return False  # no room (simple bound)
    ctypes.memmove(base_addr + data_off + (head & mask), payload, len(payload))
    head_p[0] = head + len(payload)
    return True

def ring_consume(base_addr, tail_off, head_off, data_off, data_bytes, n):
    tail_p = ctypes.cast(base_addr + tail_off, ctypes.POINTER(ctypes.c_uint64))
    head_p = ctypes.cast(base_addr + head_off, ctypes.POINTER(ctypes.c_uint64))
    tail, head = tail_p[0], head_p[0]
    if tail + n > head:
        return None
    mask = data_bytes - 1
    buf = ctypes.create_string_buffer(n)
    ctypes.memmove(buf, base_addr + data_off + (tail & mask), n)
    tail_p[0] = tail + n
    return buf.raw
