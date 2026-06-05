from __future__ import annotations

from pathlib import Path

from xiaohongshu_auto_publish.models import PublishPackage
from xiaohongshu_auto_publish.publish.base import PublishResult


class ManualPublisher:
    channel = "manual"

    def __init__(self, raw_artifact_path: Path | None = None) -> None:
        self._raw_artifact_path = raw_artifact_path

    def publish(self, package: PublishPackage, confirmed: bool) -> PublishResult:
        if not confirmed:
            return PublishResult(
                success=False,
                channel=self.channel,
                message="发布前必须明确确认",
                retryable=False,
                raw_artifact_path=self._raw_artifact_path,
            )
        if not package.can_publish:
            return PublishResult(
                success=False,
                channel=self.channel,
                message="发布包 can_publish=false，不能发布",
                retryable=True,
                raw_artifact_path=self._raw_artifact_path,
            )
        return PublishResult(
            success=True,
            channel=self.channel,
            message="请按最终发布包手动复制标题、正文、标签和素材到小红书发布页面",
            retryable=False,
            raw_artifact_path=self._raw_artifact_path,
        )
