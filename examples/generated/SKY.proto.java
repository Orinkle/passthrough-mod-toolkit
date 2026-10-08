package skycraft.proto;

/**
 * Generated passthrough protocol constants (schema.yaml + vocabulary).
 * Field offsets are ABI-equivalent to the C++ fixed blocks; all multi-byte values little-endian.
 */
public final class Proto {
	private Proto() {}

	public static final int MAGIC = 0x43594b53;
	public static final int VERSION = 11;
	public static final String MAPPING_NAME = "Local\\SkyCraft_v1";
	public static final double UNITS_PER_BLOCK = 70.0;

	public static final int OFF_HEADER = 0;
	public static final int OFF_SKY_STATE = 0x100;
	public static final int OFF_VAL_STATE = 0x100;
	public static final int OFF_MC_STATE = 0x200;
	public static final int OFF_OVERLAY_CTL = 0x300;
	public static final int OFF_OVERLAY_SLOT_HDR = 0x340;
	public static final int OFF_WATER_GRID = 0x400;
	public static final int OFF_INPUT_RING = 0x1000;
	public static final int OFF_COLLISION_RING = 0x20000;
	public static final int COLLISION_RING_BYTES = 0x2000000;
	public static final int OFF_OVERLAY_PIXELS = 0x2020000;
	public static final int MAX_OVERLAY_W = 0xf00;
	public static final int MAX_OVERLAY_H = 0x870;
	public static final int OVERLAY_SLOT_BYTES = 0x1fa4000;
	public static final int OVERLAY_SLOTS = 3;
	public static final int OFF_ACTOR_TABLE = 0x12000;
	public static final int OFF_EVENT_RING = 0x17000;
	public static final int OFF_WORLD_ENTITIES = 0x1c000;
	public static final int OFF_RENDER_RING = 0x7f0c000;
	public static final int RENDER_RING_BYTES = 0x4000000;
	public static final int MAPPING_BYTES = 0xbf0c000;
	public static final int INPUT_RING_ENTRIES = 0x1000;
	public static final int INPUT_RING_HEAD_OFF = 0;
	public static final int INPUT_RING_TAIL_OFF = 64;
	public static final int INPUT_RING_DATA_OFF = 128;
	public static final int EVENT_RING_ENTRIES = 0x200;
	public static final int EVENT_RING_HEAD_OFF = 0;
	public static final int EVENT_RING_TAIL_OFF = 64;
	public static final int EVENT_RING_DATA_OFF = 128;
	public static final int COL_RING_HEAD_OFF = 0;
	public static final int COL_RING_TAIL_OFF = 64;
	public static final int COL_RING_DATA_OFF = 128;
	public static final int COL_RING_DATA_BYTES = 0x1ffff80;
	public static final int REN_RING_HEAD_OFF = 0;
	public static final int REN_RING_TAIL_OFF = 64;
	public static final int REN_RING_DATA_OFF = 128;
	public static final int REN_RING_DATA_BYTES = 0x3ffff80;
	public static final int WATER_GRID_SIZE = 16;
	public static final double NO_WATER = -1e+30;
	public static final int MAX_ACTORS = 0x100;
	public static final int MAX_WORLD_ENTITIES = 160;
	public static final int OVERLAY_DIRTY = 4;

	public static final long WATERGRID_BYTES = 0x410L;
	public static final long WATERGRID_SEQ = 0x0L;
	public static final long WATERGRID_ORIGIN_X = 0x4L;
	public static final long WATERGRID_ORIGIN_Z = 0x8L;
	public static final long WATERGRID_WORLD_ID = 0xcL;
	public static final long WATERGRID_SURFACE = 0x10L;

	public static final long OVERLAYCTL_BYTES = 0x10L;
	public static final long OVERLAYCTL_STATE = 0x0L;
	public static final long OVERLAYCTL_PAD = 0x4L;
	public static final long OVERLAYCTL_FRAMES_PUBLISHED = 0x8L;

	public static final long OVERLAYSLOTHDR_BYTES = 0x40L;
	public static final long OVERLAYSLOTHDR_WIDTH = 0x0L;
	public static final long OVERLAYSLOTHDR_HEIGHT = 0x4L;
	public static final long OVERLAYSLOTHDR_FLAGS = 0x8L;
	public static final long OVERLAYSLOTHDR_PAD = 0xcL;
	public static final long OVERLAYSLOTHDR_FRAME_ID = 0x10L;
	public static final long OVERLAYSLOTHDR_RESERVED = 0x18L;

