"""ptgen CLI — schema -> multi-language passthrough protocol."""
import argparse
import os
import sys

from . import schema_io
from .backends import cpp, csharp, java, rust, python

BACKENDS = {
    "cpp": (cpp, "h"),
    "csharp": (csharp, "cs"),
    "java": (java, "java"),
    "rust": (rust, "rs"),
    "python": (python, "py"),
}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ptgen", description="Generate passthrough protocol bindings from schema.yaml.")
    ap.add_argument("--schema", required=True)
    ap.add_argument("--lang", required=True, choices=list(BACKENDS))
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--host", help="vocabulary key inside schema.yaml (e.g. SKY, FO4); "
                                   "defaults to the first vocabulary in the schema")
    ap.add_argument("--vocab", help="standalone vocabulary YAML file")
    args = ap.parse_args(argv)

    schema = schema_io.load(args.schema)
    if not args.host and not args.vocab and schema.get("vocabularies"):
        args.host = next(iter(schema["vocabularies"]))
    vocab = schema_io.get_vocab(schema, host=args.host, vocab_file=args.vocab)
    backend, ext = BACKENDS[args.lang]
    main_text, sync_text = backend.generate(schema, vocab)

    host = args.host or (args.vocab and os.path.splitext(os.path.basename(args.vocab))[0]) or "HOST"
    os.makedirs(args.out, exist_ok=True)
    base = os.path.join(args.out, f"{host}.proto.{ext}")
    with open(base, "w", encoding="utf-8") as f:
        f.write(main_text)
    written = [base]
    if sync_text:
        sbase = os.path.join(args.out, f"{host}.sync.{ext}")
        with open(sbase, "w", encoding="utf-8") as f:
            f.write(sync_text)
        written.append(sbase)
    print(f"[{args.lang}] wrote {len(main_text.splitlines())} lines -> {base}" +
          (f" (+sync {len(sync_text.splitlines())} lines)" if sync_text else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
