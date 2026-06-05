from __future__ import annotations

from dataclasses import dataclass

from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.media.manifest import MediaManifest, MediaValidationStage
from xiaohongshu_auto_publish.models import TaskMetadata
from xiaohongshu_auto_publish.orchestration.orchestrator import FormatReviewResult
from xiaohongshu_auto_publish.post_fields import extract_post_fields
from xiaohongshu_auto_publish.rules.format_rules import FormatRules, RuleSeverity


@dataclass(frozen=True, slots=True)
class FormatReviewIssue:
    location: str
    rule_id: str
    severity: RuleSeverity
    message: str
    suggestion: str
    auto_fixable: bool = False


class FormatReviewService:
    def __init__(self, artifact_store: ArtifactStore, rules: FormatRules) -> None:
        self._artifacts = artifact_store
        self._rules = rules

    def review(self, task: TaskMetadata) -> FormatReviewResult:
        source = self._artifacts.latest(task.task_id, stage="drafts", kind="revised") or self._artifacts.latest(
            task.task_id, stage="drafts", kind="draft"
        )
        if source is None:
            report = self._artifacts.save_partial(
                task.task_id,
                "reviews",
                "format_review",
                "# 格式审核报告\n\n缺少可审核稿件。\n",
                "missing_draft",
                True,
            )
            return FormatReviewResult(True, False, ["缺少可审核稿件"], [report])
        doc = self._artifacts.read_markdown(source)
        fields = extract_post_fields(doc.body)
        rule_issues = self._rules.check_text(fields.title, fields.body, fields.hashtags)
        manifest = MediaManifest.load(self._artifacts.task_dir(task.task_id))
        media_result = manifest.validate(MediaValidationStage.FORMAT, require_cover=self._rules.require_cover)
        issues = [
            FormatReviewIssue(
                item.location,
                item.rule_id,
                item.severity,
                item.message,
                item.suggestion,
                item.auto_fixable,
            )
            for item in rule_issues
        ]
        for item in media_result.issues:
            severity = RuleSeverity.WARN if item.severity == "warn" else RuleSeverity.BLOCK
            issues.append(FormatReviewIssue(item.path, "media.validation", severity, item.message, "检查素材"))
        blocked = any(item.severity == RuleSeverity.BLOCK for item in issues)
        requires_confirmation = any(item.severity == RuleSeverity.CONFIRM for item in issues)
        report = self._artifacts.save_markdown(
            task.task_id,
            "reviews",
            "format_review",
            _render_format_report(fields.title, fields.body, fields.hashtags, fields.cover_title, issues),
            source_artifacts=[source.artifact_id],
            user_editable=True,
        )
        return FormatReviewResult(
            blocked=blocked,
            requires_confirmation=requires_confirmation,
            warnings=[item.message for item in issues if item.severity == RuleSeverity.WARN],
            artifacts=[report],
        )


def _render_format_report(
    title: str,
    body: str,
    hashtags: list[str],
    cover_title: str,
    issues: list[FormatReviewIssue],
) -> str:
    lines = [
        "# 格式审核报告",
        "",
        f"标题：{title}",
        f"正文长度：{len(body)}",
        f"标签：{' '.join('#' + tag for tag in hashtags)}",
        f"封面标题：{cover_title}",
        "",
        "## 规则命中",
        "",
    ]
    if not issues:
        lines.append("- 未发现格式问题")
    for issue in issues:
        lines.append(f"- [{issue.severity.value}] {issue.rule_id} @ {issue.location}: {issue.message}；建议：{issue.suggestion}")
    return "\n".join(lines) + "\n"
