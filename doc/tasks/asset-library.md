# 内容资产库/历史索引模块任务

来源：`detailed_design.md` 8.19、12  
目标文件：`src/xiaohongshu_auto_publish/assets/library.py`、`src/xiaohongshu_auto_publish/assets/lock.py`  
建议阶段：Phase 8  
前置依赖：配置管理模块、账号画像模块、最终发布包模块、错误模型  
完成定义：历史内容按账号分片追加和查询，并发写入有锁保护。

## 最小任务

- [ ] 定义历史索引记录模型，包含任务 ID、账号 ID、主题、标题、标签、系列归属、创建时间、审核结论摘要。
- [ ] 索引文件按账号分片：`workspace/assets_index.<account_id>.jsonl`。
- [ ] 实现 `LockFile` 封装，接口为 `acquire(timeout_seconds: float) -> LockHandle`，支持 context manager。
- [ ] 内部优先封装 `filelock.FileLock`，默认等待超时建议 10 秒。
- [ ] 超时返回可重试 `LockError`，不得无锁写入。
- [ ] 实现追加索引：获取账号分片锁后追加完整 JSON 行，写入后 flush。
- [ ] 单条记录一次性追加，不拆分多次写入。
- [ ] 异常退出不根据 mtime 自动删除锁文件，避免误删仍被持有的锁。
- [ ] 实现按账号过滤历史内容。
- [ ] 实现按关键词查询历史内容，供写作审核做人设和系列化参考。
- [ ] 空资产库返回空列表，不影响写作审核。
- [ ] 跨账号检索时读取多个分片并在内存中合并，不使用全局唯一写入点。
- [ ] 增加单元测试：任务完成后追加索引，按账号过滤，关键词查询，空资产库。
- [ ] 增加多账号测试：不同账号写入不同索引文件。
- [ ] 增加并发和锁测试：超时返回可重试错误，索引文件不损坏，Fake Lock 与真实封装语义一致。

## 验证命令

- [ ] `uv run pytest tests/unit/test_asset_library.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/assets tests/unit/test_asset_library.py`
