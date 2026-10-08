# v2-mcp — PTmodmaker MCP server 报告

- 生成时间：2026-10-08T10:37:41
- 版本：**0.2.0**（本次针对「新手可用性实验」暴露的三处缺口做修复）
- 实现方式：**手写 JSON-RPC over stdio**（官方 `mcp` SDK 未安装且禁止联网安装；stdio 传输即逐行 JSON-RPC 2.0，并兼容 Content-Length 分帧）。
- 协议版本：默认 `2024-11-05`，同时接受 `2025-03-26` / `2025-06-18`（按客户端 `initialize` 回显）。
- 工具数：**5**（新增 `pt_schema_describe`）；零额外依赖（仅需 PyYAML，环境已带 6.0.3）。
- 解释器：`python3`。
- 复现：`cd v2-mcp && <python> smoke.py` → 写出 `smoke_log.jsonl`（**19 条** request/response，ids 1–19）；
  本报告所有 request/response 均**摘录自该文件**，未手写。脚手架实测另见 §1.3 的两条命令与原始输出。
- 硬约束遵守：**不启动游戏**；只写 `v2-mcp/`；round-trip 与 stub 都在 `v2-mcp/.work/` 隔离副本内跑，未改动 `v0-*/v1-*`。
- **错误纪律（新增，缺口 A 的核心）**：任何工具失败都返回**结构化** result（`isError:true` + `issues[]`，
  每项含 `path`/`expected`/`got`/`hint`）；异常**绝不**以裸字符串形式泄漏，traceback 只写 stderr。

结论分档：**已实测**=本次真跑并留存证据；**据项目自述**=采信上游文档/库声明；**推断**=未验证。

---

## 0. 变更摘要

| 缺口 | 位置 | 变更 | 档位 |
|---|---|---|---|
| **A** schema 无模板 / 两条隐藏契约只在崩溃时暴露 / 错误是裸异常 | `server.py` | 结构校验重写为 `issues[]`；`handle()` 兜底把异常转结构化错误（traceback→stderr）；新增工具 `pt_schema_describe`（契约 + 带注释 `schema.template.yaml`）；两条契约写进 `pt_schema_validate`/`pt_scaffold` 的 description 与本报告的「快速上手」 | 已实测 |
| **B** round-trip 只认内置 3 宿主 | `server.py` | `pt_schema_validate` 新增 `header_path`：走 extract→generate→结构化 diff 同一套流程；diff≠0 返回**逐行**差异摘要并按 `identifier`/`literal`/`structure_order` 分类 | 已实测 |
| **C** scaffold 闭环断裂（硬编码 SKY / 无 schema_path / alias 到 SKY） | `server.py` | `pt_scaffold` 新增 `schema_path`；**不再 alias、不再回退**；用宿主自身 id 生成 protocol 与 tools；生成自带 `schema.yaml`（共用 container + 本宿主 vocab 骨架）+ `tools/host_preflight.py`；骨架以**可读**方式报「未实现宿主适配器」 | 已实测 |
| **D** 空结果静默（同类小缺口） | `server.py` | `pt_param_lookup` 在宿主未收录时返回 `host_found:false` + 明确 `note` | 已实测 |

**快速上手（把两条隐藏契约写在这里，缺口 A 的一部分）**

1. `container.order` 必须是 **mapping 的列表**，每项 `{kind, key?}`，`kind ∈ regions/var/fixed/optional`。
   写成字符串列表，旧版会直接崩成 `AttributeError: 'str' object has no attribute 'get'`。
2. `container.includes` 恰恰**相反**：必须是**字符串列表**（每条是一整行 `#include`）。
   写成 mapping 列表会让 `gen_header.py` 失败（`TypeError: expected str instance, dict found`）。
3. `vocabulary_schema` 的**顶层键名就是每份 vocabulary 的必填字段名**；值只是说明文本。
   不要写 `{required: [...], optional: [...]}`。
4. 想拿到「schema 的 schema」+ 一份带注释的起点模板：调 **`pt_schema_describe`**。

---

## 1. 新手实验发现的缺口与修复（逐条：缺口 → 修法 → 复测证据）

### 1.1 缺口 A — schema 没有「模板」，契约只在崩溃时暴露

**缺口（已复现）**：干净的 agent 写 `container.includes: ["<cstdint>"]`（字符串列表）+
`container.order: ["header", "host_state"]`（字符串列表）+ `vocabulary_schema: {required: [...], optional: [...]}`，
`pt_schema_validate` 回的是**一个裸异常字符串、零结构信息**：

```json
{"ok": false, "error": "AttributeError: 'str' object has no attribute 'get'"}
```

它只能靠逆读产物 + 二分才试出两条契约，且自描述里一个字都没写。

**修法**
- 结构校验全部改写为**结构化 `issues[]`**（`path`/`expected`/`got`/`hint`），任何一条失败都不再抛异常；
- `handle()` 加兜底：每个工具 handler 的异常都转成结构化错误，traceback 只进 stderr；
- 新增工具 **`pt_schema_describe`**：返回完整契约说明 + **内置带注释的 `schema.template.yaml`**；
- 两条隐藏契约写进 `pt_schema_validate` / `pt_scaffold` 的 **description**（见 §4）与上面的「快速上手」。

**复测证据 A-1 — 同一份"会崩"的 schema，现在返回结构化错误**（`smoke_log.jsonl` id=16，`isError=True`）

