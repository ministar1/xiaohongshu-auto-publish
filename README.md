# 小红书医学/养生科普 Agent

这是一个本地运行的 Python CLI 工具，用于辅助完成医学、养生、健康科普类小红书内容的调研、内容审核、写作润色、格式审核、发布包生成和手动发布辅助。

项目的核心原则是：关键阶段都生成本地 Markdown 文件，用户可以直接编辑；医学与平台风险会被结构化审核；严重问题不能被 `--yes` 跳过；第一版只做手动发布辅助，不登录小红书，不绕过验证码、风控或平台安全机制。

## 适合谁

适合希望持续发布医学、养生、健康科普内容的个人创作者或小团队。你可以从一个选题开始，让工具先做调研；也可以导入已经写好的 Markdown 文章，直接进入审核、润色和发布包流程。

## 你将得到什么

- `xhs-agent` 命令行工具。
- 本地任务工作区：每个任务都有独立目录、状态文件、审计日志和版本化产物。
- 调研资料、来源清单、内容审核报告、润色稿、格式审核报告、最终发布包。
- 可配置的账号画像、来源策略、小红书格式规则。
- 可替换的 LLM、搜索和发布通道抽象。
- Fake provider 单元测试和集成测试，不依赖真实网络。

## 安全边界

- 不把 API Key 写入代码、Markdown 产物、JSONL 日志或错误输出。
- `.env` 已被 `.gitignore` 忽略，只提交 `.env.example`。
- `config-check` 只显示缺失的环境变量名，不显示密钥值。
- 第一版发布通道是 `ManualPublisher`，只给出手动复制发布提示。
- 不登录小红书，不保存账号密码，不绕过验证码、风控或平台安全机制。
- 这个工具不能替代医生、药师、营养师或合规人员审核。

## 环境要求

- Python 3.11 或更高版本。
- `uv`，用于依赖、虚拟环境和命令运行。
- Windows PowerShell、PowerShell 7、macOS 或 Linux shell 均可使用；本项目当前在 Windows + Python 3.13 环境下通过验证。

安装 `uv` 可参考官方文档，已安装后确认：

```powershell
uv --version
```

## 第一次运行

克隆仓库后进入项目目录：

```powershell
cd xiaohongshu_auto_publish
uv sync
```

确认 CLI 可用：

```powershell
uv run xhs-agent --help
```

初始化本地配置、账号示例、规则示例和工作区：

```powershell
uv run xhs-agent init
```

如果仓库里已经带有示例 `config.toml`、`accounts/default.toml` 和 `rules/*.toml`，再次执行 `init` 不会覆盖既有文件。需要覆盖时使用：

```powershell
uv run xhs-agent init --overwrite
```

## 配置密钥

复制示例文件：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`：

```env
XHS_AGENT_LLM_API_KEY=
XHS_AGENT_TAVILY_API_KEY=
XHS_AGENT_LLM_MODEL=deepseek-v4-flash
```

默认配置文件是 [config.toml](config.toml)，LLM 默认使用 DeepSeek OpenAI-compatible API。密钥读取优先级是：

1. 默认配置
2. `config.toml`
3. `.env`
4. 系统环境变量
5. CLI `--set section.field=value`

系统环境变量优先级高于 `.env`。检查配置：

```powershell
uv run xhs-agent config-check
```

如果只想本地体验 CLI、状态、产物和测试，可以暂时不配置真实密钥；真实调研和 LLM 审核需要配置密钥。

## 快速工作流：从选题开始

创建一个选题任务：

```powershell
uv run xhs-agent topic "睡眠不足与代谢问题" --slug sleep-metabolism
```

输出会包含任务 ID，例如：

```text
任务 ID：20260605-sleep-metabolism-a1b2
状态：waiting_research_edit
下一步：xhs-agent continue 20260605-sleep-metabolism-a1b2
```

查看状态：

```powershell
uv run xhs-agent status <task_id>
```

继续流程：

```powershell
uv run xhs-agent continue <task_id>
```

常见阶段：

- `waiting_research_edit`：调研资料已生成，等待用户编辑或确认。
- `content_blocked`：内容审核存在 S0/S1 或解析风险，必须修改后重审。
- `content_passed_with_warnings`：只有 S2/S3，展示全部问题，确认后可继续。
- `waiting_draft_edit`：润色稿已生成，等待用户编辑或确认。
- `format_blocked`：格式规则阻断，必须修改。
- `waiting_format_confirm`：格式问题需要用户确认。
- `package_ready`：发布包已生成。

## 快速工作流：导入已有文章

准备一个 Markdown 文件，例如 `article.md`，然后执行：

```powershell
uv run xhs-agent import .\article.md --topic "高血压低盐饮食" --slug low-salt
```

导入流程会跳过调研入口，生成初始草稿并进入内容审核入口。

## 常用命令

```text
xhs-agent init
xhs-agent topic "<topic>"
xhs-agent import <article_path>
xhs-agent continue <task_id>
xhs-agent retry <task_id>
xhs-agent status <task_id>
xhs-agent list
xhs-agent review-content <task_id>
xhs-agent review-writing <task_id>
xhs-agent review-format <task_id>
xhs-agent package <task_id>
xhs-agent rollback <task_id> --to-phase <phase>
xhs-agent publish <task_id>
xhs-agent cleanup [--dry-run|--apply]
xhs-agent archive <task_id>
xhs-agent accounts list
xhs-agent accounts show <account_id>
xhs-agent config-check
```

全局参数：

```powershell
uv run xhs-agent --config .\config.toml --set llm.timeout_seconds=120 config-check
```

`--set` 只能覆盖已声明字段，不能新增未知字段，也不能把整个嵌套表替换成字符串。

## 账号画像

默认账号配置在 [accounts/default.toml](accounts/default.toml)：

```toml
account_id = "default"
positioning = "医学与养生科普账号"
audience = "关注健康生活方式的普通读者"
tone = "通俗、谨慎、不过度承诺"
forbidden_phrases = ["根治", "保证有效", "替代治疗"]
```

查看账号：

```powershell
uv run xhs-agent accounts list
uv run xhs-agent accounts show default
```

新增账号时，在 `accounts/` 下创建 `<account_id>.toml`，并确保文件名和 `account_id` 一致。

## 规则文件

来源策略：

- [rules/source_policy.toml](rules/source_policy.toml)
- 用于维护可信来源和风险来源。
- 缺失发布日期会标记为“发布日期未知”，不会伪造日期。
- 高风险主题如果全部是未知来源，会进入可恢复失败。

格式规则：

- [rules/xhs_format_rules.toml](rules/xhs_format_rules.toml)
- 支持标题、正文、标签、表情、素材和敏感词规则。
- 严重程度包括 `block`、`confirm`、`warn`。

格式审核阶段如果图片当前缺失，会生成 `warn`；发布包生成阶段会重新校验素材文件，缺失会硬失败。

## 工作区结构

任务数据默认写入 `workspace/<task_id>/`。`workspace/` 不提交到 git。

典型结构：

```text
workspace/
  <task_id>/
    task.json
    artifacts.jsonl
    audit_log.jsonl
    inputs/
    research/
    drafts/
    reviews/
    package/
    media/
      media_manifest.json
      images/
