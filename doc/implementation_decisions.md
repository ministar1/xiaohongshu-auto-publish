# 实现决策记录

## 2026-06-05

- Python 支持版本调整为 `>=3.11`，以匹配详细设计中使用标准库 `tomllib` 的部署目标。
- 运行时依赖限定为设计允许的 `typer`、`openai`、`tavily-python`、`PyYAML`、`filelock`。
- Typer 使用 `>=0.20,<0.21`，原因是初始 `0.12.x` 与当前 Click 版本在测试环境中存在 CLI 参数渲染兼容问题。
- 增加 `hatchling` 作为 PEP 517 构建后端，使 `[project.scripts]` 中的 `xhs-agent` 能通过 `uv run xhs-agent` 正常解析；它不是业务运行时依赖。
- 第一版 CLI 在密钥缺失时不自动构造真实 LLM/Tavily 服务，避免未配置密钥时误联网；密钥齐全时按配置装配真实 provider。
- 不引入 Pydantic。核心边界对象使用 `dataclasses`、`StrEnum` 和显式转换函数。
- 图片尺寸不引入 Pillow 复核；素材发布前先校验路径、扩展名、文件大小和 magic bytes，尺寸字段按 manifest 声明记录。

## 2026-06-06

- 默认 LLM 配置切换为 DeepSeek OpenAI-compatible API：`base_url=https://api.deepseek.com`，`model=deepseek-v4-flash`。
- `llm.model` 和 `llm.base_url` 不能为空；否则真实模型调用会在运行中失败，配置加载阶段应提前阻断。
- `openai` 依赖范围调整为 `>=1.56,<2`，以兼容当前锁定的 `httpx 0.28.x`；旧的 `openai 1.49.0` 初始化客户端时会传入已移除的 `proxies` 参数。
- Typer 关闭富异常 locals 展示，避免未处理异常输出运行时密钥或其他敏感局部变量。
- DeepSeek JSON Output 需要请求层 `response_format={"type":"json_object"}` 且提示词包含 `json` 字样；LLM 网关按 `LLMRequest.response_format="json"` 统一传递请求参数。
- 内容审核 severity 仍以 `S0`、`S1`、`S2`、`S3` 为内部标准；解析器允许将 `S2（中风险）` 等模型描述性输出安全归一化。
- 格式审核和发布包生成共用发布字段解析，避免把润色稿模板标题误判为最终标题。
- 第一版发布命令接入 `ManualPublisher`，只记录手动发布辅助结果，不登录小红书、不访问平台发布接口。
