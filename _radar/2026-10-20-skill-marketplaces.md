# Radar 2026-10-20 —— 第三方 skill 目录调研（skillselion 等）

焦点：skillselion.com 作为**发现渠道**可不可信；其中 meta skill 与「搜集 skill 的 skill」的供应链与数据外流风险；第三方 skill 引进政策建议。
来源 lane：`agent_coding_guidelines/skill-market-survey`（campaign 制，任务书在仓外 handoffs）。问答议题 `dce1289c-06af-4117-99d4-5ca1762a94de`。

> 证据等级逐条标注：**实测**（本机抓取 / 比对 / 读 API）、**读自源码或页面**、**它声称**（站方宣传数字）、**推测**。全部判断为单人一次判断，无对抗核验；诚实边界见第五节。
> 约束遵守情况：全程未安装、未执行任何第三方 skill / 脚本 / MCP；只下载源码到会话临时目录的独立子目录读取；查询词不含项目名；未向外部站点发送任何公司内容。

## 一、站点本身（结论：可当索引，不能当信任来源）

| 问题 | 结论 | 证据 |
|---|---|---|
| 谁运营 | Ellelion LLC（美国怀俄明注册），同一家还做 Launchelion、Agent Plugins Directory、botteams.io；联系邮箱 info@skillselion.com；Product Hunt 2026-08 上线，0 评论 5 关注 | 读自页面（/about、/contact、Product Hunt） |
| 条目怎么进来 | 全靠抓取：2000 条样本里 1980 条 `source=ingested`、20 条 `official-vendor`；公开提交与评论 2026 年已关闭（`/submit` 302 回首页，contact 页明说只剩邮件） | 实测 + 读自页面 |
| 安装量从哪来 | **就是 skills.sh（Vercel）的累计安装事件计数**：它自己说「refreshed daily from the skills.sh registry」；`find-skills` 在它 API 里 3,944,520、skills.sh 首页 3.9M，一致。Vercel 自述该计数「do not represent unique people or necessarily independent choices」。排名因此是 skills.sh 排行榜的镜像；其 methodology 页还记了 skills.sh 详情接口与公开数相差「数量级」的异常（2026-08-16） | 实测 + 读自页面 |
| 有没有审核 | **没有安全审核**。About 页的四道「质量门」全是运营门槛（最低信号、fork 合并、死仓清理、编辑文案审查）。数据实测：2000 条样本 `verifiedSafe` 全 false、`trustScore` 全 0、`scan` 全空、`audit` 全 null；`riskLevel` 仅 275 条有值，且来自 skills.sh 转发的第三方审计（Socket / Snyk / Gen Agent Trust Hub / ZeroLeaks / Runlayer）。它的 methodology 页也承认「Verified-Safe 和 trust score 列未填充」 | 实测 + 读自页面 |
| 许可证怎么标 | 基本不标：样本 1963/2000 条 `license` 为空；它自己的 Clone Census 称 98.2% 的 skill 未声明许可证 | 实测 + 它声称 |
| 规模数字 | 自相矛盾：`/api/upstream/meta` 说 6,700+（dated 2026-06-06）、About 81,000+、MCP README 86,000+、llms.txt 85,807、`/api/upstream/catalog/stats` 86,537 listings / 63,954 skills（2026-10-20） | 实测 |
| 抓取可否复现 | 可以：目录 API 公开无鉴权（`limit` 最大 2000、有 `offset`），120 次/分钟；抽 3 条缓存副本（find-skills、agentpowers、browse-and-evaluate）SKILL.md 与 GitHub 原件 sha256 **逐字节一致**。但 `starchild-ai-agent/official-skills#skillmarketplace` 的缓存副本（4086 B）在上游 `main` 树（150 个 SKILL.md，未截断）里**已不存在该路径**——缓存会继续供应上游已删除或改名的内容 | 实测 |
| 元数据新鲜度 | 它声称 GitHub stars 与仓库元数据「每日重扫」。实测 2026-10-20：`mattpocock/skills` 在它那里 stars 252,771、pushed 2026-09-04，GitHub API 同日 297,992、pushed 2026-10-19；`juliusbrussee/caveman` 103,813 对 113,748。落后约六周 | 实测 对 它声称 |
| 商业 | Terms 有付费「Sponsored」位（$29/月起），声称不影响排名 | 读自页面 |
| 隐私 | MCP API 请求有服务端遥测（盐化 IP+UA 标识），浏览器端隐私开关管不到 | 读自页面 |
| 研究页 | 方法论诚实（冻结法、CSV 可复算、「不发布空字段的通过率」），Security Census 的数字可引用但要注明是 skills.sh 转发的审计 | 读自页面 |

