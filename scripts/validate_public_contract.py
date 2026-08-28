#!/usr/bin/env python3
"""Reject drift between the portal, SDK sources, and vendored MCP contract."""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
CONTRACT = ROOT / "_data" / "public-mcp-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _canonical_number(value: float) -> str:
    require(math.isfinite(value), "non-finite contract number")
    if value == 0:
        return "0"
    negative = value < 0
    decimal = Decimal(repr(abs(value)))
    if Decimal("1e-6") <= decimal < Decimal("1e21"):
        rendered = format(decimal, "f").rstrip("0").rstrip(".")
    else:
        mantissa, exponent = format(decimal.normalize(), "e").split("e")
        rendered = f"{mantissa.rstrip('0').rstrip('.')}e{int(exponent):+d}"
    return f"-{rendered}" if negative else rendered


def jcs_bytes(value) -> bytes:
    def encode(item) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if isinstance(item, str):
            return json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if isinstance(item, int) and not isinstance(item, bool):
            return str(item)
        if isinstance(item, float):
            return _canonical_number(item)
        if isinstance(item, list):
            return "[" + ",".join(encode(child) for child in item) + "]"
        if isinstance(item, dict):
            return "{" + ",".join(
                f"{encode(key)}:{encode(item[key])}" for key in sorted(item)
            ) + "}"
        raise TypeError(type(item).__name__)

    return encode(value).encode()


def projection_hash(value) -> str:
    return hashlib.sha256(jcs_bytes(value)).hexdigest()


def enum_values(schema: dict, field: str) -> set[str]:
    value = schema.get("properties", {}).get(field, {})
    return set(value.get("enum", ())) | {
        member for branch in value.get("anyOf", ()) for member in branch.get("enum", ())
    }


def cast_visual_description_schema(compose_schema: dict) -> dict:
    try:
        return compose_schema["properties"]["plan"]["properties"]["cast"]["anyOf"][0]["items"]["properties"]["visual_description"]
    except (IndexError, KeyError, TypeError) as exc:
        raise AssertionError("CastMember.visual_description schema missing") from exc


def validate_cast_visual_description_semantics(compose_schema: dict) -> None:
    """Independently verify the portal's vendored explicit-cast contract truth."""
    visual = cast_visual_description_schema(compose_schema)
    description = visual.get("description")
    require(isinstance(description, str), "CastMember.visual_description description missing")
    normalized = description.casefold()
    for term in (
        "optional", "caller-authored", "appearance", "explicit-cast",
        "deterministic", "reference prompt",
    ):
        require(term in normalized, f"CastMember.visual_description omits {term}")
    require(
        not re.search(r"auto[- ]?populat|entity[- ]?(?:discovery|extraction)|narration[- ]?derived", description, re.I),
        "CastMember.visual_description makes an unavailable inference claim",
    )
    require(visual.get("default") is None, "CastMember.visual_description default must be null")
    require(
        any(branch.get("type") == "null" for branch in visual.get("anyOf", ())),
        "CastMember.visual_description must remain optional",
    )


