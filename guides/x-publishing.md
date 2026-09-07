# Publish to X from Soundside MCP

Soundside can publish text, finished images, and finished MP4 video to a connected X account. The MCP tool is `publish_content`; it uses authenticated Soundside credits and is not available through x402.

## One-time setup

1. Open [Account settings](https://soundside.ai/account) and choose **Connect X**.
2. Review the consent notice and approve the X authorization in the browser.
3. For an unattended bot, enable publishing for the specific Soundside API key or verified OAuth client that should be allowed to post.
4. Give the bot the Soundside MCP API key. It does not receive the X password or X access tokens.

Website sign-in and the X publishing connection are separate. Soundside stores the X OAuth 1.0a user authorization encrypted on the server. These user tokens have no scheduled refresh cycle, so a daily scheduler does not require a routine website login. X can revoke an authorization; reconnecting or disconnecting X also revokes existing unattended grants, so enable the intended bot again after reconnecting.

An interactive first-party website session can publish as the connected user. API-key and verified OAuth-client calls require the explicit unattended grant. A disabled or revoked API key, OAuth client, grant, or X connection prevents publishing.

## Call `publish_content`

Always call `tools/list` at runtime for the current schema. The required `idempotency_key` identifies one intended post and must remain stable across retries. `destination` is currently `"x"`.

### Text

```json
{
  "name": "publish_content",
  "arguments": {
    "destination": "x",
    "idempotency_key": "daily-briefing:2026-09-08",
    "project_id": "11111111-1111-4111-8111-111111111111",
    "text": "Today's Soundside briefing is ready.",
    "made_with_ai": true
  }
}
```

### One finished video

```json
{
  "name": "publish_content",
  "arguments": {
    "destination": "x",
    "idempotency_key": "film:8a4d7d2c:publish",
    "project_id": "11111111-1111-4111-8111-111111111111",
    "text": "A quiet morning at the coast.",
    "resource_ids": ["22222222-2222-4222-8222-222222222222"],
    "made_with_ai": true
  }
}
```

### Images with aligned alt text

```json
{
  "name": "publish_content",
  "arguments": {
    "destination": "x",
    "idempotency_key": "campaign-stills:2026-09-08",
    "project_id": "11111111-1111-4111-8111-111111111111",
    "text": "Two moments from the new campaign.",
    "resource_ids": [
      "33333333-3333-4333-8333-333333333333",
      "44444444-4444-4444-8444-444444444444"
    ],
    "alt_texts": [
      "A cyclist on a tree-lined road at sunrise.",
      "A close view of the cyclist's hands on the handlebars."
    ],
    "made_with_ai": true
  }
}
```

The project and every resource must belong to the authenticated user. Resources must be completed Soundside media. A request may contain text, media, or both. Set `made_with_ai` to `true` unless you have a specific reason to change X's disclosure flag.

## Media and text limits

- Text is limited to 280 weighted characters. URLs use X's weighted URL length.
- Use one to four JPEG, PNG, or WebP images, with each image at most 5 MiB.
- Use one MP4 video, at most 512 MiB and 140 seconds. Video must use H.264 with `yuv420p`; audio, when present, must use AAC.
- `alt_texts` follows the same order as `resource_ids`. Each image description is optional and may contain at most 1,000 characters.
- An MP4 cannot be combined with images. Duplicate resource IDs and mixed image/video requests are rejected.

## Daily external scheduling

Soundside does not schedule posts. Use cron, a workflow runner, or the agent's scheduler to call `publish_content` after the finished resource is ready. Build the idempotency key from the intended post identity, such as `account:content-id:publish`, rather than from the current time. If the scheduler retries the same intended post, send the exact same text, resource IDs, alt text, project, `made_with_ai` value, and key.

The same key with a changed payload is rejected. Do not create a new key to bypass that rejection or to bypass an unresolved final outcome.

## Receipts and recovery

Admission returns a pending receipt resource. The receipt ID is durable and is also returned as `resource_id` in the tool response. Completion is pushed through `notifications/resources/updated`. To recover after a reconnect or process restart, call:

```json
{
  "name": "lib_list",
  "arguments": {
    "entity_type": "resources",
    "resource_id": "55555555-5555-4555-8555-555555555555"
  }
}
```

A completed receipt includes the connected X account, post ID, post URL, rendered text, and source resource IDs. Terminal failures include an `error_code`; a disconnected account can cancel queued work. If a receipt reports an unknown post outcome, inspect the X account before making another post. Reuse the unchanged idempotency key to recover the durable job state, and create a new key only after confirming that the intended post was not accepted.

## Authenticated-credit pricing

One Soundside credit is $0.01 USD. X publishing is excluded from x402 and does not appear in `GET https://mcp.soundside.ai/api/x402/status`. The current pricing policy uses these base classes:

| Request | Current base class |
| --- | ---: |
| Plain post or media post with no URL and no nonempty alt text | 2 credits |
| Plain post or media post whose text contains a URL | 22 credits |
| One to four nonempty image alt-text entries | Adds the applicable metadata class; URL requests range from 23 to 25 credits |

The server derives the class from the final text and alt-text values; callers cannot select a cheaper class by adding pricing parameters. The pre-execution estimate is authoritative and pricing may change. Successful publishing settles once; a failed admission or failed dispatch does not create a second reservation for the same durable job.

See the [tool reference](./tools.md#publish_content) for the compact schema and [x402 guide](./x402.md) for the lane rules that exclude publishing.
