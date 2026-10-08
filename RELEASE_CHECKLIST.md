# Release checklist — run BEFORE you tag / publish

Every item is a command you can actually run. Replace `.` with your repo root.
All commands expect to be run from the repository root and assume `grep` (ripgrep / `grep -rn` both fine).

> Hard red lines are numbered **R1–R6**. Each one carries its reason inline below.
>
> **Known-good hits (v4-launch audit, 2026-10-08):** the R3 grep also prints lines in
> `mcp/server.py`, `schema/verify_roundtrip.py` and `ptgen/src/ptgen/backends/rust.py`
> that *mention* ValCraft/EldenKill to explain they are not redistributed — references,
> not copied code; R3b prints `minecraft-crossover-bridge` (an unrelated repo named in
> `params/`) and analysis prose in `schema/REPORT.md`. The R5 grep prints negative
> statements ("无实机验证" / "实机验证: False") — the rule targets *false claims*, and
> there are none. All of these are expected.

---

## R3 — No code from no-license repos (ValCraft / EldenKill / chasm-bridge-fnv)

These three ship **no LICENSE** ("all rights reserved"). **Zero lines** may enter this repo.

```bash
# Expect: NO output (empty). If anything prints, delete it before release.
grep -rniE 'valcraft|eldens?kill|chasm-bridge-fnv|chasmlol/chasm-bridge' \
  --include='*.h' --include='*.cpp' --include='*.cs' --include='*.java' \
  --include='*.rs' --include='*.py' --include='*.fx' . \
  | grep -viE 'README|RELEASE_CHECKLIST|read but not copied|no license|zero lines'
```

Also confirm no *derived* identifiers leaked (e.g. `valcraft::proto`, `kValXxx`, `host-eldenring`):

```bash
# Expect: NO output.
grep -rniE 'valcraft::|kVal[A-Z]|host-eldenring|guest-ultrakill|er-bridge' . \
  | grep -viE 'README|RELEASE_CHECKLIST|inferred|read but not copied'
```

---

## R5 / honesty — No false "verified on real hardware" claims

We have **zero** on-hardware verification. Any claim of playtest / real-rig success is a lie.

```bash
# Expect: NO output. Flag and fix any match (unless it is this checklist itself).
grep -rniE 'verified on (real|hardware)|tested on (a )?rig|playtested|works on (my )?machine|实机验证|已实机' . \
  | grep -viE 'RELEASE_CHECKLIST|zero on-hardware|has ZERO|no third-party playtest'
```

Sanity check that the honest disclaimer IS present:

```bash
# Expect: at least one match (the Honest limits section).
grep -rniE 'does NOT run your game|zero on-hardware verification|MUST BE MEASURED' README.md README.zh-CN.md
```

---

## R1 — No bundled game files

Do not ship Minecraft instances, or GTA / Skyrim / Valheim assets.

```bash
# Expect: NO output. Block extensions / dirs that signal game payloads.
grep -rniE '\.(mca|schem|dat|dll|exe|bsa|esm|esp|vpk|pak)$' . \
  | grep -viE 'LICENSE|README|example|stub|fake'   # tighten as needed
find . -type d \( -iname '*.minecraft' -o -iname 'minecraft' -o -iname 'assets' \) -not -path '*/node_modules/*'
```

---

## R2 — No bundled loader binaries (SKSE / ScriptHookV / ReShade)

Upstream explicitly forbids redistribution. Ship links + version checks only.

```bash
# Expect: NO output. These filenames must never be committed.
find . -type f \( -iname 'skse*.dll' -o -iname 'skse*.exe' -o -iname 'ScriptHookV*' \
  -o -iname 'ReShade*.dll' -o -iname 'ReShade*.asi' -o -iname 'dinput8*.dll' \) 
# If the above prints anything, remove it.
```

Confirm we only *point* to loaders, not embed them:

```bash
# Acceptable: lines that say "download from" / "link to" / version pin.
grep -rniE 'skse|scripthookv|reshade' README.md | grep -iE 'download|link|version|official'
```

---

## Compliance — Third-party notices match LICENSE

Every MIT source we build on must keep its copyright notice; every no-license source must stay absent.

```bash
# 1) SkyCraft + universal-modder copyright retained in LICENSE / README.
grep -rniE 'chasmlol/SkyCraft|rehan-remade/universal-modder' LICENSE README.md README.zh-CN.md
# 2) The three no-license repos are listed under "Read but not copied", not as sources.
grep -rniE 'Read but not copied|read but not copied' README.md README.zh-CN.md
```

---

## Evidence tiers — every claim is tagged

Numeric claims must carry `measured` / `reported` / `inferred` (or 实测 / 据项目自述 / 推断).

```bash
# Spot-check: the headline schema claim is tagged "measured".
grep -rniE 'structural diff = 0|diff 全为 0|结构性 diff' README.md | grep -iE 'measured|实测'
# Spot-check: the 85.3% / 99.4% protocol-header claims cite their source doc.
grep -rniE '85\.3%|99\.4%' README.md README.zh-CN.md
```

---

## Final gate

```bash
# Nothing in the repo should mention a fake/placeholder author name left in.
grep -rn '<YOUR NAME>' .   # -> only in LICENSE; replace before tagging.
```

- [ ] All grep commands above return their expected (empty or present) result.
- [ ] `LICENSE` `<YOUR NAME>` replaced with the real author.
- [x] Demo block filled from **real** `demo.txt` output (the `<!-- DEMO:PENDING -->` marker is gone from both READMEs).
- [ ] No game files, no loader binaries, no no-license code.
- [ ] MIT copyright notices present; "Read but not copied" list accurate.
