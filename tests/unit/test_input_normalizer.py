from __future__ import annotations

from pathlib import Path

import pytest

from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.errors import StateError
from xiaohongshu_auto_publish.input.normalizer import ArticleInputRequest, InputNormalizer, TopicInputRequest
from xiaohongshu_auto_publish.models import WritingStyle
from xiaohongshu_auto_publish.state.store import StateStore, slugify


def test_topic_and_article_normalize(app_config: object, tmp_path: Path) -> None:
    state = StateStore(app_config)
    artifacts = ArtifactStore(app_config)
    normalizer = InputNormalizer(app_config, state, artifacts)
    topic = normalizer.create_topic(TopicInputRequest("睡眠不足"))
    assert topic.task.style == WritingStyle.POPULAR
    article_path = tmp_path / "article.md"
    article_path.write_text("# 标题\n正文", encoding="utf-8")
    article = normalizer.create_article(ArticleInputRequest(article_path=article_path))
    assert artifacts.read_markdown(article.artifact).body.startswith("# 标题")


def test_empty_topic_rejected(app_config: object) -> None:
    with pytest.raises(StateError):
        InputNormalizer(app_config, StateStore(app_config), ArtifactStore(app_config)).create_topic(TopicInputRequest(""))


def test_slugify_ascii_and_chinese_fallback() -> None:
    assert slugify("Sleep_Metabolism") == "sleep-metabolism"
    assert slugify("中文") == "topic"
