# Knowledge Promotion Guidelines

Rules for deciding when a lesson learned in a specific project should be
promoted to this shared guidelines repository, and how to do it.

## Why This Exists

This repository is a **meta-corpus** — rules that apply across projects. The
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

Keep out of the shared repo:

- **Project-specific names, paths, or identifiers** (commit prefixes,
  P4 workspaces, port numbers, repo URLs, engine install locations).
- **One-off bug fixes** whose solution does not generalize — the fix
  belongs in the project commit, not the meta-corpus.
- **Rules already in the framework's own docs** — if it's in the UE engine
  source comments or the tool's official guide, cite the source from the
  project instead of duplicating here.
- **Organization-specific policies** (a specific company's code-review
  norms, compliance frameworks) — they belong in that organization's own
  AGENTS.md.
- **Exploratory or unverified patterns** — if it has only been tried once
  and it worked, it is not yet a guideline. Wait until it proves itself
  in a second use.

## Promotion Workflow

1. **Draft in the project first.** Write the lesson into the project's own
   docs (`Docs/`, `AGENTS.md`, or a plan file). Use it there for at least
   one real task cycle to validate it is actionable.

2. **Strip project-specific details.** When extracting, replace concrete
   names with category examples. "In DialogueSystemSample we saw X" becomes
   "UE graph editor plugins must do X".

3. **Pick the right subdirectory** under `guidelines/` (full, non-drifting list:
   the "How This Repository Is Organized" table in `AGENTS.md` is the SoT).
   Current categories: `workflow/` `code/` `writing/` `collaboration/` `cpp/`
   `ci-windows/` `claude-code/` `p4/` `ue/` `maya/`.
   - Create a new subdirectory only if the lesson does not fit any existing
     category and at least one more lesson is expected in that category.

4. **Create the file** with a focused scope (one topic per file). Use
   existing files as style reference — declarative rules, concise bullets,
   tables where comparisons help. Keep under ~200 lines; split if longer.

5. **Register it in `AGENTS.md`** by adding `@guidelines/<subdir>/<name>.md`
   in the appropriate section. Without the `@` import, the file is
   invisible to agents even after commit.

6. **Commit separately** with a `governance:` or `docs:` message. Do not
   bundle the promotion commit with unrelated project work.

## Agent Behavior

- When you notice a signal that **clearly** matches "What to Promote"
  during project work, flag it to the user — do not silently promote.
- When unsure whether a lesson generalizes, leave it in the project docs.
  The promotion step is a conscious decision, not a default action.
- Never leave the same content in both places — either the canonical
  version lives in guidelines and the project `@`-imports it, or it moves
  fully into the project if it turned out to be project-specific.
- Do not promote at every session end. The trigger is "I spotted a
  generalizable lesson," not a periodic sweep.
