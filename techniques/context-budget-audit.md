# Context Budget Audit

## 核心问题

跨多 project 共享同一份全局 `AGENTS.md` + 大量 `@`-import + skill 自动 lazy-load 时，**always-loaded context** 会沉默膨胀。每加一条 guideline / 一份 technique 单独看都不大，累积下来：

- agent 主对话 prompt 头部塞满 guideline，吃 input token
- guideline 之间内容重叠（如"小函数原则"在 [`constraints.md`](../guidelines/code/constraints.md) / [`function-clarity.md`](../guidelines/code/function-clarity.md) 都讲），重复 cost 无收益
- 跟当前项目无关的 guideline 也加载（React 项目里整套 UE guideline 占 12 份 @-import 全 eager load）
- 每次 session 启动 cost 上升 + prompt cache 命中率下降

本 technique 提供**定期 audit always-loaded 上下文占用** 的程序化做法。

跟 [`guidelines/workflow/knowledge-promotion.md`](../guidelines/workflow/knowledge-promotion.md) 对称——那条管"什么时候把 project lesson 升级到 meta-corpus"（push 方向），本条管"meta-corpus 里 always-loaded 的部分该多大"（防止 push 方向无节制累积）。

## 何时跑 audit

- AGENTS.md `@`-import 数量超过 ~25（启动 cost 已经显著）
- 一波新增 5+ 个 guideline / technique 之后
- 加新 `@`-import **之前**——审视现有的，看能不能去掉等量旧 import 再加
- 启动 session 频繁 cache miss
- 跨多 project 共用全局 config，但每个项目只用其中一小部分

## Audit 四步骤

### Step 1: Inventory

清点 always-loaded 的所有来源：

| 来源 | 怎么查 | Token 估算 |
|---|---|---|
| `AGENTS.md` 自身 | `wc -l AGENTS.md` | line × 0.75 token/line（中文为主） |
| `@`-imported guideline | grep `^@` AGENTS.md，对每个 path 累加行数 | 同上 |
| skill SKILL.md 的 description 字段（matching 时进 context） | `find skills -name SKILL.md` + 取 frontmatter description | 字数 × 1.2 token/字 |
| SessionStart hook 注入的 additionalContext | 看 `~/.claude/settings.json` hook 配置 + handler 输出 | 注意各 harness 是否有 max-chars cap |
| Claude Code 自带 system prompt + auto memory | `~/.claude/<proj>/memory/MEMORY.md` + 个别 memory 文件 | 行数 × 0.75 |

中文 token 估算粗规则：~0.5–0.75 token / char（汉字普遍 1 token / 字，markdown 标点 + 英文 keyword 会拉低均值）。

### Step 2: Classify

每个 always-loaded 单元打分：

| 桶 | 判据 |
|---|---|
| **Always needed** | 跨所有 project 都适用，且不冗余（如 [`commits.md`](../guidelines/workflow/commits.md) / [`agent-lifecycle.md`](../guidelines/workflow/agent-lifecycle.md)） |
| **Project-conditional** | 只对某类项目有用（UE / P4 / Windows CI 等），其他项目浪费 |
| **Skill-lazy candidate** | 平时不用，遇到具体场景才用（如 [`ci-deploy-to-p4.md`](ci-deploy-to-p4.md)——部署时才 surface） |
| **Overlap candidate** | 内容跟另一份 guideline 显著重叠，可合并或用 `[[link]]` 替代 |
| **Stale** | 写完没用过 / 用过一次就过时 |

### Step 3: Detect

具体 anti-pattern 信号：

#### 信号 1: Always-imported 但只对某类项目有用

典型例子：全局 AGENTS.md `@`-import 整套 UE guideline，但当前 session 是 React 项目。

**修法**：把 domain-specific 集群（UE / P4 / Windows CI / 等）从 always-import 改为 **conditional / lazy**：

- 用 INDEX.md 做 navigation hub，**不 eager load 整个集群**——agent 看 hub 决定是否进具体 file
- 项目侧 AGENTS.md 自己 `@`-import 它需要的子集
- 或者 promote 到 skill，让 Claude Code 按 trigger description 按需 load
- 或用 **path-scoped `.claude/rules/`**（碰到该类文件才自动加载）——见下「加载时机三档模型」，注意那里两个 caveat（Claude-Code 专属 + `paths` 是文件 glob 非项目类型）

#### 信号 2: 内容显著重叠

