# Tool Reference

Complete reference for all 12 Soundside MCP tools. Always call `tools/list` at runtime to get the canonical schemas — this document is a human-readable companion.

**Live pricing:** `GET https://mcp.soundside.ai/api/x402/status`

---

## create_image

Generate images from text prompts. Supports character references for consistent characters across generations.

**Providers:** `vertex` (Gemini), `grok`, `runway`, `minimax`, `luma`

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `provider` | yes | string | AI provider |
| `prompt` | yes | string | Text description of desired image |
| `character_reference` | no | string | Resource ID or URL of a reference image for consistent character depiction (luma, minimax, grok) |
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

**Providers:** `vertex` (Veo 3.1), `runway`, `minimax` (Hailuo), `luma` (Ray-2), `grok`

All providers are **async** — returns a `resource_id` immediately, completes in background.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `provider` | yes | string | AI provider |
| `prompt` | yes | string | Text description of desired video |
| `first_frame` | no | string | Resource ID or URL for image-to-video |
| `resource_id` | no | string | Alias for `first_frame` |
| `character_reference` | no | string | Reference image for consistent characters (luma, minimax, grok, vertex) |
| `last_frame` | no | string | Resource ID or URL for last frame guidance |
| `extend_video` | no | string | Resource ID of video to extend (vertex) |
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

**Note:** `first_frame` and `character_reference` are mutually exclusive on some providers.

---

## create_audio

Create audio content. Supports multiple modes: TTS, transcription, voice cloning, voice design, and voice listing.

**Providers:** `minimax`, `vertex`

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `provider` | yes | string | AI provider |
| `mode` | no | string | `tts` (default), `transcribe`, `voice_clone`, `voice_design`, `list_voices` |
| `text` | no | string | Text for TTS |
| `voice_id` | no | string | Voice ID (default: `female-shaonv`) |
| `source` | no | string | Resource ID or URL of audio/video to transcribe |
| `language_code` | no | string | Language for transcription (default: `en-US`, v1 supports EN-US only) |
| `include_word_timestamps` | no | boolean | Per-word timestamps in transcription (default: true) |
| `audio_file_id` | no | string | Resource ID for voice cloning source |
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
    "text": "In a quiet forest, a small fox named Felix woke with the sunrise.",
    "voice_id": "female-shaonv"
  }
}
```

**Example — Transcription:**
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

---

## create_music

Generate music from lyrics and a style prompt.

**Provider:** `minimax`

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `provider` | yes | string | `minimax` |
| `lyrics` | no | string | Song lyrics (can be empty for instrumental) |
| `prompt` | no | string | Style/genre description |
| `refer_voice` | no | string | Reference voice URL |
| `refer_instrumental` | no | string | Reference instrumental URL |
| `reference_audio_resource_id` | no | string | Resource ID for reference audio |
| `reference_audio_purpose` | no | string | `song`, `voice`, or `instrumental` |
| `format` | no | string | Output: `mp3`, `wav`, `pcm` |

**Async** — returns `resource_id`, completes in background.

**Example:**
```json
{
  "name": "create_music",
  "arguments": {
    "provider": "minimax",
    "lyrics": "[verse]\nSunlight through the trees\nA fox runs wild and free\n[chorus]\nEvery path leads home",
    "prompt": "Gentle folk acoustic, warm and uplifting, children's story soundtrack"
  }
}
```

---

## create_text

Generate text using LLM chat completions. Supports structured JSON output.

**Providers:** `vertex` (Gemini, default), `grok`, `minimax`

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

Create business artifacts: presentations, charts, documents, or diagrams.

**Providers:** Local rendering (default: PPTX, Plotly, WeasyPrint, Mermaid) or `gamma` for AI-generated presentations.

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
| `output_format` | no | string | Chart: `png`/`svg`/`html`. Document: `docx`/`pdf`/`html` |
| `width` / `height` | no | integer | Output dimensions in pixels |
| `provider` | no | string | `gamma` for premium AI presentations |

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
    "diagram_code": "graph TD; A[Agent] -->|MCP| B[Soundside]; B --> C[Vertex AI]; B --> D[MiniMax]; B --> E[Luma]"
  }
}
```

---

## create_artifact_bundle

Generate multiple related artifacts from a single brief.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `brief` | yes | string | High-level description of deliverables |
| `outputs` | yes | string[] | Output formats: `pptx`, `docx`, `png`, `svg`, etc. |
| `data` | no | object | Chart data |
| `slides` | no | array | Slide definitions |
| `sections` | no | array | Document sections |
| `brand` | no | string | Brand kit applied to all artifacts |

