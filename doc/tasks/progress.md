# 模块任务总体进度

依据：

- `doc/proposal.md`
- `doc/high_level_design.md`
- `doc/detailed_design.md`，以第 8 节模块详细设计和第 15 节实现顺序为准

说明：

- 勾选模块表示该模块的任务文件中所有 checklist 已完成，并已通过对应单元测试或集成测试。
- 本文件只记录总体完成状态；具体可执行任务见各模块文件。

## Phase 1：工程与配置基础

- [x] [配置管理模块](config-management.md)
- [x] [账号画像/账号配置模块](account-profile.md)

## Phase 2：本地存储与状态

- [x] [阶段产物存储模块](artifact-store.md)
- [x] [状态与审核记录模块](state-store.md)

## Phase 3：编排骨架

- [x] [选题/文章输入模块](input-normalizer.md)
- [x] [流程编排模块](workflow-orchestrator.md)
- [x] [交互适配模块](interaction-adapter.md)

## Phase 4：外部能力适配

- [x] [LLM 网关模块](llm-gateway.md)
- [x] [联网检索服务](search-provider.md)

## Phase 5：调研与来源策略

- [x] [来源策略/白名单模块](source-policy.md)
- [x] [调研模块](research-service.md)

## Phase 6：审核核心

- [x] [内容审核模块](content-review.md)
- [x] [写作审核与润色模块](writing-review.md)

## Phase 7：格式与发布包

- [x] [格式规则模块](format-rules.md)
- [x] [素材元数据模块](media-manifest.md)
- [x] [格式审核模块](format-review.md)
- [x] [最终发布包模块](package-builder.md)

## Phase 8：资产、维护与发布辅助

- [x] [内容资产库/历史索引模块](asset-library.md)
- [x] [工作区清理与归档模块](workspace-maintenance.md)
- [x] [发布通道抽象模块](publisher.md)

## Phase 9：完整验证

- [x] 完整集成测试覆盖从选题开始的主流程
- [x] 完整集成测试覆盖从已有文章开始的主流程
- [x] 状态迁移矩阵覆盖合法迁移、非法迁移、确认、失败重试和 rollback
- [x] 并发负载测试覆盖任务创建、产物写入和资产索引追加
- [x] 恢复手册覆盖 `research_failed`、`content_blocked`、`writing_failed`、`format_blocked`、`failed`
- [x] 通过 `uv run ruff check .`
- [x] 通过 `uv run ruff format .`
- [x] 通过 `uv run mypy src`
- [x] 通过 `uv run pytest`
