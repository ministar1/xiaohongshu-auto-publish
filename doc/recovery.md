# 错误恢复手册

## research_failed

- 适用场景：联网检索失败、搜索无结果、高风险主题缺少权威来源。
- 常见原因：Tavily Key 缺失、网络不可用、选题过窄、来源全部为未知来源。
- 用户检查项：检查 `config-check` 输出，编辑最新 `sources.vNNN.md` 的“用户补充来源”小节。
- 推荐命令：`xhs-agent retry <task_id>`。
- 不可绕过条件：疾病治疗、药物、剂量、诊断、孕产、儿童、慢病管理等高风险主题必须补充权威来源。

## content_blocked

- 适用场景：出现 S0/S1 问题、结构化输出解析失败、`ParseStatus.PARTIAL`、schema 错误或关键风险字段错误。
- 常见原因：危险用药建议、疗效承诺、替代正规治疗、模型输出 JSON 不完整。
- 用户检查项：修改最新草稿，逐项处理内容审核报告中的阻断问题。
- 推荐命令：`xhs-agent review-content <task_id>` 或 `xhs-agent continue <task_id>`。
- 不可绕过条件：`--yes` 和 `--force-parse` 都不能绕过 S0/S1 或解析风险。

## writing_failed

- 适用场景：写作润色 LLM 调用失败或输出无法解析。
- 常见原因：模型返回非 JSON、服务超时、输出包含禁用表达或夸大承诺。
- 用户检查项：保留上一版可用草稿，手动编辑后重新润色。
- 推荐命令：`xhs-agent retry <task_id>` 或 `xhs-agent review-writing <task_id>`。
- 不可绕过条件：写作阶段不得新增医学事实、疗效承诺、危险用药或替代正规治疗建议。

## format_blocked

- 适用场景：格式规则 `block` 命中、manifest 缺少必需角色、素材路径越界、远程 URL 或比例/数量硬规则失败。
- 常见原因：敏感词、标题过长、封面候选缺失、素材 manifest 写错。
- 用户检查项：修改最新润色稿或 `media/media_manifest.json`。
- 推荐命令：`xhs-agent review-format <task_id>`。
- 不可绕过条件：格式 `block` 不能通过 `--yes` 跳过。

## failed

- 适用场景：发布包生成、发布尝试或提示词版本恢复失败。
- 常见原因：`last_failed_stage="package"` 时素材文件被删除；`publish` 未确认；旧提示词版本缺失。
- 用户检查项：查看 `xhs-agent status <task_id>` 的失败摘要和相关产物。
- 推荐命令：`xhs-agent package <task_id>`、`xhs-agent retry <task_id>` 或 `xhs-agent retry <task_id> --prompt-policy latest`。
- 不可绕过条件：发布包生成阶段必须复验素材存在性、路径边界、扩展名、大小、magic bytes 和封面要求。
