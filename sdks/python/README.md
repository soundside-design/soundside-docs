# soundside

Python SDK for the [Soundside](https://soundside.ai) AI media generation platform.

## Install

```bash
pip install soundside
```

## Quickstart

```python
from soundside import Soundside

client = Soundside(api_key="mcp_your_key_here")

# Generate an image (~4 credits / $0.04)
image = client.create_image("A sunset over the ocean, cinematic lighting")
print(image.storage_url)

# Generate a video (async — waits automatically, ~20-80 credits)
video = client.create_video(
    "Waves crashing on a rocky coastline",
    provider="minimax",
)
print(video.storage_url)

# Generate text
result = client.create_text("Write a haiku about the ocean")
print(result.text)
```

## What you can do

| Method | What it does | Sync/Async |
|--------|-------------|------------|
| `create_image()` | Generate images from text | Sync |
| `create_video()` | Generate video clips | Async (auto-waits) |
| `create_audio()` | TTS, sound effects, transcription | Varies |
| `create_music()` | Generate music tracks | Async (auto-waits) |
| `create_text()` | LLM text generation | Sync |
| `create_artifact()` | Presentations, charts, docs | Sync |
| `edit_video()` | 21 editing actions (text, trim, concat...) | Sync |
| `analyze_media()` | Metadata + AI quality analysis | Sync |
| `lib_list()` | Browse your library (free) | Sync |
| `lib_manage()` | Create/update/delete projects & collections | Sync |
| `call_tool()` | Call any MCP tool by name | Varies |

## Async video generation

By default, `create_video()` and `create_music()` wait for completion. Pass `wait=False` to get the resource ID immediately:

```python
resource = client.create_video("A timelapse of clouds", wait=False)
print(f"Started: {resource.resource_id}")

# ... do other work ...

completed = client.wait_for_resource(resource.resource_id, timeout=600)
print(completed.storage_url)
```

## Image-to-video pipeline

```python
image = client.create_image("A fox on a tree stump at golden hour", provider="grok")
video = client.create_video(
    "The fox looks around curiously",
    first_frame=image.resource_id,
    provider="minimax",
)
print(video.storage_url)
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
