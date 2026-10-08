# REPORT — T2：schema → 多语言协议头生成器（ptgen）

## 结论（一句话）

**五语言全部生成成功**（`cpp`/`csharp`/`java`/`rust`/`python`），且 **C++ 后端与 T1 的
`gen_header.py` 逐字节相同**，`verify_roundtrip.py` 三个宿主结构性 diff 全为 0（exit 0）。
容器部分四语言 **实测** 偏移/尺寸一致（C++ 与 Rust 是真编译器测量，Python 是运行时
`ctypes` 测量）。这验证了项目核心卖点：**第一个 "schema → 多语言" 的可安装包**。

证据分档见文末；本轮**独立复核发现并修复了 6 处真实缺陷**（见"缺陷与修复"）。

---

## 1. 生成结果（host = SKY，`v0-schema/generated/`）

| 语言 | 生成物 | 行数 | 附带骨架 |
|------|--------|------|----------|
| C++    | `SKY.proto.h` | 519 | `SKY.sync.h`（57 行，seqlock+SPSC） |
| C#     | `SKY.proto.cs` | 573 | `SKY.sync.cs`（24 行） |
| Java   | `SKY.proto.java` | 412 | seqlock/SPSC 内联 |
| Rust   | `SKY.proto.rs` | 552 | seqlock/SPSC 内联 |
| Python | `SKY.proto.py` | 838 | seqlock/SPSC 内联 |

FO4 词表同样生成了一套（`FO4.proto.*`）。样例头文件放在 `v0-schema/generated/`，
不进 `v1-ptgen/`（该目录只放包骨架，`generated/` 已清空）。

每种语言都含：包/命名空间声明、常量、enum、**带内存布局断言/ packing 的结构体**、
seqlock 读写骨架、SPSC 环骨架。

## 2. 硬要求：C++ 回归（零差异）

`backends/cpp.py` 是 T1 `gen_header.py` 的忠实移植（`fixed`/`regions_template` 原样
发射，变量词从 vocabulary 渲染）。两条证据：

- `diff v0-schema/gen_header.py 输出  vs  ptgen 的 cpp 输出` → **CPP_IDENTICAL**（逐字节）。
- `verify_roundtrip.py` → `SKY diff=0`、`FO4 diff=0`、`VAL diff=0`，**PASS，exit 0**。

**已实测。** C++ 的 seqlock/SPSC 放在独立 `SKY.sync.h`，主头保持逐字节不变，验证不退化。

## 3. 硬要求：容器四语言 ABI 等价（相同偏移、相同尺寸）

单一事实源：`src/ptgen/model.py` 把 schema 的 `fixed` 块重述为语言无关模型，
`build_ctypes()` 用 `ctypes.sizeof` 断言其等于 C++ 的 `static_assert` 尺寸；所有后端从
该模型渲染。

自检脚本 `tests/compare_layout.py` 用**真编译器**测量，而非只读断言：

- 基准：`g++ 15.2.0` 编译生成的 C++ 头，`sizeof` + `offsetof` 全量导出；
- Rust：`rustc 1.97.1` 编译生成的模块，`size_of` + `offset_of!` 导出；
- Python：导入生成的 ctypes 模块，运行时取 `ctypes.sizeof` 与字段 `.offset`；
- Java：解析生成的 `*_BYTES` / `*_<FIELD>` 常量（本机无 javac）；
- C#：解析生成的 `Marshal.SizeOf<T>() != N` 断言（本机无 dotnet，只能比尺寸）。

结果（SKY）：**28 个结构体全部匹配**，`model(ctypes) vs 编译后 C++` 也匹配，
`RESULT: PASS`，exit 0。负向验证：注入一个错误偏移后该脚本报 1 处 mismatch（非空转）。

**已实测**（C++/Rust/Python 为编译或运行时测量；Java/C# 为常量解析）。

## 4. Java 与 Proto.java 的结构性 diff

参照物 `90-源码/SkyCraft/.../Proto.java`（236 行，MIT，可直接学）。`tests/diff_java.py`：

- **结构差异 = 373 行**（归一化后 ref 205 行 / gen 376 行）。差异**几乎全部来自命名约定**：
  Proto.java 用 `OFF_*`/`H_*`/`SS_*`/`AT_*`/`ER_*`/`WE_*`/`RR_*`/`CR_*`/`OC_*`/`SH_*`/`IR_*`
  手工缩写；生成器用统一的 `<STRUCT>_<FIELD>` 与 `<STRUCT>_BYTES`（并按本任务要求对**所有
  结构体**都发射偏移，故行数多于参照物的手工子集）。两者承载**同一批数值**。
- **数值等价**：Proto.java 的 170 个数值常量（57 个不同值）中，**56/57 在生成 Java 中按值出现**。
  唯一缺失是 `DIG_MATERIAL_COUNT = 22` —— `DigMaterial` 的**计数哨兵**，schema 中为
  `value: null`（自动递增终止符），不参与 ABI，生成器按设计不发射。脚本将其归为预期，
  仅剩它时 exit 0。

**已实测**（结构性行数 + 数值覆盖均为脚本实跑）。

## 5. C# / Rust / Python 各做了什么、没做什么

- **Rust**：`rustc 1.97.1` 真实编译生成物 **exit 0**；`compare_layout.py` 导出全部
  `size_of`/`offset_of!` 与编译后 C++ 逐项比对 → **MATCH**。
  **没有** MIT Rust 参照物（EldenKill 无 LICENSE），故无逐字对照。
