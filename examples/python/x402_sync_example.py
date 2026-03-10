"""
Soundside x402 — Sync Pay-Per-Call Example

The simplest working pattern for calling Soundside tools via x402 USDC
micropayments. Sync-only, no asyncio required — suitable for use in
agents, scripts, and notebooks.

Requirements:
    pip install "git+https://github.com/coinbase/x402.git#subdirectory=python/x402&egg=x402[evm]" requests eth-account
    # Python >= 3.10 required

Usage:
    WALLET_PRIVATE_KEY=0x<your_private_key> python x402_sync_example.py

Pricing:
    curl https://mcp.soundside.ai/api/x402/status
"""

import json
import os
import sys

try:
    import requests
    from eth_account import Account
    from x402 import x402ClientSync
    from x402.http import encode_payment_signature_header, X_PAYMENT_HEADER
    from x402.mechanisms.evm.exact import register_exact_evm_client
    from x402.mechanisms.evm.signers import EthAccountSigner
    from x402.schemas import PaymentRequired
except ImportError as e:
    print(f"Missing dependency: {e}")
    print(
        'Install with:\n'
        '  pip install "git+https://github.com/coinbase/x402.git'
        '#subdirectory=python/x402&egg=x402[evm]" requests eth-account'
    )
    sys.exit(1)

ENDPOINT = "https://mcp.soundside.ai/mcp"


class SoundsideX402ClientSync:
    """
    Minimal sync x402-aware MCP client for Soundside.

    Handles the full flow: initialize session → call tool → pay 402 → retry.
    Each call_tool() invocation uses a fresh MCP session (stateless pattern).
    """

    def __init__(self, wallet_private_key: str) -> None:
        account = Account.from_key(wallet_private_key)
        self.account = account
        self.wallet_address = account.address

        self._payment_client = x402ClientSync()
        register_exact_evm_client(self._payment_client, EthAccountSigner(account))

    def call_tool(self, tool: str, args: dict, timeout: int = 120) -> dict:
        """
        Call a Soundside MCP tool with automatic x402 payment.

        Args:
            tool:    Tool name (e.g. "create_image", "create_text")
            args:    Tool arguments dict
            timeout: Request timeout in seconds (use 120+ for video/image gen)

        Returns:
            Parsed tool result as a dict.

        Raises:
            RuntimeError: On HTTP errors or tool-level errors.
        """
        session = requests.Session()

        # Step 1: Initialize MCP session
        init_r = session.post(
            ENDPOINT,
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "x402-sync-example", "version": "1.0"},
                },
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30,
        )
        init_r.raise_for_status()
        session_id = init_r.headers.get("mcp-session-id", "")

        base_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id,
            # Required: tells the server which wallet/project to attribute resources to
            "x402-wallet": self.wallet_address,
        }

        payload = {
            "jsonrpc": "2.0",
            "id": "2",
            "method": "tools/call",
            "params": {"name": tool, "arguments": args},
        }

        # Step 2: First attempt (no payment header — server will 402)
        r = session.post(ENDPOINT, json=payload, headers=base_headers, timeout=timeout)

        if r.status_code == 402:
            # Step 3: Parse the 402 body to get payment requirements
            pr = PaymentRequired.model_validate(r.json())

            # Step 4: Sign an EIP-3009 transferWithAuthorization (off-chain, no gas)
            payment_payload = self._payment_client.create_payment_payload(pr)
            payment_header = encode_payment_signature_header(payment_payload)

            # Step 5: Retry with signed payment header
            r = session.post(
                ENDPOINT,
                json=payload,
                headers={**base_headers, X_PAYMENT_HEADER: payment_header},
                timeout=timeout,
            )

        if r.status_code not in (200, 201):
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")

        # Step 6: Parse SSE response (server sends event: message / data: <json>)
        result = self._parse_sse(r.text)

        if result.get("isError"):
            content = result.get("content", [{}])
            msg = content[0].get("text", "unknown tool error") if content else "unknown tool error"
            raise RuntimeError(f"Tool error ({tool}): {msg}")

        # Structured content has the full typed result
        if "structuredContent" in result:
            return result["structuredContent"]

        # Fallback: parse text content
        for ct in result.get("content", []):
            if ct.get("type") == "text":
                try:
                    return json.loads(ct["text"])
                except json.JSONDecodeError:
                    return {"text": ct["text"]}

        return result

    @staticmethod
    def _parse_sse(text: str) -> dict:
        """Extract the JSON-RPC result from an SSE response body."""
        for line in text.splitlines():
            if line.startswith("data:"):
                try:
                    obj = json.loads(line[5:].strip())
                    if "result" in obj:
                        return obj["result"]
                except json.JSONDecodeError:
                    pass
        # Fallback: try parsing full body as JSON
        try:
            return json.loads(text).get("result", {})
        except json.JSONDecodeError:
            return {}


def main() -> None:
    private_key = os.environ.get("WALLET_PRIVATE_KEY")
    if not private_key:
        print("Set WALLET_PRIVATE_KEY=0x<your_private_key>")
        sys.exit(1)

    client = SoundsideX402ClientSync(private_key)
    print(f"Wallet: {client.wallet_address}")
    print(f"Endpoint: {ENDPOINT}\n")

    # --- Example 1: Generate text (~$0.01 USDC) ---
    print("Generating text via Vertex AI ($0.01 USDC)...")
    result = client.call_tool("create_text", {
        "provider": "vertex",
        "prompt": "Write a haiku about USDC micropayments.",
    })
    print(f"  Text: {result.get('message') or result.get('text', result)}")
    print()

    # --- Example 2: Generate image (~$0.04 USDC) ---
    print("Generating image via MiniMax ($0.04 USDC)...")
    result = client.call_tool("create_image", {
        "provider": "minimax",
        "prompt": "A glowing fox in a neon-lit cyberpunk alley, cinematic",
    }, timeout=120)
    print(f"  Resource ID: {result.get('resource_id')}")
    if result.get("wallet_link"):
        print(f"  Browser link: {result['wallet_link']}")
    if result.get("x402_session_token"):
        print("  x402_session_token: present (use for /api/x402/resource polling)")
    print()

    # --- Example 3: Share generated project with a collaborator ---
    # After any successful x402 call, a project is automatically created
    # for your wallet. You can share it:
    print("Sharing x402 project with a collaborator...")
    share_result = client.call_tool("lib_share", {
        "operation": "share",
        "project_id": result.get("project_id", "<your-x402-project-id>"),
        "user_email": "collaborator@example.com",
        "permission_level": "view",
    })
    print(f"  Share result: {share_result.get('message')}")

    print("\nDone. Check https://mcp.soundside.ai/api/x402/status for current pricing.")


if __name__ == "__main__":
    main()
