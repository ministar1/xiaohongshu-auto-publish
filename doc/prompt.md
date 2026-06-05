# Vibe Coding 起始 Prompt

你是本仓库 `xiaohongshu_auto_publish` 的主 Agent，负责把需求、概要设计、详细设计和任务拆分落地为可运行、可测试、可维护的 Python CLI 工程。你必须主动推进实现、拆分子 Agent、合并结果并完成最终验收。整个编码过程默认没有人工参与。

## 目标

实现“小红书医学/养生科普 Agent”的本地 CLI 工具。系统用于医学、养生、健康科普类小红书内容的调研、内容审核、写作润色、格式审核、发布包生成和手动发布辅助。

最终仓库必须满足：

1. 所有 `doc/tasks/*.md` 中的模块任务均完成。
2. 代码有完整、聚焦的 `pytest` 单元测试和必要集成测试。
3. `uv run ruff format .` 执行后无格式变更遗留。
4. `uv run ruff check .` 通过。
5. `uv run mypy src` 通过。
6. `uv run pytest` 通过。
7. 不泄露 API Key、账号密码或其他敏感凭据。
8. 自动发布第一版只实现手动发布辅助，不登录小红书，不绕过验证码、风控或平台安全机制。

## 必读输入

开始前必须读取并理解以下文件：

1. `doc/proposal.md`
2. `doc/high_level_design.md`
3. `doc/detailed_design.md`
4. `doc/tasks/progress.md`
5. `doc/tasks/*.md`
6. `pyproject.toml`
7. 当前仓库文件树和已有代码

不要只读摘要。每个模块子 Agent 必须读取自己对应的 `doc/tasks/<module>.md` 原文，并以其中的“最小任务”“完成定义”“验证命令”为准。

## 解释规则

当文档之间出现差异时，按以下优先级执行：

1. 本 Prompt 和用户显式指令。
2. `doc/tasks/*.md` 的模块 checklist 和完成定义。
3. `doc/detailed_design.md`。
4. `doc/high_level_design.md`。
5. `doc/proposal.md`。
6. 现有代码约定。

“整个过程不会有人工参与”指实现过程由主 Agent 和子 Agent 自动推进，不等待用户确认。产品运行时仍必须实现需求文档中的用户编辑、用户确认、严重问题阻断、发布前确认等交互语义。`--yes` 只能跳过非阻断确认点，不能绕过 S0/S1、结构化解析失败、格式 `block`、素材缺失或发布确认。

如果遇到可自行决策的细节，不要提问，按文档精神保守实现，并把假设记录到 `doc/implementation_decisions.md`。只有在仓库不可读、工具不可用或需求存在无法自洽的硬冲突且无法用上述优先级解决时，才停止并给出阻塞原因。

## 工程约束

项目是 `uv` 管理的 Python 工程。优先使用 `uv add`、`uv sync`、`uv run`。

当前设计文档已允许新增以下运行时依赖，除此之外不要新增生产依赖，除非实现确实无法完成并在 `doc/implementation_decisions.md` 记录原因：

1. `typer`
2. `openai`
3. `tavily-python`
4. `PyYAML`
5. `filelock`

实现时按 `doc/detailed_design.md` 的建议评估并调整 Python 支持版本，优先把 `requires-python` 下调到 `>=3.11`，因为设计依赖标准库 `tomllib`。更新依赖后必须保持 `uv.lock` 同步。

默认使用 `src` 布局，包名为 `xiaohongshu_auto_publish`，CLI 命令为 `xhs-agent`。建议包结构、测试结构、数据模型、状态枚举、错误模型、工作区结构、提示词版本策略均以 `doc/detailed_design.md` 为准。

不要引入 Pydantic。核心模型优先使用 `dataclasses`、`Enum` / `StrEnum` 和明确类型注解。公共接口必须类型完整，不要把无约束 `dict[str, Any]` 当成长期模块边界。

## 主 Agent 职责

主 Agent 必须维护整体进度、依赖顺序和质量闸门：

1. 先审计仓库状态、读取文档、确认当前依赖和测试命令。
2. 建立实现计划，按 Phase 推进。
3. 为每个模块派发子 Agent。没有可用子 Agent 工具时，用等价的模块工作队列模拟执行。
4. 子 Agent 完成后，主 Agent 负责代码审查、接口整合、冲突修复和跨模块测试。
5. 每个模块通过对应验证命令后，才更新 `doc/tasks/progress.md` 的勾选状态。
6. 阶段完成后运行阶段相关测试；所有 Phase 完成后运行完整验收命令。
7. 最终输出实现摘要、已运行命令、测试结果、剩余风险和关键文件。

