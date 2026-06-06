# workspace 目录详解

`workspace/` 是本工具的本地任务工作区，默认由 `config.toml` 的 `[storage].workspace_dir` 指定。目录中的内容是运行时数据和生成产物，已在 `.gitignore` 中忽略，通常不提交到 git。

每个任务会写入 `workspace/<task_id>/`。任务 ID 由日期、slug 和随机后缀组成，例如 `20260606-codex-real-run-20260606-c2aa`。

## 总体修改原则

- 优先通过 CLI 生成、重试、审核和打包：`xhs-agent continue <task_id>`、`xhs-agent retry <task_id>`、`xhs-agent review-content <task_id>`、`xhs-agent review-format <task_id>`、`xhs-agent package <task_id>`。
- 可以手工修改标记为 `user_editable: true` 的 Markdown 正文内容，但不要随意修改 YAML front matter。
- 不要手工删除或改写 `task.json`、`artifacts.jsonl`、`audit_log.jsonl`，否则任务恢复、状态展示和产物追溯会失真。
- 产物文件按 `kind.vNNN.ext` 版本化保存。手工改当前版本可以解决文字问题；如果要保留旧稿并新增版本，应优先通过程序或 CLI 生成新版本，不建议手工追加索引。
- `workspace/` 中可能包含用户草稿、账号策略推断、调研材料和发布文案。清理前先确认内容不再需要。

## 根目录文件

| 路径 | 作用 | 如何修改 |
| --- | --- | --- |
| `workspace/<task_id>/task.json` | 当前任务状态文件，记录 `status`、选题、账号、重试次数、失败摘要和当前产物引用。 | 不建议手工修改。需要改变状态时使用 CLI；只有在明确知道状态机含义并做备份后，才可修复明显损坏的 JSON。 |
| `workspace/<task_id>/artifacts.jsonl` | 产物索引，每行一个 `ArtifactRef`，记录产物 ID、阶段、版本、路径、来源产物和是否可编辑。 | 不要手工改。新增、删除或重命名产物后若索引不同步，会导致 `latest()`、状态页和恢复链路读错文件。 |
| `workspace/<task_id>/audit_log.jsonl` | 审计日志，记录任务创建、状态迁移、失败、重试、确认、发布尝试等事件。 | 不要改历史事件。需要记录人工处理时，优先通过程序追加审计事件；手工追加必须保持 JSONL 单行合法。 |
| `workspace/maintenance_log.jsonl` | 工作区级维护日志，由 `cleanup --apply` 和 `archive <task_id>` 写入。 | 通常不改。排查清理或归档行为时读取。 |
| `workspace/<task_id>/*.lock` | 并发写入锁文件，例如 `state.lock`、`artifacts.lock`。 | 不要编辑。确认没有进程运行后，遗留空锁文件通常可以保留；只有锁文件导致误判且确认无进程占用时再处理。 |
| `workspace/<task_id>/*.tmp` | 原子写入过程中的临时文件，例如 `task.json.tmp`。 | 正常运行结束后不应存在。确认没有相关命令运行且目标文件完整时，可以删除遗留 `.tmp`。 |

## Markdown 产物通用结构

多数 Markdown 产物包含 YAML front matter：

```markdown
---
task_id: ...
artifact_id: revised-001
stage: drafts
kind: revised
version: 1
created_at: ...
source_artifacts:
- research-001
user_editable: true
complete: true
---

# 正文标题
```

字段含义：

| 字段 | 作用 | 修改建议 |
| --- | --- | --- |
| `task_id` | 所属任务 ID。 | 不改。 |
| `artifact_id` | 产物 ID，通常是 `kind-版本号`。 | 不改。 |
| `stage` | 产物阶段，如 `inputs`、`research`、`drafts`、`reviews`、`package`。 | 不改。 |
| `kind` | 产物类型，如 `topic`、`research`、`revised`。 | 不改。 |
| `version` | 同类型产物版本号。 | 不改。 |
| `created_at` | 创建时间。 | 不改。 |
| `source_artifacts` | 本产物来源，用于追溯和清理保护。 | 不改。 |
| `user_editable` | 是否设计为可人工编辑。 | 不改；按它判断是否适合手工修改正文。 |
| `complete` | 产物是否完整。失败或部分输出可能是 `false`。 | 不改；处理失败时用 `retry` 或重新生成。 |
| `error_type`、`retryable` | 部分产物的错误信息。 | 不改。 |

手工修改 Markdown 时，重点改 front matter 之后的正文；保留 `---` 分隔符和 UTF-8 编码。

## inputs/

| 文件 | 作用 | 如何修改 |
| --- | --- | --- |
| `inputs/topic.vNNN.md` | 选题入口产物，记录用户输入的主题、目标受众、写作风格等。 | 可修改正文里的选题说明、受众和补充要求。修改后继续流程会让后续审核读取更新后的内容。不要改 front matter。 |
| `inputs/article.vNNN.md` | 导入已有文章时的原始稿件。 | 可修正文案错别字、结构和补充材料。若需要重新导入另一个文件，优先使用 `xhs-agent import`。 |

## research/

| 文件 | 作用 | 如何修改 |
| --- | --- | --- |
| `research/research.vNNN.md` | 调研摘要、核心观点、谨慎表达和高风险说法。内容审核和写作润色会读取它。 | 可补充事实、删除不可靠结论、改写风险提示。医学、药物、疾病、儿童、孕产等高风险主题应保留证据边界。 |
| `research/sources.vNNN.md` | 来源清单，含 URL、标题、机构、发布日期、可信度、相关性和用户补充来源表。 | 可在“用户补充来源”表中补权威来源。不要伪造发布日期；未知日期保持“发布日期未知”。 |