request:
```json
{
  "jsonrpc": "2.0",
  "id": 16,
  "method": "tools/call",
  "params": {
    "name": "pt_schema_validate",
    "arguments": {
      "schema_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/_probe/order_as_string_list.yaml"
    }
  }
}
```
response（解析 `content[0].text`；`structure.issues` 每项都带 path/expected/got/hint）:
```json
{
  "tool": "pt_schema_validate",
  "ok": false,
  "schema_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/_probe/order_as_string_list.yaml",
  "header_path": null,
  "structure": {
    "ok": false,
    "issues": [
      {
        "path": "$.container.order",
        "expected": "list[mapping]（每项 {kind, key?}）",
        "got": "list(len=2)",
        "hint": "必填。order 必须是 **mapping 列表**，不是字符串列表，例如 [{'kind':'regions'}, {'kind':'var','key':'host_state'}, {'kind':'fixed','key':'coltri'}]。kind ∈ regions/var/fixed/optional，除 regions 外都要带 key。 首个非 mapping 项：str:'header'"
      },
      {
        "path": "$.vocabularies.TEARDOWN.required",
        "expected": "必填（由 vocabulary_schema 的顶层键名定义）",
        "got": "缺失",
        "hint": "词表 'TEARDOWN' 缺字段 'required'；vocabulary_schema 的顶层键名就是必填字段名。"
      },
      {
        "path": "$.vocabularies.TEARDOWN.optional",
        "expected": "必填（由 vocabulary_schema 的顶层键名定义）",
        "got": "缺失",
        "hint": "词表 'TEARDOWN' 缺字段 'optional'；vocabulary_schema 的顶层键名就是必填字段名。"
      }
    ],
    "warnings": [],
    "summary": {
      "vocabularies": [
        "TEARDOWN"
      ],
      "required_vocab_fields": [
        "required",
        "optional"
      ],
      "order_kinds": [
        "regions",
        "var",
        "fixed",
        "optional"
      ],
      "var_keys": [
        "col_tri_flags",
        "dig_material",
        "header",
        "host_flags",
        "host_state",
        "hurt_flags",
        "input_type",
        "mc_event_type",
        "mc_flags",
        "mc_state",
        "ren_type",
        "tool_kind"
      ]
    },
    "issue_count": 3
  },
  "roundtrip": {
    "harness": "v0-schema/verify_roundtrip.py（隔离镜像副本）",
    "isolated": true,
    "exit_code": 1,
    "hosts": {},
    "conclusion": "FAIL: a MIT host did not round-trip to zero.",
    "stdout": [],
    "stderr": [
      "Traceback (most recent call last):",
      "  File \"<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/schema-cf4sxlba/mirror/03-复现路线/v0-schema/verify_roundtrip.py\", line 106, in <module>",
      "    main()",
      "    ~~~~^^",
      "  File \"<home>/WorkBuddy/202
  …  （截断；完整见 smoke_log.jsonl 中 id=16）
```
> 结果：`container.order` 与 `vocabulary_schema` **两条契约各自被点名**，各自带 expected/got/hint。
> （payload 里 `issues` 共 4 条 = 3 条结构 + 1 条 round-trip 未归零；后者是这份坏 schema 的必然结果。）

**复测证据 A-2 — 新增 `pt_schema_describe`**（id=13；`template` 字段是完整带注释模板，此处截断）

request:
```json
{
  "jsonrpc": "2.0",
  "id": 13,
  "method": "tools/call",
  "params": {
    "name": "pt_schema_describe",
    "arguments": {}
  }
}
```
response（截断 `template`）:
```json
{
  "tool": "pt_schema_describe",
  "ok": true,
  "template_filename": "schema.template.yaml",
  "hidden_contracts": [
    "container.order 必须是 **mapping 的列表**（每项 {kind, key?}）；写成字符串列表会在旧版里直接崩成 AttributeError: 'str' object has no attribute 'get'。",
    "vocabulary_schema 的 **顶层键名就是每份 vocabulary 的必填字段名**；值只是给人读的说明。"
  ],
  "contract": {
    "top_level": {
      "schema_version": "integer（当前为 1）",
      "container": "mapping —— 不变骨架，所有宿主共用；见下",
      "vocabulary_schema": "mapping —— 顶层键名 = 每份 vocabulary 的必填字段名",
      "vocabularies": "mapping[name -> 词表] —— 一个宿主一份；键名即 ptgen --host 的取值"
    },
    "container.includes": {
      "type": "list[str]（必填）",
      "meaning": "原样输出的 #include 行，每条是一整行字符串",
      "example": [
        "#include <cstdint>"
      ],
      "pitfall": "写成 mapping 列表会生成失败（TypeError: expected str instance, dict found）"
    },
    "container.regions_template": {
      "type": "str（必填）",
      "meaning": "regions 段的 C++ 文本；占位符 {host_state_off} -> kOff<host_abbr>State"
    },
    "container.fixed": {
      "type": "mapping[name -> str]（必填，可为空 mapping）",
      "meaning": "每个 fixed 块是一段原样输出的 C++ 文本（结构体/枚举/常量/static_assert）"
    },
    "container.order": {
      "type": "list[mapping]（必填）",
      "meaning": "声明顺序：工具按 order 逐项输出 fixed 块与变量槽位",
      "item": {
        "kind": "regions|var|fixed|optional",
        "key": "除 regions 外必填"
      },
      "example": [
        {
          "kind": "regions"
        },
        {
          "kind": "var",
          "key": "header"
        },
        {
          "kind": "fixed",
          "key": "coltri"
        }
      ],
      "pitfall": "写成字符串列表会崩：AttributeError: 'str' object has no attribute 'get'（旧版就是这样暴露契约的）"
    },
    
  …  （截断；完整见 smoke_log.jsonl 中 id=13）
```
- 返回的模板**自身可过结构校验**：把它落到 `.work/probe/template.yaml` 再 `pt_schema_validate` → `structure.ok=true`、`issues=0`（已实测）。
- 模板里把两条契约写成注释，并给了 `order`/`includes`/`vocabulary_schema` 的**正确写法示例**。

**复测证据 A-3 —— 一条对实验结论的纠正（重要）**

实验报告把两条契约写成"`container.includes` / `container.order` 必须是 mapping 的列表"。
我按实现对照实测，**只有 `order` 是这样**；`includes` 恰恰必须是**字符串列表**：

```text
includes=string-list   -> gen_header rc=0
includes=mapping-list  -> gen_header rc=1, TypeError: sequence item 6: expected str instance, dict found
```

来源：`v0-schema/gen_header.py` 与 `v1-ptgen/backends/cpp.py` 都做 `for inc in c["includes"]: out.append(inc)`
（原样输出，必须可拼接成字符串），而 `order` 是 `item["kind"] / item.get("key")`（必须 mapping）。
→ 所以工具现在把**两条都讲清楚**，并且 `pt_schema_validate` 会分别给出正确/错误的写法提示。
（按分档，本条为**已实测**；实验原结论在此处**有误**。）

---

### 1.2 缺口 B — round-trip 只认内置 3 宿主，新宿主恒 FAIL 且零诊断

**缺口（已复现）**：实验者写的 Teardown 词表 `structure.ok=true`，但 `roundtrip` 恒为
`{"hosts": {}, "exit_code": 1, "conclusion": "FAIL: ..."}`，`stdout` 为空、**零诊断**——
工具对"接第 4 款游戏"根本不工作。

**修法**
- `pt_schema_validate` 新增可选参数 **`header_path`**：传入你自己宿主的真实协议头后，走
  `extract_vocab.py → gen_header.py → 归一化 diff` 的**同一套流程**（隔离镜像里跑，只读 `v0-schema` 的工具脚本）。
- diff≠0 时返回**逐行差异摘要** `roundtrip.diagnostics[]`（`line`/`category`/`expected`/`got`/`hint`）
  与 `counts_by_category`，分类为 **`identifier` / `literal` / `structure_order` / `identifier+literal`**。

**复测证据 B-1 — 你的真实头 + 你的 schema：diff = 0**

