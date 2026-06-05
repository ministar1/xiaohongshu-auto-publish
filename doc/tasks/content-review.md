# 内容审核模块任务

来源：`detailed_design.md` 8.11、9、10、12、14  
目标文件：`src/xiaohongshu_auto_publish/review/content.py`、`src/xiaohongshu_auto_publish/review/output_parser.py`  
建议阶段：Phase 6，`output_parser.py` 可在 Phase 4 先做基础版本  
前置依赖：LLM 网关、来源策略、阶段产物存储、状态迁移表  
完成定义：所有审核问题都能结构化输出和渲染，S0/S1 与解析风险必须阻断。

## 最小任务

- [ ] 定义 `ReviewIssue`、`ReviewReport`、`ParseStatus` 和结构化输出错误类型。
- [ ] 在实现 parser 前维护决策表，覆盖 `OK`、`PARTIAL`、`FAILED`、schema 错误、关键风险字段错误、S0/S1、人工覆盖。
- [ ] 实现内容审核 JSON parser，根对象必填 `summary`、`blocking`、`issues`。
- [ ] 校验每个问题的关键风险字段：`issue_type`、`severity`、`risk`、`blocking`、`suggestion`。
- [ ] `severity` 只允许 `S0`、`S1`、`S2`、`S3`，`blocking` 必须为布尔值。
- [ ] 缺失 `location`、`quote` 等非关键字段时保持可用结果，但写入 `parse_warnings`。
- [ ] 完全无法解析或根结构错误时返回 `ParseStatus.FAILED` 或 `StructuredOutputSchemaError`。
- [ ] 单个问题缺失关键风险字段时返回 `StructuredOutputRiskFieldError`，标记“需人工复核”。
- [ ] `ParseStatus.PARTIAL` 只生成诊断型报告，不允许通过流程。
- [ ] 实现 `ContentReviewService`，读取最新用户编辑稿或调研稿，调用 LLM 审核四类风险。
- [ ] 使用来源策略辅助标记证据不足、来源质量差或争议内容。
- [ ] 渲染 `content_review.vNNN.md`，包含源产物说明、解析状态、解析警告、模型信息、问题列表、下一步建议。
- [ ] 安全截断原始 LLM 输出摘要，禁止包含 API Key、系统提示词全文或敏感配置。
- [ ] 实现 `--force-parse` 语义：只允许生成诊断报告，不允许强行通过任何解析风险或 S0/S1。
- [ ] 定义人工审核报告 front matter 要求：`manual_override: true`、`reviewer_note`、`source_artifacts`。
- [ ] 校验人工覆盖报告必须逐条说明原阻断项修复情况，不能只写“已确认”。
- [ ] 审核模块只返回报告和阻断结论，不直接推进流程状态。
- [ ] 增加单元测试：S0/S1 阻断，S2/S3 展示不阻断，所有问题写入 Markdown。
- [ ] 增加 parser 测试：非法 JSON、部分解析、schema 错误、关键风险字段错误、非关键字段警告。
- [ ] 增加集成测试：`ParseStatus.PARTIAL`、`StructuredOutputSchemaError`、`StructuredOutputRiskFieldError` 都进入 `content_blocked`。
- [ ] 增加人工覆盖测试：必须有逐项修复说明和 `--manual-review-note` 审计信息。

## 验证命令

- [ ] `uv run pytest tests/unit/test_content_review.py`
- [ ] `uv run pytest tests/unit/test_review_output_parser.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/review tests/unit/test_content_review.py tests/unit/test_review_output_parser.py`
