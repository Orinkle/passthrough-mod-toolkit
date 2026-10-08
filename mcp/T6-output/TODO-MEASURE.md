# TODO-MEASURE — Teardown ← Minecraft: Java Edition

> 本文件由 `pt_scaffold` 从 `v0-params/params.yaml` 自动筛出 **🔴 必须实测** 档参数生成。
> 这些数值**不存在可复用的真值**，必须在真机上实测标定后才可写入本适配器。
> 筛选范围：按客侧匹配（宿主未命中）；命中 11 条。

> ⚠ SkyCraft 的 yaw/pitch 在 DESIGN 中并未写死，作者注明 'Phase 0 with a test' 实测标定 —— 故本库不设数值，只记 'must-measure'。
> ⚠ 任务简报中 'SkyCraft: yaw = 180 - heading' 为误植；该式属于 GTA 版（minecraft-gta5-passthrough），已按解剖文档修正。
> ⚠ ValCraft / New VegasCraft 无 LICENSE；据硬约束，ValCraft 参数一律 evidence=inference 且 do_not_package=true，不可默认打包。

## 待实测项

- [ ] **skycraft.yaw_pitch** — `yaw_pitch_expr`
  - 宿主/客侧: The Elder Scrolls V: Skyrim Special Edition ← Minecraft: Java Edition
  - 现值: `UNPINNED — author states pinned in Phase 0 test: mc.yaw=f(sky.rotZ), mc.pitch=f(sky.rotX)`
  - 证据档: **doc**（实机验证: False）
  - 出处: chasmlol/SkyCraft@bfcaf17852 (SkyCraft.md#§4-L114)
  - 备注: DESIGN 未写死符号/偏移，作者本人注明是实测标定值。本库不存数值，只记 must-measure。

- [ ] **skycraft.collision_res** — `collision_resolution`
  - 宿主/客侧: The Elder Scrolls V: Skyrim Special Edition ← Minecraft: Java Edition
  - 现值: `1/8 block = 8.75 units (16^3 section bucket)`
  - 证据档: **doc**（实机验证: False）
  - 出处: chasmlol/SkyCraft@bfcaf17852 (SkyCraft.md#§4-L115)
  - 备注: 碰撞策略属 [C] 档，必须逐游戏实测。

- [ ] **skycraft.slope_threshold_deg** — `slope_threshold_deg`
  - 宿主/客侧: The Elder Scrolls V: Skyrim Special Edition ← Minecraft: Java Edition
  - 现值: `~50`
  - 证据档: **doc**（实机验证: False）
  - 出处: chasmlol/SkyCraft@bfcaf17852 (SkyCraft.md#§4-L116)

- [ ] **skycraft.vert_extent** — `vertical_extent`
  - 宿主/客侧: The Elder Scrolls V: Skyrim Special Edition ← Minecraft: Java Edition
  - 现值: `min_y=-2032, height=4064`
  - 证据档: **doc**（实机验证: False）
  - 出处: chasmlol/SkyCraft@bfcaf17852 (SkyCraft.md#§4-L119)
  - 备注: Skyrim 地形跨度超 MC 默认上限，须自定义 dimension_type；宿主几何，必须实测。

- [ ] **gta.yaw** — `yaw_expr`
  - 宿主/客侧: Grand Theft Auto V ← Minecraft: Java Edition
  - 现值: `mc.yaw = 180 - heading`
  - 证据档: **doc**（实机验证: False）
  - 出处: rehan-remade/universal-modder@baff1e5d01 (minecraft-gta5-passthrough.md#§4-L80)
  - 备注: yaw 表达式属 [C] 档，必须实测；仓库原文为 180，与 SkyCraft、与二手页传抄的 280 均不同。

- [ ] **gta.pitch** — `pitch_expr`
  - 宿主/客侧: Grand Theft Auto V ← Minecraft: Java Edition
  - 现值: `mc.pitch = -pitch`
  - 证据档: **doc**（实机验证: False）
  - 出处: rehan-remade/universal-modder@baff1e5d01 (minecraft-gta5-passthrough.md#§4-L81)

- [ ] **gta.pose_lag_frames** — `pose_lag_frames`
  - 宿主/客侧: Grand Theft Auto V ← Minecraft: Java Edition
  - 现值: `1`
  - 证据档: **doc**（实机验证: False）
  - 出处: rehan-remade/universal-modder@baff1e5d01 (minecraft-gta5-passthrough.md#§4-L85)
  - 备注: 姿态滞后 1 帧（gotcha #8）；时序参数必须实测。

- [ ] **gta.gl_none_readbuffer_bug** — `gl_readbuffer_gotcha`
  - 宿主/客侧: Grand Theft Auto V ← Minecraft: Java Edition
  - 现值: `MC 26.3 GL 后端 depth copyTextureToBuffer 后把 read buffer 留在 GL_NONE 且不还原`
  - 证据档: **doc**（实机验证: False）
  - 出处: rehan-remade/universal-modder@baff1e5d01 (minecraft-gta5-passthrough.md#§5-A-L99)
  - 备注: GOTCHA #1：须 Mixin GL command encoder 在 copy 后恢复 read buffer。非数值参数，列为已知坑。

- [ ] **gta.yaw_seo_misquote** — `yaw_expr__SEO_MISQUOTE_DO_NOT_USE`
  - 宿主/客侧: Grand Theft Auto V ← Minecraft: Java Edition
  - 现值: `280 - heading  (二手 SEO 站传抄，已被证伪)`
  - 证据档: **inference**（实机验证: False）
  - 出处: -@- (second-hand SEO pages; rebutted in minecraft-gta5-passthrough.md#§4-L80 / §7-L199)
  - 备注: 网上 SEO 站把仓库原文 180-heading 传抄成 280-heading。属二手转述，必须打 inference 且禁止采用；真值为 180-heading。

- [ ] **valcraft.license** — `license`
  - 宿主/客侧: Valheim ← Minecraft: Java Edition
  - 现值: `NONE (仓库根目录无 LICENSE，默认保留所有权利)`
  - 证据档: **repo**（实机验证: False）  `do_not_package`
  - 出处: LoAlCo/ValCraft@cf1b4cfc34 (ValCraft.md#§7-L118)
  - 备注: 合规红线：fork 了 MIT 的 SkyCraft 客侧却未带许可证 —— 学思路可以，抄代码有风险。

- [ ] **valcraft.terrain_digging** — `terrain_digging_supported`
  - 宿主/客侧: Valheim ← Minecraft: Java Edition
  - 现值: `false (协议删 DigMaterial/kRenDug/kTriDiggable 整条链路)`
  - 证据档: **inference**（实机验证: False）  `do_not_package`
  - 出处: LoAlCo/ValCraft@cf1b4cfc34 (ValCraft.md#§5-L100)
  - 备注: 由删掉的 Dig 能力反推（推断）；[C] 档典型：宿主能力不同 → 整功能分支被砍。

## 明确不做（🔴）

- ❌ 不生成宿主侧 natives / SDK 调用代码（如 SKSE / F4SE / 内存 hook）——
  这部分依赖真机上的脚本名、函数签名与偏移，**只能实测**，本脚手架拒绝臆造。
- ❌ 不猜测 yaw/pitch 表达式、碰撞策略、合成挂点或宿主几何。

---

# 【T6 增补】Teardown 宿主侧 待实测清单

> 上面 11 条是 `pt_scaffold` 自动筛出的——但它们**全是 Skyrim / GTA5 / Valheim 的**，
> 因为 Teardown 未注册，工具退化成"按客侧(Minecraft)匹配"。
> 也就是说：**工具没能为我的宿主产出任何一条 TODO**。以下 8 条由我（T6）手工补写，
> 每条的"为什么算必须实测"都引用工具自己的口径（`pt_scaffold.does_not` / 参数库 caveats）。

- [ ] **td.units_per_block** — 1 体素 = 多少 Minecraft 方块？
  - 工具口径: 参数库 `units_per_block` 属几何标定；同 SkyCraft 的 `collision_res`（🔴 doc）一样"必须逐游戏实测"。
  - 我猜的值: `1.0`（见 schema.teardown.yaml `units_per_block`）。**纯猜**，无出处。

- [ ] **td.yaw_pitch_expr** — Teardown 相机/刚体的朝向 → Minecraft yaw/pitch 的符号与偏移。
  - 工具口径: 与 `skycraft.yaw_pitch` 同类（原作者注明"Phase 0 with a test"实测标定）。
  - 我猜: 未写表达式，schema 里只留了 `host_state.yaw/pitch` 字段。**必须实测**。

- [ ] **td.voxel_scale / collision_res** — 体素→碰撞三角形/盒子 的粒度（多少体素一个桶）。
  - 工具口径: 同 `skycraft.collision_res`（🔴 doc，"碰撞策略属 [C] 档，必须逐游戏实测"）。

- [ ] **td.slope_threshold_deg** — 可攀爬坡度阈值（工具默认 50°，SkyCraft 也写 ~50）。
  - **必须实测**：Teardown 物理与 Skyrim 不同，不能照搬。

- [ ] **td.vertical_extent** — 地图竖直跨度（min_y / height）。Teardown 关卡不无限，须实测。
  - 工具口径: 同 `skycraft.vert_extent`（"宿主几何，必须实测"）。

- [ ] **td.epoch_semantics** — 换关 / 读档 时阻塞 epoch 代次递增的时机（对应 `pt_stub_run` 的 `epoch` 场景）。
  - 工具只证明"状态机会丢弃陈旧数据"，**没说** 宿主何时该 +1 epoch。

- [ ] **td.natives_hook** — Teardown 的 Lua mod API 里，读相机/写输入 的具体函数名与调用时机。
  - 工具口径: `pt_scaffold.does_not` **明确拒绝生成**宿主侧 natives/SDK 代码（"依赖真机脚本名、函数签名与偏移"）。
  - 结论: 这块**没有任何工具支持**，只能靠人读 Teardown mod 文档 + 实机。

- [ ] **td.overlay_compositing** — 画面合成挂点（客侧画面怎么叠进 Teardown）。
  - 工具口径: `does_not` 明确"不生成画面合成器（依赖真机渲染路径）"。**必须实测**。