**同类站点一眼**（均未深入，读自页面或搜索摘要）：skills.sh（Vercel，排行榜源头，未公布安全审核，CLI 遥测 `DO_NOT_TRACK=1` 可关）；SkillsMP（自报 200 万+，无审核）；Skills Directory（自报 19 万，声称 120 模式自动扫描，本次站点连不上未核实）；AgenticSkills（193 条人工编辑，自己写的对比页）。**更可信的渠道是官方市场**：Claude Code 的 `claude-plugins-official` / `anthropics/skills`（官方名字受保护，社区市场几乎逐条钉 commit SHA）与 `openai/skills` 的 `.curated`。

## 二、远程加载 MCP（`skillselion-mcp` 0.9.11，源码 1389 行已通读）

| 事实 | 判定 |
|---|---|
| 外发：搜索 GET 带 `q`（分词变体）与 `semantic=原始查询词`（**未 scrub**）；POST `/mcp/demand` 带 scrub 后的 query、是否匹配、skillId、分数（`DO_NOT_TRACK` / `SK_NO_DEMAND` 可关）；GET `/mcp/lessons/active` 让服务端下发 prefer/block 偏置排名；`context` 参数确实不外发 | README「只发 scrub 过的搜索词」不完全准确，搜索请求里是原文；查询词由 agent 现场拼写 |
| `load_skill` 把 SKILL.md + 捆绑脚本写到 `os.tmpdir()/skillselion/…`，并告诉 agent「Read or run these … exactly as the SKILL.md directs」；来源**优先取 skillselion 自己的缓存**，GitHub 只是回退；无 pin、无签名、无校验 | 远端可决定本机落盘并被执行的内容 |
| `setup` 子命令：改 `~/.claude/settings.json` 加 SessionStart hook；hook 每次会话拉 400 条目录注入 `additionalContext`（「DEFAULT TO LOADING… call load_skill FIRST」）；注册 MCP 用 `npx -y github:skillselion/skillselion-mcp`（GitHub HEAD，不是 npm 版本，不可 pin）；`--history` 扫 `~/.claude/projects/*/*.jsonl` 与 `~/.codex`（本地关键词计数，不外发） | 常驻提示注入面 + 不可 pin 的供应链 |
| 读本地：`package.json` 依赖与若干文件存在性（本地排名用）；`~/.claude/skills` 与 `installed_plugins.json`（写进 server instructions 给本地 client） | 不外发，但能力面要知道 |
| 小瑕疵：源码常量 `VERSION='0.9.10'`，包版本 0.9.11 | — |

⇒ **公司机器：排除**（与任务书预期一致，依据是组织仓「公司内容不出本地」+ 上述远端控制面）。家里也不建议跑 `setup` 模式。

## 三、抽样 skill（10 条，源码全部读过；三档）

