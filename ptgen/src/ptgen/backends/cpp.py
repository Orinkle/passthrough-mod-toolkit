"""backends/cpp.py — schema -> C++ passthrough protocol header.

This is a faithful port of T1's gen_header.py so the generated C++ is byte-for-byte
what verify_roundtrip.py expects (zero structural diff against the MIT skycraft_protocol.h).
The container is emitted from schema.yaml's `fixed`/`regions_template` verbatim, exactly
as gen_header.py did; the variable words come from the vocabulary.
"""
import sys


def render_enum(name, underlying, members):
    out = [f"\tenum {name} : {underlying}", "\t{"]
    last = len(members) - 1
    for idx, m in enumerate(members):
        comma = not (idx == last and m.get("value") is None)
        if m.get("value") is None:
            line = f"\t\t{m['name']}"
        else:
            line = f"\t\t{m['name']} = {m['value']}"
        if comma:
            line += ","
        out.append(line)
    out.append("\t};")
    return "\n".join(out)


def render_var(key, v):
    abbr = v["host_abbr"]
    prefix = v["host_prefix"]
    if key == "header":
        return (
            "\tstruct Header\n"
            "\t{\n"
            "\t\tstd::uint32_t magic;\n"
            "\t\tstd::uint32_t version;\n"
            f"\t\tstd::uint32_t {prefix}Pid;\n"
            "\t\tstd::uint32_t mcPid;\n"
            f"\t\tstd::uint64_t {prefix}HeartbeatMs;\n"
            "\t\tstd::uint64_t mcHeartbeatMs;\n"
            "\t};\n"
            "\tstatic_assert(sizeof(Header) == 0x20);"
        )
    if key == "host_flags":
        return render_enum(f"{abbr}Flags", "std::uint32_t", v["host_flags"])
    if key == "host_state":
        hs = v["host_state"]
        body = "\n".join("\t\t" + ln.strip() for ln in hs["fields"])
        blk = (
            f"\tstruct {abbr}State\n"
            "\t{\n"
            f"{body}\n"
            "\t};\n"
            f"\tstatic_assert(sizeof({abbr}State) == {hs['size']});"
        )
        if hs.get("ground_grid") is not None:
            blk += (
                f"\n\tinline constexpr std::uint32_t kGroundGrid = {hs['ground_grid']};"
            )
        return blk
    if key == "mc_flags":
        return render_enum("McFlags", "std::uint32_t", v["mc_flags"])
    if key == "mc_state":
        ms = v["mc_state"]
        body = "\n".join("\t\t" + ln.strip() for ln in ms["fields"])
        return (
            "\tstruct McState\n"
            "\t{\n"
            f"{body}\n"
            "\t};\n"
            f"\tstatic_assert(sizeof(McState) == {ms['size']});\n"
            "\tstatic_assert(sizeof(McState) <= 0x100);"
        )
    if key == "input_type":
        return render_enum("InputType", "std::uint16_t", v["input_type"])
    if key == "hurt_flags":
        return render_enum("HurtFlags", "std::uint32_t", v["hurt_flags"])
    if key == "mc_event_type":
        return render_enum("McEventType", "std::uint32_t", v["mc_event_type"])
    if key == "ren_type":
        return render_enum("RenType", "std::uint32_t", v["ren_type"])
    if key == "col_tri_flags":
        ctf = v["col_tri_flags"]
        blk = render_enum("ColTriFlags", "std::uint32_t", ctf["members"])
        if ctf.get("has_shift"):
            blk += "\n\tinline constexpr std::uint32_t kTriMaterialShift = 8;"
        return blk
    if key == "dig_material":
        if not v.get("dig_material"):
            return None
        return render_enum("DigMaterial", "std::uint8_t", v["dig_material"])
    if key == "tool_kind":
        if not v.get("tool_kind"):
            return None
        return render_enum("ToolKind", "std::uint32_t", v["tool_kind"])
    raise ValueError(f"unknown var key {key}")


def generate(schema, vocab):
    c = schema["container"]
    out = []
    out.append("// Passthrough shared-memory protocol (generated from schema.yaml).")
    out.append("//")
    out.append("// This header is generated. The byte layout is the single source of truth in")
    out.append("// schema.yaml + the per-host vocabulary. All multi-byte values are little-endian.")
    out.append("#pragma once")
    out.append("")
    for inc in c["includes"]:
        out.append(inc)
    out.append("")
    out.append(f"namespace {vocab['namespace']}")
    out.append("{")

    out.append(
        f"\tinline constexpr std::uint32_t kMagic = {vocab['magic']};"
    )
    out.append(f"\tinline constexpr std::uint32_t kVersion = {vocab['version']};")
    out.append(f"\tinline constexpr wchar_t       kMappingName[] = L\"{vocab['mapping_name']}\";")
    out.append(f"\tinline constexpr double kUnitsPerBlock = {vocab['units_per_block']};")
    out.append("")

    abbr = vocab["host_abbr"]
    for item in c["order"]:
        kind = item["kind"]
        if kind == "regions":
            txt = c["regions_template"].format(host_state_off=f"kOff{abbr}State")
            out.append(txt)
        elif kind == "fixed":
            out.append(c["fixed"][item["key"]].strip("\n"))
        elif kind == "var":
            out.append(render_var(item["key"], vocab))
        elif kind == "optional":
            key = item["key"]
            present = (
                (key == "ren_dug" and vocab.get("ren_dug"))
                or (key == "dig_material" and vocab.get("dig_material"))
                or (key == "tool_kind" and vocab.get("tool_kind"))
            )
            if present:
                if key == "ren_dug":
                    out.append(c["fixed"]["ren_dug"].strip("\n"))
                else:
                    r = render_var(key, vocab)
                    if r:
                        out.append(r)
        out.append("")

    out.append("}")
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n", generate_sync(schema, vocab)


