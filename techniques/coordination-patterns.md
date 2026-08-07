# Coordination Patterns

## Four-Phase Workflow

| Phase | Who | Purpose |
|-------|-----|---------|
| Research | Workers (parallel) | Investigate codebase, understand the problem |
| Synthesize | **Coordinator** | Read worker findings, understand the problem, formulate a plan |
| Implement | Workers | Execute the plan |
| Verify | Workers | Prove the changes work |

## Core Principle: Never Delegate Understanding

The coordinator's most important job is **synthesis**. After workers report research findings, the coordinator must understand them before directing implementation.

**Anti-patterns:**
- "Based on your findings, fix the bug" — delegates understanding to the worker
- "The researcher found an issue in the auth module, please fix it" — no synthesis

**Correct pattern:**
- "Fix the null pointer at `src/auth/validate.ts:42`. The session's `user` field is undefined when the session expires, but the token remains cached. Add a null check before accessing `user.id`; if null, return 401 with 'Session expired'."

**Rule: If your instruction contains "based on your findings" or "based on the research" — rewrite it. You have not synthesized.**

## 成本 & 何时值得用 multi-agent

multi-agent 不是默认更好——它**贵**：Anthropic 实测，单 agent 约耗普通 chat 的 **4×** token，multi-agent 系统约 **15×**；且 **token 用量单独解释了任务质量约 80% 的方差**（模型选择、工具调用次数是次要因素）。所以动手前先判断**值不值**：

| 值得上 multi-agent | 不值得（退回单 agent / 顺序执行） |
|---|---|
| 任务可重并行（独立子任务多） | 各 agent 必须共享同一 context |
| 信息量超单 context 窗 | agent 之间依赖多、需频繁往返 |
| 要接很多复杂工具 | 任务线性、上下文小 |

**项目实例**：本 repo 的 `/research-radar` 跑 deep-research workflow（5 路搜索 + 3 票对抗核验 fan-out），一轮烧 **~8M subagent token / 106 agents**，直接撞爆账号月额度、核验阶段全废。教训：重 fan-out + 多票核验对「常规巡检」过重——全套 multi-agent 留给真正高价值、可并行、超单 context 的任务；轻量场景用「只搜 + 抓、跳过多票核验」的省钱变体。

> 来源：Anthropic [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)。

## Concurrency Rules

### Read-Write Separation
- Read-only tasks (research, search, analysis): freely parallel, no restrictions
- Write operations (implementation, editing): serialize within the same file region
- Verification: can run parallel to implementation on different file regions

### When to Parallelize
- Independent research across different modules — always parallel
- Multiple file edits in unrelated areas — can parallel
- Sequential dependencies (research → synthesize → implement → verify) — must be serial at phase boundaries

## Dependency Patterns

### Serial Chain
Research → Implement → Verify. Each step depends on the previous.

### Fan-Out (parallel research)
Multiple research workers investigate different modules simultaneously. Coordinator synthesizes all findings before proceeding.

### Fan-In (parallel implementation + unified verification)
Multiple implementation workers edit different modules. A single verification pass covers all changes after all workers complete.

### 结果选优与路由模式（Anthropic 官方命名）

上面三种管「怎么分活」，下面三种管「怎么选结果 / 路由」（出处：[claude.com blog "dynamic workflows"](https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code)，2026；官方共命名 6 种，另三种——fan-out-and-synthesize / adversarial verification / loop-until-done——corpus 已有对应物）：

- **Tournament**——N 个 worker 用不同方法做同一任务，judge 做 **pairwise 比较**逐轮淘汰。官方论断："comparative judgment is more reliable than absolute scoring"——两两比较比绝对打分可靠。适合解空间宽、无客观 oracle 的选优（多方案设计、文案）；跟 [`adversarial-verification.md`](adversarial-verification.md) 的 LLM-as-judge（绝对分 0-1）/ de-anchored judge（防锚定）互补，是第三种 judge 形态。
- **Generate-and-filter**——大量生成候选 → 按 rubric 过滤 + 去重 → 只留最优。与 Tournament 的分界：filter 是**绝对门槛**筛，tournament 是**相对比较**排——评估便宜、标准能写清用 filter；评估贵或标准说不清（只能比不能打分）用 tournament。
- **Classify-and-act**——classifier agent 先判任务类型 / 复杂度，再路由到不同 agent 或模型档位。是上面「成本 & 何时值得用 multi-agent」的运行时版本：不靠人预判，先花一次小分类调用再分发。