	public static final long ACTORRECORD_BYTES = 0x40L;
	public static final long ACTORRECORD_FORM_ID = 0x0L;
	public static final long ACTORRECORD_FLAGS = 0x4L;
	public static final long ACTORRECORD_X = 0x8L;
	public static final long ACTORRECORD_Y = 0xcL;
	public static final long ACTORRECORD_Z = 0x10L;
	public static final long ACTORRECORD_YAW = 0x14L;
	public static final long ACTORRECORD_WIDTH = 0x18L;
	public static final long ACTORRECORD_HEIGHT = 0x1cL;
	public static final long ACTORRECORD_HEALTH_FRAC = 0x20L;
	public static final long ACTORRECORD_LEVEL = 0x24L;
	public static final long ACTORRECORD_PAD = 0x26L;
	public static final long ACTORRECORD_NAME = 0x28L;

	public static final long ACTORTABLE_BYTES = 0x4040L;
	public static final long ACTORTABLE_SEQ = 0x0L;
	public static final long ACTORTABLE_COUNT = 0x4L;
	public static final long ACTORTABLE_PAD = 0x8L;
	public static final long ACTORTABLE_ACTORS = 0x40L;

	public static final long MCEVENT_BYTES = 0x20L;
	public static final long MCEVENT_TYPE = 0x0L;
	public static final long MCEVENT_FORM_ID = 0x4L;
	public static final long MCEVENT_A = 0x8L;
	public static final long MCEVENT_B = 0xcL;
	public static final long MCEVENT_C = 0x10L;
	public static final long MCEVENT_D = 0x14L;
	public static final long MCEVENT_FLAGS = 0x18L;
	public static final long MCEVENT_WEAPON = 0x1cL;

	public static final long WORLDENTITY_BYTES = 0x60L;
	public static final long WORLDENTITY_KIND = 0x0L;
	public static final long WORLDENTITY_ID = 0x4L;
	public static final long WORLDENTITY_X = 0x8L;
	public static final long WORLDENTITY_Y = 0xcL;
	public static final long WORLDENTITY_Z = 0x10L;
	public static final long WORLDENTITY_YAW = 0x14L;
	public static final long WORLDENTITY_PITCH = 0x18L;
	public static final long WORLDENTITY_SCALE = 0x1cL;
	public static final long WORLDENTITY_EXT = 0x20L;
	public static final long WORLDENTITY_UV = 0x2cL;
	public static final long WORLDENTITY_TINT = 0x5cL;

	public static final long WORLDENTITIES_BYTES = 0x3c40L;
	public static final long WORLDENTITIES_SEQ = 0x0L;
	public static final long WORLDENTITIES_COUNT = 0x4L;
	public static final long WORLDENTITIES_HAS_SELECTION = 0x8L;
	public static final long WORLDENTITIES_SEL_MIN = 0xcL;
	public static final long WORLDENTITIES_SEL_MAX = 0x18L;
	public static final long WORLDENTITIES_PAD = 0x24L;
	public static final long WORLDENTITIES_ENTITIES = 0x40L;

	public static final long RENSOLIDS_BYTES = 0x10L;
	public static final long RENSOLIDS_SX = 0x0L;
	public static final long RENSOLIDS_SY = 0x4L;
	public static final long RENSOLIDS_SZ = 0x8L;
	public static final long RENSOLIDS_COUNT = 0xcL;

	public static final long RENDUG_BYTES = 0x18L;
	public static final long RENDUG_SX = 0x0L;
	public static final long RENDUG_SY = 0x4L;
	public static final long RENDUG_SZ = 0x8L;
	public static final long RENDUG_COUNT = 0xcL;
	public static final long RENDUG_WORLD_ID = 0x10L;
	public static final long RENDUG_PAD = 0x14L;

	public static final long RENLIGHTS_BYTES = 0x10L;
	public static final long RENLIGHTS_SX = 0x0L;
	public static final long RENLIGHTS_SY = 0x4L;
	public static final long RENLIGHTS_SZ = 0x8L;
	public static final long RENLIGHTS_COUNT = 0xcL;

