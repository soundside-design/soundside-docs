# Soundside — OpenClaw Skill

Connect your OpenClaw agent to Soundside's 19 MCP tools for AI media generation, editing, composition, extraction, analysis, server-side composition, and LoRA adapter training.

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
- `create_image` — Text-to-image across 4 providers (Alibaba Wan, Grok, MiniMax, Vertex AI). Creative Freedom is API-key-only.
- `create_video` — Text/image-to-video across 4 providers (Alibaba Wan 2.7, Grok, MiniMax Hailuo/H3, Vertex Veo 3.1). Creative Freedom is API-key-only.
- `create_audio` — TTS, voice cloning, sound effects (Grok, MiniMax, Runway, Vertex AI). Runway is audio-only. Creative Freedom is API-key-only.
- `create_music` — Music from lyrics + style prompt (Lyria 3; Creative Freedom is authenticated-credit only). MiniMax music is unavailable.
- `create_text` — LLM completions with structured output (Grok, MiniMax, Vertex Gemini)
- `create_artifact` — Charts, presentations, documents, diagrams (plotly, pptx, docx, weasyprint, mermaid, gamma)

### Composition (1 tool)
- `compose_video` — Authenticated-credit-only asynchronous composition using Grok visuals, MiniMax narration, and Lyria music. Stable is the default profile; plans are recursively strict and media inputs are authorized Soundside UUIDs. Public autonomy/task/hold-resume controls and URLs are unsupported. Child calls are itemized and a successful root adds a 5-credit orchestration fee. Use `lib_list` to recover state after reconnecting.

### Editing (5 tools)
- `edit_video` — Core video transforms: trim, concat, crossfade, speed, loop, color grading, subtitles, custom FFmpeg
- `edit_audio` — Mix, replace, or pad audio on existing media
- `compose_media` — Add text, overlay media, or build split-screen composites
- `apply_effect` — Ken Burns, speed ramp, film grain, vignette
- `extract_media` — Extract frames, frame sets, or audio tracks

### Analysis (1 tool)
- `analyze_media` — Technical ffprobe analysis, AI vision QA (Anthropic, Grok, OpenAI, Qwen, Vertex Gemini), canonical transcription, segment detection, and EDL export
- `create_audio(mode="transcribe")` — Deprecated v1.x transcription compatibility shim; new integrations use `analyze_media(analysis_type="transcribe")`

### Adapters — LoRA (3 tools)
- `train_adapter` — Train a LoRA adapter from library media on DashScope (Wan) or Modal (HunyuanVideo, LTX-Video) backends
- `list_adapters` — List LoRA adapters available to your account
- `manage_adapter` — Inspect, deploy, undeploy, delete, or select a checkpoint for an adapter

### Library (3 tools)
- `lib_list` — Browse projects, collections, resources; **check resource status and fetch signed asset URLs** (free)
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

The response includes an `items` array. Check `items[0].status` and `items[0].url`:

| `status` | `url` | Meaning |
|---------|---------------|---------|
| `pending` / `processing` | absent | Still generating — wait and poll again |
| `completed` | present | Ready to use in downstream tools |
| `failed` | absent | Generation failed — check `failure_reason` |

> **Field names:** The current backend publishes `status` and `url`. Older releases used `state` and `storage_url`; Soundside still returns both aliases on some code paths, so defensive code should accept `status ?? state` and `url ?? storage_url`.

### Polling Strategy

- **Poll interval:** 5–10 seconds
- **Timeout:** 300s for most tools; 600s for video generation; 600s+ for LoRA training (minutes→hours)
- **Exit conditions:** `status == "completed"` AND `url` is present, OR `status == "failed"`

### Which Tools Are Async?

| Tool | Async? | Non-binding planning range (not an SLA) |
|------|--------|-------------|
| `create_video` (all providers) | **Yes** — always | 30–120s |
| `create_music` (creative_freedom) | **Yes** | 15–60s |
| `create_music` (lyria) | No — returns immediately | 5–30s |
| `compose_video` | **Yes** — many internal async calls | 2–20 min depending on length |
| `create_image` (grok, minimax, vertex, creative_freedom) | No — returns immediately | 3–30s |
| `create_image` (alibaba) | **Yes** | 3–30s |
| `create_audio` (grok, vertex) | No — returns immediately | 2–10s |
| `create_audio` (minimax, runway) | **Yes** | 3–15s |
| `create_text` | No — returns immediately | 1–5s |
| `edit_video` / `edit_audio` / `compose_media` / `apply_effect` / `extract_media` | No — returns immediately | 2–15s |
| `analyze_media` (`technical`, `vision_qa`, `export_edl`) | No — returns immediately | 2–15s |
| `analyze_media` (`transcribe`, `detect_segments`) | No — waits and returns a final result | 5–120s |
| `create_artifact` | No — returns immediately | 1–5s |
| `train_adapter` | **Yes** — long-running | minutes→hours depending on backend |
| `list_adapters` | No — sync | 1–5s |
| `manage_adapter` | Mixed — deploy/undeploy may remain pending | 1–5s or longer for deployment |

