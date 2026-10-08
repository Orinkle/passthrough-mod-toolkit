using System;
using System.Runtime.InteropServices;

namespace skycraft.proto
{
    // Generated passthrough protocol (schema.yaml + vocabulary).
    // Structs are LayoutKind.Sequential (natural alignment, ABI-equivalent to C++).
    public static class Proto
    {
        public const uint Magic = 1129925459;
        public const uint Version = 11;
        public const string MappingName = "Local\\SkyCraft_v1";
        public const double UnitsPerBlock = 70.0;
        public const int kOffHeader = 0;
        public const int kOffSkyState = 256;
        public const int kOffValState = 256;
        public const int kOffMcState = 512;
        public const int kOffOverlayCtl = 768;
        public const int kOffOverlaySlotHdr = 832;
        public const int kOffWaterGrid = 1024;
        public const int kOffInputRing = 4096;
        public const int kOffCollisionRing = 131072;
        public const int kCollisionRingBytes = 33554432;
        public const int kOffOverlayPixels = 33685504;
        public const int kMaxOverlayW = 3840;
        public const int kMaxOverlayH = 2160;
        public const int kOverlaySlotBytes = 33177600;
        public const int kOverlaySlots = 3;
        public const int kOffActorTable = 73728;
        public const int kOffEventRing = 94208;
        public const int kOffWorldEntities = 114688;
        public const int kOffRenderRing = 133218304;
        public const int kRenderRingBytes = 67108864;
        public const int kMappingBytes = 200327168;
        public const int kInputRingEntries = 4096;
        public const int kInputRingHeadOff = 0;
        public const int kInputRingTailOff = 64;
        public const int kInputRingDataOff = 128;
        public const int kEventRingEntries = 512;
        public const int kEventRingHeadOff = 0;
        public const int kEventRingTailOff = 64;
        public const int kEventRingDataOff = 128;
        public const int kColRingHeadOff = 0;
        public const int kColRingTailOff = 64;
        public const int kColRingDataOff = 128;
        public const int kColRingDataBytes = 33554304;
        public const int kRenRingHeadOff = 0;
        public const int kRenRingTailOff = 64;
        public const int kRenRingDataOff = 128;
        public const int kRenRingDataBytes = 67108736;
        public const int kWaterGridSize = 16;
        public const double kNoWater = -1e+30;
        public const int kMaxActors = 256;
        public const int kMaxWorldEntities = 160;
        public const int kOverlayDirty = 4;
        public const int kMaxOverlaySlots = 3;

    public enum ActorFlags : uint
    {
        kActorHostile = 1,
        kActorDead = 2,
        kActorEssential = 4,
        kActorInCombat = 8
    }

    public enum WorldEntityKind : uint
    {
        kWeArrow = 1,
        kWeItem = 2,
        kWeTrident = 3,
        kWeBlock = 4,
        kWeCrack = 5,
        kWeShadow = 6
    }

    public enum RagdollPart : uint
    {
        kPartNone = 0,
        kPartHead = 1,
        kPartBody = 2,
        kPartRightArm = 3,
        kPartLeftArm = 4,
        kPartRightLeg = 5,
        kPartLeftLeg = 6,
        kPartCount = 7
    }

    public enum LightKind : byte
    {
        kLightSteady = 0,
        kLightFlame = 1,
        kLightLava = 2
    }

    public enum BlockHazard : byte
    {
        kHazardNone = 0,
        kHazardFire = 1,
        kHazardLava = 2,
        kHazardMagma = 3
    }

    public enum ColType : uint
    {
        kColPad = 0,
        kColClear = 1,
        kColRegion = 2,
        kColTris = 3
    }

    [Flags]
    public enum SkyFlags : uint
    {
        kSkyInGame = 1,
        kSkyMenuOpen = 2,
        kSkyLoading = 4
    }

    [Flags]
    public enum McFlags : uint
    {
        kMcInWorld = 1,
        kMcScreenOpen = 2,
        kMcOnGround = 4,
        kMcSneaking = 8,
        kMcSprinting = 16,
        kMcDead = 32,
        kMcSwimming = 64,
        kMcFlying = 128
    }

    public enum InputType : ushort
    {
        kInKey = 1,
        kInMouseButton = 2,
        kInScroll = 3,
        kInCursor = 4,
        kInText = 5,
        kInReleaseAll = 6,
        kInHurt = 7,
        kInOpenMenu = 8
    }

