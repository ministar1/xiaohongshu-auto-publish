# 格式规则模块任务

来源：`detailed_design.md` 8.13  
目标文件：`src/xiaohongshu_auto_publish/rules/format_rules.py`  
建议阶段：Phase 7  
前置依赖：配置管理模块、错误模型  
完成定义：小红书格式规则可由 TOML 更新，规则严重程度能映射到编排动作。

## 最小任务

- [ ] 定义 `FormatRules`、`RuleIssue`、`RuleSeverity`，严重程度包含 `block`、`confirm`、`warn`。
- [ ] 读取 `rules/xhs_format_rules.toml`，支持标题、正文、标签、表情符号、敏感词和素材规则。
- [ ] 规则文件缺失时加载内置默认规则。
- [ ] 规则文件格式错误或字段类型错误时返回 `ConfigError`，不得使用半解析结果继续。
- [ ] 实现标题长度、正文长度、段落长度、标签数量、表情数量的基础规则。
- [ ] 实现敏感词规则，返回配置中的严重程度和原因。
- [ ] 将 `block` 映射为格式阻断，`confirm` 映射为等待用户确认，`warn` 只提示。
- [ ] 具体数值全部来自配置或默认规则，不作为不可变业务常量散落在格式审核模块。
- [ ] 为格式审核模块提供可注入的 Fake Rules。
- [ ] 增加单元测试：缺失规则文件加载默认规则，敏感词返回对应严重程度。
- [ ] 增加错误测试：TOML 格式错误、未知严重程度、非法数值返回可读 `ConfigError`。
- [ ] 增加严重程度测试：`confirm` 触发用户确认状态，`warn` 不阻断。

## 验证命令

- [ ] `uv run pytest tests/unit/test_format_rules.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/rules tests/unit/test_format_rules.py`
