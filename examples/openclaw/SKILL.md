# Soundside — OpenClaw Skill

Connect your OpenClaw agent to Soundside's 11 MCP tools for AI media generation, editing, and analysis.

## Setup

Add to your `openclaw.json`:

```json
{
  "skills": {
    "entries": {
      "soundside": {
        "enabled": true,
        "env": {
          "SOUNDSIDE_API_KEY": "mcp_your_key_here"
        }
      }
    }
  },
  "mcpServers": {
    "soundside": {
      "transport": "streamable-http",
      "url": "https://mcp.soundside.ai/mcp",
      "headers": {
        "Authorization": "Bearer ${SOUNDSIDE_API_KEY}"
      }
    }
  }
}
```

Then restart: `openclaw gateway restart`

## What You Get

Once connected, your agent has access to:

### Generation (6 tools)
- `create_image` — Text-to-image across 5 providers (Vertex AI, Grok, Runway, MiniMax, Luma)
- `create_video` — Text/image-to-video across 5 providers (Vertex Veo 3.1, Runway, MiniMax, Luma, Grok)
- `create_audio` — TTS, transcription, voice cloning, sound effects (MiniMax, Vertex AI, Runway, Creative Freedom)
- `create_music` — Music from lyrics + style prompt (MiniMax, Creative Freedom)
- `create_text` — LLM completions with structured output (Vertex Gemini, Grok, MiniMax)
- `create_artifact` — Charts, presentations, documents, diagrams

### Editing & Analysis (2 tools)
- `edit_video` — 21 editing actions: trim, concat, Ken Burns, mix audio, text overlays, color grading, film grain, split screen, custom, and more
- `analyze_media` — Technical analysis + AI vision QA scoring

### Library (3 tools)
- `lib_list` — Browse projects, collections, resources; **check resource status** (free)
- `lib_manage` — Create/update/delete library entities
- `lib_share` — Share projects by email

---

## ⚡ Critical: Async Completion Pattern

**Most generation tools are asynchronous.** They return immediately with a `resource_id` in `"pending"` state. The actual media is generated in the background and typically takes 10–120 seconds.

**You MUST poll for completion before using the resource in downstream tools.**

### How to Poll

Use `lib_list` with `entity_type="resources"` and `resource_id=<id>`:

```
lib_list(entity_type="resources", resource_id="<resource_id>")
```

The response includes an `items` array. Check `items[0].state` and `items[0].storage_url`:

| `state` | `storage_url` | Meaning |
|---------|---------------|---------|
| `pending` / `processing` | absent | Still generating — wait and poll again |
| `completed` | present | Ready to use in downstream tools |
| `failed` | absent | Generation failed — check `failure_reason` |

### Polling Strategy

- **Poll interval:** 5–10 seconds
- **Timeout:** 300s for most tools; 600s for video generation
- **Exit conditions:** `state == "completed"` AND `storage_url` is present, OR `state == "failed"`

### Which Tools Are Async?

| Tool | Async? | Typical Time |
|------|--------|-------------|
| `create_video` | **Yes** — always | 30–120s |
| `create_music` | **Yes** — always | 15–60s |
| `create_image` (luma, runway) | **Yes** | 10–30s |
| `create_image` (vertex, grok, minimax) | No — returns immediately | 3–10s |
| `create_audio` (TTS) | No — returns immediately | 2–5s |
| `create_text` | No — returns immediately | 1–5s |
| `edit_video` | No — returns immediately | 2–15s |
| `analyze_media` | No — returns immediately | 2–10s |
| `create_artifact` | No — returns immediately | 1–5s |

### Polling Is Free

`lib_list` calls are **free** (zero credits). Poll as often as you need.

---

## 🔗 Pipeline Ordering

Chain operations by passing `resource_id` from one step to the next. Every resource persists across sessions — no local file storage needed.

### Canonical Pipeline Sequence

```
1. Generate media        →  create_image / create_video / create_audio / create_music
2. ⏳ Poll if async      →  lib_list(entity_type="resources", resource_id=...)
3. Chain into editing    →  edit_video(resource_id=..., action="add_text", ...)
4. Mix audio             →  edit_video(resource_id=..., action="mix_audio", audio_source=...)
5. QA analysis           →  analyze_media(resource_id=..., analysis_type="vision_qa")
6. Organize              →  lib_manage(entity_type="project", operation="create", ...)
```

### Example: Narrated Video Pipeline

```
1. create_image(prompt="A fox in a forest", provider="vertex")
   → portrait_id (sync, immediately ready)

2. create_video(prompt="The fox looks around", provider="minimax", first_frame=portrait_id)
   → video_id (async, pending)

3. Poll: lib_list(entity_type="resources", resource_id=video_id)
   → Wait until state="completed"

4. create_audio(provider="minimax", mode="tts", text="In a quiet forest...")
   → narration_id (sync, immediately ready)

5. edit_video(resource_id=video_id, action="mix_audio", audio_source=narration_id)
   → final_id (sync, immediately ready)

6. analyze_media(resource_id=final_id, analysis_type="vision_qa")
   → QA score and issues
```

