"""
Soundside MCP Client — Python Example

Demonstrates connecting to Soundside's MCP endpoint, listing tools,
generating an image, and checking the result.

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
    """Simple synchronous MCP client for Soundside."""

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
        """Parse SSE response — server may emit multiple frames (notifications
        then result). Find the frame that has an 'id' field (the JSON-RPC
        response); skip notification frames that only have 'method'.
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
        """Extract the tool result from an MCP JSON-RPC response."""
        content = rpc_result.get("result", {}).get("content", [])
        for c in content:
            if c.get("type") == "text":
                try:
                    return json.loads(c["text"])
                except json.JSONDecodeError:
                    return {"text": c["text"]}
        return rpc_result

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
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "soundside-python-example", "version": "1.0"},
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
        """Call an MCP tool and return the parsed result."""
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
                return {"error": rpc["error"]}
            return self._extract_tool_result(rpc)


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

    # 3. Generate an image
    print("\n🎨 Generating image (vertex)...")
    t0 = time.time()
    result = client.call_tool("create_image", {
        "prompt": "A vibrant sunset over a calm ocean, photorealistic",
        "provider": "vertex",
    })
    elapsed = time.time() - t0
    print(f"  Resource ID: {result.get('resource_id', 'N/A')}")
    print(f"  Time: {elapsed:.1f}s")
    if result.get("storage_url"):
        print(f"  URL: {result['storage_url'][:80]}...")

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

    print(f"\n📝 Generating text (vertex)...")
    text_result = client.call_tool("create_text", {
        "prompt": "Write a haiku about AI agents creating art",
        "provider": "vertex",
    })
    # Server may return 'message' or 'text'; handle both
    text_output = text_result.get("message") or text_result.get("text") or str(text_result)[:200]
    print(f"  {text_output}")


if __name__ == "__main__":
    main()
