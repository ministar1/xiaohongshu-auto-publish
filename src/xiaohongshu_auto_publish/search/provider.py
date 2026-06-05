from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from xiaohongshu_auto_publish.errors import SearchError
from xiaohongshu_auto_publish.models import now_iso


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    source_name: str
    published_at: str | None
    retrieved_at: str


class SearchProvider(Protocol):
    def search(self, query: str, max_results: int) -> list[SearchResult]: ...


class FakeSearchProvider:
    def __init__(
        self,
        results: list[SearchResult] | None = None,
        error: SearchError | None = None,
        delay_seconds: float = 0,
    ) -> None:
        self.results = list(results or [])
        self.error = error
        self.delay_seconds = delay_seconds
        self.queries: list[str] = []

    def search(self, query: str, max_results: int) -> list[SearchResult]:
        self.queries.append(query)
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        if self.error:
            raise self.error
        return self.results[:max_results]


def result_from_url(url: str, title: str = "来源", organization: str = "未知机构") -> SearchResult:
    return SearchResult(
        title=title,
        url=url,
        snippet="",
        source_name=organization,
        published_at=None,
        retrieved_at=now_iso(),
    )
