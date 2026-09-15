---
name: context-budget-audit
description: Use when auditing the context cost or necessity of agent instructions, skill descriptions, or loading rules. Skip ordinary application work.
---

# Context Budget Audit

## 核心问题

跨多 project 共享同一份全局 `AGENTS.md` + 大量 `@`-import + skill 自动 lazy-load 时，**always-loaded context** 会沉默膨胀。每加一条 guideline / 一份 technique 单独看都不大，累积下来：

- agent 主对话 prompt 头部塞满 guideline，吃 input token
- guideline 之间内容重叠（如"小函数原则"在 `guidelines/code/constraints.md` / `guidelines/code/function-clarity.md` 都讲），重复 cost 无收益
- 跟当前项目无关的 guideline 也加载（React 项目里整套 UE guideline 占 12 份 @-import 全 eager load）
- 每次 session 启动 cost 上升 + prompt cache 命中率下降

本 technique 提供**定期 audit always-loaded 上下文占用** 的程序化做法。

跟 `guidelines/workflow/knowledge-promotion.md` 对称——那条管"什么时候把 project lesson 升级到 meta-corpus"（push 方向），本条管"meta-corpus 里 always-loaded 的部分该多大"（防止 push 方向无节制累积）。

**两条正交的判据轴。** 本 technique 原本只量**加载成本**——token / cache / 常驻体量，问"这条该不该常驻"。还有一条正交的轴:**约束必要性**——问"即便免费常驻、又永远相关，当代模型还需不需要它当护栏"。加载成本轴贯穿下面四步；约束必要性轴单列一节(见「第二判据轴：约束必要性」)，在 Step 2 判断每条内容时一并过。

## 何时跑 audit

- AGENTS.md `@`-import 数量超过 ~25（启动 cost 已经显著）
- 一波新增 5+ 个 guideline / technique 之后
- 加新 `@`-import **之前**——审视现有的，看能不能去掉等量旧 import 再加
- 启动 session 频繁 cache miss
- 跨多 project 共用全局 config，但每个项目只用其中一小部分

## Audit 四步骤

### Step 1: Inventory

清点 always-loaded 的所有来源：

| 来源 | 怎么查 | 报告什么 |
|---|---|---|
| `AGENTS.md` 自身 | 读取源文件 | 字符数、行数及计数口径 |
| `@`-imported guideline | 查 `AGENTS.md` 中的 `^@` 路径，并核对宿主是否展开 | 实际加载的文件及字符数；未展开的引用单列 |
| skill 的 `description` | 用 `rg --files skills -g SKILL.md` 枚举，再取 frontmatter | 各描述及合计字符数 |
| hook 注入的 additionalContext | 按当前宿主配置检查 handler 输出 | 可观察的实际注入量及截断情况；无法观察时标未测 |
| 宿主系统提示与 memory | 按当前宿主暴露的记录核对 | 仅报告可见内容的测量值，不据此推算不可见总量 |

字符数、行数都不等于 token 数。只有使用明确对应的 tokenizer 或宿主提供的用量数据时才报告 token，并注明来源与覆盖范围；否则写「token 未测」。不要用每行或每字的固定倍数代替实测，也不要把文本缩短量当作延迟或效果提升。

### Step 2: Classify

每个 always-loaded 单元打分：

| 桶 | 判据 |
|---|---|
| **Always needed** | 跨所有 project 都适用，且不冗余（如 `guidelines/workflow/commits.md` / `guidelines/workflow/agent-lifecycle.md`） |
| **Project-conditional** | 只对某类项目有用（UE / P4 / Windows CI 等），其他项目浪费 |
| **Skill-lazy candidate** | 平时不用，遇到具体场景才用（如 `techniques/ci-deploy-to-p4.md`——部署时才 surface） |
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

固定 5 种 action(前 4 种针对加载成本轴，第 5 种针对约束必要性轴)：

1. **Remove**——彻底删（stale / 几乎没用）
2. **Lazy-load**——从 `@`-import 改成 skill 触发式 / INDEX hub 形态
3. **Merge**——内容跟别的合并，用 `[[link]]` 替代
4. **Trim**——只保留前部"决策表 / 核心规则"，details 移到 separate ref，主文件 always-load，ref 文件按需 load