request（`header_path` = SkyCraft 真实头；schema 用默认 `v0-schema/schema.yaml`）:
```json
{
  "jsonrpc": "2.0",
  "id": 14,
  "method": "tools/call",
  "params": {
    "name": "pt_schema_validate",
    "arguments": {
      "header_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/90-源码/SkyCraft/protocol/skycraft_protocol.h"
    }
  }
}
```
response:
```json
{
  "tool": "pt_schema_validate",
  "ok": true,
  "schema_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v0-schema/schema.yaml",
  "header_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/90-源码/SkyCraft/protocol/skycraft_protocol.h",
  "structure": {
    "ok": true,
    "issues": [],
    "warnings": [],
    "summary": {
      "vocabularies": [
        "SKY",
        "FO4"
      ],
      "required_vocab_fields": [
        "namespace",
        "host_abbr",
        "magic",
        "version",
        "mapping_name",
        "units_per_block",
        "host_flags",
        "host_state",
        "mc_flags",
        "mc_state",
        "input_type",
        "hurt_flags",
        "mc_event_type",
        "ren_type",
        "col_tri_flags"
      ],
      "order_kinds": [
        "regions",
        "var",
        "fixed",
        "optional"
      ],
      "var_keys": [
        "col_tri_flags",
        "dig_material",
        "header",
        "host_flags",
        "host_state",
        "hurt_flags",
        "input_type",
        "mc_event_type",
        "mc_flags",
        "mc_state",
        "ren_type",
        "tool_kind"
      ]
    },
    "issue_count": 0
  },
  "roundtrip": {
    "mode": "custom-header",
    "isolated": true,
    "exit_code": 0,
    "ok": true,
    "harness": "v0-schema/extract_vocab.py + gen_header.py（隔离镜像副本）",
    "header_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/90-源码/SkyCraft/protocol/skycraft_pro
  …  （截断；完整见 smoke_log.jsonl 中 id=14）
```
> `roundtrip.mode = "custom-header"`，`structural_diff = 0`，`conclusion = PASS`。**内置宿主的 0 差额是复现出来的，不是写死的。**

**复测证据 B-2 — 故意改坏 container 两处，诊断逐行点名并分类**（id=15，`isError=True`）

我构造了一份 schema：把 `ColType` 里 `kColClear = 1` 改成 `= 9`（字面量），把 `ColRegion` 里 `maxX` 改成 `mxX`（标识符）。
request 同 B-1 但 `schema_path` 指向该 schema：
```json
{
  "jsonrpc": "2.0",
  "id": 15,
  "method": "tools/call",
  "params": {
    "name": "pt_schema_validate",
    "arguments": {
      "schema_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/_probe/perturbed_container.yaml",
      "header_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/90-源码/SkyCraft/protocol/skycraft_protocol.h"
    }
  }
}
```
response（截断）:
```json
{
  "tool": "pt_schema_validate",
  "ok": false,
  "schema_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/_probe/perturbed_container.yaml",
  "header_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/90-源码/SkyCraft/protocol/skycraft_protocol.h",
  "structure": {
    "ok": true,
    "issues": [],
    "warnings": [],
    "summary": {
      "vocabularies": [
        "SKY",
        "FO4"
      ],
      "required_vocab_fields": [
        "namespace",
        "host_abbr",
        "magic",
        "version",
        "mapping_name",
        "units_per_block",
        "host_flags",
        "host_state",
        "mc_flags",
        "mc_state",
        "input_type",
        "hurt_flags",
        "mc_event_type",
        "ren_type",
        "col_tri_flags"
      ],
      "order_kinds": [
        "regions",
        "var",
        "fixed",
        "optional"
      ],
      "var_keys": [
        "col_tri_flags",
        "dig_material",
        "header",
        "host_flags",
        "host_state",
        "hurt_flags",
        "input_type",
        "mc_event_type",
        "mc_flags",
        "mc_state",
        "ren_type",
        "tool_kind"
      ]
    },
    "issue_count": 0
  },
  "roundtrip": {
    "mode": "custom-header",
    "isolated": true,
    "exit_code": 0,
    "ok": false,
    "harness": "v0-schema/extract_vocab.py + gen_header.py（隔离镜像副本）",
    "header_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/90-源码/SkyCraft/protocol/skycraft_protocol.h",
    "schema_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/_probe/perturbed_container.yaml",
    "extract": {
      "exit_code": 0,
      "stdout": "wrote <home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/hdr-8p6z1dx6/extracted_vocab.yaml",
      "stderr": null
    },
    "generate": {
      "exit_code": 0,
      "stdout": "wrote <home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-m
  …  （截断；完整见 smoke_log.jsonl 中 id=15）
```
> 结果：`structural_diff = 2`，`counts_by_category = {"identifier":1,"literal":1,...}`，
> `diagnostics` 精确给出**哪一行**（408 / 434）、**差在哪一类**、以及各自的修复提示。
> 这正是实验者当年拿不到、只能靠 ABI 断言炸出来才发现的东西。

---

### 1.3 缺口 C — scaffold 的闭环是断的

**缺口（已复现）**：实验者 `pt_scaffold(host="teardown", ...)` 后
① 生成的 `tools/run_demo.py` **硬编码 `L.verify("SKY")`** → 实测 `unknown host 'SKY'; have ['TD']`；
② `pt_scaffold` **没有 `schema_path`** → 永远读默认 `v0-schema/schema.yaml`；
③ `vocabulary` 是**默认回退**到别家（SKY）的词表 → 用户以为可以照抄。
三者任一成立，闭环就断了。

**修法**
- 新增 `schema_path` 参数；`pt_scaffold` 生成**自带**的 `out_dir/schema.yaml`
  （共用 `container`（不变骨架）+ 本宿主 vocab），`protocol/` 与 `tools/` 都只读它，**不再依赖 `v0-schema/`**。
- **删掉全部 alias / 默认回退逻辑**：解析顺序只有 `schema-key-match` → `schema-field-match(host_prefix/namespace)`；
  都没命中就用**用户传入 host 自身派生的 id**（`teardown` → `teardown`）建一份**骨架词表**
  （带 `__scaffold_status__: skeleton`），**绝不 alias 到 SKY**。
- `protocol/` 用**本宿主 id** 生成（`teardown.proto.h`）；`tools/` 的 6 个脚本按宿主 id **逐文件重写**
  （`SKYState→teardownState`、`kOffSkyState→kOffTeardownState`、`skyrimPid→teardownPid`、`"SKY"→"teardown"`…），
  并新增 `tools/host_preflight.py`：跑场景前先做**可读**的「宿主适配器是否就绪」检查，退出码 2。

**复测证据 C-1 — 造一个假的新宿主 `teardown`**（id=17）