主 Agent 不得把失败测试留给用户处理。遇到失败要继续定位并修复，直到质量闸门通过或出现真正阻塞。

## 子 Agent 通用协议

每个模块子 Agent 都必须遵守：

1. 读取 `doc/proposal.md`、`doc/high_level_design.md`、`doc/detailed_design.md` 中与本模块相关章节。
2. 读取自己的任务文件，例如 `doc/tasks/config-management.md`。
3. 只实现本模块职责和必要的相邻接口，不做无关重构。
4. 通过构造函数或 Protocol 注入外部依赖，单元测试默认使用 Fake 或 Mock，不访问真实 LLM、Tavily 或网络。
5. 添加或更新对应测试文件。
6. 运行任务文件中的验证命令。
7. 报告变更文件、实现要点、测试命令和未决风险。
8. 不泄露密钥值，不把 API Key 写入源码、日志、Markdown 产物、JSONL、错误详情或测试快照。

子 Agent 输出的代码必须能被主 Agent 接入完整工程。接口名称、数据模型和错误类型必须优先复用已存在实现，避免同义重复定义。

## Phase 执行顺序

严格按以下阶段推进。阶段内可并行，但不得违反前置依赖。

| Phase | 模块任务 | 关键目标 |
| --- | --- | --- |
| Phase 1 | `config-management.md`、`account-profile.md` | 工程依赖、配置加载、`.env` 严格解析、账号画像、`config-check`、`accounts list/show` |
| Phase 2 | `artifact-store.md`、`state-store.md` | 版本化产物、front matter 安全解析、状态存储、任务 ID、审计日志、锁语义 |
| Phase 3 | `input-normalizer.md`、`workflow-orchestrator.md`、`interaction-adapter.md` | 输入规范化、集中状态迁移表、编排骨架、CLI 命令、重试、rollback |
| Phase 4 | `llm-gateway.md`、`search-provider.md` | LLM 网关、提示词注册表、结构化输出基础、Tavily provider、Fake providers |
| Phase 5 | `source-policy.md`、`research-service.md` | 来源策略、可信来源排序、高风险缺源处理、调研 Markdown 和来源清单 |
| Phase 6 | `content-review.md`、`writing-review.md` | 内容审核、S0/S1 阻断、结构化输出 parser、写作审核与润色 |
| Phase 7 | `format-rules.md`、`media-manifest.md`、`format-review.md`、`package-builder.md` | 可配置格式规则、素材 manifest、格式审核、最终发布包、素材复验 |
| Phase 8 | `asset-library.md`、`workspace-maintenance.md`、`publisher.md` | 历史资产索引、cleanup/archive、手动发布辅助 |
| Phase 9 | `progress.md` 中的完整验证项 | 端到端集成、状态矩阵、并发测试、恢复手册、全量质量闸门 |

## 模块验收要求

每个模块必须以对应任务文件为准，不得只实现名义接口。

特别注意以下高风险模块：

1. `artifact-store.md`：front matter 必须使用 `yaml.safe_load()`，并实现 32KB 上限、禁止显式 YAML tag、anchor/alias 异常限制、解析后深度和键数量限制。产物写入必须版本化、不可覆盖、路径不得逃逸工作区。
2. `state-store.md`：`task.json` 更新要原子替换，`audit_log.jsonl` 只追加。状态更新、用户确认、人工覆盖、rollback、发布尝试和失败恢复必须写审计事件。
3. `workflow-orchestrator.md`：状态迁移必须集中在迁移表，不得散落硬编码。S0/S1、结构化解析失败、schema 错误、关键风险字段错误必须进入阻断状态。
4. `llm-gateway.md`：提示词模板必须有稳定 ID、版本号、schema ID、schema version 和 SHA-256 模板哈希。旧任务默认使用锁定版本，不能静默切换最新版本。
5. `content-review.md`：所有审核问题必须结构化输出和渲染。`ParseStatus.PARTIAL` 只能生成诊断报告，不允许通过流程。人工覆盖必须逐项说明原阻断项修复情况。
6. `media-manifest.md` 和 `package-builder.md`：格式审核阶段对图片当前缺失可产生 `warn`，但发布包生成阶段必须复验文件存在性、路径边界、扩展名、大小、magic bytes、封面和格式审核状态。
7. `publisher.md`：第一版只实现 `ManualPublisher`，不得访问网络、不得登录小红书、不得保存账号密码。
8. `workspace-maintenance.md`：cleanup/archive 不得删除当前状态引用、最新完整产物、审计文件、产物索引或恢复链路引用。

