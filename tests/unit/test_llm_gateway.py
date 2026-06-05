from __future__ import annotations

import pytest

from xiaohongshu_auto_publish.errors import ConfigError, LLMError
from xiaohongshu_auto_publish.llm.gateway import FakeLLMGateway, LLMRequest
from xiaohongshu_auto_publish.llm.prompts import default_prompt_registry


def test_fake_llm_fixed_output_and_error() -> None:
    fake = FakeLLMGateway(["ok"])
    assert fake.complete(LLMRequest("s", "u")).text == "ok"
    with pytest.raises(LLMError):
        FakeLLMGateway(error=LLMError("失败")).complete(LLMRequest("s", "u"))


def test_prompt_hash_and_missing_locked_version() -> None:
    registry = default_prompt_registry()
    template = registry.latest("content_review")
    assert template.template_hash.startswith("sha256:")
    assert template.template_hash == registry.get("content_review", template.version).template_hash
    with pytest.raises(ConfigError):
        registry.get("content_review", "missing")
