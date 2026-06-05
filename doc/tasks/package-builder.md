# 最终发布包模块任务

来源：`detailed_design.md` 8.16、12、13、14  
目标文件：`src/xiaohongshu_auto_publish/package/builder.py`  
建议阶段：Phase 7  
前置依赖：内容审核模块、格式审核模块、素材元数据模块、阶段产物存储、状态存储  
完成定义：最终发布包和发布清单可生成，`can_publish` 必须基于最新审核、确认和素材复验。

## 最小任务

- [ ] 定义 `PublishPackage` 和 `PublishManifest` 数据模型。
- [ ] 读取最新确认版本的标题、正文、标签、封面标题、来源清单和素材 manifest。
- [ ] 汇总内容审核结论、格式审核结论、来源清单和用户确认状态。
- [ ] 在生成发布清单前重新读取 `media_manifest.json`，不得只信任旧格式审核结果。
- [ ] 重新校验所有素材路径仍存在、位于任务目录内、扩展名允许、非空、大小合法、magic bytes 有效。
- [ ] 若配置要求封面图，必须存在 `role="cover"` 或 `is_cover_candidate=true` 的素材。
- [ ] 实现 `can_publish=true` 必要条件：内容审核通过、格式审核通过、confirm 已确认、素材校验通过、用户发布前确认完成。
- [ ] 素材复验失败时仍生成 `publish_manifest.vNNN.json`，但 `media_validation_passed=false`、`can_publish=false`。
- [ ] 复验失败应让编排层进入 `failed`，并设置 `last_failed_stage="package"`。
- [ ] 渲染 `final_package.vNNN.md`，包含最终标题、正文、标签、素材清单、封面标题、审核摘要、来源清单、发布许可状态。
- [ ] 生成 `publish_manifest.vNNN.json`，字段与详细设计示例保持兼容。
- [ ] 为手动发布辅助和未来自动发布通道提供统一读取接口。
- [ ] 增加单元测试：内容审核未通过、格式审核未通过、用户未确认时 `can_publish=false`。
- [ ] 增加成功测试：审核通过、确认完成、素材有效时生成完整发布清单。
- [ ] 增加素材失败测试：图片删除、缺封面、非法扩展名、magic bytes 失败时不能发布。

## 验证命令

- [ ] `uv run pytest tests/unit/test_package_builder.py`
- [ ] `uv run ruff check src/xiaohongshu_auto_publish/package tests/unit/test_package_builder.py`