	public static final long RENLIGHT_BYTES = 0x8L;
	public static final long RENLIGHT_X = 0x0L;
	public static final long RENLIGHT_Y = 0x1L;
	public static final long RENLIGHT_Z = 0x2L;
	public static final long RENLIGHT_LEVEL = 0x3L;
	public static final long RENLIGHT_COLOR = 0x4L;

	public static final long RENATLASREGION_BYTES = 0x10L;
	public static final long RENATLASREGION_X = 0x0L;
	public static final long RENATLASREGION_Y = 0x4L;
	public static final long RENATLASREGION_WIDTH = 0x8L;
	public static final long RENATLASREGION_HEIGHT = 0xcL;

	public static final long RENSCENE_BYTES = 0x20L;
	public static final long RENSCENE_ORIGIN_X = 0x0L;
	public static final long RENSCENE_ORIGIN_Y = 0x8L;
	public static final long RENSCENE_ORIGIN_Z = 0x10L;
	public static final long RENSCENE_BATCH_COUNT = 0x18L;
	public static final long RENSCENE_VERTEX_COUNT = 0x1cL;

	public static final long RENTEXTURE_BYTES = 0x10L;
	public static final long RENTEXTURE_ID = 0x0L;
	public static final long RENTEXTURE_WIDTH = 0x4L;
	public static final long RENTEXTURE_HEIGHT = 0x8L;
	public static final long RENTEXTURE_PAD = 0xcL;

	public static final long RENAVATAR_BYTES = 0x8L;
	public static final long RENAVATAR_BATCH_COUNT = 0x0L;
	public static final long RENAVATAR_VERTEX_COUNT = 0x4L;

	public static final long RENBATCH_BYTES = 0x10L;
	public static final long RENBATCH_TEXTURE = 0x0L;
	public static final long RENBATCH_FIRST = 0x4L;
	public static final long RENBATCH_COUNT = 0x8L;
	public static final long RENBATCH_FLAGS = 0xcL;

	public static final long RENATLAS_BYTES = 0x8L;
	public static final long RENATLAS_WIDTH = 0x0L;
	public static final long RENATLAS_HEIGHT = 0x4L;

	public static final long RENSECTION_BYTES = 0x10L;
	public static final long RENSECTION_SX = 0x0L;
	public static final long RENSECTION_SY = 0x4L;
	public static final long RENSECTION_SZ = 0x8L;
	public static final long RENSECTION_VERTEX_COUNT = 0xcL;

	public static final long RENVERTEX_BYTES = 0x20L;
	public static final long RENVERTEX_X = 0x0L;
	public static final long RENVERTEX_Y = 0x4L;
	public static final long RENVERTEX_Z = 0x8L;
	public static final long RENVERTEX_U = 0xcL;
	public static final long RENVERTEX_V = 0x10L;
	public static final long RENVERTEX_COLOR = 0x14L;
	public static final long RENVERTEX_LIGHT = 0x18L;
	public static final long RENVERTEX_FLAGS = 0x1cL;

	public static final long INPUTEVENT_BYTES = 0x10L;
	public static final long INPUTEVENT_TYPE = 0x0L;
	public static final long INPUTEVENT_CODE = 0x2L;
	public static final long INPUTEVENT_A = 0x4L;
	public static final long INPUTEVENT_B = 0x8L;
	public static final long INPUTEVENT_C = 0xcL;

	public static final long COLTRI_BYTES = 0x28L;
	public static final long COLTRI_V = 0x0L;
	public static final long COLTRI_FLAGS = 0x24L;

	public static final long COLMSGHEADER_BYTES = 0x8L;
	public static final long COLMSGHEADER_TYPE = 0x0L;
	public static final long COLMSGHEADER_PAYLOAD_BYTES = 0x4L;

	public static final long COLREGION_BYTES = 0x20L;
	public static final long COLREGION_MIN_X = 0x0L;
	public static final long COLREGION_MIN_Y = 0x4L;
	public static final long COLREGION_MIN_Z = 0x8L;
	public static final long COLREGION_MAX_X = 0xcL;
	public static final long COLREGION_MAX_Y = 0x10L;
	public static final long COLREGION_MAX_Z = 0x14L;
	public static final long COLREGION_EPOCH = 0x18L;
	public static final long COLREGION_COUNT = 0x1cL;

	public static final long COLBLOCK_BYTES = 0x50L;
	public static final long COLBLOCK_X = 0x0L;
	public static final long COLBLOCK_Y = 0x4L;
	public static final long COLBLOCK_Z = 0x8L;
	public static final long COLBLOCK_PAD = 0xcL;
	public static final long COLBLOCK_BITS = 0x10L;

