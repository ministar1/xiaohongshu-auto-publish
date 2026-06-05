# 素材元数据模块任务

来源：`detailed_design.md` 8.14、12  
目标文件：`src/xiaohongshu_auto_publish/media/manifest.py`  
建议阶段：Phase 7  
前置依赖：配置管理模块、格式规则模块、错误模型  
完成定义：素材 manifest 可结构化读取和校验，格式审核阶段预警，发布包阶段硬校验。

## 最小任务

- [ ] 定义 `MediaItem`、`MediaManifest`、`ImageValidationResult`、`MediaValidationIssue`。
- [ ] 读取 `media/media_manifest.json`，校验根结构和 `items` 列表。
- [ ] 校验字段完整性：`path`、`role`、`width`、`height`、`ratio`、`description`、`is_cover_candidate`。
- [ ] 所有素材路径必须是任务目录内本地相对路径，禁止路径逃逸。
- [ ] 不支持远程 URL，不下载网络图片。
- [ ] 校验角色、数量、封面候选和比例字段，供格式审核读取。
- [ ] 提供阶段化校验模式：格式审核阶段文件缺失为 `warn`，发布包生成前文件缺失为 `block`。
- [ ] 实现 `validate_image_file(path)`，检查扩展名、文件存在、非空、大小范围和基础 magic bytes。
- [ ] 允许扩展名仅为 `.png`、`.jpg`、`.jpeg`、`.webp`。
- [ ] 如果无法读取实际像素尺寸，记录降级原因到 `media_validation_issues`。
- [ ] 不新增 Pillow 等运行时依赖，除非用户后续明确确认。
- [ ] 增加单元测试：路径不存在、路径逃逸、远程 URL、比例读取、manifest 字段缺失。
- [ ] 增加图片校验测试：非法扩展名、空文件、magic bytes 不匹配、合法 png/jpg/webp 头。
- [ ] 增加阶段化测试：格式审核阶段缺失图片为 warn，发布包生成前为硬阻断。

## 验证命令

- [ ] `uv run pytest tests/unit/test_media_manifest.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/media tests/unit/test_media_manifest.py`
