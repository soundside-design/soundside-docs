"""Response types for the Soundside SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Resource:
    """A generated or managed resource in Soundside."""

    resource_id: str
    state: str = "completed"
    storage_url: str | None = None
    duration_ms: int | None = None
    provider: str | None = None
    mime_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Resource:
        # storage_url may be top-level, or nested in metadata.storage.url (lib_list),
        # or in thumbnail_url as a fallback
        storage_url = data.get("storage_url")
        raw_meta = data.get("metadata") or {}
        # metadata may be a JSON string (from lib_list) or a dict
        if isinstance(raw_meta, str):
            import json
            try:
                raw_meta = json.loads(raw_meta)
            except (json.JSONDecodeError, TypeError):
                raw_meta = {}
        if not storage_url and isinstance(raw_meta, dict):
            storage_url = (raw_meta.get("storage", {}) or {}).get("url")
        if not storage_url:
            storage_url = data.get("thumbnail_url")

        return cls(
            resource_id=data.get("resource_id") or data.get("id", ""),
            state=data.get("state", data.get("status", "completed")),
            storage_url=storage_url,
            duration_ms=data.get("duration_ms"),
            provider=data.get("provider") or (raw_meta.get("provider") if isinstance(raw_meta, dict) else None),
            mime_type=data.get("mime_type") or (raw_meta.get("mime_type") if isinstance(raw_meta, dict) else None),
            metadata=raw_meta if isinstance(raw_meta, dict) else {},
        )


@dataclass
class ToolResult:
    """Raw result from an MCP tool call."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def resource(self) -> Resource | None:
        if self.data.get("resource_id"):
            return Resource.from_dict(self.data)
        return None

    @property
    def text(self) -> str | None:
        return self.data.get("message") or self.data.get("text")
