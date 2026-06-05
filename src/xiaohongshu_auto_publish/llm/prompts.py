from __future__ import annotations

import hashlib
from dataclasses import dataclass

from xiaohongshu_auto_publish.errors import ConfigError


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    prompt_id: str
    version: str
    schema_id: str
    schema_version: int
    template: str
    deprecated: bool = False
    deprecated_at: str | None = None
    replacement_version: str | None = None
    deprecation_reason: str | None = None

    @property
    def template_hash(self) -> str:
        normalized = self.template.replace("\r\n", "\n").replace("\r", "\n")
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"


@dataclass(frozen=True, slots=True)
class LockedPrompt:
    prompt_id: str
    version: str
    schema_id: str
    schema_version: int
    template_hash: str
    model: str
    locked_at: str


class PromptRegistry:
    def __init__(self, templates: list[PromptTemplate]) -> None:
        self._templates = {(item.prompt_id, item.version): item for item in templates}

    def get(self, prompt_id: str, version: str) -> PromptTemplate:
        template = self._templates.get((prompt_id, version))
        if template is None:
            raise ConfigError(
                "提示词版本不存在",
                f"{prompt_id}@{version} 未注册",
                retryable=True,
                stage="prompt_version_missing",
                next_action="恢复旧模板，或显式使用 --prompt-policy latest 迁移",
            )
        return template

    def latest(self, prompt_id: str) -> PromptTemplate:
        candidates = [item for (item_id, _), item in self._templates.items() if item_id == prompt_id]
        if not candidates:
            raise ConfigError("提示词不存在", prompt_id)
        return sorted(candidates, key=lambda item: item.version)[-1]

    def all(self) -> list[PromptTemplate]:
        return sorted(self._templates.values(), key=lambda item: (item.prompt_id, item.version))


def default_prompt_registry() -> PromptRegistry:
    return PromptRegistry(
        [
            PromptTemplate(
                prompt_id="research_summary",
                version="2026-06-04.1",
                schema_id="research_summary_output",
                schema_version=1,
                template=("你是医学健康科普调研助手。请基于来源清单输出 JSON，包含 summary、facts、cautions、avoid_claims、outline。"),
            ),
            PromptTemplate(
                prompt_id="content_review",
                version="2026-06-06.1",
                schema_id="content_review_output",
                schema_version=1,
                template=(
                    "你是医学健康内容审核助手。必须只输出合法 JSON object，不要输出 Markdown。"
                    "根字段必须包含 summary、blocking、issues。"
                    "issues 中每项必须包含 issue_type、severity、risk、blocking、suggestion、location、quote。"
                    "severity 只能是字符串 S0、S1、S2、S3 之一，不要附加中文说明。"
                    '示例：{"summary":"审核摘要","blocking":false,"issues":[{"issue_type":"证据不足","severity":"S2","risk":"风险说明","blocking":false,"suggestion":"修改建议","location":"段落","quote":"原文"}]}'
                ),
            ),
            PromptTemplate(
                prompt_id="writing_review",
                version="2026-06-06.1",
                schema_id="writing_review_output",
                schema_version=1,
                template=(
                    "你是小红书医学科普写作助手。必须只输出合法 JSON object，不要输出 Markdown。"
                    "请在不新增医学事实和不夸大疗效的前提下润色。"
                    "根字段建议包含 title_candidates、body、hashtags、opening_notes、conversion_notes、"
                    "interaction_notes、account_fit、series_suggestions、changes、confirmation_required。"
                ),
            ),
            PromptTemplate(
                prompt_id="format_helper",
                version="2026-06-04.1",
                schema_id="format_helper_output",
                schema_version=1,
                template="你是小红书格式说明助手。请解释规则命中原因。",
            ),
        ]
    )
