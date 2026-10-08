# REPORT — 一份 schema.yaml 能否吃掉三种引擎的 passthrough 协议差异

## 结论（一句话）

**能。** 一份双层 `schema.yaml`（固定 `container` + 随宿主变的 `vocabulary`）在实测中双向还原了 SkyCraft / FalloutCraft / ValCraft 三份真实协议头，结构性 diff 均为 **0**；第 4 个宿主只需改 `vocabulary`，无需动 `container`。

| 宿主 | 许可 | 轮转目标 | 实测结构性 diff |
|------|------|----------|-----------------|
| SKY  | MIT  | 0（逐字字节布局） | **0** |
| FO4  | MIT  | 0（逐字字节布局） | **0** |
| VAL  | 无（仅对照） | 仅验证表达力 | **0**（表达力达标，生成物不进仓库） |

验证命令（零结构差异即 PASS，否则 `sys.exit(1)`）：

```bash
python3 \
  <home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v0-schema/verify_roundtrip.py
```

## 已被 schema 吃掉的真实差异（实测证据）

这些差异全部落在 `vocabulary`，`container` 一行未动即还原成功：

- 命名空间 `skycraft::proto` ↔ `valcraft::proto`（VAL 词表 `namespace`）—— `gen_header.py:112`
- 标量：`kMagic` `0x43594B53`↔`0x434C4156`、`kVersion` 11↔10、`kMappingName`、`kUnitsPerBlock` 70.0↔1.0
- 区域常量名 `kOffSkyState`↔`kOffValState`：由 `regions_template` 的 `{host_state_off}` 占位符渲染为 `kOff{abbr}State`（`abbr`=Sky/Val）—— `gen_header.py:128`
- 宿主状态结构体 `SkyState`/`ValState`（词表 `host_state.fields`）：VAL 多出 `fovSetting/fovSeq/mpMode/mpSeq/mpLink`；FO4 多出 `ground*` 字段并追加 `kGroundGrid`
- 宿主标志枚举 `SkyFlags`↔`ValFlags`（词表 `host_flags`）
- `McFlags`：FO4 增 `kMcHealthValid`；VAL 增 `kMcEyeInWater/kMcEyeInLava/kMcHoldingHoe/kMcCreative/kMcHoldingHammer`
- `InputType`：FO4 增 `kInScavenge`；VAL 增 `kInGive/kInGiveData`
- `McEventType`：VAL 增 `kEvValheimHit`
- 可选槽：`ToolKind`（仅 VAL）、`DigMaterial`（VAL 无）、`RenDug`（VAL 无）、`ColTriFlags.kTriMaterialShift`（VAL 无 `has_shift`）—— 通过 `optional` 槽 + `has_*` 开关处理
- `RenType`：VAL 增 `kRenViewModel/kRenInventory/kRenItemIcons`

源文件：`90-源码/{SkyCraft,FalloutCraft,ValCraft}/protocol/*_protocol.h`。

---

## schema 表达不了的东西（ABI 设计的真实边界）

每条附行号证据。结论分档见末列：**实测**=本轮已验证；**推断**=由设计推得、未实测（仅 3 宿主，差异全在词表层级）。

### B1. 内存布局与所有 `fixed` 块是 `container` 硬编码字面量，不在词表里
区域偏移 `kOffXxx` 全在 `container.regions_template` / `container.fixed` 作为固定多行字符串（源 `skycraft_protocol.h:22-42`；碰撞结构体 `ColTri/ColMsgHeader/ColRegion/ColBlock` 及其 `static_assert` 在 `fixed`，源 `skycraft_protocol.h:543-567`）。**推断**：第 4 个宿主若需要不同的内存映射（更大 overlay、重排 ring 偏移），无法靠 `vocabulary` 表达，必须改 `container`。这是本方案的根本边界——`container` 管"语法+布局"，`vocabulary` 只管"词"，布局本身被定为不可变。

### B2. 文件头 banner / 文档散文是生成器固定前缀，非每宿主
源 `skycraft_protocol.h:1-8` 与 `valcraft_protocol.h:1-8` 的 banner 文本不同（Skyrim/SkyCraft vs Valheim/ValCraft），但 `gen_header.py:103-106` 对所有宿主输出同一条硬编码 "generated from schema.yaml" banner。原每宿主手写 banner 被丢弃（仅外观损失，不影响结构）。

### B3. 枚举/结构体的语义注释不在词表里
`extract_vocab.py` 只收标识符、类型、数值字面量。`McEventType` 的"formId, a = MC damage..."行为散文（源 `skycraft_protocol.h:243-250` vs `valcraft_protocol.h:269-277`）、`ValState` 字段含义（`valcraft_protocol.h:92-99`）、`WorldEntity`/`RenVertex` 注释均被剥离且不再生成。diff=0 正是因为散文被忽略——schema 捕获契约的"形状"，不捕获其"文档"。**实测**。

### B4. 未命名 / 保留标志位对 schema 不可见
`ValFlags`（源 `valcraft_protocol.h:57-65`）的 bit 3、4-5、7、8 仅有散文（"bit 3 block terrain"、"bit 7 mob natural spawning, bit 8 mob griefing"），无对应命名枚举成员。schema 只发射命名 `kValXxx`，无法表示"bit N 保留/有定义但未命名"。`SkyFlags` 无保留位，故该不对称被掩盖。**实测**。

### B5. 结构体体是逐行不透明文本，非类型化字段模型 → 无类型级 ABI 校验
`gen_header.py:49,66` 把 `host_state.fields` / `mc_state.fields` 当原始行逐行吐出；抽取器存的就是源码行。诸如 `std::uint32_t pad4C;`（源 `skycraft_protocol.h:119`）、`tickPad`（`:131`）、`reserved[0x40-0x18]`（`:163`）以不透明文本重现。**推断**：词表里若把某字段 C++ 类型改错（如 `double`→`float`），生成器会吐出仍能编译、但 ABI 已悄悄破坏的头，schema 层无法发现。换句话说，本 schema 是"模板层"，不是"类型校验层"。

---

## 结论分档

- **已实测**：SKY/FO4 零结构差异（MIT，逐字字节布局）；VAL 零差异（表达力达标）；B3/B4 散文与保留位丢失为本轮直接可见。
- **据项目自述**："协议容器一行未动，差异仅在词表"——本轮 3 宿主的逐行 diff 印证了该前提成立。
- **推断**：B1（4 宿主改布局需动 container）、B5（类型级 ABI 校验缺失）由设计推得；现有 3 宿主差异全在词表层级，未触发这两类场景，故未实测。

## 产物清单（均在 `03-复现路线/v0-schema/`）

- `schema.yaml` —— 双层 schema，`vocabularies` 仅内嵌 SKY+FO4（MIT）；VAL 词表运行时不嵌入，严守"不复制 ValCraft 代码"约束。
- `gen_header.py` —— schema → C++ 头（仿 `skycraft_protocol.h` 版式）。
- `extract_vocab.py` —— 真实头 → vocabulary。
- `verify_roundtrip.py` —— 提取→生成→结构性 diff（忽略注释/空白，保留标识符/字面量/顺序）。
- `generated/SKY.h`、`generated/FO4.h` —— 零差异生成物（已落盘）。
- 本 `REPORT.md`。
