from __future__ import annotations

import json
from dataclasses import dataclass

from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.errors import SearchError
from xiaohongshu_auto_publish.llm.gateway import LLMClientProtocol, LLMRequest
from xiaohongshu_auto_publish.llm.prompts import PromptRegistry, default_prompt_registry
from xiaohongshu_auto_publish.models import ArtifactRef, SourceRecord, TaskMetadata, to_jsonable
from xiaohongshu_auto_publish.research.renderer import render_research_markdown, render_sources_markdown
from xiaohongshu_auto_publish.search.provider import SearchProvider, SearchResult
from xiaohongshu_auto_publish.source_policy.policy import SourcePolicy


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    task: TaskMetadata
    topic: str
    audience: str | None
    account_positioning: str | None = None


class ResearchService:
    def __init__(
        self,
        search_provider: SearchProvider,
        source_policy: SourcePolicy,
        llm_gateway: LLMClientProtocol,
        artifact_store: ArtifactStore,
        prompt_registry: PromptRegistry | None = None,
    ) -> None:
        self._search = search_provider
        self._policy = source_policy
        self._llm = llm_gateway
        self._artifacts = artifact_store
        self._prompts = prompt_registry or default_prompt_registry()

    def run(self, task: TaskMetadata) -> list[ArtifactRef]:
        queries = _queries_for_topic(task.topic)
        results: list[SearchResult] = []
        for query in queries:
            results.extend(self._search.search(query, max_results=5))
        if not results:
            partial = self._artifacts.save_partial(
                task.task_id,
                stage="research",
                kind="sources",
                body="# 来源清单\n\n搜索无结果，请补充权威来源。\n",
                error_type="search_no_results",
                retryable=True,
            )
            raise SearchError(
                "搜索无结果",
                "未检索到可用来源",
                retryable=True,
                related_artifacts=[self._artifacts.task_dir(task.task_id) / partial.path],
            )
        ranked = self._policy.rank(_dedupe(results))
        self._policy.require_authoritative_for_high_risk(task.topic, ranked)
        records = [self._to_source_record(item) for item in ranked]
        prompt = self._prompts.latest("research_summary")
        response = self._llm.complete(
            LLMRequest(
                system_prompt=prompt.template,
                user_prompt=json.dumps(to_jsonable(records), ensure_ascii=False),
                response_format="json",
            )
        )
        summary, facts, cautions = _parse_research_output(response.text)
        research = self._artifacts.save_markdown(
            task.task_id,
            stage="research",
            kind="research",
            body=render_research_markdown(task.topic, summary, facts, cautions),
            user_editable=True,
        )
        sources = self._artifacts.save_markdown(
            task.task_id,
            stage="research",
            kind="sources",
            body=render_sources_markdown(records),
            source_artifacts=[research.artifact_id],
            user_editable=True,
        )
        return [research, sources]

    def _to_source_record(self, result: SearchResult) -> SourceRecord:
        evaluation = self._policy.evaluate(result)
        return SourceRecord(
            url=result.url,
            title=result.title,
            organization=result.source_name or result.url,
            published_at=result.published_at,
            retrieved_at=result.retrieved_at,
            credibility=evaluation.credibility,
            relevance=evaluation.category,
            notes=evaluation.risk_note or evaluation.published_at_status,
        )


def _queries_for_topic(topic: str) -> list[str]:
    return [topic, f"{topic} 权威 指南", f"{topic} WHO CDC", f"{topic} 医院 科普"]


def _dedupe(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    unique: list[SearchResult] = []
    for item in results:
        if item.url in seen:
            continue
        seen.add(item.url)
        unique.append(item)
    return unique


def _parse_research_output(text: str) -> tuple[str, list[str], list[str]]:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        return text[:500] or "模型输出不完整", [], ["模型输出未能结构化解析，需人工复核"]
    if not isinstance(raw, dict):
        return "模型输出根结构异常", [], ["模型输出未能结构化解析，需人工复核"]
    return (
        str(raw.get("summary", "调研摘要待补充")),
        [str(item) for item in raw.get("facts", [])],
        [str(item) for item in raw.get("cautions", [])],
    )