    public enum HurtFlags : uint
    {
        kHurtBlockedInSkyrim = 1,
        kHurtPowerAttack = 2
    }

    public enum McEventType : uint
    {
        kEvHitActor = 1,
        kEvPlayerDied = 2,
        kEvExplosion = 3,
        kEvArrowStuck = 4,
        kEvSkillUse = 5
    }

    public enum RenType : uint
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
        kRenRagdoll = 9
    }

    [Flags]
    public enum ColTriFlags : uint
    {
        kTriStairHelper = 1,
        kTriDiggable = 2,
        kTriGhost = 4,
        kTriTerrain = 8
    }

    public enum ColTriShift : uint
    {
        kTriMaterialShift = 8
    }

    public enum DigMaterial : byte
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
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct WaterGrid
    {
    public uint seq;
    public int originX;
    public int originZ;
    public uint worldId;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)] public float[] surface;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct OverlayCtl
    {
    public uint state;
    public uint pad;
    public ulong framesPublished;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct OverlaySlotHdr
    {
    public uint width;
    public uint height;
    public uint flags;
    public uint pad;
    public ulong frameId;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=40)] public byte[] reserved;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct ActorRecord
    {
    public uint formId;
    public uint flags;
    public float x;
    public float y;
    public float z;
    public float yaw;
    public float width;
    public float height;
    public float healthFrac;
    public ushort level;
    public ushort pad;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=24)] public byte[] name;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct ActorTable
    {
    public uint seq;
    public uint count;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=56)] public byte[] pad;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=256)] public ActorRecord[] actors;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct McEvent
    {
    public uint type;
    public uint formId;
    public float a;
    public float b;
    public float c;
    public float d;
    public uint flags;
    public uint weapon;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct WorldEntity
    {
    public uint kind;
    public uint id;
    public float x;
    public float y;
    public float z;
    public float yaw;
    public float pitch;
    public float scale;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=3)] public float[] ext;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=3)] public float[] uv;
    public uint tint;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct WorldEntities
    {
    public uint seq;
    public uint count;
    public uint hasSelection;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=3)] public float[] selMin;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=3)] public float[] selMax;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=28)] public byte[] pad;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=160)] public WorldEntity[] entities;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenSolids
    {
    public int sx;
    public int sy;
    public int sz;
    public uint count;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenDug
    {
    public int sx;
    public int sy;
    public int sz;
    public uint count;
    public uint worldId;
    public uint pad;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenLights
    {
    public int sx;
    public int sy;
    public int sz;
    public uint count;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenLight
    {
    public byte x;
    public byte y;
    public byte z;
    public byte level;
    public uint color;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenAtlasRegion
    {
    public uint x;
    public uint y;
    public uint width;
    public uint height;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenScene
    {
    public double originX;
    public double originY;
    public double originZ;
    public uint batchCount;
    public uint vertexCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenTexture
    {
    public uint id;
    public uint width;
    public uint height;
    public uint pad;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenAvatar
    {
    public uint batchCount;
    public uint vertexCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenBatch
    {
    public uint texture;
    public uint first;
    public uint count;
    public uint flags;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenAtlas
    {
    public uint width;
    public uint height;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenSection
    {
    public int sx;
    public int sy;
    public int sz;
    public uint vertexCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RenVertex
    {
    public float x;
    public float y;
    public float z;
    public float u;
    public float v;
    public uint color;
    public uint light;
    public uint flags;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct InputEvent
    {
    public ushort type;
    public ushort code;
    public int a;
    public int b;
    public int c;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct ColTri
    {
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=9)] public float[] v;
    public uint flags;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct ColMsgHeader
    {
    public uint type;
    public uint payloadBytes;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct ColRegion
    {
    public int minX;
    public int minY;
    public int minZ;
    public int maxX;
    public int maxY;
    public int maxZ;
    public uint epoch;
    public uint count;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct ColBlock
    {
    public int x;
    public int y;
    public int z;
    public uint pad;
    [MarshalAs(UnmanagedType.ByValArray, SizeConst=8)] public ulong[] bits;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct Header
    {
    public uint magic;
    public uint version;
    public uint skyrimPid;
    public uint mcPid;
    public ulong skyrimHeartbeatMs;
    public ulong mcHeartbeatMs;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct SkyState
    {
    public uint seq;
    public uint flags;
    public uint worldId;
    public uint collisionEpoch;
    public double posX;
    public double posY;
    public double posZ;
    public float yaw;
    public float pitch;
    public uint teleportSeq;
    public uint viewportW;
    public uint viewportH;
    public float gameHour;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct McState
    {
    public uint seq;
    public uint flags;
    public double x;
    public double y;
    public double z;
    public float yaw;
    public float pitch;
    public float eyeHeight;
    public float sensitivity;
    public uint teleportAck;
    public uint guiScale;
    public ulong frameCounter;
    public float fovDeg;
    public float bobPhase;
    public float bobAmount;
    public uint pad4C;
    public double eyeX;
    public double eyeY;
    public double eyeZ;
    public long tickQpc;
    public double prevX;
    public double prevY;
    public double prevZ;
    public double curX;
    public double curY;
    public double curZ;
    public float tickEyeO;
    public float tickEye;
    public float walkDistO;
    public float walkDist;
    public float bobO;
    public float bob;
    public float tickMs;
    public uint tickPad;
    public uint cameraMode;
    public float cameraDistance;
    }

    public static void CheckLayout()
    {
        if (Marshal.SizeOf<WaterGrid>() != 1040) throw new Exception("size mismatch WaterGrid");
        if (Marshal.SizeOf<OverlayCtl>() != 16) throw new Exception("size mismatch OverlayCtl");
        if (Marshal.SizeOf<OverlaySlotHdr>() != 64) throw new Exception("size mismatch OverlaySlotHdr");
        if (Marshal.SizeOf<ActorRecord>() != 64) throw new Exception("size mismatch ActorRecord");
        if (Marshal.SizeOf<ActorTable>() != 16448) throw new Exception("size mismatch ActorTable");
        if (Marshal.SizeOf<McEvent>() != 32) throw new Exception("size mismatch McEvent");
        if (Marshal.SizeOf<WorldEntity>() != 96) throw new Exception("size mismatch WorldEntity");
        if (Marshal.SizeOf<WorldEntities>() != 15424) throw new Exception("size mismatch WorldEntities");
        if (Marshal.SizeOf<RenSolids>() != 16) throw new Exception("size mismatch RenSolids");
        if (Marshal.SizeOf<RenDug>() != 24) throw new Exception("size mismatch RenDug");
        if (Marshal.SizeOf<RenLights>() != 16) throw new Exception("size mismatch RenLights");
        if (Marshal.SizeOf<RenLight>() != 8) throw new Exception("size mismatch RenLight");
        if (Marshal.SizeOf<RenAtlasRegion>() != 16) throw new Exception("size mismatch RenAtlasRegion");
        if (Marshal.SizeOf<RenScene>() != 32) throw new Exception("size mismatch RenScene");
        if (Marshal.SizeOf<RenTexture>() != 16) throw new Exception("size mismatch RenTexture");
        if (Marshal.SizeOf<RenAvatar>() != 8) throw new Exception("size mismatch RenAvatar");
        if (Marshal.SizeOf<RenBatch>() != 16) throw new Exception("size mismatch RenBatch");
        if (Marshal.SizeOf<RenAtlas>() != 8) throw new Exception("size mismatch RenAtlas");
        if (Marshal.SizeOf<RenSection>() != 16) throw new Exception("size mismatch RenSection");
        if (Marshal.SizeOf<RenVertex>() != 32) throw new Exception("size mismatch RenVertex");
        if (Marshal.SizeOf<InputEvent>() != 16) throw new Exception("size mismatch InputEvent");
        if (Marshal.SizeOf<ColTri>() != 40) throw new Exception("size mismatch ColTri");
        if (Marshal.SizeOf<ColMsgHeader>() != 8) throw new Exception("size mismatch ColMsgHeader");
        if (Marshal.SizeOf<ColRegion>() != 32) throw new Exception("size mismatch ColRegion");
        if (Marshal.SizeOf<ColBlock>() != 80) throw new Exception("size mismatch ColBlock");
        if (Marshal.SizeOf<Header>() != 32) throw new Exception("size mismatch Header");
        if (Marshal.SizeOf<SkyState>() != 64) throw new Exception("size mismatch SkyState");
        if (Marshal.SizeOf<McState>() != 200) throw new Exception("size mismatch McState");
    }
}
}
