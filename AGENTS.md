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

**Adding new files:**
- Place new files in the appropriate subdirectory.
- If no existing category fits, create a new subdirectory.
- Add a reference to the new file in this AGENTS.md under the relevant section.
- Keep each file focused on one topic. Split if it covers 3+ independent concerns or exceeds ~200-300 lines.
- `guidelines/` = declarative rules ("always do X, never do Y"). `techniques/` = procedural patterns ("step 1, step 2, step 3").

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