request:
```json
{
  "jsonrpc": "2.0",
  "id": 17,
  "method": "tools/call",
  "params": {
    "name": "pt_scaffold",
    "arguments": {
      "host": "teardown",
      "guest": "Minecraft: Java Edition",
      "out_dir": ".work/scaffold_teardown"
    }
  }
}
```
response（截断 `does_not`）:
```json
{
  "tool": "pt_scaffold",
  "ok": true,
  "host": "teardown",
  "guest": "Minecraft: Java Edition",
  "out_dir": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/scaffold_teardown",
  "schema_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v0-schema/schema.yaml",
  "schema_used": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/scaffold_teardown/schema.yaml",
  "vocab": {
    "key": "teardown",
    "resolution": "new-host (own id; never aliased to a built-in)",
    "is_new_host": true,
    "marker": "skeleton"
  },
  "generated": {
    "protocol": {
      "cpp": {
        "exit_code": 0,
        "stdout": "[cpp] wrote 439 lines -> <home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/scaffold_teardown/protocol/teardown.proto.h (+sync 57 lines)",
        "stderr": null
      },
      "python": {
        "exit_code": 0,
        "stdout": "[python] wrote 731 lines -> <home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/scaffold_teardown/protocol/teardown.proto.py",
        "stderr": null
      }
    },
    "tools": [
      "layout_from_schema.py",
      "fake_host.py",
      "fake_guest.py",
      "run_demo.py",
      "negative_control.py",
      "render_demo.py",
      "host_preflight.py"
    ],
    "tool_host_rewrites": {
      "layout_from_schema.py": 8,
      "fake_host.py": 6,
      "fake_guest.py": 7,
      "run_demo.py": 3,
      "negative_control.py": 1,
      "render_demo.py": 0
    },
    "todo_measure": {
      "red_count": 11,
      "scope": "按客侧匹配（宿主未命中）"
    }
  },
  "manifest": [
    "README.md",
    "TODO-MEASURE.md",
    "protocol/teardown.proto.h",
    "protocol/teardown.proto.py",
    "protocol/teardown.sync.h",
    "schema.yaml",
    "tools/fake_guest.py",
    "tools/fake_host.py",
    "tools/host_preflight.py",
    "tools/layout_from_schema.py",
    "tools/negative_control.py",
    "tools/render_demo.py",
    "tools/run_demo.py"
  ],
  "warnings": [
    "宿主 'teardown' 未在你的 schema 中注册：**没有** alias 到任何内置宿主；已用你宿主的 id 'teardown' 生成一份**骨架词表**（占位值）。接新宿主的固定成本就是「填这张词表」：补完 schema.yaml 的 vocabularies.teardown 再把 __scaffold_sta
  …  （截断；完整见 smoke_log.jsonl 中 id=17）
```
> 关键字段：`vocab.key = "teardown"`、`resolution = "new-host (own id; never aliased to a built-in)"`、
> `marker = "skeleton"`、`manifest` 含 `schema.yaml` 与 `protocol/teardown.proto.h`。

**复测证据 C-2 — 真把生成的脚本跑起来（① 骨架状态：给出可读的"缺什么"）**

```bash
$ cd v2-mcp/.work/scaffold_teardown && python3 tools/run_demo.py
退出码: 2
```

stderr（**没有任何 traceback，也不再是 `unknown host 'SKY'`**）:
```text
==============================================================================
[teardown] 未实现宿主适配器：host 'teardown' 的词表仍是 pt_scaffold 生成的骨架（占位值）。
  schema : <home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/scaffold_teardown/schema.yaml
  本脚手架不臆造宿主词表——「填一张词表」正是接新宿主的固定成本，必须由你给真值。

  要补的东西：
  - host_state.fields / size —— 你宿主的状态字段与 static_assert 尺寸（🔴 必须实测）
  - mc_state.fields / size —— 客侧状态字段与尺寸（🔴 必须实测）
  - host_flags / mc_flags / input_type / hurt_flags / mc_event_type / ren_type —— 各枚举的成员名与取值（🔴 必须实测）
  - magic / version / mapping_name / units_per_block —— 协议标识与单位；取值约定见 schema.template.yaml
  - host_prefix / host_abbr / namespace —— 标识符命名（驱动 Header 字段名与 <Abbr>State 名）

  步骤：
    1) 按 TODO-MEASURE.md 实测其中的 🔴 项；
    2) 把真值写进 schema.yaml 的 vocabularies.teardown；
    3) 把 __scaffold_status__ 改为 implemented（或删掉该键）；
    4) 重跑本脚本。
==============================================================================
```
> 对比实验者遇到的那行 `unknown host 'SKY'`：现在是**点名宿主、列出证据、给出 4 步修法**的可读消息。

**复测证据 C-3 — 补上一份真实词表后，闭环真的跑通**

我另做了一份"用户提供的"完整 schema（把 SKY 词表克隆到新键 `teardown` 下并重命名标识符），再 `pt_scaffold(schema_path=…)`：

```bash
$ cd v2-mcp/.work/scaffold_teardown_full && python3 tools/run_demo.py
退出码: 0
```

stdout（**host=teardown，三场景全过**）:
```text
[layout_from_schema] host=teardown structs=28 consts=41 enums=108 mapping_bytes=200327168
    sizeof(Header) = 32
    sizeof(teardownState) = 64
    sizeof(McState) = 200
    sizeof(ColTri) = 40
    sizeof(ColRegion) = 32
    sizeof(McEvent) = 32
[layout_from_schema] schema<->ctypes assertions: PASS
  scenario a: PASS
  scenario b: PASS
  scenario c: PASS
  OVERALL: PASS
```
> 这一次 `vocab.resolution = "schema-key-match"`、`is_new_host = false`、无骨架标记、无 warnings。
> ⚠ 诚实标注：这份 fixture 的词表是 **SKY 词表的克隆**，只用来证明**管线**（protocol 命名、tools 重写、schema 自包含、preflight、ABI 断言）真的通了；
> 它**不证明** Teardown 的真实数值正确——后者仍是 🔴 必须实测（见 `TODO-MEASURE.md`）。

---

### 1.4 缺口 D（同类小缺口，一并修了）

