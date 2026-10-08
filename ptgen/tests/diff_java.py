"""diff_java.py — structural + semantic diff of generated Java vs SkyCraft's Proto.java (MIT).

Two reports:
  * structural: normalized line diff (comments/whitespace stripped, identifiers+literals kept).
  * semantic:   every numeric offset/size/enum value in Proto.java must also appear in the
                generated Java (value-equivalence, independent of naming convention).
Neither is a pass/fail gate on T1; it documents the contract the Java generator honours.
"""
import re
import sys
import os
import argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
PROTOC_JAVA = os.path.join(_HERE, "..", "..", "..", "90-源码", "SkyCraft", "fabric",
                            "src", "main", "java", "dev", "skycraft", "link", "Proto.java")
GENERATED = os.path.join(_HERE, "..", "..", "v0-schema", "generated", "SKY.proto.java")


def normalize(text):
    out = []
    for ln in text.splitlines():
        s = re.sub(r"\s+", " ", ln).strip()
        s = re.sub(r"//.*", "", s).strip()
        if s:
            out.append(s)
    return out


def num_consts(text):
    d = {}
    for m in re.finditer(r"(\w+)\s*=\s*(0x[0-9A-Fa-f]+|\d+)(?:L?|(?:\.\d+)?);", text):
        name = m.group(1)
        val = m.group(2)
        v = int(val, 16) if val.lower().startswith("0x") else float(val) if "." in val else int(val)
        d[name] = v
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=PROTOC_JAVA)
    ap.add_argument("--gen", default=GENERATED)
    args = ap.parse_args()

    with open(args.ref, encoding="utf-8") as f:
        ref = f.read()
    with open(args.gen, encoding="utf-8") as f:
        gen = f.read()

    a = normalize(ref)
    b = normalize(gen)
    n = min(len(a), len(b))
    mism = sum(1 for i in range(n) if a[i] != b[i])
    extra = abs(len(a) - len(b))
    structural = mism + extra

    ref_c = num_consts(ref)
    gen_c = num_consts(gen)
    ref_vals = set(ref_c.values())
    gen_vals = set(gen_c.values())
    matched_vals = ref_vals & gen_vals
    missing = ref_vals - gen_vals
    missing_names = [nm for nm, v in ref_c.items() if v in missing]
    # `*_COUNT` are auto-increment terminators (schema `value: null`): the generator
    # deliberately does not emit them because they are not part of the wire ABI.
    sentinels = sorted(nm for nm in missing_names if nm.endswith(("_COUNT", "_COUNT_")) or nm.endswith("COUNT"))
    hard = sorted(nm for nm in missing_names if nm not in sentinels)

    print("=== Java structural diff vs Proto.java ===")
    print(f"  ref lines={len(a)} gen lines={len(b)}  differing/extra lines = {structural}")
    print("  (dominated by naming convention: Proto.java uses H_/SS_/AT_/ER_...; the")
    print("   generator uses <STRUCT>_<FIELD>/<STRUCT>_BYTES; both carry the same values)")
    print("=== Java semantic equivalence (numeric values) ===")
    print(f"  Proto.java numeric constants: {len(ref_c)}")
    print(f"  distinct values in Proto.java: {len(ref_vals)}")
    print(f"  values reproduced in generated Java: {len(matched_vals)}/{len(ref_vals)}")
    if sentinels:
        print(f"  expected auto-sentinels not emitted (non-ABI): {sentinels}")
    if hard:
        print("  UNEXPECTED values missing from generated Java:")
        for nm in hard:
            print(f"    {nm} = {ref_c[nm]!r}")
    else:
        print("  ALL numeric offset/size/enum values in Proto.java are present in generated Java.")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
