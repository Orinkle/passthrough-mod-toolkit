# passthrough 适配器骨架 — Teardown ← Minecraft: Java Edition

由 `pt_scaffold`（PTmodmaker）生成。**这是骨架，不是可用成品。**

## 五件东西（桥）中，本骨架覆盖了哪些

| # | 组件 | 本骨架状态 |
|---|------|-----------|
| ① | 客侧 mod（guest） | 🧱 占位：`protocol/` 里有生成好的协议头，逻辑需你写 |
| ② | 宿主侧插件（host） | ❌ **未生成**——见 `TODO-MEASURE.md` 的「明确不做」 |
| ③ | 传输层（约定） | ✅ 来自 schema：共享内存映射（`Local\\...` 命名），协议头即约定 |
| ④ | 画面合成器 | ❌ 未生成（依赖真机渲染路径） |
| ⑤ | 启动器 | 🧱 占位：`tools/` 是可跑的假桩自测harness |

## 生成物

- `protocol/` — `ptgen` 依据 `v0-schema/schema.yaml` 的 vocab `SKY` 生成的多语言协议头。
  若宿主未在 schema 中注册，这里是**默认模板**，请自行补 vocabulary。
- `tools/` — 假桩 harness（`fake_host.py` / `fake_guest.py` / `run_demo.py`）。**不启动真游戏**。
- `TODO-MEASURE.md` — 必须先实测的 🔴 参数清单（含出处）。
- `README.md` — 本文件。

## 跑自测（不启动游戏）

```bash
PT_SCHEMA=/abs/path/to/v0-schema/schema.yaml \
python tools/run_demo.py
```

## 覆盖面说明

- vocab 解析: `SKY`（default-template）
- 生成后端: cpp, python
- 安全: 本脚手架拒绝一切联机/多人/反作弊/服务端地址输入。
