from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import StateError
from xiaohongshu_auto_publish.models import ArtifactRef, TaskMetadata, TaskStatus, WritingStyle, now_iso
from xiaohongshu_auto_publish.state.store import StateStore, generate_task_id, slugify


@dataclass(frozen=True, slots=True)
class TopicInputRequest:
    topic: str
    account_id: str = "default"
    style: WritingStyle = WritingStyle.POPULAR
    audience: str | None = None
    length: str = "medium"
    series: bool = False
    slug: str | None = None


@dataclass(frozen=True, slots=True)
class ArticleInputRequest:
    article_path: Path | None = None
    pasted_text: str | None = None
    topic: str | None = None
    account_id: str = "default"
    style: WritingStyle = WritingStyle.POPULAR
    audience: str | None = None
    slug: str | None = None


@dataclass(frozen=True, slots=True)
class NormalizedInput:
    task: TaskMetadata
    artifact: ArtifactRef
    slug_hint: str | None = None


class InputNormalizer:
    def __init__(self, config: AppConfig, state_store: StateStore, artifact_store: ArtifactStore) -> None:
        self._config = config
        self._state_store = state_store
        self._artifact_store = artifact_store

    def create_topic(self, request: TopicInputRequest) -> NormalizedInput:
        topic = request.topic.strip()
        if not topic:
            raise StateError("选题不能为空", "请提供非空 topic")
        task, slug_hint = self._new_task(
            input_type="topic",
            topic=topic,
            account_id=request.account_id,
            style=request.style,
            audience=request.audience,
            slug=request.slug or topic,
        )
        self._state_store.create_task(task)
        body = (
            f"# 选题说明\n\n"
            f"选题：{topic}\n\n"
            f"目标受众：{request.audience or '未指定'}\n\n"
            f"篇幅：{request.length}\n\n"
            f"系列化：{'是' if request.series else '否'}\n"
        )
        artifact = self._artifact_store.save_markdown(
            task.task_id,
            stage="inputs",
            kind="topic",
            body=body,
            user_editable=True,
        )
        task.current_artifacts["topic"] = artifact.artifact_id
        return NormalizedInput(task=task, artifact=artifact, slug_hint=slug_hint)

    def create_article(self, request: ArticleInputRequest) -> NormalizedInput:
        text = self._read_article_text(request)
        topic = request.topic or _derive_topic(request.article_path) or "导入文章"
        task, slug_hint = self._new_task(
            input_type="article",
            topic=topic,
            account_id=request.account_id,
            style=request.style,
            audience=request.audience,
            slug=request.slug or topic,
            status=TaskStatus.CREATED,
        )
        self._state_store.create_task(task)
        artifact = self._artifact_store.save_markdown(
            task.task_id,
            stage="drafts",
            kind="draft",
            body=text,
            front_matter={"source_path": str(request.article_path) if request.article_path else None},
            user_editable=True,
        )
        task.current_artifacts["draft"] = artifact.artifact_id
        return NormalizedInput(task=task, artifact=artifact, slug_hint=slug_hint)

    def _new_task(
        self,
        input_type: str,
        topic: str,
        account_id: str,
        style: WritingStyle,
        audience: str | None,
        slug: str,
        status: TaskStatus = TaskStatus.CREATED,
    ) -> tuple[TaskMetadata, str | None]:
        task_id, _attempted = generate_task_id(self._state_store.workspace_dir, slug)
        created_at = now_iso()
        normalized_slug = slugify(slug)
        slug_hint = "可使用 --slug 指定更清晰的英文短名" if normalized_slug == "topic" else None
        return (
            TaskMetadata(
                task_id=task_id,
                input_type=input_type,
                topic=topic,
                account_id=account_id,
                style=style,
                audience=audience,
                status=status,
                created_at=created_at,
                updated_at=created_at,
            ),
            slug_hint,
        )

    def _read_article_text(self, request: ArticleInputRequest) -> str:
        if request.pasted_text is not None and request.pasted_text.strip():
            return request.pasted_text
        if request.article_path is None:
            raise StateError("缺少文章输入", "请提供 Markdown 文件路径或粘贴正文")
        path = request.article_path
        if not path.is_absolute():
            path = self._config.project_root / path
        if not path.exists():
            raise StateError(
                "文章文件不存在",
                str(path),
                next_action="检查路径后重新执行 xhs-agent import",
                related_artifacts=[path],
            )
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StateError("无法读取文章文件", str(path), related_artifacts=[path]) from exc


def _derive_topic(path: Path | None) -> str | None:
    return path.stem if path is not None else None
