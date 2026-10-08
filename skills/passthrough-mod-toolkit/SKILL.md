---
name: passthrough-mod-toolkit
description: 用 passthrough-mod-toolkit 脚手架生成 passthrough mod(跨游戏桥联 / 游戏缝合:两个完整游戏作为两个独立进程,经本地 IPC——共享内存 / WebSocket——交换数据)。填一张逐宿主词表(schema.yaml 的 vocabulary),生成五语言(C++ / C# / Java / Rust / Python)共享内存协议绑定、假宿主/假客侧桩、ctypes 内存布局与零依赖 MCP 服务器(5 工具)。当用户想做 passthrough mod、cross-game bridge、two-game mashup、双进程游戏桥、shared memory game bridge,或需要 SKSE / BepInEx / ScriptHookV / Minecraft Fabric 两侧的协议骨架与 IPC 脚手架时使用。本技能只负责指向工具包并给出使用路径;领域知识(五种 mashup pattern)以 mashup-mods 技能为准,诚实边界以仓库 README 的 Honest limits 为准。
description_en: Use the passthrough-mod-toolkit repo to scaffold a passthrough mod — two full games as two separate processes bridged over local IPC (shared memory / WebSocket). Fill a per-host vocabulary sheet (schema.yaml), generate shared-memory protocol bindings in five languages (C++ / C# / Java / Rust / Python), fake-host/fake-guest stubs, a ctypes memory layout, and a zero-dependency MCP server (5 tools). Trigger when the user wants a passthrough mod, cross-game bridge, two-game mashup, two-process game bridge, shared-memory game bridge, or protocol scaffolds for SKSE / BepInEx / ScriptHookV / Minecraft Fabric. This skill only points at the toolkit and gives the usage path; domain knowledge lives in the mashup-mods skill, and hard limits live in the repo README's Honest limits section.
license: MIT
disable: false
---

# passthrough-mod-toolkit — scaffold a two-process game bridge

This skill routes you to the **passthrough-mod-toolkit** repository and its entry points.
It does **not** re-teach passthrough design — for the five mashup patterns and when
passthrough is the right one, load the `mashup-mods` skill. For what the toolkit cannot
do, read the repo's `README.md` → *Honest limits* (it is deliberately unsoftened).

## When this is the right tool

The user wants to **build** a passthrough mod (not just understand one): two games as two
processes, guest owns the body (movement / collision / inventory), host owns the world
(terrain / NPCs / rendering), data exchanged over local IPC. Examples: Minecraft inside
Skyrim (SKSE), inside Valheim (BepInEx), inside GTA V (ScriptHookV), inside Fallout 4 (F4SE).

## Entry commands (repo root)

```bash
python -m pip install ./ptgen     # only installable package; PyYAML is the sole dependency
ptgen --schema schema/schema.yaml --lang cpp --host SKY --out out/   # 5 languages
python schema/verify_roundtrip.py # proof: real MIT headers, structural diff = 0
python stubs/run_demo.py          # 3 bridge-guard scenarios, no game needed
python mcp/server.py              # zero-dep MCP: pt_schema_validate / pt_schema_describe /
                                  # pt_param_lookup / pt_stub_run / pt_scaffold
```

## Usage path

1. Read `schema/schema.yaml` — fixed `container` (never edit per host) + per-host `vocabulary`.
2. Copy an existing host vocabulary (skyrim / gta5) as the template for the new host.
3. Look up every parameter in `params/params.yaml`; anything 🔴 (`verified_on_hardware: false`)
   MUST be measured on the user's real build — say so explicitly, never present a copied
   magic number as trustworthy (yaw/pitch, camera matrices, yOffset, depth convention…).
4. Generate bindings with `ptgen`, then develop game-free against `stubs/`
   (fake host + fake guest run heartbeat / epoch / collision scenarios).
5. Before any release, run every grep in `RELEASE_CHECKLIST.md`.

## Hard constraints (do not soften)

- The toolkit ships a **skeleton**; the host-side plugin is hand-written per game build.
- **Zero on-hardware verification** anywhere in the repo. Keep the
  `measured` / `reported` / `inferred` tags on every number you repeat.
- Never bundle game files or loader binaries; never emit code from the no-license repos
  (ValCraft / EldenKill / chasm-bridge-fnv). The ValCraft header is absent by design.
- Direction convention in the shipped samples: host game → guest client; the abstract
  layer must not hard-code "Minecraft" anywhere.
