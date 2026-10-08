#!/usr/bin/env python3
"""verify_roundtrip.py — extract -> generate -> structural diff for each real header.

Normalization (per the brief): comments and whitespace are ignored; identifiers, literals
and declaration order are preserved.
  - SKY (SkyCraft, MIT)  and FO4 (FalloutCraft, MIT): target ZERO structural difference.
  - VAL (ValCraft, no LICENSE): expressiveness only. The regenerated header is NOT committed
    and NOT used as a pass/fail byte comparison; we only confirm it generates and report the
    structural delta as information about schema coverage.
"""
import sys
import os
import re
import difflib
import argparse
import yaml
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable  # the venv python this script runs under

HOSTS = [
    ("SKY", "SkyCraft/protocol/skycraft_protocol.h",  "MIT",    "gen"),
    ("FO4", "FalloutCraft/skycraft_protocol.h",        "MIT",    "gen"),
    ("VAL", "ValCraft/protocol/valcraft_protocol.h",  "none",   "tmp"),
]

# Where the reference protocol headers live. The first candidate that holds every
# MIT header we need wins, so this works both in the development tree and in an
# assembled checkout. Override with PT_HEADERS_DIR.
HEADER_ROOTS = [
    os.environ.get("PT_HEADERS_DIR"),
    os.path.join(HERE, "..", "headers"),              # <repo>/schema/../headers
    os.path.join(HERE, "..", "examples", "headers"),  # <repo>/examples/headers
    os.path.join(HERE, "..", "..", "90-源码"),        # development tree
]


def header_root():
    for cand in HEADER_ROOTS:
        if not cand:
            continue
        root = os.path.abspath(cand)
        if all(os.path.exists(os.path.join(root, rel))
               for _, rel, lic, _ in HOSTS if lic == "MIT"):
            return root
    tried = "\n  ".join(os.path.abspath(c) for c in HEADER_ROOTS if c)
    print("FATAL: cannot find the reference protocol headers. Looked in:\n  " + tried +
          "\nSet PT_HEADERS_DIR to the directory that contains "
          "'SkyCraft/protocol/skycraft_protocol.h'.", file=sys.stderr)
    sys.exit(2)


def strip_comment(line):
    i = line.find("//")
    return line[:i] if i >= 0 else line


def normalize(text):
    out = []
    for ln in text.splitlines():
        s = re.sub(r"\s+", " ", strip_comment(ln)).strip()
        if s:
            out.append(s)
    return out


def structural_diff(a_lines, b_lines):
    # positional mismatch over the common prefix + trailing extras
    n = min(len(a_lines), len(b_lines))
    mism = sum(1 for i in range(n) if a_lines[i] != b_lines[i])
    extra = abs(len(a_lines) - len(b_lines))
    return mism + extra


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default=os.path.join(HERE, "schema.yaml"))
    ap.add_argument("--keep-gen", default=os.path.join(HERE, "generated"))
    args = ap.parse_args()

    schema = args.schema
    results = {}
    root = header_root()
    temp_files = []
    skipped = []
    for key, rel, lic, dest in HOSTS:
        hdr = os.path.join(root, rel)
        if not os.path.exists(hdr):
            if lic == "MIT":
                print(f"FATAL: MIT reference header missing: {hdr}", file=sys.stderr)
                sys.exit(2)
            skipped.append(key)
            print(f"{key} ({lic:4}): SKIPPED — reference header not redistributed "
                  f"(that repo carries no LICENSE); checked {rel}")
            continue
        vpath = os.path.join(HERE, f"._v_{key.lower()}.yaml")
        if dest == "gen":
            os.makedirs(args.keep_gen, exist_ok=True)
            gpath = os.path.join(args.keep_gen, f"{key}.h")
        else:
            gpath = os.path.join(HERE, f"._gen_{key}.h")
        temp_files += [vpath, gpath]
        run([PY, os.path.join(HERE, "extract_vocab.py"), "--header", hdr, "--out", vpath])
        run([PY, os.path.join(HERE, "gen_header.py"), "--schema", schema,
             "--vocab", vpath, "--out", gpath])

        with open(hdr, encoding="utf-8") as f:
            orig = f.read()
        with open(gpath, encoding="utf-8") as f:
            gen = f.read()
        d = structural_diff(normalize(orig), normalize(gen))
        results[key] = (lic, d, gpath)
        print(f"{key} ({lic:4}): structural diff = {d}  [{os.path.basename(gpath)}]")

    print()
    print("Conclusion check:")
    print(f"  SKY diff = {results['SKY'][1]} (target 0)")
    print(f"  FO4 diff = {results['FO4'][1]} (target 0)")
    if "VAL" in results:
        print(f"  VAL diff = {results['VAL'][1]} (expressiveness only; not a pass/fail target)")
    elif skipped:
        print("  VAL: skipped — its reference header is not redistributed "
              "(no LICENSE on that repo). Copy it in yourself and set PT_HEADERS_DIR.")
    # non-zero exit if a MIT host is not zero (so CI can gate)
    if results["SKY"][1] != 0 or results["FO4"][1] != 0:
        print("FAIL: a MIT host did not round-trip to zero", file=sys.stderr)
        sys.exit(1)
    print("PASS: both MIT hosts round-trip to zero structural difference.")

    # clean up scratch files (VAL generated header must not enter the repo)
    for tf in temp_files:
        try:
            os.remove(tf)
        except OSError:
            pass


if __name__ == "__main__":
    main()
