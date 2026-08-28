"""Soundside MCP client — thin wrapper over Streamable HTTP transport."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from soundside.types import Resource, ToolResult

_DEFAULT_ENDPOINT = "https://mcp.soundside.ai/mcp"


class SoundsideError(Exception):
    """Raised on MCP-level or tool-level errors."""


class Soundside:
    """Client for the Soundside MCP media generation platform.

    Usage::

        from soundside import Soundside

        client = Soundside(api_key="mcp_your_key")
        image = client.create_image("A sunset over the ocean", provider="vertex")
        print(image.url)
    """

    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = _DEFAULT_ENDPOINT,
        timeout: int = 120,
    ) -> None:
        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout = timeout
        self._session_id: str | None = None
        self._msg_id = 0
        self._connected = False

    # ── low-level ──────────────────────────────────────────

    def _next_id(self) -> str:
        self._msg_id += 1
        return str(self._msg_id)

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            h["mcp-session-id"] = self._session_id
        return h

    @staticmethod
    def _parse_sse(text: str) -> dict[str, Any]:
        """Parse SSE response — find the JSON-RPC result frame."""
        last: dict[str, Any] | None = None
        for line in text.splitlines():
            if line.startswith("data:"):
                try:
                    obj = json.loads(line[5:].strip())
                    if "id" in obj:
                        return obj
                    last = obj
                except json.JSONDecodeError:
                    pass
        if last is not None:
            return last
        return json.loads(text)

    def _post(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a JSON-RPC request and return the parsed response."""
        with httpx.Client(timeout=self._timeout) as http:
            r = http.post(
                self._endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": method,
                    "params": params or {},
                },
                headers=self._headers(),
            )
            r.raise_for_status()
            if "mcp-session-id" in r.headers:
                self._session_id = r.headers["mcp-session-id"]
            return self._parse_sse(r.text)

    def _ensure_connected(self) -> None:
        if not self._connected:
            self.connect()

    # ── connection ─────────────────────────────────────────

    def connect(self) -> None:
        """Initialize the MCP session. Called automatically on first tool use."""
        self._post("initialize", {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "soundside-python-sdk", "version": "0.1.0"},
        })
        self._connected = True

    # ── generic tool call ──────────────────────────────────

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> ToolResult:
        """Call any MCP tool by name and return the parsed result."""
        self._ensure_connected()
        rpc = self._post("tools/call", {"name": name, "arguments": arguments or {}})

        if "error" in rpc:
            raise SoundsideError(f"MCP error: {rpc['error']}")

        result = rpc.get("result", {})
        if result.get("isError"):
            for ct in result.get("content", []):
                if ct.get("type") == "text":
                    raise SoundsideError(f"Tool error: {ct['text']}")
            raise SoundsideError("Tool error: unknown")

        # Merge structuredContent + content[0].text
        structured = result.get("structuredContent") or {}
        text_data: dict[str, Any] = {}
        for c in result.get("content", []):
            if c.get("type") == "text":
                try:
                    text_data = json.loads(c["text"])
                except (json.JSONDecodeError, KeyError):
                    text_data = {"text": c.get("text", "")}
                break

        merged = {**text_data, **structured}
        return ToolResult(
            success=merged.get("success", True),
            data=merged,
        )

    def list_tools(self) -> list[dict[str, Any]]:
        """Return the list of available tools and their schemas."""
        self._ensure_connected()
        rpc = self._post("tools/list")
        return rpc.get("result", {}).get("tools", [])

    # ── polling ────────────────────────────────────────────

    def wait_for_resource(
        self,
        resource_id: str,
        *,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> Resource:
        """Poll lib_list until an async resource completes. Free (0 credits)."""
        start = time.time()
        while time.time() - start < timeout:
            result = self.call_tool("lib_list", {
                "entity_type": "resources",
                "resource_id": resource_id,
            })
            items = result.data.get("items", [])
            item = items[0] if items else result.data
            status = item.get("status") or item.get("state", "")

            if status in ("failed", "error"):
                raise SoundsideError(
                    f"Resource {resource_id} failed: {item.get('failure_reason', 'unknown')}"
                )
            # Signed asset URL lands on the item as ``url`` once the backend
            # finalizes the resource; older responses used ``storage_url``.
            if status == "completed" and (item.get("url") or item.get("storage_url")):
                return Resource.from_dict(item)

            time.sleep(poll_interval)

        raise TimeoutError(f"Resource {resource_id} did not complete in {timeout}s")

    def get_resource(self, resource_id: str) -> Resource:
        """Fetch a resource's full details (including signed URL) via lib_list. Free."""
        result = self.call_tool("lib_list", {
            "entity_type": "resources",
            "resource_id": resource_id,
        })
        items = result.data.get("items", [])
        if not items:
            raise SoundsideError(f"Resource {resource_id} not found")
        return Resource.from_dict(items[0])

    def _ensure_url(self, resource: Resource) -> Resource:
        """Re-fetch if the signed URL is missing (e.g. sync response didn't carry it)."""
        if resource.url:
            return resource
        return self.get_resource(resource.resource_id)

    # ── convenience methods ────────────────────────────────

    def create_image(
        self,
        prompt: str,
        *,
        provider: str,
        **kwargs: Any,
    ) -> Resource:
        """Generate an image. Returns a Resource with storage_url populated."""
        args: dict[str, Any] = {"prompt": prompt, **kwargs}
        args["provider"] = provider
        result = self.call_tool("create_image", args)
        res = result.resource
        if res is None:
            raise SoundsideError(f"No resource_id in response: {result.data}")
        return self._ensure_url(res)

    def create_video(
        self,
        prompt: str,
        *,
        provider: str,
        first_frame: str | None = None,
        wait: bool = True,
        wait_timeout: int = 600,
        **kwargs: Any,
    ) -> Resource:
        """Generate a video. Async by default — waits for completion unless wait=False."""
        args: dict[str, Any] = {"prompt": prompt, **kwargs}
        args["provider"] = provider
        if first_frame:
            args["first_frame"] = first_frame
        result = self.call_tool("create_video", args)
        res = result.resource
        if res is None:
            raise SoundsideError(f"No resource_id in response: {result.data}")
        if wait and res.status != "completed":
            return self.wait_for_resource(res.resource_id, timeout=wait_timeout)
        return res

    def create_audio(
        self,
        prompt: str,
        *,
        provider: str,
        mode: str = "tts",
        **kwargs: Any,
    ) -> Resource:
        """Generate audio (TTS, sound effects, and voice operations)."""
        args: dict[str, Any] = {"prompt": prompt, "mode": mode, **kwargs}
        args["provider"] = provider
        result = self.call_tool("create_audio", args)
        res = result.resource
        if res is None:
            raise SoundsideError(f"No resource_id in response: {result.data}")
        return self._ensure_url(res)

    def create_music(
        self,
        prompt: str,
        *,
        lyrics: str | None = None,
        provider: str,
        wait: bool = True,
        wait_timeout: int = 300,
        **kwargs: Any,
    ) -> Resource:
        """Generate a music track. Async — waits for completion unless wait=False."""
        args: dict[str, Any] = {"prompt": prompt, **kwargs}
        if lyrics:
            args["lyrics"] = lyrics
        args["provider"] = provider
        result = self.call_tool("create_music", args)
        res = result.resource
        if res is None:
            raise SoundsideError(f"No resource_id in response: {result.data}")
        if wait and res.status != "completed":
            return self.wait_for_resource(res.resource_id, timeout=wait_timeout)
        return res

    def create_text(
        self,
        prompt: str,
        *,
        provider: str | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """Generate text via LLM. Returns a ToolResult (use .text for the output)."""
        args: dict[str, Any] = {"prompt": prompt, **kwargs}
        if provider:
            args["provider"] = provider
        return self.call_tool("create_text", args)

    def create_artifact(
        self,
        type: str,
        **kwargs: Any,
    ) -> Resource:
        """Create a business artifact (presentation, chart, document, diagram)."""
        args: dict[str, Any] = {"type": type, **kwargs}
        result = self.call_tool("create_artifact", args)
        res = result.resource
        if res is None:
            raise SoundsideError(f"No resource_id in response: {result.data}")
        return self._ensure_url(res)

    def transcribe(
        self,
        resource_id: str,
        *,
        language_code: str = "en-US",
        include_word_timestamps: bool = True,
        enable_diarization: bool = False,
        enable_silence_detection: bool = False,
        silence_threshold_sec: float = 1.0,
        subtitle_formats: list[str] | None = None,
    ) -> ToolResult:
        """Transcribe media through the canonical analyze_media surface."""
        return self.call_tool("analyze_media", {
            "resource_id": resource_id,
            "analysis_type": "transcribe",
            "language_code": language_code,
            "include_word_timestamps": include_word_timestamps,
            "enable_diarization": enable_diarization,
            "enable_silence_detection": enable_silence_detection,
            "silence_threshold_sec": silence_threshold_sec,
            "subtitle_formats": subtitle_formats,
        })

    def edit_video(
        self,
        resource_id: str,
        action: str,
        **kwargs: Any,
    ) -> Resource:
        """Apply a core editing action (trim, concat, crossfade, adjust_speed, loop, color_grade, custom, burn_subtitles)."""
        args: dict[str, Any] = {"resource_id": resource_id, "action": action, **kwargs}
        result = self.call_tool("edit_video", args)
        res = result.resource
        if res is None:
            raise SoundsideError(f"No resource_id in response: {result.data}")
        return self._ensure_url(res)

    def compose_media(
        self,
        action: str,
        *,
        resource_id: str | None = None,
        resource_ids: list[str] | None = None,
        **kwargs: Any,
    ) -> Resource:
        """Compose media (add_text, overlay, split_screen)."""
        args: dict[str, Any] = {"action": action, **kwargs}
        if resource_id:
            args["resource_id"] = resource_id
        if resource_ids:
            args["resource_ids"] = resource_ids
        result = self.call_tool("compose_media", args)
        res = result.resource
        if res is None:
            raise SoundsideError(f"No resource_id in response: {result.data}")
        return self._ensure_url(res)

    def edit_audio(
        self,
        resource_id: str,
        action: str,
        **kwargs: Any,
    ) -> Resource:
        """Edit audio on video (mix_audio, replace_audio, pad_audio)."""
        args: dict[str, Any] = {"resource_id": resource_id, "action": action, **kwargs}
        result = self.call_tool("edit_audio", args)
        res = result.resource
        if res is None:
            raise SoundsideError(f"No resource_id in response: {result.data}")
        return self._ensure_url(res)

    def apply_effect(
        self,
        resource_id: str,
        action: str,
        **kwargs: Any,
    ) -> Resource:
        """Apply cinematic effect (ken_burns, speed_ramp, film_grain, vignette)."""
        args: dict[str, Any] = {"resource_id": resource_id, "action": action, **kwargs}
        result = self.call_tool("apply_effect", args)
        res = result.resource
        if res is None:
            raise SoundsideError(f"No resource_id in response: {result.data}")
        return self._ensure_url(res)

    def extract_media(
        self,
        resource_id: str,
        action: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Extract content from media (extract_frame, extract_frames, extract_audio).
        
        Returns ToolResult — use .data['resource_id'] or .data['resource_ids'].
        """
        args: dict[str, Any] = {"resource_id": resource_id, "action": action, **kwargs}
        return self.call_tool("extract_media", args)

    def analyze_media(
        self,
        resource_id: str,
        *,
        analysis_type: str = "technical",
        **kwargs: Any,
    ) -> ToolResult:
        """Analyze a media resource. Returns full analysis data."""
        args: dict[str, Any] = {
            "resource_id": resource_id,
            "analysis_type": analysis_type,
            **kwargs,
        }
        return self.call_tool("analyze_media", args)

    def lib_list(
        self,
        entity_type: str = "resources",
        **kwargs: Any,
    ) -> ToolResult:
        """List library entities (resources, projects, collections). Free."""
        args: dict[str, Any] = {"entity_type": entity_type, **kwargs}
        return self.call_tool("lib_list", args)

    def lib_manage(
        self,
        entity_type: str,
        operation: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Create, update, or delete library entities."""
        args: dict[str, Any] = {
            "entity_type": entity_type,
            "operation": operation,
            **kwargs,
        }
        return self.call_tool("lib_manage", args)
