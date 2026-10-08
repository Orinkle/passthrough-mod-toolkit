#!/usr/bin/env python3
"""fake_host.py — a stand-in HOST (the "world" side) for testing passthrough with NO game.

It plays the host's half of the wire protocol, exactly as declared by `schema.yaml`:
  * publishes the host player pose every tick (SkyState, written as a seqlock: odd seq ->
    write -> even seq), so a guest can follow the camera;
  * streams collision geometry into the collision ring (a flat floor, and — with --wall — one
    vertical (90 deg) AABB wall, i.e. far steeper than the 50 deg walkable limit);
  * pushes one host->guest input (Space, a jump) into the input ring;
  * drains the guest->host event ring and prints what the guest reported.

Every byte layout, offset and constant comes from `layout_from_schema.py`, which is *generated*
from `v0-schema/schema.yaml`.  This file contains no hand-written struct field or offset.

Transport: a **shared-memory mapping**.  On Windows the schema calls it a named mapping
(`Local\\SkyCraft_v1`).  On Linux the same thing is a MAP_SHARED mapping over a file — all
processes see the same pages, and the seqlock / SPSC-ring head+tail are plain in-place u64s, so
no serialisation is needed.  We back it with a file (not /dev/shm): /dev/shm here is 10 MB and
the collision ring alone is 32 MB.  The mapping is sized from the schema constant that covers
every region this stub touches.

    python fake_host.py --link /tmp/pt.bin --seconds 30 [--wall] [--epoch 1] [--events ev.jsonl]
"""
from __future__ import annotations

import argparse
import ctypes
import json
import mmap
import os
import struct
import sys
import time

import layout_from_schema as L

P = L.generate("SKY")[1]

# ------------------------------------------------------------------ world geometry (blocks)
FLOOR_Y = 0.0
WALL_X = 8.0            # the wall is the plane x = 8
WALL_Z0, WALL_Z1 = -3.0, 3.0
WALL_H = 6.0           # 6 blocks tall: far above any step height -> un-climbable
HOST_SPEED = 3.0       # blocks/s the host "walks" along +X
PLAYER_R = 0.3
PLAYER_H = 1.8
STEP_H = 0.6
MAX_SLOPE_DEG = 50.0   # steeper than this is a wall, not walkable ground

HEARTBEAT_TIMEOUT_MS = 1500
TICK_HZ = 60.0
DT = 1.0 / TICK_HZ

# The mapping only needs to cover the regions this stub uses; the largest is the collision ring.
MAP_BYTES = P.kOffCollisionRing + P.kCollisionRingBytes


# ------------------------------------------------------------------------------- transport
def map_open(path: str, size: int, create: bool) -> mmap.mmap:
    flags = os.O_RDWR | (os.O_CREAT if create else 0)
    fd = os.open(path, flags, 0o600)
    try:
        if create:
            os.ftruncate(fd, size)
        m = mmap.mmap(fd, size, access=mmap.ACCESS_WRITE)
    finally:
        os.close(fd)
    return m


def ring_produce_bytes(buf, base, data_bytes, payload: bytes):
    """Collision/render rings: head/tail are *byte* counters; messages are 8-byte aligned.

    `payload` is the WHOLE message: the 8-byte ColMsgHeader (type, payloadBytes) followed by
    the body.  The on-wire `payloadBytes` counts only the body, so callers pass len(body).
    """
    head = struct.unpack_from("<Q", buf, base + P.kColRingHeadOff)[0]
    total = (len(payload) + 7) & ~7
    pos = head % data_bytes
    if pos + total > data_bytes:                      # wrap: write a 0-length pad message
        struct.pack_into("<II", buf, base + 0x80 + pos, 0, 0)
        head += data_bytes - pos
        pos = 0
    typ, plen = struct.unpack_from("<II", payload, 0)
    struct.pack_into("<II", buf, base + 0x80 + pos, typ, plen)
    body = payload[8:]
    buf[base + 0x80 + pos + 8: base + 0x80 + pos + 8 + len(body)] = body
    head += total
    struct.pack_into("<Q", buf, base + P.kColRingHeadOff, head)


