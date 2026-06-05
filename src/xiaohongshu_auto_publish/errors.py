from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class XHSError(Exception):
    summary: str
    detail: str = ""
    retryable: bool = False
    stage: str | None = None
    next_action: str | None = None
    related_artifacts: list[Path] = field(default_factory=list)

    def __post_init__(self) -> None:
        Exception.__init__(self, self.summary)


class ConfigError(XHSError):
    pass


class ArtifactError(XHSError):
    pass


class StateError(XHSError):
    pass


class LLMError(XHSError):
    pass


class StructuredOutputError(XHSError):
    pass


class StructuredOutputSchemaError(StructuredOutputError):
    pass


class StructuredOutputRiskFieldError(StructuredOutputError):
    pass


class SearchError(XHSError):
    pass


class ReviewBlockedError(XHSError):
    pass


class MediaValidationError(XHSError):
    pass


class LockError(XHSError):
    pass


class PublishError(XHSError):
    pass
