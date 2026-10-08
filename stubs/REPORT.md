# REPORT — 统一假桩（fake host / fake guest）for PTmodmaker

全程**不启动任何游戏**：一条由 `schema.yaml` 生成的共享内存通道，一对假桩在上面跑通三个自验证场景。
结论：**a / b / c 三场景在纯 Python 下全部 PASS**，且每一项都能被反向对照证伪（见 §5）。

---

## 1. 产物与复现命令

```
v1-stubs/
  layout_from_schema.py   # schema.yaml -> ctypes 布局（生成器 + 断言）★ 唯一的字节来源
  fake_host.py            # 宿侧假桩：位姿(seqlock) / 碰撞几何 / 输入环 / 读事件环
  fake_guest.py           # 客侧假桩：运动学积分 + step-up + 碰撞解算 + 事件回传
  run_demo.py             # 顺序跑 a/b/c，写 demo_trace.json，打印 PASS/FAIL
  render_demo.py          # demo_trace.json -> 确定性 ANSI 文本（README 30 秒 demo）
  negative_control.py     # 逐个关掉守卫，证明三个测试不是空跑
  generated/SKY_layout.py, generated/FO4_layout.py   # 生成物落盘
  demo_trace.json         # 三个场景的完整结构化轨迹（含跨生成器一致性核对）
```

一条命令复现（解释器绝对路径）：

```bash
/home/zjk/.workbuddy/binaries/python/envs/default/bin/python \
  /home/zjk/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v1-stubs/run_demo.py && \
/home/zjk/.workbuddy/binaries/python/envs/default/bin/python \
  /home/zjk/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v1-stubs/render_demo.py
```

## 2. 传输方式：**共享内存映射**（不是 WebSocket）

理由（半句）：schema 定义的就是“一整块映射 + 就地 seqlock + SPSC 环”，WebSocket 会把这套就地读写重新序列化成消息，丢掉 schema 的语义；而且 /dev/shm 在本机只有 10 MB，`kCollisionRingBytes` 单独就 32 MB，`multiprocessing.shared_memory` 撑不下，所以用**文件支撑的 `mmap`（MAP_SHARED）**——它正是 schema 里 Windows 命名映射（`Local\SkyCraft_v1`）的 POSIX 等价物，两个进程看到同一批页，head/tail 是就地 u64。

映射大小由 schema 常量算出：`kOffCollisionRing + kCollisionRingBytes = 33685504`（本假桩只用位姿/输入/事件/碰撞四块区域）。注意 Python 的 `mmap.mmap(-1, tagname=...)` 在 Linux 上是匿名映射、**跨不了进程**，不能拿来当“命名共享内存”。

## 3. schema 是唯一事实源（硬约束的证据）

`layout_from_schema.py` 读 `v0-schema/schema.yaml`（只读，未改动其中任何文件），解析
`container`（`inline constexpr` 常量、`enum`、`struct` 字段与 `static_assert` 尺寸、`{host_state_off}` 占位符）+
`vocabulary`（`host_state`/`mc_state` 字段表、各枚举、`Header` 由 `host_abbr/host_prefix` 合成），
**emitter 出 ctypes.Structure 源码**并 exec。`fake_host.py`/`fake_guest.py` 只 `import` 生成物，**没有任何手写字段或手写偏移**。

生成的断言（`layout_from_schema.verify`，不通过即 `SystemExit(1)`）：

| 检查 | 内容 |
|---|---|
| ABI | `ctypes.sizeof(struct)` == schema 的 `static_assert` 尺寸 / `vocabulary.size`（SKY 28 个结构体，含 `SkyState=64`、`McState=200`、`ActorRecord=64`、`WorldEntity=96`…） |
| 字段 | 字段名、顺序、ctypes 类型逐条与 schema 声明一致（含 `[kMaxActors]`、`[3][4]`、`[0x40-0x18]` 等维度表达式求值） |
| 常量 | 每个 `inline constexpr` / 枚举成员由表达式独立求值后与发射值一致 |
| 跨生成器 | 与另一 agent 的生成物 `protocol_sky.py` 逐结构体比 `sizeof`：**28/28 一致** |

**已实测**：`SKY` 与 `FO4` 两个词表都通过全部断言（FO4 `FO4State=192`）。这补上了 T1 REPORT 里的 B5（“无类型级 ABI 校验”）——把某字段 `double` 改成 `float`，尺寸断言立刻失败。

## 4. 三个场景结果（如实）

