from __future__ import annotations

from dataclasses import dataclass

from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.errors import (
    StructuredOutputRiskFieldError,
    StructuredOutputSchemaError,
)
from xiaohongshu_auto_publish.llm.gateway import LLMClientProtocol, LLMRequest
from xiaohongshu_auto_publish.llm.prompts import PromptRegistry, default_prompt_registry
from xiaohongshu_auto_publish.models import ParseStatus, ReviewIssue, ReviewReport, TaskMetadata
from xiaohongshu_auto_publish.review.output_parser import parse_content_review_output


@dataclass(frozen=True, slots=True)
class ContentReviewResult:
    report: ReviewReport
    artifact_id: str


class ContentReviewService:
    def __init__(
        self,
        llm_gateway: LLMClientProtocol,
        artifact_store: ArtifactStore,
        prompt_registry: PromptRegistry | None = None,
    ) -> None:
        self._llm = llm_gateway
        self._artifacts = artifact_store
        self._prompts = prompt_registry or default_prompt_registry()

    def review(self, task: TaskMetadata) -> ReviewReport:
        source = (
            self._artifacts.latest(task.task_id, stage="drafts", kind="draft")
            or self._artifacts.latest(task.task_id, stage="research", kind="research")
            or self._artifacts.latest(task.task_id, stage="inputs", kind="topic")
        )
        if source is None:
            report = ReviewReport(
                task_id=task.task_id,
                stage="content",
                issues=[],
                blocking=True,
                summary="没有可审核的源产物",
                model="none",
                created_at="",
                parse_status=ParseStatus.FAILED,
            )
            self._save_report(report)
            return report
        doc = self._artifacts.read_markdown(source)
        prompt = self._prompts.latest("content_review")
        try:
            response = self._llm.complete(
                LLMRequest(
                    system_prompt=prompt.template,
                    user_prompt=doc.body,
                    response_format="json",
                    metadata={"prompt_id": prompt.prompt_id, "prompt_version": prompt.version},
                )
            )
            report = parse_content_review_output(
                response.text,
                task_id=task.task_id,
                model=response.model,
                source_artifacts=[source.artifact_id],
            )
        except (StructuredOutputSchemaError, StructuredOutputRiskFieldError) as exc:
            report = ReviewReport(
                task_id=task.task_id,
                stage="content",
                issues=[],
                blocking=True,
                summary=exc.summary,
                model="unknown",
                created_at="",
                source_artifacts=[source.artifact_id],
                parse_status=ParseStatus.FAILED,
                parse_warnings=[exc.detail],
            )
        self._save_report(report)
        return report

    def _save_report(self, report: ReviewReport) -> None:
        body = render_content_review_report(report)
        self._artifacts.save_markdown(
            report.task_id,
            stage="reviews",
            kind="content_review",
            body=body,
            front_matter={
                "parse_status": report.parse_status.value,
                "blocking": report.blocking,
                "source_artifacts": report.source_artifacts,
                "manual_override": report.manual_override,
            },
            source_artifacts=report.source_artifacts,
            user_editable=True,
        )


def render_content_review_report(report: ReviewReport) -> str:
    lines = [
        "# 内容审核报告",
        "",
        f"本次审核对象：{', '.join(report.source_artifacts) or '未知'}",
        f"解析状态：{report.parse_status.value}",
        f"审核结论：{'阻断' if report.blocking else '通过'}",
        "",
        "## 摘要",
        "",
        report.summary,
        "",
        "## 问题列表",
        "",
    ]
    if not report.issues:
        lines.append("- 暂无结构化问题")
    for issue in report.issues:
        lines.extend(_issue_lines(issue))
    if report.parse_warnings:
        lines.extend(["", "## 解析警告", ""])
        lines.extend(f"- {warning}" for warning in report.parse_warnings)
    lines.extend(["", "## 下一步建议", "", "如存在 S0/S1 或解析风险，请修改源稿后重新审核。"])
    return "\n".join(lines) + "\n"


def _issue_lines(issue: ReviewIssue) -> list[str]:
    return [
        f"- [{issue.severity.value}] {issue.issue_type}",
        f"  - 位置：{issue.location or '未提供'}",
        f"  - 原文：{issue.quote or '未提供'}",
        f"  - 风险：{issue.risk}",
        f"  - 建议：{issue.suggestion}",
        f"  - 是否阻断：{'是' if issue.blocking else '否'}",
    ]
