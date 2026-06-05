# 账号画像/账号配置模块任务

来源：`detailed_design.md` 8.18  
目标文件：`src/xiaohongshu_auto_publish/account/profile.py`  
建议阶段：Phase 1  
前置依赖：配置管理模块  
完成定义：可按账号 ID 加载账号画像，CLI 能列出和展示账号摘要，输出不泄露敏感值。

## 最小任务

- [ ] 定义 `AccountProfile` 数据模型，包含 `account_id`、`positioning`、`audience`、`tone`、`forbidden_phrases`、`style_examples`、`conversion_strategy`。
- [ ] 实现账号配置目录解析，默认从 `accounts/<account_id>.toml` 读取。
- [ ] 实现默认账号加载逻辑，默认账号 ID 来自配置管理模块。
- [ ] 校验账号 ID 与文件名一致，账号 ID 不存在时返回可读 `ConfigError`。
- [ ] 校验必填字段，缺失定位、受众或语气时返回明确错误。
- [ ] 支持多个账号画像互不影响，不维护全局“当前账号”状态。
- [ ] 实现 `list_profiles()`，返回可用账号 ID、默认账号标记和配置文件路径。
- [ ] 实现 `show_profile(account_id)`，输出非敏感摘要。
- [ ] 将禁用表达、语气风格和关注转化策略暴露给写作审核模块。
- [ ] 为 `xhs-agent accounts list` 和 `xhs-agent accounts show` 提供可调用服务接口。
- [ ] 增加单元测试：默认账号可加载，账号不存在报错，多账号配置互不影响。
- [ ] 增加输出测试：`accounts show` 不输出环境变量值、API Key 或其他敏感配置。

## 验证命令

- [ ] `uv run pytest tests/unit/test_account_profile.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/account tests/unit/test_account_profile.py`