同篇 blog 的一句安全做法（**非**命名模式，别引成模式）：读不受信外部内容的 agent 不持高权限、持高权限的 agent 只收处理后的信息——跟 [`fact-forcing-gate.md`](fact-forcing-gate.md) 的权限分层同向。

## Continue vs. New Worker

| Situation | Decision | Reason |
|-----------|----------|--------|
| Research worker found the exact files to edit | Continue same worker | Already has file context |
| Research was broad but implementation is narrow | New worker | Avoid context noise |
| Correcting a failed attempt | Continue same worker | Already has error context |
| Verifying someone else's implementation | New worker | Fresh perspective, no anchoring |
| First approach was completely wrong | New worker | Avoid anchoring to failed strategy |

## Iterative Retrieval (when worker context cannot be predicted)

The default rule in `techniques/worker-instructions.md` is "make the prompt
self-contained" — list file paths, line numbers, completion criteria. This
works when the **coordinator already knows** which files / symbols the worker
needs.

For genuinely exploratory tasks — "find all places that handle X" / "review
every caller of Y for memory safety" / "is there an existing helper for Z?" —
the coordinator does not yet know the file set. Three naive options all fail:

- **Send everything**: exceeds worker context
- **Send nothing**: worker lacks critical context, makes wrong calls
- **Guess what's needed**: usually wrong; wastes a dispatch

### The 4-phase loop

```
  Dispatch ──▶ Evaluate ──▶ Refine ──▶ Loop (max 3 cycles)
  (broad      (what was    (worker     (then return findings
   initial     found vs     fetches     even if partial — do
   query)      what's       follow-up   not extend the budget)
               missing)     itself)
```

The defining move is **Phase 3 (Refine)**: the worker fetches its own follow-up
context (Grep / Read more files) instead of returning to the coordinator and
asking for permission. Each round-trip to the coordinator costs latency and
context — the worker should be empowered to dig deeper within its own session.

### When to use this pattern

- Worker task is **exploratory** (research, audit, "find all X")
- Coordinator can articulate the **goal** but not the **file set**
- Worker has Glob / Grep / Read tools available
- Sending whole repo would exceed worker context

### When NOT to use

- Coordinator already knows the file set → use standard self-contained prompt
- Task is **implementation** with clear target file (file paths are in the plan)
- Worker has only narrow read tools without search capability

### Worker prompt template

```
Task: [investigation goal in one sentence].

Phase 1 — Dispatch: start with [initial search query / glob pattern].

Phase 2 — Evaluate: after the initial sweep, report (to yourself):
  - what you found
  - what is still unclear / missing
  - what additional context you need

Phase 3 — Refine: based on Phase 2, fetch the additional context yourself
  (Grep / Read more files). DO NOT come back to ask permission for
  follow-up reads.

Phase 4 — Loop: max 2 more cycles, then return findings even if incomplete.

Report:
  - files investigated
  - what was found vs what was missed
  - confidence level
```

### Cap the loop

**Max 3 cycles total.** After that:

- Either the worker has enough → report findings
- Or the task is too broad → return partial findings + flag "needs scope reduction"

Do **not** extend the loop budget. If 3 cycles isn't enough, the coordinator
should reformulate the task — splitting it, narrowing the scope, or providing
a better initial dispatch query — rather than letting the worker spin.

## Failure Escalation

This applies the general failure escalation from `guidelines/workflow/agent-lifecycle.md` to the coordinator-worker context:

1. Worker fails → continue the same worker (already has error context)
2. Correction fails → change approach, still continue the same worker
3. Third failure → report to the user with a list of approaches tried and why each failed

**Never let a failing approach loop more than three times.**

## Stopping Misdirected Work

If the direction changes mid-task (user redirects, new information emerges):
- Stop the current worker immediately
- Do not let a wrong-direction worker run to completion
- Continue the same worker with corrected instructions (it has the existing context)

## Related Guidelines

- See `guidelines/collaboration/multi-agent.md` for declarative multi-agent rules.
- See `guidelines/workflow/agent-lifecycle.md` for general failure modes and escalation rules.
- See `techniques/worker-instructions.md` for how to write effective worker prompts.
