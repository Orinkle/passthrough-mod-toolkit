// Passthrough shared-memory protocol (generated from schema.yaml).
//
// This header is generated. The byte layout is the single source of truth in
// schema.yaml + the per-host vocabulary. All multi-byte values are little-endian.
#pragma once

#include <cstdint>

namespace skycraft::proto
{
	inline constexpr std::uint32_t kMagic = 0x43594B53;
	inline constexpr std::uint32_t kVersion = 11;
	inline constexpr wchar_t       kMappingName[] = L"Local\\SkyCraft_v1";
	inline constexpr double kUnitsPerBlock = 70.0;

// ---- region offsets ---------------------------------------------------------------------
inline constexpr std::uint64_t kOffHeader = 0x0;
inline constexpr std::uint64_t kOffSkyState = 0x100;
inline constexpr std::uint64_t kOffMcState = 0x200;
inline constexpr std::uint64_t kOffOverlayCtl = 0x300;
inline constexpr std::uint64_t kOffOverlaySlotHdr = 0x340;  // 3 x 0x40
inline constexpr std::uint64_t kOffWaterGrid = 0x400;       // host -> MC, see WaterGrid
inline constexpr std::uint64_t kOffInputRing = 0x1000;
inline constexpr std::uint64_t kOffCollisionRing = 0x20000;
inline constexpr std::uint64_t kCollisionRingBytes = 32ull << 20;
inline constexpr std::uint64_t kOffOverlayPixels = kOffCollisionRing + kCollisionRingBytes;
inline constexpr std::uint32_t kMaxOverlayW = 3840;
inline constexpr std::uint32_t kMaxOverlayH = 2160;
inline constexpr std::uint64_t kOverlaySlotBytes = std::uint64_t(kMaxOverlayW) * kMaxOverlayH * 4;
inline constexpr std::uint32_t kOverlaySlots = 3;
inline constexpr std::uint64_t kOffActorTable = 0x12000;   // host -> MC, see ActorTable
inline constexpr std::uint64_t kOffEventRing = 0x17000;    // MC -> host, see McEvent
inline constexpr std::uint64_t kOffWorldEntities = 0x1C000;  // MC -> host, see WorldEntities
inline constexpr std::uint64_t kOffRenderRing = kOffOverlayPixels + kOverlaySlotBytes * kOverlaySlots;
inline constexpr std::uint64_t kRenderRingBytes = 64ull << 20;
inline constexpr std::uint64_t kMappingBytes = kOffRenderRing + kRenderRingBytes;


	struct Header
	{
		std::uint32_t magic;
		std::uint32_t version;
		std::uint32_t skyrimPid;
		std::uint32_t mcPid;
		std::uint64_t skyrimHeartbeatMs;
		std::uint64_t mcHeartbeatMs;
	};
	static_assert(sizeof(Header) == 0x20);

	enum SkyFlags : std::uint32_t
	{
		kSkyInGame = 1u << 0,
		kSkyMenuOpen = 1u << 1,
		kSkyLoading = 1u << 2,
	};

// ---- host water grid (seqlock like host state) ----------------------------------------
inline constexpr std::uint32_t kWaterGridSize = 16;
inline constexpr float         kNoWater = -1.0e30f;

struct WaterGrid
{
  std::uint32_t seq;
  std::int32_t  originX, originZ;  // Minecraft block column of surface[0]
  std::uint32_t worldId;           // as in host state
  float         surface[kWaterGridSize * kWaterGridSize];  // [z * size + x]: MC y of the water surface; kNoWater: none
};
static_assert(sizeof(WaterGrid) <= 0xC00);

	struct SkyState
	{
		std::uint32_t seq;
		std::uint32_t flags;
		std::uint32_t worldId;
		std::uint32_t collisionEpoch;
		double        posX, posY, posZ;
		float         yaw, pitch;
		std::uint32_t teleportSeq;
		std::uint32_t viewportW, viewportH;
		float         gameHour;
	};
	static_assert(sizeof(SkyState) == 0x40);

	enum McFlags : std::uint32_t
	{
		kMcInWorld = 1u << 0,
		kMcScreenOpen = 1u << 1,
		kMcOnGround = 1u << 2,
		kMcSneaking = 1u << 3,
		kMcSprinting = 1u << 4,
		kMcDead = 1u << 5,
		kMcSwimming = 1u << 6,
		kMcFlying = 1u << 7,
	};

