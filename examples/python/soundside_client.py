"""
Soundside MCP Client — Python SDK

Production-grade client for Soundside's MCP endpoint with async polling,
error handling, and pipeline support.

Requirements:
    pip install httpx

Usage:
    python soundside_client.py <API_KEY>
    # or
    SOUNDSIDE_API_KEY=mcp_... python soundside_client.py
"""

import httpx
import json
import os
import sys
import time


class SoundsideClient:
    """Production MCP client for Soundside with async resource polling."""

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

    def _parse_sse(self, text: str) -> dict:
        """Parse SSE response — server emits notification frames before the
        actual JSON-RPC result. Find the frame with 'id' (the response).
        Falls back to last data frame if no 'id' frame found.
        """
        last_data = None
        for line in text.splitlines():
            if line.startswith("data:"):
                try:
                    obj = json.loads(line[5:].strip())
                    # JSON-RPC responses have 'id'; notifications do not
                    if "id" in obj:
                        return obj
                    last_data = obj  # keep as fallback
                except json.JSONDecodeError:
                    pass
        if last_data is not None:
            return last_data
        # Fall back: try parsing the whole text as JSON
        return json.loads(text)

    def _extract_tool_result(self, rpc_result: dict) -> dict:
        """Extract the tool result from an MCP JSON-RPC response.

        Soundside MCP returns data in two places:
        - content[0].text — JSON string (sync tools) or plain message (async tools)
        - structuredContent — always a dict with resource_id, state, etc.

        For async tools (create_video, create_music), the resource_id is ONLY
        in structuredContent, so we merge both sources.
        """
        result = rpc_result.get("result", {})

        # Check for tool-level errors (isError=True in MCP result)
        if result.get("isError"):
            for ct in result.get("content", []):
                if ct.get("type") == "text":
                    raise RuntimeError(f"Tool error: {ct['text']}")
            raise RuntimeError("Tool error: unknown error")

        # Extract from content[0].text (may be JSON or plain text)
        text_result = {}
        content = result.get("content", [])
        for c in content:
            if c.get("type") == "text":
                try:
                    text_result = json.loads(c["text"])
                except json.JSONDecodeError:
                    text_result = {"text": c["text"]}
                break

        # Extract from structuredContent (always has resource_id for async tools)
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            # Merge: structuredContent wins for resource tracking fields
            merged = {**text_result, **structured}
            return merged

        return text_result or rpc_result

    def connect(self) -> dict:
        """Initialize MCP session."""
        with httpx.Client(timeout=30) as client:
            r = client.post(
                self.endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-11-25",
                        "capabilities": {},
                        "clientInfo": {"name": "soundside-python-sdk", "version": "1.1"},
                    },
                },
                headers=self._headers(),
            )
            self.session_id = r.headers.get("mcp-session-id")
            return self._parse_sse(r.text)

    def list_tools(self) -> list:
        """Get available tools and their schemas."""
        with httpx.Client(timeout=30) as client:
            r = client.post(
                self.endpoint,
                json={"jsonrpc": "2.0", "id": self._next_id(), "method": "tools/list", "params": {}},
                headers=self._headers(),
            )
            result = self._parse_sse(r.text)
            return result.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict, timeout: int = 120) -> dict:
        """Call an MCP tool and return the parsed result.

        Raises RuntimeError on JSON-RPC errors or tool-level errors (isError).
        """
        with httpx.Client(timeout=timeout) as client:
            r = client.post(
                self.endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                },
                headers=self._headers(),
            )
            rpc = self._parse_sse(r.text)
            if "error" in rpc:
                raise RuntimeError(f"MCP error: {rpc['error']}")
            return self._extract_tool_result(rpc)

    def wait_for_resource(
        self,
        resource_id: str,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> dict:
        """Poll until an async resource completes.

        Checks lib_list every `poll_interval` seconds until:
        - status="completed" AND url is present → returns the resource dict
        - status="failed" or "error" → raises RuntimeError
        - timeout exceeded → raises TimeoutError

        lib_list calls are free (zero credits). The signed GCS asset URL
        arrives on the item as ``url`` (older responses used ``storage_url``
        — both are accepted).

        Args:
            resource_id: UUID of the resource to wait for.
            timeout: Maximum seconds to wait (default 300, use 600 for video).
            poll_interval: Seconds between polls (default 5).

        Returns:
            The resource dict from lib_list (includes url, status, metadata).
        """
        start = time.time()
        while time.time() - start < timeout:
            result = self.call_tool("lib_list", {
                "entity_type": "resources",
                "resource_id": resource_id,
            })
            # lib_list wraps results: {success, status, items: [...]}
            item = result.get("items", [{}])[0] if result.get("items") else result
            status = item.get("status") or item.get("state", "")

            if status in ("failed", "error"):
                reason = item.get("failure_reason", "unknown")
                raise RuntimeError(f"Resource {resource_id} failed: {reason}")

            if status == "completed" and (item.get("url") or item.get("storage_url")):
                return item

            time.sleep(poll_interval)

        raise TimeoutError(f"Resource {resource_id} did not complete in {timeout}s")

    def call_and_wait(
        self,
        name: str,
        arguments: dict,
        timeout: int = 300,
        poll_interval: int = 5,
        call_timeout: int = 120,
    ) -> dict:
        """Call an MCP tool, then poll until the resource completes.

        Convenience wrapper for tools that return async resource_ids.
        Combines call_tool() + wait_for_resource() in one call.

        Args:
            name: Tool name (e.g., "create_video").
            arguments: Tool arguments dict.
            timeout: Max seconds to wait for resource completion.
            poll_interval: Seconds between polls.
            call_timeout: HTTP timeout for the initial tool call.

        Returns:
            The completed resource dict (includes url, status, metadata).
        """
        result = self.call_tool(name, arguments, timeout=call_timeout)
        resource_id = result.get("resource_id")
        if not resource_id:
            # Tool returned synchronously (no resource_id to poll)
            return result

        status = result.get("status") or result.get("state", "")
        asset_url = result.get("url") or result.get("storage_url")
        if status == "completed" and asset_url:
            # Already complete (sync tool or instant result)
            return result

        # Async — poll until done
        return self.wait_for_resource(resource_id, timeout=timeout, poll_interval=poll_interval)


def main():
    api_key = (
        sys.argv[1] if len(sys.argv) > 1
        else os.environ.get("SOUNDSIDE_API_KEY")
    )
    if not api_key:
        print("Usage: python soundside_client.py <API_KEY>")
        print("   or: SOUNDSIDE_API_KEY=mcp_... python soundside_client.py")
        sys.exit(1)

    client = SoundsideClient(api_key)

    # 1. Connect
    print("Connecting to Soundside MCP...")
    client.connect()
    print(f"✅ Connected (session: {client.session_id[:16]}...)")

    # 2. List tools
    tools = client.list_tools()
    print(f"\n📋 Available tools ({len(tools)}):")
    for t in tools:
        print(f"  • {t['name']}: {t.get('description', '')[:60]}")

    # 3. Generate an image (sync — returns immediately)
    print("\n🎨 Generating image (vertex)...")
    t0 = time.time()
    result = client.call_tool("create_image", {
        "prompt": "A vibrant sunset over a calm ocean, photorealistic",
        "provider": "vertex",
    })
    elapsed = time.time() - t0
    print(f"  Resource ID: {result.get('resource_id', 'N/A')}")
    print(f"  Time: {elapsed:.1f}s")
    asset_url = result.get("url") or result.get("storage_url")
    if asset_url:
        print(f"  URL: {asset_url[:80]}...")

    # 4. Analyze it
    if result.get("resource_id"):
        print("\n🔍 Analyzing image...")
        analysis = client.call_tool("analyze_media", {
            "resource_id": result["resource_id"],
        })
        meta = analysis.get("metadata", analysis)
        print(f"  Type: {meta.get('mime_type', 'N/A')}")
        if "image" in meta:
            img = meta["image"]
            print(f"  Dimensions: {img.get('width')}×{img.get('height')}")

    # 5. Generate text
    print(f"\n📝 Generating text (vertex)...")
    text_result = client.call_tool("create_text", {
        "prompt": "Write a haiku about AI agents creating art",
        "provider": "vertex",
    })
    text_output = text_result.get("message") or text_result.get("text") or str(text_result)[:200]
    print(f"  {text_output}")

    # 6. Demo: call_and_wait (generates video and polls until complete)
    print(f"\n🎬 Generating video with call_and_wait (minimax)...")
    print("   This calls create_video then automatically polls until complete.")
    if result.get("resource_id"):
        t0 = time.time()
        try:
            video = client.call_and_wait("create_video", {
                "prompt": "Gentle waves lapping at a golden shore at sunset",
                "provider": "minimax",
                "first_frame": result["resource_id"],
            }, timeout=600)
            elapsed = time.time() - t0
            print(f"  ✅ Video complete in {elapsed:.1f}s")
            print(f"  Resource ID: {video.get('id', video.get('resource_id', 'N/A'))}")
            video_url = video.get("url") or video.get("storage_url")
            if video_url:
                print(f"  URL: {video_url[:80]}...")
        except (RuntimeError, TimeoutError) as e:
            print(f"  ⚠️  Video generation failed: {e}")


if __name__ == "__main__":
    main()