**缺口**：`pt_param_lookup(host="teardown")` 返回 `matched=0` 就完了，没有"该宿主未收录"的提示，
实验者只能从 `library.seed_count=9` 反推。**修法**：未收录时返回 `host_found:false` + 明确 `note`。
**复测证据**（id=19）：
```json
{
  "tool": "pt_param_lookup",
  "filter": {
    "host": "teardown",
    "color": null
  },
  "library": {
    "library": "PTmodmaker params (v0-seed)",
    "license": "CC0-1.0",
    "pulled_on": "2026-10-07",
    "verified_on_hardware": false,
    "seed_count": 9,
    "param_count": 35,
    "color_distribution": {
      "green": 14,
      "yellow": 10,
      "red": 11
    },
    "evidence_distribution": {
      "repo": 8,
      "doc": 20,
      "inference": 7
    },
    "do_not_package_count": 7,
    "caveats": [
      "SkyCraft 的 yaw/pitch 在 DESIGN 中并未写死，作者注明 'Phase 0 with a test' 实测标定 —— 故本库不设数值，只记 'must-measure'。",
      "任务简报中 'SkyCraft: yaw = 180 - heading' 为误植；该式属于 GTA 版（minecraft-gta5-passthrough），已按解剖文档修正。",
      "ValCraft / New VegasCraft 无 LICENSE；据硬约束，ValCraft 参数一律 evidence=inference 且 do_not_package=true，不可默认打包。"
    ]
  },
  "cli_exit_code": 1,
  "cli_output": "",
  "match
  …  （截断；完整见 smoke_log.jsonl 中 id=19）
```

---

## 2. 冒烟调用记录（真实摘录）

### initialize（id=1） / notifications/initialized（无响应，符合规范）
request:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "smoke",
      "version": "0"
    }
  }
}
```
response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {
        "listChanged": false
      }
    },
    "serverInfo": {
      "name": "ptmodmaker-mcp",
      "version": "0.2.0"
    }
  }
}
```

### tools/list（id=2）
返回 **5** 个工具：pt_schema_validate, pt_schema_describe, pt_param_lookup, pt_stub_run, pt_scaffold

