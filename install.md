# Install

Requires **Python 3.9+** and pip. **PyYAML is the only hard dependency.**
The MCP layer is hand-written JSON-RPC over stdio with zero extra deps — on purpose.

```bash
# 1. Install the code generator (adds the `ptgen` console script)
python -m pip install ./ptgen

# 2. Prove the install — round-trip the real MIT protocol headers
#    (expect: SKY diff=0, FO4 diff=0, VAL SKIPPED by design)
python schema/verify_roundtrip.py

# 3. Watch the bridge guards work — three scenarios, no game, no engine, no GPU
python stubs/run_demo.py
```

Optional — drive the toolkit from an agent instead of a shell:

```bash
python mcp/server.py     # MCP server, JSON-RPC over stdio; config example: mcp/mcp.json.example
```

## Packaging notes (why one package, not three)

- **One pip package: `ptgen`.** The generator is the only component with a dependency
  (PyYAML) and the only thing you *install*. Single `console_scripts` entry: `ptgen`.
- **`stubs/`, `params/`, `mcp/`, `schema/` are repo scripts, not packages.** You run them
  from the repo root (`python stubs/run_demo.py`). Packaging them would drag the fake
  stubs and the MCP server into every install's dependency graph for zero benefit —
  they have no third-party deps and no library consumers.
- If you only want the MCP tools, you still don't install anything: `mcp/server.py`
  is stdlib-only Python.
