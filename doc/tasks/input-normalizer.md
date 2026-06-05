# 选题/文章输入模块任务

来源：`detailed_design.md` 7.2、8.3、13  
目标文件：`src/xiaohongshu_auto_publish/input/normalizer.py`  
建议阶段：Phase 3  
前置依赖：配置管理模块、账号画像模块、状态模型、阶段产物存储模块  
完成定义：选题和已有文章都能规范化为任务元数据与初始 Markdown 产物。

## 最小任务

- [ ] 定义输入请求对象，覆盖选题文本、文章路径、粘贴正文、账号 ID、风格、受众、篇幅、系列化标记和可选 slug。
- [ ] 实现选题输入校验，空选题返回可读校验错误。
- [ ] 实现已有 Markdown 文件读取，使用 UTF-8，并在不可读或不存在时返回可操作错误。
- [ ] 实现粘贴文本导入，生成初始草稿正文。
- [ ] 实现写作风格默认值，未指定时使用 `popular`。
- [ ] 实现 slug 规范化：转小写、保留英文数字、空格下划线连字符归一为单个 `-`。
- [ ] 中文或非 ASCII 为主且无法生成 slug 时使用 `topic`，并返回提示用户可用 `--slug` 指定更清晰短名。
- [ ] 生成 `TaskMetadata`，包含输入类型、主题、账号、风格、受众、创建时间和初始状态。
- [ ] 为选题流程生成初始选题说明产物，为文章流程生成 `draft.v001.md`。
- [ ] 保留用户原始输入，不在规范化阶段调用 LLM 或搜索。
- [ ] 增加单元测试：空选题、UTF-8 Markdown 读取、粘贴文本导入、风格默认值。
- [ ] 增加 slug 测试：英文、空格、下划线、中文主题 fallback、用户指定 slug。

## 验证命令

- [ ] `uv run pytest tests/unit/test_input_normalizer.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/input tests/unit/test_input_normalizer.py`
