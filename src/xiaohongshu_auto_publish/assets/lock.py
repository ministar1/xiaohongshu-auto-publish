from __future__ import annotations

from pathlib import Path
from types import TracebackType

from filelock import FileLock, Timeout

from xiaohongshu_auto_publish.errors import LockError


class LockHandle:
    def __init__(self, lock: FileLock) -> None:
        self._lock = lock

    def __enter__(self) -> LockHandle:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._lock.release()


class LockFile:
    def __init__(self, path: Path) -> None:
        self._lock = FileLock(str(path))

    def acquire(self, timeout_seconds: float = 10) -> LockHandle:
        try:
            self._lock.acquire(timeout=timeout_seconds)
        except Timeout as exc:
            raise LockError("锁获取超时", str(self._lock.lock_file), retryable=True) from exc
        return LockHandle(self._lock)
