"""Protocol bindings generated from schema.yaml (host: Sky). Do not edit by hand."""
import ctypes

# ---- scalar constants ----
MAGIC = 1129925459
VERSION = 11
MAPPING_NAME = "Local\\SkyCraft_v1"
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
kWaterGridSize = 16
kNoWater = -1e+30
kMaxActors = 256
kMaxWorldEntities = 160
kOverlayDirty = 4
kOverlaySlotBytes = 33177600
kOverlaySlots = 3
kCollisionRingBytes = 33554432
kRenderRingBytes = 67108864
kInputRingEntries = 4096
kEventRingEntries = 512

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
    'kMaxActors': 256,
    'kMaxWorldEntities': 160,
    'kCollisionRingBytes': 33554432,
    'kInputRingEntries': 4096,
    'kEventRingEntries': 512,
}

def sizeof_struct(name):
    return globals()[name].SIZE
