# Tool Reference

Complete reference for all 19 Soundside MCP tools. Always call `tools/list` at runtime to get the canonical schemas — this document is a human-readable companion.

> **Currency 2026-08 (2026-08-23):** Luma removed entirely; Runway is audio-only (`create_audio` TTS + sound effects). New: `create_music` Lyria 3, `create_audio` Grok TTS, Grok per-second × resolution video pricing, Alibaba Wan 2.7 video defaults, MiniMax H3 video adapter.

**Live pricing:** `GET https://mcp.soundside.ai/api/x402/status`

**Tool surface:**
- Generation (6): `create_image`, `create_video`, `create_audio`, `create_music`, `create_text`, `create_artifact`
- Composition (1): `compose_video`
- Editing (5): `edit_video`, `edit_audio`, `compose_media`, `apply_effect`, `extract_media`
- Analysis (1): `analyze_media`
- Adapters (3): `train_adapter`, `list_adapters`, `manage_adapter`
- Library (3): `lib_list`, `lib_manage`, `lib_share`

---

## create_image

Generate images from text prompts. Supports character references for consistent characters across generations.

**Providers:** `alibaba` (Wan), `grok`, `minimax`, `vertex` (Gemini), and authenticated-credit-only `creative_freedom`. Vertex is text-to-image only; reference/edit support is provider-specific.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `provider` | yes | string | AI provider |
| `prompt` | yes | string | Text description of desired image |
| `character_reference` | no | string | Resource ID or URL of a reference image for consistent character depiction (minimax, grok) |
| `advanced_options` | no | object | Provider-specific settings |
| `project_id` | no | string | Library project UUID |
| `collection_id` | no | string | Library collection UUID |
| `tags` | no | string[] | Tags for filtering |
| `name` | no | string | Custom filename |

**Example:**
```json
{
  "name": "create_image",
  "arguments": {
    "prompt": "A small orange fox in a sunlit forest clearing, children's storybook illustration style",
    "provider": "vertex"
  }
}
```

**Example with character reference:**
```json
{
  "name": "create_image",
  "arguments": {
    "prompt": "The same fox exploring a stream, watercolor style",
    "provider": "minimax",
    "character_reference": "<resource-id-of-first-image>"
  }
}
```

---

## create_video

Generate video from text prompt or image. Supports text-to-video, image-to-video (via `first_frame`), video extension, and character references.

**Providers:** `alibaba` (Wan 2.7), `grok`, `minimax` (Hailuo/H3), `vertex` (Veo 3.1), and authenticated-credit-only `creative_freedom`. Creative Freedom is text-to-video only; other operations vary by provider.

All providers are **async** — returns a `resource_id` immediately, completes in background.

**x402 amounts are ceiling quotes:** the catalog publishes the worst case, not the typical settled price. `alibaba` publishes a $24 reservation ceiling, but the actual 402 challenge quotes the metered per-second price for the requested duration and resolution; a default `grok` text-to-video (8s, 720p) quotes $1.12 against the $3.82 ceiling; `minimax` runs from $0.28 (H3 is metered up to the $1.95 ceiling); `vertex` from $1.60 against a $3.20 ceiling.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `provider` | yes | string | AI provider |
| `prompt` | yes | string | Text description of desired video |
| `first_frame` | no | string | Resource ID or URL for image-to-video |
| `resource_id` | no | string | Alias for `first_frame` |
| `character_reference` | no | string | Reference image for consistent characters (minimax, grok, vertex) |
| `last_frame` | no | string | Resource ID or URL for last frame guidance |
| `extend_video` | no | string | Resource ID or URL of video to extend/continue. Supported by: `vertex` (Veo), `grok` (6-10s). Mutually exclusive with `first_frame` and `input_video`. |
| `input_video` | no | string | Resource ID for video-to-video or Act-Two |
| `input_audio` | no | string | Resource ID for Act-Two audio input |
| `advanced_options` | no | object | Provider-specific settings |
| `project_id` | no | string | Library project UUID |
| `collection_id` | no | string | Library collection UUID |
| `tags` | no | string[] | Tags for filtering |

**Example — text-to-video:**
```json
{
  "name": "create_video",
  "arguments": {
    "prompt": "A fox drinking from a forest stream, cinematic lighting, slow motion",
    "provider": "minimax"
  }
}
```

**Example — image-to-video:**
```json
{
  "name": "create_video",
  "arguments": {
    "prompt": "The fox looks up and starts walking through the forest",
    "provider": "minimax",
    "first_frame": "<resource-id-of-image>"
  }
}
```

**Example — extend/continue an existing video (Grok):**
```json
{
  "name": "create_video",
  "arguments": {
    "prompt": "The fox continues walking deeper into the forest as dusk falls",
    "provider": "grok",
    "extend_video": "<resource-id-of-previous-clip>"
  }
}
```

