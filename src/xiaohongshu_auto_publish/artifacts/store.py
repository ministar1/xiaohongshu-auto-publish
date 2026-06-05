from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from filelock import FileLock, Timeout

from xiaohongshu_auto_publish.artifacts.front_matter import (
    parse_markdown,
    render_markdown,
)
from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import ArtifactError, LockError
from xiaohongshu_auto_publish.models import ArtifactRef, artifact_from_dict, now_iso, to_jsonable

ARTIFACTS_INDEX = "artifacts.jsonl"


@dataclass(frozen=True, slots=True)
class StoredMarkdownDocument:
    front_matter: dict[str, object]
    body: str
    artifact: ArtifactRef


class ArtifactStore:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self.workspace_dir = self._resolve_workspace()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def task_dir(self, task_id: str) -> Path:
        path = (self.workspace_dir / task_id).resolve()
        self._ensure_within_workspace(path)
        return path

    def save_markdown(
        self,
        task_id: str,
        stage: str,
        kind: str,
        body: str,
        front_matter: dict[str, object] | None = None,
        source_artifacts: Iterable[str] = (),
        user_editable: bool = True,
    ) -> ArtifactRef:
        return self._save(
            task_id=task_id,
            stage=stage,
            kind=kind,
            body=body,
            front_matter=dict(front_matter or {}),
            source_artifacts=list(source_artifacts),
            user_editable=user_editable,
            complete=True,
            error_type=None,
            retryable=None,
            extension="md",
        )

    def save_partial(
        self,
        task_id: str,
        stage: str,
        kind: str,
        body: str,
        error_type: str,
        retryable: bool,
        source_artifacts: Iterable[str] = (),
    ) -> ArtifactRef:
        front_matter = {"complete": False, "error_type": error_type, "retryable": retryable}
        return self._save(
            task_id=task_id,
            stage=stage,
            kind=kind,
            body=body,
            front_matter=front_matter,
            source_artifacts=list(source_artifacts),
            user_editable=True,
            complete=False,
            error_type=error_type,
            retryable=retryable,
            extension="md",
        )

    def save_json(
        self,
        task_id: str,
        stage: str,
        kind: str,
        payload: object,
        source_artifacts: Iterable[str] = (),
        complete: bool = True,
    ) -> ArtifactRef:
        body = json.dumps(payload, ensure_ascii=False, indent=2)
        return self._save(
            task_id=task_id,
            stage=stage,
            kind=kind,
            body=body,
            front_matter={},
            source_artifacts=list(source_artifacts),
            user_editable=False,
            complete=complete,
            error_type=None,
            retryable=None,
            extension="json",
        )

    def read_markdown(self, artifact: ArtifactRef | str | Path) -> StoredMarkdownDocument:
        ref = artifact if isinstance(artifact, ArtifactRef) else self._find_ref_by_path(Path(artifact))
        path = self._artifact_path(ref)
        try:
            parsed = parse_markdown(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ArtifactError("无法读取产物", str(path), related_artifacts=[path]) from exc
        return StoredMarkdownDocument(parsed.front_matter, parsed.body, ref)

    def latest(
        self,
        task_id: str,
        stage: str | None = None,
        kind: str | None = None,
        include_partial: bool = False,
    ) -> ArtifactRef | None:
        artifacts = self.list_artifacts(task_id, stage, kind, include_partial)
        if not artifacts:
            return None
        return max(artifacts, key=lambda ref: (ref.version, ref.created_at))

    def list_artifacts(
        self,
        task_id: str,
        stage: str | None = None,
        kind: str | None = None,
        include_partial: bool = False,
    ) -> list[ArtifactRef]:
        index = self.task_dir(task_id) / ARTIFACTS_INDEX
        if not index.exists():
            return []
        refs: list[ArtifactRef] = []
        try:
            lines = index.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ArtifactError("无法读取产物索引", str(index), related_artifacts=[index]) from exc
        for line in lines:
            if not line.strip():
                continue
            try:
                ref = artifact_from_dict(json.loads(line))
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                raise ArtifactError("产物索引损坏", f"{index}: {exc}", related_artifacts=[index]) from exc
            if stage is not None and ref.stage != stage:
                continue
            if kind is not None and ref.kind != kind:
                continue
            if not include_partial and not ref.complete:
                continue
            refs.append(ref)
        return refs

    def _save(
        self,
        task_id: str,
        stage: str,
        kind: str,
        body: str,
        front_matter: dict[str, object],
        source_artifacts: list[str],
        user_editable: bool,
        complete: bool,
        error_type: str | None,
        retryable: bool | None,
        extension: str,
    ) -> ArtifactRef:
        task_dir = self.task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        lock = FileLock(str(task_dir / "artifacts.lock"))
        attempted: list[int] = []
        try:
            with lock.acquire(timeout=10):
                for _ in range(8):
                    version = self._next_version(task_id, stage, kind)
                    attempted.append(version)
                    relative_path = Path(stage) / f"{kind}.v{version:03d}.{extension}"
                    target = (task_dir / relative_path).resolve()
                    self._ensure_within_workspace(target)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    artifact_id = f"{kind}-{version:03d}"
                    created_at = now_iso()
                    ref = ArtifactRef(
                        artifact_id=artifact_id,
                        task_id=task_id,
                        stage=stage,
                        kind=kind,
                        version=version,
                        path=str(relative_path).replace("\\", "/"),
                        created_at=created_at,
                        source_artifacts=source_artifacts,
                        user_editable=user_editable,
                        complete=complete,
                        error_type=error_type,
                        retryable=retryable,
                    )
                    full_front_matter = {
                        **front_matter,
                        "task_id": task_id,
                        "artifact_id": artifact_id,
                        "stage": stage,
                        "kind": kind,
                        "version": version,
                        "created_at": created_at,
                        "source_artifacts": source_artifacts,
                        "user_editable": user_editable,
                        "complete": complete,
                    }
                    if error_type is not None:
                        full_front_matter["error_type"] = error_type
                    if retryable is not None:
                        full_front_matter["retryable"] = retryable
                    content = render_markdown(full_front_matter, body) if extension == "md" else body
                    try:
                        with target.open("x", encoding="utf-8", newline="\n") as handle:
                            handle.write(content)
                            handle.flush()
                            os.fsync(handle.fileno())
                    except FileExistsError:
                        continue
                    except OSError as exc:
                        if target.exists():
                            target.unlink(missing_ok=True)
                        raise ArtifactError("产物写入失败", str(target), related_artifacts=[target]) from exc
                    self._append_index(task_dir, ref)
                    return ref
        except Timeout as exc:
            raise LockError("产物锁获取失败", str(task_dir / "artifacts.lock"), retryable=True) from exc
        raise ArtifactError(
            "产物版本冲突",
            f"已尝试版本: {attempted}",
            next_action="请稍后重试，或检查是否有并发写入任务",
        )

    def _next_version(self, task_id: str, stage: str, kind: str) -> int:
        refs = self.list_artifacts(task_id, stage=stage, kind=kind, include_partial=True)
        max_index = max((ref.version for ref in refs), default=0)
        stage_dir = self.task_dir(task_id) / stage
        if stage_dir.exists():
            for path in stage_dir.glob(f"{kind}.v*.*"):
                parts = path.name.split(".")
                if len(parts) >= 3 and parts[1].startswith("v"):
                    try:
                        max_index = max(max_index, int(parts[1][1:]))
                    except ValueError:
                        continue
        return max_index + 1

    def _append_index(self, task_dir: Path, ref: ArtifactRef) -> None:
        index = task_dir / ARTIFACTS_INDEX
        with index.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(to_jsonable(ref), ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _find_ref_by_path(self, path: Path) -> ArtifactRef:
        resolved = path.resolve()
        self._ensure_within_workspace(resolved)
        for task_dir in self.workspace_dir.iterdir():
            if not task_dir.is_dir():
                continue
            for ref in self.list_artifacts(task_dir.name, include_partial=True):
                if self._artifact_path(ref).resolve() == resolved:
                    return ref
        raise ArtifactError("产物未索引", str(path), related_artifacts=[path])

    def _artifact_path(self, ref: ArtifactRef) -> Path:
        path = (self.task_dir(ref.task_id) / ref.path).resolve()
        self._ensure_within_workspace(path)
        return path

    def _resolve_workspace(self) -> Path:
        path = Path(self._config.storage.workspace_dir)
        if not path.is_absolute():
            path = self._config.project_root / path
        return path.resolve()

    def _ensure_within_workspace(self, path: Path) -> None:
        try:
            path.resolve().relative_to(self.workspace_dir)
        except ValueError as exc:
            raise ArtifactError("路径越界", f"{path} 不在工作区内", related_artifacts=[path]) from exc
