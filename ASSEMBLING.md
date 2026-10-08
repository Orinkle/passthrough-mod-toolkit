# ASSEMBLING.md — turning the working tree into the published repo

The work happened in a lab tree (`passthrough-lab/03-复现路线/…`). The repo you push has a
flatter layout. This file is the recipe: **the mapping, the link rewrites, and the things
that must NOT ship.**

## Target layout

```
<repo root>/
├── README.md                 ← v3-repo-draft/README.md
├── README.zh-CN.md           ← v3-repo-draft/README.zh-CN.md
├── LICENSE                   ← v3-repo-draft/LICENSE      ⚠️ replace <YOUR NAME>
├── ASSEMBLING.md             ← this file
├── RELEASE_CHECKLIST.md      ← v3-repo-draft/RELEASE_CHECKLIST.md
├── NAME.md                   ← v3-repo-draft/NAME.md      (repo-name decision notes)
├── demo/                     ← v3-repo-draft/demo/
├── examples/                 ← v3-repo-draft/examples/
├── schema/                   ← 03-复现路线/v0-schema/
├── params/                   ← 03-复现路线/v0-params/
├── ptgen/                    ← 03-复现路线/v1-ptgen/
├── stubs/                    ← 03-复现路线/v1-stubs/
├── mcp/                      ← 03-复现路线/v2-mcp/
└── headers/                  ← NEW — the two MIT reference protocol headers
    ├── SkyCraft/protocol/skycraft_protocol.h
    ├── FalloutCraft/skycraft_protocol.h
    └── NOTICE.md
```

## 1. Copy the pieces

```bash
LAB=~/WorkBuddy/2026-10-07-20-05-03/passthrough-lab
SRC=$LAB/03-复现路线
REPO=/path/to/new/repo && mkdir -p "$REPO" && cd "$REPO"

cp -r "$SRC/v3-repo-draft/." .
cp -r "$SRC/v0-schema"  schema
cp -r "$SRC/v0-params"  params
cp -r "$SRC/v1-ptgen"   ptgen
cp -r "$SRC/v1-stubs"   stubs
cp -r "$SRC/v2-mcp"     mcp

# reference headers — MIT ones only, see step 3
mkdir -p headers/SkyCraft/protocol headers/FalloutCraft
cp "$LAB/90-源码/SkyCraft/protocol/skycraft_protocol.h" headers/SkyCraft/protocol/
cp "$LAB/90-源码/FalloutCraft/skycraft_protocol.h"      headers/FalloutCraft/
```

## 2. Rewrite the cross-directory links

The draft was written *inside* `03-复现路线/`, so it links to siblings as `../v0-schema/`.
After assembly those become `schema/`, `params/`, `stubs/`:

```bash
cd "$REPO"
sed -i 's#](\.\./v0-schema/#](schema/#g; s#`\.\./v0-schema/#`schema/#g' README.md README.zh-CN.md demo/README.md examples/README.md RELEASE_CHECKLIST.md
sed -i 's#](\.\./v0-params/#](params/#g; s#`\.\./v0-params/#`params/#g' README.md demo/README.md examples/README.md
sed -i 's#`\.\./v1-stubs/#`stubs/#g;  s#`\.\./v2-mcp/#`mcp/#g'        demo/README.md
sed -i 's#(\.\./demo/#(demo/#g' README.md README.zh-CN.md

# eyeball whatever is left — nothing should point above the repo root
grep -rn '\.\./' --include='*.md' .
```

## 3. What must NOT ship

| Exclude | Why |
|---|---|
| `mcp/.work/` | Scratch copies made during development. (It may contain a 0-byte file the filesystem refuses to unlink — harmless, just don't copy it.) |
| `schema/generated/` | Regenerable output. Drop it, or keep it as `examples/generated/` — the Quickstart regenerates it. |
| **`ValCraft/protocol/valcraft_protocol.h`** | **That repo carries no LICENSE.** Not redistributed. `schema/verify_roundtrip.py` detects its absence and prints a `SKIPPED` line instead of failing — that is by design. |
| Anything from `90-源码/ValCraft/` | Same reason. |
| Game files, SKSE / ReShade / ScriptHookV binaries | Red lines R1–R6 in `RELEASE_CHECKLIST.md`. |

## 4. `headers/NOTICE.md` (must ship alongside the two headers)

```markdown
# Third-party reference headers

Redistributed **unmodified** so that `schema/verify_roundtrip.py` can be re-run by
anyone. These are not our code.

| File | Source | License |
|---|---|---|
| `SkyCraft/protocol/skycraft_protocol.h` | chasmlol/SkyCraft | MIT |
| `FalloutCraft/skycraft_protocol.h` | zeyvu/FalloutCraft | MIT (derived from SkyCraft) |

<paste the full MIT text + the original copyright line from each repo's LICENSE>

**Not included:** `ValCraft/protocol/valcraft_protocol.h`. That repository ships **no
LICENSE**, so it is read-only to this project and is not redistributed. To run that
line anyway, point `PT_HEADERS_DIR` at your own copy:

    PT_HEADERS_DIR=/path/to/dir python schema/verify_roundtrip.py
```

## 5. Before you push

- [ ] `LICENSE` — replace `<YOUR NAME>` with a real name or handle.
- [ ] `NAME.md` — pick the repo name, the description and the topics.
- [ ] `python schema/verify_roundtrip.py` → **PASS**, run from the *assembled* tree (the ValCraft line shows `SKIPPED`).
- [ ] `python stubs/run_demo.py` → a/b/c all PASS.
- [ ] Run every command block in `RELEASE_CHECKLIST.md`.
- [ ] `pip install ./ptgen && ptgen --help` works from the assembled tree.
- [ ] `git add` only by explicit path — never `git add -A` from the lab tree.

## Known integration gaps (honest list)

- **Only `schema/verify_roundtrip.py` was verified in *both* layouts** (development tree and assembled repo). `mcp/`, `stubs/` and `params/` were developed against lab-relative paths and were **not** re-run from the assembled layout.
- **The C# backend was never compiled** — no `dotnet` in the build environment. Rust and Python backends were compiler/runtime-checked; Java was structurally diffed against a real generated file, not compiled.
- **Nothing has ever been run against a real game.** Every behavioural number in this repo comes from scripted stubs.
