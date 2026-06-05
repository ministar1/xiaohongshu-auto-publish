# 调研模块任务

来源：`detailed_design.md` 8.10、13、14  
目标文件：`src/xiaohongshu_auto_publish/research/service.py`、`src/xiaohongshu_auto_publish/research/renderer.py`  
建议阶段：Phase 5  
前置依赖：配置管理、阶段产物存储、状态存储、LLM 网关、联网检索服务、来源策略、流程编排骨架  
完成定义：选题可生成可编辑调研资料和来源清单，高风险缺源时能给出可执行恢复指引。

## 最小任务

- [ ] 定义调研请求和响应对象，输入包含 `TaskMetadata`、选题、受众、账号定位、风格。
- [ ] 实现检索查询生成，至少覆盖核心选题、权威指南、公共卫生机构和中文健康科普来源。
- [ ] 调用 `SearchProvider` 获取结果，并记录检索时间。
- [ ] 使用 `SourcePolicy.rank()` 对来源排序和筛选。
- [ ] 调用 LLM 汇总核心结论、可引用事实、谨慎表达、不建议使用说法和结构建议。
- [ ] 渲染 `research.vNNN.md`，包含选题摘要、核心观点、可引用事实、风险说法、来源概览。
- [ ] 渲染 `sources.vNNN.md`，包含来源链接、机构、发布日期或未知标记、可信度说明、相关性说明。
- [ ] `sources.vNNN.md` 设置 `user_editable=true`，并包含“用户补充来源”小节。
- [ ] 用户补充来源表格字段包含 `url`、`title`、`organization`、`published_at`、`reason`。
- [ ] 实现补充来源解析和去重，重试时合并用户补充来源和重新检索结果。
- [ ] 高风险主题缺少权威来源时生成失败产物，进入 `research_failed`，提示编辑最新 `sources.vNNN.md` 后执行 `xhs-agent retry <task_id>`。
- [ ] 搜索无结果时返回可恢复失败，并保存可诊断的部分产物。
- [ ] LLM 返回不完整时仍保留原始来源清单，不丢失检索证据。
- [ ] 增加单元测试：输出包含链接、机构、发布日期或未知、可信度说明。
- [ ] 增加失败测试：搜索无结果、高风险缺权威来源、LLM 不完整输出。
- [ ] 增加重试测试：用户补充来源被重新读取、去重并进入排序。

## 验证命令

- [ ] `uv run pytest tests/unit/test_research_service.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/research tests/unit/test_research_service.py`