| # | 条目 | 安装量 / 审计标记 | 做什么、依赖什么 | 与本仓重叠 | 档 |
|---|---|---|---|---|---|
| 1 | `vercel-labs/skills#find-skills` | 3.9M / MEDIUM | 纯 SKILL.md 无脚本；驱动 `npx skills` CLI；教 agent 用 `-g -y` 免确认安装；「可信源」名单 Vercel 排第一 | 本仓无发现类 skill；与 `_radar` 人审流程方向相反 | 只当参考（读六步法，不装） |
| 2 | `starchild-ai-agent/official-skills#skillmarketplace` | 7.1k / **CRITICAL** | 依赖 Starchild 平台 `search_skills` 工具，默认 `auto_install=true`；上游已删/改名，站点仍供缓存 | 无 | **不碰** |
| 3 | `agentpowers-ai/agentpowers-skill#agentpowers` | — | 纯 SKILL.md，用 curl 调 `api.agentpowers.ai`，tar 解压直装 `~/.claude/skills`，含付费 checkout；安全规则（硬编码 URL、slug 校验、拒 symlink、临时目录解压）写得认真 | 无 | **不碰**（第三方商业市场直装） |
| 4 | `skillcreatorai/ai-agent-skills#browse-and-evaluate` | — | 驱动 `npx ai-agent-skills` CLI；护栏：`--dry-run`、`--fields`、一次不超 3 个 | 护栏写法可借鉴 | 只当参考 |
| 5 | `neolabhq/context-engineering-kit#agent-evaluation` | 1.2k / LOW | 57 KB 纯文本：评测 skill/agent 的多维 rubric 与 LLM-as-judge | 与 `techniques/adversarial-verification.md` 的 LLM-as-judge 节同源同数字 | 只当参考 |
| 6 | `openai/skills#skill-installer`（官方） | 3.6k / MEDIUM | Python 脚本：GitHub zip 或 sparse checkout 装到 `$CODEX_HOME/skills`；有 zip 路径穿越校验、目标已存在即中止、不执行下载内容 | `scripts/sync-skills.ps1` 是本仓→本机；这是远端→本机，可作 Codex 侧「从审过的仓库装」参考实现 | 只当参考 |
| 7 | `bytedance/deer-flow#find-skills` | 3.8k / HIGH | find-skills 改写 + `install-skill.sh`（`npx skills add -g -y` 静默 + symlink 进项目） | 无 | **不碰** |
| 8 | `mattpocock/skills#grill-me` → `grilling` | 1.4M / LOW | 2 KB 纯文本：把计划画成**设计树**，按「frontier」分轮逼问，每题附推荐答案、答「yes」即接受；事实自己查、决策留给用户；frontier 空才结束 | 与 `supervised-workflow` / `auditing-plan-scope` 同向，形式更锋利 | **值得按 `_radar` 流程引进评估**（作 plan 阶段可选「逼问模式」；零脚本；仓库 MIT，GitHub API 2026-10-20 核） |
| 9 | `juliusbrussee/caveman#caveman` | 582k / — | 极简输出风格，规则严谨：否定词不丢、payload 原样、七种破例场景、发送前四检 | 本仓回复偏长；对 lane 间回信有参考价值 | 值得评估（**个人层偏好**，不进通用仓；仓库 Apache-2.0，同日核） |
| 10 | `forrestchang/andrej-karpathy-skills#karpathy-guidelines` | — / MIT | 2.5 KB 四条：先想后写、最小代码、外科手术式改动、目标驱动可验证 | 与 `constraints` / `function-clarity` / tdd 基本重叠 | 只当参考（无增量） |

**第三方实证佐证**（读自 arXiv 2601.10338 摘要）：31,132 个 skill 中 26.1% 至少一处漏洞，带脚本的 skill 漏洞几率是纯指令的 2.12 倍（OR=2.12, p<0.001）。

**未读源码、仅登记的线索（👁 观察）**：`mattpocock/skills` 的 writing-for-agents / teach / handoff；`affaan-m/ecc#rules-distill`（从 skill 库提炼规则文件）；`rebelytics/one-skill-to-rule-them-all#task-observer`（观察任务沉淀为 skill）；`alchaincyf/darwin-skill`（CRITICAL，自评测 skill）；`anthropics/skills#skill-creator`（官方，审计标 HIGH）。另：`obra/superpowers` 多条在排行榜上，本机已通过插件装有。

## 四、引进政策建议（草案，裁决归用户 / main）

1. **第三方 skill 进本仓**：只走「目录发现 → 源码下载到隔离目录 → 人工读 SKILL.md 与全部脚本 → `_radar` 登记（commit sha、许可证、证据等级）→ 手工复制或改写进 `skills/`」。不接任何自动同步或自动安装（`npx skills add`、skill-installer、find-skills 的 `-g -y`）。优先官方市场，第三方目录只当索引；无许可证的不进仓；进仓的钉 commit sha。
2. **任务中途远程加载 MCP**：公司机器直接排除。Claude Code 管理设置可机械执行（`strictKnownMarketplaces` 白名单 + `disableSideloadFlags` + `allowedMcpServers`，见 code.claude.com/docs/en/plugins/org），建议 main 评估是否在公司机器落 `managed-settings.json`。
3. **家里的个人探索**：建议选 (b)——可装可试，但 (i) 不跑 `skillselion-mcp setup`（它改 `settings.json` 加常驻 hook）；(ii) `DO_NOT_TRACK=1`；(iii) 试完要进本仓的仍走第 1 条。**用户 2026-10-21 在问答裁决：「家里可以开口子」**，即采纳 (b)；配套三点仍建议执行，落到个人叠加仓由 main 定。

