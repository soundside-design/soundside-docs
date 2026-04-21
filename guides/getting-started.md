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

> **MCP Tasks (2025-11-25):** Clients that support the `tasks` capability can also track async operations via `tasks/get` and `tasks/list`. The tool result will include a `resource_link` content block with the resource URI for convenient access.

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

Each generation tool supports multiple AI providers. If you don't specify one, Soundside picks a default.

| Use Case | Recommended Provider | Why |
|----------|---------------------|-----|
| Highest quality video | `vertex` (Veo 3.1) | Best motion, longest clips |
| Open-weights video with tight controls | `alibaba` (Wan) | 13 operations incl. VACE, i2v, kf2v, animate |
| Best value video | `minimax` (Hailuo) | Good quality, lowest cost |
| Fast image generation | `vertex` or `grok` | Sync, sub-10s |
| Cheapest images | `luma` ($0.02) / `alibaba` ($0.05) / `minimax` ($0.04) | |
| Text-to-speech | `minimax` | Multiple voices, voice cloning |
| Transcription (STT) | `vertex` | EN-US, word-level timestamps |
| Music generation | `minimax` | Only public provider (Creative Freedom is API-key-only) |
| LLM text | `vertex` (Gemini) | General purpose |
| Vision QA over video | `vertex` (Gemini 2.5 Pro, default) or `qwen` | Also: `anthropic`, `grok`, `openai` |

## 6. Sync vs Async

| Behavior | Tools |
|----------|-------|
| **Sync** — result in response | `create_image` (alibaba, grok, minimax, vertex), `create_text`, `create_audio` (vertex, runway), `create_artifact`, `edit_video`, `compose_media`, `edit_audio`, `apply_effect`, `extract_media`, `analyze_media` (technical/vision_qa/export_edl), `list_adapters`, `manage_adapter`, `lib_*` |
| **Async** — returns `resource_id`, completes later | `create_video` (all providers), `create_music`, `compose_video`, `create_image` (luma, runway), `create_audio` (minimax TTS, minimax sound_effect), `analyze_media` (transcribe/detect_segments on long inputs), `train_adapter` |

For async tools, listen for MCP `notifications/resources/updated`, poll with `lib_list`, or use MCP tasks (see below).

## 7. MCP Tasks (Advanced)

Soundside supports MCP **tasks** for tracking async operations. Clients that declare the `tasks` capability during `initialize` get structured progress tracking:

- Tools like `create_video` declare `execution.taskSupport = "optional"`
- Tool results include `resource_link` content blocks with `soundside://resources/{id}` URIs
- Use `tasks/get` to poll status: `working` → `completed` or `failed`
- Use `tasks/list` to see all active tasks

Most clients (Claude, OpenClaw, etc.) handle tasks automatically. For raw HTTP usage, you can continue using `lib_list` polling.

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