5. **Relax**(轴 2)——不删内容，把"写死的规则"改成"交给判断力"的表述；判据见下「第二判据轴」。跟 Remove 区分：Remove 因为"没用 / 没人碰"，Relax 因为"模型不需要被这样管"

按 `token saving × confidence`(轴 1) / `over-constraint × confidence`(轴 2)排 top-N，落实施 commit。

## 第二判据轴：约束必要性(跟加载成本正交)

四步法量的是**加载成本**——"这条该不该常驻"。约束必要性是**正交**的另一问：**即便这条免费常驻、又永远相关，当前任务的目标模型还需要它当护栏，还是本可交给判断力?** 一条规则可以加载不要钱、又永远相关，却仍是**过度规约**——把模型本会做对的事写死，反而压制它按上下文判断。

一句话判据：**这条规则编码的是模型推不出来的事实，还是模型本就会做的品味?**

| KEEP(必要护栏，别碰) | RELAX / 删(过度规约候选) |
|---|---|
| framework hidden contract(UE `PostEditChangeProperty` 同步 / LogicDriver 撕 wire / BuildPlugin 剥字段)——模型无法从代码推出 | 品味 / 风格类规则，能干活的模型本就会做("函数别太长""注释写清楚") |
| 硬 API 契约 / 版本 gotcha(签名、`FVector4` 的 W 分量、5.8 redist 版本) | 形如 "never do trivial-X" 的机械禁令，把常识写成规则 |
| 破坏性操作护栏(见 `guidelines/workflow/agent-lifecycle.md` 确认清单) | 靠罗列举例来约束行为(博文 Rule 2：好接口 / 参数设计 > 举例) |
| 项目专属决策 / 不可从环境推导的事实 | 同一条常识在多份 guideline 重申(既是 overlap 又是 over-constraint) |

对应的落地动作是 Step 4 的第 5 种 **Relax**(博文 Rule 1：用 "match surrounding code" 取代 "never write multi-paragraph docstrings")。

**目标模型与宿主分别判断。** 目标模型以当前项目或任务的声明为准，本文不固定“当前使用”的型号。放宽约束的力度由用户策略及目标模型上的实际任务结果决定；一篇面向某型号的建议不能直接证明其他型号也适用。

- **宿主机制**：Claude Code 可展开 `@`-import；Codex 不展开，需要按适用目录读取文件。这决定资料如何定位和加载，不能据此推导模型判断力强弱。
- **必要约束**：保留用户明确选择的审批方式、领域隐藏契约和其他真实约束。冗余表述可以精简，但不能把文字去重等同于撤销要求。
- **验证**：用目标模型处理相同的代表性任务，分别记录选用资料、是否完成要求及何时停下。双方审查意见一致不是双模型行为实测。

每新增一条 guideline 时，也检查其约束必要性，避免把模型可按上下文判断的常识写成硬规则。

> 一手 framing：Anthropic [The new rules of context engineering for Claude 5-generation models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models) —— "unhobbling"：删掉 Claude Code 系统提示 80% 而"无可测量损失"；judgment-over-rules / interface-over-examples / lean-descriptions。**blog-only、且明确不覆盖旧模型 / 混合 fleet；本轴尚未在真实 audit 里跑过一轮**——按 `_radar/README.md` 政策落地前实测，别照搬。

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
| 把常识写成规则 / 靠举例约束行为 | 对当代模型是过度规约、压制判断力(约束必要性轴，见「第二判据轴」)；跟"加载成本"无关，免费常驻也该 Relax |

## 项目实例参考

`agent_coding_guidelines` repo 自身走过一轮完整 audit（2026-07-18 起识别、2026-07-19 Tier D 执行），是本 technique 四步法的真实产出：

**识别（Inventory + Classify + Detect）**：AGENTS.md 曾常驻 **70 个 `@`-import / ~8886 行**，~70% 是条件域（UE / Maya / cpp / P4 / Windows CI / Claude-Code / 部分 techniques）——只对特定项目类型相关却每个 session 常驻。最大浪费是「机制已建未启用」：Maya / UE 的 INDEX hub 早建好、却仍全 `@`-import，等于零收益 overhead。

**执行（Report + Actions，按簇 lazy 化）**：

