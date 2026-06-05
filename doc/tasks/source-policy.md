# 来源策略/白名单模块任务

来源：`detailed_design.md` 8.9、14  
目标文件：`src/xiaohongshu_auto_publish/source_policy/policy.py`  
建议阶段：Phase 5  
前置依赖：配置管理模块、联网检索服务、核心数据模型  
完成定义：来源可被分类、排序和解释，高风险主题缺少权威来源时能触发可恢复失败。

## 最小任务

- [ ] 定义 `SourceEvaluation`，包含来源类别、可信度、优先级、风险说明、发布日期状态和是否权威。
- [ ] 读取 `rules/source_policy.toml`，支持 `trusted_sources` 和 `risk_sources`。
- [ ] 规则文件缺失时加载内置最小可信来源清单：WHO、CDC、NIH、FDA、NHS、国家卫生健康委。
- [ ] 规则文件格式错误时返回 `ConfigError`，不得静默降级。
- [ ] 实现 `evaluate(source)`，按域名识别白名单、灰名单、风险来源和未知来源。
- [ ] 缺失发布日期时标记 `published_at_unknown`，不得伪造日期。
- [ ] 实现 `rank(sources)`，按可信度、优先级和风险等级排序。
- [ ] 搜索结果全部未知来源时允许生成调研报告，但必须输出“来源可信度不足”提示。
- [ ] 实现高风险主题判断规则，覆盖疾病治疗、药物、剂量、诊断、孕产、儿童、慢病管理。
- [ ] 高风险主题且所有来源未知时返回可恢复失败，提示用户补充权威来源。
- [ ] 确保未知来源不会被包装成权威结论，供调研和内容审核使用。
- [ ] 增加单元测试：白名单高可信、风险来源降权、缺失发布日期、未知来源不冒充权威。
- [ ] 增加降级测试：规则文件缺失加载内置清单，规则文件错误返回 `ConfigError`。
- [ ] 增加高风险主题测试：全未知来源返回可恢复失败。

## 验证命令

- [ ] `uv run pytest tests/unit/test_source_policy.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/source_policy tests/unit/test_source_policy.py`