def _col_msg(typ: int, payload: bytes) -> bytes:
    return struct.pack("<II", typ, len(payload)) + payload


def ring_drain_bytes(buf, base, data_bytes, consume):
    """Consume a byte-counter ring (collision/render): yields (type, body)."""
    head = struct.unpack_from("<Q", buf, base + P.kColRingHeadOff)[0]
    tail = struct.unpack_from("<Q", buf, base + P.kColRingTailOff)[0]
    while tail < head:
        pos = tail % data_bytes
        typ, plen = struct.unpack_from("<II", buf, base + 0x80 + pos)
        if typ == 0:                                     # wrap pad
            tail += data_bytes - pos
            continue
        body = bytes(buf[base + 0x80 + pos + 8: base + 0x80 + pos + 8 + plen])
        consume(typ, body)
        tail += (8 + plen + 7) & ~7
    struct.pack_into("<Q", buf, base + P.kColRingTailOff, tail)


def ring_drain_input(buf, consume):
    """Consume the entry-counter input ring (host -> guest)."""
    size = ctypes.sizeof(P.InputEvent)
    head = struct.unpack_from("<Q", buf, P.kOffInputRing + P.kInputRingHeadOff)[0]
    tail = struct.unpack_from("<Q", buf, P.kOffInputRing + P.kInputRingTailOff)[0]
    while tail < head:
        pos = tail % P.kInputRingEntries
        off = P.kOffInputRing + 0x80 + pos * size
        consume(P.InputEvent.from_buffer_copy(buf[off:off + size]))
        tail += 1
    struct.pack_into("<Q", buf, P.kOffInputRing + P.kInputRingTailOff, tail)


def seqlock_read(obj, nbytes: int):
    """Read a seqlock struct: retry until the sequence is even and unchanged across the copy."""
    for _ in range(100000):
        s1 = obj.seq
        if s1 & 1:
            continue
        blob = ctypes.string_at(ctypes.addressof(obj), nbytes)
        if obj.seq == s1:
            return blob
    return None


def write_collision(buf, epoch: int, with_wall: bool):
    ring_produce_bytes(buf, P.kOffCollisionRing, P.kColRingDataBytes,
                       _col_msg(P.kColClear, struct.pack("<I", epoch)))
    # floor: two big horizontal triangles at y = FLOOR_Y (normal +Y -> 0 deg, walkable)
    y = FLOOR_Y
    fx0, fx1, fz0, fz1 = -50.0, 50.0, -50.0, 50.0
    tris = [(fx0, y, fz0, fx1, y, fz0, fx1, y, fz1),
            (fx0, y, fz0, fx1, y, fz1, fx0, y, fz1)]
    if with_wall:
        # vertical wall at x = WALL_X (normal ~ +/-X -> 90 deg, NOT walkable)
        tris += [(WALL_X, 0.0, WALL_Z0, WALL_X, WALL_H, WALL_Z0, WALL_X, WALL_H, WALL_Z1),
                 (WALL_X, 0.0, WALL_Z0, WALL_X, WALL_H, WALL_Z1, WALL_X, 0.0, WALL_Z1)]
    for t in tris:
        ring_produce_bytes(buf, P.kOffCollisionRing, P.kColRingDataBytes,
                           _col_msg(P.kColTris, struct.pack("<9fI", *t, 0)))


def push_input(buf, typ: int, code: int, a=0, b=0, c=0):
    """Input ring: head/tail are *entry* counters (one InputEvent per entry)."""
    head = struct.unpack_from("<Q", buf, P.kOffInputRing + P.kInputRingHeadOff)[0]
    pos = head % P.kInputRingEntries
    off = P.kOffInputRing + 0x80 + pos * ctypes.sizeof(P.InputEvent)
    struct.pack_into("<HHiii", buf, off, typ, code, a, b, c)
    struct.pack_into("<Q", buf, P.kOffInputRing + P.kInputRingHeadOff, head + 1)


