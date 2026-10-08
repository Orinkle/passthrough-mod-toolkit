#!/usr/bin/env python3
"""extract_vocab.py — reverse extractor: real protocol header -> vocabulary dict.

Parses the *variable* parts of a passthrough header into the data contract defined by
schema.yaml's vocabulary_schema. The invariant container is NOT re-extracted (it lives in
schema.yaml). Only the host's "words" are pulled out, so a 4th host is onboarded by pointing
this at its header and feeding the result to gen_header.py.
"""
import sys
import re
import argparse
import yaml


def strip_comment(line):
    # remove // comments (no string literals contain // in these headers)
    idx = line.find("//")
    if idx >= 0:
        line = line[:idx]
    return line


def find_struct(lines, name):
    for i, ln in enumerate(lines):
        if re.search(rf"struct\s+{name}\b", ln):
            # collect until the matching };
            buf = []
            depth = 0
            for j in range(i, len(lines)):
                s = strip_comment(lines[j])
                depth += s.count("{") - s.count("}")
                if j > i and s.strip() == "};":
                    return buf
                if j > i:
                    buf.append(lines[j])
            return buf
    return []


def struct_fields(lines):
    fields = []
    for ln in lines:
        s = strip_comment(ln).strip()
        if s == "":
            continue
        if s.endswith(";"):
            fields.append(s)
    return fields


def find_enum_members(text, name):
    m = re.search(rf"enum\s+{name}\s*:\s*\S+\s*\{{(.*?)\}};", text, re.DOTALL)
    if not m:
        return None
    body = m.group(1)
    members = []
    for ln in body.splitlines():
        s = strip_comment(ln).strip()
        if not s:
            continue
        mm = re.match(r"(\w+)(?:\s*=\s*([^,]+?))?\s*,?\s*$", s)
        if mm:
            value = mm.group(2)
            members.append({"name": mm.group(1), "value": value.strip() if value else None})
    return members


def struct_size(text, name):
    m = re.search(rf"static_assert\(sizeof\({name}\)\s*==\s*(0x[0-9A-Fa-f]+)\)", text)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--header", required=True)
    ap.add_argument("--out", required=False)
    args = ap.parse_args()

    with open(args.header, encoding="utf-8") as f:
        raw = f.read()
    lines = raw.splitlines()
    text = raw

    ns = re.search(r"namespace\s+([\w:]+)", text).group(1)

    # host words from the heartbeat field: prefix (skyrim/valheim) and abbreviation (Sky/Val).
    # The regex already captures just the prefix before "HeartbeatMs".
    hb = re.search(r"std::uint64_t\s+(\w+)HeartbeatMs", text).group(1)
    prefix = hb                                 # skyrim / valheim
    if prefix.endswith("heim"):
        abbr = prefix[:-4].capitalize()          # valheim -> val -> Val
    else:
        abbr = prefix[:-3].capitalize()          # skyrim -> sky -> Sky

    magic = re.search(r"kMagic\s*=\s*(0x[0-9A-Fa-f]+)", text).group(1)
    version = int(re.search(r"kVersion\s*=\s*(\d+)", text).group(1))
    mapping = re.search(r'kMappingName\[\]\s*=\s*L"([^"]*)"', text).group(1)
    units = re.search(r"kUnitsPerBlock\s*=\s*([\d.]+)", text).group(1)

    host_flags = find_enum_members(text, f"{abbr}Flags")
    host_state_name = f"{abbr}State"
    hs_lines = find_struct(lines, host_state_name)
    hs_fields = struct_fields(hs_lines)
    hs_size = struct_size(text, host_state_name)
    gg = re.search(r"kGroundGrid\s*=\s*(\d+)", text)
    ground_grid = int(gg.group(1)) if gg else None

    mc_flags = find_enum_members(text, "McFlags")
    ms_lines = find_struct(lines, "McState")
    ms_fields = struct_fields(ms_lines)
    ms_size = struct_size(text, "McState")

    input_type = find_enum_members(text, "InputType")
    hurt_flags = find_enum_members(text, "HurtFlags")
    mc_event_type = find_enum_members(text, "McEventType")
    ren_type = find_enum_members(text, "RenType")
    col_tri_flags = find_enum_members(text, "ColTriFlags")
    has_shift = "kTriMaterialShift" in text
    dig_material = find_enum_members(text, "DigMaterial")
    ren_dug = bool(re.search(r"\bstruct\s+RenDug\b", text))
    tool_kind = find_enum_members(text, "ToolKind")

    vocab = {
        "namespace": ns,
        "host_abbr": abbr,
        "host_prefix": prefix,
        "magic": magic,
        "version": version,
        "mapping_name": mapping,
        "units_per_block": units,
        "host_flags": host_flags,
        "host_state": {"fields": hs_fields, "size": hs_size, "ground_grid": ground_grid},
        "mc_flags": mc_flags,
        "mc_state": {"fields": ms_fields, "size": ms_size},
        "input_type": input_type,
        "hurt_flags": hurt_flags,
        "mc_event_type": mc_event_type,
        "ren_type": ren_type,
        "col_tri_flags": {"members": col_tri_flags, "has_shift": has_shift},
        "dig_material": dig_material,
        "ren_dug": ren_dug,
        "tool_kind": tool_kind,
    }

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            yaml.safe_dump(vocab, f, sort_keys=False, width=100, allow_unicode=True)
        print(f"wrote {args.out}")
    else:
        print(yaml.safe_dump(vocab, sort_keys=False, width=100, allow_unicode=True))


if __name__ == "__main__":
    main()