## 五、诚实边界与待办

- **无对抗核验、无多票**。实测项（API 转储计数、sha256 比对、GitHub 树检查、源码阅读）可复现；三档判定与政策建议是单人一次判断。
- **抽样不是随机**：10 条按「安装量靠前 + 关键词命中 meta / find / marketplace」挑选，另三条按用户「想看跳出习惯的」要求补入；结论不外推到全目录。
- **同类站点**：第一轮只看了一眼；用户追问后第二轮补做，见第六节。Skills Directory、SkillsMP、Glama、ClaudeLog 本机连不上，cursor.directory 被 429 限流，均未核。
- **本轮不促升**：按 `_radar/README.md`，从这里到 `guidelines/` 或 `skills/` 是用户有意识的一步；「值得引进评估」两条的促成门槛是在一次真实 plan 阶段试用一次并与 `supervised-workflow` / `auditing-plan-scope` 划清分工。
- **已裁决（2026-10-21，问答）**：家里可以开口子；第六节 A 列的 2（caveman）、3（karpathy-guidelines）、4（writing-for-agents）「收录到 guidelines 里试试」。落地归 main，方案见第七节。政策①②由谁落实仍待 main。
- **登记去向**：任务书把需用户决定的事路由到问答，本轮未再重复登记到本机 Vikunja；是否补登由 main 定。
- 原始证据在会话临时目录（`dl-skillselion` 站点页面与 API 转储、`dl-skillselion-mcp\package\index.js`、`dl-skills\*` 含 `PROVENANCE.txt` 的 tree sha、`dl-others` 同类站点页面、`tools\*.py` 只读解析脚本），会话结束后会被清理；按本文的 URL、listing id 与 sha 可重新抓取复核。

## 六、第二轮（用户追问）：「颠覆习惯」候选补抽 + 同类站点与最佳实践站

用户在问答答复问题 2 时说想要「跳出现有 guidelines 和工作习惯、能 mind blow」的东西，并问「还有别的 skill 站或 AI 最佳实践站吗」。本节是对这两问的补做；源码均读 GitHub 原件。

### 6.1 补抽的 skill（含第三节已列的 8、9、10 三条，共 10 条「颠覆」样本）

| 条目 | 大小 / 许可证 | 机制一句话 | 与本仓的关系 | 档 |
|---|---|---|---|---|
| `mattpocock/skills#writing-for-agents` | 10.9 KB + 2.6 KB 附件 / MIT | 给 agent 写文档的工程学：context pointer 的措辞决定可达性；context load 对 cognitive load 两种负载；信息层级三档与分支测试；completion criterion 的「拉力/阻力」；leading word；negation 失效要写正向；no-op 逐句测试（判据：有没有改变默认行为）；环境是事实源、文档重述只是缓存；不剪则沉积 | 与 `context-budget-audit`、`instruction-content`、`knowledge-promotion` 同一问题域，多出一套可操作词汇与判据 | **📥 重点评审** |
| `mattpocock/skills#teach` | 9.7 KB + 4 份格式附件 / MIT | 当前目录当教学工作区：MISSION、learning-records（= 学习版 ADR，用于算最近发展区）、每课一个 HTML、速查参考、不信参数记忆先找资料；区分 fluency 与 storage strength | 超出编码范围；「learning record = ADR」「不信参数记忆」两点可借 | 👁 个人学习用 |
| `mattpocock/skills#handoff` / `#wait-what` | 940 B / 396 B / MIT | handoff：对话压成交接文档存系统临时目录、列建议 skill、不复制已有产物、脱敏。wait-what：一句话「重新讲，用 ASD-STE100，用 GLOSSARY 术语」 | 「极小 skill」范例；本仓 skill 普遍偏长 | 👁 参考形态 |
| `rebelytics/one-skill-to-rule-them-all#task-observer` | 45 KB SKILL.md + 400 KB 参考 + 5 脚本 / CC-BY-4.0 | 每次会话首个工具调用前触发，记摩擦与纠正进 observation log，周评审转 skill 更新 | 思路同 `evidence/incidents` + `record-incident`；实现是 context-budget 原则的反面 | ⛔ 不碰，记思路 |
| `affaan-m/ecc#rules-distill` | 11.8 KB（日文）/ 未核 | 扫描已装 skill，抽「2+ skill、可执行、有违反风险、规则尚无」的原则，LLM 裁决六类处置，人逐条批准 | 「2+ 才算」同构于 two-strike；「确定性收集 + LLM 判断」同构于 `enumerate-then-adjudicate` | 👁 只当参考 |

