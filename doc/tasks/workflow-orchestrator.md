# 流程编排模块任务

来源：`detailed_design.md` 8.2、9、10、12、13、15  
目标文件：`src/xiaohongshu_auto_publish/orchestration/orchestrator.py`、`src/xiaohongshu_auto_publish/orchestration/states.py`  
建议阶段：Phase 3  
前置依赖：配置管理、账号画像、输入规范化、阶段产物存储、状态存储  
完成定义：编排层能驱动两条主流程，集中执行状态迁移、阻断、确认、重试和回滚。

## 最小任务

- [ ] 在 `states.py` 定义 `TaskStatus`、触发事件和集中状态迁移表。
- [ ] 为迁移表项增加字段：当前状态、触发、目标状态、是否需要用户确认、是否允许重试、失败阶段。
- [ ] 实现迁移校验函数，业务代码不得散落硬编码状态判断。
- [ ] 定义 `WorkflowResult`，包含状态、产物路径、阻断问题、警告、下一步命令和失败摘要。
- [ ] 实现 `create_from_topic()`：创建任务、执行调研、保存产物、进入 `waiting_research_edit` 或 `research_failed`。
- [ ] 实现 `create_from_article()`：导入草稿后直接进入内容审核入口或等待确认。
- [ ] 实现 `continue_task()`，根据当前状态分派到内容审核、写作审核、格式审核、发布包生成或失败恢复。
- [ ] 实现内容审核阻断：S0/S1、解析失败、schema 错误、关键风险字段错误都进入 `content_blocked`。
- [ ] 实现 S2/S3 警告确认：无阻断但有警告时进入 `content_passed_with_warnings`，用户确认后才进入写作审核。
- [ ] 实现写作润色失败处理：超过重试次数进入 `writing_failed`，保留上一版可用草稿。
- [ ] 实现格式审核处理：`block` 进入 `format_blocked`，`confirm` 进入 `waiting_format_confirm`，`warn` 不阻断。
- [ ] 实现发布包生成失败处理：设置通用 `failed` 和 `last_failed_stage="package"`。
- [ ] 实现 `publish()`：只有 `package_ready` 且用户确认时调用发布通道。
- [ ] 实现 `retry_task()`，只允许可恢复状态调用，并根据 `last_failed_stage` 回到对应执行中状态。
- [ ] 实现 `rollback_task()`，只更新任务指针和审计日志，不删除、不覆盖既有产物。
- [ ] 实现 `get_status()`，展示最近完整产物、最近部分产物、失败原因、重试次数和推荐下一步命令。
- [ ] 实现提示词版本策略：默认 `locked`，显式 `latest` 时写入审计日志。
- [ ] 实现人工覆盖入口校验：必须有 `--manual-review-note` 或等价理由，`--yes` 不得替代。
- [ ] 增加状态迁移矩阵测试，覆盖每个状态的合法触发和至少一个非法触发。
- [ ] 增加编排单元测试：选题创建、S0 阻断、S2/S3 确认、格式失败不生成发布包、发布前未确认不调用发布通道。
- [ ] 增加恢复测试：临时失败只递增阶段重试计数，不产生 `*_retrying` 状态。
- [ ] 增加 rollback 测试：不删除产物，只追加审计事件。

## 验证命令

- [ ] `uv run pytest tests/unit/test_orchestrator.py`
- [ ] `uv run pytest tests/unit/test_states.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/orchestration tests/unit/test_orchestrator.py tests/unit/test_states.py`