### Polling Is Free

`lib_list` calls are **free** (zero credits). Poll as often as you need.

---

## 🔗 Pipeline Ordering

Chain operations by passing `resource_id` from one step to the next. Every resource persists across sessions — no local file storage needed.

### Canonical Pipeline Sequence

```
1. Generate media        →  create_image / create_video / create_audio / create_music
2. ⏳ Poll if async      →  lib_list(entity_type="resources", resource_id=...)
3. Add overlays          →  compose_media(resource_id=..., action="add_text", ...)
4. Mix audio             →  edit_audio(resource_id=..., action="mix_audio", audio_source=...)
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
   → Wait until status="completed" and url is present

4. create_audio(provider="minimax", mode="tts", prompt="In a quiet forest...")
   → narration_id (sync, immediately ready)

5. edit_audio(resource_id=video_id, action="mix_audio", audio_source=narration_id)
   → final_id (sync, immediately ready)

6. analyze_media(resource_id=final_id, analysis_type="vision_qa")
   → QA score and issues
```

### Example: Smart Cut / Rough Cut

```
1. analyze_media(resource_id=source_id, analysis_type="technical")
   → duration, frame rate, audio presence

2. analyze_media(
     resource_id=source_id,
     analysis_type="transcribe",
     enable_diarization=true,
     enable_silence_detection=true,
     subtitle_formats=["srt", "vtt"]
   )
   → transcript_resource_id (+ transcript JSON as the primary resource)

3. analyze_media(
     resource_id=source_id,
     analysis_type="detect_segments",
     transcript_resource_id=transcript_resource_id,
     prompt="keep the pricing discussion and closing Q&A",
     padding_sec=0.5,
     merge_gap_sec=2.0
   )
   → segments_resource_id with keep ranges

4. Present the keep ranges to the user before cutting.

5. Trim each keep range with edit_video(action="trim"), then assemble with
   edit_video(action="concat", resource_ids=[...], crossfade_ms=75)

6. analyze_media(
     resource_id=source_id,
     analysis_type="export_edl",
     segments_resource_id=segments_resource_id,
     title="SOUNDSIDE_CUT"
   )
   → edl_resource_id

7. analyze_media(resource_id=rough_cut_id, analysis_type="vision_qa", intent_checklist={...})
   → verify no abrupt seams, no text timing issues, no audio overlap
```

Smart Cut is video-first in Phase 1. Audio-only sources support transcript, detected segments, and EDL export, but not assembled rough-cut media.

---

## ⚠️ Common Pitfalls

### 1. Using a Pending Resource Too Early
**Problem:** Passing a resource that's still generating to `edit_video` or `analyze_media`.
**Fix:** Always poll with `lib_list` until `status == "completed"` and `url` is present before chaining.

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
3. Chain into editing: `compose_media(resource_id=..., action="add_text", ...)`
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
"Generate a video of waves crashing using MiniMax,
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

One credit is $0.01 USD. Published metered rates are based on provider cost with an approximately 10% platform margin unless a tool-specific flat fee is listed. Compose adds a five-credit success-only orchestration fee and separately itemizes child calls; it is not available through x402. Every paid call receives a pre-execution estimate and settles once.

At the pro tier, `lib_list` alone is free, Compose is authenticated-credit only, and the remaining 17 tools are x402-eligible subject to their provider/mode lanes.

## Docs

- [Getting Started](https://github.com/soundside-design/soundside-docs/blob/main/guides/getting-started.md)
- [Tool Reference](https://github.com/soundside-design/soundside-docs/blob/main/guides/tools.md)
- [x402 Pay-Per-Call](https://github.com/soundside-design/soundside-docs/blob/main/guides/x402.md)
