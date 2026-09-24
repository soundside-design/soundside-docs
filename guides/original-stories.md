# Build an original short film, one reviewed stage at a time

This is an **assisted MCP workflow** for turning an original premise into a
short film. You or your agent author the shot plan, review the storyboard,
inspect generated takes, and choose the edit. Existing Soundside tools handle
generation, assembly and checks. There is no new autonomous story-maker endpoint
or dedicated storyboard-review interface on the website.

Start with a small cast, one location and clear physical actions. The example
below targets **30 seconds at 1280×720, 24 fps**, using six logical shots. It is a
copyable planning example, not a claim that this story has passed a live quality
review or that every run will produce an acceptable film.

## 1. Author the beats before generating media

Premise: a stage robot switches on a spotlight, jumps into its beam and bows.

| Shot | Target time | Action to verify |
|---|---|---|
| 1 | 0–5s | Robot reaches the button. |
| 2 | 5–10s | Finger visibly presses the button. |
| 3 | 10–15s | Spotlight turns on after contact. |
| 4 | 15–20s | Robot takes a run-up. |
| 5 | 20–25s | Robot jumps into the beam. |
| 6 | 25–30s | Robot lands and bows. |

These are editing targets, not a requirement to generate one long 30-second
clip. Write the starting state, action and ending state for each shot. Establish
shared character, location and prop reference images through `create_image`.
Use media already in the Soundside library and authorized for your account.
Import outside media first; public Compose plans do not accept media URLs.

## 2. Review the full storyboard and its timing

Prepare first and last images for every shot; add a middle image where a contact
or state change needs inspection. Review the entire sequence for consistent
identity, object placement, screen direction and cause and consequence. Record
the visible evidence separately from the executable plan. A still showing a
pressed button does not prove that generated motion will show correct contact.

The self-contained [preview request](../examples/original-story-preview.json)
is an ordinary `compose_video` call: twelve static still holds, each 2.5 seconds,
with cut transitions and no audio. It labels the output as a storyboard preview.
Replace its twelve numbered UUID placeholders with your reviewed image resource
IDs before submitting. The placeholders are syntactically valid UUIDs but do
not identify usable media.

For a middle hold, split that shot's five seconds among first/middle/last images;
each still must last at least one second. Keep every hold on the output frame
grid (multiples of 1/24 second here), and keep the total at 30 seconds. Review the
playable preview before motion generation. This pause is your workflow decision,
not a server-side hold/resume feature. Preview execution and QA are billable.

## 3. Generate one take, then inspect what happened

Generate one initial video for each reviewed shot through `create_video`. For
example, the following uses Grok first/last-frame guidance for the contact shot:

```json
{
  "name": "create_video",
  "arguments": {
    "provider": "grok",
    "prompt": "The same stage robot reaches forward and visibly presses the red button once. Keep the finger, button and contact clearly visible. Preserve the reviewed stage layout.",
    "first_frame": "00000000-0000-0000-0000-000000001003",
    "last_frame": "00000000-0000-0000-0000-000000001004",
    "advanced_options": {"duration": 5, "aspect_ratio": "16:9", "resolution": "720p"}
  }
}
```

Replace both placeholders with authorized images. Check the current tool/provider
support for references and endpoint combinations; guidance is not a guarantee of
identity or physical continuity inside a clip. Generate the hardest action first
before spending on all remaining shots.

If using Compose to generate a complete authored timeline instead, set
`quality_profile="stable"` and `video_candidates=1` for one initial video
candidate per generated shot. Frontier or a larger explicit candidate count
costs more. This setting does not disable provider recovery or establish a total
spending ceiling. For this assisted workflow, individual calls make it easier
to review each action before continuing.

Watch each result and its proposed cut. Reuse an acceptable take, trim to the
action that actually happened, or diagnose one specific defect before choosing
an edit, extension or frame-guided replacement. Check support before using a
provider edit/extension. Avoid repeated blind regeneration and do not label a
different result an improvement without comparing it.

## 4. Assemble accepted footage

The self-contained [selected-edit request](../examples/original-story-edit.json)
assembles six existing clips using source windows 0–5 seconds and a supplied
music track. Replace its six video UUID placeholders and music UUID placeholder
with authorized resources, then adjust the windows to what you observed. Each
video must actually contain the chosen interval; review music against the full cut.

An existing-footage segment has this shape within `plan.segments`:

