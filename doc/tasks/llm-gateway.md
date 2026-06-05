# LLM 网关模块任务

来源：`detailed_design.md` 8.7、9、10、12  
目标文件：`src/xiaohongshu_auto_publish/llm/gateway.py`、`src/xiaohongshu_auto_publish/llm/prompts.py`  
建议阶段：Phase 4  
前置依赖：配置管理模块、错误模型、核心数据模型  
完成定义：业务模块通过统一同步接口调用 OpenAI-compatible 模型，提示词版本可锁定和追溯。

## 最小任务

- [ ] 定义 `LLMRequest`，包含 `system_prompt`、`user_prompt`、`response_format`、`temperature`、`metadata`。
- [ ] 定义 `LLMResponse`，包含 `text`、`model`、`provider`、`usage`、`raw_id`、`raw_response`。
- [ ] 实现 `LLMGateway.complete()` 同步完整响应接口，第一版不暴露流式事件给业务模块。
- [ ] 接入 OpenAI-compatible client，正确使用 `base_url`、`model` 和运行时 API Key。
- [ ] 实现超时、重试、速率限制和模型错误统一转换为 `LLMError`。
- [ ] 保证错误对象和日志不包含 API Key、系统提示词全文或敏感配置。
- [ ] 实现 Fake LLM，支持单元测试固定输出、异常输出和延迟模拟。
- [ ] 建立提示词注册表，支持按 `prompt_id + version` 精确取回模板。
- [ ] 为调研汇总、内容审核、写作审核、格式辅助解释定义首版提示词占位模板。
- [ ] 实现提示词模板 SHA-256 哈希，格式为 `sha256:<lowercase_hex_digest>`，输入为 UTF-8 和统一 LF 行尾后的原始模板。
- [ ] 提示词版本记录包含 `prompt_id`、`version`、`schema_id`、`schema_version`、`template_hash`、`model`、`locked_at`。
- [ ] 支持旧版本保留和废弃元数据：`deprecated`、`deprecated_at`、`replacement_version`、废弃原因。
- [ ] 旧任务引用的提示词版本不存在时返回 `ConfigError`，不得静默切到最新版本。
- [ ] 明确结构化输出由下游 parser 校验，网关不直接信任模型文本。
- [ ] 增加单元测试：base_url/model/api key 使用正确，失败按配置重试，超限后统一错误。
- [ ] 增加提示词测试：哈希算法、哈希输入边界、废弃版本保留、锁定版本缺失错误。
- [ ] 增加 Fake LLM 测试：业务模块可注入 Fake LLM 独立运行。

## 验证命令

- [ ] `uv run pytest tests/unit/test_llm_gateway.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/llm tests/unit/test_llm_gateway.py`
