from __future__ import annotations

from xiaohongshu_auto_publish.account.profile import AccountProfileService
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.config.loader import check_required_secrets
from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.input.normalizer import InputNormalizer
from xiaohongshu_auto_publish.llm.gateway import LLMGateway
from xiaohongshu_auto_publish.orchestration.orchestrator import WorkflowOrchestrator
from xiaohongshu_auto_publish.package.builder import PackageBuilder
from xiaohongshu_auto_publish.research.service import ResearchService
from xiaohongshu_auto_publish.review.content import ContentReviewService
from xiaohongshu_auto_publish.review.format import FormatReviewService
from xiaohongshu_auto_publish.review.writing import WritingReviewService
from xiaohongshu_auto_publish.rules.format_rules import FormatRules
from xiaohongshu_auto_publish.search.tavily_provider import TavilySearchProvider
from xiaohongshu_auto_publish.source_policy.policy import SourcePolicy
from xiaohongshu_auto_publish.state.store import StateStore


def build_orchestrator(config: AppConfig) -> WorkflowOrchestrator:
    state_store = StateStore(config)
    artifact_store = ArtifactStore(config)
    normalizer = InputNormalizer(config, state_store, artifact_store)
    account_service = AccountProfileService(config)
    format_rules = FormatRules.load(config)
    format_review = FormatReviewService(artifact_store, format_rules)
    package_builder = PackageBuilder(artifact_store, format_rules)

    if check_required_secrets(config):
        return WorkflowOrchestrator(
            state_store=state_store,
            artifact_store=artifact_store,
            normalizer=normalizer,
            format_review_service=format_review,
            package_builder=package_builder,
        )

    llm_gateway = LLMGateway(config)
    source_policy = SourcePolicy(config)
    return WorkflowOrchestrator(
        state_store=state_store,
        artifact_store=artifact_store,
        normalizer=normalizer,
        research_service=ResearchService(
            TavilySearchProvider(config),
            source_policy,
            llm_gateway,
            artifact_store,
        ),
        content_review_service=ContentReviewService(llm_gateway, artifact_store),
        writing_review_service=WritingReviewService(config, llm_gateway, artifact_store, account_service),
        format_review_service=format_review,
        package_builder=package_builder,
    )


def build_account_service(config: AppConfig) -> AccountProfileService:
    return AccountProfileService(config)
