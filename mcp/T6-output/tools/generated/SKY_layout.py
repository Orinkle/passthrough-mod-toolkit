"""Protocol layout generated from schema.yaml (host: SKY). Do not edit."""
import ctypes

# ---- scalars from the schema vocabulary ----
MAGIC = 1413761876
VERSION = 1
MAPPING_NAME = 'Local\\Teardown_v1'
UNITS_PER_BLOCK = 1.0

# ---- container constants (inline constexpr, evaluated) ----
kColRegionMaxTris = 2048
kCollisionRingBytes = 16777216
kEventRingEntries = 4096
kInputRingEntries = 4096
kMagic = 1413761876
kMappingBytes = 52428800
kOffCollisionRing = 131072
kOffEventRing = 16908288
kOffHeader = 0
kOffInputRing = 4096
kOffMcState = 512
kOffRenderRing = 18874368
kOffWaterGrid = 768
kOffkOffSkyState = 256
kRenderRingBytes = 33554432
kVersion = 1

# ---- enums (container + vocabulary) ----
kHurtEnv = 1
kHurtFall = 3
kHurtMob = 2
kHurtNone = 0
kInputKey = 0
kInputMouseBtn = 1
kInputMouseMove = 2
kInputScroll = 3
kMcDead = 32
kMcEvBlockBreak = 0
kMcEvBlockPlace = 1
kMcEvDig = 2
kMcEvInteract = 3
kMcInWorld = 1
kMcOnGround = 4
kMcScreenOpen = 2
kMcSneaking = 8
kMcSprinting = 16
kRenOverlay = 0
kRenTile = 1
kTdInGame = 1
kTdLoading = 4
kTdMenuOpen = 2
kTdPaused = 8

class Header(ctypes.Structure):
    _fields_ = [
        ('magic', ctypes.c_uint32),
        ('version', ctypes.c_uint32),
        ('tdPid', ctypes.c_uint32),
        ('mcPid', ctypes.c_uint32),
        ('tdHeartbeatMs', ctypes.c_uint64),
        ('mcHeartbeatMs', ctypes.c_uint64),
    ]
Header.SIZE = 32  # == schema static_assert

class ColTri(ctypes.Structure):
    _fields_ = [
        ('nx', ctypes.c_float),
        ('ny', ctypes.c_float),
        ('nz', ctypes.c_float),
        ('d', ctypes.c_float),
        ('x0', ctypes.c_float),
        ('y0', ctypes.c_float),
        ('z0', ctypes.c_float),
        ('x1', ctypes.c_float),
        ('y1', ctypes.c_float),
        ('z1', ctypes.c_float),
        ('x2', ctypes.c_float),
        ('y2', ctypes.c_float),
        ('z2', ctypes.c_float),
    ]
ColTri.SIZE = 40  # == schema static_assert

class ColRegion(ctypes.Structure):
    _fields_ = [
        ('seq', ctypes.c_uint32),
        ('triCount', ctypes.c_uint32),
        ('originX', ctypes.c_int32),
        ('originZ', ctypes.c_int32),
        ('epoch', ctypes.c_uint32),
        ('triOffset', ctypes.c_uint64),
    ]
ColRegion.SIZE = 32  # == schema static_assert

class McEvent(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_uint32),
        ('flags', ctypes.c_uint32),
        ('tick', ctypes.c_uint64),
        ('x', ctypes.c_double),
        ('y', ctypes.c_double),
        ('z', ctypes.c_double),
    ]
McEvent.SIZE = 32  # == schema static_assert

class Header(ctypes.Structure):
    _fields_ = [
        ('magic', ctypes.c_uint32),
        ('version', ctypes.c_uint32),
        ('skyPid', ctypes.c_uint32),
        ('mcPid', ctypes.c_uint32),
        ('skyHeartbeatMs', ctypes.c_uint64),
        ('mcHeartbeatMs', ctypes.c_uint64),
    ]
Header.SIZE = 32  # == schema static_assert

class SKYState(ctypes.Structure):
    _fields_ = [
        ('seq', ctypes.c_uint32),
        ('flags', ctypes.c_uint32),
        ('bodyId', ctypes.c_uint32),
        ('epoch', ctypes.c_uint32),
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
SKYState.SIZE = 64  # == schema static_assert

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
        ('teleportAck', ctypes.c_uint32),
        ('guiScale', ctypes.c_uint32),
        ('frameCounter', ctypes.c_uint64),
        ('fovDeg', ctypes.c_float),
        ('onGround', ctypes.c_uint32),
        ('pad', ctypes.c_uint32 * 110),
    ]
McState.SIZE = 512  # == schema static_assert

MAPPING_BYTES = kMappingBytes

# ---- region base offsets (in the shared mapping) ----
REGIONS = {
    'kCollisionRingBytes': 16777216,
    'kEventRingEntries': 4096,
    'kInputRingEntries': 4096,
    'kMappingBytes': 52428800,
    'kOffCollisionRing': 131072,
    'kOffEventRing': 16908288,
    'kOffHeader': 0,
    'kOffInputRing': 4096,
    'kOffMcState': 512,
    'kOffRenderRing': 18874368,
    'kOffWaterGrid': 768,
    'kOffkOffSkyState': 256,
    'kRenderRingBytes': 33554432,
}

def sizeof_struct(name):
    return globals()[name].SIZE
