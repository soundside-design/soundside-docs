"""
Soundside Vision QA — Example

Demonstrates analyze_media(analysis_type="vision_qa") for:
  1. Generic quality scoring on an image
  2. Generic quality scoring on a video
  3. Spec-driven production QA using intent_checklist

vision_qa uses:
  - Gemini 2.5 Pro for VIDEO  (temporal reasoning + native audio understanding)
  - Gemini 2.5 Flash for IMAGE (faster, sufficient for single frames)

Cost: 3 credits per call (Gemini inference). Technical analysis is 1 credit.

Requirements:
    pip install httpx

Usage:
    SOUNDSIDE_API_KEY=mcp_... python vision_qa_example.py
"""

import httpx
import json
import os
import sys


class SoundsideClient:
    """Minimal MCP client for Soundside."""

    def __init__(self, api_key: str, endpoint: str = "https://mcp.soundside.ai/mcp"):
        self.api_key = api_key
        self.endpoint = endpoint
        self.session_id = None
        self._msg_id = 0

    def _next_id(self) -> str:
        self._msg_id += 1
        return str(self._msg_id)

    def _headers(self) -> dict:
        h = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            h["mcp-session-id"] = self.session_id
        return h

    def _parse(self, text: str) -> dict:
        """Parse SSE response — server emits notification frames before the
        actual JSON-RPC result. Find the frame with 'id' (the response)."""
        last_data = None
        for line in text.splitlines():
            if line.startswith("data:"):
                try:
                    obj = json.loads(line[5:].strip())
                    if "id" in obj:
                        return obj
                    last_data = obj
                except json.JSONDecodeError:
                    pass
        if last_data is not None:
            return last_data
        return json.loads(text)

    def connect(self):
        with httpx.Client(timeout=30) as c:
            r = c.post(self.endpoint, json={
                "jsonrpc": "2.0", "id": self._next_id(), "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                           "clientInfo": {"name": "vision-qa-example", "version": "1.0"}}
            }, headers=self._headers())
            self.session_id = r.headers.get("mcp-session-id")

    def call(self, tool: str, args: dict, timeout: int = 120) -> dict:
        with httpx.Client(timeout=timeout) as c:
            r = c.post(self.endpoint, json={
                "jsonrpc": "2.0", "id": self._next_id(), "method": "tools/call",
                "params": {"name": tool, "arguments": args}
            }, headers=self._headers())
            rpc = self._parse(r.text)
            if "error" in rpc:
                raise RuntimeError(f"MCP error: {rpc['error']}")
            for content in rpc.get("result", {}).get("content", []):
                if content.get("type") == "text":
                    try:
                        return json.loads(content["text"])
                    except json.JSONDecodeError:
                        return {"text": content["text"]}
            return rpc


def print_qa_result(result: dict):
    """Pretty-print a vision_qa result."""
    meta = result.get("metadata", result)
    score = meta.get("score", "?")
    passed = meta.get("passed", "?")
    issues = meta.get("issues", [])
    suggestions = meta.get("suggestions", [])
    audio_summary = meta.get("audio_summary", "")
    checklist = meta.get("checklist_results", {})

    icon = "✅" if passed else "❌"
    print(f"   {icon} score={score:.2f} passed={passed}")
    if audio_summary:
        print(f"   🔊 Audio: {audio_summary}")
    if checklist:
        print("   📋 Checklist:")
        for k, v in checklist.items():
            status = "✓" if v == "pass" else "✗" if v == "fail" else "–"
            print(f"      {status} {k}: {v}")
    if issues:
        print("   ⚠️  Issues:")
        for issue in issues:
            print(f"      • {issue}")
    if suggestions:
        print("   💡 Suggestions:")
        for s in suggestions:
            print(f"      • {s}")


def main():
    api_key = os.environ.get("SOUNDSIDE_API_KEY")
    if not api_key:
        print("Set SOUNDSIDE_API_KEY environment variable")
        sys.exit(1)

    # Pass a resource ID or public URL from your library
    resource_id = os.environ.get("SOUNDSIDE_RESOURCE_ID")
    if not resource_id:
        print("Set SOUNDSIDE_RESOURCE_ID to a video or image resource ID to analyze")
        sys.exit(1)

    client = SoundsideClient(api_key)
    client.connect()
    print("✅ Connected\n")

    # --- Step 1: Technical analysis (1 credit, fast) ---
    print("📀 Step 1: Technical analysis (ffprobe)...")
    tech = client.call("analyze_media", {
        "resource_id": resource_id,
        "analysis_type": "technical",
    })
    meta = tech.get("metadata", tech)
    # Field names differ slightly between image and video responses
    duration = meta.get("duration_sec") or meta.get("duration", "N/A (image)")
    width = meta.get("width") or meta.get("resolution", {"width": "?"}).get("width", "?")
    height = meta.get("height") or meta.get("resolution", {"height": "?"}).get("height", "?")
    print(f"   Duration: {duration}s")
    print(f"   Resolution: {width}x{height}")
    print(f"   Codec: {meta.get('video_codec') or meta.get('codec', 'N/A')} | FPS: {meta.get('frame_rate', 'N/A')}")
    print(f"   Audio: {meta.get('audio_codec', 'N/A')} | Channels: {meta.get('audio_channels', 'N/A')}")

    # --- Step 2: Generic vision QA (3 credits) ---
    print("\n🔍 Step 2: Generic vision QA...")
    print("   (Gemini 2.5 Pro for video / 2.5 Flash for images — 3 credits)")
    generic_qa = client.call("analyze_media", {
        "resource_id": resource_id,
        "analysis_type": "vision_qa",
        "reference_prompt": "A high-quality visual asset, professional and cinematic",
        "criteria": ["prompt_match", "artifacts", "composition", "audio_quality"],
    })
    print_qa_result(generic_qa)

    # --- Step 3: Spec-driven QA with intent_checklist (3 credits) ---
    # Customize the checklist to match your production spec.
    # All checklist keys are optional — include only what you want verified.
    print("\n📋 Step 3: Spec-driven QA (intent_checklist)...")
    print("   Checking: no pillarboxing, no audio overlap, text timing, language")
    spec_qa = client.call("analyze_media", {
        "resource_id": resource_id,
        "analysis_type": "vision_qa",
        "intent_checklist": {
            # Verify text overlay appears only in the specified window
            "text_overlays": [
                {"text": "Seoul, 1987", "start_sec": 1, "end_sec": 6},
            ],
            # Flag black bars that indicate aspect ratio mismatch between clips
            "no_pillarboxing": True,
            # Flag if multiple narrations play simultaneously (audio mix defect)
            "no_audio_overlap": True,
            # Verify spoken and written language
            "expected_language": "English",
            # Verify the video meets a minimum resolution
            "expected_resolution": "1280x720",
        },
    })
    print_qa_result(spec_qa)

    print("\n✅ Done!")
    print(f"   Resource: {resource_id}")
    if not spec_qa.get("metadata", spec_qa).get("passed", True):
        print("   ⚠️  QA did not pass — review issues above before delivering.")


if __name__ == "__main__":
    main()
