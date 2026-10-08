# T6-output —— Teardown ← Minecraft 的 passthrough 开发骨架

本目录是 T6 上手实验的产物。**骨架，不是可用成品。**

## 目录结构（我理解的"这类项目该有的形状"）

```
T6-output/
├── README.md                  # pt_scaffold 生成：五件东西覆盖表
├── TODO-MEASURE.md            # pt_scaffold 生成 + 【T6 增补】Teardown 宿主侧 8 条
├── schema.teardown.yaml       # 【T6 写】自写 schema/词表（structure.ok=true）
├── schema.teardown.guess1.yaml# 【T6 写】第一次的错版，留作证据（校验时崩溃）
├── schema.v1..v6.yaml         # 【T6 写】二分定位用的变体
├── protocol/                  # pt_scaffold 生成：SKY 词表的多语言协议头（默认模板）
│   ├── SKY.proto.h
│   ├── SKY.proto.py
│   └── SKY.sync.h
├── tools/                     # pt_scaffold 生成：假桩 harness（不启动游戏）
│   ├── layout_from_schema.py  #   schema -> ctypes 布局（单一真相源）
│   ├── fake_host.py / fake_guest.py
│   ├── run_demo.py            #   三个场景 a/b/c
│   ├── negative_control.py / render_demo.py
│   └── generated/SKY_layout.py
├── t6_driver.py               # 【T6 写】复用 smoke.py 协议的 JSON-RPC stdio 驱动
├── requests*.json             # 【T6 写】逐轮请求序列
└── t6_log*.jsonl              # 【T6 写】逐轮 request/response 原始记录
```

## 已知的"形状缺口"（工具没给，我自己补的）

| 应有组件 | 工具是否产出 | 说明 |
|---|---|---|
| 协议 schema/词表 | 部分 | 工具只**校验** schema，不给模板；Teardown 词表由我从产物反推手写 |
| 协议头（cpp/python） | 是 | 但基于默认 `SKY` 词表，非 Teardown |
| 假桩 harness | 是 | 硬编码 `SKY`，**跑不了新宿主**（见报告缺口#3） |
| 宿主侧插件/natives | 否 | 工具明确拒绝（`does_not`） |
| 画面合成器 | 否 | 工具明确拒绝（`does_not`） |
| 启动器 | 占位 | `tools/` 即入口 |

## 可验证运行

- 工具级：`pt_stub_run(scenario=all)` → `PASS`（协议/状态机；与宿主无关）。
- 骨架级：`PT_SCHEMA=$PWD/schema.teardown.yaml python tools/run_demo.py` → **失败**
  （`unknown host 'SKY'`），原因见报告。
