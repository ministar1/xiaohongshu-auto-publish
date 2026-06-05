from __future__ import annotations

from tests.factories import task
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.errors import MediaValidationError
from xiaohongshu_auto_publish.package.builder import PackageBuilder
from xiaohongshu_auto_publish.rules.format_rules import FormatRules
from xiaohongshu_auto_publish.state.store import StateStore


def test_package_builder_success_without_required_media(app_config: object) -> None:
    metadata = StateStore(app_config).create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    artifacts.save_markdown("task-1", "drafts", "revised", "# 标题\n正文 #健康 #科普")
    package, refs = PackageBuilder(artifacts, FormatRules.load(app_config)).build(metadata, user_confirmed=True)
    assert package.can_publish
    assert len(refs) == 2


def test_package_builder_fails_when_required_cover_missing(app_config: object) -> None:
    app_config.format_rules.config_path = "missing.toml"
    rules = FormatRules.load(app_config)
    rules.require_cover = True
    metadata = StateStore(app_config).create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    artifacts.save_markdown("task-1", "drafts", "revised", "# 标题\n正文")
    try:
        PackageBuilder(artifacts, rules).build(metadata, user_confirmed=True)
    except MediaValidationError as exc:
        assert exc.stage == "package"
