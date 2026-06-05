from __future__ import annotations

import pytest

from xiaohongshu_auto_publish.errors import StructuredOutputRiskFieldError, StructuredOutputSchemaError
from xiaohongshu_auto_publish.models import ParseStatus
from xiaohongshu_auto_publish.review.output_parser import parse_content_review_output


def test_parser_ok_with_optional_warnings() -> None:
    report = parse_content_review_output(
        '{"summary":"ok","blocking":false,"issues":[{"issue_type":"x","severity":"S2","risk":"r","blocking":false,"suggestion":"s"}]}',
        "task",
        "fake",
        [],
    )
    assert report.parse_status == ParseStatus.OK
    assert report.parse_warnings


def test_parser_normalizes_descriptive_severity() -> None:
    report = parse_content_review_output(
        '{"summary":"ok","blocking":false,"issues":[{"issue_type":"x","severity":"S2（中风险）","risk":"r","blocking":false,"suggestion":"s"}]}',
        "task",
        "fake",
        [],
    )
    assert report.issues[0].severity == "S2"


def test_parser_failed_invalid_json() -> None:
    report = parse_content_review_output("bad", "task", "fake", [])
    assert report.parse_status == ParseStatus.FAILED
    assert report.blocking


def test_parser_schema_and_risk_errors() -> None:
    with pytest.raises(StructuredOutputSchemaError):
        parse_content_review_output("{}", "task", "fake", [])
    with pytest.raises(StructuredOutputRiskFieldError):
        parse_content_review_output('{"summary":"x","blocking":false,"issues":[{"severity":"S2"}]}', "task", "fake", [])
