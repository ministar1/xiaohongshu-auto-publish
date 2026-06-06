from __future__ import annotations

from tests.factories import task
from xiaohongshu_auto_publish.account.profile import AccountProfileService
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.llm.gateway import FakeLLMGateway
from xiaohongshu_auto_publish.review.writing import WritingReviewService
from xiaohongshu_auto_publish.state.store import StateStore


def test_writing_review_outputs_revised_and_report(app_config: object) -> None:
    metadata = StateStore(app_config).create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    artifacts.save_markdown("task-1", "drafts", "draft", "# 标题\n正文")
    service = WritingReviewService(
        app_config,
        FakeLLMGateway(
            ['{"title_candidates":["标题1"],"body":"正文 #健康","hashtags":["健康"],"opening_notes":"开头","account_fit":"一致"}']
        ),
        artifacts,
        AccountProfileService(app_config),
    )
    refs = service.review(metadata)
    assert [ref.kind for ref in refs] == ["revised", "writing_review"]


def test_writing_review_keeps_string_confirmation_as_one_item(app_config: object) -> None:
    metadata = StateStore(app_config).create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    artifacts.save_markdown("task-1", "drafts", "draft", "# 标题\n正文")
    service = WritingReviewService(
        app_config,
        FakeLLMGateway(['{"title_candidates":"标题1","body":"正文 #健康","hashtags":"健康","confirmation_required":"确认医学表达"}']),
        artifacts,
        AccountProfileService(app_config),
    )
    refs = service.review(metadata)
    revised = artifacts.read_markdown(refs[0])
    assert "- 确认医学表达" in revised.body
    assert "- 确\n" not in revised.body


def test_writing_review_merges_character_arrays_before_rendering(app_config: object) -> None:
    metadata = StateStore(app_config).create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    artifacts.save_markdown("task-1", "drafts", "draft", "# 标题\n正文")
    service = WritingReviewService(
        app_config,
        FakeLLMGateway(
            [
                (
                    '{"title_candidates":["标题1"],"body":"正文 #健康","hashtags":["健康"],'
                    '"series_suggestions":["后","续","选","题"],'
                    '"changes":["1","."," ","改","写","；","2","."," ","补","充"],'
                    '"confirmation_required":["确","认","1","：","医","学","表","达","；","确","认","2","：","平","台","规","范"]}'
                )
            ]
        ),
        artifacts,
        AccountProfileService(app_config),
    )
    refs = service.review(metadata)
    revised = artifacts.read_markdown(refs[0])
    report = artifacts.read_markdown(refs[1])

    assert "- 确认1：医学表达" in revised.body
    assert "- 确认2：平台规范" in revised.body
    assert "- 后续选题" in report.body
    assert "- 1. 改写" in report.body
    assert "- 2. 补充" in report.body
    assert "- 确\n" not in revised.body
    assert "- 后\n" not in report.body
