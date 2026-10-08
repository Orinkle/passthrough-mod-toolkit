# demo/ — provenance of the 30-second demo

**Status: DONE.** The terminal block in [`../README.md`](../README.md) shows the
**actual output** of the stub run below — 46 lines, captured verbatim. Nothing here is
invented, and no game, engine or GPU was involved.

## Assets

| Asset | What it is |
|-------|------------|
| `demo.txt` | Verbatim capture of the three-scenario stub run (46 lines). This is what the README embeds (abridged — the full ASCII side view lives here). |
| `demo_trace.json` | The recorded bridge trace the renderer replays. |

## Canonical source (this folder is a snapshot)

The demo is produced by the **unified stubs**, which live one level up and are the
single source of truth:

```
../stubs/
  layout_from_schema.py   # schema.yaml -> ctypes layout (the only source of byte offsets)
  fake_host.py            # host stub: pose (seqlock) / collision geometry / input ring / event ring
  fake_guest.py           # guest stub: kinematic integration + step-up + collision + events
  run_demo.py             # runs scenarios a/b/c, prints PASS/FAIL summary
  render_demo.py          # renders demo_trace.json into the deterministic terminal transcript
  negative_control.py     # disables each guard in turn -> exactly the matching scenario flips to FAIL
```

## How to regenerate

```bash
PY=python3
$PY ../stubs/run_demo.py        # the three scenarios themselves
$PY ../stubs/render_demo.py     # the terminal transcript embedded in the README
$PY ../stubs/negative_control.py  # falsification: break a guard, watch one scenario fail
```

## What the three scenarios prove

| Scenario | Guard being exercised |
|---|---|
| `a` heartbeat timeout | Host dies → guest **freezes safely** instead of crashing or spinning on stale data. |
| `b` epoch invalidation | Host restarts (epoch bump) → late packets from the **old session are discarded**; no teleport, no wall-clip. |
| `c` steep wall | A >50° AABB is presented as **a wall, not a ramp** — the guest cannot climb or cross it. |

## Evidence tier

`measured (scripted stub run)` — **not** an on-hardware playtest. Both processes are
Python; the shared-memory layout is itself generated from `../schema/schema.yaml`,
which is the same definition the multi-language backends are generated from.

The reference project's own notes are blunt about why this path matters —
*"The fake host and fake GTA let most of the work happen before the 125 GB game finished
installing."*
