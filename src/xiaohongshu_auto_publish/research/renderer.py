from __future__ import annotations

from xiaohongshu_auto_publish.models import SourceRecord


def render_research_markdown(topic: str, summary: str, facts: list[str], cautions: list[str]) -> str:
    return (
        f"# 调研资料：{topic}\n\n"
        f"## 选题摘要\n\n{summary}\n\n"
        "## 适合小红书表达的核心观点\n\n"
        + "\n".join(f"- {item}" for item in facts)
        + "\n\n## 需要谨慎表达的内容\n\n"
        + "\n".join(f"- {item}" for item in cautions)
        + "\n\n## 不建议使用或风险较高的说法\n\n- 绝对化疗效承诺\n- 替代正规诊疗建议\n"
    )


def render_sources_markdown(records: list[SourceRecord]) -> str:
    lines = [
        "# 来源清单",
        "",
        "| url | title | organization | published_at | credibility | relevance | notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    item.url,
                    item.title,
                    item.organization,
                    item.published_at or "发布日期未知",
                    item.credibility,
                    item.relevance,
                    item.notes,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 用户补充来源",
            "",
            "| url | title | organization | published_at | reason |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    return "\n".join(lines) + "\n"
