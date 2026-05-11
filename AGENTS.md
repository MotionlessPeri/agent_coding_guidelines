# AGENTS.md — Universal Agent Guidelines

This is the canonical instruction file for both Claude and Codex agents.

---

## How This Repository Is Organized

Guidelines are grouped by topic under `guidelines/`:

| Directory | Contents |
|-----------|----------|
| `guidelines/workflow/` | Commit rules, documentation rules, agent lifecycle, handoff workflow |
| `guidelines/code/` | Code constraints, validation requirements |
| `guidelines/collaboration/` | Multi-agent setup, private docs policy |
| `guidelines/ue/` | **当前最重的子目录**（~1400 行 / 8 份 guidelines）。Unreal Engine framework hidden contracts + idiom 集中在此。**非 UE 项目可整段 skip**。完整索引 + 按场景导航见 [`guidelines/ue/INDEX.md`](guidelines/ue/INDEX.md) |
| `techniques/` | Procedural patterns and step-by-step operational guides |
| `skills/` | Claude Code skill files (each skill = `skills/<name>/SKILL.md`). **Lazy-loaded** by Claude Code at invocation time — NOT `@`-imported here. Synced to `~/.claude/skills/` via `scripts/sync-skills.ps1`. Codex 无对应机制，需手动读取 SKILL.md |

**Adding new files:**
- Place new files in the appropriate subdirectory.
- If no existing category fits, create a new subdirectory.
- Add a reference to the new file in this AGENTS.md under the relevant section.
- Keep each file focused on one topic. Split if it covers 3+ independent concerns or exceeds ~200-300 lines.
- `guidelines/` = declarative rules ("always do X, never do Y"). `techniques/` = procedural patterns ("step 1, step 2, step 3"). `skills/` = Claude Code skills, triggered on demand (not eager-imported).

---

## Guidelines

@guidelines/workflow/commits.md

@guidelines/workflow/documentation.md

@guidelines/workflow/agent-lifecycle.md

@guidelines/workflow/handoffs.md

@guidelines/workflow/code-review.md

@guidelines/workflow/knowledge-promotion.md

@guidelines/code/clarify-before-implementing.md

@guidelines/code/reuse-before-implementing.md

@guidelines/code/constraints.md

@guidelines/code/validation.md

@guidelines/collaboration/multi-agent.md

@guidelines/collaboration/private-docs-policy.md

@guidelines/ue/reference-engine-source.md

@guidelines/ue/graph-editor-constraints.md

@guidelines/ue/editor-runtime-separation.md

@guidelines/ue/graph-data-ownership.md

@guidelines/ue/blueprint-auto-override-api.md

@guidelines/ue/asset-definition-can-duplicate-limit.md

@guidelines/ue/localization-pitfalls.md

@guidelines/ue/settings-persistence.md

---

## Techniques

@techniques/adversarial-verification.md

@techniques/coordination-patterns.md

@techniques/worker-instructions.md

@techniques/ue-custom-graph-editor.md

@techniques/claude-code-autonomous-permissions.md

---

## Skills

`skills/` 下是 Claude Code skill 形态的内容。跟 guidelines / techniques 的核心区别：

- **不通过 `@` 进 context**——由 Claude Code 在 invocation 时按需 lazy load
- 适合按 phase / domain 触发的内容（workflow 编排、跨工作流的 TDD discipline 等）
- 通过 `scripts/sync-skills.ps1` 单向同步到 `~/.claude/skills/`（Claude Code 的 personal scope 发现位置）；repo 是 source of truth
- Codex 无 skill 发现机制；如需 Codex 用，手动读取对应 `SKILL.md`（每个 skill 是 markdown 文档）

当前 skills：

- [`skills/supervised-workflow/SKILL.md`](skills/supervised-workflow/SKILL.md) — high-touch 工作流，三个 hard user-review gate（plan / impl-plan / per-milestone）
- [`skills/autonomous-workflow/SKILL.md`](skills/autonomous-workflow/SKILL.md) — low-touch 工作流，无 gate；handoff 文档（brief / context / worklog / result）+ 强 TDD 作安全网
- [`skills/tdd-with-fixtures/SKILL.md`](skills/tdd-with-fixtures/SKILL.md) — augment superpowers TDD，加 milestone-level discipline + fixture/manual case escape hatch
