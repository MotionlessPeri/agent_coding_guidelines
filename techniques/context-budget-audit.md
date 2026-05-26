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

## Anti-Patterns

| 反 pattern | 为什么错 |
|---|---|
| "再加一份 guideline 没什么吧"——0.5K token / file × 50 file = 25K | always-loaded cost 是 cumulative；每加一份都在拉高 baseline |
| 内容重复："X 在 A 讲过，但 B 再讲一遍方便读者" | 读者会读 INDEX，agent 多一份重复 = 多 token / 不增信息 |
| Domain-specific 集群 always-import | 跨项目用全局 config 时整段浪费 |
| Audit 完不真做 trim | report 不写 action item 等于没 audit |
| Skill description 写整段说明 | description 是 trigger 用的，不是文档；保留 2-3 句关键判据 + 把详情留 SKILL.md body |

## 项目实例参考

`agent_coding_guidelines` repo 当前状态（2026-05-26 快照）：

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

总 `@`-import: ~35。其中 UE + P4 + Windows CI + 部分 techniques = ~16 个 conditional——非 UE 项目里都是浪费。

**潜在优化方向**（不立刻执行，作为本 audit 的产出示例）：

- **UE 12 份**：用 [`guidelines/ue/INDEX.md`](../guidelines/ue/INDEX.md) 替代 always-import；INDEX 提供 navigation，具体 file 走 skill description trigger 或 project-conditional load
- **P4 + CI Windows**：同样按项目 surface
- **techniques 里 conditional 的**（`ue-custom-graph-editor.md` / `ci-deploy-to-p4.md`）：promote 到 skill 或 project-conditional

估算 always-loaded token 节省：~40–60%。Cost 本身不大但 cache 命中率 + 启动延迟会改善。

⚠️ **本 technique 自身也是一份 always-loaded** —— 如果跟着前面 audit 思路严格走，应该考虑把本 file 也 lazy-load（只 audit 时才需要）。一种折中：留 navigation stub 在 AGENTS.md，本 file body 走 skill 触发式 load。本 commit 暂时按惯例 always-import，等下一轮 audit 跟其他 conditional 一起评估。

## 相关 Guidelines / Techniques

- [`guidelines/workflow/knowledge-promotion.md`](../guidelines/workflow/knowledge-promotion.md) —— 对称的"project → meta-corpus"方向；本 audit 防止 meta-corpus 端无节制膨胀
- [`AGENTS.md`](../AGENTS.md) —— `@`-import 列表是本 audit 的主 input
- ECC `context-budget` skill（[github](https://github.com/affaan-m/ECC/tree/master/skills/context-budget)）—— 本 technique 的灵感来源；ECC 还覆盖 MCP server schema 占用 / Agent description 占用，本 technique 暂没纳入（agent 形态在本 repo 还不重）
