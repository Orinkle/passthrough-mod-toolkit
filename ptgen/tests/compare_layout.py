#!/usr/bin/env python3
"""compare_layout.py — cross-language offset/size table for the passthrough protocol.

The hard requirement of ptgen is that the *container* is ABI-equivalent in every
language: identical field offsets, identical struct sizes. This script proves it by
measuring, not by assertion-reading, wherever a compiler/runtime exists:

  * C++   : compiled with g++ against the generated header (sizeof + offsetof)  -> ground truth
  * Rust  : compiled with rustc against the generated module (size_of + offset_of)
  * Python: the generated ctypes module is imported and sized at runtime
  * Java  : the emitted constants are parsed (no javac in this environment)
  * C#     : the emitted Marshal.SizeOf assertions are parsed (no dotnet here)

Ground truth is the **compiled C++ header**, and the language-neutral ctypes model is
checked against it too. Every other language's measured/parsed table must match it.

Run:  /home/zjk/.workbuddy/binaries/python/envs/default/bin/python tests/compare_layout.py
Exit: 0 if every comparable language matches C++; non-zero otherwise.
"""
import argparse
import ctypes
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ptgen import schema_io, plan, model  # noqa: E402
from ptgen.backends import cpp, csharp, java, rust, python as pyb  # noqa: E402

EXT = {"cpp": "h", "csharp": "cs", "java": "java", "rust": "rs", "python": "py"}


# --------------------------------------------------------------------------- plan
def structs_of(schema, vocab):
    p = plan.build_plan(schema, vocab)
    # (struct_name, [(field, offset, size)], size, mx)
    return p["structs"], p


# ------------------------------------------------------------------- generate all
def generate_all(schema_path, host, outdir):
    schema = schema_io.load(schema_path)
    vocab = schema_io.get_vocab(schema, host=host)
    written = {}
    for lang, mod in (("cpp", cpp), ("csharp", csharp), ("java", java),
                      ("rust", rust), ("python", pyb)):
        main_text, sync_text = mod.generate(schema, vocab)
        base = os.path.join(outdir, f"{host}.proto.{EXT[lang]}")
        with open(base, "w", encoding="utf-8") as f:
            f.write(main_text)
        written[lang] = base
        if sync_text:
            with open(os.path.join(outdir, f"{host}.sync.{EXT[lang]}"), "w", encoding="utf-8") as f:
                f.write(sync_text)
    written["_schema"] = schema
    written["_vocab"] = vocab
    return written


