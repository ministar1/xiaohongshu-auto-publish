# 修复日志

## 2026-06-06

- 修复 `workspace` 中 Markdown 产物的逐字项目符号排版：
  - `drafts/revised.v001.md` 的“仍需用户确认”合并为 3 条正常确认项。
  - `package/final_package.v001.md` 中嵌入旧稿的“仍需用户确认”同步合并为正常确认项。
  - `reviews/writing_review.v001.md` 的“系列化建议”和“关键改写”恢复为正常列表。
- 为写作输出解析增加字符数组归一化，避免模型把句子拆成字符列表时再次生成逐字 Markdown。
- 新增 `doc/workspace_detail.md`，说明 `workspace/` 中各类文件的作用、修改边界和清理方式。
- 清理本地工具缓存：`.pytest_cache/`、`.ruff_cache/`、`.mypy_cache/` 和测试生成的 `__pycache__/`。