`grep -i "<concept>" guidelines/` 找同一个 concept 在几个 file 重复讲——多数情况可以合并 / 用 `[[name]]` 链接替代。

#### 信号 3: Skill description > ~30 词 / ~200 字

skill SKILL.md frontmatter 的 `description` 每次 Claude Code matching 都进 context。冗长描述无收益，每个 skill 都浪一点点最后总量很可观。

#### 信号 4: AGENTS.md "Read This First" 列表 + body 重复

AGENTS.md 自己介绍每个 imported guideline + 然后 `@`-import 把 guideline 整段拉进来 = duplicate effort。AGENTS.md body 应该是 navigation，不重复 guideline 内容。

### Step 4: Report + Actions

固定 4 种 action：

1. **Remove**——彻底删（stale / 几乎没用）
2. **Lazy-load**——从 `@`-import 改成 skill 触发式 / INDEX hub 形态
3. **Merge**——内容跟别的合并，用 `[[link]]` 替代
4. **Trim**——只保留前部"决策表 / 核心规则"，details 移到 separate ref，主文件 always-load，ref 文件按需 load

按 `token saving × confidence` 排 top-N，落实施 commit。

## 加载时机三档模型（决定每条内容该放哪档）

context 膨胀的根因是「该按需加载的内容被 always-load 了」。Claude Code 的 steering 机制按**加载时机**分三档，给「这条内容放哪档」一张决策依据：

| 档 | 机制 | 何时进 context | 适合放 |
|---|---|---|---|
| **永远在** | 根 `CLAUDE.md` / `@`-import / 不带 `paths` 的 `.claude/rules/` | session 一开就在，压缩后重注入 | 真·跨所有 project 通用（commits / agent-lifecycle / validation） |
| **碰文件自动进** | **path-scoped `.claude/rules/`**（frontmatter `paths: ["**/*.uasset"]`）/ 子目录 `CLAUDE.md` | 摸到匹配文件时自动加载，docs-only session 不进 | 跟某类文件强相关、但非全项目需要的规则 |
| **被调才进** | **Skills**（`/手动` 或 description 自动匹配）/ subagent | 调用时才加载正文，平时只 name + description | 按场景 / 流程触发的程序化内容（本 repo 大量 UE / Maya 内容已走此档） |

**path-scoped rule 是「永远在」和「被调才进」之间缺的中间档**——补上「我没主动调、但碰到这类文件就该自动生效」的场景。

⚠️ 两个 caveat（决定它**不是** always-import 的银弹）：

- **Claude-Code 专属**：`.claude/rules/` 只有 Claude Code 认；本 repo 的 `@`-import 走 `AGENTS.md` 是为了 **Codex 也能读**（见 `collaboration/multi-agent.md` single-source 政策）。全面改 rules/ = 放弃跨工具单源。只用 Claude 的项目无此顾虑。
- **`paths` 是文件 glob，不是「项目类型」**：触发依据是「这次 session 摸了哪些文件」，不等于「这是不是 UE 项目」。本 repo 是**全局加载**（`~/.claude/CLAUDE.md`），「UE 集群在非 UE 项目浪费」这个痛点，file-glob 只能**部分**对上（UE 项目开头还没碰 `.uasset` 时也不加载）。

所以三档是**工具箱**，不是「把 always-import 全改 rules/」。Step 3 信号 1 的「conditional / lazy」修法，落地时按本表选档：domain 集群走 path-scoped rule（碰文件自动进）还是 skill（被调才进），取决于它是「碰某类文件触发」还是「按场景触发」。

> 一手 framing：把「决定每个推理周期 context 里放什么」当成独立于 prompt engineering 的学科，见 Anthropic [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)——其 just-in-time 检索 + agentic 笔记落盘，正是本 technique 与 `coordination-patterns.md` iterative-retrieval 在做的事。

## Anti-Patterns

| 反 pattern | 为什么错 |
|---|---|
| "再加一份 guideline 没什么吧"——0.5K token / file × 50 file = 25K | always-loaded cost 是 cumulative；每加一份都在拉高 baseline |
| 内容重复："X 在 A 讲过，但 B 再讲一遍方便读者" | 读者会读 INDEX，agent 多一份重复 = 多 token / 不增信息 |
| Domain-specific 集群 always-import | 跨项目用全局 config 时整段浪费 |
| Audit 完不真做 trim | report 不写 action item 等于没 audit |
| Skill description 写整段说明 | description 是 trigger 用的，不是文档；保留 2-3 句关键判据 + 把详情留 SKILL.md body |

