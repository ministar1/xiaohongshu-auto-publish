from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import ConfigError, SearchError
from xiaohongshu_auto_publish.search.provider import SearchResult

TRUSTED_DEFAULTS = {
    "who.int": ("public_health", 1),
    "cdc.gov": ("public_health", 1),
    "nih.gov": ("medical_institution", 2),
    "fda.gov": ("health_authority", 1),
    "nhs.uk": ("medical_institution", 2),
    "nhc.gov.cn": ("health_authority", 1),
}
HIGH_RISK_KEYWORDS = ("治疗", "药", "剂量", "诊断", "孕", "儿童", "慢病", "高血压", "糖尿病")


@dataclass(frozen=True, slots=True)
class SourceEvaluation:
    category: str
    credibility: str
    priority: int
    risk_note: str
    published_at_status: str
    authoritative: bool


class SourcePolicy:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._trusted, self._risk = self._load_rules()

    def evaluate(self, source: SearchResult) -> SourceEvaluation:
        domain = _domain(source.url)
        published_status = "known" if source.published_at else "published_at_unknown"
        if domain in self._risk:
            return SourceEvaluation("risk", "low", 99, self._risk[domain], published_status, False)
        if domain in self._trusted:
            category, priority = self._trusted[domain]
            return SourceEvaluation(category, "high", priority, "", published_status, True)
        parent = _trusted_parent(domain, self._trusted)
        if parent:
            category, priority = self._trusted[parent]
            return SourceEvaluation(category, "high", priority, "", published_status, True)
        return SourceEvaluation("unknown", "unknown", 50, "来源可信度不足", published_status, False)

    def rank(self, sources: list[SearchResult]) -> list[SearchResult]:
        return sorted(
            sources,
            key=lambda item: (
                0 if self.evaluate(item).authoritative else 1,
                self.evaluate(item).priority,
                item.title,
            ),
        )

    def require_authoritative_for_high_risk(self, topic: str, sources: list[SearchResult]) -> None:
        if not is_high_risk_topic(topic):
            return
        if sources and any(self.evaluate(item).authoritative for item in sources):
            return
        raise SearchError(
            "高风险主题缺少权威来源",
            "疾病治疗、药物、剂量、诊断、孕产、儿童或慢病主题至少需要权威来源",
            retryable=True,
            stage="research",
            next_action="编辑 sources.vNNN.md 的用户补充来源小节后重试",
        )

    def _load_rules(self) -> tuple[dict[str, tuple[str, int]], dict[str, str]]:
        path = Path(self._config.source_policy.config_path)
        if not path.is_absolute():
            path = self._config.project_root / path
        if not path.exists():
            return dict(TRUSTED_DEFAULTS), {}
        try:
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError("来源策略 TOML 格式错误", f"{path}: {exc}", related_artifacts=[path]) from exc
        trusted: dict[str, tuple[str, int]] = {}
        for domain, value in _dict(raw.get("trusted_sources")).items():
            if not isinstance(value, dict):
                raise ConfigError("来源策略字段类型错误", f"{domain} 必须是 table", related_artifacts=[path])
            trusted[str(domain)] = (str(value.get("category", "trusted")), int(value.get("priority", 10)))
        risk = {str(key): str(value) for key, value in _dict(raw.get("risk_sources")).items()}
        return trusted, risk


def is_high_risk_topic(topic: str) -> bool:
    return any(keyword in topic for keyword in HIGH_RISK_KEYWORDS)


def _domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().removeprefix("www.")


def _trusted_parent(domain: str, trusted: dict[str, tuple[str, int]]) -> str | None:
    for item in trusted:
        if domain.endswith("." + item):
            return item
    return None


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}
