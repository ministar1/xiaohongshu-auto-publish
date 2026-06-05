from __future__ import annotations

import pytest

from xiaohongshu_auto_publish.errors import SearchError
from xiaohongshu_auto_publish.search.provider import result_from_url
from xiaohongshu_auto_publish.source_policy.policy import SourcePolicy


def test_source_policy_builtin_trusted_and_unknown_date(app_config: object) -> None:
    policy = SourcePolicy(app_config)
    evaluation = policy.evaluate(result_from_url("https://www.who.int/news"))
    assert evaluation.authoritative
    assert evaluation.published_at_status == "published_at_unknown"


def test_high_risk_all_unknown_sources_recoverable_failure(app_config: object) -> None:
    policy = SourcePolicy(app_config)
    with pytest.raises(SearchError):
        policy.require_authoritative_for_high_risk("高血压药物剂量", [result_from_url("https://blog.example/a")])