## 项目实例参考

`agent_coding_guidelines` repo 当前状态（下表 2026-05-26 快照**已漂**——现值请 live-query `grep -c '^@' AGENTS.md`，别信下表定值）：

| 类别 | `@`-import 数 | 备注 |
|---|---|---|
| workflow | 7 | 跨项目 always needed |
| code | 5 | 跨项目 always needed |
| collaboration | 2 | always needed |
| ci-windows | 1 | conditional（只 Windows CI 项目用） |
| claude-code | 1 | always needed（hook 写作约定） |
| p4 | 1 | conditional（只 P4 项目用） |
| ue | 12 | conditional（**非 UE 项目可整段 skip**，AGENTS.md 自己写明） |
| techniques | 6 | 混合：adversarial / coordination / worker = always；ue-custom-graph / ci-deploy-to-p4 = conditional |

总 `@`-import: ~35（**2026-07-18 audit 实测已到 70，常驻 ~8886 行**——用 `grep -c '^@' AGENTS.md` + `find guidelines techniques -name '*.md' | xargs wc -l` 现查）。其中 UE + Maya + P4 + Windows CI + C++ + Claude-Code + 部分 techniques ≈ 70% 是 conditional——非匹配项目里都是浪费。

**潜在优化方向**（不立刻执行，作为本 audit 的产出示例）：

- **UE 12 份**：用 [`guidelines/ue/INDEX.md`](../guidelines/ue/INDEX.md) 替代 always-import；INDEX 提供 navigation，具体 file 走 skill description trigger 或 project-conditional load
- **P4 + CI Windows**：同样按项目 surface
- **techniques 里 conditional 的**（`ue-custom-graph-editor.md` / `ci-deploy-to-p4.md`）：promote 到 skill 或 project-conditional

估算 always-loaded token 节省：~40–60%。Cost 本身不大但 cache 命中率 + 启动延迟会改善。

⚠️ **本 technique 自身也是一份 always-loaded** —— 如果跟着前面 audit 思路严格走，应该考虑把本 file 也 lazy-load（只 audit 时才需要）。一种折中：留 navigation stub 在 AGENTS.md，本 file body 走 skill 触发式 load。本 commit 暂时按惯例 always-import，等下一轮 audit 跟其他 conditional 一起评估。

## 外部数值锚（参考，落地前须实测——别照搬）

radar 2026-07-18 从外部 best-practice 文章收的几个具体阈值，可作本 audit 的参考锚，但**数字互相矛盾、blog-only，用前先实测自己的 repo**：

- **always-loaded 索引文件（AGENTS.md / CLAUDE.md）有"甜区"**：一说 ~200 行内每轮全读、过 ~500 行开始 skim 信号密度崩；另一说 ~40 / ~400——**两个数字打架**。本 repo 的 AGENTS.md 本身 ~235 行、走 `@`-import 展开（真正常驻的是被 import 的 ~8900 行，不是 AGENTS.md 自己）。判据不是抄行数，是**实测**你的索引多长时 harness 开始 skim（可推探针验）。
- **skill 库 sprawl 上限 ~20 + 周期性退休**：外部经验是攒到 40-50 个但 top 5 占 ~90% 调用、长尾为零 → 硬上限 ~20 + 定期删低调用的。本 repo 当前 15 个 skill，在线内。**只取"设个上限 + 到点复查退休"的纪律**——团队维度的量化指标（人均调用率 / owner 字段 / PR 强制）不纳入（属组织政策，见 `knowledge-promotion.md` 排除项）。

来源：radar `_radar/2026-07-18.md` 候选 #4（digitalapplied / ai.rundatarun，未经对抗核验）。

## 相关 Guidelines / Techniques

- [`guidelines/workflow/knowledge-promotion.md`](../guidelines/workflow/knowledge-promotion.md) —— 对称的"project → meta-corpus"方向；本 audit 防止 meta-corpus 端无节制膨胀
- [`AGENTS.md`](../AGENTS.md) —— `@`-import 列表是本 audit 的主 input
- ECC `context-budget` skill（[github](https://github.com/affaan-m/ECC/tree/master/skills/context-budget)）—— 本 technique 的灵感来源；ECC 还覆盖 MCP server schema 占用 / Agent description 占用，本 technique 暂没纳入（agent 形态在本 repo 还不重）
