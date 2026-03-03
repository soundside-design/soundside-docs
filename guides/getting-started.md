# Getting Started with Soundside

Connect to Soundside's MCP endpoint and make your first tool call in 5 minutes.

## 1. Get Access

**Option A: API Key** — Sign up at [soundside.ai](https://soundside.ai), go to `/developer/console`, and generate a key. Keys look like: `mcp_abc123...`

**Option B: x402 (no account)** — Just have USDC on Base. See the [x402 Guide](./x402.md).

## 2. Connect via MCP

Soundside speaks [MCP (Model Context Protocol)](https://modelcontextprotocol.io). Any MCP-compatible client can connect.

**Endpoint:** `https://mcp.soundside.ai/mcp`

### Initialize a Session

```
POST https://mcp.soundside.ai/mcp
Authorization: Bearer mcp_your_key_here
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc":"2.0","id":"1","method":"initialize","params":{
  "protocolVersion":"2024-11-05",
  "capabilities":{},
  "clientInfo":{"name":"my-agent","version":"1.0"}
}}
```

The response includes a `mcp-session-id` header — include it in all subsequent requests.

## 3. List Available Tools

```json
{"jsonrpc":"2.0","id":"2","method":"tools/list","params":{}}
```

Returns all 12 tools with their full input schemas. Always read schemas from this response — don't hardcode argument assumptions.

## 4. Call a Tool

### Generate an Image

```json
{"jsonrpc":"2.0","id":"3","method":"tools/call","params":{
  "name":"create_image",
  "arguments":{
    "prompt":"A red fox sitting on a tree stump at golden hour, photorealistic",
    "provider":"vertex"
  }
}}
```

Returns a `resource_id` and `storage_url` (signed GCS URL to download).

### Generate a Video (Async)

```json
{"jsonrpc":"2.0","id":"4","method":"tools/call","params":{
  "name":"create_video",
  "arguments":{
    "prompt":"A fox exploring a forest stream, cinematic",
    "provider":"minimax"
  }
}}
```

Returns a `resource_id` immediately. The video generates in the background — Soundside pushes an MCP `notifications/resources/updated` when complete. For on-demand checks, use `lib_list`:

```json
{"jsonrpc":"2.0","id":"5","method":"tools/call","params":{
  "name":"lib_list",
  "arguments":{
    "entity_type":"resources",
    "resource_id":"<your-resource-id>"
  }
}}
```

### Edit Media

```json
{"jsonrpc":"2.0","id":"6","method":"tools/call","params":{
  "name":"edit_video",
  "arguments":{
    "resource_id":"<resource-id>",
    "action":"add_text",
    "text":"Hello World",
    "position":"bottom_left",
    "fontsize":32,
    "fontcolor":"white"
  }
}}
```

### Analyze Media

```json
{"jsonrpc":"2.0","id":"7","method":"tools/call","params":{
  "name":"analyze_media",
  "arguments":{
    "resource_id":"<resource-id>",
    "analysis_type":"vision_qa",
    "reference_prompt":"A fox sitting on a tree stump at golden hour",
    "criteria":["style_consistency","prompt_match","artifacts"]
  }
}}
```

Returns a score (0-1), pass/fail, and detailed issues/suggestions.

## 5. Provider Selection

Each generation tool supports multiple AI providers. If you don't specify one, Soundside picks a default.

| Use Case | Recommended Provider | Why |
|----------|---------------------|-----|
| Highest quality video | `vertex` (Veo 3.1) | Best motion, longest clips |
| Best value video | `minimax` (Hailuo) | Good quality, lowest cost |
| Fast image generation | `vertex` or `grok` | Sync, sub-10s |
| Cheapest images | `luma` or `minimax` | $0.02-0.04 |
| Text-to-speech | `minimax` | Multiple voices, voice cloning |
| Transcription (STT) | `vertex` | EN-US, word-level timestamps |
| Music generation | `minimax` | Only provider, lyrics + style prompt |
| LLM text | `vertex` (Gemini) | General purpose |

## 6. Sync vs Async

| Behavior | Tools |
|----------|-------|
| **Sync** — result in response | `create_image` (most providers), `create_text`, `create_audio` (TTS), `create_artifact`, `edit_video`, `analyze_media`, `lib_*` |
| **Async** — returns `resource_id`, completes later | `create_video` (all providers), `create_music`, `create_image` (luma, runway), `create_audio` (minimax TTS) |

For async tools, listen for MCP `notifications/resources/updated` or poll with `lib_list`.

## 7. Library Organization

Your media is organized in a library:
- **Projects** — top-level containers
- **Collections** — groups within projects
- **Resources** — individual media files

Pass `project_id` and/or `collection_id` when generating to auto-organize. Use `lib_manage` to create/update/delete. Use `lib_share` to share projects by email.

## Next Steps

- [x402 Guide](./x402.md) — Pay per call with crypto, no account needed
- [Tool Reference](./tools.md) — Detailed docs for every tool and parameter
- [Examples](../examples/) — Working Python, TypeScript, and OpenClaw code
