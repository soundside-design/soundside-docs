# Soundside — Developer Documentation

**AI Media Production Platform for Agents**

Soundside exposes 15 MCP tools for generating, editing, composing, extracting, and analyzing media — images, video, audio, music, text, and business artifacts. Connect any MCP client. Pay with an API key (credits) or crypto (x402 USDC on Base, no account needed).

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

## Tools (15)

### Generation

| Tool | What It Does | Providers |
|------|-------------|-----------|
| `create_image` | Text-to-image, character references | Vertex AI, Grok, Runway, MiniMax, Luma |
| `create_video` | Text-to-video, image-to-video, video extension | Vertex AI (Veo 3.1), Runway, MiniMax, Luma, Grok |
| `create_audio` | TTS, deprecated transcribe compatibility shim, voice cloning, sound effects, voice design | MiniMax, Vertex AI, Runway, Creative Freedom |
| `create_music` | Music from lyrics and style prompts | MiniMax, Creative Freedom |
| `create_text` | LLM chat completions, structured output | Vertex AI (Gemini), Grok, MiniMax |
| `create_artifact` | Charts, presentations, documents, diagrams; bundle mode for multi-artifact packages from a single brief | Plotly, PPTX, WeasyPrint, Mermaid, Gamma |

### Editing & Analysis

| Tool | What It Does |
|------|-------------|
| `edit_video` | Core video transforms: trim, concat, crossfade, speed, loop, color grade, burn subtitles, custom FFmpeg |
| `edit_audio` | Mix, replace, or pad audio on existing media |
| `compose_media` | Add text, overlay media, or build split-screen composites |
| `apply_effect` | Ken Burns, speed ramp, film grain, vignette |
| `extract_media` | Extract frames, frame sets, or audio tracks |
| `analyze_media` | Technical analysis, AI vision QA, transcription, segment detection, and EDL export |

### Library Management

| Tool | What It Does |
|------|-------------|
| `lib_list` | Browse projects, collections, resources, lineage, brand kits; query credit balance |
| `lib_manage` | CRUD for projects, collections, resources, brand kits |
| `lib_share` | Share projects with other users by email |

## Pricing Philosophy

Soundside aims to break even on provider pass-through costs with a small margin (~10%). The real value is in the editing engine, library management, and self-hosted models — those are priced at $0.01/call ($0.03 for analyze_media vision_qa).

**Live pricing is always available at:**
```
GET https://mcp.soundside.ai/api/x402/status
```

This returns machine-readable per-tool, per-provider USDC prices. Prices are DB-driven and may change — always check the endpoint rather than hardcoding.

## x402: Pay-Per-Call with Crypto

No API key needed. Pay with USDC on Base (L2) per tool call.

```
Network: eip155:8453 (Base mainnet)
Token: USDC
Facilitator: Coinbase CDP
```

See [x402 Guide](./guides/x402.md) for full setup.

## Guides

- **[Getting Started](./guides/getting-started.md)** — First MCP connection in 5 minutes
- **[x402 Pay-Per-Call](./guides/x402.md)** — Crypto payments, no account needed
- **[Tool Reference](./guides/tools.md)** — Detailed docs for all 15 tools

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