```

说明：

- `task.json`：当前任务状态。
- `artifacts.jsonl`：版本化产物索引。
- `audit_log.jsonl`：状态更新、确认、失败、重试、回滚、发布尝试等审计事件。
- Markdown 产物允许用户直接编辑。
- 产物使用 `kind.vNNN.ext` 命名，不覆盖旧版本。

## 素材 manifest

如果任务需要图片，在任务目录下创建：

```text
workspace/<task_id>/media/media_manifest.json
```

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

限制：

- 只支持任务目录内的本地相对路径。
- 不支持远程 URL，不下载网络图片。
- 允许扩展名：`.png`、`.jpg`、`.jpeg`、`.webp`。
- 发布包生成前会复验文件存在性、大小、扩展名和 magic bytes。

## 审核分级

| 等级 | 是否阻断 | 说明 |
| --- | --- | --- |
| S0 | 是 | 严重医学风险、危险建议、严重违规 |
| S1 | 是 | 高风险误导，必须修改 |
| S2 | 否 | 中风险提示，需要展示并确认 |
| S3 | 否 | 轻微问题或风格建议 |

`--yes` 不能绕过：

- S0/S1
- `ParseStatus.PARTIAL`
- 结构化解析失败
- schema 错误
- 关键风险字段错误
- 格式 `block`
- 发布包素材复验失败
- 发布前确认

## 发布

第一版只支持手动发布辅助：

```powershell
uv run xhs-agent publish <task_id> --confirmed
```

发布前必须已有最终发布包，且 `can_publish=true`。工具不会访问小红书网络服务，不会登录账号，也不会保存账号密码。

## 失败恢复

恢复手册见 [doc/recovery.md](doc/recovery.md)。覆盖：

- `research_failed`
- `content_blocked`
- `writing_failed`
- `format_blocked`
- `failed`

先查看任务状态：

```powershell
uv run xhs-agent status <task_id>
```

常见恢复命令：

```powershell
uv run xhs-agent retry <task_id>
uv run xhs-agent review-content <task_id>
uv run xhs-agent review-format <task_id>
uv run xhs-agent package <task_id>
```

## 开发者快速检查

格式化：

```powershell
uv run ruff format .
```

Lint：

```powershell
uv run ruff check .
```

类型检查：

```powershell
uv run mypy src
```

测试：

```powershell
uv run pytest
```

本仓库当前验证结果：

- `uv run ruff format .`：通过
- `uv run ruff check .`：通过
- `uv run mypy src`：通过
- `uv run pytest`：通过，60 个测试

## 项目结构

```text
src/xiaohongshu_auto_publish/
  cli.py                  # Typer CLI
  app.py                  # 应用装配
  errors.py               # 统一错误模型
  models.py               # 核心 dataclass 和枚举
  config/                 # 配置加载、.env 严格解析、init 模板
  account/                # 账号画像
  artifacts/              # front matter 和版本化产物存储
  state/                  # task.json、audit_log.jsonl、任务 ID
  input/                  # 选题和文章导入规范化
  orchestration/          # 状态迁移表和编排器
  llm/                    # LLM 网关、Fake LLM、提示词注册表
  search/                 # SearchProvider、Tavily、Fake Search
  source_policy/          # 来源策略和高风险缺源判断
  research/               # 调研服务和 Markdown 渲染
  review/                 # 内容审核、写作审核、格式审核
  rules/                  # 小红书格式规则
  media/                  # 素材 manifest 和图片基础校验
  package/                # 最终发布包和发布清单
  publish/                # Publisher Protocol 和 ManualPublisher
  assets/                 # 历史资产索引
  maintenance/            # cleanup 和 archive
```

测试目录：

```text
tests/
  unit/
  integration/
  factories.py
  conftest.py
```

## 进一步阅读

- [doc/proposal.md](doc/proposal.md)：需求文档
- [doc/high_level_design.md](doc/high_level_design.md)：概要设计
- [doc/detailed_design.md](doc/detailed_design.md)：详细设计
- [doc/tasks/progress.md](doc/tasks/progress.md)：模块完成状态
- [doc/implementation_decisions.md](doc/implementation_decisions.md)：实现决策记录
- [doc/recovery.md](doc/recovery.md)：错误恢复手册