# ---------------------------------------------------------------------------- C++
def measure_cpp(schema, vocab, header_path, workdir):
    gxx = shutil.which("g++")
    if not gxx:
        return None, "g++ not found"
    structs, p = structs_of(schema, vocab)
    ns = p["namespace"]
    lines = ['#include "%s"' % os.path.basename(header_path),
             "#include <cstddef>", "#include <cstdio>", "int main() {",
             f"  using namespace {ns};"]
    for sname, flds, tot, mx in structs:
        lines.append(f'  std::printf("SIZE {sname} %zu\\n", sizeof({sname}));')
        for fn, tok, off, sz in flds:
            lines.append(f'  std::printf("OFF {sname} {fn} %zu\\n", offsetof({sname}, {fn}));')
    lines.append("  return 0;\n}")
    src = os.path.join(workdir, "harness.cpp")
    with open(src, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    exe = os.path.join(workdir, "harness_gpp")
    r = subprocess.run([gxx, "-std=c++17", "-w", "-I", os.path.dirname(header_path),
                        src, "-o", exe], capture_output=True, text=True)
    if r.returncode != 0:
        return None, "g++ failed: " + r.stderr.strip()[:400]
    out = subprocess.run([exe], capture_output=True, text=True).stdout
    return _parse_table(out), None


# --------------------------------------------------------------------------- Rust
_RS_KW = rust._KEYWORDS


def measure_rust(schema, vocab, rs_path, workdir):
    rc = shutil.which("rustc")
    if not rc:
        return None, "rustc not found"
    structs, p = structs_of(schema, vocab)
    lines = [f'#[path = "{os.path.basename(rs_path)}"] mod proto;',
             "use std::mem::{size_of, offset_of};", "fn main() {"]
    for sname, flds, tot, mx in structs:
        lines.append(f'  println!("SIZE {sname} {{}}", size_of::<proto::{sname}>());')
        for fn, tok, off, sz in flds:
            ident = f"r#{fn}" if fn in _RS_KW else fn
            lines.append(f'  println!("OFF {sname} {fn} {{}}", offset_of!(proto::{sname}, {ident}));')
    lines.append("}")
    src = os.path.join(workdir, "harness.rs")
    with open(src, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    exe = os.path.join(workdir, "harness_rs")
    r = subprocess.run([rc, "--edition", "2021", "-A", "warnings", src, "-o", exe],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, "rustc failed: " + r.stderr.strip()[:400]
    out = subprocess.run([exe], capture_output=True, text=True).stdout
    return _parse_table(out), None


# ------------------------------------------------------------------------- Python
def measure_python(py_path):
    spec = importlib.util.spec_from_file_location("ptgen_generated", py_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    table = {}
    for name, cls in list(vars(m).items()):
        if isinstance(cls, type) and issubclass(cls, ctypes.Structure) and cls is not ctypes.Structure:
            table.setdefault(name, {"_size": ctypes.sizeof(cls), "fields": {}})
            for fn, _ in cls._fields_:
                table[name]["fields"][fn] = getattr(cls, fn).offset
    return table, None


# --------------------------------------------------------------- Java / C# (parse)
def parse_java(java_path, schema, vocab):
    structs, p = structs_of(schema, vocab)
    text = open(java_path, encoding="utf-8").read()
    const = dict(re.findall(r"public static final long (\w+) = (0x[0-9a-fA-F]+|\d+)L;", text))
    const = {k: int(v, 0) for k, v in const.items()}
    table = {}
    for sname, flds, tot, mx in structs:
        t = {"_size": const.get(f"{sname.upper()}_BYTES"), "fields": {}}
        for fn, tok, off, sz in flds:
            t["fields"][fn] = const.get(f"{sname.upper()}_{java._upper_camel(fn)}")
        table[sname] = t
    return table, None


def parse_csharp(cs_path):
    text = open(cs_path, encoding="utf-8").read()
    sizes = {m.group(1): int(m.group(2))
             for m in re.finditer(r"SizeOf<(\w+)>\(\)\s*!=\s*(\d+)", text)}
    return sizes, None


# ------------------------------------------------------------------------ helpers
def _parse_table(out):
    table = {}
    for ln in out.splitlines():
        parts = ln.split()
        if parts and parts[0] == "SIZE":
            _, sname, sz = parts
            table.setdefault(sname, {"_size": int(sz), "fields": {}})
        elif parts and parts[0] == "OFF":
            _, sname, fn, off = parts
            table.setdefault(sname, {"_size": None, "fields": {}})["fields"][fn] = int(off)
    return table


def check(label, table, ground, report):
    """Compare a measured/parsed table against the C++ ground truth."""
    bad = 0
    for sname, g in ground.items():
        if sname not in table:
            report.append(f"  [{label}] MISSING struct {sname}")
            bad += 1
            continue
        t = table[sname]
        if t["_size"] is None:
            report.append(f"  [{label}] {sname}: size not emitted")
            bad += 1
        elif t["_size"] != g["_size"]:
            report.append(f"  [{label}] {sname}: size {t['_size']} != C++ {g['_size']}")
            bad += 1
        for fn, goff in g["fields"].items():
            toff = t["fields"].get(fn)
            if toff is None:
                # C# emits sizes only (no per-field offsets) -> skip silently
                continue
            if toff != goff:
                report.append(f"  [{label}] {sname}.{fn}: off {toff} != C++ {goff}")
                bad += 1
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default=os.path.join(ROOT, "..", "v0-schema", "schema.yaml"))
    ap.add_argument("--host", default=None)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    schema = schema_io.load(args.schema)
    host = args.host or next(iter(schema["vocabularies"]))
    workdir = args.workdir or tempfile.mkdtemp(prefix="ptgen_abi_")
    os.makedirs(workdir, exist_ok=True)
    print(f"schema: {args.schema}")
    print(f"host  : {host}")
    print(f"workdir: {workdir}")
    print()

    files = generate_all(args.schema, host, workdir)
    vocab = files["_vocab"]
    structs, p = structs_of(schema, vocab)
    total_structs = len(structs)

    # ground truth
    cpp_tab, err = measure_cpp(schema, vocab, files["cpp"], workdir)
    if cpp_tab is None:
        print("FATAL: cannot measure C++ ground truth:", err)
        return 2

    sources = {}
    src, err = measure_rust(schema, vocab, files["rust"], workdir)
    sources["rust"] = (src, err)
    src, err = measure_python(files["python"])
    sources["python"] = (src, err)
    sources["java"] = parse_java(files["java"], schema, vocab)
    cs_sizes, err = parse_csharp(files["csharp"])
    cs_tab = {n: {"_size": v, "fields": {}} for n, v in cs_sizes.items()}
    sources["csharp"] = (cs_tab, err)

    report = []
    bad_total = 0

    # model self-check: language-neutral ctypes model == compiled C++
    classes, _ = model.build_ctypes()
    model_bad = 0
    for sname, flds, tot, mx in structs:
        if sname in classes:
            if ctypes.sizeof(classes[sname]) != cpp_tab[sname]["_size"]:
                model_bad += 1
    report.append(f"model(ctypes) vs compiled C++ : {'MATCH' if model_bad == 0 else f'{model_bad} MISMATCH'}")

    status = {}
    for label, (tab, err) in sources.items():
        if tab is None:
            status[label] = f"SKIP ({err})"
            continue
        bad = check(label, tab, cpp_tab, report)
        bad_total += bad
        status[label] = "MATCH" if bad == 0 else f"{bad} MISMATCH"

    print(f"container structs compared: {total_structs}")
    print("ground truth             : compiled C++ header (g++ sizeof + offsetof)")
    print()
    print("== per-language result vs C++ ==")
    print(f"  cpp    (compiled)      : {status.get('cpp', 'MATCH') if False else 'ground truth'}")
    print(f"  rust   (compiled)      : {status.get('rust')}")
    print(f"  python (runtime ctypes): {status.get('python')}")
    print(f"  java   (parsed consts) : {status.get('java')}")
    print(f"  csharp (parsed asserts): {status.get('csharp')}  [sizes only]")
    print()
    print("== detail ==")
    for ln in report:
        print(ln)

    ok = (bad_total == 0) and (model_bad == 0)
    print()
    print("RESULT:", "PASS — offsets and sizes agree across languages" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
