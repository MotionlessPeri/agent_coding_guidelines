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
| `guidelines/ci-windows/` | Windows CI (PowerShell / GitLab runner) 跑 native command 时的 pitfall 集——PowerShell ↔ native exe 之间的抽象漏洞 |
| `guidelines/claude-code/` | Claude Code 自身（harness / hooks / settings.json）的 hidden contract——文档没明说但实测如此的行为 |
| `guidelines/p4/` | Perforce 特有 hidden contracts——charset transcoding / typemap / 跟 git 不同的字节保留语义 |
| `guidelines/ue/` | **当前最重的子目录**（~950 行 / 6 份 guidelines；另有 4 份内容已 promote 到 skill：`skills/ue-module-architecture/` 2 份 + `skills/ue-reference-engine-source/` + `skills/ue-settings-persistence/`）。Unreal Engine framework hidden contracts + idiom 集中在此。**非 UE 项目可整段 skip**。完整索引 + 按场景导航见 [`guidelines/ue/INDEX.md`](guidelines/ue/INDEX.md) |
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

@guidelines/workflow/daily-and-open-items.md

@guidelines/code/clarify-before-implementing.md

@guidelines/code/reuse-before-implementing.md

@guidelines/code/constraints.md

@guidelines/code/function-clarity.md

@guidelines/code/validation.md

@guidelines/collaboration/multi-agent.md

@guidelines/collaboration/private-docs-policy.md

@guidelines/ci-windows/powershell-native-command-pitfalls.md

@guidelines/claude-code/hook-conventions.md

@guidelines/p4/charset-pitfalls.md

@guidelines/ue/graph-editor-constraints.md

@guidelines/ue/graph-data-ownership.md

@guidelines/ue/blueprint-auto-override-api.md

@guidelines/ue/asset-definition-can-duplicate-limit.md

@guidelines/ue/localization-pitfalls.md

@guidelines/ue/build-plugin-limitations.md

@guidelines/ue/automation-test-from-ci.md

---

## Techniques

@techniques/adversarial-verification.md

@techniques/coordination-patterns.md

@techniques/worker-instructions.md

@techniques/ue-custom-graph-editor.md

@techniques/claude-code-autonomous-permissions.md

@techniques/ci-deploy-to-p4.md

---

## Skills

`skills/` 下是 Claude Code skill 形态的内容。跟 guidelines / techniques 的核心区别：

- **不通过 `@` 进 context**——由 Claude Code 在 invocation 时按需 lazy load
- 适合按 phase / domain 触发的内容（workflow 编排、跨工作流的 TDD discipline 等）
- 通过 `scripts/sync-skills.ps1` 单向同步到 `~/.claude/skills/`（Claude Code 的 personal scope 发现位置）；repo 是 source of truth
- Codex 无 skill 发现机制；如需 Codex 用，手动读取对应 `SKILL.md`（每个 skill 是 markdown 文档）

当前 skills：

- [`skills/supervised-workflow/SKILL.md`](skills/supervised-workflow/SKILL.md) — high-touch 工作流，三个 hard user-review gate（plan / impl-plan / per-milestone）
- [`skills/autonomous-workflow/SKILL.md`](skills/autonomous-workflow/SKILL.md) — low-touch 工作流，仅 plan gate（实施阶段无 gate）；handoff 文档（brief / context / worklog / result）+ 强 TDD 作执行期安全网
- [`skills/tdd-with-fixtures/SKILL.md`](skills/tdd-with-fixtures/SKILL.md) — augment superpowers TDD，加 milestone-level discipline + fixture/manual case escape hatch
- [`skills/ue-module-architecture/SKILL.md`](skills/ue-module-architecture/SKILL.md) — UE plugin module 切分两层规则：同 module 内 Runtime Ops / Editor Actions / UI 三层模型 + 跨 module Runtime ← Editor 依赖方向硬约束。bundle 了 `editor-runtime-separation.md` + `runtime-module-no-editor-dep.md` 两份原 guideline 内容
- [`skills/ue-reference-engine-source/SKILL.md`](skills/ue-reference-engine-source/SKILL.md) — meta prep-work：写 UE 功能前先找 reference impl。按 22 个 UE 子系统给 engine source 清单 + 5-tier 优先级 + anti-patterns。bundle 了原 `reference-engine-source.md`
- [`skills/ue-settings-persistence/SKILL.md`](skills/ue-settings-persistence/SKILL.md) — UE settings 持久化的三件套（`UPROPERTY(config)` + `Config=<Cat>, DefaultConfig` + `TryUpdateDefaultConfigFile()`）/ `SaveConfig()` 无参陷阱 / `AssetRegistrySearchable` per-instance tag / 嵌套 UObject 集合 PostEditChangeProperty 同步 pattern / 症状→trap 排查表。bundle 了原 `settings-persistence.md`
- [`skills/multi-session-coordination/SKILL.md`](skills/multi-session-coordination/SKILL.md) — 多个 Claude Code 对话并发在同一 repo 工作时的协调协议。bundle 了 hook 脚本 (`multi_session.py`) + agent-side 政策（lease 让/抢/协商 heuristics + commit-then-release 强约束）+ 安装文档 (`install.md` / `install.ps1`)。Hook 机制由 `settings.json` 注册自动跑（SessionStart 注册 / PreToolUse 撞 lease deny / PostToolUse 记 touched_files / UserPromptSubmit 注入 inbox + git log since last turn / Stop 释放 lease）；skill 仅在 hook surface 协调信息时按需 load。需走 `install.ps1` 一次注册 hook
