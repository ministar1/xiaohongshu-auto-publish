from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from openai import OpenAI

from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import ConfigError, LLMError


@dataclass(frozen=True, slots=True)
class LLMRequest:
    system_prompt: str
    user_prompt: str
    response_format: str | None = None
    temperature: float = 0.2
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)
    raw_id: str | None = None
    raw_response: object | None = None


class LLMClientProtocol(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...


class LLMGateway:
    def __init__(self, config: AppConfig, client: OpenAI | None = None) -> None:
        self._config = config
        api_key = config.runtime_secrets.get(config.llm.api_key_env)
        if not api_key:
            raise ConfigError(
                "缺少 LLM API Key",
                f"请设置环境变量 {config.llm.api_key_env}",
                next_action="在 .env 或系统环境变量中设置密钥",
            )
        self._client = client or OpenAI(
            api_key=api_key,
            base_url=config.llm.base_url,
            timeout=config.llm.timeout_seconds,
        )

    def complete(self, request: LLMRequest) -> LLMResponse:
        last_error: Exception | None = None
        for attempt in range(self._config.llm.max_retries + 1):
            try:
                params: dict[str, Any] = {
                    "model": self._config.llm.model,
                    "messages": [
                        {"role": "system", "content": request.system_prompt},
                        {"role": "user", "content": request.user_prompt},
                    ],
                    "temperature": request.temperature,
                }
                if request.response_format == "json":
                    params["response_format"] = {"type": "json_object"}
                response = self._client.chat.completions.create(**params)
                text = response.choices[0].message.content or ""
                usage = getattr(response, "usage", None)
                return LLMResponse(
                    text=text,
                    model=self._config.llm.model,
                    provider=self._config.llm.provider,
                    usage=_usage_to_dict(usage),
                    raw_id=getattr(response, "id", None),
                    raw_response=response,
                )
            except Exception as exc:  # noqa: BLE001 - external SDK errors are normalized here
                last_error = exc
                if attempt < self._config.llm.max_retries:
                    time.sleep(min(0.2 * (attempt + 1), 1.0))
        raise LLMError(
            "LLM 调用失败",
            _safe_error_detail(last_error),
            retryable=True,
            next_action="检查模型、base_url、网络和服务状态后重试",
        )


class FakeLLMGateway:
    def __init__(
        self,
        responses: list[str] | None = None,
        error: LLMError | None = None,
        delay_seconds: float = 0,
    ) -> None:
        self._responses = list(responses or [])
        self._error = error
        self._delay = delay_seconds
        self.requests: list[LLMRequest] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        if self._delay:
            time.sleep(self._delay)
        if self._error is not None:
            raise self._error
        text = self._responses.pop(0) if self._responses else "{}"
        return LLMResponse(text=text, model="fake-model", provider="fake")


def _usage_to_dict(usage: Any) -> dict[str, int]:
    if usage is None:
        return {}
    return {
        "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
    }


def _safe_error_detail(error: Exception | None) -> str:
    if error is None:
        return ""
    detail = str(error)
    for marker in ("sk-", "XHS_AGENT_", "api_key"):
        if marker in detail:
            return "外部模型调用返回错误，敏感详情已隐藏"
    return detail[:500]