## drafts/

| 文件 | 作用 | 如何修改 |
| --- | --- | --- |
| `drafts/draft.vNNN.md` | 初始草稿，通常来自导入文章或调研内容。 | 可直接修改正文、标题、段落和标签。修改后重新运行内容审核或写作审核。 |
| `drafts/revised.vNNN.md` | 写作润色后的稿件，通常包含“标题候选”“正文”“标签建议”“仍需用户确认”。 | 这是最常需要人工修改的文件。可调整标题、正文、标签和确认项；医学结论不应新增无来源事实。 |

`revised` 中如果出现逐字列表，例如：

```markdown
- 确
- 认
- 1
```

应合并为正常条目：

```markdown
- 确认1：未夸大疗效，所有结论均有研究支持
```

本仓库已在写作输出解析中增加防护：当模型把一句话返回为字符数组时，会先合并再渲染。

## reviews/

| 文件 | 作用 | 如何修改 |
| --- | --- | --- |
| `reviews/content_review.vNNN.md` | 内容审核报告，记录医学风险、平台风险、严重等级、阻断状态和修改建议。 | 通常用于阅读和定位问题，不建议把审核结论改成“通过”。应修改源稿后重新审核。 |
| `reviews/writing_review.vNNN.md` | 写作审核报告，记录开头优化、互动引导、账号一致性、系列化建议和关键改写。 | 可修正可读性问题或补充人工判断，但后续流程主要读取 `drafts/revised.vNNN.md`。 |
| `reviews/format_review.vNNN.md` | 格式审核报告，记录标题长度、正文长度、标签、封面标题和规则命中。 | 通常按报告修改 `drafts/revised.vNNN.md` 或 `media/media_manifest.json` 后重新审核。 |

审核报告是诊断材料。确有误判时，可以在草稿中调整表达并重新跑对应审核，优先保留可追溯链路。

## package/

| 文件 | 作用 | 如何修改 |
| --- | --- | --- |
| `package/final_package.vNNN.md` | 最终发布包，包含标题、正文、标签、封面标题、发布许可和素材问题。 | `user_editable` 通常为 `false`，不建议作为源稿修改。若发布前发现文案问题，应改 `drafts/revised.vNNN.md` 后重新生成发布包。 |
| `package/publish_manifest.vNNN.json` | 结构化发布清单，供发布通道读取，包含 `title`、`body`、`hashtags`、`cover_title`、`can_publish` 等字段。 | 不建议手工改。需要改变发布内容时重新生成发布包；需要排查发布问题时可读取。 |

`can_publish=true` 只表示本地规则和用户确认条件满足，不代表平台审核一定通过。

## media/

| 文件或目录 | 作用 | 如何修改 |
| --- | --- | --- |
| `media/media_manifest.json` | 素材清单，声明图片路径、角色、尺寸、比例、描述和是否可作为封面。 | 可手工创建或修改。路径必须是任务目录内相对路径，不支持远程 URL 或绝对路径。 |
| `media/images/` | 图片文件目录。 | 可放入 `.png`、`.jpg`、`.jpeg`、`.webp`。单图不超过 15 MB，扩展名和 magic bytes 必须匹配。 |

示例：

```json
{
  "items": [
    {
      "path": "media/images/cover.png",
      "role": "cover",
      "width": 1080,
      "height": 1080,
      "ratio": "1:1",
      "description": "封面图",
      "is_cover_candidate": true
    }
  ]
}
```

格式审核阶段缺图通常是 `warn`；发布包生成阶段会变成 `block`。

## archive/

`workspace/archive/<task_id>/` 是归档任务目录，由 `xhs-agent archive <task_id>` 移动生成。归档目录中会额外写入：

| 文件 | 作用 | 如何修改 |
| --- | --- | --- |
| `archived.json` | 归档标记，记录 `archived_at`。 | 不改。 |

不要手工移动任务到 `archive/`，否则任务审计日志和维护日志不会记录归档事件。

## 清理与恢复

- 查看候选清理项：`xhs-agent cleanup --dry-run`
- 执行清理：`xhs-agent cleanup --apply`
- 归档任务：`xhs-agent archive <task_id>`
- 查看状态：`xhs-agent status <task_id>`

清理模块不会删除 `task.json`、`artifacts.jsonl`、`audit_log.jsonl`、最新完整产物和仍被来源链路引用的产物。手工清理时也应遵守这些边界。

## 常见问题处理

| 问题 | 处理方式 |
| --- | --- |
| Markdown 出现逐字项目符号 | 合并为正常句子或列表项；后续版本已在写作解析处防护字符数组。 |
| `artifacts.jsonl` 指向的文件不存在 | 优先从备份恢复文件；如果确实被清理，确认是否符合保留策略，再重新生成对应阶段产物。 |
| `task.json` 状态与实际产物不一致 | 先用 `xhs-agent status <task_id>` 和 `audit_log.jsonl` 排查。不要直接改状态，优先使用 `retry`、`continue` 或 `rollback`。 |
| 发布包不是最新草稿内容 | 修改 `drafts/revised.vNNN.md` 后重新执行格式审核和打包。 |
| 素材路径校验失败 | 确认路径是任务目录内相对路径，文件存在，扩展名受支持，图片文件没有损坏。 |
