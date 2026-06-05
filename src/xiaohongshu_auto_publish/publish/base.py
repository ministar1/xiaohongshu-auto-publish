from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from xiaohongshu_auto_publish.models import PublishPackage


@dataclass(frozen=True, slots=True)
class PublishResult:
    success: bool
    channel: str
    message: str
    retryable: bool = False
    published_url: str | None = None
    raw_artifact_path: Path | None = None


class Publisher(Protocol):
    def publish(self, package: PublishPackage, confirmed: bool) -> PublishResult: ...
