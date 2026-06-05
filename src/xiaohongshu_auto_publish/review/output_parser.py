from __future__ import annotations

import json
import re
from typing import Any

from xiaohongshu_auto_publish.errors import (
    StructuredOutputRiskFieldError,
    StructuredOutputSchemaError,
)
from xiaohongshu_auto_publish.models import ParseStatus, ReviewIssue, ReviewReport, Severity, now_iso

CRITICAL_ISSUE_FIELDS = ("issue_type", "severity", "risk", "blocking", "suggestion")


def parse_content_review_output(
    text: str,
    task_id: str,
    model: str,
    source_artifacts: list[str],
) -> ReviewReport:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        return ReviewReport(
            task_id=task_id,
            stage="content",
            issues=[],
            blocking=True,
            summary="内容审核输出无法解析",
            model=model,
            created_at=now_iso(),
            source_artifacts=source_artifacts,
            raw_output_excerpt=_safe_excerpt(text),
            parse_status=ParseStatus.FAILED,
            parse_warnings=[str(exc)],
        )
    if not isinstance(raw, dict):
        raise StructuredOutputSchemaError("结构化输出根结构错误", "根对象必须是 JSON object")
    for field in ("summary", "blocking", "issues"):
        if field not in raw:
            raise StructuredOutputSchemaError("结构化输出缺少必填字段", field)
    if not isinstance(raw["issues"], list) or not isinstance(raw["blocking"], bool):
        raise StructuredOutputSchemaError("结构化输出字段类型错误", "blocking 必须为 bool，issues 必须为 list")
    warnings: list[str] = []
    issues = [_parse_issue(item, index, warnings) for index, item in enumerate(raw["issues"], start=1)]
    computed_blocking = bool(raw["blocking"]) or any(issue.blocking for issue in issues)
    status = ParseStatus.PARTIAL if raw.get("partial") is True else ParseStatus.OK
    if status is ParseStatus.PARTIAL:
        computed_blocking = True
    return ReviewReport(
        task_id=task_id,
        stage="content",
        issues=issues,
        blocking=computed_blocking,
        summary=str(raw["summary"]),
        model=model,
        created_at=now_iso(),
        source_artifacts=source_artifacts,
        raw_output_excerpt=_safe_excerpt(text),
        parse_status=status,
        parse_warnings=warnings,
    )


def _parse_issue(raw: object, index: int, warnings: list[str]) -> ReviewIssue:
    if not isinstance(raw, dict):
        raise StructuredOutputRiskFieldError("审核问题结构错误", f"issues[{index}] 必须是 object")
    for field in CRITICAL_ISSUE_FIELDS:
        if field not in raw:
            raise StructuredOutputRiskFieldError("审核问题缺少关键风险字段", f"issues[{index}].{field}")
    if not isinstance(raw["blocking"], bool):
        raise StructuredOutputRiskFieldError("审核问题 blocking 类型错误", f"issues[{index}].blocking")
    severity = _parse_severity(raw["severity"])
    if severity is None:
        raise StructuredOutputRiskFieldError("审核问题 severity 非法", f"issues[{index}].severity")
    if "location" not in raw:
        warnings.append(f"issues[{index}] 缺少 location")
    if "quote" not in raw:
        warnings.append(f"issues[{index}] 缺少 quote")
    blocking = bool(raw["blocking"]) or severity in {Severity.S0, Severity.S1}
    return ReviewIssue(
        location=str(raw.get("location", "")),
        quote=str(raw.get("quote", "")),
        issue_type=str(raw["issue_type"]),
        severity=severity,
        risk=str(raw["risk"]),
        suggestion=str(raw["suggestion"]),
        blocking=blocking,
    )


def _parse_severity(raw: object) -> Severity | None:
    value = str(raw).strip().upper()
    if value in Severity:
        return Severity(value)
    match = re.search(r"\bS[0-3]\b", value)
    if match:
        return Severity(match.group(0))
    chinese_mapping = {
        "严重": Severity.S0,
        "高风险": Severity.S1,
        "中风险": Severity.S2,
        "轻微": Severity.S3,
    }
    for marker, severity in chinese_mapping.items():
        if marker in str(raw):
            return severity
    return None


def _safe_excerpt(text: str) -> str:
    redacted = text
    for token in ("sk-", "XHS_AGENT_", "api_key"):
        if token in redacted:
            redacted = "原始输出包含敏感标记，已隐藏"
            break
    return redacted[:1000]


def require_manual_override_fields(front_matter: dict[str, Any]) -> None:
    if front_matter.get("manual_override") is not True:
        raise StructuredOutputSchemaError("人工覆盖报告缺少 manual_override", "必须为 true")
    if not front_matter.get("reviewer_note"):
        raise StructuredOutputSchemaError("人工覆盖报告缺少 reviewer_note", "必须说明覆盖理由")
    if not front_matter.get("source_artifacts"):
        raise StructuredOutputSchemaError("人工覆盖报告缺少 source_artifacts", "必须追溯源产物")
    fixes = front_matter.get("blocking_issue_fixes")
    if not isinstance(fixes, list) or not fixes:
        raise StructuredOutputSchemaError("人工覆盖报告缺少逐项修复说明", "blocking_issue_fixes 必须非空")
