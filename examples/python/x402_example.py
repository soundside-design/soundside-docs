"""
Soundside x402 Client — Pay-Per-Call Example

Demonstrates calling Soundside tools with x402 crypto payment.
No API key or Soundside account needed — just USDC on Base.

Requirements:
    pip install "x402[evm]" mcp

Usage:
    WALLET_PRIVATE_KEY=0x... python x402_example.py
"""

import asyncio
import json
import os
import sys

# Check dependencies before importing
try:
    from eth_account import Account
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    from x402 import x402ClientAsync
    from x402.mechanisms.evm.exact import register_exact_evm_client
    from x402.mechanisms.evm.signers import LocalAccountEVMSigner
    from x402.mcp import x402MCPClient
except ImportError as e:
    print(f"Missing dependency: {e}")
    print('Install with: pip install "x402[evm]" mcp')
    sys.exit(1)

ENDPOINT = "https://mcp.soundside.ai/mcp-x402"
NETWORK  = "eip155:8453"  # Base mainnet


async def main():
    private_key = os.environ.get("WALLET_PRIVATE_KEY")
    if not private_key:
        print("Set WALLET_PRIVATE_KEY environment variable (with 0x prefix)")
        sys.exit(1)

    # Set up wallet signer
    account = Account.from_key(private_key)
    signer  = LocalAccountEVMSigner(account)
    print(f"🔑 Wallet: {account.address}")

    # Create x402 payment client
    payment_client = x402ClientAsync()
    register_exact_evm_client(payment_client, signer, networks=NETWORK)

    # Connect to Soundside via MCP
    async with streamablehttp_client(ENDPOINT) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to Soundside MCP (x402 mode)")

            # Wrap session with x402 auto-payment
            x402_session = x402MCPClient(session, payment_client, auto_payment=True)

            # --- Example 1: Generate text (~$0.01) ---
            print("\n📝 Generating text (auto-pays with USDC)...")
            result = await x402_session.call_tool(
                "create_text",
                {"prompt": "Write a haiku about autonomous AI agents."}
            )
            text = result.content[0].text
            try:
                data = json.loads(text)
                print(f"  {data.get('text', text[:200])}")
            except json.JSONDecodeError:
                print(f"  {text[:200]}")

            # --- Example 2: Generate image (~$0.04) ---
            print("\n🎨 Generating image (minimax, auto-pays)...")
            result = await x402_session.call_tool(
                "create_image",
                {
                    "provider": "minimax",
                    "prompt": "A fox in a cyberpunk city, neon lights reflecting in rain puddles",
                }
            )
            text = result.content[0].text
            try:
                data = json.loads(text)
                print(f"  ✅ Resource ID: {data.get('resource_id', 'N/A')}")
                if data.get("storage_url"):
                    print(f"  📥 URL: {data['storage_url'][:80]}...")
                if data.get("wallet_link"):
                    print(f"  🔗 Browser access: {data['wallet_link'][:60]}...")
            except json.JSONDecodeError:
                print(f"  {text[:200]}")

            print("\n💰 Done! Check your wallet for USDC charges on Base.")
            print("   Live pricing: https://mcp.soundside.ai/api/x402/status")


if __name__ == "__main__":
    asyncio.run(main())
