// Generated passthrough protocol (schema.yaml + vocabulary).
// #[repr(C)] structs; multi-byte values are little-endian.
// Field names mirror the C++ header even when they are Rust keywords (raw idents).
#![allow(non_upper_case_globals, non_camel_case_types, non_snake_case)]

pub const MAGIC: u32 = 1129925459;
pub const VERSION: u32 = 11;
pub const MAPPING_NAME: &str = "Local\\SkyCraft_v1";
pub const UNITS_PER_BLOCK: f64 = 70.0;
pub const kOffHeader: i32 = 0;
pub const kOffSkyState: i32 = 256;
pub const kOffValState: i32 = 256;
pub const kOffMcState: i32 = 512;
pub const kOffOverlayCtl: i32 = 768;
pub const kOffOverlaySlotHdr: i32 = 832;
pub const kOffWaterGrid: i32 = 1024;
pub const kOffInputRing: i32 = 4096;
pub const kOffCollisionRing: i32 = 131072;
pub const kCollisionRingBytes: i32 = 33554432;
pub const kOffOverlayPixels: i32 = 33685504;
pub const kMaxOverlayW: i32 = 3840;
pub const kMaxOverlayH: i32 = 2160;
pub const kOverlaySlotBytes: i32 = 33177600;
pub const kOverlaySlots: i32 = 3;
pub const kOffActorTable: i32 = 73728;
pub const kOffEventRing: i32 = 94208;
pub const kOffWorldEntities: i32 = 114688;
pub const kOffRenderRing: i32 = 133218304;
pub const kRenderRingBytes: i32 = 67108864;
pub const kMappingBytes: i32 = 200327168;
pub const kInputRingEntries: i32 = 4096;
pub const kInputRingHeadOff: i32 = 0;
pub const kInputRingTailOff: i32 = 64;
pub const kInputRingDataOff: i32 = 128;
pub const kEventRingEntries: i32 = 512;
pub const kEventRingHeadOff: i32 = 0;
pub const kEventRingTailOff: i32 = 64;
pub const kEventRingDataOff: i32 = 128;
pub const kColRingHeadOff: i32 = 0;
pub const kColRingTailOff: i32 = 64;
pub const kColRingDataOff: i32 = 128;
pub const kColRingDataBytes: i32 = 33554304;
pub const kRenRingHeadOff: i32 = 0;
pub const kRenRingTailOff: i32 = 64;
pub const kRenRingDataOff: i32 = 128;
pub const kRenRingDataBytes: i32 = 67108736;
pub const kWaterGridSize: i32 = 16;
pub const kNoWater: f64 = -1e+30;
pub const kMaxActors: i32 = 256;
pub const kMaxWorldEntities: i32 = 160;
pub const kOverlayDirty: i32 = 4;
pub const kMaxOverlaySlots: i32 = 3;

pub mod actorflags {
    pub const kActorHostile: u32 = 1;
    pub const kActorDead: u32 = 2;
    pub const kActorEssential: u32 = 4;
    pub const kActorInCombat: u32 = 8;
}

pub mod worldentitykind {
    pub const kWeArrow: u32 = 1;
    pub const kWeItem: u32 = 2;
    pub const kWeTrident: u32 = 3;
    pub const kWeBlock: u32 = 4;
    pub const kWeCrack: u32 = 5;
    pub const kWeShadow: u32 = 6;
}

pub mod ragdollpart {
    pub const kPartNone: u32 = 0;
    pub const kPartHead: u32 = 1;
    pub const kPartBody: u32 = 2;
    pub const kPartRightArm: u32 = 3;
    pub const kPartLeftArm: u32 = 4;
    pub const kPartRightLeg: u32 = 5;
    pub const kPartLeftLeg: u32 = 6;
    pub const kPartCount: u32 = 7;
}

pub mod lightkind {
    pub const kLightSteady: u8 = 0;
    pub const kLightFlame: u8 = 1;
    pub const kLightLava: u8 = 2;
}

