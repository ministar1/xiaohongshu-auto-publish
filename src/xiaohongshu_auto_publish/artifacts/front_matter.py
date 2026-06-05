from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import yaml  # type: ignore[import-untyped]

from xiaohongshu_auto_publish.errors import ArtifactError

MAX_FRONT_MATTER_SIZE = 32 * 1024
MAX_FRONT_MATTER_DEPTH = 5
MAX_FRONT_MATTER_KEYS = 100
MAX_ANCHOR_ALIAS_MARKERS = 32

_EXPLICIT_TAG_RE = re.compile(r"(^|[\s\[{,])!(?:!|<|[A-Za-z_])", re.MULTILINE)
_ANCHOR_ALIAS_RE = re.compile(r"(^|[\s\[{,])[*&][A-Za-z0-9_-]+")


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    front_matter: dict[str, Any]
    body: str


def parse_markdown(text: str) -> MarkdownDocument:
    if not text.startswith("---\n"):
        return MarkdownDocument(front_matter={}, body=text)
    end = text.find("\n---\n", 4)
    if end == -1:
        return MarkdownDocument(front_matter={}, body=text)
    raw_front_matter = text[4:end]
    body = text[end + 5 :]
    if body.startswith("\n"):
        body = body[1:]
    front_matter = parse_front_matter(raw_front_matter)
    return MarkdownDocument(front_matter=front_matter, body=body)


def parse_front_matter(raw: str) -> dict[str, Any]:
    size = len(raw.encode("utf-8"))
    if size > MAX_FRONT_MATTER_SIZE:
        raise ArtifactError("front matter 过大", "YAML front matter 不能超过 32KB")
    if _EXPLICIT_TAG_RE.search(raw):
        raise ArtifactError("front matter 包含显式 YAML tag", "禁止使用 !、!! 或 !<tag> 形式")
    if len(_ANCHOR_ALIAS_RE.findall(raw)) > MAX_ANCHOR_ALIAS_MARKERS:
        raise ArtifactError("front matter anchor/alias 过多", "请移除异常 YAML anchor 或 alias")
    try:
        parsed = yaml.safe_load(raw) if raw.strip() else {}
    except yaml.YAMLError as exc:
        raise ArtifactError("front matter 解析失败", str(exc)) from exc
    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        raise ArtifactError("front matter 根结构非法", "YAML front matter 必须是字典")
    key_count = _validate_node(parsed, depth=0)
    if key_count > MAX_FRONT_MATTER_KEYS:
        raise ArtifactError("front matter 键数量过多", "YAML front matter 键总数不能超过 100")
    return parsed


def render_markdown(front_matter: dict[str, Any], body: str) -> str:
    if not front_matter:
        return body
    yaml_text = yaml.safe_dump(
        front_matter,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    return f"---\n{yaml_text}\n---\n\n{body.lstrip()}"


def _validate_node(node: object, depth: int) -> int:
    if depth > MAX_FRONT_MATTER_DEPTH:
        raise ArtifactError("front matter 嵌套过深", "YAML front matter 嵌套深度不能超过 5")
    if isinstance(node, dict):
        total = 0
        for key, value in node.items():
            if not isinstance(key, str):
                raise ArtifactError("front matter 键类型非法", "YAML front matter 字典键必须是字符串")
            total += 1 + _validate_node(value, depth + 1)
        return total
    if isinstance(node, list):
        return sum(_validate_node(item, depth + 1) for item in node)
    if isinstance(node, (str, int, float, bool)) or node is None:
        return 0
    raise ArtifactError("front matter 值类型非法", "只允许标量、列表和字典")
