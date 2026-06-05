from __future__ import annotations

from tests.factories import task
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.llm.gateway import FakeLLMGateway
from xiaohongshu_auto_publish.research.service import ResearchService
from xiaohongshu_auto_publish.search.provider import FakeSearchProvider, result_from_url
from xiaohongshu_auto_publish.source_policy.policy import SourcePolicy
from xiaohongshu_auto_publish.state.store import StateStore


def test_research_outputs_sources_with_unknown_date(app_config: object) -> None:
    state = StateStore(app_config)
    metadata = state.create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    service = ResearchService(
        FakeSearchProvider([result_from_url("https://www.who.int/a", "WHO", "WHO")]),
        SourcePolicy(app_config),
        FakeLLMGateway(['{"summary":"摘要","facts":["事实"],"cautions":["谨慎"]}']),
        artifacts,
    )
    refs = service.run(metadata)
    source_doc = artifacts.read_markdown(refs[1])
    assert "发布日期未知" in source_doc.body
    assert "用户补充来源" in source_doc.body
