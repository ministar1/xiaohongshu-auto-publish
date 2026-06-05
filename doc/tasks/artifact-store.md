# 阶段产物存储模块任务

来源：`detailed_design.md` 6、8.4、12  
目标文件：`src/xiaohongshu_auto_publish/artifacts/store.py`、`src/xiaohongshu_auto_publish/artifacts/front_matter.py`  
建议阶段：Phase 2  
前置依赖：配置管理模块、错误模型、核心数据模型  
完成定义：Markdown 和 JSON 产物可版本化保存、读取、索引和追溯，路径不能逃逸工作区。

## 最小任务

- [ ] 定义 `ArtifactRef`、`MarkdownDocument` 及产物阶段、类型相关常量。
- [ ] 实现 Markdown front matter 读写，使用 `yaml.safe_load()`，空 front matter 视为 `{}`。
- [ ] 实现 front matter 安全限制：最大 32KB、禁止显式 YAML tag、限制 anchor/alias 异常数量。
- [ ] 实现解析后结构校验：只允许标量、列表、字典；最大深度 5；总键数量不超过 100；字典键必须是字符串。
- [ ] 实现 `save_markdown()`，写入 UTF-8、front matter 和正文。
- [ ] 实现 `save_partial()`，写入 `complete=false`、`error_type`、`retryable` 和源产物引用。
- [ ] 实现任务级锁，优先使用 `filelock.FileLock`，锁文件为 `workspace/<task_id>/artifacts.lock`。
- [ ] 实现版本号分配：扫描目录和 `artifacts.jsonl` 后递增，同阶段同类型不可重复。
- [ ] 使用独占创建写版本化产物，禁止覆盖已有版本文件；冲突时重新扫描并最多重试 8 次。
- [ ] 版本文件写入成功后 flush，并按平台能力 fsync；写入失败时删除未完成目标文件。
- [ ] 在同一锁内追加 `artifacts.jsonl`，追加后立即 flush。
- [ ] 实现 `read_markdown()`，返回 front matter、正文和对应 `ArtifactRef`。
- [ ] 实现 `latest()`，默认只返回 `complete=true` 的最新产物。
- [ ] 实现 `list_artifacts()`，可按阶段和类型过滤，并支持显式包含部分产物。
- [ ] 对所有路径做绝对路径解析，确认其位于 `workspace_dir` 内。
- [ ] 增加单元测试：保存读取、版本递增、latest、部分产物不参与继续流程、路径逃逸报错。
- [ ] 增加并发测试：同阶段并发保存不会分配重复版本。
- [ ] 增加冲突超限测试：返回可读 `ArtifactError`，包含尝试过的版本号和下一步建议。

## 验证命令

- [ ] `uv run pytest tests/unit/test_artifact_store.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/artifacts tests/unit/test_artifact_store.py`
