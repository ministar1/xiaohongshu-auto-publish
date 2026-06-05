# 发布通道抽象模块任务

来源：`detailed_design.md` 8.17、14  
目标文件：`src/xiaohongshu_auto_publish/publish/base.py`、`src/xiaohongshu_auto_publish/publish/manual.py`  
建议阶段：Phase 8  
前置依赖：最终发布包模块、流程编排模块  
完成定义：第一版仅支持手动发布辅助，不登录小红书，不访问网络，不保存账号密码。

## 最小任务

- [ ] 定义最小 `Publisher` Protocol：`publish(package: PublishPackage, confirmed: bool) -> PublishResult`。
- [ ] 定义 `PublishResult`，包含 `success`、`channel`、`message`、`retryable`、`published_url`、`raw_artifact_path`。
- [ ] 第一版不在协议中定义 `get_status()` 或 `cancel()`，避免编排层依赖不存在的远端能力。
- [ ] 实现 `ManualPublisher`，只输出手动发布辅助信息和本地产物路径。
- [ ] 未确认发布时拒绝发布，返回可读失败原因。
- [ ] `can_publish=false` 时拒绝发布，并说明缺失条件。
- [ ] 手动发布辅助不得访问网络、不得登录小红书、不得保存账号密码或明文凭据。
- [ ] 发布尝试结果写入状态与审计记录，供 `status` 展示。
- [ ] 为未来官方 API、浏览器自动化、第三方工具保留替换通道，不把具体实现写入主流程。
- [ ] 增加单元测试：未确认拒绝、`ManualPublisher` 不访问网络、失败原因可读。
- [ ] 增加编排测试：编排层只依赖 `Publisher` 协议，不调用状态查询或取消能力。

## 验证命令

- [ ] `uv run pytest tests/unit/test_publish_manual.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/publish tests/unit/test_publish_manual.py`