	struct McState
	{
		std::uint32_t seq;
		std::uint32_t flags;
		double        x, y, z;
		float         yaw, pitch;
		float         eyeHeight;
		float         sensitivity;
		std::uint32_t teleportAck;
		std::uint32_t guiScale;
		std::uint64_t frameCounter;
		float         fovDeg;
		float         bobPhase;
		float         bobAmount;
		std::uint32_t pad4C;
		double        eyeX, eyeY, eyeZ;
		std::int64_t tickQpc;
		double       prevX, prevY, prevZ;
		double       curX, curY, curZ;
		float        tickEyeO, tickEye;
		float        walkDistO, walkDist;
		float        bobO, bob;
		float        tickMs;
		std::uint32_t tickPad;
		std::uint32_t cameraMode;
		float         cameraDistance;
	};
	static_assert(sizeof(McState) == 0xC8);
	static_assert(sizeof(McState) <= 0x100);

// ---- overlay triple buffer @0x300 --------------------------------------------------------
inline constexpr std::uint32_t kOverlayDirty = 1u << 2;

struct OverlayCtl
{
  std::uint32_t state;
  std::uint32_t pad;
  std::uint64_t framesPublished;
};

struct OverlaySlotHdr
{
  std::uint32_t width;
  std::uint32_t height;
  std::uint32_t flags;  // bit0: rows are bottom-up
  std::uint32_t pad;
  std::uint64_t frameId;
  std::uint8_t  reserved[0x40 - 0x18];
};
static_assert(sizeof(OverlaySlotHdr) == 0x40);

// ---- input ring @0x1000 (host produces, MC consumes) ----------------------------------
inline constexpr std::uint32_t kInputRingEntries = 4096;  // power of two
inline constexpr std::uint64_t kInputRingHeadOff = 0x00;  // u64, written by host
inline constexpr std::uint64_t kInputRingTailOff = 0x40;  // u64, written by MC
inline constexpr std::uint64_t kInputRingDataOff = 0x80;

	enum InputType : std::uint16_t
	{
		kInKey = 1,
		kInMouseButton = 2,
		kInScroll = 3,
		kInCursor = 4,
		kInText = 5,
		kInReleaseAll = 6,
		kInHurt = 7,
		kInOpenMenu = 8,
	};

enum HurtKind : std::uint16_t
{
  kHurtMelee = 0,
  kHurtProjectile = 1,
  kHurtMagic = 2,
  kHurtOther = 3,
};

	enum HurtFlags : std::uint32_t
	{
		kHurtBlockedInSkyrim = 1u << 0,
		kHurtPowerAttack = 1u << 1,
	};

// ---- actor table @0x12000 (host -> MC, seqlock) ----------------------------------------
inline constexpr std::uint32_t kMaxActors = 256;

enum ActorFlags : std::uint32_t
{
  kActorHostile = 1u << 0,    // hostile to the player right now
  kActorDead = 1u << 1,
  kActorEssential = 1u << 2,
  kActorInCombat = 1u << 3,
};

struct ActorRecord
{
  std::uint32_t formId;
  std::uint32_t flags;       // ActorFlags
  float         x, y, z;     // feet, MC coords
  float         yaw;         // MC degrees
  float         width;       // blocks
  float         height;      // blocks
  float         healthFrac;  // 0..1
  std::uint16_t level;
  std::uint16_t pad;
  char          name[24];    // display name, UTF-8, NUL-terminated (truncated)
};
static_assert(sizeof(ActorRecord) == 64);

struct ActorTable
{
  std::uint32_t seq;
  std::uint32_t count;
  std::uint8_t  pad[0x40 - 8];
  ActorRecord   actors[kMaxActors];
};
static_assert(sizeof(ActorTable) == 0x40 + 64 * kMaxActors);

// ---- event ring @0x17000 (MC -> host) ---------------------------------------------------
inline constexpr std::uint32_t kEventRingEntries = 512;  // power of two
inline constexpr std::uint64_t kEventRingHeadOff = 0x00;  // u64, written by MC
inline constexpr std::uint64_t kEventRingTailOff = 0x40;  // u64, written by host
inline constexpr std::uint64_t kEventRingDataOff = 0x80;