# Small seqlock / SPSC companion (NOT part of the verified header, kept separate so the
# header stays byte-identical to T1's gen_header.py and verify_roundtrip stays green).
def generate_sync(schema, vocab):
    abbr = vocab["host_abbr"]
    return (
        "// Passthrough seqlock + SPSC ring skeletons (generated; companion to the header).\n"
        "// These are ABI-neutral helpers: they only read/write the container offsets.\n"
        "#pragma once\n"
        f"namespace {vocab['namespace']} {{\n"
        "\n"
        "// seqlock: read a struct guarded by a u32 seq at `seq_off`.\n"
        "template <typename T>\n"
        "bool SeqlockRead(const std::uint8_t* base, std::uint64_t seq_off, T& out) {\n"
        "  for (;;) {\n"
        "    std::uint32_t s0 = *reinterpret_cast<const std::uint32_t*>(base + seq_off);\n"
        "    if (s0 & 1u) { return false; }            // writer mid-update\n"
        "    std::atomic_thread_fence(std::memory_order_acquire);\n"
        "    std::memcpy(&out, base + seq_off + 8, sizeof(T));\n"
        "    std::atomic_thread_fence(std::memory_order_acquire);\n"
        "    std::uint32_t s1 = *reinterpret_cast<const std::uint32_t*>(base + seq_off);\n"
        "    if (s0 == s1) { return true; }            // even, stable\n"
        "  }\n"
        "}\n"
        "\n"
        "template <typename T>\n"
        "void SeqlockWrite(std::uint8_t* base, std::uint64_t seq_off, const T& in) {\n"
        "  auto* s = reinterpret_cast<std::uint32_t*>(base + seq_off);\n"
        "  std::uint32_t s0 = *s + 1;                  // -> odd\n"
        "  std::atomic_thread_fence(std::memory_order_release);\n"
        "  *s = s0;\n"
        "  std::atomic_thread_fence(std::memory_order_release);\n"
        "  std::memcpy(base + seq_off + 8, &in, sizeof(T));\n"
        "  std::atomic_thread_fence(std::memory_order_release);\n"
        "  *s = s0 + 1;                                // -> even\n"
        "}\n"
        "\n"
        "// SPSC ring (power-of-two). head/tail are u64 at head_off/tail_off; data at data_off.\n"
        "inline std::uint64_t RingMask(std::uint64_t data_bytes) { return data_bytes - 1; }\n"
        "inline bool RingTryProduce(std::uint8_t* base, std::uint64_t head_off,\n"
        "                           std::uint64_t data_off, std::uint64_t data_bytes,\n"
        "                           const void* payload, std::uint64_t n) {\n"
        "  std::uint64_t head = *reinterpret_cast<std::uint64_t*>(base + head_off);\n"
        "  std::uint64_t mask = data_bytes - 1;\n"
        "  if ((head & mask) + n > data_bytes) { return false; }  // no room (simple bound)\n"
        "  std::uint64_t pos = head & mask;\n"
        "  std::memcpy(base + data_off + pos, payload, n);\n"
        "  *reinterpret_cast<std::uint64_t*>(base + head_off) = head + n;\n"
        "  return true;\n"
        "}\n"
        "inline bool RingTryConsume(std::uint8_t* base, std::uint64_t tail_off,\n"
        "                           std::uint64_t data_off, std::uint64_t data_bytes,\n"
        "                           void* out, std::uint64_t n) {\n"
        "  std::uint64_t tail = *reinterpret_cast<std::uint64_t*>(base + tail_off);\n"
        "  std::uint64_t head = *reinterpret_cast<std::uint64_t*>(base + tail_off - 0x40);\n"
        "  if (tail + n > head) { return false; }\n"
        "  std::uint64_t mask = data_bytes - 1;\n"
        "  std::uint64_t pos = tail & mask;\n"
        "  std::memcpy(out, base + data_off + pos, n);\n"
        "  *reinterpret_cast<std::uint64_t*>(base + tail_off) = tail + n;\n"
        "  return true;\n"
        "}\n"
        "}  // namespace\n"
    )
