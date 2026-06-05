from __future__ import annotations

from typing import Any

from tavily import TavilyClient  # type: ignore[import-untyped]

from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import ConfigError, SearchError
from xiaohongshu_auto_publish.models import now_iso
from xiaohongshu_auto_publish.search.provider import SearchResult


class TavilySearchProvider:
    def __init__(self, config: AppConfig, client: TavilyClient | None = None) -> None:
        self._config = config
        api_key = config.runtime_secrets.get(config.search.api_key_env)
        if not api_key:
            raise ConfigError(
                "缺少 Tavily API Key",
                f"请设置环境变量 {config.search.api_key_env}",
                next_action="在 .env 或系统环境变量中设置密钥",
            )
        self._client = client or TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int) -> list[SearchResult]:
        try:
            response = self._client.search(query=query, max_results=max_results)
        except Exception as exc:  # noqa: BLE001
            raise SearchError("联网检索失败", str(exc)[:500], retryable=True) from exc
        results = response.get("results", []) if isinstance(response, dict) else []
        return [_result_from_tavily(item) for item in results if isinstance(item, dict)]


def _result_from_tavily(item: dict[str, Any]) -> SearchResult:
    return SearchResult(
        title=str(item.get("title", "")),
        url=str(item.get("url", "")),
        snippet=str(item.get("content") or item.get("snippet") or ""),
        source_name=str(item.get("source") or item.get("url") or ""),
        published_at=str(item["published_date"]) if item.get("published_date") else None,
        retrieved_at=now_iso(),
    )
