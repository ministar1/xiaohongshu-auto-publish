from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import ConfigError


class RuleSeverity(StrEnum):
    BLOCK = "block"
    CONFIRM = "confirm"
    WARN = "warn"


@dataclass(frozen=True, slots=True)
class RuleIssue:
    location: str
    rule_id: str
    severity: RuleSeverity
    message: str
    suggestion: str
    auto_fixable: bool = False


@dataclass(frozen=True, slots=True)
class SensitiveWordRule:
    word: str
    severity: RuleSeverity
    reason: str


@dataclass(slots=True)
class FormatRules:
    title_max_length: int = 40
    title_severity: RuleSeverity = RuleSeverity.CONFIRM
    body_max_length: int = 1200
    paragraph_max_length: int = 120
    body_severity: RuleSeverity = RuleSeverity.WARN
    hashtag_min_count: int = 2
    hashtag_max_count: int = 8
    hashtag_severity: RuleSeverity = RuleSeverity.CONFIRM
    emoji_max_count: int = 20
    emoji_severity: RuleSeverity = RuleSeverity.WARN
    media_min_items: int = 0
    media_max_items: int = 9
    require_cover: bool = False
    sensitive_words: list[SensitiveWordRule] = field(default_factory=list)

    @classmethod
    def load(cls, config: AppConfig) -> FormatRules:
        path = Path(config.format_rules.config_path)
        if not path.is_absolute():
            path = config.project_root / path
        if not path.exists():
            return cls(
                sensitive_words=[
                    SensitiveWordRule("根治", RuleSeverity.BLOCK, "医学健康内容不得承诺根治"),
                    SensitiveWordRule("保证有效", RuleSeverity.BLOCK, "不得承诺疗效"),
                ]
            )
        try:
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError("格式规则 TOML 格式错误", f"{path}: {exc}", related_artifacts=[path]) from exc
        return _rules_from_raw(raw, path)

    def check_text(self, title: str, body: str, hashtags: list[str]) -> list[RuleIssue]:
        issues: list[RuleIssue] = []
        if len(title) > self.title_max_length:
            issues.append(RuleIssue("title", "title.max_length", self.title_severity, "标题过长", "缩短标题"))
        if len(body) > self.body_max_length:
            issues.append(RuleIssue("body", "body.max_length", self.body_severity, "正文过长", "压缩正文"))
        for index, paragraph in enumerate(body.splitlines(), start=1):
            if len(paragraph) > self.paragraph_max_length:
                issues.append(
                    RuleIssue(
                        f"body.paragraph[{index}]",
                        "body.paragraph_max_length",
                        self.body_severity,
                        "段落过长",
                        "拆分段落",
                        True,
                    )
                )
        if not (self.hashtag_min_count <= len(hashtags) <= self.hashtag_max_count):
            issues.append(
                RuleIssue(
                    "hashtags",
                    "hashtags.count",
                    self.hashtag_severity,
                    "话题标签数量不符合规则",
                    "调整标签数量",
                )
            )
        emoji_count = len(re.findall(r"[\U0001F300-\U0001FAFF]", title + body))
        if emoji_count > self.emoji_max_count:
            issues.append(RuleIssue("body", "emoji.max_count", self.emoji_severity, "表情过多", "减少表情"))
        for rule in self.sensitive_words:
            if rule.word in title or rule.word in body:
                issues.append(
                    RuleIssue(
                        "text",
                        f"sensitive.{rule.word}",
                        rule.severity,
                        rule.reason,
                        f"删除或替换“{rule.word}”",
                    )
                )
        return issues


def _rules_from_raw(raw: dict[str, object], path: Path) -> FormatRules:
    try:
        title = _table(raw, "title")
        body = _table(raw, "body")
        hashtags = _table(raw, "hashtags")
        emoji = _table(raw, "emoji")
        media = _table(raw, "media")
        sensitive = raw.get("sensitive_words", [])
        if not isinstance(sensitive, list):
            raise TypeError("sensitive_words must be list")
        return FormatRules(
            title_max_length=_positive_int(title.get("max_length", 40), "title.max_length"),
            title_severity=_severity(title.get("severity", "confirm")),
            body_max_length=_positive_int(body.get("max_length", 1200), "body.max_length"),
            paragraph_max_length=_positive_int(body.get("max_paragraph_length", 120), "body.max_paragraph_length"),
            body_severity=_severity(body.get("severity", "warn")),
            hashtag_min_count=_non_negative_int(hashtags.get("min_count", 2), "hashtags.min_count"),
            hashtag_max_count=_positive_int(hashtags.get("max_count", 8), "hashtags.max_count"),
            hashtag_severity=_severity(hashtags.get("severity", "confirm")),
            emoji_max_count=_non_negative_int(emoji.get("max_count", 20), "emoji.max_count"),
            emoji_severity=_severity(emoji.get("severity", "warn")),
            media_min_items=_non_negative_int(media.get("min_items", 0), "media.min_items"),
            media_max_items=_positive_int(media.get("max_items", 9), "media.max_items"),
            require_cover=bool(media.get("require_cover", False)),
            sensitive_words=[_sensitive_rule(item) for item in sensitive],
        )
    except (TypeError, ValueError) as exc:
        raise ConfigError("格式规则字段错误", f"{path}: {exc}", related_artifacts=[path]) from exc


def _table(raw: dict[str, object], key: str) -> dict[str, object]:
    value = raw.get(key, {})
    if not isinstance(value, dict):
        raise TypeError(f"{key} must be table")
    return value


def _severity(value: object) -> RuleSeverity:
    return RuleSeverity(str(value))


def _positive_int(value: object, name: str) -> int:
    result = _coerce_int(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _non_negative_int(value: object, name: str) -> int:
    result = _coerce_int(value, name)
    if result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _coerce_int(value: object, name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be int")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError(f"{name} must be int")


def _sensitive_rule(value: object) -> SensitiveWordRule:
    if not isinstance(value, dict):
        raise TypeError("sensitive_words item must be table")
    return SensitiveWordRule(
        word=str(value["word"]),
        severity=_severity(value.get("severity", "block")),
        reason=str(value.get("reason", "")),
    )