**Example:**
```json
{
  "name": "create_artifact_bundle",
  "arguments": {
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

Edit media with 21 compositing, effects, and transformation actions. Works on video, audio, and images.

**Provider:** `soundside.ai` (platform editing engine, FFmpeg-based)

### Actions

| Action | What It Does | Key Parameters |
|--------|-------------|----------------|
| `trim` | Extract a time range | `resource_id`, `start_sec`, `duration_sec` |
| `concat` | Join multiple clips | `resource_ids` (auto-normalizes resolution) |
| `crossfade` | Transition between clips | `resource_ids`, `duration_sec` |
| `add_text` | Text overlay | `resource_id`, `text`, `position`, `fontsize`, `fontcolor` |
| `adjust_speed` | Speed up/slow down | `resource_id`, `factor`, `smooth` (AI frame interp) |
| `replace_audio` | Swap audio track | `resource_id`, `audio_source` |
| `mix_audio` | Layer audio over video | `resource_id`, `audio_source`, `video_volume`, `overlay_volume`, `duration_mode` |
| `color_grade` | Adjust brightness/contrast/saturation | `resource_id`, `brightness`, `contrast`, `saturation` |
| `extract_frame` | Single frame as image | `resource_id`, `timestamp` |
| `extract_frames` | Multiple frames | `resource_id`, `frame_interval_sec`, `start_sec`, `end_sec` |
| `extract_audio` | Audio track as file | `resource_id` |
| `ken_burns` | Pan/zoom on still image | `resource_id`, `zoom_start`, `zoom_end`, `pan_direction`, `easing` |
| `speed_ramp` | Gradual speed change | `resource_id`, `speed_start`, `speed_end`, `easing` |
| `film_grain` | Add film grain texture | `resource_id`, `grain_intensity` (1-100) |
| `vignette` | Dark edge vignette | `resource_id`, `vignette_angle` |
| `split_screen` | Side-by-side comparison | `resource_ids`, `layout`, `labels`, `gap` |
| `overlay` | Picture-in-picture | `resource_id`, `overlay_source`, `overlay_position`, `overlay_scale`, `overlay_opacity` |
| `burn_subtitles` | Burn SRT/VTT/ASS subtitles | `resource_id`, `subtitle_source` |
| `pad_audio` | Pad audio to target duration | `resource_id`, `target_duration`, `audio_position` |
| `loop` | Loop media | `resource_id` |
| `custom_ffmpeg` | Raw FFmpeg args | `resource_id`, `ffmpeg_args` |

### Common Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string (required) | One of the 21 actions above |
| `resource_id` | string | Source resource for single-input actions |
| `resource_ids` | string[] | Source resources for multi-input actions (concat, crossfade, split_screen) |
| `advanced_options` | object | Extra settings (e.g., `{"bg_color": "rgba(0,0,0,0.5)"}` for text background, `{"duration": 5}` for ken_burns) |
| `project_id` | string | Library project UUID |

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

**Example — Mix narration into video:**
```json
{
  "name": "edit_video",
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

**Example — Ken Burns on a still image:**
```json
{
  "name": "edit_video",
  "arguments": {
    "resource_id": "<image-id>",
    "action": "ken_burns",
    "zoom_start": 1.0,
    "zoom_end": 1.3,
    "pan_direction": "documentary",
    "advanced_options": {"duration": 8}
  }
}
```

**Example — Strip audio (keep video only):**
```json
{
  "name": "edit_video",
  "arguments": {
    "resource_id": "<video-id>",
    "action": "custom_ffmpeg",
    "ffmpeg_args": "-an -c:v copy"
  }
}
```

### Tips

- **Concat auto-normalizes** different resolutions to 1280×720 H.264. No manual normalization needed.
- **mix_audio with `video_volume: 0.0`** effectively replaces the audio track.
- **`duration_mode`** for mix_audio: `shortest` (default), `longest`, or `first` (video controls length).
- **Ken Burns** converts still images into video with smooth pan/zoom — great for extending scenes.

---

## analyze_media

Analyze media for technical properties, quality metrics, or AI-powered evaluation.

**Analysis types:**
- `technical` (default) — Duration, resolution, codecs, bitrate via ffprobe
- `quality` — Quality metrics
- `vision_qa` — AI evaluation using Gemini. Scores prompt adherence, style consistency, artifacts

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `resource_id` | yes | string | Resource ID or URL to analyze |
| `analysis_type` | no | string | `technical`, `quality`, `vision_qa` (default: `technical`) |
| `reference_prompt` | no | string | Original prompt for vision_qa scoring |
| `criteria` | no | string[] | Evaluation criteria: `style_consistency`, `prompt_match`, `artifacts`, `audio_quality`, `composition` |

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

**Example — Vision QA:**
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

Returns: `score` (0-1), `passed` (bool), `issues` (array of strings), `suggestions` (array).

---

## lib_list

List and search library entities.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `entity_type` | yes | string | `projects`, `collections`, `resources`, `lineage`, `brand_kits` |
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

Share projects with other users.

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `operation` | yes | string | `share`, `list`, `revoke` |
| `project_id` | yes | string | Project UUID |
| `user_email` | no | string | Email to share with (for `share`) |
| `permission_level` | no | string | `view`, `edit`, `admin` |
| `user_id_to_revoke` | no | string | User ID (for `revoke`) |
