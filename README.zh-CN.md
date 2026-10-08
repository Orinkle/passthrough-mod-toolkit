# passthrough-mod-toolkit（中文说明）

> **填一张词表，吐出一个「passthrough mod」骨架。**
> passthrough mod 让**两个完整游戏以两个独立进程同时运行**（例如客侧跑 Minecraft Fabric mod，
> 宿主侧跑 SKSE / BepInEx / ScriptHookV 插件），经本地 IPC（共享内存 / WebSocket）交换数据，
> 实现「用 A 游戏的机制玩 B 游戏的世界」。
>
> **也叫：** passthrough mod · 跨游戏桥联 · 游戏缝合 · 双进程游戏桥 · cross-game bridge · two-game mashup

本仓库是**脚手架工具包**——它生成桥的固定骨架（五语言协议头、假宿主/假客侧桩、共享内存布局、
零依赖 MCP 服务器），**不替你跑游戏，也不含任何游戏代码**。见[诚实边界](#诚实边界)。

## 目录

- [passthrough mod 到底是什么](#passthrough-mod-到底是什么)
- [什么时候用 / 什么时候别用](#什么时候用--什么时候别用)
- [30 秒演示](#30-秒演示)
- [快速开始](#快速开始)
- [五件东西各干什么](#五件东西各干什么)
- [诚实边界](#诚实边界)
- [鸣谢与版权](#鸣谢与版权)
- [许可](#许可)

---

## passthrough mod 到底是什么

两个游戏、两个进程、一座本地桥。分工固定：

- **客侧管身体**——位移、碰撞、背包、战斗。
- **宿主管世界**——地形、NPC、存档、画面。

桥**不是「一个 mod」**，而是**五件东西**：

| # | 部件 | 是什么 |
|---|------|--------|
| ① | **客侧 mod** | 跑在客侧游戏里（如 Minecraft Fabric mod）。 |
| ② | **宿主侧插件** | 跑在宿主游戏里（SKSE / BepInEx / ScriptHookV `.asi`）。 |
| ③ | **传输层** | 共享内存 / WebSocket **约定**，是*契约*，不是插件。 |
| ④ | **画面合成器** | ReShade add-on 或宿主内嵌渲染，**独立于两个游戏进程**。 |
| ⑤ | **启动器** | 起进程、开通道、心跳、录屏。 |

架构图见主文档 [`README.md`](README.md)（含 Mermaid / 纯文本两版）。

---

## 什么时候用 / 什么时候别用

**该用的时候：**

- 你要做 **passthrough mod**（两游戏两进程、本地 IPC 桥），不想从零推导共享内存协议、
  结构体布局、epoch / 心跳守卫。
- 你要**一份 schema → C++ / C# / Java / Rust / Python 五语言协议绑定**，并且要有
  「schema 双向还原三种真实引擎协议头、结构性 diff = 0」的实证。
- 你想**不装游戏也能开发**——假宿主/假客侧桩用纯 Python 进程跑三个经典失败场景
  （心跳超时、epoch 失效、陡墙碰撞）。
- 你是一个 **agent**，要找的是脚手架和清单，不是成品 mod。

**别用的时候：**

- 你要的是**拿来就能玩的成品 mod**。这里只有骨架；宿主侧插件（②）必须你自己写、自己测。
  跳过[诚实边界](#诚实边界)会让你白干几周。
- 你只想给**一个游戏**做 mod——用那个游戏正常的 mod 技术栈；双进程桥是加内容最贵的方式。
- 你需要**实机验证过的参数**。这里没有。`params/params.yaml` 里每个 🔴 参数
  （`verified_on_hardware: false`）都必须在你自己的构建上实测。
- 任何与**联机、反作弊、EULA 绕过**相关的用途。硬性排除，所有样本一律按单机理解。

---

## 30 秒演示

**无游戏、无引擎、无 GPU。** 两个 Python 进程跑在一块共享内存映射上，而这块映射本身是**从 `schema.yaml` 生成**的 —— 与多语言后端同源。完整记录见 [`demo/demo.txt`](demo/demo.txt)。

三个 PASS **可被反证**：`stubs/negative_control.py` 逐个关掉守卫，恰好对应的那个场景翻 FAIL。一个你故意弄不坏的绿色 demo 不算证据。

（英文主 README 有完整终端输出：[README.md](README.md#30-second-demo)）

---

## 快速开始

桥由一个**双层 schema** 驱动：固定 `container`（内存布局，不随宿主改）+ 逐宿主 `vocabulary`（你填的「词」）。
这是本仓库最硬的一条结论，且是**实测**而非设想：

> 一份 `schema.yaml` 双向还原了 **三种**引擎协议头（SkyCraft / FalloutCraft / ValCraft），
> **结构性 diff = 0**。— [`schema/REPORT.md`](schema/REPORT.md)

约 20 行词表摘录（真实已记录值；完整文件见该报告）：

```yaml
vocabularies:
  skyrim:                      # MIT 源：chasmlol/SkyCraft
    kUnitsPerBlock: 70.0       # [据项目自述] 需实机核实
    yaw_expr: "f(rotZ)"        # [推断] 作者注明必须实测，未给值
  gta5:                        # MIT 源：rehan-remade/universal-modder
    kUnitsPerBlock: 1.0        # [据项目自述] 1 GTA 米 = 1 MC 方块
    yaw_expr: "180 - heading"  # [据项目自述] 需在你的构建上核实
  valheim:                     # [推断] 只读；不发射（无 LICENSE）
    kUnitsPerBlock: 1.0
```

从这一份 schema 生成**五种语言**的绑定（真实命令，`ptgen` 是唯一的控制台入口）：

```bash
python -m pip install ./ptgen      # 安装 ptgen 命令行（唯一硬依赖是 PyYAML）

ptgen --schema schema/schema.yaml --lang cpp    --host SKY --out out/
ptgen --schema schema/schema.yaml --lang python --host SKY --out out/
# --lang csharp | java | rust 亦可

python schema/verify_roundtrip.py  # 回归：真实 MIT 协议头，结构性 diff 必须为 0
python stubs/run_demo.py           # 上面演示里的三个场景
python mcp/server.py               # 零依赖 MCP 服务器（JSON-RPC over stdio，5 个工具）
```

安装细节（3 条命令以内）见 [`install.md`](install.md)。

②（宿主插件）仍需手写——见[诚实边界](#诚实边界)。

---

## 五件东西各干什么

- **① 客侧 mod**——身体侧插件模板（注入点、mixin 清单）。约 50% 可模板化。
- **② 宿主侧插件**——**本工具写不了的那件**。约 20% 可模板化（Link 层 + 探针工具）。
- **③ 传输层**——纯约定，零游戏逻辑。**约 100% 生成**，是工具的主场。
- **④ 画面合成器**——shader 骨架 + 三缓冲可生成；深度约定 / 挂点 / 轴向逐宿主。
- **⑤ 启动器**——起进程、开通道、心跳、录屏。约 90% 脚本化。

> 百分比证据档：①④为 **[推断]**（三样本外推）；②③⑤为 **[实测]**（行数 + 职责边界读码）。

---

## 诚实边界

本节**故意不软化**。跳过它会让你白干几周。

- **本工具不替你跑游戏。** 它只出骨架。游戏、加载器、宿主插件都由你装、你写。
- **宿主侧插件代码 🔴 必须实机测量。** 以下**永远不能**从样本抄来就用——它们都是逐构建的魔法数：
  - 相机 / 姿态矩阵与 **yaw / pitch 表达式**（SkyCraft 的 `f(rotZ)` 作者明说没写死，必须测）。
  - 坐标映射、`yOffset` 标定、**深度约定**（reversed-Z 还是常规）。
  - 碰撞探针策略及其对象数上限（某样本约 1500 个脚本对象即崩）。
  - 重投影（6-DoF 光线步进）调参、姿态滞后。
  - 你目标游戏构建的具体加载器 / hook API 面。
- **证据分档：** `measured` 实测 ／ `reported` 据项目自述 ／ `inferred` 推断。
- **本仓库零实机验证。** 作者机器带不动游戏（125 GB 安装、GPU / 反作弊限制）。
  所有数字来自**逐行源码比对**，不是玩出来的。整个生态同理：权威 70 条总目录里，
  **70 条全部无第三方验玩记录**。此处无任何「实机已验证」结论。
- **「出骨架」≠「出桥」。** 固定骨架按行数只占 ~11.5%；其余 ~88.5% 是逐游戏的翻译逻辑，
  最贵的知识（常数标定、坑）全在那里。

---

## 鸣谢与版权

遵循 [`zeyvu/FalloutCraft`](https://github.com/zeyvu/FalloutCraft)（生态里最规范的 MIT 合规样板）的做法。

- **采用并保留版权（MIT）：** `chasmlol/SkyCraft`（Copyright chasmlol）、
  `rehan-remade/universal-modder`（Copyright rehan-remade）。
- **只读、未抄：** `LoAlCo/ValCraft`、`FFwLo/EldenKill`、`chasmlol/chasm-bridge-fnv`——
  三者均无 LICENSE，**零行代码被采用或发射**（见 `RELEASE_CHECKLIST.md` R3）。

## 许可

**MIT License**——见 [`LICENSE`](LICENSE)，第三方声明见 [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md)。可商用，但须保留上述 MIT 组件的版权声明与全文许可；
**不得**捆绑游戏文件、加载器二进制（SKSE / ScriptHookV / ReShade）或无许可项目的代码。
