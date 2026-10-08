# AGENTS.md — read this first if you are an agent

## What this repo is

**passthrough-mod-toolkit** scaffolds *passthrough mods*: two complete games running as
two separate processes, bridged over local IPC (shared memory / WebSocket). You fill in a
per-host vocabulary in `schema/schema.yaml`; the toolkit generates the fixed bones of the
bridge. It is a **scaffold, not a finished mod** — the host-side game plugin is always
yours to write and measure.

## Entry commands (run from the repo root)

```bash
python -m pip install ./ptgen     # the only installable package (dep: PyYAML only)
ptgen --schema schema/schema.yaml --lang cpp --host SKY --out out/   # codegen, 5 languages
python schema/verify_roundtrip.py # proof: real MIT headers round-trip, structural diff = 0
python stubs/run_demo.py          # 3 bridge-guard scenarios, no game needed (a/b/c PASS)
python mcp/server.py              # MCP server, zero-dependency JSON-RPC over stdio
```

## MCP tools exposed by `mcp/server.py`

`pt_schema_validate` · `pt_schema_describe` · `pt_param_lookup` · `pt_stub_run` · `pt_scaffold`
— each carries a self-description; call `tools/list` for schemas.

## Repo map

| Path | What it is |
|---|---|
| `schema/` | Two-layer schema (fixed container + per-host vocabulary) + round-trip proof |
| `params/` | 35 parameters with evidence tiers; `param_lookup.py --host skyrim --color red` |
| `ptgen/` | The code generator (pip-installable, PyYAML only) |
| `stubs/` | Fake host + fake guest; `negative_control.py` falsifies each guard |
| `mcp/` | Zero-dependency MCP server (stdlib JSON-RPC) |
| `headers/` | MIT reference protocol headers (SkyCraft, FalloutCraft) + `NOTICE.md` |
| `demo/` `examples/` | Verbatim demo capture; generated header samples |

## What NOT to use this for

- A ready-to-play mod. There isn't one. The host-side plugin (piece ② of 5) is hand-written
  per game build.
- Single-game modding — use that game's normal mod stack.
- Anything involving online play, anti-cheat, or EULA circumvention. Hard rule; all samples
  are treated as single-player.

## Parameters that MUST be measured on real hardware

Every 🔴 entry in `params/params.yaml` has `verified_on_hardware: false`. Never trust a
copied value for: yaw/pitch expressions, camera/pose matrices, coordinate mapping, `yOffset`
calibration, depth convention (reversed-Z vs normal), collision probe ceilings, reprojection
tuning. State this to the user before generating host-side code.

## License & redistribution constraints

- Repo license: MIT. Third-party MIT headers in `headers/` are redistributed unmodified
  with `headers/NOTICE.md` — keep it.
- **The ValCraft protocol header is deliberately absent** (upstream repo has no LICENSE).
  `verify_roundtrip.py` prints a `SKIPPED` line for it — that is by design, not a failure.
  To run that line with your own copy: `PT_HEADERS_DIR=/path/to/dir python schema/verify_roundtrip.py`.
- Never bundle game files or loader binaries (SKSE / F4SE / ScriptHookV / ReShade).
- Evidence discipline: claims are tagged `measured` / `reported` / `inferred`.
  **Nothing in this repo has on-hardware verification.** Do not repeat any number without
  its tier tag, and never upgrade a tag.

## Working on this repo

- `RELEASE_CHECKLIST.md` — run every grep in it before tagging a release (red lines R1–R6).
- `ASSEMBLING.md` — how the published tree is produced from the development tree
  (`assemble.sh` reproduces it end-to-end).
- Do not add a test suite unprompted: the maintainer's stated position is that the three
  commands above are the assembly integrity check, and that is enough.
