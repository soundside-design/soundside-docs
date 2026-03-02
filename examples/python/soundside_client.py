"""
Soundside MCP Client — Python Example

Demonstrates connecting to Soundside's MCP endpoint and generating media.
Requires: pip install httpx
"""

import httpx
import json
import sys
import time


class SoundsideClient:
    """Simple MCP client for Soundside."""

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
        """Parse SSE response and return the JSON-RPC result."""
        for line in text.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:])
        # Fallback: try parsing as plain JSON
        return json.loads(text)

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
                        "clientInfo": {"name": "soundside-python", "version": "1.0"},
                    },
                },
                headers=self._headers(),
            )
            self.session_id = r.headers.get("mcp-session-id")
            return self._parse_sse(r.text)

    def list_tools(self) -> list:
        """Get available tools."""
        with httpx.Client(timeout=30) as client:
            r = client.post(
                self.endpoint,
                json={"jsonrpc": "2.0", "id": self._next_id(), "method": "tools/list", "params": {}},
                headers=self._headers(),
            )
            result = self._parse_sse(r.text)
            return result.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict, timeout: int = 120) -> dict:
        """Call an MCP tool."""
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
            result = self._parse_sse(r.text)
            # Extract tool result text
            content = result.get("result", {}).get("content", [])
            for c in content:
                if c.get("type") == "text":
                    try:
                        return json.loads(c["text"])
                    except json.JSONDecodeError:
                        return {"text": c["text"]}
            return result


def main():
    api_key = sys.argv[1] if len(sys.argv) > 1 else input("API Key: ")
    client = SoundsideClient(api_key)

    # Connect
    print("Connecting to Soundside MCP...")
    client.connect()
    print(f"✅ Connected (session: {client.session_id[:16]}...)")

    # List tools
    tools = client.list_tools()
    print(f"\n📋 Available tools ({len(tools)}):")
    for t in tools:
        print(f"  • {t['name']}")

    # Generate an image
    print("\n🎨 Generating image...")
    t0 = time.time()
    result = client.call_tool("create_image", {
        "prompt": "A vibrant sunset over a calm ocean, photorealistic",
        "provider": "vertex",
    })
    elapsed = time.time() - t0
    print(f"  Resource ID: {result.get('resource_id', 'N/A')}")
    print(f"  Time: {elapsed:.1f}s")

    # Check the resource
    if result.get("resource_id"):
        print("\n📦 Checking resource...")
        info = client.call_tool("lib_list", {
            "entity_type": "resources",
            "resource_id": result["resource_id"],
        })
        print(f"  State: {info.get('state', 'N/A')}")
        url = info.get("storage_url", "")
        if url:
            print(f"  URL: {url[:80]}...")

    # Generate text
    print("\n📝 Generating text...")
    text_result = client.call_tool("create_text", {
        "prompt": "Write a haiku about AI agents creating art",
        "provider": "vertex",
    })
    print(f"  {text_result.get('text', text_result)[:200]}")


if __name__ == "__main__":
    main()
