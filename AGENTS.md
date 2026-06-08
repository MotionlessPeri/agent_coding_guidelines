# AGENTS.md — Universal Agent Guidelines

This is the canonical instruction file for both Claude and Codex agents.

---

## How This Repository Is Organized

Guidelines are grouped by topic under `guidelines/`:

| Directory | Contents |
|-----------|----------|
| `guidelines/workflow/` | Commit rules, documentation rules, agent lifecycle, handoff workflow |
| `guidelines/code/` | Code constraints, validation requirements |
| `guidelines/cpp/` | C++ / Windows DLL / cmake / MSVC 工程底座的 hidden contract——跨 DLL 单例内联陷阱 / 符号导出 / 增量编译 ABI 不一致 / stale `.vcxproj` / 热路径 move 与 dynamic_cast。框架无关，多 DLL 插件（含 Maya `.mll`）高频命中。**非 C++ 项目可 skip** |
| `guidelines/collaboration/` | Multi-agent setup, private docs policy |
| `guidelines/ci-windows/` | Windows CI (PowerShell / GitLab runner) 跑 native command 时的 pitfall 集——PowerShell ↔ native exe 之间的抽象漏洞 |
| `guidelines/claude-code/` | Claude Code 自身（harness / hooks / settings.json）的 hidden contract——文档没明说但实测如此的行为 |
| `guidelines/p4/` | Perforce 特有 hidden contracts——charset transcoding / typemap / 跟 git 不同的字节保留语义 |
| `guidelines/ue/` | **当前最重的子目录**（~950 行 / 6 份 guidelines；另有 4 份内容已 promote 到 skill：`skills/ue/ue-module-architecture/` 2 份 + `skills/ue/ue-reference-engine-source/` + `skills/ue/ue-settings-persistence/`）。Unreal Engine framework hidden contracts + idiom 集中在此。**非 UE 项目可整段 skip**。完整索引 + 按场景导航见 [`guidelines/ue/INDEX.md`](guidelines/ue/INDEX.md) |
| `guidelines/maya/` | Maya C++ 插件（`MPx*` plugin / manip / context / 多 `.mll` 共享 base 层）的 framework hidden contracts——靠踩坑得到、Maya 文档没明说的约束。**非 Maya 项目可整段 skip**。索引 + 配套 skill 见 [`guidelines/maya/INDEX.md`](guidelines/maya/INDEX.md) |
| `techniques/` | Procedural patterns and step-by-step operational guides |
| `skills/` | Claude Code skill files, organized by category under `skills/<category>/<name>/SKILL.md` (categories: `ue/` / `maya/` / `architecture/` / `workflow/` / `collaboration/`). **Lazy-loaded** by Claude Code at invocation time — NOT `@`-imported here. Synced **flat** to `~/.claude/skills/<name>/` (Claude Code discovery requires flat) via `scripts/sync-skills.ps1` (recursive scan + flat copy)。Codex 无对应机制，需手动读取 SKILL.md |

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

@guidelines/code/diagnose-before-fixing.md

@guidelines/code/validation.md

@guidelines/cpp/multi-dll-plugin.md

@guidelines/cpp/build-incremental-and-cmake.md

@guidelines/cpp/hot-path-cpp.md

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

@guidelines/ue/details-customization-prefer-reflection.md

@guidelines/ue/property-handle-strong-capture.md

@guidelines/ue/external-automation-write-path.md

@guidelines/ue/mcp-platform-choice.md

@guidelines/ue/logicdriver-state-class-rewires-boundgraph.md

@guidelines/maya/manip-container-constraints.md

@guidelines/maya/selection-context-and-undo.md

@guidelines/maya/plugin-build-and-scripting-contracts.md

---

## Techniques

@techniques/adversarial-verification.md

@techniques/coordination-patterns.md

@techniques/worker-instructions.md

@techniques/fact-forcing-gate.md

@techniques/context-budget-audit.md

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

