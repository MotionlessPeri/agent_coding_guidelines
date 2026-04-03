# AGENTS.md — Universal Agent Guidelines

This is the canonical instruction file for both Claude and Codex agents.

---

## How This Repository Is Organized

Guidelines are grouped by topic under `guidelines/`:

| Directory | Contents |
|-----------|----------|
| `guidelines/workflow/` | Commit rules, documentation rules, agent lifecycle |
| `guidelines/code/` | Code constraints, validation requirements |
| `guidelines/collaboration/` | Multi-agent setup, private docs policy |
| `guidelines/ue/` | Unreal Engine editor and graph development rules |
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

@guidelines/code/constraints.md

@guidelines/code/validation.md

@guidelines/collaboration/multi-agent.md

@guidelines/collaboration/private-docs-policy.md

@guidelines/ue/graph-editor-constraints.md

@guidelines/ue/editor-runtime-separation.md

---

## Techniques

@techniques/adversarial-verification.md

@techniques/coordination-patterns.md

@techniques/worker-instructions.md

@techniques/ue-custom-graph-editor.md
