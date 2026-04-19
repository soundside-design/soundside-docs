# Soundside — Developer Documentation

**AI Media Production Platform for Agents**

Soundside exposes 19 MCP tools for generating, editing, composing, extracting, and analyzing media — images, video, audio, music, text, and business artifacts — plus LoRA adapter fine-tuning and server-side video composition. Connect any MCP client. Pay with an API key (credits) or crypto (x402 USDC on Base, no account needed).

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
| `create_image` | Text-to-image, character references | Alibaba (Wan), Grok, Luma, MiniMax, Runway, Vertex AI |
| `create_video` | Text-to-video, image-to-video, video extension | Alibaba (Wan), Grok, Luma, MiniMax, Runway, Vertex AI (Veo 3.1) |
| `create_audio` | TTS, sound effects, voice cloning, voice design | MiniMax, Runway, Vertex AI |
| `create_music` | Music from lyrics and style prompts | MiniMax |
| `create_text` | LLM chat completions, structured output | Grok, MiniMax, Vertex AI (Gemini) |
| `create_artifact` | Charts, presentations, documents, diagrams; bundle mode for multi-artifact packages | plotly, pptx, docx, weasyprint, mermaid, gamma |

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

Soundside aims to break even on provider pass-through costs with a small margin (~10%). The editing engine and library are priced at $0.01/call; vision QA is $0.03.

**Live pricing is always available at:**
```
GET https://mcp.soundside.ai/api/x402/status
```

This returns machine-readable per-tool, per-provider USDC prices. Prices are DB-driven and may change — **always check the endpoint rather than hardcoding**.

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
