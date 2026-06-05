from __future__ import annotations

from xiaohongshu_auto_publish.post_fields import extract_post_fields


def test_extract_post_fields_from_revised_markdown() -> None:
    fields = extract_post_fields(
        "# 润色稿\n\n"
        "## 标题候选\n\n"
        "- 睡够7小时真的能瘦肚子？真相来了！\n"
        "- 备用标题\n\n"
        "## 正文\n\n"
        "正文第一段 #睡眠健康\n\n"
        "## 标签建议\n\n"
        "#睡眠健康 #健康科普\n\n"
        "## 仍需用户确认\n\n"
        "- 确认医学表达\n"
    )
    assert fields.title == "睡够7小时真的能瘦肚子？真相来了！"
    assert fields.body == "正文第一段 #睡眠健康"
    assert fields.hashtags == ["睡眠健康", "健康科普"]
    assert fields.cover_title == "睡够7小时真的能瘦肚子？真相来了！"
