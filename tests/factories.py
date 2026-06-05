from __future__ import annotations

from xiaohongshu_auto_publish.models import ReviewIssue, ReviewReport, Severity, TaskMetadata, TaskStatus, WritingStyle, now_iso


def task(task_id: str = "20260605-topic-a1b2", status: TaskStatus = TaskStatus.CREATED) -> TaskMetadata:
    return TaskMetadata(
        task_id=task_id,
        input_type="topic",
        topic="睡眠与代谢",
        account_id="default",
        style=WritingStyle.POPULAR,
        status=status,
        created_at=now_iso(),
        updated_at=now_iso(),
    )


def issue(severity: Severity = Severity.S2, blocking: bool = False) -> ReviewIssue:
    return ReviewIssue(
        location="第 1 段",
        quote="示例",
        issue_type="medical_fact",
        severity=severity,
        risk="风险说明",
        suggestion="修改建议",
        blocking=blocking,
    )


def report(blocking: bool = False) -> ReviewReport:
    items = [issue(Severity.S0, True)] if blocking else [issue()]
    return ReviewReport(
        task_id="20260605-topic-a1b2",
        stage="content",
        issues=items,
        blocking=blocking,
        summary="摘要",
        model="fake",
        created_at=now_iso(),
    )
