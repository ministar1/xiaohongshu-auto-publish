from __future__ import annotations

from dataclasses import dataclass

from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.errors import MediaValidationError
from xiaohongshu_auto_publish.media.manifest import MediaManifest, MediaValidationStage
from xiaohongshu_auto_publish.models import ArtifactRef, PublishPackage, TaskMetadata
from xiaohongshu_auto_publish.post_fields import extract_post_fields
from xiaohongshu_auto_publish.rules.format_rules import FormatRules


@dataclass(frozen=True, slots=True)
class PublishManifest:
    package: PublishPackage
    media_issues: list[str]


class PackageBuilder:
    def __init__(self, artifact_store: ArtifactStore, rules: FormatRules) -> None:
        self._artifacts = artifact_store
        self._rules = rules

    def build(self, task: TaskMetadata, user_confirmed: bool = False) -> tuple[PublishPackage, list[ArtifactRef]]:
        source = self._artifacts.latest(task.task_id, stage="drafts", kind="revised") or self._artifacts.latest(
            task.task_id, stage="drafts", kind="draft"
        )
        if source is None:
            raise MediaValidationError("缺少发布稿件", "没有 revised 或 draft 产物", retryable=True)
        doc = self._artifacts.read_markdown(source)
        fields = extract_post_fields(doc.body)
        manifest = MediaManifest.load(self._artifacts.task_dir(task.task_id))
        media_result = manifest.validate(MediaValidationStage.PACKAGE, require_cover=self._rules.require_cover)
        media_validation_passed = media_result.passed
        can_publish = media_validation_passed and user_confirmed
        package = PublishPackage(
            title=fields.title,
            body=fields.body,
            hashtags=fields.hashtags,
            media_items=manifest.items,
            cover_title=fields.cover_title,
            source_records=[],
            review_summary="内容审核和格式审核摘要请见 reviews/ 目录",
            media_validation_passed=media_validation_passed,
            user_confirmed=user_confirmed,
            can_publish=can_publish,
        )
        markdown = self._render_final_package(package, [issue.message for issue in media_result.issues])
        final_ref = self._artifacts.save_markdown(
            task.task_id,
            "package",
            "final_package",
            markdown,
            source_artifacts=[source.artifact_id],
            user_editable=False,
        )
        manifest_ref = self._artifacts.save_json(
            task.task_id,
            "package",
            "publish_manifest",
            {
                "title": package.title,
                "body": package.body,
                "hashtags": package.hashtags,
                "cover_title": package.cover_title,
                "media_validation_passed": package.media_validation_passed,
                "user_confirmed": package.user_confirmed,
                "can_publish": package.can_publish,
                "media_issues": [issue.__dict__ if hasattr(issue, "__dict__") else str(issue) for issue in media_result.issues],
            },
            source_artifacts=[final_ref.artifact_id],
            complete=True,
        )
        if not media_validation_passed:
            raise MediaValidationError(
                "素材复验失败",
                "发布包生成前素材硬校验未通过",
                retryable=True,
                stage="package",
            )
        return package, [final_ref, manifest_ref]

    def _render_final_package(self, package: PublishPackage, media_issues: list[str]) -> str:
        return (
            "# 最终发布包\n\n"
            f"## 标题\n\n{package.title}\n\n"
            f"## 正文\n\n{package.body}\n\n"
            f"## 标签\n\n{' '.join('#' + tag.lstrip('#') for tag in package.hashtags)}\n\n"
            f"## 封面标题\n\n{package.cover_title}\n\n"
            f"## 发布许可\n\ncan_publish: {str(package.can_publish).lower()}\n\n"
            f"media_validation_passed: {str(package.media_validation_passed).lower()}\n\n"
            "## 素材问题\n\n" + ("\n".join(f"- {item}" for item in media_issues) if media_issues else "- 无") + "\n"
        )