- **Maya**（8 份）→ 停 `@`-import，用 `guidelines/maya/INDEX.md` 导航
- **cpp**（8 份）→ 新建 `guidelines/cpp/INDEX.md` 导航
- **UE**：ultra-niche 簇 bundle 成懒加载 skill（procedural-numerical / ml-animation / custom-graph-editor），broad 14 份**当轮保留常驻**（→ 2026-07-28 收尾复审后也转懒加载，见下），`guidelines/ue/INDEX.md` 做 broad + skill 双层导航
- **P4 / CI-Windows / Claude-Code**（含配套 techniques ci-deploy-to-p4 / claude-code-autonomous-permissions）→ 停 `@`-import，AGENTS.md 段末懒加载说明
- 顺带把散在条件域文件里跟通用条重复的机制**去冗余**（保留 canonical、另一处缩指针）

**结果**：`@`-import **70 → 38**（现值 live-query `grep -c '^@' AGENTS.md`，别信定值）。条件域内容全部转 skill trigger / INDEX 导航，非匹配项目 session 不再常驻它们；broad-UE + 通用 guidelines 当轮保留常驻。这轮坐实了本 technique 的判断：机制已建未启用是最大浪费，且拆分时要「保留 canonical、去重不丢信息」。

**2026-07-28 收尾（broad-UE → lazy）**：07-19 当轮 broad-UE 14 份保留常驻，判据只到「加载成本」轴。用本次新增的「约束必要性」第二轴 + Claude 5-gen 博文的渐进披露原则复审——这 14 份 ~2500 行在**每个** session 常驻（约占当时 eager footprint 一半），连非 UE 项目也吃，而 `guidelines/ue/INDEX.md` 早已双层覆盖 broad + skill → 停 `@`-import 转 INDEX 懒加载，重度 UE 项目在项目侧 `AGENTS.md` `@`-import 需要的子集拉回（multi-agent Option 2）。`@`-import 进一步降到 **25**（现值 live-query `grep -c '^@' AGENTS.md`，别信定值）。教训：07-19 漏动它不是因为它不浪费，是因为当时判据只看「加载成本 + 常相关」，没问「非 UE session 相不相关」——正是第二轴要补的盲区。

**本 skill 已按需加载**：`AGENTS.md` 保留发现入口，审计任务命中后再读取正文；无需把本文件加入常驻 `@`-import。

## 外部数值锚（参考，落地前须实测——别照搬）

radar 2026-07-18 从外部 best-practice 文章收的几个具体阈值，可作本 audit 的参考锚，但**数字互相矛盾、blog-only，用前先实测自己的 repo**：

- **always-loaded 索引文件（AGENTS.md / CLAUDE.md）有"甜区"**：一说 ~200 行内每轮全读、过 ~500 行开始 skim 信号密度崩；另一说 ~40 / ~400——**两个数字打架**。历史记录中的本仓体量不代表当前加载量；当前文件及宿主展开情况按 Inventory 重新清点。判据不是抄行数，是**实测**你的索引多长时 harness 开始 skim（可推探针验）。
- **skill 库 sprawl 上限 ~20 + 周期性退休**：外部经验是攒到 40-50 个但 top 5 占 ~90% 调用、长尾为零 → 硬上限 ~20 + 定期删低调用的。当前 skill 清单用 `rg --files skills -g SKILL.md` 现场枚举，不沿用历史数量。**只取"设个上限 + 到点复查退休"的纪律**——团队维度的量化指标（人均调用率 / owner 字段 / PR 强制）不纳入（属组织政策，见 `knowledge-promotion.md` 排除项）。

来源：radar `_radar/2026-07-18.md` 候选 #4（digitalapplied / ai.rundatarun，未经对抗核验）。

## 相关 Guidelines / Techniques

- `guidelines/workflow/knowledge-promotion.md` —— 对称的"project → meta-corpus"方向；本 audit 防止 meta-corpus 端无节制膨胀
- `AGENTS.md` —— `@`-import 列表是本 audit 的主 input
- ECC `context-budget` skill（[github](https://github.com/affaan-m/ECC/tree/master/skills/context-budget)）—— 本 technique 的灵感来源；ECC 还覆盖 MCP server schema 占用 / Agent description 占用，本 technique 暂没纳入（agent 形态在本 repo 还不重）
