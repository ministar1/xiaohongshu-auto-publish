# 格式审核模块任务

来源：`detailed_design.md` 8.15、12、14  
目标文件：`src/xiaohongshu_auto_publish/review/format.py`  
建议阶段：Phase 7  
前置依赖：格式规则模块、素材元数据模块、阶段产物存储、状态迁移表  
完成定义：格式审核能输出 `block`、`confirm`、`warn` 问题和是否可进入发布包生成的结论。

## 最小任务

- [ ] 定义格式审核请求、结果和问题对象，问题字段包含 `location`、`rule_id`、`severity`、`message`、`suggestion`、`auto_fixable`。
- [ ] 读取最新润色稿或用户编辑稿，提取标题、正文、话题标签和封面标题候选。
- [ ] 使用 `FormatRules` 检查标题、正文段落、标签、敏感词、表情符号。
- [ ] 读取 `MediaManifest`，检查 manifest 完整性、图片数量、比例、封面候选和路径合法性。
- [ ] 格式审核阶段做一次文件当前是否存在的非阻断检查，缺失图片作为 `warn` 写入报告和 CLI 预警。
- [ ] manifest 缺少必需角色、路径越界、远程 URL、比例或数量不满足硬规则时返回 `block`。
- [ ] 汇总严重程度：存在 `block` 则不可继续，存在 `confirm` 则等待用户确认，仅 `warn` 不影响发布包生成。
- [ ] 渲染 `format_review.vNNN.md`，包含规则命中、素材检查、是否需要确认、是否阻断。
- [ ] 不在格式审核阶段硬阻断图片文件被删除或移动；最终文件存在性由发布包模块复验。
- [ ] 增加单元测试：标题超长、敏感词 `block`、素材 manifest 缺封面、全部通过。
- [ ] 增加严重程度测试：`confirm` 要求确认，`warn` 只写报告不影响 `can_publish`。
- [ ] 增加素材缺失测试：格式审核生成 warn，发布包生成阶段必须失败。

## 验证命令

- [ ] `uv run pytest tests/unit/test_format_review.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/review tests/unit/test_format_review.py`
