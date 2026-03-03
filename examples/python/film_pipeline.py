"""
Soundside Film Pipeline — End-to-End Example

Demonstrates the full creative pipeline:
  1. Generate a portrait image (vertex)
  2. Generate video from that image (minimax I2V)
  3. Generate narration (minimax TTS)
  4. Generate background music (minimax)
  5. Add text overlay to video
  6. Extend video with Ken Burns to fit narration length
  7. Mix narration into video
  8. Mix music into final

This is a simplified version of the "Felix the Fox" demo film
produced via Soundside's x402 payment path.

Requirements:
    pip install httpx

Usage:
    SOUNDSIDE_API_KEY=mcp_... python film_pipeline.py
"""

import httpx
import json
import os
import sys
import time


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
        for line in text.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        return json.loads(text)

    def connect(self):
        with httpx.Client(timeout=30) as c:
            r = c.post(self.endpoint, json={
                "jsonrpc": "2.0", "id": self._next_id(), "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                           "clientInfo": {"name": "film-pipeline", "version": "1.0"}}
            }, headers=self._headers())
            self.session_id = r.headers.get("mcp-session-id")

    def call(self, tool: str, args: dict, timeout: int = 300) -> dict:
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

    def wait_for_resource(self, resource_id: str, timeout: int = 300) -> dict:
        """Poll until an async resource completes."""
        start = time.time()
        while time.time() - start < timeout:
            result = self.call("lib_list", {
                "entity_type": "resources",
                "resource_id": resource_id,
            })
            state = result.get("state") or result.get("status", "")
            if state == "completed":
                return result
            if state in ("failed", "error"):
                raise RuntimeError(f"Resource {resource_id} failed: {result}")
            time.sleep(5)
        raise TimeoutError(f"Resource {resource_id} did not complete in {timeout}s")


def main():
    api_key = os.environ.get("SOUNDSIDE_API_KEY")
    if not api_key:
        print("Set SOUNDSIDE_API_KEY environment variable")
        sys.exit(1)

    client = SoundsideClient(api_key)
    client.connect()
    print("✅ Connected\n")

    # --- Step 1: Generate portrait image ---
    print("🎨 Step 1: Generating portrait image...")
    t0 = time.time()
    img = client.call("create_image", {
        "prompt": "A small orange fox sitting in a sunlit forest clearing, "
                  "children's storybook illustration, warm watercolor palette",
        "provider": "vertex",
    })
    portrait_id = img["resource_id"]
    print(f"   Portrait: {portrait_id} ({time.time()-t0:.1f}s)")

    # --- Step 2: Generate video from image (I2V) ---
    print("\n🎬 Step 2: Generating video from image (async)...")
    t0 = time.time()
    vid = client.call("create_video", {
        "prompt": "The fox stretches, yawns, and looks around the forest clearing",
        "provider": "minimax",
        "first_frame": portrait_id,
    })
    video_id = vid["resource_id"]
    print(f"   Submitted: {video_id}")
    client.wait_for_resource(video_id)
    print(f"   Video ready ({time.time()-t0:.1f}s)")

    # --- Step 3: Generate narration ---
    print("\n🎤 Step 3: Generating narration...")
    t0 = time.time()
    narr = client.call("create_audio", {
        "provider": "minimax",
        "mode": "tts",
        "text": "In a quiet forest, a small fox named Felix woke with the sunrise. "
                "Today would be his greatest adventure yet.",
    })
    narr_id = narr["resource_id"]
    print(f"   Narration: {narr_id} ({time.time()-t0:.1f}s)")

    # --- Step 4: Generate music ---
    print("\n🎵 Step 4: Generating background music (async)...")
    t0 = time.time()
    music = client.call("create_music", {
        "provider": "minimax",
        "lyrics": "",
        "prompt": "Gentle folk acoustic, warm and uplifting, children's story soundtrack",
    })
    music_id = music["resource_id"]
    print(f"   Submitted: {music_id}")
    client.wait_for_resource(music_id)
    print(f"   Music ready ({time.time()-t0:.1f}s)")

    # --- Step 5: Add text overlay ---
    print("\n✏️ Step 5: Adding provider overlay...")
    overlay = client.call("edit_video", {
        "resource_id": video_id,
        "action": "add_text",
        "text": "create_video • minimax • image_to_video",
        "position": "bottom_left",
        "fontsize": 24,
        "fontcolor": "white",
        "advanced_options": {"bg_color": "rgba(0,0,0,0.5)"},
    })
    overlay_id = overlay["resource_id"]
    print(f"   Overlay: {overlay_id}")

    # --- Step 6: Check durations and extend if needed ---
    print("\n📏 Step 6: Checking durations...")
    vid_info = client.call("analyze_media", {"resource_id": overlay_id})
    narr_info = client.call("analyze_media", {"resource_id": narr_id})
    vid_dur = vid_info.get("metadata", {}).get("duration_sec", 0)
    narr_dur = narr_info.get("metadata", {}).get("duration_sec", 0)
    print(f"   Video: {vid_dur:.1f}s, Narration: {narr_dur:.1f}s")

    final_video_id = overlay_id
    if narr_dur > vid_dur:
        extra = narr_dur - vid_dur + 1.0
        print(f"   ⚠️  Narration longer than video by {extra-1:.1f}s — extending with Ken Burns...")

        # Extract last frame
        frame = client.call("edit_video", {
            "resource_id": video_id,
            "action": "extract_frame",
            "timestamp": max(0, vid_dur - 0.5),
        })

        # Ken Burns the last frame
        kb = client.call("edit_video", {
            "resource_id": frame["resource_id"],
            "action": "ken_burns",
            "zoom_start": 1.0,
            "zoom_end": 1.05,
            "pan_direction": "center",
            "advanced_options": {"duration": int(extra + 1)},
        })

        # Concat original + extension
        extended = client.call("edit_video", {
            "action": "concat",
            "resource_ids": [overlay_id, kb["resource_id"]],
        })
        final_video_id = extended["resource_id"]
        print(f"   Extended video: {final_video_id}")

    # --- Step 7: Mix narration ---
    print("\n🔊 Step 7: Mixing narration into video...")
    narrated = client.call("edit_video", {
        "resource_id": final_video_id,
        "action": "mix_audio",
        "audio_source": narr_id,
        "video_volume": 0.0,
        "overlay_volume": 1.0,
        "duration_mode": "first",
    })
    narrated_id = narrated["resource_id"]
    print(f"   Narrated: {narrated_id}")

    # --- Step 8: Mix music ---
    print("\n🎶 Step 8: Mixing background music...")
    final = client.call("edit_video", {
        "resource_id": narrated_id,
        "action": "mix_audio",
        "audio_source": music_id,
        "video_volume": 1.0,
        "overlay_volume": 0.25,
    })
    final_id = final["resource_id"]
    print(f"   Final: {final_id}")

    # --- Done ---
    print(f"\n✅ Film complete!")
    print(f"   Resource ID: {final_id}")
    if final.get("storage_url"):
        print(f"   Download: {final['storage_url'][:80]}...")
    print(f"\n   To check status later:")
    print(f'   lib_list(entity_type="resources", resource_id="{final_id}")')


if __name__ == "__main__":
    main()
