#!/usr/bin/env python3
"""fake_guest.py — a stand-in GUEST (the "body" side) for testing passthrough with NO game.

The guest owns the body: it reads the host pose (SkyState, via the container's seqlock), pulls
the host's collision geometry out of the collision ring, integrates its own player with simple
gravity + step-up, collides against that geometry, and reports events (hit / death) back into
the event ring.  It also drains the host->guest input ring (a Space press = jump).

It exercises the three hazards the real passthrough project hit (see the GTA-V knowledge note):
  a) heartbeat timeout : if the host dies, the guest freezes safely (no crash, no error spam)
  b) epoch invalidation: after a host restart (new epoch) the OLD session's seq/pose/teleport
                         must be discarded — the guest must NOT teleport or move through stale
                         geometry
  c) >50deg collision  : a wall steeper than the walkable-slope limit must act as a solid wall

Layout comes only from `layout_from_schema.py` (generated from v0-schema/schema.yaml).

    python fake_guest.py --link /tmp/pt.bin --seconds 6 --trace out.jsonl
"""
from __future__ import annotations

import argparse
import ctypes
import json
import math
import struct
import time

import layout_from_schema as L
from fake_host import (P, MAP_BYTES, map_open, ring_drain_bytes, ring_drain_input,
                       seqlock_read, FLOOR_Y, PLAYER_R, PLAYER_H, STEP_H, MAX_SLOPE_DEG,
                       HEARTBEAT_TIMEOUT_MS, DT)

GRAVITY = -20.0
WALK_SPEED = 3.0          # blocks/s, the guest walks along +X
JUMP_V = 7.0
DEATH_Y = -20.0

MC_N = ctypes.sizeof(P.McState)
SKY_N = ctypes.sizeof(P.SKYState)


# ------------------------------------------------------------------------------ geometry
def _tri_normal(v):
    ax, ay, az, bx, by, bz, cx, cy, cz = v
    ux, uy, uz = bx - ax, by - ay, bz - az
    wx, wy, wz = cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx
    ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / ln, ny / ln, nz / ln


def slope_deg(n):
    """Angle of a surface from horizontal, in degrees (0 = flat floor)."""
    c = min(1.0, abs(n[1]))
    return math.degrees(math.acos(c))


def point_in_tri_xz(px, pz, v):
    def side(ax, az, bx, bz):
        return (bx - ax) * (pz - az) - (bz - az) * (px - ax)
    d1 = side(v[0], v[2], v[3], v[5])
    d2 = side(v[3], v[5], v[6], v[8])
    d3 = side(v[6], v[8], v[0], v[2])
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


