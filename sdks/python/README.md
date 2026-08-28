# soundside

Python SDK for the [Soundside](https://soundside.ai) AI media generation platform.

## Install from a local checkout

This SDK is source-only. Soundside does not publish a wheel or registry package from this repository.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install ./soundside-docs/sdks/python
```

## Quickstart

```python
from soundside import Soundside

client = Soundside(api_key="mcp_your_key_here")

# Generate an image (~4 credits / $0.04)
image = client.create_image("A sunset over the ocean, cinematic lighting", provider="vertex")
print(image.url)

# Generate a video (async — waits automatically, ~20-80 credits)
video = client.create_video(
    "Waves crashing on a rocky coastline",
    provider="minimax",
)
print(video.url)

# Generate text
result = client.create_text("Write a haiku about the ocean", provider="vertex")
print(result.text)
```

## What you can do

Soundside exposes 19 MCP tools. The SDK has typed wrappers for the most common ones and a generic `call_tool()` for everything else.

### Typed wrappers

| Method | What it does | Sync/Async |
|--------|-------------|------------|
| `create_image()` | Generate images from text | Varies (Alibaba is pending) |
| `create_video()` | Generate video clips | Async (auto-waits) |
| `create_audio()` | TTS, sound effects, voice cloning, voice design | Varies |
| `create_music()` | Generate music tracks | Varies (auto-waits when pending) |
| `create_text()` | LLM text generation | Sync |
| `create_artifact()` | Presentations, charts, documents, diagrams | Sync |
| `edit_video()` | Video edits (trim, concat, crossfade, color_grade, ...) | Sync |
| `analyze_media()` | Metadata + AI quality analysis + transcription | Sync |
| `lib_list()` | Browse your library (free) | Sync |
| `lib_manage()` | Create/update/delete projects & collections | Sync |

### Generic dispatch (everything else)

Use `client.call_tool(name, arguments)` for any tool without a typed wrapper:

- `compose_media`, `edit_audio`, `apply_effect`, `extract_media` — editing composition tools
- `compose_video` — server-side video composition pipeline
- `lib_share` — share a project with other users
- `train_adapter`, `list_adapters`, `manage_adapter` — LoRA adapter lifecycle

See `soundside-docs/guides/tools.md` for the full reference.

## Async video generation

By default, `create_video()` and `create_music()` wait for completion. Pass `wait=False` to get the resource ID immediately:

```python
resource = client.create_video("A timelapse of clouds", provider="minimax", wait=False)
print(f"Started: {resource.resource_id}")

# ... do other work ...

completed = client.wait_for_resource(resource.resource_id, timeout=600)
print(completed.url)
```

## Image-to-video pipeline

```python
image = client.create_image("A fox on a tree stump at golden hour", provider="grok")
video = client.create_video(
    "The fox looks around curiously",
    first_frame=image.resource_id,
    provider="minimax",
)
print(video.url)
```

## Transcription

`transcribe()` calls the canonical `analyze_media(analysis_type="transcribe")` surface and does not require a prompt:

```python
result = client.transcribe(video.resource_id, subtitle_formats=["srt", "vtt"])
print(result.data)
```

## Low-level access

Use `call_tool()` for any MCP tool, including new tools added after this SDK version:

```python
result = client.call_tool("create_image", {
    "prompt": "A sunset",
    "provider": "vertex",
})
print(result.data)  # Full response dict
```

## Requirements

- Python 3.10+
- httpx

## Links

- [Documentation](https://soundside.ai/docs)
- [Quickstart](https://soundside.ai/docs/quickstart)
- [Tool Catalog](https://soundside.ai/docs/tool-catalog)
