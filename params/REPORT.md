# PTmodmaker 参数库 V0 种子 — 入库报告

生成日期：2026-10-07
产物目录：`passthrough-lab/03-复现路线/v0-params/`
数据来源：`bailo167/awesome-game-mashups`（CC0-1.0）+ 三份解剖文档（本项目产出，同样 CC0 口径）

---

## 1. 入库条数 & 三色分布

| 项 | 数量 |
|---|---|
| 种子骨架（seeds，passthrough/shared-memory 项目） | **9** |
| 手工提取参数（params） | **35** |
| 合计 | 44 |

三色分布（仅 params，35 条）：

| 档 | 含义 | 条数 |
|---|---|---|
| 🟢 green | 同引擎同加载器可直搬 | 14 |
| 🟡 yellow | 只能当初始值，必须复核 | 10 |
| 🔴 red | 必须实测 | 11 |

证据档分布（35 条）：`repo` 8 · `doc` 20 · `inference` 7。
其中 `do_not_package=true`（无许可仓库，禁止默认打包）：**7** 条（全部 ValCraft）。

> 注：任务简报预估筛选"约 18 条"，实际匹配 `approach` 含 passthrough / shared memory 的**只有 9 条**。
> 宽松按 "shared" 或 "memory" 词面能扩到 15~16 条，但会混入非 passthrough 项目，故严格采用 9 条。

## 2. 补到 SHA 的仓库数 / 尝试数

- MIT 条目：**7 / 7** 成功取到 HEAD commit SHA（经 `gh api`，默认分支均为 `main`）。
- 失败的：0。任何取不到的情况脚本会如实记 `source_commit: null` + 原因，**无编造**。
- 未拉 SHA 的 2 条（`valcraft`、`new-vegascraft`）均为**无 LICENSE**，按规则不拉；记 `sha_fetch_note: non-MIT / no license -> 未拉 SHA`。
- 交叉校验：SkyCraft 取的 `bfcaf178524b92c2cdeb88e4ce0f13ef9ded6f32` 与解剖文档检出 commit 完全一致 ✅。

## 3. 三大空洞（最缺的字段 / 真空洞清单）

这是参数库目前最该补的地方：

1. **`loader`（装载器名）—— 9/9 骨架缺失。**
   接一款新宿主第一步就是确定 loader（SKSE / BepInEx / ScriptHookV / F4SE / xNVSE…）。
   当前种子里全部为 `null`，仅 `loader_hint` 从 approach 文本留了线索。这是参数库最大的**结构性缺口**。

2. **`source_commit`（可复现锚点）—— 非 MIT 仓库永久缺失。**
   只有 MIT 才拉得到 SHA；2 个无许可仓库永远缺锚点。CC0 种子集本身不强制 SHA，
   但"无锚点 = 不可复现"是合规层面的暗洞。

3. **实测值本身（🔴 档数值空洞）—— 35/35 `verified_on_hardware=false`。**
   整个生态零 playtest（awesome 全集 `playtest` 70/70 为空）。最贵的参数（yaw/pitch 表达式、
   碰撞策略、宿主几何）**大多还没有任何数值**——如 SkyCraft 的 yaw/pitch 在 DESIGN 里就未写死，
   作者注明"Phase 0 with a test"实测标定。参数库今天存的是"待测量清单"，不是"常量表"。

附带普遍缺失（awesome 全集中也常见）：`creator`（多数为 null）、`requirements`、`scope_note`、`review_note`
在不少条目里为 null；但这些不影响参数库骨架。

## 4. 只在二手转述里出现、必须打 `inference` 的参数

- **`gta.yaw_seo_misquote`**：网上 SEO 站把 GTA 版仓库原文 `yaw = 180 − heading` 传抄成
  `280 − heading`。已被仓库原文（minecraft-gta5-passthrough.md §4-L80 / §7-L199）证伪。
  本库以 `evidence=inference` + 显式命名 `yaw_expr__SEO_MISQUOTE_DO_NOT_USE` 入库，标注禁止采用。
- **ValCraft 全家（7 条）**：因上游 `LoAlCo/ValCraft` 无 LICENSE，按硬约束一律 `evidence=inference`
  且 `do_not_package=true`，不可默认打包——尽管这些值是从读码得到的，但许可状态逼我们降级为推断档。
- **`valcraft.terrain_digging`**：由"协议删掉 `DigMaterial`/`kRenDug`/`kTriDiggable`"反推 Valheim 不支持挖地形，属推断，打 `inference`。

> 经验：凡"数值与某仓库原文对不上、或只在博客/SEO 页出现"的参数，一律 `inference` 且不放可执行默认值。

## 5. 合规与硬约束落实

- ✅ 只存观测值 + 出处，无任何代码片段。
- ✅ 无许可仓库（ValCraft / New VegasCraft）参数不进"可打包"集；ValCraft 7 条标 `do_not_package`。
- ✅ 未运行任何游戏；`verified_on_hardware` 全 false。
- ✅ 无出处参数不进库（如 SkyCraft yaw/pitch 未写死，只记"must-measure"，不给数值）。
- ⚠️ 简报"SkyCraft: yaw = 180 − heading"为误植；该式属 GTA 版，已按解剖文档修正入库。

## 6. 产物清单

```
v0-params/
├── params.yaml            # 参数库（meta + 9 seeds + 35 params）
├── seeds.yaml             # seed_from_awesome.py 的独立产出（9 骨架，含 MIT SHA）
├── seed_from_awesome.py   # 从 projects.json 筛 passthrough/shared-memory + 拉 MIT SHA
├── param_lookup.py        # CLI 查询（--host / --color）
└── REPORT.md
```

## 7. 可复现命令

```bash
python3 \
  passthrough-lab/03-复现路线/v0-params/param_lookup.py --host skyrim --color red
```
解释器为已装 PyYAML 6.0.3 的专用环境；`--host` 按宿主名子串过滤（如 skyrim/valheim/gta），
`--color` 按 🟢🟡🔴 复用档过滤，输出带完整出处的表格。重建种子：
```bash
python3 \
  passthrough-lab/03-复现路线/v0-params/seed_from_awesome.py
```
（自动对 7 个 MIT 仓库调 `gh` 取 HEAD SHA，失败如实留 null。）
