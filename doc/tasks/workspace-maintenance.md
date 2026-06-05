# 工作区清理与归档模块任务

来源：`detailed_design.md` 8.20、10、12  
目标文件：`src/xiaohongshu_auto_publish/maintenance/cleanup.py`、`src/xiaohongshu_auto_publish/maintenance/archive.py`  
建议阶段：Phase 8  
前置依赖：配置管理模块、阶段产物存储模块、状态与审核记录模块  
完成定义：清理和归档不会破坏任务恢复、审计追溯和当前状态引用。

## 最小任务

- [ ] 定义保留策略模型，读取 `keep_recent_versions`、`keep_task_days`、`archive_dir`、`cleanup_dry_run_default`。
- [ ] 校验 `archive_dir` 位于 `workspace_dir` 内，路径逃逸返回 `ConfigError`。
- [ ] 实现 cleanup 扫描，识别可清理旧版本产物、已归档过期任务和不可处理原因。
- [ ] `cleanup --dry-run` 只输出候选文件、原因和释放空间估算，不修改文件系统。
- [ ] `cleanup --apply` 只能删除保留策略明确允许删除的旧版本产物或已归档过期任务。
- [ ] 删除前再次确认任务不处于执行中状态。
- [ ] 永不删除 `task.json`、`artifacts.jsonl`、`audit_log.jsonl`、最新完整产物、当前状态引用产物。
- [ ] 不删除仍被 `source_artifacts` 引用的恢复链路产物。
- [ ] 实现 `archive <task_id>`，只移动整个任务目录到 `archive_dir/<task_id>/`。
- [ ] 归档目标已存在时返回 `StateError`，不得覆盖。
- [ ] 执行中状态不得被清理或归档：`researching`、`content_reviewing`、`writing_reviewing`、`format_reviewing`、`publishing`。
- [ ] 每次 archive 或 cleanup apply 写入 `workspace/maintenance_log.jsonl`。
- [ ] 归档单个任务时也在任务 `audit_log.jsonl` 写入归档事件。
- [ ] `status <task_id>` 查询归档任务时应提示已归档并展示归档路径。
- [ ] 已清理旧版本引用展示“已按保留策略清理”，不得当作状态损坏。
- [ ] 增加单元测试：dry-run 不修改文件系统，apply 不删除最新完整产物和审计文件。
- [ ] 增加安全测试：执行中任务不会被清理或归档，路径逃逸报错，目标已存在不覆盖。
- [ ] 增加日志测试：cleanup 和 archive 写入维护日志。

## 验证命令

- [ ] `uv run pytest tests/unit/test_workspace_maintenance.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/maintenance tests/unit/test_workspace_maintenance.py`
