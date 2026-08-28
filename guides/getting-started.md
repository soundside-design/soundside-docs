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
  "protocolVersion":"2025-11-25",
  "capabilities":{},
  "clientInfo":{"name":"my-agent","version":"1.0"}
}}
```

The response includes a `mcp-session-id` header — include it in all subsequent requests.

> **Session lifetime:** Sessions expire after roughly 2 minutes of inactivity. If a subsequent request returns `400 Bad Request: No valid session ID provided`, re-initialize with a fresh `initialize` call to get a new session ID.

## 3. List Available Tools

```json
{"jsonrpc":"2.0","id":"2","method":"tools/list","params":{}}
```

Returns all available tools with their full input schemas. Always read schemas from this response — don't hardcode argument assumptions.

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

Returns a `resource_id`. The signed GCS asset URL arrives on the **item fetched via `lib_list`** — use `lib_list(entity_type="resources", resource_id=<id>)` and read `items[0].url`. Older backend versions used the field name `storage_url`; `url` is the canonical name today.

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
  "name":"compose_media",
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

Follow each live schema. `create_image`, `create_video`, `create_audio`, and `create_music` require an explicit provider; `create_text` defaults to Vertex, and `create_artifact` routes primarily by artifact type.

| Use Case | Recommended Provider | Why |
|----------|---------------------|-----|
| Highest quality video | `vertex` (Veo 3.1) | Best motion, longest clips |
| Open-weights video with tight controls | `alibaba` (Wan) | 13 operations incl. VACE, i2v, kf2v, animate |
| Best value video | `minimax` (Hailuo) | Good quality, lowest cost |
| Fast image generation | `vertex` or `grok` | Sync, sub-10s |
| Cheapest images | `minimax` ($0.04) / `alibaba` ($0.05) / `vertex` ($0.08) | |
| Text-to-speech | `minimax` or `grok` | MiniMax: multiple voices, voice cloning. Grok: 26 multilingual voices, sync |
| Transcription (STT) | `vertex` | EN-US, word-level timestamps |
| Music generation | `lyria` (Lyria 3) | Lyria is sync; Creative Freedom is authenticated-credit only and async |
| LLM text | `vertex` (Gemini) | General purpose |
| Vision QA over video | `vertex` (Gemini 2.5 Pro, default) or `qwen` | Also: `anthropic`, `grok`, `openai` |

## 6. Sync vs Async

| Behavior | Tools |
|----------|-------|
| **Sync** — final result in response | `create_image` (creative_freedom, grok, minimax, vertex), `create_text`, `create_audio` (grok, vertex), `create_music` (lyria), `create_artifact`, editing tools, all `analyze_media` modes, `list_adapters`, and library tools |
| **Pending** — returns a resource that completes later | `create_video` (all providers), `create_image` (alibaba), `create_music` (creative_freedom), `compose_video`, `create_audio` (minimax/runway and provider-dependent Creative Freedom modes), `train_adapter`, and `manage_adapter` deploy/undeploy operations |

For async tools, listen for MCP `notifications/resources/updated` or recover state with `lib_list`. Public task/hold/resume guarantees are not part of the current contract.

## 7. Async recovery

Keep the returned `resource_id`. Completion/failure is pushed while connected; after a reconnect or session loss, call `lib_list(entity_type="resources", resource_ids=[...])` to recover current state.

## 8. Tool Result Format

Tool results use MCP's `structuredContent` (preferred) plus a text content block. Async tools that declare MCP `taskSupport` additionally emit a `resource_link` block so task-aware clients can render a download/preview inline.

```json
{
  "structuredContent": {
    "resource_id": "abc-123",
    "status": "pending",
    "provider": "minimax",
    "wallet_link": "https://www.soundside.ai/auth/wallet-link?token=...",
    "x402_session_token": "eyJ..."
  },
  "content": [
    {"type": "text", "text": "Video generation started."},
    {"type": "resource_link", "uri": "soundside://resources/abc-123", "name": "generated-video.mp4", "mimeType": "video/mp4"}
  ]
}
```

- The canonical lifecycle field is **`status`** (`pending` / `completed` / `failed`). Older responses used `state`; both are still returned on some code paths.
- For completed resources that carry an asset, the signed URL lives on `structuredContent.url` — or on the `lib_list` item if the tool didn't include it inline.
- The `resource_link` block enables MCP clients to render download buttons, previews, or inline embeds.

## 9. Library Organization

Your media is organized in a library:
- **Projects** — top-level containers
- **Collections** — groups within projects
- **Resources** — individual media files

Pass `project_id` and/or `collection_id` when generating to auto-organize. Use `lib_manage` to create/update/delete. Use `lib_share` to share projects by email.

## Next Steps

- [x402 Guide](./x402.md) — Pay per call with crypto, no account needed
- [Tool Reference](./tools.md) — Detailed docs for every tool and parameter
- [Examples](../examples/) — Working Python, TypeScript, and OpenClaw code