def drain_events(buf, sink):
    """Event ring: head/tail are *entry* counters (one McEvent per entry)."""
    head = struct.unpack_from("<Q", buf, P.kOffEventRing + P.kEventRingHeadOff)[0]
    tail = struct.unpack_from("<Q", buf, P.kOffEventRing + P.kEventRingTailOff)[0]
    while tail < head:
        pos = tail % P.kEventRingEntries
        off = P.kOffEventRing + 0x80 + pos * ctypes.sizeof(P.McEvent)
        ev = P.McEvent.from_buffer_copy(buf[off:off + ctypes.sizeof(P.McEvent)])
        sink({"type": ev.type, "formId": ev.formId,
              "a": round(ev.a, 3), "b": round(ev.b, 3),
              "c": round(ev.c, 3), "d": round(ev.d, 3), "flags": ev.flags})
        tail += 1
    struct.pack_into("<Q", buf, P.kOffEventRing + P.kEventRingTailOff, tail)


def publish_pose(st, now, epoch):
    """Seqlock publish: seq odd while mutating, even (=2k) when stable."""
    st.seq = (st.seq + 1) | 1
    st.flags = P.kSkyInGame
    st.worldId = 1
    st.collisionEpoch = epoch
    st.posX = 4.0 + (now * HOST_SPEED) % 20.0
    st.posY = FLOOR_Y + 1.0
    st.posZ = 0.5
    st.yaw = (now * 40.0) % 360.0          # keep turning the head
    st.pitch = 10.0
    st.teleportSeq = epoch                  # a restart (new epoch) is a new teleport request
    st.viewportW, st.viewportH = 1280, 720
    st.gameHour = 12.0
    st.seq = (st.seq + 1) & ~1


def run(link_path, seconds, epoch, with_wall, events_path=None, stop=None, create=True):
    m = map_open(link_path, MAP_BYTES, create)
    base = (ctypes.c_uint8 * MAP_BYTES).from_buffer(m)
    hdr = P.Header.from_buffer(base, P.kOffHeader)
    st = P.SKYState.from_buffer(base, P.kOffSkyState)

    # A host process owns the link header + host state: reset only 0x0..0x300 every start
    # (this is also what makes a restart visible to the guest as a seq/epoch change).
    m[0:P.kOffMcState] = b"\x00" * P.kOffMcState
    hdr.magic = P.MAGIC
    hdr.version = P.VERSION
    hdr.skyrimPid = os.getpid()
    st.collisionEpoch = epoch
    st.seq = 0

    write_collision(m, epoch, with_wall)

    events = []
    sink = events.append
    if events_path:
        def sink(e):
            events.append(e)
            events_path.write(json.dumps(e) + "\n")

    start = time.time()
    n_input = 0
    while True:
        now = time.time() - start
        if seconds and now >= seconds:
            break
        if stop is not None and stop.is_set():
            break
        hdr.skyrimHeartbeatMs = int(time.time() * 1000) & 0xFFFFFFFFFFFFFFFF
        publish_pose(st, now, epoch)
        if n_input == 0 and now >= 0.4:
            push_input(m, P.kInKey, 32)      # Space down (keycode 32)
            n_input = 1
        elif n_input == 1 and now >= 0.55:
            push_input(m, P.kInKey, 32)      # a second entry, exercises multi-entry drain
            n_input = 2
        drain_events(m, sink)
        time.sleep(DT)
    return events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--link", required=True)
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--epoch", type=int, default=1)
    ap.add_argument("--wall", action="store_true")
    ap.add_argument("--events", default=None)
    ap.add_argument("--create", dest="create", action="store_true", default=True)
    ap.add_argument("--no-create", dest="create", action="store_false")
    args = ap.parse_args()
    evf = open(args.events, "w", encoding="utf-8") if args.events else None
    try:
        ev = run(args.link, args.seconds, args.epoch, args.wall, evf, create=args.create)
    finally:
        if evf:
            evf.close()
    print(f"fake_host: done (epoch={args.epoch}, wall={args.wall}, saw {len(ev)} guest events)")


if __name__ == "__main__":
    main()
