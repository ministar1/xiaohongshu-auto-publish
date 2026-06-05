from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PostFields:
    title: str
    body: str
    hashtags: list[str]
    cover_title: str


def extract_post_fields(text: str) -> PostFields:
    title = _first_title_candidate(text) or _first_content_heading(text) or _first_non_empty_line(text)
    body = _section_body(text, "正文", stop_headings={"标签建议", "仍需用户确认"}) or text
    hashtags = list(dict.fromkeys(re.findall(r"#([\w\u4e00-\u9fff-]+)", text)))
    return PostFields(title=title, body=body.strip(), hashtags=hashtags, cover_title=title[:20])


def _first_title_candidate(text: str) -> str:
    section = _section_body(text, "标题候选", stop_headings={"正文", "标签建议", "仍需用户确认"})
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            return stripped[2:].strip()
    return ""


def _first_content_heading(text: str) -> str:
    ignored = {"润色稿", "最终发布包", "写作审核报告", "格式审核报告"}
    for match in _heading_matches(text):
        title = match.group("title").strip()
        if title and title not in ignored:
            return title
    return ""


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().lstrip("# ").strip()
        if stripped:
            return stripped
    return ""


def _section_body(text: str, heading: str, stop_headings: set[str]) -> str:
    matches = list(_heading_matches(text))
    for index, match in enumerate(matches):
        if match.group("title").strip() != heading:
            continue
        start = match.end()
        end = len(text)
        for next_match in matches[index + 1 :]:
            if next_match.group("title").strip() in stop_headings:
                end = next_match.start()
                break
        return text[start:end].strip()
    return ""


def _heading_matches(text: str) -> list[re.Match[str]]:
    return list(re.finditer(r"^#{1,6}\s+(?P<title>.+?)\s*$", text, flags=re.MULTILINE))