### pt_schema_validate（默认 schema_path，内置 3 宿主 round-trip）（id=3）
request:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "pt_schema_validate",
    "arguments": {}
  }
}
```
response（截断）:
```json
{
  "tool": "pt_schema_validate",
  "ok": true,
  "schema_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v0-schema/schema.yaml",
  "header_path": null,
  "structure": {
    "ok": true,
    "issues": [],
    "warnings": [],
    "summary": {
      "vocabularies": [
        "SKY",
        "FO4"
      ],
      "required_vocab_fields": [
        "namespace",
        "host_abbr",
        "magic",
        "version",
        "mapping_name",
        "units_per_block",
        "host_flags",
        "host_state",
        "mc_flags",
        "mc_state",
        "input_type",
        "hurt_flags",
        "mc_event_type",
        "ren_type",
        "col_tri_flags"
      ],
      "order_kinds": [
        "regions",
        "var",
        "fixed",
        "optional"
      ],
      "var_keys": [
        "col_tri_flags",
        "dig_material",
        "header",
        "host_flags",
        "host_state",
        "hurt_flags",
        "input_type",
        "mc_event_type",
        "mc_flags",
        "mc_state",
        "ren_type",
        "tool_kind"
      ]
    },
    "issue_count": 0
  },
  "roundtrip": {
    "harness": "v0-schema/verify_roundtrip.py（隔离镜像副本）",
    "isolated": true,
    "exit_code": 0,
    "hosts": {
      "SKY": {
        "license": "MIT",
        "structural_diff": 0,
        "pass_target": true
      },
      "FO4": {
        "license": "MIT",
        "structural_diff": 0,
        "pass_target": true
      },
      "VAL": {
        "license": "none",
        "structural_diff": 0,
        "pass_target": false
      }
    },
    "conclusion": "PASS: both MIT hosts round-trip to zero structural difference.",
    "stdout": [
      "SKY (MIT ): structural diff = 0  [SKY.h]",
      "FO4 (MIT ): structural diff = 0  [FO4.h]",
      "VAL (none): s
  …  （截断；完整见 smoke_log.jsonl 中 id=3）
```

### pt_param_lookup(host=skyrim, color=red)（id=4）/ pt_param_lookup(color=red)（id=5）
request:
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "pt_param_lookup",
    "arguments": {
      "host": "skyrim",
      "color": "red"
    }
  }
}
```
response（截断；完整见 smoke_log.jsonl）:
```json
{
  "tool": "pt_param_lookup",
  "filter": {
    "host": "skyrim",
    "color": "red"
  },
  "library": {
    "library": "PTmodmaker params (v0-seed)",
    "license": "CC0-1.0",
    "pulled_on": "2026-10-07",
    "verified_on_hardware": false,
    "seed_count": 9,
    "param_count": 35,
    "color_distribution": {
      "green": 14,
      "yellow": 10,
      "red": 11
    },
    "evidence_distribution": {
      "repo": 8,
      "doc": 20,
      "inference": 7
    },
    "do_not_package_count": 7,
    "caveats": [
      "SkyCraft 的 yaw/pitch 在 DESIGN 中并未写死，作者注明 'Phase 0 with a test' 实测标定 —— 故本库不设数值，只记 'must-measure'。",
      "任务简报中 'SkyCraft: yaw = 180 - heading' 为误植；该式属于 GTA 版（minecraft-gta5-passthrough），已按解剖文档修正。",
      "ValCraft / New VegasCraft 无 LICENSE；据硬约束，ValCraft 参数一律 evidence=inference 且 do_not_package=true，不可默认打包。"
    ]
  },
  "cli_exit_code": 1,
  "cli_output": "",
  "matched": 4,
  "counts_by_color": {
    "green": 0,
    "yellow": 0,
    "red": 4
  },
  "records": [
    
  …  （截断；完整见 smoke_log.jsonl 中 id=4）
```

### pt_stub_run(scenario=heartbeat)（id=6）/ (scenario=all)（id=7）
request:
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "pt_stub_run",
    "arguments": {
      "scenario": "heartbeat"
    }
  }
}
```
response（截断；逐场景 trace 已剔除）:
```json
{
  "tool": "pt_stub_run",
  "scenario": "heartbeat",
  "ok": true,
  "transport": "共享内存映射（MAP_SHARED over a file）——非真游戏，非真 IPC 驱动",
  "results": {
    "heartbeat": {
      "host_killed_at_s": 1.8,
      "guest_froze": true,
      "frozen_ticks": 114,
      "stayed_frozen_to_exit": true,
      "guest_exit_code": 0,
      "guest_stderr": "",
      "crashed": false,
      "passed": true
    }
  },
  "verdict": {
    "heartbeat": true
  },
  "overall": "PASS",
  "stdout": [],
  "stderr": null,
  "exit_code": 0,
  "evidence_level": "已实测",
  "evidence_note": "假桩进程（fake_host/fake_guest）真实执行；但这证明的是协议与状态机，不是真游戏集成。",
  "does_not": [
    "不启动任何真游戏；宿主/客侧都是 Python 假桩。",
    "不测真引擎的插件加载、反作弊、画面合成或显卡路径。",
    "不写 v1-stubs：每次在 v2-mcp/.work 下的隔离副本中运行。"
  ]
}
```
> id=7（all）`overall = PASS`（heartbeat/epoch/collision_wall 三场景全过）。

### pt_scaffold（已注册宿主：Skyrim → field-match SKY）（id=8）
request:
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "tools/call",
  "params": {
    "name": "pt_scaffold",
    "arguments": {
      "host": "The Elder Scrolls V: Skyrim Special Edition",
      "guest": "Minecraft: Java Edition",
      "out_dir": ".work/scaffold_demo"
    }
  }
}
```
response（截断）:
```json
{
  "tool": "pt_scaffold",
  "ok": true,
  "host": "The Elder Scrolls V: Skyrim Special Edition",
  "guest": "Minecraft: Java Edition",
  "out_dir": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/scaffold_demo",
  "schema_path": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v0-schema/schema.yaml",
  "schema_used": "<home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/scaffold_demo/schema.yaml",
  "vocab": {
    "key": "SKY",
    "resolution": "schema-field-match(skyrim)",
    "is_new_host": false,
    "marker": null
  },
  "generated": {
    "protocol": {
      "cpp": {
        "exit_code": 0,
        "stdout": "[cpp] wrote 519 lines -> <home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/scaffold_demo/protocol/SKY.proto.h (+sync 57 lines)",
        "stderr": null
      },
      "python": {
        "exit_code": 0,
        "stdout": "[python] wrote 838 lines -> <home>/WorkBuddy/2026-10-07-20-05-03/passthrough-lab/03-复现路线/v2-mcp/.work/scaffold_demo/protocol/SKY.proto.py",
        "stderr": null
      }
    },
    "tools": [
      "layout_from_schema.py",
      "fake_host.py",
      "fake_guest.py",
      "run_demo.py",
      "negative_control.py",
      "render_demo.py",
      "host_preflight.py"
    ],
    "tool_host_rewrites": {
      "layout_from_schema.py": 9,
      "fake_host.py": 6,
      "fake_guest.py": 7,
      "run_demo.py": 3,
      "negative_control.py": 1,
      "re
  …  （截断；完整见 smoke_log.jsonl 中 id=8）
```

---

## 3. 安全拦截用例（工具层拒绝，必须全 refused）

新增的 `pt_schema_describe` 也在同一道闸门之后，所以拒绝用例从 4 条扩到 5 条。**全部 refused（已实测）**：

| id | 工具 | 命中 | `isError` |
|---|---|---|---|

| 9 | `pt_scaffold` | 含联机/多人语义 'online' | True |
| 10 | `pt_scaffold` | 指向服务端地址（URL scheme） | True |
| 11 | `pt_param_lookup` | 含联机/多人语义 'fivem' | True |
| 12 | `pt_stub_run` | 含联机/多人语义 'multiplayer' | True |
| 18 | `pt_schema_describe` | 指向服务端地址（URL scheme） | True |

逐条 request/response：


#### id=9 → gate `safety/network-multiplayer`，isError=True
arguments:
```json
{"host": "GTA Online", "guest": "Minecraft", "out_dir": ".work/denied1"}
```
hits:
```json
[
  {
    "field": "$.host",
    "value": "GTA Online",
    "reason": "含联机/多人语义 'online'"
  }
]
```
> 本项目的真实事故先例：passthrough 桥会把一侧的输入事件自动注入另一侧，开发中曾差点把合成出来的击键打进 GTA Online 的落地页（联机/在线服务）。因此任何联机、多人、反作弊或指向服务端地址的输入都在工具层被直接拒绝。

#### id=10 → gate `safety/network-multiplayer`，isError=True
arguments:
```json
{"host": "Skyrim", "guest": "Minecraft", "out_dir": "ws://10.0.0.5:7777/sync"}
```
hits:
```json
[
  {
    "field": "$.out_dir",
    "value": "ws://10.0.0.5:7777/sync",
    "reason": "指向服务端地址（URL scheme）"
  }
]
```
> 本项目的真实事故先例：passthrough 桥会把一侧的输入事件自动注入另一侧，开发中曾差点把合成出来的击键打进 GTA Online 的落地页（联机/在线服务）。因此任何联机、多人、反作弊或指向服务端地址的输入都在工具层被直接拒绝。

#### id=11 → gate `safety/network-multiplayer`，isError=True
arguments:
```json
{"host": "fivem server 51.83.1.20"}
```
hits:
```json
[
  {
    "field": "$.host",
    "value": "fivem server 51.83.1.20",
    "reason": "含联机/多人语义 'fivem'"
  }
]
```
> 本项目的真实事故先例：passthrough 桥会把一侧的输入事件自动注入另一侧，开发中曾差点把合成出来的击键打进 GTA Online 的落地页（联机/在线服务）。因此任何联机、多人、反作弊或指向服务端地址的输入都在工具层被直接拒绝。

#### id=12 → gate `safety/network-multiplayer`，isError=True
arguments:
```json
{"scenario": "multiplayer"}
```
hits:
```json
[
  {
    "field": "$.scenario",
    "value": "multiplayer",
    "reason": "含联机/多人语义 'multiplayer'"
  }
]
```
> 本项目的真实事故先例：passthrough 桥会把一侧的输入事件自动注入另一侧，开发中曾差点把合成出来的击键打进 GTA Online 的落地页（联机/在线服务）。因此任何联机、多人、反作弊或指向服务端地址的输入都在工具层被直接拒绝。

#### id=18 → gate `safety/network-multiplayer`，isError=True
arguments:
```json
{"schema_path": "ws://10.0.0.5:7777/x"}
```
hits:
```json
[
  {
    "field": "$.schema_path",
    "value": "ws://10.0.0.5:7777/x",
    "reason": "指向服务端地址（URL scheme）"
  }
]
```
> 本项目的真实事故先例：passthrough 桥会把一侧的输入事件自动注入另一侧，开发中曾差点把合成出来的击键打进 GTA Online 的落地页（联机/在线服务）。因此任何联机、多人、反作弊或指向服务端地址的输入都在工具层被直接拒绝。


> 另外 `pt_stub_run(scenario="multiplayer")`（id=12）也在**工具层**被拒（不是靠端内校验）。

---

## 4. 五个工具的 description 全文（供人工复审自描述质量）

### `pt_schema_validate`

inputSchema:
```json
{
  "type": "object",
  "properties": {
    "schema_path": {
      "type": "string",
      "description": "schema.yaml 路径（绝对或相对 03-复现路线/）。默认 v0-schema/schema.yaml。"
    },
    "header_path": {
      "type": "string",
      "description": "可选。你自己宿主的真实协议头（.h）。传入后走 extract→generate→结构化 diff 的同一套流程，并为新宿主返回逐行差异诊断（按 标识符/字面量/结构顺序 分类），不再只对内置 3 宿主跑。"
    }
  },
  "additionalProperties": false
}
```

description:
```text
校验一份 schema.yaml 的**结构**，并做 extract→generate→structural-diff 的 round-trip，返回每个宿主的**结构性 diff 数**；失败时一定是**结构化错误**（issues[] 每项含 path/expected/got/hint），绝不抛裸异常。
输入: {schema_path?（默认 v0-schema/schema.yaml）, header_path?（你自己宿主的真实协议头）}。
  - 不传 header_path：对内置三份真实头（SkyCraft/FO4/ValCraft）跑 round-trip。
  - 传了 header_path：对你的宿主跑同一套流程（extract_vocab → gen_header → 归一化 diff），diff≠0 时返回逐行差异摘要并按 标识符(identifier)/字面量(literal)/结构顺序(structure_order) 分类（roundtrip.diagnostics + counts_by_category）。**这是「接第 4 款游戏」能自证的地方。**
输出: {ok, schema_path, header_path, structure:{ok,issues[],warnings[],summary,issue_count}, roundtrip:{mode,exit_code,hosts|diagnostics,counts_by_category,conclusion}, evidence_level, does_not}。
**两条隐藏契约（旧版只在崩溃时暴露，现在写在这里）**：
  ① `container.order` 必须是 **mapping 的列表**（每项 {kind, key?}，kind ∈ regions/var/fixed/optional）——写成字符串列表旧版会崩成 `AttributeError: 'str' object has no attribute 'get'`。注意 `container.includes` **相反**，必须是**字符串列表**（每条是一整行 #include；写成 mapping 列表会让 gen_header 报 TypeError）。
  ② `vocabulary_schema` 的**顶层键名就是每份 vocabulary 的必填字段名**；值只是说明文本。不要写成 {required:[...], optional:[...]}，否则工具会反过来要求你的词表拥有名为 'required'/'optional' 的字段。（完整契约 + 带注释模板：调 pt_schema_describe。）
证据档: 已实测（真跑 extract/gen_header；SKY/FO4 为 MIT，目标 diff=0；VAL 无 LICENSE，仅作表达力参考，不作为通过/失败判据）。
它不会做: 不校验 C++ 表达式的语义正确性（只做结构键检查，语义交给实际生成暴露）；不修改 schema；不写 v0-*（round-trip 在 v2-mcp/.work 的隔离镜像中跑）；不启动任何游戏。
```

### `pt_schema_describe`

inputSchema:
```json
{
  "type": "object",
  "properties": {
    "schema_path": {
      "type": "string",
      "description": "可选。传了就顺带体检这份 schema（返回它的结构 issues/warnings）。"
    }
  },
  "additionalProperties": false
}
```

description:
```text
返回 **schema.yaml 的契约说明**（每个字段的类型/是否必填/含义），以及一份**带注释的 `schema.template.yaml`** 作为你写词表的起点。这是「schema 的 schema」——旧版完全缺失，新手只能靠逆读产物 + 二分反推。
输入: {schema_path?（可选，顺带体检这份 schema）}。
输出: {ok, template_filename, hidden_contracts[], contract:{top_level, container.includes, container.regions_template, container.fixed, container.order{type,item,example,pitfall}, vocabulary_schema{type,meaning,pitfall}, vocabulary_fields, order_var_keys, order_optional_keys}, template(带注释 YAML 全文), observed?, evidence_level, does_not}。
**两条隐藏契约**（也返回在 hidden_contracts 里）：
  ① container.order 必须是 **mapping 列表**（{kind, key?}）；container.includes 必须是 **字符串列表**。
  ② vocabulary_schema 的**顶层键名 = 每份 vocabulary 的必填字段名**。
证据档: 已实测（契约来自对 gen_header.py / ptgen cpp backend 的实现阅读 + 对照实测：includes=字符串列表可用、=mapping 列表使 gen_header 失败；order=字符串列表触发 AttributeError）。
它不会做: 不修改任何 schema；不替你填词表真值；不校验语义（语义交给 pt_schema_validate 的 round-trip）。
```

### `pt_param_lookup`

inputSchema:
```json
{
  "type": "object",
  "properties": {
    "host": {
      "type": "string",
      "description": "宿主名子串（大小写不敏感），如 skyrim / valheim / gta。"
    },
    "color": {
      "type": "string",
      "enum": [
        "green",
        "yellow",
        "red"
      ],
      "description": "复用档：green 可直搬 / yellow 需复核 / red 必须实测。"
    }
  },
  "additionalProperties": false
}
```

description:
```text
查询 PTmodmaker 参数库（CC0 种子库），返回带**出处与证据档**的记录。
输入: {host?（子串匹配）, color?（green/yellow/red）}。
输出: {filter, cli_output（param_lookup.py 原文）, matched, counts_by_color, records:[{id,host,guest,param,value,unit,reuse_level,evidence,source:{repo,commit,doc},verified_on_hardware,do_not_package,notes}], library(meta), does_not}。
证据档: 据项目自述——库中**全部**参数 verified_on_hardware=false；每条记录的 evidence 为 repo（读源码）/doc（项目自述）/inference（推断）三档之一；do_not_package=true 者不可默认打包（如 ValCraft 无 LICENSE）。
它不会做: 不验证参数真值（本库无实机验证数值）；不提供代码片段（无出处参数不入库）；不联网重拉上游仓库。
```

### `pt_stub_run`

inputSchema:
```json
{
  "type": "object",
  "properties": {
    "scenario": {
      "type": "string",
      "enum": [
        "heartbeat",
        "epoch",
        "collision_wall",
        "all"
      ],
      "description": "heartbeat=宿主心跳超时安全冻结；epoch=宿主重启后陈旧数据丢弃；collision_wall=>50° 不可攀爬墙；all=三个都跑。默认 all。"
    }
  },
  "additionalProperties": false
}
```

description:
```text
运行假桩（fake_host ↔ fake_guest）场景，验证传输与状态机，**不启动任何游戏**。
输入: {scenario: heartbeat|epoch|collision_wall|all}。
输出: {scenario, transport, results:{<scenario>:{passed, 关键数值...}}, verdict, overall:PASS|FAIL, stdout, exit_code, does_not}。关键数值示例：heartbeat→guest_froze/frozen_ticks；epoch→session_discards/max_single_tick_dx/late_teleports；collision_wall→guest_max_x/crossed_wall/climbed_wall/blocked_ticks。
证据档: 已实测（假桩真实执行；但只证明协议与状态机，不等于真游戏集成）。
它不会做: 不启动真游戏；不测真引擎的插件加载/反作弊/画面合成/显卡路径；不写 v1-stubs（每次在 v2-mcp/.work 的隔离副本中运行）。
```

### `pt_scaffold`

inputSchema:
```json
{
  "type": "object",
  "properties": {
    "host": {
      "type": "string",
      "description": "宿主游戏名，如 'The Elder Scrolls V: Skyrim Special Edition' 或新宿主 'teardown'。"
    },
    "guest": {
      "type": "string",
      "description": "客侧游戏名，如 'Minecraft: Java Edition'。"
    },
    "out_dir": {
      "type": "string",
      "description": "输出目录（绝对，或相对 v2-mcp/）。"
    },
    "schema_path": {
      "type": "string",
      "description": "可选。你的 schema.yaml（绝对或相对 03-复现路线/）。默认 v0-schema/schema.yaml。宿主在其中注册了就按它生成；没注册就用你传入的 host 自身 id 生成**骨架词表**（绝不 alias/回退到内置宿主）。"
    }
  },
  "required": [
    "host",
    "guest",
    "out_dir"
  ],
  "additionalProperties": false
}
```

description:
```text
为一个 host↔guest 生成**适配器骨架**（不是可用成品）。
输入: {host, guest, out_dir（均必填）, schema_path?}。
输出: 目录含 `schema.yaml`（**自带的** schema：共用 container + 本 host 的 vocab）、`protocol/`（ptgen 为**本 host 的 id** 生成的多语言协议头，如 `teardown.proto.h`）、`tools/`（假桩 harness 拷贝**并按 host id 重写**，含 `host_preflight.py`）、`README.md`、`TODO-MEASURE.md`（从 v0-params/params.yaml 现筛的 🔴 必须实测清单，含出处，**非硬编码**）。返回 {host, guest, out_dir, schema_used, vocab:{key,resolution,is_new_host,marker}, generated:{protocol,tools,tool_host_rewrites,todo_measure}, manifest, warnings, does_not}。
**闭环保证（旧版是断的）**：
  - 生成的 `protocol/` 用**你宿主的 id**，不硬编码 SKY；`tools/` 里的运行脚本也引用该 id，不再出现 `unknown host 'SKY'`。
  - 宿主未注册时**绝不 alias / 回退到别家词表**：改用你宿主的 id 生成一份 `__scaffold_status__: skeleton` 的**骨架词表**；此时 `python tools/run_demo.py` 会给出**可读的**「未实现宿主适配器」提示（列出缺什么、怎么补），退出码 2。
  - **隐藏契约**：`container.order` 必须是 **mapping 列表**（{kind, key?}）、`vocabulary_schema` 的**顶层键名即词表必填字段名**——这两条旧版只在崩溃时暴露，现已在 pt_schema_validate / pt_schema_describe 里说明。`container.includes` 则必须是**字符串列表**（每条一整行 #include）。
证据档: 已实测（ptgen 真实生成 + params.yaml 真实筛选）。
它不会做: **不生成宿主侧 natives/SDK 调用代码**（SKSE/F4SE/内存 hook）——那依赖真机的脚本名、函数签名与偏移，是 🔴 必须实测的部分，本工具拒绝臆造；不生成画面合成器；不生成可用成品（客侧 mod 与启动器仅占位）；不为联机/多人/反作弊环境生成任何东西；不写 v0-*/v1-*。
```

---

## 5. 故意没做的能力 / 只修到一半的

| 能力 / 缺口 | 现状 | 为什么 | 档位 |
|---|---|---|---|
| 宿主侧 natives / SDK 调用代码生成（SKSE / F4SE / 内存 hook） | ❌ 不做 | 依赖真机脚本名、函数签名与内存偏移；属 🔴 必须实测，臆造即错误代码 | 必须实测 |
| 画面合成器 / overlay 合成 | ❌ 不做 | 依赖真引擎渲染路径（D3D/Vulkan 挂点、GL readbuffer 陷阱），无法离线生成 | 必须实测 |
| 真游戏集成测试 / 反作弊兼容 | ❌ 不做 | 硬约束不运行任何游戏，也不碰联机/反作弊环境 | 不适用 |
| 联机 / 多人 / 服务端对接（任何形式） | ❌ 拒绝 | 有真实事故先例（自动输入注入差点打进 GTA Online 落地页）；工具层直接拒绝 | 拒绝 |
| **结构校验仍不校验 ABI 尺寸语义**（🔴 **只修一半**） | ⚠ 半修 | `pt_schema_validate` 只做**键/类型**检查；`static_assert(sizeof(X)==N)` 与字段实际布局是否相符，仍要靠跑 `tools/layout_from_schema.py` 的 ctypes 断言才会炸（实验者的 `ColTri` 52≠40 就是这类）。我只能把"结构通过 ≠ 语义正确"讲清楚（`does_not` + 骨架 `__scaffold_status__` 警告），**没有**在 validate 里内建 ctypes ABI 复算 | 已实测（缺陷仍在） |
| **新宿主枚举取值集合仍要人给**（🔴 半修） | ⚠ 半修 | `schema.template.yaml` 给了**最小示例集**与契约，但每款宿主的真实枚举成员/取值无法离线推断，必须实测 | 推断 |
| `container.fixed` 与 `regions_template` 的分工、`magic/version/mapping_name` 约定 | ⚠ 半修 | `pt_schema_describe` 给了文字契约与示例值，但没有强制规则（工具不会替你选 magic） | 已实测（说明）/ 推断（约定） |
| 参数真值的二次验证 | ❌ 不做 | 库中无实机验证数值（`verified_on_hardware` 一律 false） | 据项目自述 |
| 自动安装 `mcp` SDK / 任何联网装依赖 | ❌ 不做 | 尊重零依赖与离线约束 | 已决策 |
| 修改 `v0-*` / `v1-*` | ❌ 不做 | 硬约束只读；所有写落在 `v2-mcp/` 或 `out_dir` | 已实测 |

### 仍然**没有修**的（诚实的待办）

- **`pt_schema_validate` 不会替你做 ABI/语义复算**：它明说"不校验语义"。这是**设计取舍**（保持它与
  `layout_from_schema.py` 的分工），但也意味着：一条 `size: '0x40'` 写错、字段又恰好凑不出 0x40 的 schema，
  能过结构校验、却会在脚手架跑起来时才炸。**这是本次唯一"只修一半"的核心缺口**。
- **Teardown 的真实词表仍是空白**：脚手架只给了骨架 + `TODO-MEASURE.md`；我**没有**也不应臆造它的数值。

---

## 6. 文件清单

- `REPORT.md` — 本文件
- `mcp.json.example` — MCP 客户端接入示例（未改）
- `server.py` — MCP server（**本次大改**：5 工具、结构化错误、header_path、新 scaffold）
- `smoke.py` — 冒烟调用客户端（**本次扩展**：ids 13–19）
- `smoke_log.jsonl` — 冒烟原始 request/response（本报告唯一数据源，19 条）
- `.work/` — 运行时隔离副本、scaffold 演示输出、`_evidence/` 原始运行输出（可删）

