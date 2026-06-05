from __future__ import annotations

import pytest

from xiaohongshu_auto_publish.errors import ConfigError, SearchError
from xiaohongshu_auto_publish.search.provider import FakeSearchProvider, result_from_url
from xiaohongshu_auto_publish.search.tavily_provider import TavilySearchProvider


def test_fake_search_provider_results_and_error() -> None:
    provider = FakeSearchProvider([result_from_url("https://www.who.int/a")])
    assert provider.search("query", 1)[0].url.endswith("/a")
    with pytest.raises(SearchError):
        FakeSearchProvider(error=SearchError("失败")).search("q", 1)


def test_tavily_missing_api_key_returns_config_error(app_config: object) -> None:
    app_config.runtime_secrets = {}
    with pytest.raises(ConfigError):
        TavilySearchProvider(app_config)
