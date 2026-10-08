# ptgen — passthrough-mod protocol generator

`ptgen` turns one `schema.yaml` (the double-layer schema from T1: a fixed `container`
plus a per-host `vocabulary`) into protocol bindings for **C++, C#, Java, Rust and
Python**. It is the first *installable* package that does schema → five languages for the
passthrough-mod shared-memory protocol — the eight ecosystem repos all hand-port the same
protocol and ship no package.

The generic part (region offsets, ring layouts, struct layouts, seqlock/SPSC) lives in
the `container`; the host-specific words (namespace, magic, version, enums, field lists)
live in the `vocabulary`. Change the vocabulary, get a new host for free.

## Install

```bash
pip install -e .        # from this directory
# or, once published on PyPI:
pip install ptgen
```

Only runtime dependency: `pyyaml`. The `ptgen` console script is declared in
`pyproject.toml` (`[project.scripts] ptgen = "ptgen.cli:main"`).

## Use

```bash
ptgen --schema schema.yaml --lang cpp    --out gen/
ptgen --schema schema.yaml --lang csharp --out gen/
ptgen --schema schema.yaml --lang java   --out gen/
ptgen --schema schema.yaml --lang rust   --out gen/
ptgen --schema schema.yaml --lang python --out gen/    # ctypes module for the test stubs
```

`--host SKY` selects a vocabulary inside the schema; without it the first vocabulary is
used. `--vocab file.yaml` takes a standalone vocabulary (e.g. one produced by
`extract_vocab.py` from a real header).

Each backend emits, for the chosen host:

- a package / namespace / module declaration;
- scalar constants (magic, version, mapping name, units-per-block) and every region and
  ring offset;
- enums (host flags, mc flags, input types, hurt flags, event types, render types,
  collision-tri flags, optional dig-material / tool-kind);
- **structs with memory-layout assertions / packing** — `Header`, `HostState`, `McState`
  and every container struct (`ActorTable`, `WorldEntities`, `RenVertex`,
  `ColRegion/ColBlock/ColTri`, …). C++ uses `static_assert`, Rust `#[repr(C)]` +
  `assert!(size_of…)` + `offset_of`, C# `LayoutKind.Sequential` + `Marshal.SizeOf` +
  `ByValArray`, Java emits the offset/size constant table, Python emits `ctypes.Structure`;
- a **seqlock** read/write skeleton and an **SPSC ring** produce/consume skeleton.

## The hard invariant

The container must be ABI-equivalent across all languages: identical field offsets,
identical struct sizes. This is enforced by a single language-neutral model
(`src/ptgen/model.py`), `ctypes`-verified against the C++ `static_assert` sizes in
`schema.yaml`. Every backend renders from that one model, so the generated C#/Java/Rust/
Python layouts carry the same offsets and sizes the C++ header does.

## Verification

Run everything with Python 3.9+ (PyYAML installed)


```bash
# 1. C++ still round-trips to zero structural diff against the MIT skycraft_protocol.h (T1 gate)
python ../schema/verify_roundtrip.py
# 2. cross-language offset/size table (compiles C++ with g++ and Rust with rustc for real;
#    imports the Python module; parses the Java/C# constant tables)
python tests/compare_layout.py
# 3. Java structural + semantic diff vs SkyCraft's Proto.java (MIT)
python tests/diff_java.py
# 4. C#/Rust size-assert consistency vs the ctypes model (no C# toolchain here)
python tests/verify_abi.py
```

`compare_layout.py` prints a per-language verdict against the **compiled C++ header**
(the ground truth) and exits non-zero on any mismatch.

## Status by language

| lang   | reference            | verification                                              |
|--------|----------------------|-----------------------------------------------------------|
| C++    | T1 `gen_header.py`   | byte-identical output; round-trip zero diff (regression)   |
| Java   | `Proto.java` (MIT)   | structural + semantic diff documented                      |
| C#     | ValCraft `Proto.cs`  | **no MIT reference → self-consistency only, unverified**   |
| Rust   | none (EldenKill)     | compiled with `rustc`; sizes/offsets vs C++                |
| Python | (feeds the stubs)    | imported; `ctypes.sizeof`/`offset` vs the compiled C++      |

See `REPORT.md` for the measured numbers and the honest confidence tiers
(`已实测 / 据项目自述 / 推断`).