	enum McEventType : std::uint32_t
	{
		kEvHitActor = 1,
		kEvPlayerDied = 2,
		kEvExplosion = 3,
		kEvArrowStuck = 4,
		kEvSkillUse = 5,
	};


enum HitFlags : std::uint32_t
{
  kHitCritical = 1u << 0,
  kHitProjectile = 1u << 1,
  kHitSweep = 1u << 2,
  kHitFire = 1u << 3,
};

enum HitWeapon : std::uint32_t
{
  kWeaponUnarmed = 0,
  kWeaponBlade = 1,   // swords
  kWeaponAxe = 2,
  kWeaponBlunt = 3,   // maces, pickaxes, shovels, hoes, anything else held
  kWeaponPierce = 4,  // tridents, spears
  kWeaponArrow = 5,   // arrows and other projectiles
};

struct McEvent
{
  std::uint32_t type;
  std::uint32_t formId;
  float         a, b, c, d;
  std::uint32_t flags;
  std::uint32_t weapon;  // HitWeapon for kEvHitActor
};
static_assert(sizeof(McEvent) == 32);

// ---- world entities @0x1C000 (MC -> host, seqlock) -------------------------------------
inline constexpr std::uint32_t kMaxWorldEntities = 160;

enum WorldEntityKind : std::uint32_t
{
  kWeArrow = 1,    // uv[0]: the arrow's item icon
  kWeItem = 2,     // dropped/thrown item: a flat sprite (uv[0]) turning about the vertical
  kWeTrident = 3,  // uv[0]: the trident's item icon
  kWeBlock = 4,    // dropped block item: a spinning cube of side `scale`, uv[0..2] = side, top, bottom
  kWeCrack = 5,    // block-breaking cracks over the box at (x, y, z) of size ext, uv[0] = crack stage
  kWeShadow = 6,   // a player's or mob's feet at (x, y, z), `scale` wide: its soft contact shadow
};

struct WorldEntity
{
  std::uint32_t kind;        // WorldEntityKind
  std::uint32_t id;          // MC entity id (stable while it exists)
  float         x, y, z;     // MC coords (interpolated at MC's render time)
  float         yaw, pitch;  // MC degrees
  float         scale;
  float         ext[3];      // kWeCrack: box size
  float         uv[3][4];    // atlas rects {u0, v0, u1, v1}
  std::uint32_t tint;        // RGBA8 multiplier for the top face (grass, leaves); 0 = none
};
static_assert(sizeof(WorldEntity) == 96);

struct WorldEntities
{
  std::uint32_t seq;
  std::uint32_t count;
  std::uint32_t hasSelection;           // draw an outline around the targeted block
  float         selMin[3], selMax[3];   // MC coords
  std::uint8_t  pad[0x40 - 36];
  WorldEntity   entities[kMaxWorldEntities];
};
static_assert(sizeof(WorldEntities) == 0x40 + sizeof(WorldEntity) * kMaxWorldEntities);
static_assert(kOffWorldEntities + sizeof(WorldEntities) <= kOffCollisionRing);

// ---- render ring (MC -> host) -----------------------------------------------------------
inline constexpr std::uint64_t kRenRingHeadOff = 0x00;
inline constexpr std::uint64_t kRenRingTailOff = 0x40;
inline constexpr std::uint64_t kRenRingDataOff = 0x80;
inline constexpr std::uint64_t kRenRingDataBytes = kRenderRingBytes - kRenRingDataOff;

	enum RenType : std::uint32_t
	{
		kRenPad = 0,
		kRenAtlas = 1,
		kRenSection = 2,
		kRenClearAll = 3,
		kRenTexture = 4,
		kRenAvatar = 5,
		kRenScene = 6,
		kRenAtlasRegion = 7,
		kRenLights = 8,
		kRenSolids = 10,
		kRenDug = 11,
		kRenRagdoll = 9,
	};

struct RenSolids
{
  std::int32_t  sx, sy, sz;  // section coords, as in RenSection
  std::uint32_t count;       // solid blocks (0: none, and no bitset follows)
};

struct RenDug
{
  std::int32_t  sx, sy, sz;  // section coords, as in RenSection
  std::uint32_t count;       // dug blocks (0: none, and no bitset follows)
  std::uint32_t worldId;     // the host world (host state::worldId) the bits belong to
  std::uint32_t pad;
};
static_assert(sizeof(RenDug) == 24);