- **C#**：`compare_layout.py` 把生成的 `Marshal.SizeOf` 断言与编译后 C++ 的 `sizeof` 比对 →
  **尺寸全部 MATCH**（C# 未发射逐字段偏移，故只比尺寸）。
  **没有** C# 工具链，**未编译**；**也没有** MIT 对照物（ValCraft 无 LICENSE），
  仅做结构约定对照，**一个字符都未复制**。→ 标 `推断 / 无 MIT 对照物 / 未编译验证`。
- **Python**：**运行时导入**生成的 ctypes 模块，`ctypes.sizeof` 与字段 `.offset` 全部
  与编译后 C++ **MATCH**（如 `Header=32`、`SkyState=64`、`McState=200`、`WaterGrid=1040`）。
  **未做**：跨进程真跑（不运行任何游戏）。

## 6. 缺陷与修复（本轮独立复核发现）

| # | 缺陷 | 影响 | 修复 |
|---|------|------|------|
| 1 | Rust 结构体字段用保留字 `type`（`McEvent`/`InputEvent`/`ColMsgHeader`） | 生成的 `.rs` **无法编译** | 发射为 raw ident `r#type` |
| 2 | `mapping_name` 反斜杠未转义（C#/Java/Rust/Python） | `"Local\SkyCraft_v1"` 为**非法转义**，编译失败 | 新增 `unescape_c`（还原 schema 的 C 源码转义）+ `c_escape`（按语言再转义）；C++ 仍原样发射 |
| 3 | 尺寸断言误用 WaterGrid 的上限 `0xC00` | C# `CheckLayout()` 会抛异常、Rust `assert!` 会编译失败（真实 `sizeof` 为 `0x410`） | 断言改用真实 `tot`，上限另加 `<=` 断言 |
| 4 | `REGIONS` 与 `EXTRA_SCALARS` 键重叠 | Rust 重复 `pub const`（硬错误）；`kNoWater` 第二份被当作 `i32` 存 `f64` | 在 `plan.build_plan` 去重（保留首次出现） |
| 5 | Rust `ring_produce` 返回类型与 `Some((..))` 不符 | 编译失败 E0308 | 返回类型改为 `Option<(u64,u64)>` |
| 6 | Python 后端缺 seqlock/SPSC 骨架 | 不满足"每种语言都要骨架" | 补齐 `seqlock_read/write`、`ring_produce/consume` |

同一批问题在 `verify_abi.py`（旧自检）里**未能暴露**——它只读断言文本、且把 WaterGrid
按 `<=` 放行；这正是本轮升级为 `compare_layout.py`（真编译器测量）的原因。

## 7. 可复现命令

解释器（绝对路径）：`/home/zjk/.workbuddy/binaries/python/envs/default/bin/python`

```bash
BASE=/home/zjk/WorkBuddy/2026-10-07-20-05-03/passthrough-lab
PY=/home/zjk/.workbuddy/binaries/python/envs/default/bin/python
export PYTHONPATH=$BASE/03-复现路线/v1-ptgen/src

# 生成五语言（默认取 schema 第一个词表）
for L in cpp csharp java rust python; do
  $PY -m ptgen --schema $BASE/03-复现路线/v0-schema/schema.yaml --lang $L \
      --host SKY --out $BASE/03-复现路线/v0-schema/generated
done

# C++ 回归（零差异，exit 0）
$PY $BASE/03-复现路线/v0-schema/verify_roundtrip.py

# 跨语言偏移/尺寸自检（真实编译 g++/rustc + 运行时 ctypes）
$PY $BASE/03-复现路线/v1-ptgen/tests/compare_layout.py

# Java 结构 + 数值 diff
$PY $BASE/03-复现路线/v1-ptgen/tests/diff_java.py
```

`pip install -e .` 在本环境**未实测**：该解释器无 `setuptools`/`wheel` 且无网络。
已改为校验 `pyproject.toml` 可解析、`console_scripts` 目标 `ptgen.cli:main` 可导入且可调用。

## 8. 结论分档

- **已实测**：
  - C++ 逐字节等于 `gen_header.py`；`verify_roundtrip` 三宿主 diff=0、exit 0；
  - 28 结构体的偏移/尺寸：编译后 C++（g++）== Rust（rustc 编译）== Python（运行时 ctypes）
    == Java（常量解析）== C#（断言解析，仅尺寸）；
  - Rust 生成物 rustc 编译 exit 0；生成 C++ 头 g++ 编译 exit 0；
  - Java vs Proto.java：结构差异 373 行、数值覆盖 56/57。
- **据项目自述**：容器一行未动、差异全在词表（T1 结论）。
- **推断 / 未验证**：
  - C# 未编译（无 dotnet）→ 只做尺寸自洽，标"无 MIT 对照物、未验证"；
  - Rust 无 MIT 对照物（EldenKill 无许可）→ 无逐字对照；
  - 未运行任何游戏，未做跨进程联调。

## 9. 产物

`v1-ptgen/`：`pyproject.toml`、`README.md`、`REPORT.md`、
`src/ptgen/{__init__,__main__,cli,schema_io,model,plan}.py`、
`src/ptgen/backends/{cpp,csharp,java,rust,python}.py`、
`tests/{compare_layout,diff_java,verify_abi}.py`。
样例生成物：`v0-schema/generated/{SKY,FO4}.proto.{h,cs,java,rs,py}`（+ `*.sync.{h,cs}`）。
