# Getting Started with Soundside

## 1. Get an API Key

Sign up at [soundside.ai](https://soundside.ai) and generate an API key from Settings → API Keys.

Your key looks like: `mcp_abc123...`

## 2. Connect via MCP

Soundside speaks [MCP (Model Context Protocol)](https://modelcontextprotocol.io). Any MCP-compatible client can connect.

**Endpoint:** `https://mcp.soundside.ai/mcp`

### MCP JSON-RPC Flow

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

Returns all 12 tools with their schemas.

## 4. Call a Tool

```json
{"jsonrpc":"2.0","id":"3","method":"tools/call","params":{
  "name":"create_image",
  "arguments":{
    "prompt":"A red fox sitting on a tree stump, photorealistic",
    "provider":"vertex"
  }
}}
```

### Sync vs Async

- **Sync tools** (images, text, audio, artifacts): Return the result immediately with a `resource_id` and `storage_url`
- **Async tools** (video, music): Return a `resource_id` immediately. Poll with `lib_list` to check status.

## 5. Retrieve Your Media

```json
{"jsonrpc":"2.0","id":"4","method":"tools/call","params":{
  "name":"lib_list",
  "arguments":{
    "entity_type":"resources",
    "resource_id":"your-resource-id-here"
  }
}}
```

The `storage_url` field contains a signed GCS URL to download your media.

## 6. Share It

```json
{"jsonrpc":"2.0","id":"5","method":"tools/call","params":{
  "name":"lib_share",
  "arguments":{
    "resource_id":"your-resource-id-here"
  }
}}
```

Returns a shareable signed URL (valid for 7 days by default).

## Provider Selection

Each generation tool supports multiple AI providers. Choose based on your needs:

| Provider | Strengths |
|----------|-----------|
| **Vertex AI** | Google's enterprise AI. Fast, reliable, good for images and text |
| **Luma** | High-quality video generation (Ray-2) |
| **MiniMax** | Versatile — video, audio, music, TTS, images |
| **Runway** | Premium video quality (Gen-3 Alpha) |
| **Grok** | xAI's model — fast image and video generation |

If you don't specify a provider, Soundside picks the best default for each tool.

## Library Organization

Your media is organized in a library:
- **Projects** — top-level containers (like folders)
- **Collections** — groups within projects
- **Resources** — individual media files

Use `lib_manage` to create projects/collections, and pass `project_id`/`collection_id` when generating media to auto-organize.

## Next Steps

- [x402 Guide](./x402.md) — Pay per call with crypto (no account needed)
- [Tool Reference](./tools/) — Detailed docs for each tool
- [Examples](../examples/) — TypeScript, Python, and OpenClaw examples