	enum DigMaterial : std::uint8_t
	{
		kDigNone = 0,
		kDigGrass = 1,
		kDigDirt = 2,
		kDigStone = 3,
		kDigCobble = 4,
		kDigSnow = 5,
		kDigIce = 6,
		kDigSand = 7,
		kDigGravel = 8,
		kDigMud = 9,
		kDigOakLog = 10,
		kDigSpruceLog = 11,
		kDigBirchLog = 12,
		kDigPlanks = 13,
		kDigMetal = 14,
		kDigGlass = 15,
		kDigOrganic = 16,
		kDigCloth = 17,
		kDigBone = 18,
		kDigWeb = 19,
		kDigAsh = 20,
		kDigBedrock = 21,
		kDigMaterialCount
	};

enum RagdollPart : std::uint32_t
{
  kPartNone = 0,
  kPartHead = 1,
  kPartBody = 2,
  kPartRightArm = 3,
  kPartLeftArm = 4,
  kPartRightLeg = 5,
  kPartLeftLeg = 6,
  kPartCount = 7,
};

struct RenLights
{
  std::int32_t  sx, sy, sz;  // section coords, as in RenSection
  std::uint32_t count;
};

enum LightKind : std::uint8_t
{
  kLightSteady = 0,
  kLightFlame = 1,  // torches, fire, campfires, candles: flicker
  kLightLava = 2,   // lava, magma: a slow glow
};

enum BlockHazard : std::uint8_t
{
  kHazardNone = 0,
  kHazardFire = 1,   // fire, soul fire, campfires: burns what stands in it
  kHazardLava = 2,   // lava: burns hard
  kHazardMagma = 3,  // magma block: hurts what stands on top of it
};

struct RenLight
{
  std::uint8_t  x, y, z;  // block within the section
  std::uint8_t  level;    // Minecraft light emission, 1-15
  std::uint32_t color;    // RGB8 (r low byte); top byte: LightKind in bits 0-3, BlockHazard in 4-7
};
static_assert(sizeof(RenLight) == 8);

struct RenAtlasRegion
{
  std::uint32_t x, y, width, height;  // pixels in the combined atlas (kRenAtlas)
};

struct RenScene
{
  double        originX, originY, originZ;  // MC block the positions are relative to
  std::uint32_t batchCount;
  std::uint32_t vertexCount;
};

struct RenTexture
{
  std::uint32_t id;  // 1+, referenced by RenBatch::texture
  std::uint32_t width, height;
  std::uint32_t pad;
};

struct RenAvatar
{
  std::uint32_t batchCount;
  std::uint32_t vertexCount;
};

struct RenBatch
{
  std::uint32_t texture;  // 0: the block/item atlas, else a RenTexture id
  std::uint32_t first;    // first vertex
  std::uint32_t count;    // vertices (multiple of 3)
  std::uint32_t flags;    // bit0: translucent (blended, after the solid pass; casts no shadow)
};

struct RenAtlas
{
  std::uint32_t width, height;
};

struct RenSection
{
  std::int32_t  sx, sy, sz;   // section coords (16-block cubes)
  std::uint32_t vertexCount;  // multiple of 3
};

struct RenVertex
{
  float         x, y, z;  // MC coords relative to the section origin (sx*16, sy*16, sz*16)
  float         u, v;     // atlas UV
  std::uint32_t color;    // RGBA8 (tint * ambient occlusion; Minecraft's fixed face shading is left out)
  std::uint32_t light;    // low byte: block light 0-15, next byte: sky light 0-15
  std::uint32_t flags;    // bit0: cutout (alpha test), bit1: translucent,
                          // bits 4-6: face normal as MC Direction ordinal + 1 (0 = none: lit without a normal)
};
static_assert(sizeof(RenVertex) == 32);

struct InputEvent
{
  std::uint16_t type;
  std::uint16_t code;
  std::int32_t  a;
  std::int32_t  b;
  std::int32_t  c;
};
static_assert(sizeof(InputEvent) == 16);

// ---- collision ring @0x20000 (host produces, MC consumes) -----------------------------
inline constexpr std::uint64_t kColRingHeadOff = 0x00;  // u64 total bytes written
inline constexpr std::uint64_t kColRingTailOff = 0x40;  // u64 total bytes consumed
inline constexpr std::uint64_t kColRingDataOff = 0x80;
inline constexpr std::uint64_t kColRingDataBytes = kCollisionRingBytes - kColRingDataOff;

enum ColType : std::uint32_t
{
  kColPad = 0,
  kColClear = 1,   // payload: u32 epoch
  kColRegion = 2,  // payload: ColRegion + ColBlock[count]
  kColTris = 3,    // payload: ColRegion (count = triangles) + ColTri[count]; sent before kColRegion
};

	enum ColTriFlags : std::uint32_t
	{
		kTriStairHelper = 1u << 0,
		kTriDiggable = 1u << 1,
		kTriGhost = 1u << 2,
		kTriTerrain = 1u << 3,
	};
	inline constexpr std::uint32_t kTriMaterialShift = 8;

struct ColTri
{
  float         v[9];
  std::uint32_t flags;
};
static_assert(sizeof(ColTri) == 40);

struct ColMsgHeader
{
  std::uint32_t type;
  std::uint32_t payloadBytes;
};

struct ColRegion
{
  std::int32_t  minX, minY, minZ;
  std::int32_t  maxX, maxY, maxZ;
  std::uint32_t epoch;
  std::uint32_t count;
};
static_assert(sizeof(ColRegion) == 32);

struct ColBlock
{
  std::int32_t  x, y, z;
  std::uint32_t pad;
  std::uint64_t bits[8];
};
static_assert(sizeof(ColBlock) == 80);

}
