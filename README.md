# Soundside — Developer Documentation

**AI Media Production Platform for Agents**

Soundside exposes 19 MCP tools for generating, editing, composing, extracting, and analyzing media — images, video, audio, music, text, and business artifacts — plus LoRA adapter fine-tuning and server-side video composition. Connect any MCP client. Pay with an API key (credits) or crypto (x402 USDC on Base, no account needed).

> **Currency 2026-08 (2026-08-23)**
> - **Removed:** Luma (entirely) and Runway image/video generation. Runway is now audio-only — TTS and sound effects via `create_audio`.
> - **Added:** Lyria 3 music generation (`create_music`), Grok TTS (`create_audio`), Grok per-second × resolution video pricing, Alibaba Wan 2.7 video models (international default), MiniMax H3 video adapter.
> - Provider and pricing data below matches the live x402 catalog: `GET https://mcp.soundside.ai/api/x402/status`.

## Quick Start

```bash
# MCP endpoint
https://mcp.soundside.ai/mcp

# Auth: API key or x402 crypto payment
Authorization: Bearer <your-api-key>
```

```json
POST https://mcp.soundside.ai/mcp
{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}
```

## Tools (19)

### Generation

| Tool | What It Does | Providers |
|------|-------------|-----------|
| `create_image` | Text-to-image, character references | Alibaba (Wan), Grok, MiniMax, Vertex AI |
| `create_video` | Text-to-video, image-to-video, video extension | Alibaba (Wan 2.7), Grok, MiniMax (Hailuo/H3), Vertex AI (Veo 3.1) |
| `create_audio` | TTS, sound effects, voice cloning, voice design | Grok, MiniMax, Runway (audio-only), Vertex AI |
| `create_music` | Music from lyrics and style prompts | MiniMax, Lyria 3 |
| `create_text` | LLM chat completions, structured output | Grok, MiniMax, Qwen, Vertex AI (Gemini) |
| `create_artifact` | Charts, presentations, documents, diagrams; bundle mode for multi-artifact packages | plotly, pptx, docx, weasyprint, mermaid, gamma, soundside.ai |

### Composition

| Tool | What It Does |
|------|-------------|
| `compose_video` | Server-side pipeline: enrich plan, generate assets in parallel, assemble with transitions, audio ducking, and overlays |

### Editing

| Tool | What It Does |
|------|-------------|
| `edit_video` | Core video transforms: trim, concat, crossfade, speed, loop, color grade, burn subtitles, custom FFmpeg |
| `edit_audio` | Mix, replace, or pad audio on existing media |
| `compose_media` | Add text, overlay media, or build split-screen composites |
| `apply_effect` | Ken Burns, speed ramp, film grain, vignette |
| `extract_media` | Extract frames, frame sets, or audio tracks |

### Analysis

| Tool | What It Does | Providers |
|------|-------------|-----------|
| `analyze_media` | Technical metadata, vision QA, transcription, segment detection, EDL export | Anthropic, Grok, OpenAI, Qwen, Vertex (+ soundside.ai ffprobe) |

### Adapters (LoRA)

| Tool | What It Does | Backends |
|------|-------------|----------|
| `train_adapter` | Train a LoRA adapter from library media | DashScope (Wan), Modal (Hunyuan/LTX) |
| `list_adapters` | List your LoRA adapters |  |
| `manage_adapter` | Inspect, deploy, undeploy, delete, or select checkpoint |  |

### Library Management

| Tool | What It Does |
|------|-------------|
| `lib_list` | Browse projects, collections, resources, lineage, brand kits; query credit balance |
| `lib_manage` | CRUD for projects, collections, resources, brand kits |
| `lib_share` | Share projects with other users by email |

## Pricing

Soundside uses a credit system: **100 credits = $1 USD**.

- **AI provider pass-through** (generation tools) is billed at the provider's wholesale rate, rounded up to the nearest cent — no markup.
- **Platform tools** (editing engine, library) are fixed-price: $0.01/call; vision QA is $0.03.
- Every call is quoted before it runs. The estimate is a **ceiling** — the actual charge is never more than the quote — and each tool call is settled exactly once.

**Live pricing is always available at:**
```
GET https://mcp.soundside.ai/api/x402/status
```

This returns machine-readable per-tool, per-provider USDC prices. Prices are DB-driven and may change — **always check the endpoint rather than hardcoding**. For variable-priced tools the published amount is a ceiling quote (worst case), not the typical settled price — rows carry a `price_note` where this matters.

## x402: Pay-Per-Call with Crypto

No API key needed. Pay with USDC on Base (L2) per tool call via EIP-3009 `transferWithAuthorization` (off-chain signing, facilitator pays gas).

```
Network: eip155:8453 (Base mainnet)
Token: USDC
Facilitator: Coinbase CDP
```

See [x402 Guide](./guides/x402.md) for full setup.

## Guides

- **[Getting Started](./guides/getting-started.md)** — First MCP connection in 5 minutes
- **[x402 Pay-Per-Call](./guides/x402.md)** — Crypto payments, no account needed
- **[Tool Reference](./guides/tools.md)** — Detailed docs for all 19 tools

## Examples

- **[Python — API Key](./examples/python/soundside_client.py)** — Connect and generate with httpx
- **[Python — x402](./examples/python/x402_example.py)** — Pay-per-call with USDC
- **[TypeScript — API Key](./examples/typescript/soundside-client.ts)** — Node.js MCP client
- **[OpenClaw Skill](./examples/openclaw/SKILL.md)** — One-line config for OpenClaw agents

## Links

- **Website**: [soundside.ai](https://soundside.ai)
- **MCP Endpoint**: `https://mcp.soundside.ai/mcp`
- **Live Pricing**: `https://mcp.soundside.ai/api/x402/status`
- **GitHub**: [github.com/soundside-design/soundside-docs](https://github.com/soundside-design/soundside-docs)
