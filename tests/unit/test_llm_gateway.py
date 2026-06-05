from __future__ import annotations

import pytest

from xiaohongshu_auto_publish.errors import ConfigError, LLMError
from xiaohongshu_auto_publish.llm.gateway import FakeLLMGateway, LLMGateway, LLMRequest
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


def test_llm_gateway_passes_json_response_format(app_config: object) -> None:
    client = _DummyClient()
    gateway = LLMGateway(app_config, client=client)
    gateway.complete(LLMRequest("system", "user", response_format="json"))
    assert client.params["response_format"] == {"type": "json_object"}


class _DummyMessage:
    content = "{}"


class _DummyChoice:
    message = _DummyMessage()


class _DummyResponse:
    choices = [_DummyChoice()]
    id = "dummy"
    usage = None


class _DummyCompletions:
    def __init__(self) -> None:
        self.params: dict[str, object] = {}

    def create(self, **params: object) -> _DummyResponse:
        self.params = params
        return _DummyResponse()


class _DummyChat:
    def __init__(self, completions: _DummyCompletions) -> None:
        self.completions = completions


class _DummyClient:
    def __init__(self) -> None:
        self._completions = _DummyCompletions()
        self.chat = _DummyChat(self._completions)

    @property
    def params(self) -> dict[str, object]:
        return self._completions.params
