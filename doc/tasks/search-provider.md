# 联网检索服务任务

来源：`detailed_design.md` 8.8、11、12  
目标文件：`src/xiaohongshu_auto_publish/search/provider.py`、`src/xiaohongshu_auto_publish/search/tavily_provider.py`  
建议阶段：Phase 4  
前置依赖：配置管理模块、错误模型、核心数据模型  
完成定义：调研模块可通过可替换接口获取结构化搜索结果，测试默认不访问真实网络。

## 最小任务

- [ ] 定义 `SearchProvider` Protocol：`search(query: str, max_results: int) -> list[SearchResult]`。
- [ ] 定义 `SearchResult`，包含 `title`、`url`、`snippet`、`source_name`、`published_at`、`retrieved_at`。
- [ ] 实现 Tavily provider 初始化，读取配置中的 provider、API Key 环境变量、超时和最大结果数。
- [ ] 缺少 Tavily API Key 时返回 `ConfigError`，错误中只展示环境变量名。
- [ ] 将 Tavily 外部响应映射为内部 `SearchResult`，缺失发布时间时保留 `None` 或未知标记。
- [ ] 实现搜索超时、失败重试和可重试 `SearchError`。
- [ ] 实现 Fake SearchProvider，支持固定结果、空结果、失败和延迟。
- [ ] 保留原始搜索结果快照所需字段，供调研模块重试时写入新版产物。
- [ ] 增加单元测试：外部响应字段映射、缺少 API Key、失败可重试、空结果。
- [ ] 增加集成辅助测试：调研模块可通过 Fake SearchProvider 独立测试且不访问网络。

## 验证命令

- [ ] `uv run pytest tests/unit/test_search_provider.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/search tests/unit/test_search_provider.py`
