"""Response types for the Soundside SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Resource:
    """A generated or managed resource in Soundside.

    The signed GCS asset URL is exposed as ``url``. ``storage_url`` is
    kept as an alias so older client code keeps working. A missing
    ``url`` means the resource is still pending — poll ``lib_list``
    (or use :meth:`Soundside.wait_for_resource`) until it populates.
    """

    resource_id: str
    status: str = "completed"
    url: str | None = None
    duration_ms: int | None = None
    provider: str | None = None
    mime_type: str | None = None
    thumbnail_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # ── back-compat aliases ─────────────────────────────────
    @property
    def state(self) -> str:
        """Alias for :attr:`status` (legacy name from earlier SDK versions)."""
        return self.status

    @property
    def storage_url(self) -> str | None:
        """Alias for :attr:`url` (legacy name from earlier SDK versions)."""
        return self.url

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Resource:
        # Canonical field is ``url``. Older responses / consumers used
        # ``storage_url``; accept either for backwards-compat.
        url = data.get("url") or data.get("storage_url")

        raw_meta = data.get("metadata") or {}
        if isinstance(raw_meta, str):
            import json
            try:
                raw_meta = json.loads(raw_meta)
            except (json.JSONDecodeError, TypeError):
                raw_meta = {}
        if not url and isinstance(raw_meta, dict):
            # Some legacy persistence paths nested the URL under metadata.storage.url
            url = (raw_meta.get("storage", {}) or {}).get("url")

        return cls(
            resource_id=data.get("resource_id") or data.get("id", ""),
            status=data.get("status", data.get("state", "completed")),
            url=url,
            duration_ms=data.get("duration_ms"),
            provider=data.get("provider") or (raw_meta.get("provider") if isinstance(raw_meta, dict) else None),
            mime_type=data.get("mime_type") or (raw_meta.get("mime_type") if isinstance(raw_meta, dict) else None),
            thumbnail_url=data.get("thumbnail_url"),
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
