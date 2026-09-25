# Build an original short film, one reviewed stage at a time

This is an **assisted MCP workflow** for turning an original premise into a
short film. You or your agent author the shot plan, review the storyboard,
inspect generated takes, and choose the edit. Existing Soundside tools handle
generation, assembly and checks. There is no new autonomous story-maker endpoint
or dedicated storyboard-review interface on the website.

Start with a small cast, one location and clear physical actions. The example
below targets **30 seconds at 1280×720, 24 fps**, using six logical shots. It is a
copyable planning example. The reviewed film below shows a separate executed
version of the premise; its accepted edit is shorter than the planning target.

## Reviewed example: The Grand Entrance

**25.5 seconds · 1280×720 · 24 fps · Music and native effects**

A tiny theatrical robot finds the light button on a dark stage, jumps onto it to
switch on the spotlight, then takes its moment in the beam and bows.

[Play the film on the website](https://www.soundside.ai/docs/original-stories#grand-entrance)
· [Direct film video](https://www.soundside.ai/r/2RJe8QnqNi2ktaduggM9Uz/resource)

[Play the full initial/revised comparison](https://www.soundside.ai/docs/original-stories#grand-entrance-revision)
· [Direct comparison video](https://www.soundside.ai/r/6v17g2dubRRdCGqxyxjCvW/resource)

**Initial left · Revised right.** Both films start together; cuts diverge after
the trims. The initial film lasts 30.25 seconds and the revised film 25.5 seconds.
The right panel then holds its final frame with a completion label. Only the
revised soundtrack plays. The repaired shot is at **13.5–16.5 seconds** in the
revision, corresponding to approximately **15.1–20.2 seconds** in the initial cut.

This was an assisted production with review between stages:

- Fifteen images were generated in total: ten distinct accepted images, reused
  across thirteen storyboard holds, and five superseded images. The full board
  was reviewed before broad motion generation, including the repaired frames.
- Six initial five-second motion takes were generated, one per shot.
- Direct inspection found a changing button housing. One targeted provider
  video edit repaired that shot;
  the other five motion takes were reused.
- The 30-second draft was trimmed to a 25.5-second edit, using the observed
  action and adding music while retaining selected native effects.

The final film passed mechanical checks and automated review and was also
inspected directly. A slightly floaty jump and minor spatial inconsistency
between cuts remain. Automated review supports the editorial decision and
still needs visual inspection. This example demonstrates an assisted workflow,
not unattended or guaranteed film
quality. The robot-story templates below remain illustrative 30-second plans rather than
the exact requests used for this finished edit.

## Reviewed documentary: The Chip Race

**88 seconds · 1280×720 · 24 fps · Continuous narration**

**Reporting cutoff: 24 September 2026**

A short explainer about export controls and China's developing GPU and
AI-accelerator industry. Authored source graphics carry the evidence; generated
B-roll is labeled as illustration. Company claims remain attributed, and the
film does not claim blanket performance parity with Nvidia.

[Play the documentary](https://www.soundside.ai/docs/original-stories#chip-race)
· [Direct film video](https://www.soundside.ai/r/7Uxr4d6D5QJvPAtD3MWX9N/resource)

[Play the full initial/revised comparison](https://www.soundside.ai/docs/original-stories#chip-race-revision)
· [Direct comparison video](https://www.soundside.ai/r/3MWZoHkgFw0HuJFJMhbj8x/resource)

**Initial left · Revised right.** Both films last 88 seconds, with the same
narration and timing. Only **0–5 seconds** and **39–43 seconds** change.

The assisted production used one 197-word MiniMax narration, six reviewed
initial reference images and six initial B-roll takes. Two targeted video edits
were attempted, followed by selection of clean source windows. The original and
rejected full takes were preserved. Acceptance applies to the observed selected
intervals; the full takes did not reliably carry out the intended contact actions.
Seven authored card videos and the illustration windows form the 16-segment edit.

The final film passed technical checks and four automated model reviews; its
cards and cuts were also inspected directly. Minor AI stiffness and inconsistent
server textures remain. The review supports this edit, not unattended factual
verification or guaranteed complex motion.

The [downloadable source ledger](../examples/documentary-sources.json) maps the
claims and their limits to these six primary sources:

- [BIS, 7 October 2022](https://www.bis.gov/node/20292): export-control announcement
  and stated national-security rationale.
- [BIS, 17 October 2023](https://www.bis.gov/media/1332): the follow-up controls.
- [Moore Threads S5000 product page](https://en.mthreads.com/product/S5000), accessed
  24 September 2026: a vendor description of a GPU for AI training and inference.
- [CloudMatrix384 research paper, v3, 19 June 2025](https://arxiv.org/html/2506.12708v3):
  developer-reported architecture using 384 Ascend NPUs, not an independent
  across-the-board benchmark. The paper was first submitted on 15 June 2025.
- [Huawei, 17 September 2026](https://www.huawei.com/cn/news/2026/9/hc-wang-keynote):
  the company's claim of more than 1,000 Ascend 910C supernodes deployed, not an
  independent audit.
- [Huawei, 18 September 2025](https://www.huawei.com/en/news/2025/9/hc-xu-keynote-speech):
  its account of the 2019 Ascend 910 launch and manufacturing constraints.

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
with cut transitions and no audio. It labels the output as a storyboard preview
and explicitly requests a draft with `qa=false`, `qa_policy="advisory"` and
`allow_degraded_output=false` from the outset. Review its stills and timing
manually; technical checks still run, but this draft is not semantically
approved motion.
Replace its twelve numbered UUID placeholders with your reviewed image resource
IDs before submitting. The placeholders are syntactically valid UUIDs but do
not identify usable media.

For a middle hold, split that shot's five seconds among first/middle/last images;
each still must last at least one second. Keep every hold on the output frame
grid (multiples of 1/24 second here), and keep the total at 30 seconds. Review the
playable preview before motion generation. This pause is your workflow decision,
not a server-side hold/resume feature. Preview assembly is billable. Check the
actual hold durations, image order and output geometry as well as the story.
Use `qa=true`, `qa_policy="gate"` and `allow_degraded_output=false` for the final
motion edit, as the selected-edit example does; draft review does not replace
that gate or direct inspection of the film.

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

## Make a narration-led 60–90 second documentary

For a short documentary, establish the evidence and continuous voice track before
choosing the final picture edit. You or your agent research, author and review
each stage; Compose assembles the supplied media. This is not one-click automatic
fact-checking, and generated illustrations do not establish what happened in the
real world.

1. **Keep a primary-source ledger.** Record a source ID, publisher, publication or
   version date, URL, the exact claim it supports and its limits. Set a reporting
   cutoff. Map each narrated assertion and graphic to that ledger; distinguish
   company-reported figures from independently checked results. Keep the ledger,
   script and editorial notes beside the request, outside the strict public plan.
2. **Record one continuous narrator.** Review the script, choose one MiniMax voice,
   then submit the whole text with `create_audio(provider="minimax", mode="tts")`.
   Listen to the resulting audio from start to finish. Use
   `analyze_media(analysis_type="transcribe")` for timing and a transcript, but
   check questionable names against the audio: a transcription error alone does
   not prove a pronunciation error. Measure the recording before fixing the
   film's duration; leave room for the final sentence and its tail.
3. **Prepare pictures that support the voice.** Review first frames for every
   generated B-roll shot together, checking hardware, hands, geography and the
   intended action before purchasing motion. Generate one initial candidate per
   shot and inspect the actual footage. First-frame guidance does not make
   intricate installation, plugging or other contact motion reliable. If a take
   fails, keep a useful observed interval or make one diagnosed repair; describe
   only what the selected interval shows. Author charts, diagrams, dates and
   citations as deliberate graphics rather than asking a video model to invent
   factual text. Import completed graphics and turn them into timed card videos.
4. **Lock an edit from existing resource windows.** The
   [88-second documentary request](../examples/original-story-documentary.json)
   uses six illustration clips and seven authored card videos across **16 existing
   segments**, plus one narration resource. Repeated UUID placeholders deliberately
   reuse the same source. Replace the thirteen distinct video UUIDs and the audio
   UUID with completed resources your account may use; these numbered placeholders
   are valid UUID syntax, not usable media. Check every selected start/end against
   its source. The durations total 88 seconds at 24 fps; fit them to your own
   reviewed narration instead of assuming any script takes 88 seconds. The template
   follows the reviewed documentary's edit structure but contains no usable media.
5. **Normalize and label before delivery.** Prepare a narration master at an
   explicit sample rate, channel count and loudness target, then inspect the
   exported file and listen again. For example, use 48 kHz mono, a −16 LUFS target
   and a −1.5 dBTP true-peak limit for a speech-led web edit; verify the measured
   result rather than assuming the requested settings were achieved. This example
   mutes clip sound with `source_audio_volume=0`, supplies no music and retains one
   narration track. Its segment-local overlays label every generated illustration
   for that interval's full duration. Keep that label visible after trims and do
   not present synthetic B-roll as footage of a named company or event. Put readable
   source attribution and dates on the authored cards.
6. **Review the actual delivered film.** Keep `qa=true`, `qa_policy="gate"` and
   `allow_degraded_output=false`. Inspect the native output with sound and read its
   QA report; review suspicious motion frame by frame, all cuts, labels, graphics
   and the final words. Check loudness, clipping, silence, speech intelligibility
   and narration/picture alignment. Automated visual or audio review is not a
   factual audit. Preserve acceptable media and repair only the observed defect,
   then reassemble and compare the complete initial/revised films with changed
   intervals identified.

MiniMax's standard MP3, WAV, FLAC and PCM TTS sample rates top out at **44,100 Hz**;
48 kHz delivery is a subsequent export/resampling step. In `create_audio`, use the
existing public `sample_rate`, `channel` and `format` fields, for example
`sample_rate=44100`, `channel=1`, `format="wav"`. Then normalize/export the completed
resource to your delivery format and verify its actual audio properties. See the
[MiniMax TTS reference](https://platform.minimax.io/docs/api-reference/speech-t2a-http).

For **supplied narration**, the assembly plan uses only the resource and mix level:

```json
{
  "audio_strategy": "narrated",
  "audio": {
    "narration": {
      "resource_id": "00000000-0000-0000-0000-000000006001",
      "volume_db": 0
    }
  }
}
```

This is a plan fragment; use the complete linked request for submission. Do not
attach `script`, `provider`, `voice_id`, `speed` or per-segment generation settings
to that supplied narration. Those belong to the earlier generation request, not
to reuse of its finished audio. Do not copy internal checkpoint fields into a
public request. Preparation, attempted repairs, analysis and assembly are billable;
the template is not a fixed-price production quote.

## Submit a saved request through MCP

Download a JSON request above, replace its resource IDs, and review it before
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
