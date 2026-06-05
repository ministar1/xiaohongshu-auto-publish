from __future__ import annotations

from xiaohongshu_auto_publish.models import PublishPackage
from xiaohongshu_auto_publish.publish.manual import ManualPublisher


def _package(can_publish: bool) -> PublishPackage:
    return PublishPackage(
        title="标题",
        body="正文",
        hashtags=[],
        media_items=[],
        cover_title="封面",
        source_records=[],
        review_summary="通过",
        media_validation_passed=True,
        user_confirmed=can_publish,
        can_publish=can_publish,
    )


def test_manual_publisher_rejects_unconfirmed_and_cannot_publish() -> None:
    publisher = ManualPublisher()
    assert not publisher.publish(_package(True), confirmed=False).success
    assert not publisher.publish(_package(False), confirmed=True).success


def test_manual_publisher_success_is_manual_only() -> None:
    result = ManualPublisher().publish(_package(True), confirmed=True)
    assert result.success
    assert result.channel == "manual"
    assert "手动" in result.message
