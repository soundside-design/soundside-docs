"""Quote and purchase a Recast run without regenerating on a transport retry.

Install: pip install httpx
Set SOUNDSIDE_API_KEY, then use --help for the quote, purchase and status commands.
Quotation performs paid source analysis. Purchase spends up to the saved run quote.
Keep the saved JSON private: it contains the source, brief and purchase token.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from soundside_client import SoundsideClient


def _checked(result: dict) -> dict:
    if result.get("success") is False:
        code = result.get("error_code", "TOOL_ERROR")
        parent = f" (existing job: {result['resource_id']})" if result.get("resource_id") else ""
        raise RuntimeError(f"{code}: {result.get('error', 'Tool call failed')}{parent}")
    return result


def request_quote(client: SoundsideClient, creative: dict, cap: int) -> dict:
    """Return exact request settings and the signed quote; never start generation."""
    result = _checked(client.call_tool("remix_video", {
        **creative, "rights_attested": True, "estimate_only": True,
        "budget_cap_credits": cap,
    }, timeout=600))
    metadata = result.get("metadata", {})
    total = metadata.get("quote", {}).get("total_credits")
    if type(total) is not int or total < 0 or not metadata.get("quote_token"):
        raise ValueError("The server did not return a purchasable quote; do not start a run.")
    if total > cap:
        raise ValueError(f"Quote is {total} credits, above the accepted cap of {cap}.")
    if type(metadata.get("quote_expires_at")) is not int:
        raise ValueError("The server did not return a quote expiry; do not start a run.")
    return {"version": 1, "arguments": creative, "metadata": metadata}


def purchase_quote(client: SoundsideClient, saved: dict, cap: int | None = None) -> dict:
    """Buy the saved plan. Repeating this call with the same file reuses its parent."""
    metadata = saved["metadata"]
    total = metadata["quote"]["total_credits"]
    if type(total) is not int or total < 0 or not metadata.get("quote_token"):
        raise ValueError("Saved quote is missing its price or purchase token.")
    if metadata.get("quote_expires_at", 0) <= time.time():
        raise ValueError("Quote expired. Use status for an existing job, or request a new quote.")
    accepted = total if cap is None else min(total, cap)
    if accepted < total:
        raise ValueError(f"Quote is {total} credits, above the accepted cap of {accepted}.")
    return _checked(client.call_tool("remix_video", {
        **saved["arguments"], "rights_attested": True, "estimate_only": False,
        "quote_token": metadata["quote_token"], "budget_cap_credits": accepted,
    }, timeout=180))


def resource_status(client: SoundsideClient, resource_id: str) -> dict:
    """Recover a parent or output on demand; lib_list is free."""
    return _checked(client.call_tool("lib_list", {
        "entity_type": "resources", "resource_ids": [resource_id],
    }))


def main() -> None:
    from soundside_client import SoundsideClient

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    quote = commands.add_parser("quote", help="Analyze an owned source and save its paid quote")
    quote.add_argument("--source-id", required=True, help="Completed owned video resource UUID")
    quote.add_argument("--brief", required=True)
    quote.add_argument("--mode", choices=("recast", "reskin"), default="recast")
    quote.add_argument("--profile", choices=("draft", "standard", "premium"), default="standard")
    quote.add_argument("--start", type=float)
    quote.add_argument("--end", type=float)
    quote.add_argument("--reference-id", action="append", default=[])
    quote.add_argument("--cap", type=int, required=True, help="Maximum run price in credits ($0.01 each)")
    quote.add_argument("--output", type=Path, required=True, help="New private quote JSON file")
    quote.add_argument("--rights-attested", action="store_true", required=True)
    purchase = commands.add_parser("purchase", help="Purchase or retry a saved, unexpired quote")
    purchase.add_argument("quote_file", type=Path)
    purchase.add_argument("--cap", type=int, help="Optional stricter cap; never raises the quoted ceiling")
    purchase.add_argument("--rights-attested", action="store_true", required=True)
    status = commands.add_parser("status", help="Read a job or output without starting a new run")
    status.add_argument("resource_id")
    args = parser.parse_args()
    api_key = os.environ.get("SOUNDSIDE_API_KEY")
    if not api_key:
        parser.error("Set SOUNDSIDE_API_KEY.")
    if args.command == "quote" and args.output.exists():
        parser.error("Choose a new output file so an existing purchase token is preserved.")
    client = SoundsideClient(api_key)
    client.connect()
    if args.command == "quote":
        creative = {
            "source_resource_id": args.source_id, "brief": args.brief,
            "mode": args.mode, "recipe": "source_edit", "quality_profile": args.profile,
            "reference_images": args.reference_id,
        }
        if args.start is not None:
            creative["range_start_sec"] = args.start
        if args.end is not None:
            creative["range_end_sec"] = args.end
        saved = request_quote(client, creative, args.cap)
        with os.fdopen(os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as file:
            json.dump(saved, file, indent=2)
            file.write("\n")
        # Do not print the signed purchase token.
        print(json.dumps({"quote_file": str(args.output), "quote": saved["metadata"]["quote"],
                          "quote_expires_at": saved["metadata"]["quote_expires_at"]}, indent=2))
    elif args.command == "purchase":
        result = purchase_quote(client, json.loads(args.quote_file.read_text()), args.cap)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(resource_status(client, args.resource_id), indent=2))


if __name__ == "__main__":
    main()
