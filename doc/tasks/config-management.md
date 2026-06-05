# 配置管理模块任务

来源：`detailed_design.md` 5、8.6、10、12  
目标文件：`src/xiaohongshu_auto_publish/config/loader.py`、`src/xiaohongshu_auto_publish/config/schema.py`  
建议阶段：Phase 1  
前置依赖：无  
完成定义：配置对象可结构化加载，密钥不落盘，`config-check` 能报告缺失项和非法配置。

## 最小任务

- [ ] 定义 `AppConfig` 及子配置 dataclass，覆盖 `llm`、`search`、`storage`、`retention`、`writing`、`source_policy`、`format_rules`、`account`、`publish`。
- [ ] 实现默认配置常量，字段与详细设计 5.1 保持一致。
- [ ] 实现 `config.toml` 读取，使用 Python 3.11+ 标准库 `tomllib`，解析失败返回 `ConfigError` 并包含文件路径。
- [ ] 实现 `.env` 严格解析器，只接受非空 `KEY=VALUE` 行，`KEY` 匹配 `[A-Za-z_][A-Za-z0-9_]*`。
- [ ] 实现配置加载优先级：默认配置、`config.toml`、`.env`、系统环境变量、CLI `--set` 覆盖。
- [ ] 实现 CLI 点号路径覆盖，只允许覆盖已声明字段，不允许新增未知字段或替换整个嵌套表。
- [ ] 实现类型转换和合理性校验：超时为正数、重试次数非负、保留版本数大于等于 1、保留天数非负。
- [ ] 校验 `workspace_dir`、规则路径、账号目录和归档目录的路径边界，归档目录不得逃逸工作区。
- [ ] 实现 `check_required_secrets(config)`，只返回缺失的环境变量名，不返回密钥值。
- [ ] 提供 `init` 命令需要的模板字符串：`config.toml`、`.env.example`、规则文件示例、默认账号示例。
- [ ] 保证日志、错误详情、阶段产物和测试快照中不包含真实 API Key。
- [ ] 增加配置加载单元测试：系统环境变量覆盖 `.env`，CLI 覆盖优先级最高。
- [ ] 增加错误测试：非法 TOML、非法 `.env` KEY、未知覆盖键、负数超时、非法保留策略。
- [ ] 增加 `config-check` 输出测试：能展示缺失的 `XHS_AGENT_` 环境变量名且不展示密钥值。

## 验证命令

- [ ] `uv run pytest tests/unit/test_config_loader.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/config tests/unit/test_config_loader.py`
