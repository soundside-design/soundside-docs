# Soundside — OpenClaw Skill

Connect your OpenClaw agent to Soundside's MCP tools for AI media generation.

## Setup

Add to your `openclaw.json`:

```json
{
  "skills": {
    "entries": {
      "soundside": {
        "enabled": true,
        "env": {
          "SOUNDSIDE_API_KEY": "mcp_your_key_here"
        }
      }
    }
  },
  "mcpServers": {
    "soundside": {
      "transport": "streamable-http",
      "url": "https://mcp.soundside.ai/mcp",
      "headers": {
        "Authorization": "Bearer ${SOUNDSIDE_API_KEY}"
      }
    }
  }
}
```

## Available Tools

Once connected, your agent can use:

- `create_image` — Generate images (Vertex AI, Luma, MiniMax, Grok, Runway)
- `create_video` — Generate video (Luma, MiniMax, Runway, Vertex AI, Grok)
- `create_audio` — Text-to-speech, sound effects (MiniMax, Vertex AI)
- `create_music` — Generate music from lyrics (MiniMax)
- `create_text` — Generate text content (Vertex AI, MiniMax, Grok)
- `create_artifact` — Charts, presentations, documents
- `edit_video` — 20+ editing actions (trim, concat, add_text, burn_subtitles, etc.)
- `analyze_media` — Technical analysis, vision QA
- `lib_list` / `lib_manage` / `lib_share` — Media library management

## Example Prompts

```
"Generate an image of a sunset over the ocean using Vertex AI"
→ Agent calls create_image(prompt="...", provider="vertex")

"Create a 5-second video of waves crashing on rocks"
→ Agent calls create_video(prompt="...", provider="luma")

"Make a chart showing Q1 sales data"
→ Agent calls create_artifact(type="chart", chart_type="bar", data=[...])
```

## x402 (No API Key)

For agents with crypto wallets, Soundside supports x402 pay-per-call. No API key needed — just USDC on Base.

See the [x402 guide](https://github.com/soundside-design/soundside-docs/blob/main/guides/x402.md).
