# examples/ — upstream product entry points

This directory is a **table of contents**, not a copy. The heavy artifacts live
upstream (in `../schema/` and `../params/`); we point at them so the repo
stays small and the source of truth stays single.

> Paths below are relative to this file (`examples/`), i.e. `../` = `v3-repo-draft/`.

## 1. Schema round-trip proof (the hardest selling point)

- **Read:** [`../schema/REPORT.md`](../schema/REPORT.md)
  — one `schema.yaml` round-tripped SkyCraft / FalloutCraft / ValCraft protocol
  headers with **structural diff = 0** (measured).
- **Artifacts (upstream, not copied here):**
  - `../schema/schema.yaml` — the two-layer schema (fixed `container` + per-host `vocabulary`).
  - `generated/SKY.proto.h`, `generated/FO4.proto.h` — zero-diff generated headers (MIT sources only; ValCraft vocabulary is **not** embedded, per the no-license rule).
  - `../schema/verify_roundtrip.py` — re-run the proof.

## 2. Parameter library (with provenance + evidence tiers)

- **Read:** [`../params/REPORT.md`](../params/REPORT.md)
  — 9 seeds + 35 params, three-color reuse grading (🟢 copy / 🟡 re-verify / 🔴 measure)
  and four-element records (`value` / `source` / `evidence` / `verified_on_hardware`).
- **Artifacts (upstream):**
  - `../params/params.yaml` — the library (all `verified_on_hardware = false`).
  - `../params/param_lookup.py` — `python param_lookup.py --host skyrim --color red`.

## 3. Schema snippet example (copy-paste starter)

The ~20-line vocabulary excerpt shown in the main `../README.md` Quickstart is the
canonical starter. For the full, runnable schema, open `../schema/schema.yaml`.

## Why pointer-only
Copying `params.yaml` / `schema.yaml` into this draft would fork the source of
truth and drift. We keep one copy upstream and link. (If you want them vendored at
release time, copy explicitly and bump the version noted in the upstream REPORTs.)