```json
{
  "id": "shot-2",
  "type": "existing",
  "resource_id": "00000000-0000-0000-0000-000000002002",
  "source_start_sec": 0,
  "source_end_sec": 5,
  "duration_sec": 5,
  "description": "Finger visibly presses the button",
  "source_audio_volume": 0
}
```

Both source timestamps are required together. `duration_sec`, when present, must
equal their difference; each interval must fit the actual source and last at
most 30 seconds. Positive subsecond inserts are supported for existing footage.
Keep the selected durations aligned to the delivery frame rate and review the
total runtime when changing a cut. The example uses `audio_strategy="scored"`,
retains the supplied music and deliberately mutes native clip audio. If you retain
native sound or add narration, review overlap, placement and timing again.

Keep timed overlays within their selected shots. Narration that fit the original
cut may no longer fit or describe the revised one. Runtime checks do not replace
watching and listening to the complete film. Keep QA enabled and read its report,
including unresolved findings; a completed resource alone is not a creative
quality endorsement.

## Submit a saved request through MCP

Download either JSON request above, replace its resource IDs, and review it before
submitting. This script uses the public MCP SDK, with no Soundside backend imports.
Install `mcp` and `httpx`, set `SOUNDSIDE_API_KEY` and `SOUNDSIDE_MCP_URL` (normally
`https://mcp.soundside.ai/mcp`), then run it with the JSON file path. It submits
once and keeps listening for updates; Ctrl-C stops the local listener.

```python
import asyncio
import json
import os
from pathlib import Path
import sys

import httpx
from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client

async def on_message(message):
    if isinstance(message, types.ServerNotification) and isinstance(
        message.root, types.ResourceUpdatedNotification
    ):
        print("Resource changed:", message.root.params.uri, flush=True)

async def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    headers = {"Authorization": f"Bearer {os.environ['SOUNDSIDE_API_KEY']}"}
    async with httpx.AsyncClient(headers=headers, timeout=httpx.Timeout(30, read=3600)) as http:
        async with streamable_http_client(os.environ["SOUNDSIDE_MCP_URL"], http_client=http) as (read, write, _):
            async with ClientSession(read, write, message_handler=on_message) as session:
                await session.initialize()
                result = await session.call_tool(request["name"], request["arguments"])
                print(result.model_dump_json(indent=2), flush=True)
                payload = result.structuredContent or json.loads(
                    next(item.text for item in result.content if item.type == "text")
                )
                if result.isError or payload.get("success") is False or not payload.get("resource_id"):
                    raise RuntimeError("Tool call failed; inspect the response above.")
                # Save the returned parent resource_id. An update is not a terminal status.
                await asyncio.Event().wait()

asyncio.run(main())
```

Resource notifications identify what changed; they do not themselves prove
completion. Read the saved parent on demand, including after reconnecting:

```json
{
  "name": "lib_list",
  "arguments": {
    "entity_type": "resources",
    "resource_ids": ["00000000-0000-0000-0000-000000003001"]
  }
}
```

Replace that placeholder with the returned parent ID. A timeout or disconnected
client is not permission to submit the purchase again; inspect the existing job.

## Revise a specific problem

For a selected-footage edit, obtain and review the replacement take, then submit
an updated edit plan with its resource ID/window. Existing clips are reused.
Keep the original and make a labeled, synchronized side-by-side comparison with
the revision, identifying the changed intervals.

For a generated-shot composition with a durable checkpoint, `revise_from` can
rebuild the plan and reuse unchanged clips. Set `plan={}` and explicitly list the
shots to regenerate. Include all downstream `continues_from` dependents: if
shot 1 continues shot 0 and shot 2 continues shot 1, changing shot 0 requires
`regenerate=[0,1,2]`. An independent shot ends that chain; a reference image alone
does not remove an explicit continuation. Incomplete dependent sets are rejected
before charging rather than silently purchasing additional shots. See the
[Compose revision contract](./tools.md#compose_video).

## Access and cost

Compose requires OAuth/API-key credits. A successful parent adds a five-credit
orchestration fee; generation, evaluation and editing are charged separately.
One credit is $0.01. Preview, final assembly and later revisions can each incur
their own processing costs. There is no fixed price or guaranteed result for
this 30-second example, and no Compose quote-token, reserved-budget or x402
purchase flow. Track itemized usage as you proceed. Recast has a separate quoted
purchase contract for transforming an existing source film.
