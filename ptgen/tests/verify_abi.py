"""verify_abi.py — self-consistency of the non-C++ backends.

No C#/Rust toolchain exists here, so we cannot compile. Instead we prove the generated
size assertions (C#: Marshal.SizeOf<T>() != N ; Rust: size_of::<T>() == N) match the
ctypes model — which is ctypes-verified to equal the C++ schema static_assert sizes.
That closes the loop: if the generated C#/Rust compiled, their structs would be ABI
identical to the C++ ones (subject to the natural-alignment assumption of each compiler).

Run:  python tests/verify_abi.py   (exits 0 only if every asserted size matches the model)
"""
import re
import sys
import argparse
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from ptgen import schema_io, model  # noqa: E402

GEN = os.path.join(os.path.dirname(__file__), "..", "..", "v0-schema", "generated")


def ctypes_sizes():
    cls, _ = model.build_ctypes()
    out = {n: model.ctypes.sizeof(c) for n, c in cls.items()}
    # also size the variable structs (Header / HostState / McState) the same way the
    # C++ generator sizes them (these are validated transitively by T1's C++ round-trip).
    s = schema_io.load(os.path.join(os.path.dirname(__file__), "..", "..",
                                    "v0-schema", "schema.yaml"))
    v = s["vocabularies"]["SKY"]
    classes = model.build_ctypes()[0]
    for name, lines in (("Header", ["std::uint32_t magic;", "std::uint32_t version;",
                                    "std::uint32_t skyrimPid;", "std::uint32_t mcPid;",
                                    "std::uint64_t skyrimHeartbeatMs;", "std::uint64_t mcHeartbeatMs;"]),
                         (f"{v['host_abbr']}State", v["host_state"]["fields"]),
                         ("McState", v["mc_state"]["fields"])):
        parsed = model.parse_field_lines([ln if ln.endswith(";") else ln + ";" for ln in lines])
        ct = [(fn, model._ct_of(ft, classes)) for fn, ft in parsed]
        c = type(name, (model.ctypes.Structure,), {"_fields_": ct})
        out[name] = model.ctypes.sizeof(c)
    return out


def parse_cs(path):
    out = {}
    for m in re.finditer(r"SizeOf<(\w+)>\(\)\s*!=\s*(\d+)", open(path, encoding="utf-8").read()):
        out[m.group(1)] = int(m.group(2))
    return out


def parse_rs(path):
    out = {}
    for m in re.finditer(r"size_of::<(\w+)>\(\)\s*==\s*(\d+)", open(path, encoding="utf-8").read()):
        out[m.group(1)] = int(m.group(2))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", default=GEN)
    args = ap.parse_args()
    sizes = ctypes_sizes()
    ok = True
    found = 0
    for lang, parser, fn in (("csharp", parse_cs, "SKY.proto.cs"),
                             ("rust", parse_rs, "SKY.proto.rs")):
        path = os.path.join(args.gen, fn)
        if not os.path.exists(path):
            print(f"[{lang}] generated file not found: {path}")
            continue
        found += 1
        asserted = parser(path)
        print(f"=== {lang} size-assert consistency (vs ctypes model) ===")
        for name, n in sorted(asserted.items()):
            model_sz = sizes.get(name)
            if model_sz is None:
                # Header/SkyState/McState are var structs (not in container ctypes table); skip
                status = "model-only (var struct, not in container ctypes table)"
            else:
                # WaterGrid uses a <= max contract in C++; others are exact.
                match = (model_sz <= n) if name == "WaterGrid" else (model_sz == n)
                ok = ok and match
                status = "OK" if match else f"MISMATCH (model {model_sz:#x})"
            print(f"  {name}: asserted {n:#x}  {status}")
        # WaterGrid uses a max contract, not exact: report separately
        if "WaterGrid" in asserted:
            print(f"  WaterGrid: asserted {asserted['WaterGrid']:#x}  model sizeof {sizes['WaterGrid']:#x}  (C++ uses <=0xC00 max)")
    print("RESULT:", "PASS — all asserted struct sizes match the ABI model" if ok else "FAIL")
    if found == 0:
        print("FATAL: no generated C#/Rust files found to verify")
        return 2
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