**workflow/** —— 跨域 workflow 编排 + TDD discipline：

- [`skills/workflow/supervised-workflow/SKILL.md`](skills/workflow/supervised-workflow/SKILL.md) — high-touch 工作流，三个 hard user-review gate（plan / impl-plan / per-milestone）
- [`skills/workflow/autonomous-workflow/SKILL.md`](skills/workflow/autonomous-workflow/SKILL.md) — low-touch 工作流，仅 plan gate（实施阶段无 gate）；handoff 文档（brief / context / worklog / result）+ 强 TDD 作执行期安全网
- [`skills/workflow/tdd-with-fixtures/SKILL.md`](skills/workflow/tdd-with-fixtures/SKILL.md) — augment superpowers TDD，加 milestone-level discipline + fixture/manual case escape hatch
- [`skills/workflow/bugfix-tdd/SKILL.md`](skills/workflow/bugfix-tdd/SKILL.md) — bug-fix 场景的 TDD 红→绿 discipline。先写 demonstrate bug 的 failing test → 跑确认 FAIL → 改 production → 跑 PASS → 跑全 regression → test + fix 单 commit。跟 `superpowers:test-driven-development`（feature TDD）/ `superpowers:systematic-debugging`（debug 阶段方法论）/ `tdd-with-fixtures`（escape hatch）互补不重叠。防"看代码自信改一行"无证据修复

**ue/** —— UE 专用：

- [`skills/ue/ue-module-architecture/SKILL.md`](skills/ue/ue-module-architecture/SKILL.md) — UE plugin module 切分两层规则：同 module 内 Runtime Ops / Editor Actions / UI 三层模型 + 跨 module Runtime ← Editor 依赖方向硬约束。bundle 了 `editor-runtime-separation.md` + `runtime-module-no-editor-dep.md` 两份原 guideline 内容
- [`skills/ue/ue-reference-engine-source/SKILL.md`](skills/ue/ue-reference-engine-source/SKILL.md) — meta prep-work：写 UE 功能前先找 reference impl。按 22 个 UE 子系统给 engine source 清单 + 5-tier 优先级 + anti-patterns。bundle 了原 `reference-engine-source.md`
- [`skills/ue/ue-settings-persistence/SKILL.md`](skills/ue/ue-settings-persistence/SKILL.md) — UE settings 持久化的三件套（`UPROPERTY(config)` + `Config=<Cat>, DefaultConfig` + `TryUpdateDefaultConfigFile()`）/ `SaveConfig()` 无参陷阱 / `AssetRegistrySearchable` per-instance tag / 嵌套 UObject 集合 PostEditChangeProperty 同步 pattern / 症状→trap 排查表。bundle 了原 `settings-persistence.md`
- [`skills/ue/unrealmcp-usage/SKILL.md`](skills/ue/unrealmcp-usage/SKILL.md) — 消费侧 agent 用 UnrealMCP 插件（TCP 命令到 UE editor）做编辑器自动化（spawn / 改 property / call subsystem / save-exit 等）。bundle 了 canonical TCP 客户端 `ue_cmd.py`，消费项目不再需要自己拷贝。覆盖 detection / TCP invoke pattern / capability gap policy（MCP 不够用先问 user 要不要扩 fork） / top 5 inline gotchas / onboarding 新项目接入步骤 / extending fork 时两侧同步规则。Fork 是 `E:\xd_projects\unreal-mcp`，完整命令参考 + known-issues 在项目里 sync 后的 `UnrealMCP_Docs/`

**maya/** —— Maya 插件专用：

- [`skills/maya/maya-tool-interaction/SKILL.md`](skills/maya/maya-tool-interaction/SKILL.md) — DCC 拖拽编辑工具（Maya manip/context，泛化到其他 3D 工具）的五个交互模式：press-time 完整重算（不累加 delta）/ press-time caching 防反馈闭环漂移 / 位移阈值防抖 / snapshot-diff undo（非 plug-level）/ undo 数据存业务对象而非 UI manip。配套 framework 契约见 `guidelines/maya/`。单项目验证、apply-and-refine

**architecture/** —— 框架无关架构 pattern：

- [`skills/architecture/multi-plugin-shared-core/SKILL.md`](skills/architecture/multi-plugin-shared-core/SKILL.md) — 多插件共享一个 core 实体的五个可组合模式：type-keyed ExtensionContainer（替代继承爆炸）/ feature-parser 注册制（base 零依赖）/ Preset→Template→Instance 数据驱动三段式 / Snapshot+Ops 数据操作分离 / 非拥有 Registry 单一查询入口解耦命令。框架无关（Maya 多 `.mll` 提炼，UE module / 通用 plugin 系统同样适用）。跟 `skills/ue/ue-module-architecture` 同形态不同框架。单项目验证、apply-and-refine

**collaboration/** —— 多 agent / 多对话协作机制：

- [`skills/collaboration/multi-session-coordination/SKILL.md`](skills/collaboration/multi-session-coordination/SKILL.md) — 多个 Claude Code 对话并发在同一 repo 工作时的协调协议。bundle 了 hook 脚本 (`multi_session.py`) + agent-side 政策（lease 让/抢/协商 heuristics + commit-then-release 强约束）+ 安装文档 (`install.md` / `install.ps1`)。Hook 机制由 `settings.json` 注册自动跑（SessionStart 注册 / PreToolUse 撞 lease deny / PostToolUse 记 touched_files / UserPromptSubmit 注入 inbox + git log since last turn / Stop 释放 lease）；skill 仅在 hook surface 协调信息时按需 load。需走 `install.ps1` 一次注册 hook

> Sync 注：repo 是分类目录（`<category>/<name>/SKILL.md`），但 sync 到 `~/.claude/skills/` 时**扁平化**为 `<name>/`（Claude Code discovery 不识别嵌套）。`ue-*` prefix 在 sync 后的 flat target 仍然可见 UE 归属。详 `scripts/sync-skills.ps1`