	public static final long HEADER_BYTES = 0x20L;
	public static final long HEADER_MAGIC = 0x0L;
	public static final long HEADER_VERSION = 0x4L;
	public static final long HEADER_SKYRIM_PID = 0x8L;
	public static final long HEADER_MC_PID = 0xcL;
	public static final long HEADER_SKYRIM_HEARTBEAT_MS = 0x10L;
	public static final long HEADER_MC_HEARTBEAT_MS = 0x18L;

	public static final long SKYSTATE_BYTES = 0x40L;
	public static final long SKYSTATE_SEQ = 0x0L;
	public static final long SKYSTATE_FLAGS = 0x4L;
	public static final long SKYSTATE_WORLD_ID = 0x8L;
	public static final long SKYSTATE_COLLISION_EPOCH = 0xcL;
	public static final long SKYSTATE_POS_X = 0x10L;
	public static final long SKYSTATE_POS_Y = 0x18L;
	public static final long SKYSTATE_POS_Z = 0x20L;
	public static final long SKYSTATE_YAW = 0x28L;
	public static final long SKYSTATE_PITCH = 0x2cL;
	public static final long SKYSTATE_TELEPORT_SEQ = 0x30L;
	public static final long SKYSTATE_VIEWPORT_W = 0x34L;
	public static final long SKYSTATE_VIEWPORT_H = 0x38L;
	public static final long SKYSTATE_GAME_HOUR = 0x3cL;

	public static final long MCSTATE_BYTES = 0xc8L;
	public static final long MCSTATE_SEQ = 0x0L;
	public static final long MCSTATE_FLAGS = 0x4L;
	public static final long MCSTATE_X = 0x8L;
	public static final long MCSTATE_Y = 0x10L;
	public static final long MCSTATE_Z = 0x18L;
	public static final long MCSTATE_YAW = 0x20L;
	public static final long MCSTATE_PITCH = 0x24L;
	public static final long MCSTATE_EYE_HEIGHT = 0x28L;
	public static final long MCSTATE_SENSITIVITY = 0x2cL;
	public static final long MCSTATE_TELEPORT_ACK = 0x30L;
	public static final long MCSTATE_GUI_SCALE = 0x34L;
	public static final long MCSTATE_FRAME_COUNTER = 0x38L;
	public static final long MCSTATE_FOV_DEG = 0x40L;
	public static final long MCSTATE_BOB_PHASE = 0x44L;
	public static final long MCSTATE_BOB_AMOUNT = 0x48L;
	public static final long MCSTATE_PAD4_C = 0x4cL;
	public static final long MCSTATE_EYE_X = 0x50L;
	public static final long MCSTATE_EYE_Y = 0x58L;
	public static final long MCSTATE_EYE_Z = 0x60L;
	public static final long MCSTATE_TICK_QPC = 0x68L;
	public static final long MCSTATE_PREV_X = 0x70L;
	public static final long MCSTATE_PREV_Y = 0x78L;
	public static final long MCSTATE_PREV_Z = 0x80L;
	public static final long MCSTATE_CUR_X = 0x88L;
	public static final long MCSTATE_CUR_Y = 0x90L;
	public static final long MCSTATE_CUR_Z = 0x98L;
	public static final long MCSTATE_TICK_EYE_O = 0xa0L;
	public static final long MCSTATE_TICK_EYE = 0xa4L;
	public static final long MCSTATE_WALK_DIST_O = 0xa8L;
	public static final long MCSTATE_WALK_DIST = 0xacL;
	public static final long MCSTATE_BOB_O = 0xb0L;
	public static final long MCSTATE_BOB = 0xb4L;
	public static final long MCSTATE_TICK_MS = 0xb8L;
	public static final long MCSTATE_TICK_PAD = 0xbcL;
	public static final long MCSTATE_CAMERA_MODE = 0xc0L;
	public static final long MCSTATE_CAMERA_DISTANCE = 0xc4L;

