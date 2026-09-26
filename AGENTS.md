# AGENTS.md — soundside-docs

Developer documentation for Soundside MCP (tools, guides, SDKs).

## Rules

- Docs-only unless tasked otherwise. No inventing API behavior — match `ssd-mcp` / live catalog.
- Prefer small, precise edits; keep tables/tool lists consistent with backend.
- No secrets in examples (use placeholders).

## Capture what you learn

Guides are the canonical long-form surface — the place a user reads before spending credits, and the place another agent looks after a surprising result.

- When a measurement, delivery report or support case contradicts a guide, **fix the guide in the same change**. A guide that is quietly wrong is worse than a gap, because it is trusted.
- One canonical home per fact: the guide holds the full version; the tool description holds the one-line version; an internal `ssd-mcp/docs/` note points back rather than restating.
- State mechanisms, not stories. Name the field, setting or function involved so a reader can grep the backend.

## Verify

Markdown/link hygiene; no automated test suite required unless one is added later.

## OpenCode

```bash
opencode run "…" --dir "$HOME/src/soundside/soundside-docs" --agent build --auto --format json
```
