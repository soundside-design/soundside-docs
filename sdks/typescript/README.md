# soundside

TypeScript SDK for the [Soundside](https://soundside.ai) AI media generation platform.

Zero dependencies — uses built-in `fetch` (Node 18+).

## Install

```bash
npm install soundside
```

## Quickstart

```ts
import { Soundside } from "soundside";

const client = new Soundside({ apiKey: "mcp_your_key_here" });

// Generate an image (~4 credits / $0.04)
const image = await client.createImage("A sunset over the ocean, cinematic lighting");
console.log(image.storageUrl);

// Generate a video (async — waits automatically, ~20-80 credits)
const video = await client.createVideo("Waves crashing on a rocky coastline", {
  provider: "minimax",
});
console.log(video.storageUrl);

// Generate text
const result = await client.createText("Write a haiku about the ocean");
console.log(result.text);
```

## What you can do

Soundside exposes 19 MCP tools. The SDK has typed wrappers for the most common ones and a generic `callTool()` for everything else.

### Typed wrappers

| Method | What it does | Sync/Async |
|--------|-------------|------------|
| `createImage()` | Generate images from text | Sync |
| `createVideo()` | Generate video clips | Async (auto-waits) |
| `createAudio()` | TTS, sound effects, voice cloning, voice design | Varies |
| `createMusic()` | Generate music tracks | Async (auto-waits) |
| `createText()` | LLM text generation | Sync |
| `createArtifact()` | Presentations, charts, documents, diagrams | Sync |
| `editVideo()` | Video edits (trim, concat, crossfade, color_grade, ...) | Sync |
| `analyzeMedia()` | Metadata + AI quality analysis + transcription | Sync |
| `libList()` | Browse your library (free) | Sync |
| `libManage()` | Create/update/delete projects & collections | Sync |

### Generic dispatch (everything else)

Use `client.callTool(name, arguments)` for any tool without a typed wrapper:

- `compose_media`, `edit_audio`, `apply_effect`, `extract_media` — editing composition tools
- `compose_video` — server-side video composition pipeline
- `lib_share` — share a project with other users
- `train_adapter`, `list_adapters`, `manage_adapter` — LoRA adapter lifecycle

See `soundside-docs/guides/tools.md` for the full reference.

## Async video generation

By default, `createVideo()` and `createMusic()` wait for completion. Pass `wait: false` to get the resource ID immediately:

```ts
const resource = await client.createVideo("A timelapse of clouds", { wait: false });
console.log(`Started: ${resource.resourceId}`);

// ... do other work ...

const completed = await client.waitForResource(resource.resourceId, {
  timeout: 600_000,
});
console.log(completed.storageUrl);
```

## Image-to-video pipeline

```ts
const image = await client.createImage("A fox on a tree stump at golden hour", {
  provider: "grok",
});
const video = await client.createVideo("The fox looks around curiously", {
  firstFrame: image.resourceId,
  provider: "minimax",
});
console.log(video.storageUrl);
```

## Low-level access

Use `callTool()` for any MCP tool, including new tools added after this SDK version:

```ts
const result = await client.callTool("create_image", {
  prompt: "A sunset",
  provider: "vertex",
});
console.log(result.data); // Full response object
```

## Requirements

- Node.js 18+ (uses built-in `fetch`)
- No external dependencies

## Links

- [Documentation](https://soundside.ai/docs)
- [Quickstart](https://soundside.ai/docs/quickstart)
- [Tool Catalog](https://soundside.ai/docs/tool-catalog)
