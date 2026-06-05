from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from xiaohongshu_auto_publish.assets.lock import LockFile
from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.models import now_iso, to_jsonable


@dataclass(frozen=True, slots=True)
class AssetRecord:
    task_id: str
    account_id: str
    topic: str
    title: str
    hashtags: list[str]
    series: str | None
    created_at: str
    review_summary: str


class AssetLibrary:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._workspace = self._resolve_workspace()
        self._workspace.mkdir(parents=True, exist_ok=True)

    def append(self, record: AssetRecord, timeout_seconds: float = 10) -> None:
        path = self._index_path(record.account_id)
        lock = LockFile(path.with_suffix(path.suffix + ".lock"))
        with lock.acquire(timeout_seconds), path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(to_jsonable(record), ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def list_by_account(self, account_id: str) -> list[AssetRecord]:
        return self._read_index(account_id)

    def search(self, keyword: str, account_id: str | None = None) -> list[AssetRecord]:
        records = self._read_index(account_id) if account_id else self._read_all()
        return [
            item
            for item in records
            if keyword.lower() in item.topic.lower()
            or keyword.lower() in item.title.lower()
            or any(keyword.lower() in tag.lower() for tag in item.hashtags)
        ]

    def record_from_package(
        self,
        task_id: str,
        account_id: str,
        topic: str,
        title: str,
        hashtags: list[str],
        review_summary: str,
        series: str | None = None,
    ) -> AssetRecord:
        return AssetRecord(task_id, account_id, topic, title, hashtags, series, now_iso(), review_summary)

    def _read_all(self) -> list[AssetRecord]:
        records: list[AssetRecord] = []
        for path in self._workspace.glob("assets_index.*.jsonl"):
            account_id = path.name.removeprefix("assets_index.").removesuffix(".jsonl")
            records.extend(self._read_index(account_id))
        return records

    def _read_index(self, account_id: str | None) -> list[AssetRecord]:
        if account_id is None:
            return []
        path = self._index_path(account_id)
        if not path.exists():
            return []
        records: list[AssetRecord] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            records.append(
                AssetRecord(
                    task_id=str(raw["task_id"]),
                    account_id=str(raw["account_id"]),
                    topic=str(raw["topic"]),
                    title=str(raw["title"]),
                    hashtags=[str(item) for item in raw.get("hashtags", [])],
                    series=str(raw["series"]) if raw.get("series") is not None else None,
                    created_at=str(raw["created_at"]),
                    review_summary=str(raw.get("review_summary", "")),
                )
            )
        return records

    def _index_path(self, account_id: str) -> Path:
        safe = account_id.replace("/", "_").replace("\\", "_")
        return self._workspace / f"assets_index.{safe}.jsonl"

    def _resolve_workspace(self) -> Path:
        path = Path(self._config.storage.workspace_dir)
        if not path.is_absolute():
            path = self._config.project_root / path
        return path.resolve()