### 6.2 同类站点与「最佳实践」站（证据等级：读自页面，除注明外）

| 档 | 站点 | 要点 |
|---|---|---|
| 官方 | `anthropics/claude-plugins-official`（43k★，Apache-2.0） | 内部插件 + 外部提交表单，「须达到质量与安全标准」，审核流程未公开；官方市场名受保护；装前仍弹信任警告 |
| 官方 | `anthropics/skills`、code.claude.com 文档、Anthropic 工程博客、`openai/skills` `.curated` | 行为类问题以官方为准 |
| 官方 | MCP 官方注册表 registry.modelcontextprotocol.io | Registry 工作组维护；只验命名空间归属（GitHub OAuth / DNS），不审代码不评质量，只存元数据；v0.1 API 冻结仍 preview |
| 标准 | agentskills.io（Anthropic 发起的开放标准，约 45 客户端采用）；agents.md（Linux Foundation 下 Agentic AI Foundation） | 只有规范与格式说明，无策展目录；agents.md 指向 GitHub 搜索 60k+ 示例 |
| 人工策展 | awesome-claude-code（hesreallyhim，56k★，无官方关联） | 硬门槛「首提交满 14 天且持续开发，或 ≥100★」；只接受人通过 issue 表单推荐、不接 PR；bot 只查格式与许可证；闭源/付费项目只按社区采用度收。最可靠的「别人怎么用」入口 |
| 原则文 | 12-factor-agents（HumanLayer，26.8k★） | 12 条写 agent 程序的原则，非目录 |
| 抓取排行 | skills.sh（Vercel） | About 页：安装计数来自 CLI 匿名遥测、opt-in、每小时去重；每个 skill 经合作方例行审计（公开页 Gen Agent Trust Hub / Socket / Snyk），「全部审计不过的排除」；同时声明不保证质量与安全。口径不一：FAQ「completely anonymous」、About「去重」、Vercel 博客「不代表独立用户」 |
| 抓取排行 | claudemarket.ai | 个人运营，OpenClaw 为主；目录来自公开仓库，兼卖付费 persona / skill 包；无审核说明 |
| 未核 | SkillsMP、Glama、ClaudeLog、cursor.directory、Skills Directory | 本机连不上或 429；只有搜索摘要，不作结论 |

**渠道分层建议**：① 查行为以官方为准；② 找「别人怎么用」优先有硬门槛的人工策展与有署名的原则文；③ 排行榜只用来发现名字，然后回 GitHub 读源码；④ MCP 先在官方注册表验命名空间，再看评级或自己读代码；⑤ 进本仓仍走第四节第 1 条。

## 七、用户裁决（2026-10-21）与促升方案（交 main 落地）

用户在问答回复：「我觉得 2 3 4 还不错，我们收录到 guidelines 里试试吧。家里可以开口子」。编号按第六节 A 列（问答第二轮答复的 A 节）理解：2 = caveman，3 = karpathy-guidelines，4 = writing-for-agents。本 lane 按任务书不改 `guidelines/` `techniques/` `skills/` 正文，以下是落地方案；逐项对照过现有文件，去重结论标在「增量」列。

