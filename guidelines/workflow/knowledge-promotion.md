---
class: norm
scope: universal
---

# Knowledge Promotion Guidelines

Rules for deciding when a lesson learned in a specific project should be
promoted to this shared guidelines repository, and how to do it.

The promotion criteria and workflow below apply when adopting a new cross-project
rule or operational default. Saving source-linked reference material or a synthesis
with explicit uncertainty is not that promotion: use [Maintenance and Evidence](#maintenance-and-evidence)
for those pages. They need neither two project incidents nor a new approval merely
to remain reference material, and they do not acquire authority by being saved.

## Why This Exists

This repository contains shared rules, procedures and supporting knowledge. The
pull direction (guidelines → project) is covered by
`collaboration/multi-agent.md`. This file covers the push direction
(project → guidelines).

Without an explicit promotion discipline:

- **Under-promotion** — every new project re-discovers the same framework
  constraints. The lesson stays trapped in one project's docs.
- **Over-promotion** — project-specific details pollute the shared repo
  and make it noisy for other projects.

Both failure modes are real. This file draws the line.

## What to Promote

A lesson is promotion-worthy if it meets **at least one** of these:

- **Two-strike rule** — the same class of issue **hit** in two different
  projects. One incident is an anecdote; two is a pattern. "Hit" means an
  **observed instance**, not a prediction — see the warning below.
- **Hidden contract in an external framework or tool** — behavior not
  documented by the tool itself but learned from its source, crashes, or
  bug reports. Examples: UE `PinWidget->SetOwner()` must be called exactly
  once; `git rebase --no-edit` is invalid.
- **Editor / IDE / CLI gotcha** an agent would otherwise re-encounter —
  e.g., Live Coding vs. cold rebuild, MCP protocol quirks, shell
  portability pitfalls.
- **Workflow discipline the user has confirmed works** — validated patterns
  for commits, reviews, verification, coordination.

### ⚠️ 多 agent 场景:一致的**推测**会伪造两击信号

两击规则里的"命中"必须是**观察到的实例**。但在多 agent / 多 lane 收尾复盘这种场景里,有一种东西
**长着两击的形状而没有两击的内容**:

**两个互不通气的 agent 从同一条框架契约出发推理,必然收敛到同一结论** —— 这个收敛由**共享前提**解释,
不由**世界**解释,所以零信息量。而汇总方看到"N 条 lane 独立提出同一条",天然读成"证据强"。

**当场判据**(收敛不携带信息的直接体现):**两条收敛的推测,如果收敛真的来自世界,它们不会在细节上
朝不同方向错。** 实测形态:两条 lane 对同一个框架约束给出几乎相同的推测,一条错在"**永久**关闭",
另一条错在"**必须**提供开关" —— 错的方向不同,正好说明收敛来自共享前提。

⇒ 汇总多方 harvest 时,给每条明确标一个字,别笼统说"N 条 lane 都提到了":

| 类别 | 判据 | 能否作两击 |
|---|---|---|
| **命中** | 观察到的实例,有实际代价 | ✅ |
| **规则生效** | 已有规则当场拦住一次误判。判据是**那个错误状态有没有留下第三方能看见的痕迹**(一条真的写进候选清单的条目 / 一句真的准备发出的话);只有"我本来会写 X、实际写了 Y"这种自述的,退回不可证伪一档 | ⛔ 但它是这份语料库**唯一的投入产出证据**(命中证明问题存在,生效才证明写下来的规矩真的拦住了问题)。⚠️ 这个数**结构性只报下界、偏差方向固定**:规矩内化得越好,错误状态越不成形、痕迹越少 ⇒ 只作存在性证明,**不能跟命中数并列读**,也不能因为它小就推断规矩没起作用 |
| **提议** | 从机制推演,无实例 | ⛔ |

**诚实边界**:一次,且**没有造成误判**(当次汇总方判对了两条推测都不算)。所以它是"差点发生"的证据。
按本文件既有的促升先例(见 `code/reporting-limits-and-null-results.md` 诚实边界:不是"试了一次成功的
做法",而是**有明确机制 + 可量化代价**的失败模式,这类只能靠明写规矩兜的失败越早写下越省),仍值得
先写下:它的代价形态是"零证据的推测顶着『多次独立验证』进入常驻语料,之后污染所有引用且无痕",
而多 lane harvest 本身是低频动作 —— 等它真骗过一次,第一次的账已经付了。

## What NOT to Promote

Do not promote the following into cross-project rules or operational defaults:

- **Project-specific operational defaults** (commit prefixes, P4 workspaces,
  port numbers or engine install locations) do not become universal settings.
  Keep source project names, versions or commit IDs when needed to locate evidence;
  distinguish that provenance from instructions for the consuming project.
- **One-off bug fixes** whose solution does not generalize — the fix
  belongs in the project commit, not the meta-corpus.
- **Rules already in the framework's own docs** — if it's in the UE engine
  source comments or the tool's official guide, cite the source from the
  project instead of duplicating here.
- **Organization-specific or personal content** (a specific company's
  machines, services, forks or review norms; one person's preferences) — keep
  it in a narrower-scope corpus, an organization or personal overlay that links
  to this one. Promote upward only the part that still holds after those
  specifics are stripped.
- **Exploratory or unverified patterns** — if it has only been tried once
  and it worked, it is not yet a guideline. Wait until it proves itself
  in a second use.

## Promotion Workflow

1. **Draft in the project first.** Write the lesson into the project's own
   docs (`Docs/`, `AGENTS.md`, or a plan file). Use it there for at least
   one real task cycle to validate it is actionable.

2. **Separate the transferable conclusion from its source context.** State the
   conditions under which the lesson applies, and retain enough project/version
   information to locate its evidence. One project's observation does not become
   "all UE graph editor plugins must do X" merely by removing its project name.

3. **Choose the content type and destination.** Use [content boundaries](instruction-content.md)
   to distinguish knowledge, workflow and norms. Find the relevant topic in
   [the guidelines index](../INDEX.md), [the techniques index](../../techniques/INDEX.md),
   [the skill index](../../skills/INDEX.md) or [references](../../references/README.md).
   - Create a new subdirectory only if the lesson does not fit any existing
     category and at least one more lesson is expected in that category.

4. **Create or update a focused source.** State a norm declaratively, explain
   knowledge with its conditions and evidence, or write a procedure for its current
   task. Split by independent reading needs rather than copying the same conclusion
   into multiple authoritative files.

5. **Register a discovery entry** in `AGENTS.md` or a linked topic index.
   Use a task-specific link or skill for conditional material. Add an `@` import
   only when the content merits loading for every task in a host that expands
   imports. Discoverability does not require loading the whole file at startup.

6. **Commit separately** with a `governance:` or `docs:` message. Do not
   bundle the promotion commit with unrelated project work.

## Maintenance and Evidence

- Keep one authoritative location for each rule or technical conclusion. Indexes
  summarize its task boundary and link to it; a synthesis page explains connections
  without creating a second policy. Search relevance and summary fluency do not
  determine authority.
- For version-sensitive or uncertain claims, record the applicable environment,
  a source or reproducible observation, and what has actually been checked. Use a
  short paragraph or existing section; no mandatory metadata template for every file.
  If the version or original artifact was not recorded, say so rather than inventing it.
- Keep evidence limits at the granularity of the claim or section. A verified name
  or path does not establish an API signature or behavior. Excerpts and derived
  pages must preserve relevant conditions, exceptions and unverified parts.
- When a source changes, inspect known indexes and summaries that reference it.
  Search its filename or symbol within the affected topic, update dependent claims,
  and repair links after a move. Git preserves history; an extra universal ledger
  or a new approval round is not required.
- If a claim is disproved or superseded, remove it from current instructions or
  mark the affected passage with its replacement. Keep useful historical evidence
  separate from current guidance. Age alone does not prove a claim false, and a
  recent edit does not prove it correct.
- A model-generated synthesis is a reading aid. It retains links to its sources;
  new factual conclusions need supporting evidence, and new behavioral requirements
  must be covered by applicable authority. Reuse existing task authorization; saving
  a reference does not require another approval. Do not promote an answer merely
  because it was generated or reused.

## Agent Behavior

- When you notice a signal that **clearly** matches "What to Promote"
  during project work, flag it to the user — do not silently promote.
- When unsure whether a lesson generalizes, leave it in the project docs.
  The promotion step is a conscious decision, not a default action.
- Keep the canonical version in one place and link to it from the consuming
  project or topic summary. Project-specific variants state their differences;
  they do not silently fork the universal rule. A normal link is sufficient for
  on-demand discovery; imports are a separate loading decision.
- Do not promote at every session end. The trigger is "I spotted a
  generalizable lesson," not a periodic sweep.
