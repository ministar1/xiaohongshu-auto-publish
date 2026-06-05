# 写作审核与润色模块任务

来源：`detailed_design.md` 8.12、9、12、14  
目标文件：`src/xiaohongshu_auto_publish/review/writing.py`  
建议阶段：Phase 6  
前置依赖：内容审核模块、LLM 网关、账号画像模块、内容资产库接口、阶段产物存储  
完成定义：内容审核通过后可生成小红书风格润色稿和写作审核报告，不引入新的医学风险。

## 最小任务

- [ ] 定义写作审核请求对象，包含最新通过审核稿件、内容审核报告、账号画像、历史内容索引、写作风格。
- [ ] 支持风格枚举 `popular`、`professional`、`balanced`，默认 `popular`。
- [ ] 从配置读取标题候选数量和系列化建议开关。
- [ ] 构造写作润色 LLM 请求，传入账号定位、受众、禁用表达、语气和历史风格参考。
- [ ] 输出 `revised.vNNN.md`，包含标题候选、最终候选正文、标签建议和需要用户确认的表达。
- [ ] 输出 `writing_review.vNNN.md`，包含开头优化说明、关注引导、互动引导、账号一致性评价、系列化建议、关键改写说明。
- [ ] 在 prompt 和输出校验中约束不得新增医学事实、疗效承诺、危险用药或替代治疗建议。
- [ ] 写作解析失败时进入 `writing_failed` 的可诊断结果，保留上一版可用草稿和原始输出摘要。
- [ ] 标记所有仍需用户确认的表达，供编排层停在 `waiting_draft_edit`。
- [ ] 空历史资产库应可正常运行，不影响润色。
- [ ] 增加单元测试：默认风格为 `popular`，`professional` 改变提示参数，标题候选数量来自配置。
- [ ] 增加单元测试：输出包含账号一致性评价、系列化建议、关键改写和需确认表达。
- [ ] 增加编排测试：内容审核未通过时不调用写作审核。
- [ ] 增加安全测试：LLM 输出含禁用表达或夸大承诺时被标记为需确认或失败。

## 验证命令

- [ ] `uv run pytest tests/unit/test_writing_review.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/review tests/unit/test_writing_review.py`
