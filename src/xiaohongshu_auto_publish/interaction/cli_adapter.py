from __future__ import annotations

from xiaohongshu_auto_publish.orchestration.orchestrator import WorkflowResult


def format_result(result: WorkflowResult) -> str:
    lines = [f"状态：{result.status.value}"]
    if result.task_id:
        lines.append(f"任务 ID：{result.task_id}")
    if result.artifact_paths:
        lines.append("最近产物：")
        lines.extend(f"- {path}" for path in result.artifact_paths)
    if result.blocking_issues:
        lines.append("阻断问题：")
        lines.extend(f"- [{issue.severity.value}] {issue.risk}" for issue in result.blocking_issues)
    if result.warnings:
        lines.append("提示：")
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.failure_summary:
        lines.append(f"失败原因：{result.failure_summary}")
    if result.next_command:
        lines.append(f"下一步：{result.next_command}")
    return "\n".join(lines)