**Note:** `extend_video`, `first_frame`, and `input_video` are mutually exclusive on Grok. `character_reference` is mutually exclusive with `first_frame` on some providers.

**MiniMax resolution defaults:** For durations ≤ 6s, MiniMax Hailuo-2.3 defaults to 1080P output. For 10s clips, 768P is used (API cap). Override via `advanced_options: {"resolution": "768P"}`.

---

## create_audio

Create audio content. Supports multiple modes: TTS, sound effects, voice cloning, voice design, and voice listing.

**Providers (x402 + authenticated credits):** `grok` (TTS), `minimax`, `runway` (TTS + sound effects), `vertex`. Authenticated-credit-only `creative_freedom` supports TTS + sound effects.
**Additionally via API key only:** `creative_freedom` (self-hosted CosyVoice on Modal).

Runway is audio-only — it no longer generates images or video. Grok TTS is sync and supports 26 multilingual voices (list them with `mode: "list_voices"`).

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `provider` | yes | string | AI provider |
| `mode` | no | string | `tts` (default), `sound_effect`, `transcribe` _(deprecated compatibility shim)_, `voice_clone`, `voice_design`, `list_voices` |
| `prompt` | no | string | Text for TTS speech or sound effect description |
| `voice_id` | no | string | Voice ID (default: `Calm_Woman` for MiniMax, `en-US-Chirp3-HD-Aoede` for Vertex) |
| `source` | no | string | Resource ID or URL of audio/video to transcribe |
| `language_code` | no | string | Language for transcription (default: `en-US`, v1 supports EN-US only) |
| `include_word_timestamps` | no | boolean | Per-word timestamps in transcription (default: true) |
| `audio_file_id` | no | string | Resource ID for voice cloning source |
| `duration` | no | number | Duration for sound effects (seconds) |
| `speed` | no | number | Speech speed multiplier |
| `format` | no | string | Output format: `mp3`, `wav`, `flac`, `pcm` |
| `advanced_options` | no | object | Provider-specific settings |

**Example — TTS:**
```json
{
  "name": "create_audio",
  "arguments": {
    "provider": "minimax",
    "mode": "tts",
    "prompt": "In a quiet forest, a small fox named Felix woke with the sunrise.",
    "voice_id": "Calm_Woman"
  }
}
```

**Example — Sound effect:**
```json
{
  "name": "create_audio",
  "arguments": {
    "provider": "runway",
    "mode": "sound_effect",
    "prompt": "thunder rolling across a mountain valley, cinematic"
  }
}
```

**Example — Deprecated transcription shim:**
```json
{
  "name": "create_audio",
  "arguments": {
    "provider": "vertex",
    "mode": "transcribe",
    "source": "<resource-id-of-video>",
    "language_code": "en-US"
  }
}
```

Use `analyze_media(analysis_type="transcribe")` for the canonical STT surface. `create_audio(mode="transcribe")` remains available for one version cycle and delegates internally to `analyze_media`.

---

## create_music

Generate music from lyrics and a style prompt.

**Providers:** `lyria` (Lyria 3, synchronous) and `creative_freedom` (authenticated-credit only, asynchronous). MiniMax music is unavailable and is rejected by the public schema.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `provider` | yes | string | `lyria` or `creative_freedom` |
| `lyrics` | no | string | Song lyrics (can be empty for instrumental) |
| `prompt` | no | string | Style/genre description |
| `reference_audio_resource_id` | no | string | Resource ID for reference audio |
| `reference_audio_purpose` | no | string | `song`, `voice`, or `instrumental` |
| `format` | no | string | Output: `mp3`, `wav`, `pcm` |

Creative Freedom returns a pending resource and completes in the background. Lyria returns the result synchronously.

**Example — Lyria 3:**
```json
{
  "name": "create_music",
  "arguments": {
    "provider": "lyria",
    "lyrics": "[verse]\nSunlight through the trees\nA fox runs wild and free",
    "prompt": "Gentle folk acoustic, warm and uplifting"
  }
}
```

---

## create_text

Generate text using LLM chat completions. Supports structured JSON output.

**Providers:** `vertex` (Gemini, default), `grok`, `minimax`, `qwen`

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `provider` | no | string | Default: `vertex` |
| `prompt` | no | string | Single prompt (alternative to messages) |
| `messages` | no | array | Chat messages with `role` and `content` |
| `model` | no | string | Model override |
| `temperature` | no | number | 0-2, default 0.7 |
| `max_tokens` | no | integer | Default 512 |
| `json_schema` | no | object | Schema for structured output |
| `store_response` | no | boolean | Save as library resource |