	public static final int kActorHostile = 1;
	public static final int kActorDead = 2;
	public static final int kActorEssential = 4;
	public static final int kActorInCombat = 8;
	public static final int kWeArrow = 1;
	public static final int kWeItem = 2;
	public static final int kWeTrident = 3;
	public static final int kWeBlock = 4;
	public static final int kWeCrack = 5;
	public static final int kWeShadow = 6;
	public static final int kPartNone = 0;
	public static final int kPartHead = 1;
	public static final int kPartBody = 2;
	public static final int kPartRightArm = 3;
	public static final int kPartLeftArm = 4;
	public static final int kPartRightLeg = 5;
	public static final int kPartLeftLeg = 6;
	public static final int kPartCount = 7;
	public static final int kLightSteady = 0;
	public static final int kLightFlame = 1;
	public static final int kLightLava = 2;
	public static final int kHazardNone = 0;
	public static final int kHazardFire = 1;
	public static final int kHazardLava = 2;
	public static final int kHazardMagma = 3;
	public static final int kColPad = 0;
	public static final int kColClear = 1;
	public static final int kColRegion = 2;
	public static final int kColTris = 3;
	public static final int kSkyInGame = 1;
	public static final int kSkyMenuOpen = 2;
	public static final int kSkyLoading = 4;
	public static final int kMcInWorld = 1;
	public static final int kMcScreenOpen = 2;
	public static final int kMcOnGround = 4;
	public static final int kMcSneaking = 8;
	public static final int kMcSprinting = 16;
	public static final int kMcDead = 32;
	public static final int kMcSwimming = 64;
	public static final int kMcFlying = 128;
	public static final int kInKey = 1;
	public static final int kInMouseButton = 2;
	public static final int kInScroll = 3;
	public static final int kInCursor = 4;
	public static final int kInText = 5;
	public static final int kInReleaseAll = 6;
	public static final int kInHurt = 7;
	public static final int kInOpenMenu = 8;
	public static final int kHurtBlockedInSkyrim = 1;
	public static final int kHurtPowerAttack = 2;
	public static final int kEvHitActor = 1;
	public static final int kEvPlayerDied = 2;
	public static final int kEvExplosion = 3;
	public static final int kEvArrowStuck = 4;
	public static final int kEvSkillUse = 5;
	public static final int kRenPad = 0;
	public static final int kRenAtlas = 1;
	public static final int kRenSection = 2;
	public static final int kRenClearAll = 3;
	public static final int kRenTexture = 4;
	public static final int kRenAvatar = 5;
	public static final int kRenScene = 6;
	public static final int kRenAtlasRegion = 7;
	public static final int kRenLights = 8;
	public static final int kRenSolids = 10;
	public static final int kRenDug = 11;
	public static final int kRenRagdoll = 9;
	public static final int kTriStairHelper = 1;
	public static final int kTriDiggable = 2;
	public static final int kTriGhost = 4;
	public static final int kTriTerrain = 8;
	public static final int kTriMaterialShift = 8;
	public static final int kDigNone = 0;
	public static final int kDigGrass = 1;
	public static final int kDigDirt = 2;
	public static final int kDigStone = 3;
	public static final int kDigCobble = 4;
	public static final int kDigSnow = 5;
	public static final int kDigIce = 6;
	public static final int kDigSand = 7;
	public static final int kDigGravel = 8;
	public static final int kDigMud = 9;
	public static final int kDigOakLog = 10;
	public static final int kDigSpruceLog = 11;
	public static final int kDigBirchLog = 12;
	public static final int kDigPlanks = 13;
	public static final int kDigMetal = 14;
	public static final int kDigGlass = 15;
	public static final int kDigOrganic = 16;
	public static final int kDigCloth = 17;
	public static final int kDigBone = 18;
	public static final int kDigWeb = 19;
	public static final int kDigAsh = 20;
	public static final int kDigBedrock = 21;

	// seqlock read: even, stable seq; returns false while a writer is mid-update.
	public static boolean seqlockRead(java.nio.ByteBuffer buf, long seqOff) {
		int s0 = buf.getInt((int) seqOff);
		if ((s0 & 1) != 0) return false;
		int s1 = buf.getInt((int) seqOff);
		return s0 == s1;
	}

	// SPSC ring: power-of-two data region; head/tail are u64 at headOff/tailOff.
	public static int ringProduce(java.nio.ByteBuffer buf, long headOff,
			long dataOff, long dataBytes, byte[] payload) {
		long head = buf.getLong((int) headOff);
		long pos = head & (dataBytes - 1);
		buf.position((int) (dataOff + pos));
		buf.put(payload);
		buf.putLong((int) headOff, head + payload.length);
		return payload.length;
	}
}