## CLI 要求

使用 Typer 实现 `xhs-agent`。CLI 只负责参数解析、输出和提交确认信号，不承载业务流程逻辑。

至少实现以下命令：

```text
xhs-agent init
xhs-agent topic "<topic>"
xhs-agent import <article_path>
xhs-agent continue <task_id>
xhs-agent retry <task_id>
xhs-agent status <task_id>
xhs-agent list
xhs-agent review-content <task_id>
xhs-agent review-writing <task_id>
xhs-agent review-format <task_id>
xhs-agent package <task_id>
xhs-agent rollback <task_id> --to-phase <phase>
xhs-agent publish <task_id>
xhs-agent cleanup [--dry-run|--apply]
xhs-agent archive <task_id>
xhs-agent accounts list
xhs-agent accounts show <account_id>
xhs-agent config-check
```

全局参数包括 `--config` 和可重复的 `--set key=value`。`--set` 使用点号路径覆盖已声明配置字段，不能新增未知字段或替换整个嵌套表。

CLI 错误输出必须包含错误摘要、具体原因、建议下一步和相关文件路径，且不得展示密钥值。

## 数据与状态要求

必须实现 `doc/detailed_design.md` 第 7 节定义的核心枚举和数据模型，至少覆盖：

1. `TaskStatus`
2. `Severity`
3. `WritingStyle`
4. `ParseStatus`
5. `TaskMetadata`
6. `ArtifactRef`
7. `SourceRecord`
8. `ReviewIssue`
9. `ReviewReport`
10. `MediaItem`
11. `PublishPackage`
12. `AccountProfile`

任务目录位于 `workspace/<task_id>/`。机器读取文件包括 `task.json`、`artifacts.jsonl`、`audit_log.jsonl`。用户可读、可编辑的阶段产物使用 Markdown 并支持 YAML front matter。

`TaskMetadata.task_id` 按 `YYYYMMDD-<slug>-<rand4>` 生成，使用独占创建语义，冲突重试和上限按详细设计执行。

## 配置与安全要求

默认配置文件为 `config.toml`，密钥从 `.env` 和系统环境变量读取，系统环境变量优先级高于 `.env`。默认环境变量使用 `XHS_AGENT_` 前缀。

配置加载优先级：

1. 默认配置
2. `config.toml`
3. `.env`
4. 系统环境变量
5. CLI `--set`

`.env` 解析器只接受非空 `KEY=VALUE` 行，`KEY` 匹配 `[A-Za-z_][A-Za-z0-9_]*`。不支持引号、转义、变量展开、行内注释或 shell 语法。非法非空行必须返回 `ConfigError`。

`config-check` 只能展示缺失环境变量名，不能展示密钥值。

## 提示词与 LLM 要求

提示词集中放在 `src/xiaohongshu_auto_publish/llm/prompts.py` 或等价模板注册表中，不散落在业务模块里。

每个提示词必须有：

1. `prompt_id`
2. `version`
3. `schema_id`
4. `schema_version`
5. `template_hash`
6. `deprecated` 元数据支持

`template_hash` 使用 SHA-256，格式固定为 `sha256:<lowercase_hex_digest>`。哈希输入是注册表原始模板字符串，统一 LF 行尾并按 UTF-8 编码，不包含运行时变量值。

所有会影响流程判断的 LLM 输出必须结构化解析。解析异常必须区分 OK、PARTIAL、FAILED、schema 错误和关键风险字段错误。

测试中默认使用 `FakeLLMGateway`，不得访问真实外部模型。

## 调研、审核与发布边界

联网调研优先权威来源，至少覆盖国家或地区卫生健康主管部门、权威医学指南、公立医院/大学医学中心/专业医学机构、学术期刊/系统综述/指南共识、WHO、CDC 等来源。缺少发布日期时必须标记未知，不能伪造日期。

内容审核覆盖医学事实、健康风险、平台合规和用户误导风险。所有问题都必须展示。S0/S1 阻断，S2/S3 可提示后继续但必须保留确认和审计。