pub mod blockhazard {
    pub const kHazardNone: u8 = 0;
    pub const kHazardFire: u8 = 1;
    pub const kHazardLava: u8 = 2;
    pub const kHazardMagma: u8 = 3;
}

pub mod coltype {
    pub const kColPad: u32 = 0;
    pub const kColClear: u32 = 1;
    pub const kColRegion: u32 = 2;
    pub const kColTris: u32 = 3;
}

pub mod skyflags {
    pub const kSkyInGame: u32 = 1;
    pub const kSkyMenuOpen: u32 = 2;
    pub const kSkyLoading: u32 = 4;
}

pub mod mcflags {
    pub const kMcInWorld: u32 = 1;
    pub const kMcScreenOpen: u32 = 2;
    pub const kMcOnGround: u32 = 4;
    pub const kMcSneaking: u32 = 8;
    pub const kMcSprinting: u32 = 16;
    pub const kMcDead: u32 = 32;
    pub const kMcSwimming: u32 = 64;
    pub const kMcFlying: u32 = 128;
}

pub mod inputtype {
    pub const kInKey: u16 = 1;
    pub const kInMouseButton: u16 = 2;
    pub const kInScroll: u16 = 3;
    pub const kInCursor: u16 = 4;
    pub const kInText: u16 = 5;
    pub const kInReleaseAll: u16 = 6;
    pub const kInHurt: u16 = 7;
    pub const kInOpenMenu: u16 = 8;
}

pub mod hurtflags {
    pub const kHurtBlockedInSkyrim: u32 = 1;
    pub const kHurtPowerAttack: u32 = 2;
}

pub mod mceventtype {
    pub const kEvHitActor: u32 = 1;
    pub const kEvPlayerDied: u32 = 2;
    pub const kEvExplosion: u32 = 3;
    pub const kEvArrowStuck: u32 = 4;
    pub const kEvSkillUse: u32 = 5;
}

pub mod rentype {
    pub const kRenPad: u32 = 0;
    pub const kRenAtlas: u32 = 1;
    pub const kRenSection: u32 = 2;
    pub const kRenClearAll: u32 = 3;
    pub const kRenTexture: u32 = 4;
    pub const kRenAvatar: u32 = 5;
    pub const kRenScene: u32 = 6;
    pub const kRenAtlasRegion: u32 = 7;
    pub const kRenLights: u32 = 8;
    pub const kRenSolids: u32 = 10;
    pub const kRenDug: u32 = 11;
    pub const kRenRagdoll: u32 = 9;
}

pub mod coltriflags {
    pub const kTriStairHelper: u32 = 1;
    pub const kTriDiggable: u32 = 2;
    pub const kTriGhost: u32 = 4;
    pub const kTriTerrain: u32 = 8;
}

pub mod coltrishift {
    pub const kTriMaterialShift: u32 = 8;
}

