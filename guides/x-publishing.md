# X account operations from Soundside MCP

`publish_content` is Soundside's single X tool. It can publish finished Soundside media and perform the supported account, Post, and relationship operations listed below. It requires authenticated Soundside credits and is unavailable through x402.

Call `tools/list` against the live MCP endpoint before integrating. It is the machine-readable source for the current schema and limits.

## One-time setup and permissions

1. Open [Account settings](https://soundside.ai/account) and choose **Connect X**.
2. Approve the displayed X authorization for the destination account.
3. For an unattended API key or verified OAuth client, select that agent and grant only the capabilities it needs: **read**, **publish**, or **manage**.
4. Give the agent its Soundside credential. It never receives an X password, OAuth 1.0a token, or token secret.

Website sign-in and the X connection are separate. Soundside stores the X OAuth 1.0a user authorization encrypted on the server. Those tokens have no routine refresh cycle, and normal daily use does not need another Soundside browser login. X can revoke the authorization. Reconnecting or disconnecting X revokes existing unattended grants, so reconnect the intended account and grant the intended agents again. The agent's Soundside API key or OAuth credential remains separate and must remain valid.

A first-party website session has the connected account's capabilities. API keys and verified OAuth clients require an explicit, current-generation standing grant. Existing grants start with **publish** only; read and manage are never added silently.

| Capability | Supported actions |
| --- | --- |
| `read` | `get_account`, `get_user`, `get_posts`, `list_posts`, `list_mentions`, `search_posts`, `list_followers`, `list_following` |
| `publish` | `publish`, `reply` |
| `manage` | `edit`, `delete`, `like`, `unlike`, `repost`, `unrepost` |

## The shared `publish_content` contract

Use `destination: "x"`. Set `action` to one of the supported values. `action` defaults to `publish` for existing clients.

- `idempotency_key` is **required for every write**: `publish`, `reply`, `edit`, `delete`, `like`, `unlike`, `repost`, and `unrepost`. Reuse the exact key and payload to recover an interrupted write. Reads reject an idempotency key because they are synchronous.
- `made_with_ai` remains `true` by default for the MCP tool, for compatibility. New posts from the website show an unchecked **Made with AI** checkbox; the choice is saved and locked with the pending request. Pass this field explicitly in an agent integration and keep its value unchanged on a retry.
- X Post and user identifiers are numeric strings, for example `"1888000000000000001"`. They are not Soundside resource UUIDs.
- `limit` defaults to 10. `list_posts` and `list_mentions` require at least 5, `search_posts` at least 10, and `list_followers`/`list_following` at least 1; every list caps at 100. Recent search covers the last seven days. Private fields are available only for the connected account’s own Posts where X permits them in its active window. `pagination_token` is opaque and at most 2,048 characters; do not parse or synthesize it.
- `get_posts` accepts either one `post_id` or `post_ids` (up to 100), never both. `include_private_metrics` is accepted only by `get_posts` and defaults to `false`.
- `username` is accepted **only** by `get_user`, which requires exactly one of `username` or `x_user_id`.
- `list_posts`, `list_followers`, and `list_following` use the connected account by default or accept `x_user_id`. They do not accept `username`; resolve a handle first with `get_user` so a paid lookup is explicit.

### Supported reads — synchronous

Read actions return a completed standard response with top-level `data` (an X object or list), `meta`, optional `includes`, bounded `errors`, Soundside-derived `total_count`, and `next_pagination_token` where available. There is no `items` field. An empty page succeeds with `total_count: 0`; partial data and errors can coexist.

| Action | Required or useful arguments |
| --- | --- |
| `get_account` | None; returns the connected account identity. |
| `get_user` | Exactly one of `username` or `x_user_id`. |
| `get_posts` | `post_id` or `post_ids`; optional `include_private_metrics`. |
| `list_posts` | Optional `x_user_id`, `limit`, `pagination_token`; defaults to the connected account. |
| `list_mentions` | Optional `limit`, `pagination_token`; reads mentions for the connected account. |
| `search_posts` | `query`; optional `limit`, `pagination_token`. Recent search only. |
| `list_followers` | Optional `x_user_id`, `limit`, `pagination_token`; defaults to the connected account. |
| `list_following` | Optional `x_user_id`, `limit`, `pagination_token`; defaults to the connected account. |

```json
{"name":"publish_content","arguments":{"action":"get_account","destination":"x"}}
```

```json
{"name":"publish_content","arguments":{"action":"get_user","destination":"x","username":"soundside"}}
```

```json
{"name":"publish_content","arguments":{"action":"get_posts","destination":"x","post_ids":["1888000000000000001","1888000000000000002"],"include_private_metrics":false}}
```

```json
{"name":"publish_content","arguments":{"action":"list_posts","destination":"x","x_user_id":"1888000000000000003","limit":10}}
```

```json
{"name":"publish_content","arguments":{"action":"list_mentions","destination":"x","limit":10,"pagination_token":"opaque-page-token"}}
```

```json
{"name":"publish_content","arguments":{"action":"search_posts","destination":"x","query":"soundside release","limit":10}}
```

```json
{"name":"publish_content","arguments":{"action":"list_followers","destination":"x","x_user_id":"1888000000000000003","limit":10}}
```

```json
{"name":"publish_content","arguments":{"action":"list_following","destination":"x","limit":10}}
```

### Supported writes — durable and asynchronous

Writes return a durable receipt resource after admission. `publish`, `reply`, and `edit` eventually include a Post ID; `delete`, `like`, `unlike`, `repost`, and `unrepost` complete as operations and do not claim that a new Post was published. A receipt can become `completed`, `failed`, `cancelled`, or `unknown`.

Use one stable, short idempotency key for the intended operation. Do not create a new key after a timeout, ambiguous response, or unknown outcome. Reusing the same key with a different action, text, target, media, disclosure, or principal is rejected. An unknown final outcome is never blindly retried against X; an exact replay recovers the existing durable request.

#### Publish text, finished video, or images

```json
{"name":"publish_content","arguments":{"action":"publish","destination":"x","idempotency_key":"xop-pub-a1","project_id":"11111111-1111-4111-8111-111111111111","text":"Today’s Soundside briefing is ready.","made_with_ai":false}}
```

```json
{"name":"publish_content","arguments":{"action":"publish","destination":"x","idempotency_key":"xop-vid-a1","project_id":"11111111-1111-4111-8111-111111111111","text":"A quiet morning at the coast.","resource_ids":["22222222-2222-4222-8222-222222222222"],"made_with_ai":true}}
```

```json
{"name":"publish_content","arguments":{"action":"publish","destination":"x","idempotency_key":"xop-img-a1","project_id":"11111111-1111-4111-8111-111111111111","text":"Two moments from the new campaign.","resource_ids":["33333333-3333-4333-8333-333333333333","44444444-4444-4444-8444-444444444444"],"alt_texts":["A cyclist on a tree-lined road at sunrise.","A close view of the cyclist’s hands on the handlebars."],"made_with_ai":true}}
```

#### Reply and manage operations

X permits a self-serve reply only when the original author mentioned the replying account or quoted one of its Posts (the account is summoned). Do not automatically reply to a mention or search result. Omit `reply_settings` for X’s default; valid choices for `publish` and `reply` are `mentionedUsers`, `following`, `subscribers`, and `verified`.

```json
{"name":"publish_content","arguments":{"action":"reply","destination":"x","idempotency_key":"xop-reply-a1","post_id":"1888000000000000001","text":"Thanks for the feedback.","made_with_ai":false}}
```


```json
{"name":"publish_content","arguments":{"action":"edit","destination":"x","idempotency_key":"xop-edit-a1","post_id":"1888000000000000001","text":"Updated copy.","preserve_media":true,"made_with_ai":false}}
```

Edit checks the Post's current X `edit_controls`, including the deadline and edits remaining; Soundside does not promise a fixed edit window. With `preserve_media: true` (the default), omit replacement `resource_ids`. Media preservation uses trusted upload IDs saved for posts published through Soundside. For attachments from other sources, supply replacement library resources and set `preserve_media: false`; Soundside rejects the edit before mutation when it cannot preserve media safely.

```json
{"name":"publish_content","arguments":{"action":"delete","destination":"x","idempotency_key":"xop-del-a1","post_id":"1888000000000000001","text":"","made_with_ai":false}}
```

```json
{"name":"publish_content","arguments":{"action":"like","destination":"x","idempotency_key":"xop-like-a1","post_id":"1888000000000000001","text":"","made_with_ai":false}}
```

Use the same shape for `unlike`, `repost`, and `unrepost`, changing only `action` and using a new key for that intended operation. `delete`, `like`, `unlike`, `repost`, and `unrepost` reject text and media.

### Media rules for publish/reply/edit replacements

- Use one to four JPEG, PNG, or WebP images, at most **5 MiB each**.
- Use one MP4 video, at most **512 MiB** and **140 seconds**; H.264 with `yuv420p`, with optional AAC audio.
- `alt_texts` aligns with image `resource_ids`; each entry is at most 1,000 characters. Use `""` to skip one image. Omit alt text for video.
- Media must be owner-owned, completed Soundside resources. Arbitrary URLs, mixed images/video, multiple videos, and duplicate resources are rejected.
- Text has a conservative 280 weighted-character limit. URLs count as at least 23 characters.

## Receipts, notifications, and recovery

A newly admitted write returns a pending receipt such as:

```json
{"success":true,"status":"pending","resource_id":"55555555-5555-4555-8555-555555555555","metadata":{"provider":"x","account":{"username":"soundside"}}}
```

Listen for `notifications/resources/updated`. To recover after a reconnect or a new process, make one free library lookup:

```json
{"name":"lib_list","arguments":{"entity_type":"resources","resource_ids":["55555555-5555-4555-8555-555555555555"]}}
```

A confirmed publish/reply/edit receipt carries a Post ID and `post_url`. A completed manage receipt describes the completed operation. Failed and cancelled receipts carry a bounded error. With `unknown`, X may have accepted the final write: inspect the connected account before starting another operation, then reuse the exact original key only to recover the existing request.

## Authenticated-credit pricing

One credit is USD $0.01. X operations are authenticated-credit-only and never appear in `GET https://mcp.soundside.ai/api/x402/status`. A read admission quotes the requested-page ceiling, but final read settlement uses actual returned count `N`; empty results cost 0.

| Operation | Credit rule |
| --- | --- |
| Publish | 2 credits normally; 22 credits when text contains a URL; nonempty image alt text uses the existing metadata class. |
| Reply | Same class as publish. |
| Edit | `ceil(total provider USD × 110)`: 3 credits plain, 23 with a URL, before optional alt-text metadata. |
| Delete | 2 credits, including ownership lookup. |
| Like, unlike, repost, unrepost | 2 credits each. |
| Post reads (`get_posts`, `list_posts`, `list_mentions`, `search_posts`) | `ceil(0.55 × N)` credits for actual returned count `N`. |
| User and relationship reads (`get_account`, `get_user`, `list_followers`, `list_following`) | `ceil(1.1 × N)` credits for actual returned count `N`. |

Read admission uses the requested page ceiling, up to 100. No hidden username expansion occurs for list, follower, or following calls. Final settlement uses the returned count.

## Unsupported in this release

This release does not support DMs, bookmarks, ads, quote creation, or any raw X endpoint passthrough. Quote creation is Enterprise-only and intentionally excluded. Soundside does not schedule actions; use your own cron job or workflow to invoke a deliberate tool call.
