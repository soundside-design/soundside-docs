# Soundside.ai — Developer Documentation

**The AI Media Production Platform for Agents**

Soundside provides 12 MCP tools for generating, editing, and analyzing media — images, video, audio, music, text, and artifacts. Pay per call with crypto (x402) or API key.

## Quick Start

```bash
# MCP endpoint
https://mcp.soundside.ai/mcp

# Authentication: API key (header) or x402 (crypto payment)
Authorization: Bearer <your-api-key>
```

## Tools

| Tool | What It Does | Providers |
|------|-------------|-----------|
| `create_image` | Generate images from text prompts | Luma, MiniMax, Vertex AI, Grok, Runway |
| `create_video` | Generate video from text/image | Luma, MiniMax, Runway, Vertex AI, Grok |
| `create_audio` | Text-to-speech, sound effects | MiniMax, Vertex AI |
| `create_music` | Generate music from lyrics/prompt | MiniMax |
| `create_text` | Generate text content | MiniMax, Vertex AI, Grok |
| `create_artifact` | Charts, presentations, documents | Plotly, PPTX, WeasyPrint |
| `create_artifact_bundle` | Multi-artifact packages | Combined |
| `edit_video` | 20+ video editing actions | FFmpeg |
| `analyze_media` | Technical analysis, vision QA | FFmpeg, Vertex AI |
| `lib_list` | Browse your media library | — |
| `lib_manage` | Organize projects, collections | — |
| `lib_share` | Share resources via signed URLs | — |

## x402: Pay-Per-Call with Crypto

No API key needed. Pay with USDC on Base (L2) for each tool call.

```
Network: eip155:8453 (Base mainnet)
Token: USDC
Facilitator: Coinbase CDP
```

See [x402 Guide](./guides/x402.md) for full setup.

## Examples

- **[TypeScript](./examples/typescript/)** — Node.js client with x402 payment
- **[Python](./examples/python/)** — Python client with httpx
- **[OpenClaw](./examples/openclaw/)** — OpenClaw skill configuration

## Pricing

| Tool | Price (USDC) | Sync |
|------|-------------|------|
| create_text | $0.01 | ⚡ Yes |
| create_image | $0.10–0.20 | ⚡ Yes |
| create_audio | $0.05–0.10 | ⚡ Yes |
| create_music | $0.40 | ⏳ Async |
| create_video | $0.50–1.00 | ⏳ Async |
| create_artifact | $0.05 | ⚡ Yes |
| edit_video | $0.10 | ⚡ Yes |
| analyze_media | $0.05 | ⚡ Yes |

## Links

- **Website**: [soundside.ai](https://soundside.ai)
- **MCP Endpoint**: `https://mcp.soundside.ai/mcp`
- **x402 Status**: `https://mcp.soundside.ai/api/x402/status`
- **Discord**: Coming soon
- **API Key**: [Sign up](https://soundside.ai) → Settings → API Keys
