"""
Soundside x402 — Pay-Per-Call Example

Calls Soundside MCP tools using x402 crypto micropayments (USDC on Base).
No API key or Soundside account needed — just a funded wallet.

Requirements:
    uv run --with "x402[evm]" --with mcp python x402_example.py

Usage:
    WALLET_PRIVATE_KEY=0x... python x402_example.py
"""

import asyncio
import json
import os
import sys
import time

# Check dependencies before importing
try:
    import httpx
    from eth_account import Account
    from x402 import x402Client
    from x402.http import (
        PAYMENT_REQUIRED_HEADER,
        X_PAYMENT_HEADER,
        decode_payment_required_header,
        encode_payment_signature_header,
    )
    from x402.mechanisms.evm.exact import register_exact_evm_client
    from x402.mechanisms.evm.signers import EthAccountSigner
except ImportError as e:
    print(f"Missing dependency: {e}")
    print('Install with: uv run --with "x402[evm]" python x402_example.py')
    sys.exit(1)

ENDPOINT = "https://mcp.soundside.ai/mcp"
NETWORK  = "eip155:8453"  # Base mainnet


class SoundsideX402Client:
    """
    Minimal x402-aware MCP client.

    Calls Soundside tools directly over HTTP/SSE (same pattern as
    soundside_client.py) and transparently handles 402 Payment Required
    responses by signing a USDC payment and retrying the request.
    """

    def __init__(self, endpoint: str, payment_client: x402Client):
        self.endpoint = endpoint
        self.payment_client = payment_client
        self.session_id: str | None = None
        self._req_id = 0

    def _next_id(self) -> str:
        self._req_id += 1
        return str(self._req_id)

    def _headers(self, extra: dict | None = None) -> dict:
        h = {
            "Content-Type": "application/json",
            "Accept":       "application/json, text/event-stream",
        }
        if self.session_id:
            h["mcp-session-id"] = self.session_id
        if extra:
            h.update(extra)
        return h

    def _parse_sse(self, text: str) -> dict:
        """Find the JSON-RPC result frame (has 'id') among SSE notification frames."""
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

    def connect(self) -> None:
        with httpx.Client(timeout=30) as c:
            r = c.post(self.endpoint, json={
                "jsonrpc": "2.0", "id": self._next_id(), "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                           "clientInfo": {"name": "x402-example", "version": "1.0"}},
            }, headers=self._headers())
            self.session_id = r.headers.get("mcp-session-id")

    async def call_tool(self, tool: str, args: dict, timeout: int = 60) -> dict:
        """
        Call an MCP tool, automatically paying any 402 challenge.

        Returns the parsed tool result dict.
        """
        payload = {
            "jsonrpc": "2.0", "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": tool, "arguments": args},
        }

        # First attempt (unauthenticated — server will 402 if no API key)
        with httpx.Client(timeout=timeout) as c:
            r = c.post(self.endpoint, json=payload, headers=self._headers())

        if r.status_code == 402:
            # httpx lowercases headers; check both cased and lowercase versions
            pr_header = (
                r.headers.get(PAYMENT_REQUIRED_HEADER)
                or r.headers.get(PAYMENT_REQUIRED_HEADER.lower())
            )
            if pr_header:
                payment_required = decode_payment_required_header(pr_header)
            else:
                pr_body = r.json()
                from x402.schemas import PaymentRequired
                payment_required = PaymentRequired(**pr_body)

            print(f"  💳 Payment required — signing USDC on Base...")
            payment_payload = await self.payment_client.create_payment_payload(payment_required)
            payment_header  = encode_payment_signature_header(payment_payload)

            # Retry with signed payment
            with httpx.Client(timeout=timeout) as c:
                r = c.post(
                    self.endpoint, json=payload,
                    headers=self._headers({X_PAYMENT_HEADER: payment_header}),
                )

        if r.status_code not in (200, 201):
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")

        rpc = self._parse_sse(r.text)
        if "error" in rpc:
            raise RuntimeError(f"MCP error: {rpc['error']}")

        result = rpc.get("result", {})
        if result.get("isError"):
            for ct in result.get("content", []):
                if ct.get("type") == "text":
                    raise RuntimeError(f"Tool error ({tool}): {ct['text']}")
            raise RuntimeError(f"Tool error ({tool}): unknown error")

        for content in result.get("content", []):
            if content.get("type") == "text":
                try:
                    return json.loads(content["text"])
                except json.JSONDecodeError:
                    return {"text": content["text"]}
        return rpc


async def main():
    private_key = os.environ.get("WALLET_PRIVATE_KEY")
    if not private_key:
        print("Set WALLET_PRIVATE_KEY environment variable (with 0x prefix)")
        sys.exit(1)

    # Set up wallet
    account = Account.from_key(private_key)
    signer  = EthAccountSigner(account)
    print(f"🔑 Wallet: {account.address}")

    # Payment client (async x402)
    payment_client = x402Client()
    register_exact_evm_client(payment_client, signer, networks=NETWORK)

    # Connect to Soundside
    client = SoundsideX402Client(ENDPOINT, payment_client)
    client.connect()
    print("✅ Connected to Soundside MCP (x402 mode)\n")

    # --- Example 1: Generate text ($0.01 USDC) ---
    t0 = time.time()
    print("📝 Generating text (vertex, ~$0.01 USDC)...")
    text_result = await client.call_tool("create_text", {
        "prompt": "Write a haiku about autonomous AI agents.",
        "provider": "vertex",
    })
    text_out = text_result.get("message") or text_result.get("text", str(text_result)[:200])
    print(f"  {text_out}")
    print(f"  ⏱ {time.time()-t0:.1f}s\n")

    # --- Example 2: Generate image ($0.04 USDC) ---
    # Re-connect to get a fresh session (MCP sessions can expire between calls)
    client.connect()

    t0 = time.time()
    print("🎨 Generating image (minimax, ~$0.04 USDC)...")
    img_result = await client.call_tool("create_image", {
        "provider": "minimax",
        "prompt": "A fox in a cyberpunk city, neon lights reflecting in rain puddles",
    }, timeout=120)
    print(f"  ✅ Resource ID: {img_result.get('resource_id', 'N/A')}")
    if img_result.get("storage_url"):
        print(f"  📥 URL: {img_result['storage_url'][:80]}...")
    if img_result.get("wallet_link"):
        print(f"  🔗 Browser access: {img_result['wallet_link'][:60]}...")
    print(f"  ⏱ {time.time()-t0:.1f}s\n")

    print("💰 Done! USDC payments settled on Base via Coinbase facilitator.")
    print("   Pricing: https://mcp.soundside.ai/api/x402/status")


if __name__ == "__main__":
    asyncio.run(main())