| # | 条目 / 许可证 | 建议落点与形态 | 增量（对照现有文件后） | 不收的部分 | 验证方式 |
|---|---|---|---|---|---|
| 2 | caveman（`juliusbrussee/caveman`，Apache-2.0，sha 见 `dl-skills` PROVENANCE） | **个人叠加仓**，与 `dialectic-thinking` / `think-back` 同列「我命名的流程」表：新建 skill（如 `terse-mode`），触发词「简洁模式」「caveman」「少废话」，关闭词「正常模式」。用自己的话重写：先答案后理由再下一步；杀寒暄铺垫收尾；否定词绝不省；一句一意；代码路径数字原样；七种破例；发送前四检。source 行写仓库、许可证、sha | 通用仓 `guidelines/writing/prose-and-register.md` 明确把「对话回复」排除在外（走 per-project 偏好），所以通用仓没有现成落点；它本质是用户偏好，与个人仓「回复一律用中文」兼容（caveman 第 8 条：压缩风格不换语言） | 「ultracave / megacave」别名与 hook 状态汇报（绑它自己的插件机制）。若用户坚持进通用仓：`skills/workflow/`，但 `sync-skills.ps1` 只允许 `name` / `description` frontmatter，得靠 description 触发词 | 试用一到两周，专盯它自己列的失败模式：丢否定词、丢步骤顺序、把问句压成歧义句 |
| 3 | karpathy-guidelines（`forrestchang/andrej-karpathy-skills`，MIT） | **不新建文件**。规则 3「外科手术」= `guidelines/code/constraints.md` Edit Scope Discipline 逐条已有（相邻代码不动、匹配现有风格、只清自己造成的孤儿、死代码只提不删、每行可追溯）；规则 2「最小代码」= 同文件 Simplicity；规则 1「先想」= `guidelines/code/clarify-before-implementing.md`（说出假设、列并行解释、能更简单就推回）；规则 4「目标驱动」= `validation.md` 与 tdd skills | 只有两小句：(a) 自检句「写了 200 行而 50 行能解决就重写」→ 加进 `constraints.md` Simplicity；(b) 多步任务的轻量计划格式「`步骤 → verify: 检查`，一行一验」→ 加进 `validation.md` 或 `autonomous-workflow`（main 先核那两处是否已有等价句） | 其余三条半：已覆盖，再写就是重复（`knowledge-promotion.md` 排除项）。它让人 mind blow 的是「2.5 KB 讲完」这件事，那是**表达压缩**，不是新规则；如需一页短版给别的 agent 贴，是从现有四份**派生**，不是促升 | 加完两句后跑一遍 `context-budget-audit` 第二轴（约束必要性），确认没把常识写成硬规则 |
| 4 | writing-for-agents（`mattpocock/skills`，MIT） | **新建** `guidelines/workflow/writing-for-agents.md`（`class: knowledge`，`scope: universal`，带来源），注册到 `guidelines/INDEX.md` 第一行「维护指令库…」；`instruction-content.md`「新增与维护」节加一句指针；`skills/workflow/context-budget-audit/SKILL.md` Step 2 / 第二轴加「no-op 逐句测试」「指针措辞」判据指针；`skills/INDEX.md` 维护段加一句（description 就是 context pointer）。内容用自己的话重写，保留它的术语作 leading word：context pointer 的两项工作与三条写法；两种负载；信息层级三档 + 分支测试 + 共置 + 蔓延；completion criterion 的清晰度与要求度、拉力/阻力、先磨判据后藏步骤（只有跨真实上下文边界才有效）；leading word 与自造词成本；negation 失效 → 写正向、禁令只作硬护栏且配正向；剪枝四条（单一事实源 / 环境是事实源、文档只是缓存 / 相关性 / no-op 逐句测试，判据模型相对，靠跑不靠辩）；沉积 | 与本仓的关系：`context-budget-audit` 第二轴「约束必要性」≈ no-op 测试，但它给了更可操作的判据（「有没有改变默认行为、有争议就跑一遍」）；`adversarial-verification.md` 的「否定式约束盲区」是审查侧，这里是写作侧的同一现象；`documentation.md` 拆分规则按**长度**（3 主题 / 200–300 行），它按**分支与序列**拆，互补；`skills/INDEX.md`「附件按需读取」= 信息层级第三档 | SKILL-MECHANICS 里的 `disable-model-invocation` / router skill 两节：本仓 skill frontmatter 只允许 `name` / `description`，且双宿主共用，机制不对口，只记一句「用户调用 vs 模型调用」的取舍 | 下一次改 skill 或 `AGENTS.md` 时拿它的判据过一遍（description 的 pointer 写法、逐句 no-op），记一条 `evidence` 作首次命中 |

证据等级：三条的内容本身都是「它主张」；本仓 2026-10-13 审计有同向实测（description 常驻成本、附件按需读取）。按 `knowledge-promotion.md`，这属于「有来源的参考综合」，不需要两击，但要写成带来源的知识页，不写成硬规范；两击前不升为 norm。

**执行归属**：按任务书与本 lane 角色说明，正文由 `agent_coding_guidelines/main` 落地；caveman 一项落个人叠加仓，也由 main 协调。本 lane 工作区观察到 `techniques/lane-router.md` 有不属于本 lane 的在途改动，同仓并发编辑按文件分执笔。
