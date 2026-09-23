# Recast a video

Recast changes the people in a video, or its people and setting, while keeping the source edit and soundtrack. Use it for alternate casting, genre experiments and visual remakes of footage you have permission to transform. The MCP tool is `remix_video`; the website workspace is [Recast](https://soundside.ai/recast).

The intended result keeps the source's cuts, duration, camera movement and story beats. The assembly verifies frame counts and restores the original audio. Generated faces, hands, props and performances can still differ: inspect the synchronized comparison and delivery report before using a result. A completed job is not a guarantee that every quality check passed.

## Choose what changes

| Setting | Behavior |
| --- | --- |
| `mode="recast"` | Replace the on-screen cast while retaining the source setting, lighting and wardrobe context. |
| `mode="reskin"` | Replace the cast and visual world together; preserve the source actions and edit. |
| `recipe="source_edit"` | Default. Transform source video shots using their motion and camera information. |
| `recipe="keyframe"` | Alternate workflow that generates motion between restyled reference frames. More likely to reinterpret motion. |
| `quality_profile="draft"` | 480p generation; no automatic repair wave. |
| `quality_profile="standard"` | 720p generation; one bounded repair wave. Default. |
| `quality_profile="premium"` | 1080p generation; up to two bounded repair waves. |

Generation resolution is distinct from delivery geometry: clips are conformed to the source timeline and output dimensions. Upscaling does not create native detail. All profiles run unattended; none requires a mid-run approval. One initial take is generated per planned unit, followed by targeted repairs within the quoted allowance. Long continuous takes can require provider chunks; these are not new editorial cuts.

The source soundtrack stays in place. Recast does **not** replace dialogue, clone a voice or change the spoken language.

## Start on the website

1. Sign in at [soundside.ai/recast](https://soundside.ai/recast). Select an owned video, upload one or import a direct video-file link.
2. Describe the desired cast and, for Reskin, the setting. Optional owned reference images help communicate the desired appearance.
3. Choose a profile and, optionally, a shorter source interval. Attest that you hold the rights to remix the source.
4. Request a quote. Source analysis is paid even if you do not purchase the run. Review the processing allowance, service fee and total before starting.
5. Start with sufficient available credits to cover the quoted run ceiling. Return to the job for its film, synchronized comparison and report.

A direct link must serve video bytes over HTTP(S), not a YouTube page, streaming-player page or a login screen. For large files or inaccessible links, use upload. Imported and generated resources are private by default; sharing publicly is a separate choice.

## Price and payment

One credit is **US $0.01**. Recast has two components:

- **Processing:** metered source analysis, reference creation, video transformation, checks, repairs and assembly. The quote reserves a conservative maximum for provider processing; the final processing charge can be lower. Only work actually charged is billed; unused repair allowance is not a charge.
- **Service fee:** **$0.20 per transformed source second, with a $2 minimum per newly transformed delivery**, in addition to processing. Ten transformed seconds have a $2 service fee; 30 seconds have a $6 service fee. These are service-fee examples, not total production quotes.

The service fee is success-only: it is waived if the final motion review is missing or fails, or if unresolved quality or parity findings remain. Processing already performed is still charged, including on a failed run. A pure reassembly has no transformation service fee. A partial revision prices only the selected new transformations for its service fee; reused clips do not attract another transformation fee.

Requesting a quote performs paid analysis: probing, cut detection, and a bounded scan of longer takes where needed, plus supporting media operations. This cost is separate from buying the run and is not refunded if you decline it. A purchased token reuses its frozen plan without rescanning. Your available credit balance must cover the accepted run quote; the final run charge cannot exceed that ceiling. Keep analysis charges in mind when setting a total project budget.

**Recast currently uses authenticated account credits only.** OAuth and API keys are supported. Wallet sign-in/funding does not make Recast a per-run x402 purchase: `remix_video` is not in the x402 lane. The x402 pricing catalog therefore does not contain its purchase quote. Use `estimate_only=true` for the actual Recast price.

## Import a direct video link

Use the existing library tool first; `remix_video.source_resource_id` accepts an owned, completed video UUID, not a URL. Supply an explicit project to keep imports organized. Resource imports are paid library operations and subject to size and fetch limits.

```python
import os
from soundside_client import SoundsideClient

client = SoundsideClient(os.environ["SOUNDSIDE_API_KEY"])
client.connect()
source = client.call_tool("lib_manage", {
    "entity_type": "resource",
    "operation": "create",
    "project_id": "<owned-project-uuid>",
    "name": "courier-source.mp4",
    "mime_type": "video/mp4",
    "content_url": "https://your-media-host.example/courier-source.mp4",
    "visibility": "private",
})
if source.get("success") is False:
    raise RuntimeError(source.get("error", "Import failed"))
source_id = source["resource_id"]
```

For local files, use the website upload or the `lib_manage` `upload_initiate` → signed PUT → `upload_complete` flow. Do not put large videos in base64 tool arguments.

## Quote, review, then purchase

Fresh estimates return these fields under `metadata`:

| Field | Meaning |
| --- | --- |
| `quote.total_credits` | Maximum quoted run cost in credits. |
| `quote.line_items` | Itemized allowances and service fee. |
| `quote.root_fee_credits` | Maximum service fee included in this quote. |
| `shot_plan` / `shot_plan_resource_id` | Inline plan and its persisted private library resource. |
| `quote_token` | Opaque, signed purchase token. Store privately and send unchanged. |
| `quote_expires_at` | Expiry as Unix seconds; tokens are valid for 24 hours. |

The token is bound to the account and exact source, brief, mode, recipe, profile, range, reference images and other creative settings. It freezes the plan and terms. Changing those inputs requires a new quote. Library placement and a stricter budget cap are not creative changes.

```python
creative = {
    "source_resource_id": source_id,
    "brief": (
        "Replace the courier with an original silver-haired woman in her sixties, "
        "with expressive eyebrows and a mischievous smile. Keep the source's "
        "actions, outfit, shot framing, setting and camera movement."
    ),
    "mode": "recast",
    "recipe": "source_edit",
    "quality_profile": "standard",
    "range_start_sec": 0,
    "range_end_sec": 10,
}
estimate = client.call_tool("remix_video", {
    **creative,
    "rights_attested": True,
    "estimate_only": True,
    "budget_cap_credits": 2000,  # Example run ceiling of $20, not a price prediction.
}, timeout=600)
if estimate.get("success") is False:
    raise RuntimeError(estimate.get("error", "Quote failed"))
metadata = estimate["metadata"]
print(metadata["quote"])  # Review this before executing the purchase below.
```

After accepting the price, send the same creative settings and token:

```python
run = client.call_tool("remix_video", {
    **creative,
    "rights_attested": True,
    "estimate_only": False,
    "quote_token": metadata["quote_token"],
    "budget_cap_credits": metadata["quote"]["total_credits"],
}, timeout=180)
if run.get("success") is False:
    raise RuntimeError(run.get("error", "Purchase failed"))
parent_id = run["resource_id"]
print(parent_id)
```

If the purchase response is lost, resend **that same unexpired token and settings**. It returns the same parent job instead of generating again; `metadata.purchase_replayed=true` identifies a replay. Do not request a new quote merely to retry a purchase. A token that already produced a failed job returns that failed job, not another attempt. Starting over is a deliberate new quote and purchase.

The [runnable Python example](../examples/python/recast_quote.py) separates quotation and purchase into commands, saves the exact settings and token in a private JSON file, and rejects missing or expired quotes:

```bash
pip install httpx
export SOUNDSIDE_API_KEY="<your-api-key>"

python examples/python/recast_quote.py quote \
  --source-id "<owned-video-uuid>" \
  --brief "Replace the cyclist with an original silver-haired space courier; keep all actions and the source setting." \
  --mode recast --profile standard --start 0 --end 10 \
  --cap 2000 --output courier-quote.json --rights-attested

# Inspect the printed price before purchasing. This command can be retried.
python examples/python/recast_quote.py purchase courier-quote.json --rights-attested

# On-demand status after disconnecting; no new job and no generation charge.
python examples/python/recast_quote.py status "<parent-resource-uuid>"
```

Keep the JSON private and preserve it for retries. Do not edit its creative arguments after accepting the quote. The account still has to authenticate; possession of a token alone does not grant access.

## Completion, comparison and quality

The purchase returns a pending parent resource. MCP clients receive `notifications/resources/updated` when it changes state; no client polling is required. After reconnecting, make an on-demand read:

```json
{"name":"lib_list","arguments":{"entity_type":"resources","resource_ids":["<parent-resource-uuid>"]}}
```

The `items` response contains the parent and its metadata. Metadata may be an object or JSON string; parse it before reading `remix`. That checkpoint names the assembly and report resources. The run's library placement is also returned as `metadata.library` at purchase, so you can browse its deliverables without guessing UUIDs. Fetch output resources through `lib_list` to obtain current signed `url` download links; do not rely on a previously cached link remaining valid.

Each run organizes its evidence into six collections:

| Collection | Contents |
| --- | --- |
| `1 Source` | Source trims, native frames and contact sheets. |
| `2 Plan` | Shot plan, cast roster, continuity instructions and shot descriptions. |
| `3 Design` | Cast sheets, setting references and composition references. |
| `4 Shots` | Generated takes, including targeted repair attempts. |
| `5 Conform` | Clips fitted to the source timeline and comparison evidence. |
| `6 Deliverables` | Finished film, synchronized comparison and JSON report. |

The primary comparison shows the **original source on the left and the Recast result on the right**, synchronized in one playable frame. Review the full video with audio, especially contact between hands and props, cuts, speaking faces, text and background characters. The original is retained.

The report includes:

- `frames_expected` and `frames_delivered`: output length verification. Matching counts do not prove that each generated frame follows the source motion.
- `delivery_review`: final motion checks of the source/result comparison, sampled at 4 fps in windows of at most 10 seconds across the full delivery. This is an automated sampling check, not a guarantee that all defects were detected.
- `needs_review` and `unresolved_defects`: findings that still require attention. A technically complete film can contain these.
- `verdicts`, `parity` and `repairs`: shot checks and repair evidence where applicable.
- `processing_credits`, `service_fee_credits` and `credits_settled`: accounted job costs. Account usage records are authoritative for the settled invoice.
- `changed_intervals`: for revisions, frame intervals changed from the previous version, relative to the delivered film with an exclusive end. Divide by the parent's `metadata.remix.assembly.fps` to convert to seconds.

## Revise selected shots or recover an assembly

Use `revise_from` with an owned parent UUID and `brief=""`. A revision reuses the parent's plan and continuity design. Choose action IDs from its shot plan/report; they are not necessarily the same as detected shot numbers. A different cast or world needs a fresh brief and quote, rather than changing a revision's inherited design.

```json
{
  "name": "remix_video",
  "arguments": {
    "source_resource_id": "<original-source-uuid>",
    "brief": "",
    "rights_attested": true,
    "revise_from": "<parent-remix-uuid>",
    "regenerate_actions": ["<action-id-from-parent-plan>"],
    "budget_cap_credits": 1200,
    "estimate_only": true
  }
}
```

Review the revision estimate, then repeat with `estimate_only=false` and the accepted cap. **Purchase tokens currently apply only to fresh jobs, not revisions.** Revision calls do not have token replay protection: retain the returned parent UUID and inspect it after a timeout instead of blindly resubmitting.

For pure reassembly, set `regenerate_actions=[]`. This reuses the parent's available accepted clips and performs assembly, comparisons and review, with processing charges but no transformation service fee. It does not restore clips that were never successfully generated. Revisions retain prior resources; compare source/result for fidelity and prior/revised output for the changed intervals.

The parent's `metadata.remix.assembly.revision_comparison_resource_id` identifies the full, synchronized prior/revised film (initial on the left, revised on the right). This is supplemental to `comparison_resource_id`, which keeps the original source on the left and the current remix on the right. The website displays both and lists the changed intervals. A visible change does not by itself demonstrate an improvement.

## Recover from errors

| Response | Action |
| --- | --- |
| `QUOTE_BUSY`, `retryable=true` | Another purchase request is starting this token. Retry the same token and settings shortly. |
| `INVALID_PARAMS` for an expired/changed/invalid quote | For an already-started job, inspect its parent. Otherwise obtain a new quote and review the new price. |
| Quote exceeds `budget_cap_credits` | Inspect `metadata.quote`; shorten the selected interval, choose another profile or explicitly accept a higher cap. Analysis already performed remains paid. |
| Insufficient available balance | Fund the authenticated account, then retry the same valid token. A token is not a payment authorization by itself. |
| `PERMISSION_DENIED` | Use an owned completed source and owned image references. Do not substitute signed URLs for resource UUIDs. |
| Parent is `failed` | Inspect the failure and existing paid outputs. Reuse accepted clips where possible; do not assume all processing was refunded. |

Use runtime `tools/list` for the current schema and [the tool reference](./tools.md#remix_video) for parameters. Start with a short, representative interval before spending on a longer film.
