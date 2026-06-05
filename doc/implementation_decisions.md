# 实现决策记录

## 2026-06-05

- Python 支持版本调整为 `>=3.11`，以匹配详细设计中使用标准库 `tomllib` 的部署目标。
- 运行时依赖限定为设计允许的 `typer`、`openai`、`tavily-python`、`PyYAML`、`filelock`。
- Typer 使用 `>=0.20,<0.21`，原因是初始 `0.12.x` 与当前 Click 版本在测试环境中存在 CLI 参数渲染兼容问题。
- 增加 `hatchling` 作为 PEP 517 构建后端，使 `[project.scripts]` 中的 `xhs-agent` 能通过 `uv run xhs-agent` 正常解析；它不是业务运行时依赖。
- 第一版 CLI 默认不自动构造真实 LLM/Tavily 服务，避免在未配置密钥时误联网；真实 provider 保留在对应模块，可由后续装配层启用。
- 不引入 Pydantic。核心边界对象使用 `dataclasses`、`StrEnum` 和显式转换函数。
- 图片尺寸不引入 Pillow 复核；素材发布前先校验路径、扩展名、文件大小和 magic bytes，尺寸字段按 manifest 声明记录。
