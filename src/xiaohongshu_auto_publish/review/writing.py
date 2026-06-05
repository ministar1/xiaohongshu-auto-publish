from __future__ import annotations

import json
from dataclasses import dataclass

from xiaohongshu_auto_publish.account.profile import AccountProfileService
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import LLMError
from xiaohongshu_auto_publish.llm.gateway import LLMClientProtocol, LLMRequest
from xiaohongshu_auto_publish.llm.prompts import PromptRegistry, default_prompt_registry
from xiaohongshu_auto_publish.models import ArtifactRef, TaskMetadata, WritingStyle


@dataclass(frozen=True, slots=True)
class WritingReviewOutput:
    title_candidates: list[str]
    body: str
    hashtags: list[str]
    opening_notes: str
    conversion_notes: str
    interaction_notes: str
    account_fit: str
    series_suggestions: list[str]
    changes: list[str]
    confirmation_required: list[str]


class WritingReviewService:
    def __init__(
        self,
        config: AppConfig,
        llm_gateway: LLMClientProtocol,
        artifact_store: ArtifactStore,
        account_service: AccountProfileService,
        prompt_registry: PromptRegistry | None = None,
    ) -> None:
        self._config = config
        self._llm = llm_gateway
        self._artifacts = artifact_store
        self._accounts = account_service
        self._prompts = prompt_registry or default_prompt_registry()

    def review(self, task: TaskMetadata, content_report: object | None = None) -> list[ArtifactRef]:
        del content_report
        source = self._artifacts.latest(task.task_id, stage="drafts", kind="draft") or self._artifacts.latest(
            task.task_id, stage="research", kind="research"
        )
        if source is None:
            raise LLMError("缺少可润色稿件", "没有 draft 或 research 产物", retryable=True)
        profile = self._accounts.load_profile(task.account_id)
        prompt = self._prompts.latest("writing_review")
        doc = self._artifacts.read_markdown(source)
        response = self._llm.complete(
            LLMRequest(
                system_prompt=prompt.template,
                user_prompt=json.dumps(
                    {
                        "style": task.style.value,
                        "title_candidates": self._config.writing.title_candidates,
                        "account": profile.__dict__ if hasattr(profile, "__dict__") else {},
                        "body": doc.body,
                    },
                    ensure_ascii=False,
                ),
                response_format="json",
            )
        )
        output = _parse_writing_output(response.text, task.style)
        if _contains_forbidden(output.body, profile.forbidden_phrases):
            output.confirmation_required.append("输出包含账号禁用表达，需人工确认或修改")
        revised = self._artifacts.save_markdown(
            task.task_id,
            stage="drafts",
            kind="revised",
            body=_render_revised(output),
            source_artifacts=[source.artifact_id],
            user_editable=True,
        )
        report = self._artifacts.save_markdown(
            task.task_id,
            stage="reviews",
            kind="writing_review",
            body=_render_writing_report(output),
            source_artifacts=[source.artifact_id, revised.artifact_id],
            user_editable=True,
        )
        return [revised, report]


def _parse_writing_output(text: str, style: WritingStyle) -> WritingReviewOutput:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError("写作润色输出解析失败", str(exc), retryable=True, stage="writing") from exc
    if not isinstance(raw, dict):
        raise LLMError("写作润色输出结构错误", "根对象必须是 JSON object", retryable=True, stage="writing")
    return WritingReviewOutput(
        title_candidates=_string_list(raw.get("title_candidates"), [f"{style.value} 标题候选"]),
        body=str(raw.get("body", "")),
        hashtags=_string_list(raw.get("hashtags")),
        opening_notes=str(raw.get("opening_notes", "")),
        conversion_notes=str(raw.get("conversion_notes", "")),
        interaction_notes=str(raw.get("interaction_notes", "")),
        account_fit=str(raw.get("account_fit", "")),
        series_suggestions=_string_list(raw.get("series_suggestions")),
        changes=_string_list(raw.get("changes")),
        confirmation_required=_string_list(raw.get("confirmation_required")),
    )


def _string_list(value: object, default: list[str] | None = None) -> list[str]:
    if value is None:
        return list(default or [])
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]


def _render_revised(output: WritingReviewOutput) -> str:
    return (
        "# 润色稿\n\n"
        "## 标题候选\n\n"
        + "\n".join(f"- {item}" for item in output.title_candidates)
        + "\n\n## 正文\n\n"
        + output.body
        + "\n\n## 标签建议\n\n"
        + " ".join(f"#{tag.lstrip('#')}" for tag in output.hashtags)
        + "\n\n## 仍需用户确认\n\n"
        + "\n".join(f"- {item}" for item in output.confirmation_required)
        + "\n"
    )


def _render_writing_report(output: WritingReviewOutput) -> str:
    return (
        "# 写作审核报告\n\n"
        f"开头优化：{output.opening_notes}\n\n"
        f"关注引导：{output.conversion_notes}\n\n"
        f"互动引导：{output.interaction_notes}\n\n"
        f"账号一致性：{output.account_fit}\n\n"
        "## 系列化建议\n\n"
        + "\n".join(f"- {item}" for item in output.series_suggestions)
        + "\n\n## 关键改写\n\n"
        + "\n".join(f"- {item}" for item in output.changes)
        + "\n"
    )


def _contains_forbidden(body: str, forbidden: list[str]) -> bool:
    return any(item and item in body for item in forbidden)