**Example:**
```json
{
  "name": "create_text",
  "arguments": {
    "prompt": "Write a 3-sentence children's story about a fox who discovers a hidden garden.",
    "provider": "vertex",
    "max_tokens": 256
  }
}
```

---

## create_artifact

Create business artifacts: presentations, charts, documents, or diagrams. Supports a **bundle mode** for generating multiple related artifacts from a single brief (e.g., a slide deck + chart + document in one call).

**Providers / implementations:** Local rendering (PPTX, Plotly, DOCX, WeasyPrint, Mermaid) or `gamma` for AI-generated presentations.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `type` | yes | string | `presentation`, `chart`, `document`, `diagram` |
| `title` | no | string | Artifact title |
| `brand` | no | string | Brand kit name for styling |
| `slides` | no | array | Slide objects (presentation) |
| `chart_type` | no | string | `bar`, `line`, `pie`, `scatter`, `area`, `heatmap`, `treemap` |
| `data` | no | object | Chart data |
| `sections` | no | array | Document sections |
| `diagram_code` | no | string | Mermaid diagram syntax |
| `output_format` | no | string | Chart: `html` (default)/`png`/`svg`. Document: `docx`/`pdf`/`html` |
| `width` / `height` | no | integer | Output dimensions in pixels |
| `provider` | no | string | `gamma` for premium AI presentations |
| `outputs` | no | string[] | **Bundle mode.** List of output formats to produce (e.g., `["pptx", "png"]`). When provided, generates multiple artifacts in one call. |
| `brief` | no | string | **Bundle mode.** High-level description of deliverables. Used with `outputs` to drive multi-artifact generation. |

**Example — Chart:**
```json
{
  "name": "create_artifact",
  "arguments": {
    "type": "chart",
    "title": "Monthly Revenue",
    "chart_type": "bar",
    "data": {
      "labels": ["Jan", "Feb", "Mar", "Apr"],
      "datasets": [{"label": "Revenue", "data": [12000, 19000, 15000, 22000]}]
    },
    "output_format": "png"
  }
}
```

**Example — Presentation:**
```json
{
  "name": "create_artifact",
  "arguments": {
    "type": "presentation",
    "title": "Q1 Review",
    "slides": [
      {"layout": "title", "title": "Q1 2026 Review", "subtitle": "Soundside Design"},
      {"layout": "content", "title": "Highlights", "body": "• Revenue up 40%\n• 3 new providers\n• x402 launch"}
    ]
  }
}
```

**Example — Diagram:**
```json
{
  "name": "create_artifact",
  "arguments": {
    "type": "diagram",
    "diagram_code": "graph TD; A[Agent] -->|MCP| B[Soundside]; B --> C[Vertex AI]; B --> D[MiniMax]; B --> E[Grok]"
  }
}
```

**Example — Bundle mode (multiple artifacts from one brief):**
```json
{
  "name": "create_artifact",
  "arguments": {
    "type": "presentation",
    "brief": "Quarterly investor update with revenue chart and slide deck",
    "outputs": ["pptx", "png"],
    "data": {
      "labels": ["Q1", "Q2", "Q3", "Q4"],
      "datasets": [{"label": "ARR", "data": [100, 250, 400, 600]}]
    }
  }
}
```

---

## edit_video

Core video transforms: trim, join, speed, color, loops, subtitles, and custom FFmpeg.

**Provider:** `soundside.ai` (platform editing engine, FFmpeg-based)

### Actions

| Action | What It Does | Key Parameters |
|--------|-------------|----------------|
| `trim` | Extract a time range | `resource_id`, `start_sec`, `duration_sec` |
| `concat` | Join multiple clips | `resource_ids`, `crossfade_ms` (optional seam smoothing) |
| `crossfade` | Transition between clips | `resource_ids`, `duration_sec`, `transition` |
| `adjust_speed` | Speed up/slow down | `resource_id`, `factor`, `smooth` (AI frame interp) |
| `loop` | Loop media to target duration | `resource_id`, `target_duration` |
| `color_grade` | Adjust brightness/contrast/saturation | `resource_id`, `brightness`, `contrast`, `saturation` |
| `custom` | Raw FFmpeg command | `resource_id` or `resource_ids`, `ffmpeg_args`, `output_format` |
| `burn_subtitles` | Burn SRT/VTT/ASS subtitles | `resource_id`, `subtitle_source` |

**Example — Concat with auto-normalization:**
```json
{
  "name": "edit_video",
  "arguments": {
    "action": "concat",
    "resource_ids": ["<id-1>", "<id-2>", "<id-3>"]
  }
}
```

**Example — Strip audio (keep video only):**
```json
{
  "name": "edit_video",
  "arguments": {
    "resource_id": "<video-id>",
    "action": "custom",
    "ffmpeg_args": "-an -c:v copy"
  }
}
```

