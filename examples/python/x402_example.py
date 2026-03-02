"""
Soundside x402 Client — Pay-Per-Call Example

Demonstrates calling Soundside tools with x402 crypto payment (no API key).
Requires: pip install x402 httpx
"""

import httpx
import json
import os
import sys


def main():
    """
    x402 flow:
    1. Send tool call → get 402 with payment requirements
    2. Pay via facilitator with your wallet
    3. Re-send with payment receipt
    """
    private_key = os.environ.get("WALLET_PRIVATE_KEY")
    if not private_key:
        print("Set WALLET_PRIVATE_KEY environment variable (with 0x prefix)")
        sys.exit(1)

    endpoint = "https://mcp.soundside.ai/mcp"

    # Step 1: Check what's available
    print("📋 Checking x402 status...")
    status = httpx.get("https://mcp.soundside.ai/api/x402/status").json()
    print(f"  Network: {status['network']}")
    print(f"  Tools: {len(status['enabled_tools'])}")
    for t in status["enabled_tools"][:5]:
        sync = "⚡" if t.get("sync", True) else "⏳"
        print(f"    {sync} {t['tool']:20} ${t['price_usdc']}")
    if len(status["enabled_tools"]) > 5:
        print(f"    ... and {len(status['enabled_tools']) - 5} more")

    # Step 2: Use x402 client for automatic payment handling
    try:
        from x402.client import x402_client

        client = x402_client(
            private_key=private_key,
            network="eip155:8453",
        )

        # Initialize MCP session
        init_resp = client.post(endpoint, json={
            "jsonrpc": "2.0", "id": "1", "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "x402-example", "version": "1.0"},
            },
        })
        session_id = init_resp.headers.get("mcp-session-id", "")

        # Call create_image (will automatically handle 402 payment)
        print("\n🎨 Generating image (paying with USDC)...")
        resp = client.post(
            endpoint,
            json={
                "jsonrpc": "2.0", "id": "2", "method": "tools/call",
                "params": {
                    "name": "create_image",
                    "arguments": {
                        "prompt": "A fox in a cyberpunk city, neon lights, rain",
                        "provider": "vertex",
                    },
                },
            },
            headers={"mcp-session-id": session_id} if session_id else {},
        )

        # Parse result
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                result = json.loads(line[5:])
                content = result.get("result", {}).get("content", [])
                for c in content:
                    if c.get("text"):
                        data = json.loads(c["text"])
                        print(f"  ✅ Resource ID: {data.get('resource_id', 'N/A')}")
                        print(f"  💰 Paid with x402 (USDC on Base)")
                break

    except ImportError:
        print("\n⚠️  x402 SDK not installed. Install with: pip install x402")
        print("  Falling back to manual flow explanation...")
        print("\n  Manual x402 flow:")
        print("  1. POST to /mcp with tools/call → get HTTP 402")
        print("  2. Parse payment requirements from 402 response")
        print("  3. Sign and send payment to facilitator")
        print("  4. Re-POST with X-PAYMENT header containing receipt")


if __name__ == "__main__":
    main()