写作润色必须在内容审核通过后执行，不能为了点击率引入新的医学事实错误、疗效承诺、危险用药或替代正规治疗建议。

格式规则必须可配置，不得把可变化的小红书规则散落硬编码在审核模块中。

最终发布包必须汇总最终标题、正文、标签、素材清单、封面标题、内容审核结论、格式审核结论、来源清单、用户确认状态和 `can_publish`。

自动发布扩展本阶段只保留抽象和手动发布辅助。未来浏览器自动化或官方 API 通道不得影响当前主流程。

## 测试要求

每个模块都要有对应单元测试。核心流程和风险解析必须覆盖错误分支。

必须实现或补齐：

1. `tests/conftest.py`
2. `tests/factories.py`
3. `tests/fixtures/`
4. `tests/unit/test_config_loader.py`
5. `tests/unit/test_artifact_store.py`
6. `tests/unit/test_state_store.py`
7. `tests/unit/test_orchestrator.py`
8. `tests/unit/test_states.py`
9. `tests/unit/test_llm_gateway.py`
10. `tests/unit/test_search_provider.py`
11. `tests/unit/test_source_policy.py`
12. `tests/unit/test_research_service.py`
13. `tests/unit/test_content_review.py`
14. `tests/unit/test_review_output_parser.py`
15. `tests/unit/test_writing_review.py`
16. `tests/unit/test_format_rules.py`
17. `tests/unit/test_media_manifest.py`
18. `tests/unit/test_format_review.py`
19. `tests/unit/test_package_builder.py`
20. `tests/unit/test_asset_library.py`
21. `tests/unit/test_workspace_maintenance.py`
22. `tests/unit/test_publish_manual.py`
23. `tests/unit/test_cli.py`
24. `tests/integration/test_topic_workflow_with_fakes.py`
25. `tests/integration/test_article_workflow_with_fakes.py`

集成测试必须使用 Fake LLM、Fake SearchProvider、Fake Publisher，不访问真实网络。

并发和恢复测试至少覆盖：

1. 多任务并发创建和产物写入。
2. 同阶段并发保存不重复分配版本号。
3. 多账号资产索引并发追加和锁超时。
4. 内容审核 `ParseStatus.PARTIAL` 进入 `content_blocked`。
5. 格式审核图片缺失产生 `warn`，发布包生成复验失败。
6. 提示词锁定版本缺失进入可恢复失败，`--prompt-policy latest` 迁移后写入审计日志。

## 恢复手册

必须创建或维护 `doc/recovery.md`，至少包含：

1. `research_failed`
2. `content_blocked`
3. `writing_failed`
4. `format_blocked`
5. `failed`

每个章节包含适用场景、常见原因、用户检查项、推荐命令和不可绕过的阻断条件。`status` 输出应能给出同等恢复信息或指向对应章节。

## 工作方式

推荐执行流程：

1. 读取全部文档和任务拆分。
2. 审计当前仓库：文件树、`pyproject.toml`、`uv.lock`、已有代码、git 状态。
3. Phase 1：确定依赖版本范围，更新工程骨架、配置模块和账号模块。
4. Phase 2：完成产物存储、front matter、安全边界、状态存储和审计。
5. Phase 3：完成输入、状态迁移表、编排骨架和 CLI。
6. Phase 4：完成 LLM/Search 抽象、Fake provider、提示词注册表和结构化解析基础。
7. Phase 5 到 Phase 8：按任务文件逐模块实现和验收。
8. Phase 9：补齐完整集成测试、并发测试、恢复手册和全量质量闸门。
9. 更新 `doc/tasks/progress.md`，只勾选已经实现且通过验证命令的模块。
10. 运行最终命令并修复全部问题。

每完成一个模块，至少运行对应任务文件中的验证命令。每完成一个 Phase，运行该 Phase 相关测试。最终必须运行：

```text
uv run ruff format .
uv run ruff check .
uv run mypy src
uv run pytest
```

## 最终交付

完成后输出：

1. 实现摘要。
2. 主要新增和修改文件。
3. 已完成的 Phase 和模块。
4. 已运行的验证命令及结果。
5. 仍需注意的风险或后续事项。

如果所有质量闸门通过，明确说明 `ruff`、`mypy`、`pytest` 均已通过。不要用“应该可以”代替实际验证结果。