def main() -> int:
    raw = CONTRACT.read_bytes()
    contract = json.loads(raw)
    pin = (CONTRACT.with_suffix(CONTRACT.suffix + ".sha256")).read_text().split()[0]
    meta = json.loads((ROOT / "_data/public-mcp-contract-meta.json").read_text())
    require(hashlib.sha256(raw).hexdigest() == pin, "vendored contract hash mismatch")
    require(meta["artifact_sha256"] == pin, "artifact discovery hash mismatch")
    require(meta["tool_schema_sha256"] == contract["tool_schema_sha256"], "tool projection hash mismatch")
    require(meta["lane_projection_sha256"] == contract["lane_projection_sha256"], "lane projection hash mismatch")
    tools = sorted(contract["tools"], key=lambda item: item["name"])
    tool_projection = [
        {
            "name": tool["name"],
            "inputSchema": tool["inputSchema"],
            "outputSchema": tool["outputSchema"],
            "annotations": tool["annotations"],
        }
        for tool in tools
    ]
    require(projection_hash(tool_projection) == contract["tool_schema_sha256"], "tool projection is not reproducible")
    lane_projection = {
        "contract_version": contract["contract_version"],
        "public_tier": contract["public_tier"],
        "pro_tools": contract["sets"]["pro_tools"],
        "free_tools": contract["sets"]["free_tools"],
        "x402_eligible_tools": contract["sets"]["x402_eligible_tools"],
        "authenticated_credit_only_tools": contract["sets"]["authenticated_credit_only_tools"],
        "execution": {tool["name"]: tool["execution"] for tool in tools},
        "provider_mode_matrix": contract["provider_mode_matrix"],
    }
    require(projection_hash(lane_projection) == contract["lane_projection_sha256"], "lane projection is not reproducible")
    require(contract["contract_version"] == "1.0", "unexpected contract version")
    require(contract["public_tier"] == "pro", "production contract must be pro")
    require(len(contract["sets"]["pro_tools"]) == 19, "expected 19 pro tools")
    require(contract["sets"]["free_tools"] == ["lib_list"], "lib_list must be sole free tool")
    require(contract["sets"]["authenticated_credit_only_tools"] == ["compose_video"], "Compose lane mismatch")
    require(len(contract["sets"]["x402_eligible_tools"]) == 17, "expected 17 x402 tools")
    require("compose_video" not in contract["sets"]["x402_eligible_tools"], "Compose cannot be x402")
    for key, value in contract["counts"].items():
        if key.endswith("_tools"):
            require(value == len(contract["sets"][key]), f"{key} count/set mismatch")

    by_name = {tool["name"]: tool for tool in tools}
    matrix_by_tool = {
        name: [row for row in contract["provider_mode_matrix"] if row["tool"] == name]
        for name in by_name
    }
    for name in ("create_image", "create_video", "create_audio", "create_music"):
        require(
            {row["provider"] for row in matrix_by_tool[name]}
            == enum_values(by_name[name]["inputSchema"], "provider"),
            f"{name} schema/matrix provider mismatch",
        )
    require(
        {mode for row in matrix_by_tool["create_audio"] for mode in row["modes"]}
        == enum_values(by_name["create_audio"]["inputSchema"], "mode"),
        "create_audio schema/matrix mode mismatch",
    )
    require(enum_values(by_name["create_music"]["inputSchema"], "provider") == {"lyria", "creative_freedom"}, "MiniMax music is public")
    compose_schema = by_name["compose_video"]["inputSchema"]
    require(compose_schema.get("additionalProperties") is False, "Compose arguments are not strict")
    require(compose_schema["properties"]["plan"].get("additionalProperties") is False, "Compose plan is not strict")
    require(compose_schema["properties"]["quality_profile"].get("default") == "stable", "Compose stable default missing")
    validate_cast_visual_description_semantics(compose_schema)
    require(by_name["manage_adapter"]["execution"] == "mixed", "manage_adapter execution mismatch")

    current_files = [ROOT / "README.md"]
    current_files.extend(sorted((ROOT / "guides").glob("*.md")))
    current_files.extend(sorted(path for path in (ROOT / "examples").rglob("*") if path.suffix in {".md", ".py", ".ts"}))
    current_files.extend([
        ROOT / "sdks" / "python" / "README.md",
        ROOT / "sdks" / "python" / "src" / "soundside" / "client.py",
        ROOT / "sdks" / "typescript" / "README.md",
        ROOT / "sdks" / "typescript" / "src" / "client.ts",
    ])
    current = "\n".join(path.read_text() for path in current_files)
    music_minimax_lines = [line for line in current.splitlines() if any(
        pattern in line.lower() for pattern in (
            "`create_music` (minimax)",
            "`create_music` | music from lyrics and style prompts | minimax",
            "`create_music` — music from lyrics + style prompt (minimax",
        )
    )]
    require(not music_minimax_lines, f"current docs claim MiniMax music: {music_minimax_lines}")
    require(not re.search(r"(?:no markup|wholesale rate|real-time pricing catalog)", current, re.I), "stale pricing claim")
    require(not re.search(r"list_adapters[^\n]*\(free\)|manage_adapter[^\n]*free", current, re.I), "non-free adapter claim")
    require("one credit" in current.lower() and "approximately 10%" in current, "authoritative pricing statement missing")
    require("five-credit success-only" in current.lower(), "Compose orchestration pricing missing")
    require("Compose" in current and "not available through x402" in current, "Compose x402 exclusion missing")
    guide_headings = re.findall(r"^## (\w+)$", (ROOT / "guides/tools.md").read_text(), re.M)
    require(
        sorted(name for name in guide_headings if name in by_name) == sorted(by_name),
        "tool guide inventory is not the exact contract set",
    )
    compose_reference = (ROOT / "guides/tools.md").read_text()
    require("public autonomy/tasks fields" in compose_reference, "Compose unsupported autonomy/tasks rule missing")
    require(not re.search(r'"autonomy_level"\s*:\s*"full"', current), "unsupported Compose autonomy example")
    require(not re.search(r'advanced_options\s*[=:]\s*\{[^\n}]*adapters', current, re.I), "unsupported image/video adapter nesting")

    python_source = (ROOT / "sdks/python/src/soundside/client.py").read_text()
    ts_source = (ROOT / "sdks/typescript/src/client.ts").read_text()
    require("artifact_type" not in python_source + ts_source, "SDK sends nonexistent artifact_type")
    require('"type": type' in python_source and "{ type, ...options }" in ts_source, "SDK artifact type field missing")
    require('"analysis_type": "transcribe"' in python_source + ts_source, "canonical transcription helper missing")
    require("pip install soundside\n" not in current and "npm install soundside\n" not in current, "registry install claim")
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    require(not any(path.startswith("sdks/python/dist/") for path in tracked), "Python distributions must not be committed")
    require(not any(path.startswith("sdks/typescript/dist/") for path in tracked), "TypeScript dist must not be committed")

    instruction_paths = [
        WORKSPACE / "AGENTS.md", WORKSPACE / "CLAUDE.md",
        WORKSPACE / "soundside-ai/public/llms.txt",
        WORKSPACE / "soundside-ai/docs/agent-integration-guide.md",
        WORKSPACE / ".agents/skills/autorefine/SKILL.md",
        WORKSPACE / "soundside-ai/docs/openclaw-skill/SKILL.md",
        ROOT / "examples/openclaw/SKILL.md",
    ]
    for path in instruction_paths:
        require(path.exists(), f"missing mandatory instruction path: {path}")
        source = path.read_text()
        lowered = source.lower()
        require("analyze_media" in source and "transcribe" in source, f"canonical STT fact missing: {path}")
        require("create_audio" in source and "transcribe" in source and ("deprecated" in lowered or "compatibility shim" in lowered), f"v1.x STT shim fact missing: {path}")
        require("stable" in lowered and "grok" in lowered and "compose" in lowered, f"Compose provider/default fact missing: {path}")
        require("minimax music is unavailable" in lowered, f"MiniMax music removal missing: {path}")
        require("approximately 10%" in lowered and ("five-credit" in lowered or "5-credit" in lowered or "adds five credits" in lowered), f"pricing fact missing: {path}")
        require("lib_list" in source and "free" in lowered, f"sole-free-tool fact missing: {path}")
        require(
            "remaining 17" in lowered or "x402-eligible tools (17)" in lowered,
            f"x402 lane count missing: {path}",
        )
    print(f"portal public contract {contract['contract_version']} validated ({len(contract['tools'])} tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
