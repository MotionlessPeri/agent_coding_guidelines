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
3. **家里的个人探索**：建议选 (b)——可装可试，但 (i) 不跑 `skillselion-mcp setup`（它改 `settings.json` 加常驻 hook）；(ii) `DO_NOT_TRACK=1`；(iii) 试完要进本仓的仍走第 1 条。**等用户在问答裁决**（用户 2026-10-20 回复「没看懂」，已追加解释，尚未定）。

## 五、诚实边界与待办

- **无对抗核验、无多票**。实测项（API 转储计数、sha256 比对、GitHub 树检查、源码阅读）可复现；三档判定与政策建议是单人一次判断。
- **抽样不是随机**：10 条按「安装量靠前 + 关键词命中 meta / find / marketplace」挑选，另三条按用户「想看跳出习惯的」要求补入；结论不外推到全目录。
- **同类站点只看了一眼**：Skills Directory 本次站点连不上，其「120 模式自动扫描」只是它声称；skills.sh 的安装计数去重方式 Vercel 未公开。
- **本轮不促升**：按 `_radar/README.md`，从这里到 `guidelines/` 或 `skills/` 是用户有意识的一步；「值得引进评估」两条的促成门槛是在一次真实 plan 阶段试用一次并与 `supervised-workflow` / `auditing-plan-scope` 划清分工。
- **等用户裁决**：家里要不要开口子（问答议题问题 1）；三条政策建议是否采纳及由谁落实。
- **登记去向**：任务书把需用户决定的事路由到问答，本轮未再重复登记到本机 Vikunja；是否补登由 main 定。
- 原始证据在会话临时目录（`dl-skillselion` 站点页面与 API 转储、`dl-skillselion-mcp\package\index.js`、`dl-skills\*` 含 `PROVENANCE.txt` 的 tree sha、`tools\*.py` 只读解析脚本），会话结束后会被清理；按本文的 URL、listing id 与 sha 可重新抓取复核。