| 场景 | 判据 | 实测 | 结论 |
|---|---|---|---|
| **a 心跳超时** | 杀 host 后 guest 冻结且不再解冻、干净退出、stderr 为空 | `froze=True`、冻结持续到退出、`exit=0`、`stderr=''` | **PASS** |
| **b epoch 失效** | 重启 host（epoch 1→2）后进入失效态、丢弃旧 session 的 seq/teleport、**不瞬移** | `session_discards=1`、失效 11 tick、`teleports=1`（仅 t≈0 入会那次，`late=[]`）、单 tick 最大位移 `0.05` | **PASS** |
| **c 陡墙** | >50° 的 AABB 必须是整面墙：不穿、不爬 | 墙 `slope=90.0°`（阈值 50°）、`guest_max_x=7.7 < 8`、`crossed=False`、`climbed=False`、被挡 293 tick | **PASS** |

客侧还消费了宿侧的输入环（一次 Space=跳跃）与 seqlock 位姿；宿侧读到了客侧事件环。`render_demo.py` 输出（去色后）见 §1 命令，`demo_trace.json` 内嵌三段完整轨迹。

## 5. 反向对照（证明测试不是空跑）

`negative_control.py` 把本目录复制到临时目录，**只关掉该项对应的那一个守卫**再跑一次：

```
disable-guard for a_heartbeat_timeout   -> {'a': False, 'b': True, 'c': True}   OK
disable-guard for b_epoch_invalidation  -> {'a': True,  'b': False,'c': True}   OK
disable-guard for c_steep_wall          -> {'a': True,  'b': True, 'c': False}  OK
NEGATIVE CONTROL: PASS
```

每次恰好只有对应场景翻成 FAIL —— 说明 PASS 是那条守卫挣来的。

## 6. 假桩暴露的 schema 不足

1. **环 head/tail 的单位没有声明。** 碰撞/渲染环 schema 写了“u64 total bytes written”（字节），但输入/事件环只写“u64, written by host/MC”，**没写单位**；真实生产者（`fake_skyrim.py`）用的是**条目计数**（`head % kInputRingEntries`、`tail % kEventRingEntries`）。假桩只能从定长条目结构（`InputEvent=16`、`McEvent=32`）反推单位。schema 应声明每环的单位与条目尺寸。
2. **字节环的换行/对齐纪律没进 schema。** 碰撞环消息 8 字节对齐、写满时写一条 `(0,0)` 空消息并跳到环尾——这些只在生产者代码里。笔者的第一版把 8 字节 `ColMsgHeader` 重复计入长度，导致环立刻失步、客侧解不出几何（实测：只收到 clear、收不到 tri）。
3. **`Header` 根本不是 schema 实体。** 它只由 `host_abbr` 的注释暗示；6 个字段（`magic/version/{prefix}Pid/mcPid/{prefix}HeartbeatMs/mcHeartbeatMs`）与 32 字节尺寸都得生成器自行合成，`kOffHeader` 区域也没有声明长度。
4. **seqlock 的发布纪律没声明。** 容器注释说 `host_state` 是“seqlock like”，`host_state/mc_state/WorldEntities/WaterGrid` 都有 `seq`，但“写时 seq 取奇数、稳定后为偶数”的发布/读取纪律不在 schema 里，客侧只能手工实现。
5. **各环的方向（谁产谁消）只是散文。** `kOffEventRing "MC -> host"` 之类无法被生成器校验。
6. **`WaterGrid` 只有上界。** 它用 `static_assert(sizeof <= 0xC00)`（实际 1040），因此没有“精确声明尺寸”，ABI 断言对它只能判上界。
7. **`{host_state_off}` 是单一名字占位符**（同 T1 的 B1）：宿状态区域名只要不是 `kOff{abbr}State` 就无法表达。

以上 1–5 是本轮**实测**踩到的；6 是断言实现时**实测**发现的；7 沿用 T1 的**推断**。

## 7. 结论分档

- **已实测**：传输可用；`layout_from_schema.py` 对 SKY+FO4 的全部尺寸/字段/常量断言通过；与另一生成物 28/28 结构体尺寸一致；a/b/c 三场景 PASS；三处反向对照各自翻 FAIL。命令见 §1。
- **据项目自述**：三个隐患（心跳/epoch/陡墙）来自项目知识笔记 `minecraft-passthrough.md`；“安全冻结 / 重启不瞬移 / >50° 视为墙”是本文对该笔记的实现选择，非笔记逐字规定。
- **推断**：§6 的第 1、2 条会绊倒第 4 个宿主（本轮只造了 SKY，未实测）；`protocol_sky.py` 与本文生成物只在“结构体尺寸”上核对一致，字段级未逐条比对。