### Tips

- **Resolution:** `concat` normalizes to 1280×720 (720P) by default. For 1080P delivery, normalize first. See [Resolution Strategy](#resolution-strategy) below.
- **`custom`** automatically appends `-pix_fmt yuv420p` when omitted — a safety net for social media compatibility.

---

## compose_media

Layer text, images, or videos onto a base video.

**Provider:** `soundside.ai`

### Actions

| Action | What It Does | Key Parameters |
|--------|-------------|----------------|
| `add_text` | Text overlay | `resource_id`, `text`, `position`, `fontsize`, `fontcolor`, `text_start_sec`, `text_end_sec` |
| `overlay` | Picture-in-picture | `resource_id`, `overlay_source`, `overlay_position`, `overlay_scale`, `overlay_opacity` |
| `split_screen` | Side-by-side comparison | `resource_ids`, `layout`, `labels`, `gap` |

**Example — Timed text overlay:**
```json
{
  "name": "compose_media",
  "arguments": {
    "resource_id": "<video-id>",
    "action": "add_text",
    "text": "Seoul, 1987",
    "position": "bottom",
    "text_start_sec": 1.0,
    "text_end_sec": 6.0
  }
}
```

### Tips

- **`text_start_sec` / `text_end_sec`** gate text overlays to a specific window — without them, text runs for the full video duration.
- **CJK text** (Korean, Chinese, Japanese) is automatically rendered using the Noto Sans CJK font — no extra configuration needed.

---

## edit_audio

Edit audio tracks on video: mix, replace, or pad audio.

**Provider:** `soundside.ai`

### Actions

| Action | What It Does | Key Parameters |
|--------|-------------|----------------|
| `mix_audio` | Layer audio over video | `resource_id`, `audio_source`, `video_volume`, `overlay_volume`, `duration_mode`, `audio_delay_sec` |
| `replace_audio` | Swap audio track | `resource_id`, `audio_source` |
| `pad_audio` | Pad audio to target duration | `resource_id`, `target_duration`, `audio_position` |

**Example — Mix narration into video:**
```json
{
  "name": "edit_audio",
  "arguments": {
    "resource_id": "<video-id>",
    "action": "mix_audio",
    "audio_source": "<narration-audio-id>",
    "video_volume": 0.0,
    "overlay_volume": 1.0,
    "duration_mode": "first"
  }
}
```

### Tips

- **mix_audio with `video_volume: 0.0`** effectively replaces the audio track.
- **`audio_delay_sec`** offsets narration start time — use this when narrations for different clips are mixed sequentially into one composite video file.
- **`duration_mode`** for mix_audio: `shortest`, `longest`, or `first` (video controls length, recommended).

---

## apply_effect

Apply cinematic effects: Ken Burns pan/zoom, speed ramp, film grain, vignette.

**Provider:** `soundside.ai`

### Actions

| Action | What It Does | Key Parameters |
|--------|-------------|----------------|
| `ken_burns` | Pan/zoom on still image→video | `resource_id`, `zoom_start`, `zoom_end`, `pan_direction`, `easing`, `duration_sec`, `ai_enhance` |
| `speed_ramp` | Gradual speed change | `resource_id`, `speed_start`, `speed_end`, `easing` |
| `film_grain` | Add film grain texture | `resource_id`, `grain_intensity` (1-100) |
| `vignette` | Dark edge vignette | `resource_id`, `vignette_angle` |

**Example — Ken Burns on a still image:**
```json
{
  "name": "apply_effect",
  "arguments": {
    "resource_id": "<image-id>",
    "action": "ken_burns",
    "zoom_start": 1.0,
    "zoom_end": 1.3,
    "pan_direction": "documentary",
    "duration_sec": 8
  }
}
```

### Tips

- **Ken Burns** converts still images into video with smooth pan/zoom — great for extending scenes.
- Use `pan_direction: "static"` for a pure zoom-only effect with no lateral movement.
- `ai_enhance: true` enables AI subject tracking + depth-based parallax (uses Modal GPU).

---

## extract_media

Extract content from media: single frame, multiple frames, or audio track.

**Provider:** `soundside.ai`

### Actions

| Action | What It Does | Key Parameters |
|--------|-------------|----------------|
| `extract_frame` | Single frame as image | `resource_id`, `timestamp` |
| `extract_frames` | Multiple frames | `resource_id`, `frame_interval_sec`, `start_sec`, `end_sec` |
| `extract_audio` | Audio track as file | `resource_id` |

**Example — Extract a frame:**
```json
{
  "name": "extract_media",
  "arguments": {
    "resource_id": "<video-id>",
    "action": "extract_frame",
    "timestamp": 5.0
  }
}
```

---

## analyze_media

Analyze media for technical properties, reusable transcript artifacts, rough-cut segment selection, EDL export, or AI-powered evaluation.

**Providers (vision_qa):** `anthropic` (Claude), `grok`, `openai` (GPT-4o), `qwen` (omnimodal), `vertex` (Gemini — default). Technical + ffprobe routes via `soundside.ai`.

**Analysis types:**
- `technical` (default) — Duration, resolution, codecs, bitrate via ffprobe
- `vision_qa` — AI evaluation. Default provider `vertex` uses **Gemini 3.1 Pro Preview** (for video) or Gemini 3.7 Flash (images). Scores prompt adherence, motion quality, temporal coherence, plus audio content analysis (narration overlap, audio artifacts, what's heard)
- `transcribe` — Canonical STT surface. Persists transcript JSON plus optional SRT/VTT sidecars
- `detect_segments` — Transcript-guided keep-range detection for rough cuts
- `export_edl` — Export persisted or inline keep-ranges as a CMX 3600 EDL

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `resource_id` | yes | string | Resource ID or URL to analyze |
| `analysis_type` | no | string | `technical`, `vision_qa`, `transcribe`, `detect_segments`, `export_edl` (default: `technical`) |
| `reference_prompt` | no | string | Original prompt for vision_qa scoring |
| `criteria` | no | string[] | Evaluation criteria: `style_consistency`, `prompt_match`, `artifacts`, `audio_quality`, `composition` |
| `intent_checklist` | no | object | Production spec checklist (vision_qa video only). See below. |
| `language_code` | no | string | Transcription language (currently `en-US` only) |
| `enable_diarization` | no | boolean | Add speaker labels to transcription output |
| `enable_silence_detection` | no | boolean | Insert silence markers into transcript segments |
| `silence_threshold_sec` | no | number | Minimum silence gap to mark |
| `include_word_timestamps` | no | boolean | Include per-word timings in transcript output |
| `subtitle_formats` | no | string[] | Subtitle sidecars to persist for transcription output (`srt`, `vtt`) |
| `prompt` | no | string | Natural-language criteria for `detect_segments` |
| `transcript_resource_id` | no | string | Reuse a previously persisted transcript for `detect_segments` |
| `mode` | no | string | `keep` or `remove` for `detect_segments` |
| `min_segment_sec` | no | number | Minimum returned keep-range duration |
| `padding_sec` | no | number | Breathing room added around cut points |
| `merge_gap_sec` | no | number | Merge neighboring ranges within this gap |
| `max_segments` | no | integer | Cap the number of returned keep-ranges |
| `segments_resource_id` | no | string | Preferred segment list input for `export_edl` |
| `segments` | no | object[] | Inline segment fallback for `export_edl` |
| `title` | no | string | EDL title header |
| `format` | no | string | `cmx3600` |
| `reel_name` | no | string | Reel identifier for CMX 3600 |
| `frame_rate` | no | number | Override source fps during EDL export |
| `include_audio` | no | boolean | Include audio tracks in EDL output when source audio exists |

**`intent_checklist` keys** (all optional):
- `text_overlays` — `[{"text": "Seoul, 1987", "start_sec": 1, "end_sec": 6}]` — verify text appears only in its window
- `no_pillarboxing` — `true` — flag any letterbox/pillarbox black bars
- `no_audio_overlap` — `true` — flag if multiple narrations play simultaneously
- `expected_resolution` — `"1280x720"` — verify resolution is met
- `expected_language` — `"English"` — verify spoken/written language

**Example — Technical:**
```json
{
  "name": "analyze_media",
  "arguments": {
    "resource_id": "<resource-id>"
  }
}
```

Returns: duration, resolution, codecs, bitrate, frame rate, audio channels, etc.

**Example — Transcribe (canonical STT):**
```json
{
  "name": "analyze_media",
  "arguments": {
    "resource_id": "<resource-id>",
    "analysis_type": "transcribe",
    "enable_diarization": true,
    "enable_silence_detection": true,
    "subtitle_formats": ["srt", "vtt"]
  }
}
```

Returns a primary `resource_id` for the transcript JSON resource plus `metadata.text`, `metadata.segments`, `metadata.srt_resource_id`, and `metadata.vtt_resource_id`.

**Example — Detect rough-cut keep ranges:**
```json
{
  "name": "analyze_media",
  "arguments": {
    "resource_id": "<resource-id>",
    "analysis_type": "detect_segments",
    "transcript_resource_id": "<transcript-resource-id>",
    "prompt": "keep the pricing discussion and the closing Q&A",
    "padding_sec": 0.5,
    "merge_gap_sec": 2.0
  }
}
```

**Example — Export CMX 3600 EDL:**
```json
{
  "name": "analyze_media",
  "arguments": {
    "resource_id": "<resource-id>",
    "analysis_type": "export_edl",
    "segments_resource_id": "<segment-resource-id>",
    "title": "SOUNDSIDE_CUT"
  }
}
```

**Example — Vision QA (generic):**
```json
{
  "name": "analyze_media",
  "arguments": {
    "resource_id": "<resource-id>",
    "analysis_type": "vision_qa",
    "reference_prompt": "A fox sitting on a tree stump at golden hour, photorealistic",
    "criteria": ["style_consistency", "prompt_match", "artifacts"]
  }
}
```

**Example — Vision QA with intent checklist (film production QA):**
```json
{
  "name": "analyze_media",
  "arguments": {
    "resource_id": "<final-film-id>",
    "analysis_type": "vision_qa",
    "intent_checklist": {
      "text_overlays": [{"text": "Seoul, 1987", "start_sec": 1, "end_sec": 6}],
      "no_pillarboxing": true,
      "no_audio_overlap": true,
      "expected_language": "Korean"
    }
  }
}
```

**Returns (vision_qa):** `score` (0–1), `passed` (bool), `issues` (array), `suggestions` (array), `checklist_results` (object, if checklist provided), `audio_summary` (string).

> **Pricing:** `technical` = 1 credit, `vision_qa` = 3 credits, `transcribe` = 2 credits, `detect_segments` = 2 credits, `export_edl` = 1 credit.

**See also:** [vision\_qa\_example.py](../examples/python/vision_qa_example.py) — dedicated example covering generic QA, spec-driven checklists, and reading audio summaries.

---

## Resolution Strategy

**TL;DR:** Don't assume a specific output resolution, be explicit about your target.

### Why This Matters

Different AI video providers output different native resolutions. The `concat` action normalizes all clips to **1280×720** (720P) by default — a safe cross-provider baseline. But this may not be what you want, especially now that MiniMax defaults to 1080P.

| Provider | Native Output | At 720P concat | At 1080P concat |
|----------|--------------|----------------|-----------------|
| Vertex | 1280×720 | no change ✓ | slight upscale |
| MiniMax (≤6s default) | 1920×1080 | **downscaled ⬇️** | no change ✓ |
| MiniMax (10s) | 1366×768 | downscaled | slight upscale |
| Grok | 848×480 | upscaled | larger upscale |

### Choosing a Target

**Use 720P (1280×720) when:**
- Your workflow mixes multiple providers (especially Vertex, which outputs 720P natively)
- You're building for social media, fast iteration, or internal review
- File size and processing speed matter
- Grok is in the mix (upscaling 480P further to 1080P loses quality)

**Use 1080P (1920×1080) when:**
- You're producing a final film deliverable for broadcast, streaming (YouTube, Vimeo), or archival
- Your clip mix is primarily or entirely MiniMax (which already generates at 1080P)
- Quality is the priority over processing speed or file size

### How to Normalize to Your Target

**720P (auto, concat default) — no action needed:**
```json
{"name": "edit_video", "arguments": {"action": "concat", "resource_ids": ["<id1>", "<id2>"]}}
```

**1080P — normalize each clip first, then concat:**
```json
{"name": "edit_video", "arguments": {
  "resource_id": "<clip-id>",
  "action": "custom",
  "ffmpeg_args": "-vf \"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2\" -c:v libx264 -crf 18 -pix_fmt yuv420p -r 24 -an"
}}
```

Then concat the normalized 1080P clips.

> **If you don't specify a target, you get 720P.** This is intentional — it's the safe cross-provider baseline. For any delivery context that specifies a resolution (broadcast, streaming platforms, client deliverables), always normalize explicitly to your target before concat.

---

## lib_list

List and search library entities.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `entity_type` | yes | string | `projects`, `collections`, `resources`, `lineage`, `brand_kits`, `credits` |
| `project_id` | no | string | Filter by project |
| `collection_id` | no | string | Filter by collection |
| `resource_id` | no | string | Get single resource |
| `resource_ids` | no | string[] | Get specific resources |
| `mime_type_prefix` | no | string | Filter by MIME type (e.g., `video/`) |
| `tags` | no | string[] | Filter by tags |
| `search` | no | string | Full-text search |
| `sort_by` | no | string | `created_at`, `name`, `size_bytes` |
| `limit` / `offset` | no | integer | Pagination |

**Example — Check async resource status:**
```json
{
  "name": "lib_list",
  "arguments": {
    "entity_type": "resources",
    "resource_id": "<resource-id>"
  }
}
```

**Example — Check credit balance:**
```json
{
  "name": "lib_list",
  "arguments": {
    "entity_type": "credits"
  }
}
```

---

## lib_manage

CRUD operations for library entities.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `entity_type` | yes | string | `project`, `collection`, `resource`, `brand_kit` |
| `operation` | yes | string | `create`, `update`, `delete` |
| `entity_id` | no | string | UUID for update/delete |
| `name` | no | string | Entity name |
| `project_id` | no | string | Parent project |
| `collection_id` | no | string | Parent collection |
| `tags` | no | string[] | Tags |
| `metadata` | no | object | Custom metadata |

**Example — Create a project:**
```json
{
  "name": "lib_manage",
  "arguments": {
    "entity_type": "project",
    "operation": "create",
    "name": "Felix the Fox Film"
  }
}
```

---

## lib_share

Share projects with other users. **Manages access permissions only — does not generate download URLs.** To retrieve a download URL for a resource, use `lib_list` with `entity_type: "resources"` and the resource UUID.

| Parameter | Required | Type | Description |
|-----------|----------|------|--------------|
| `operation` | yes | string | `share`, `list`, `revoke` |
| `project_id` | yes | string | Project UUID |
| `user_email` | no | string | Email to share with (for `share`) |
| `permission_level` | no | string | `view`, `edit`, `admin` |
| `user_id_to_revoke` | no | string | User ID (for `revoke`) |

---

## compose_video

Server-side, asynchronous video composition pipeline. It accepts a recursively strict sparse or detailed timeline, validates it before side effects, enriches gaps, generates Grok visuals with MiniMax narration and Lyria music, and assembles a final resource. **Use this when you want a finished video from a plan; use individual generation/editing tools when you need manual control.**

The production default is `quality_profile="stable"`. The only public visual-generation provider is Grok; narration uses MiniMax and generated music uses Lyria. `frontier` is an explicit experimental/high-cost, all-Grok visual candidate profile; it does not unlock other visual providers.

Fixed generated-audio fanout is profile-owned, not caller-selectable: stable creates two MiniMax narration candidates and two Lyria music candidates; frontier creates three of each. Every missing explicit-cast reference creates exactly one Grok image candidate. Compose uses one Generate→Evaluate→Select round and one narration-transcription attempt. Planning/text judges, media judges, transcription, storage, and deterministic rendering are implementation dependencies, not alternative output providers.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `plan` | yes | object | Strict `CompositionPlan`: a sparse `brief`, a detailed `segments` timeline, or both. Unknown keys are rejected recursively. |
| `reuse_segments` | no | object | Segment index → owned resource UUID for surgical revision/reuse. |
| `parent_resource_id` / `reuse_from` | no | string | Owned parent composition UUID for checkpoint-based reassembly. |
| `revise_from` | no | string | Owned parent composition UUID to revise. The server reconstructs the plan and reuse map from the parent's durable checkpoint; requires `plan={}` (`regenerate` is optional), and is mutually exclusive with `parent_resource_id`/`reuse_from`, `reuse_segments`, and `reassemble_only`. |
| `regenerate` | no | array | 0-based, unique segment indices within the parent's timeline to regenerate with `revise_from`. Empty or omitted means pure re-assembly: every parent segment is reused (zero generation), carried audio, full QA and publication — the recovery path for a failed own parent whose segments all completed. Validated against the parent's checkpointed segment count before any charge. |
| `segment_overrides` | no | object | Per-segment edits keyed by canonical index string; keys must appear in a non-empty `regenerate`. Allowed keys per override: `prompt`, `duration_sec`, `motion_intensity`, `camera_position`; unknown keys are rejected. |
| `project_id` | no | string | Library project UUID. If omitted, a project is auto-created. |
| `collection_id` | no | string | Library collection UUID. |
| `quality_profile` | no | string | `stable` (default) or explicit `frontier`; both are Grok-only for visual generation. |
| `qa`, `qa_policy`, `allow_degraded_output` | no | varies | Intermediate and mechanical checks always fail closed. Advisory degradation can publish only a complete, non-vetoed final semantic panel that misses its score, labeled `verified_degraded`. |
| `reassemble_only` | no | boolean | Rebuild from a complete reuse map or an owned parent checkpoint without regenerating segments. |

**Pricing and access:** Compose requires OAuth or API-key credits and is absent from x402 discovery/quotes. A successful root adds a five-credit orchestration fee; child generation, evaluation, and editing calls are separately itemized. Failed roots do not pay the orchestration fee.

The initial response is `pending` with a parent `resource_id`. Completion/failure is pushed through `notifications/resources/updated`; after reconnecting, recover the parent and children with `lib_list`. Duration and cost estimates are planning estimates, not an SLA.

**Example — brief + narration:**
```json
{
  "name": "compose_video",
  "arguments": {
    "plan": {
      "brief": "A concise explainer about how bees pollinate flowers, warm naturalistic style, kind narration"
    },
    "quality_profile": "stable"
  }
}
```

**Example — detailed Grok timeline:**
```json
{
  "name": "compose_video",
  "arguments": {
    "plan": {
      "title": "Pollination",
      "brief": "A warm natural-history explainer",
      "segments": [
        {"type": "video", "provider": "grok", "prompt": "Macro shot of a bee landing on a sunflower", "duration_sec": 6},
        {"type": "video", "provider": "grok", "prompt": "Pollen clings to the bee as it visits another flower", "duration_sec": 6}
      ]
    },
    "quality_profile": "stable"
  }
}
```

All media references must be authorized Soundside resource UUIDs. Public Compose does not accept media URLs, top-level `duration_sec`, nested `advanced_options`, non-Grok segment providers, public autonomy/tasks fields, or a hold/resume promise. Reuse supports complete parent reassembly and surgical revision; it does not weaken resource ownership checks.

Reference generation is explicit-cast-only: Compose does not discover or invent cast members with a provider call. Cast voice namespaces are split: `narration_voice_id` selects a closed MiniMax voice for generated dialogue, while `native_video_voice_id` selects a closed Grok voice for native video speech; legacy `cast.voice_id` is rejected. Narration is bounded to 12,000 Unicode code points total, 2,000 per per-segment entry, and at most 15 unique in-range segment entries.

Reassembly has two exact shapes. Pass exactly one of `parent_resource_id` or `reuse_from` with `reassemble_only=true`, `plan={}`, and no `reuse_segments`; or pass a detailed plan and an exact all-index reuse map. Ordinary surgical revision sets `reassemble_only=false` and may reuse only a proper subset; empty means ordinary regeneration, while a full map must use reassembly.

Revision has a server-reconstructed shortcut alongside those manual shapes: pass `revise_from=<parent UUID>` with `plan={}` and a `regenerate` list. The server rebuilds the plan and the reuse map from the owner's parent checkpoint — every segment not listed in `regenerate` reuses the parent's clip, and the parent's monolithic narration and music carry over as supplied audio (per-segment narration is re-synthesized, so even a `regenerate=[]` re-assembly of a per-segment-narration parent pays TTS again). An empty or omitted `regenerate` is a pure re-assembly of a possibly-failed own parent: zero segment generation, full QA and publication — the cheap recovery path when a run failed after all its segments completed. Optional `segment_overrides` edits only regenerated segments and requires a non-empty `regenerate`. Ownership checks are unchanged: `revise_from` is owner-only, and every reused clip and carried audio resource is authorized before any charge.

---

## train_adapter

Train a LoRA adapter (`character`, `style`, `effect`, or `transition`) from library media.

**Backends:**
- `dashscope` — Alibaba Wan LoRAs (wan2.1-t2v, wan2.2-t2v, etc.) — hosted training, fastest turnaround.
- `modal` — Self-hosted fine-tunes (HunyuanVideo, LTX-Video, Wan on Modal, HF repos).

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `name` | yes | string | Adapter display name |
| `adapter_type` | yes | string | `character`, `style`, `effect`, or `transition` |
| `training_data` | yes | array | Each item: `{ first_frame_resource_id, video_resource_id, caption }`. `kf2v` also needs `last_frame_resource_id`. |
| `base_model` | no | string | Base model identifier (defaults to `wan2.6-i2v`) |
| `backend` | no | string | `dashscope` (default) or `modal` |
| `hyper_parameters` | no | object | Backend-specific training parameters |

**Async.** Returns a pending resource_id; recover via `list_adapters` or `manage_adapter(action="inspect")`.

---

## list_adapters

List LoRA adapters mirrored into the Soundside library.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `project_id` | no | string | Project UUID filter |
| `status` | no | string | `uploading`, `training`, `selecting`, `deploying`, `deployed`, `undeploying`, `undeployed`, or `failed` |
| `adapter_type` | no | string | `character`, `style`, `effect`, or `transition` |

---

## manage_adapter

Manage an adapter's lifecycle: inspect, deploy, undeploy, delete, or select a specific checkpoint.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `adapter_id` | yes | string | Adapter resource UUID |
| `action` | yes | string | `inspect`, `deploy`, `undeploy`, `delete`, `select_checkpoint` |
| `checkpoint` | no | number/string | Checkpoint index or name (for `select_checkpoint`) |

`manage_adapter` is mixed: inspect/delete are synchronous while deploy, undeploy, and checkpoint selection can return pending.

**Inference usage:** adapters are video-only. Pass deployed adapter resource UUIDs through top-level `adapter_ids` (or deprecated singular `adapter_id`) to `create_video`. Image-adapter inference and `advanced_options.adapters` are not supported.