---

## ⚠️ Common Pitfalls

### 1. Using a Pending Resource Too Early
**Problem:** Passing a resource that's still generating to `edit_video` or `analyze_media`.
**Fix:** Always poll with `lib_list` until `state == "completed"` before chaining.

### 2. Concat Before Resources Are Ready
**Problem:** `edit_video(action="concat", resource_ids=[id1, id2])` fails because one resource is still processing.
**Fix:** Poll ALL input resources to completion before concatenating.

### 3. Session Expiry on Long Pipelines
**Problem:** MCP sessions can expire during long-running pipelines (10+ minutes of inactivity).
**Fix:** If you get a connection error mid-pipeline, re-initialize the MCP session. Your `resource_id` values are durable — they persist regardless of session state.

### 4. SSE Response Parsing
**Problem:** The server sends multiple SSE frames per response — notification frames followed by the actual JSON-RPC result.
**Fix:** Use the Python or TypeScript SDK clients in `soundside-docs/examples/`. They handle SSE parsing correctly. Do not roll your own.

### 5. Forgetting to Check for Tool-Level Errors
**Problem:** The HTTP response is 200, but the tool returned an error (`isError: true` in the MCP response).
**Fix:** Always check `result.isError` in addition to HTTP status codes.

---

## 🔄 State Persistence for Long Pipelines

For pipelines that may span multiple sessions or need crash recovery, save resource IDs to a JSON file after each step:

```json
{
  "pipeline": "narrated_video",
  "step": 3,
  "resources": {
    "portrait": "uuid-1",
    "video": "uuid-2",
    "narration": "uuid-3"
  }
}
```

On resume, load the state file and skip completed steps. All resource IDs are durable — they survive session expiry, reconnections, and server restarts.

---

## 💰 x402 Pay-Per-Call (No Account Needed)

Soundside supports [x402](https://www.x402.org/) machine-to-machine payments. Agents with an EVM wallet (Base USDC) can pay per tool call without any API key or account:

1. Call any tool without `Authorization` header
2. Server responds with `402 Payment Required` + payment details
3. Sign the USDC payment with your wallet
4. Retry the request with the signed payment header

See [`examples/python/x402_example.py`](../python/x402_example.py) for a complete implementation.

---

## 📦 SDK Clients

Pre-built clients that handle SSE parsing, session management, and async polling:

- **Python:** [`examples/python/soundside_client.py`](../python/soundside_client.py) — `SoundsideClient` with `wait_for_resource()` and `call_and_wait()`
- **TypeScript:** [`examples/typescript/soundside-client.ts`](../typescript/soundside-client.ts) — `SoundsideClient` with `waitForResource()` and `callToolAndWait()`
- **Full Pipeline Example:** [`examples/python/film_pipeline.py`](../python/film_pipeline.py) — 9-step video production pipeline

---

## Durable Resource Pattern

Every generation returns a `resource_id` that persists across sessions:

1. Generate media → receive `resource_id`
2. Poll if async → `lib_list(entity_type="resources", resource_id=...)`
3. Chain into editing: `edit_video(resource_id=..., action="add_text", ...)`
4. Organize: `lib_manage(entity_type="project", operation="create", ...)`
5. Download only for final delivery

This keeps workflow state durable without local storage.

---

## Example Workflows

**Generate and edit an image:**
```
"Create an image of a sunset over the ocean using Vertex AI,
 then add the text 'Golden Hour' as a title overlay"
```

**Produce a narrated video:**
```
"Generate a video of waves crashing using Luma,
 poll until complete,
 create TTS narration saying 'The ocean calls to those who listen',
 then mix the narration into the video"
```

**Build a presentation:**
```
"Create a pitch deck with 5 slides covering our Q1 metrics,
 include a revenue chart showing growth from $100K to $600K"
```

## Pricing

Live pricing: `GET https://mcp.soundside.ai/api/x402/status`

Soundside charges near-cost on provider pass-through (~10% margin). Editing and analysis are $0.01/call. A typical video pipeline (image → video → edit → analyze) costs $0.50-3.00 depending on provider.

## Docs

- [Getting Started](https://github.com/soundside-design/soundside-docs/blob/main/guides/getting-started.md)
- [Tool Reference](https://github.com/soundside-design/soundside-docs/blob/main/guides/tools.md)
- [x402 Pay-Per-Call](https://github.com/soundside-design/soundside-docs/blob/main/guides/x402.md)
