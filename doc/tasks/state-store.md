# 状态与审核记录模块任务

来源：`detailed_design.md` 7、8.5、10、12  
目标文件：`src/xiaohongshu_auto_publish/state/store.py`  
建议阶段：Phase 2  
前置依赖：配置管理模块、核心数据模型、阶段产物存储模块  
完成定义：任务状态可持久化、审计日志只追加、失败和重试信息可恢复。

## 最小任务

- [ ] 定义 `TaskMetadata`、`AuditEvent`、`LastError` 等状态层数据模型。
- [ ] 实现 `create_task(metadata)`，用独占创建语义创建任务目录和 `task.json`，不得覆盖已有任务。
- [ ] 实现 `get_task(task_id)`，读取并校验 `task.json`。
- [ ] 实现 `update_status(task_id, status)`，使用状态锁和临时文件加原子替换写 `task.json`。
- [ ] 实现 `record_failure()`，保存 `last_failed_stage`、`last_error`、`retryable`、`related_artifacts` 和 `next_action`。
- [ ] 实现 `increment_retry()`，按阶段递增 `retry_counts` 并返回新次数。
- [ ] 实现 `append_audit_event()`，只追加 `audit_log.jsonl`，不得重写既有审计记录。
- [ ] 实现 `list_tasks()`，列出普通任务；归档任务由维护模块额外标记。
- [ ] `task.json` 保存 `prompt_versions` 和 `manual_overrides`，供提示词锁定和人工覆盖追溯。
- [ ] 状态更新、用户确认、人工覆盖、回滚、发布尝试和失败恢复必须写审计事件。
- [ ] 损坏的 `task.json`、非法状态值或缺失关键字段应返回清晰 `StateError`。
- [ ] 增加单元测试：创建后可读取，状态更新持久化，审计日志 JSON Lines 追加。
- [ ] 增加失败恢复测试：失败状态可被读取，并能为编排层提供 `last_failed_stage`。
- [ ] 增加回滚和人工覆盖审计测试：事件包含源状态、目标状态、产物 ID、用户确认信息。

## 验证命令

- [ ] `uv run pytest tests/unit/test_state_store.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/state tests/unit/test_state_store.py`