pub mod digmaterial {
    pub const kDigNone: u8 = 0;
    pub const kDigGrass: u8 = 1;
    pub const kDigDirt: u8 = 2;
    pub const kDigStone: u8 = 3;
    pub const kDigCobble: u8 = 4;
    pub const kDigSnow: u8 = 5;
    pub const kDigIce: u8 = 6;
    pub const kDigSand: u8 = 7;
    pub const kDigGravel: u8 = 8;
    pub const kDigMud: u8 = 9;
    pub const kDigOakLog: u8 = 10;
    pub const kDigSpruceLog: u8 = 11;
    pub const kDigBirchLog: u8 = 12;
    pub const kDigPlanks: u8 = 13;
    pub const kDigMetal: u8 = 14;
    pub const kDigGlass: u8 = 15;
    pub const kDigOrganic: u8 = 16;
    pub const kDigCloth: u8 = 17;
    pub const kDigBone: u8 = 18;
    pub const kDigWeb: u8 = 19;
    pub const kDigAsh: u8 = 20;
    pub const kDigBedrock: u8 = 21;
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct WaterGrid {
    pub seq: u32,
    pub originX: i32,
    pub originZ: i32,
    pub worldId: u32,
    pub surface: [f32; 256],
}
const _: () = assert!(std::mem::size_of::<WaterGrid>() == 1040);
const _: () = assert!(std::mem::size_of::<WaterGrid>() <= 3072);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct OverlayCtl {
    pub state: u32,
    pub pad: u32,
    pub framesPublished: u64,
}
const _: () = assert!(std::mem::size_of::<OverlayCtl>() == 16);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct OverlaySlotHdr {
    pub width: u32,
    pub height: u32,
    pub flags: u32,
    pub pad: u32,
    pub frameId: u64,
    pub reserved: [u8; 40],
}
const _: () = assert!(std::mem::size_of::<OverlaySlotHdr>() == 64);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ActorRecord {
    pub formId: u32,
    pub flags: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub yaw: f32,
    pub width: f32,
    pub height: f32,
    pub healthFrac: f32,
    pub level: u16,
    pub pad: u16,
    pub name: [u8; 24],
}
const _: () = assert!(std::mem::size_of::<ActorRecord>() == 64);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ActorTable {
    pub seq: u32,
    pub count: u32,
    pub pad: [u8; 56],
    pub actors: [ActorRecord; 256],
}
const _: () = assert!(std::mem::size_of::<ActorTable>() == 16448);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct McEvent {
    pub r#type: u32,
    pub formId: u32,
    pub a: f32,
    pub b: f32,
    pub c: f32,
    pub d: f32,
    pub flags: u32,
    pub weapon: u32,
}
const _: () = assert!(std::mem::size_of::<McEvent>() == 32);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct WorldEntity {
    pub kind: u32,
    pub id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub yaw: f32,
    pub pitch: f32,
    pub scale: f32,
    pub ext: [f32; 3],
    pub uv: [[f32; 4]; 3],
    pub tint: u32,
}
const _: () = assert!(std::mem::size_of::<WorldEntity>() == 96);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct WorldEntities {
    pub seq: u32,
    pub count: u32,
    pub hasSelection: u32,
    pub selMin: [f32; 3],
    pub selMax: [f32; 3],
    pub pad: [u8; 28],
    pub entities: [WorldEntity; 160],
}
const _: () = assert!(std::mem::size_of::<WorldEntities>() == 15424);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenSolids {
    pub sx: i32,
    pub sy: i32,
    pub sz: i32,
    pub count: u32,
}
const _: () = assert!(std::mem::size_of::<RenSolids>() == 16);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenDug {
    pub sx: i32,
    pub sy: i32,
    pub sz: i32,
    pub count: u32,
    pub worldId: u32,
    pub pad: u32,
}
const _: () = assert!(std::mem::size_of::<RenDug>() == 24);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenLights {
    pub sx: i32,
    pub sy: i32,
    pub sz: i32,
    pub count: u32,
}
const _: () = assert!(std::mem::size_of::<RenLights>() == 16);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenLight {
    pub x: u8,
    pub y: u8,
    pub z: u8,
    pub level: u8,
    pub color: u32,
}
const _: () = assert!(std::mem::size_of::<RenLight>() == 8);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenAtlasRegion {
    pub x: u32,
    pub y: u32,
    pub width: u32,
    pub height: u32,
}
const _: () = assert!(std::mem::size_of::<RenAtlasRegion>() == 16);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenScene {
    pub originX: f64,
    pub originY: f64,
    pub originZ: f64,
    pub batchCount: u32,
    pub vertexCount: u32,
}
const _: () = assert!(std::mem::size_of::<RenScene>() == 32);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenTexture {
    pub id: u32,
    pub width: u32,
    pub height: u32,
    pub pad: u32,
}
const _: () = assert!(std::mem::size_of::<RenTexture>() == 16);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenAvatar {
    pub batchCount: u32,
    pub vertexCount: u32,
}
const _: () = assert!(std::mem::size_of::<RenAvatar>() == 8);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenBatch {
    pub texture: u32,
    pub first: u32,
    pub count: u32,
    pub flags: u32,
}
const _: () = assert!(std::mem::size_of::<RenBatch>() == 16);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenAtlas {
    pub width: u32,
    pub height: u32,
}
const _: () = assert!(std::mem::size_of::<RenAtlas>() == 8);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenSection {
    pub sx: i32,
    pub sy: i32,
    pub sz: i32,
    pub vertexCount: u32,
}
const _: () = assert!(std::mem::size_of::<RenSection>() == 16);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RenVertex {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub u: f32,
    pub v: f32,
    pub color: u32,
    pub light: u32,
    pub flags: u32,
}
const _: () = assert!(std::mem::size_of::<RenVertex>() == 32);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct InputEvent {
    pub r#type: u16,
    pub code: u16,
    pub a: i32,
    pub b: i32,
    pub c: i32,
}
const _: () = assert!(std::mem::size_of::<InputEvent>() == 16);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ColTri {
    pub v: [f32; 9],
    pub flags: u32,
}
const _: () = assert!(std::mem::size_of::<ColTri>() == 40);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ColMsgHeader {
    pub r#type: u32,
    pub payloadBytes: u32,
}
const _: () = assert!(std::mem::size_of::<ColMsgHeader>() == 8);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ColRegion {
    pub minX: i32,
    pub minY: i32,
    pub minZ: i32,
    pub maxX: i32,
    pub maxY: i32,
    pub maxZ: i32,
    pub epoch: u32,
    pub count: u32,
}
const _: () = assert!(std::mem::size_of::<ColRegion>() == 32);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ColBlock {
    pub x: i32,
    pub y: i32,
    pub z: i32,
    pub pad: u32,
    pub bits: [u64; 8],
}
const _: () = assert!(std::mem::size_of::<ColBlock>() == 80);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct Header {
    pub magic: u32,
    pub version: u32,
    pub skyrimPid: u32,
    pub mcPid: u32,
    pub skyrimHeartbeatMs: u64,
    pub mcHeartbeatMs: u64,
}
const _: () = assert!(std::mem::size_of::<Header>() == 32);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct SkyState {
    pub seq: u32,
    pub flags: u32,
    pub worldId: u32,
    pub collisionEpoch: u32,
    pub posX: f64,
    pub posY: f64,
    pub posZ: f64,
    pub yaw: f32,
    pub pitch: f32,
    pub teleportSeq: u32,
    pub viewportW: u32,
    pub viewportH: u32,
    pub gameHour: f32,
}
const _: () = assert!(std::mem::size_of::<SkyState>() == 64);

#[repr(C)]
#[derive(Clone, Copy)]
pub struct McState {
    pub seq: u32,
    pub flags: u32,
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub yaw: f32,
    pub pitch: f32,
    pub eyeHeight: f32,
    pub sensitivity: f32,
    pub teleportAck: u32,
    pub guiScale: u32,
    pub frameCounter: u64,
    pub fovDeg: f32,
    pub bobPhase: f32,
    pub bobAmount: f32,
    pub pad4C: u32,
    pub eyeX: f64,
    pub eyeY: f64,
    pub eyeZ: f64,
    pub tickQpc: i64,
    pub prevX: f64,
    pub prevY: f64,
    pub prevZ: f64,
    pub curX: f64,
    pub curY: f64,
    pub curZ: f64,
    pub tickEyeO: f32,
    pub tickEye: f32,
    pub walkDistO: f32,
    pub walkDist: f32,
    pub bobO: f32,
    pub bob: f32,
    pub tickMs: f32,
    pub tickPad: u32,
    pub cameraMode: u32,
    pub cameraDistance: f32,
}
const _: () = assert!(std::mem::size_of::<McState>() == 200);

// seqlock + SPSC helpers over a &[u8] mapping (offsets from this module).
pub fn seqlock_even(seq: u32) -> bool { seq & 1 == 0 }
pub fn ring_produce(head: u64, data_bytes: u64, n: u64) -> Option<(u64, u64)> {
    let mask = data_bytes - 1;
    if (head & mask) + n > data_bytes { None } else { Some((head & mask, head + n)) }
}