class Geometry:
    """What the guest built from the host's collision stream."""

    def __init__(self):
        self.epoch = None
        self.walkable = []     # (verts, normal) with slope <= MAX_SLOPE_DEG
        self.walls = []        # (x0, x1, y0, y1, z0, z1) for steeper surfaces
        self.wall_slope = None

    def ingest(self, typ, body):
        if typ == P.kColClear:
            self.epoch = struct.unpack_from("<I", body, 0)[0]
            self.walkable.clear()
            self.walls.clear()
        elif typ == P.kColTris:
            v = struct.unpack("<9fI", body)
            verts, n = v[:9], _tri_normal(v[:9])
            ang = slope_deg(n)
            if ang <= MAX_SLOPE_DEG:
                self.walkable.append((verts, n))
            else:
                xs = (verts[0], verts[3], verts[6])
                ys = (verts[1], verts[4], verts[7])
                zs = (verts[2], verts[5], verts[8])
                self.walls.append((min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
                if self.wall_slope is None:
                    self.wall_slope = round(ang, 3)

    def floor_y(self, x, z):
        best = None
        for verts, n in self.walkable:
            if abs(n[1]) < 1e-6 or not point_in_tri_xz(x, z, verts):
                continue
            vy = verts[1] - (n[0] * (x - verts[0]) + n[2] * (z - verts[2])) / n[1]
            best = vy if best is None else max(best, vy)
        return best


def resolve_axis(x, y, z, axis, delta, walls, blocked):
    """Axis-separated AABB resolution with step-up (Minecraft-style)."""
    if delta == 0.0:
        return x, y, z
    nx = x + (delta if axis == "x" else 0.0)
    nz = z + (delta if axis == "z" else 0.0)
    for (ax0, ax1, ay0, ay1, az0, az1) in walls:
        if not (nx + PLAYER_R > ax0 and nx - PLAYER_R < ax1):
            continue
        if not (nz + PLAYER_R > az0 and nz - PLAYER_R < az1):
            continue
        if not (y + PLAYER_H > ay0 and y < ay1):
            continue
        if (ay1 - y) <= STEP_H:                 # low enough to step up
            y = ay1
            continue
        blocked.append(True)
        if axis == "x":
            nx = (ax0 - PLAYER_R) if delta > 0 else (ax1 + PLAYER_R)
        else:
            nz = (az0 - PLAYER_R) if delta > 0 else (az1 + PLAYER_R)
    return nx, y, nz


# ------------------------------------------------------------------------------ run
def run(link_path, seconds, trace_path, stop=None):
    m = map_open(link_path, MAP_BYTES, create=False)
    base = (ctypes.c_uint8 * MAP_BYTES).from_buffer(m)
    hdr = P.Header.from_buffer(base, P.kOffHeader)
    st = P.SKYState.from_buffer(base, P.kOffSkyState)
    mc = P.McState.from_buffer(base, P.kOffMcState)

    x, y, z = 0.0, FLOOR_Y + 1.0, 0.5
    vy = 0.0
    on_ground = False
    jump_pending = False

    geom = Geometry()
    epoch_valid = True
    last_epoch = None
    applied_teleport = None
    host_seq_last = None
    holdoff = 0
    session_discards = 0

    frozen = False
    events = 0
    died = hit_reported = False
    trace = open(trace_path, "w", encoding="utf-8")
    summary = {"frozen_ticks": 0, "epoch_invalid_ticks": 0, "teleports": 0,
               "jumps": 0, "blocked_ticks": 0, "max_tick_dx": 0.0, "ticks": 0}
    start = time.time()

    def on_input(ev):
        nonlocal jump_pending
        if ev.type == P.kInKey and ev.code == 32:      # Space
            jump_pending = True

    while True:
        now = time.time() - start
        if seconds and now >= seconds:
            break
        if stop is not None and stop.is_set():
            break
        summary["ticks"] += 1

        host_beat = hdr.skyrimHeartbeatMs
        now_ms = int(time.time() * 1000)
        host_alive = bool(host_beat) and (now_ms - host_beat) < HEARTBEAT_TIMEOUT_MS

        # keep our own heartbeat ticking even while frozen, so *we* don't look dead
        hdr.mcHeartbeatMs = now_ms & 0xFFFFFFFFFFFFFFFF

        rec = {"t": round(now, 3), "host_alive": host_alive, "frozen": frozen,
               "epoch_valid": epoch_valid, "epoch": geom.epoch, "x": round(x, 3),
               "y": round(y, 3), "z": round(z, 3), "vy": round(vy, 3),
               "host_seq": host_seq_last, "blocked": False, "on_ground": on_ground,
               "teleported": False, "jumped": False, "event": None}

        if not host_alive:
            # ---- (a) heartbeat timeout: freeze safely, do nothing, keep only heartbeating
            frozen = True
            summary["frozen_ticks"] += 1
            trace.write(json.dumps(rec) + "\n")
            time.sleep(DT)
            continue
        frozen = False

        # ---- pull fresh collision geometry (host -> guest)
        ring_drain_bytes(m, P.kOffCollisionRing, P.kColRingDataBytes, geom.ingest)

        # ---- seqlock-read the host pose
        blob = seqlock_read(st, SKY_N)
        snap = P.SKYState.from_buffer_copy(blob) if blob else None

        # ---- (b) epoch / seq invalidation: a restart is a NEW session
        if snap is not None:
            cur_epoch, cur_seq, tseq = snap.collisionEpoch, snap.seq, snap.teleportSeq
            if last_epoch is None:                      # first contact: join the session
                last_epoch = cur_epoch
            else:
                regressed = host_seq_last is not None and cur_seq < host_seq_last
                if cur_epoch != last_epoch or regressed:
                    # a restart / new session: DISCARD the old session's seq, pose and teleport
                    if epoch_valid:
                        session_discards += 1
                    epoch_valid = False
                    holdoff = 12
                    last_epoch = cur_epoch
            host_seq_last = cur_seq
            if not epoch_valid:
                holdoff -= 1
                if holdoff <= 0 and geom.epoch == cur_epoch:
                    # the new session's geometry has arrived: re-adopt WITHOUT teleporting
                    epoch_valid = True
                    applied_teleport = tseq
            elif tseq != applied_teleport:
                # a legitimate host teleport (same session): follow it
                x, y, z = snap.posX, snap.posY, snap.posZ
                applied_teleport = tseq
                vy = 0.0
                rec["teleported"] = True
                summary["teleports"] += 1
        if not epoch_valid:
            summary["epoch_invalid_ticks"] += 1

        # ---- host -> guest input (jump)
        if epoch_valid:
            ring_drain_input(m, on_input)

        if epoch_valid:
            px0, pz0 = x, z
            vy += GRAVITY * DT
            if jump_pending and on_ground:
                vy = JUMP_V
                rec["jumped"] = True
                summary["jumps"] += 1
            jump_pending = False

            blocked = []
            x, y, z = resolve_axis(x, y, z, "x", WALK_SPEED * DT, geom.walls, blocked)
            x, y, z = resolve_axis(x, y, z, "z", 0.0, geom.walls, blocked)

            y += vy * DT
            fy = geom.floor_y(x, z)
            if fy is not None and y <= fy and vy <= 0:
                y, vy, on_ground = fy, 0.0, True
            else:
                on_ground = False

            summary["max_tick_dx"] = max(summary["max_tick_dx"], abs(x - px0))
            rec["blocked"] = bool(blocked)
            if blocked:
                summary["blocked_ticks"] += 1
                if not hit_reported:
                    emit_event(m, P.kEvHitActor, 200.0, 0, 0, 0, 0)
                    hit_reported = True
                    rec["event"] = "hit"
            if y < DEATH_Y and not died:
                emit_event(m, P.kEvPlayerDied)
                died = True
                rec["event"] = "died"

            # publish McState via the same seqlock discipline
            mc.seq = (mc.seq + 1) | 1
            mc.flags = P.kMcInWorld | (P.kMcOnGround if on_ground else 0)
            mc.x, mc.y, mc.z = x, y, z
            mc.eyeHeight = 1.62
            mc.teleportAck = applied_teleport or 0
            mc.frameCounter = (mc.frameCounter + 1) & 0xFFFFFFFFFFFFFFFF
            mc.seq = (mc.seq + 1) & ~1

        rec.update({"x": round(x, 3), "y": round(y, 3), "z": round(z, 3),
                    "epoch_valid": epoch_valid, "epoch": geom.epoch,
                    "on_ground": on_ground, "vy": round(vy, 3),
                    "discards": session_discards})
        trace.write(json.dumps(rec) + "\n")
        time.sleep(DT)

    trace.close()
    summary["wall_slope_deg"] = geom.wall_slope
    summary["session_discards"] = session_discards
    summary["final_x"] = round(x, 3)
    summary["final_y"] = round(y, 3)
    with open(trace_path + ".summary", "w", encoding="utf-8") as f:
        json.dump(summary, f)
    return summary


def emit_event(buf, typ, a=0.0, b=0.0, c=0.0, d=0.0, flags=0):
    ev = P.McEvent()
    ev.type, ev.formId, ev.a, ev.b, ev.c, ev.d, ev.flags, ev.weapon = \
        typ, 0, a, b, c, d, flags, 0
    head = struct.unpack_from("<Q", buf, P.kOffEventRing + P.kEventRingHeadOff)[0]
    pos = head % P.kEventRingEntries
    off = P.kOffEventRing + 0x80 + pos * ctypes.sizeof(P.McEvent)
    buf[off:off + ctypes.sizeof(P.McEvent)] = bytes(ev)
    struct.pack_into("<Q", buf, P.kOffEventRing + P.kEventRingHeadOff, head + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--link", required=True)
    ap.add_argument("--seconds", type=float, default=6.0)
    ap.add_argument("--trace", required=True)
    args = ap.parse_args()
    s = run(args.link, args.seconds, args.trace)
    print(f"fake_guest: done ({json.dumps(s)})")


if __name__ == "__main__":
    main()
