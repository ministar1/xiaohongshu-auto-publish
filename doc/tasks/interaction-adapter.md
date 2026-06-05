# 交互适配模块任务

来源：`detailed_design.md` 4、8.1、10  
目标文件：`src/xiaohongshu_auto_publish/cli.py`、`src/xiaohongshu_auto_publish/interaction/cli_adapter.py`  
建议阶段：Phase 3  
前置依赖：配置管理模块、流程编排模块、账号画像模块  
完成定义：CLI 只负责参数解析、输出和确认，不承载业务流程逻辑。

## 最小任务

- [ ] 创建 Typer app，并注册 `xhs-agent` 入口所需 app 对象。
- [ ] 实现全局参数：`--config` 和多次 `--set key=value`，并传给配置加载器。
- [ ] 实现 `init` 命令，委托配置管理模块写模板文件和目录。
- [ ] 实现 `topic "<topic>"` 命令，解析 `--account`、`--style`、`--audience`、`--series`、`--length`、`--slug`。
- [ ] 实现 `import <article_path>` 命令，解析主题、账号、风格和 slug 参数。
- [ ] 实现 `continue <task_id>`，支持 `--yes`、`--force-parse`、`--prompt-policy`、`--manual-review-note`。
- [ ] 实现 `retry <task_id>`，支持提示词策略参数。
- [ ] 实现 `status <task_id>` 和 `list`，展示状态、最近产物路径、失败原因和下一步命令。
- [ ] 实现手动阶段命令：`review-content`、`review-writing`、`review-format`、`package`、`publish`。
- [ ] 实现 `rollback <task_id> --to-phase <phase>`，只提交请求给编排层。
- [ ] 实现 `accounts list` 和 `accounts show <account_id>`，委托账号画像模块。
- [ ] 实现 `config-check`，展示缺失项和配置错误，不展示密钥值。
- [ ] 实现 `cleanup` 和 `archive` 命令入口，委托维护模块。
- [ ] 统一错误捕获，输出错误摘要、具体原因、建议下一步和相关文件路径。
- [ ] 格式化展示审核问题，确保所有阻断和非阻断问题都直接显示给用户。
- [ ] 增加 CLI 测试：`topic` 参数传给编排层，`import` 文件不存在时返回可读错误。
- [ ] 增加 CLI 测试：`status` 展示状态和最新产物路径，`continue` 展示下一步操作。
- [ ] 增加安全测试：`--yes` 不绕过 S0/S1、解析失败、格式 block、素材缺失和发布确认。

## 验证命令

- [ ] `uv run pytest tests/unit/test_cli.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/cli.py src/xiaohongshu_auto_publish/interaction tests/unit/test_cli.py`
