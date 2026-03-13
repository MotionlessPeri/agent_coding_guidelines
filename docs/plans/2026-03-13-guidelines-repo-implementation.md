# Guidelines Repository Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the full `agent_coding_guidelines` repository structure with all guideline files, entry docs, and README.

**Architecture:** AGENTS.md is the canonical entry point that imports all guideline files. CLAUDE.md is a thin pointer to AGENTS.md. Six guideline files under `guidelines/` organized into three categories. README explains the repo and how to connect it to other projects.

**Tech Stack:** Markdown files only. No build tools.

---

### Task 1: Create directory structure

**Files:**
- Create: `guidelines/workflow/` (directory)
- Create: `guidelines/code/` (directory)
- Create: `guidelines/collaboration/` (directory)

**Step 1: Create directories**

```bash
mkdir -p guidelines/workflow guidelines/code guidelines/collaboration
```

**Step 2: Verify**

```bash
ls guidelines/
```
Expected: `code/  collaboration/  workflow/`

**Step 3: Commit**

```bash
git add guidelines/
git commit -m "chore: scaffold guidelines directory structure"
```

---

### Task 2: Write `guidelines/workflow/commits.md`

**Files:**
- Create: `guidelines/workflow/commits.md`

**Step 1: Write the file**

```markdown
# Commit Guidelines

## Granularity

- One commit = one clear theme. All changed files must serve the same purpose.
- Valid commit themes: feature addition, bug fix, refactor, doc update, governance change, chore.
- Do not mix unrelated themes in one commit.

## Timing

- Commit only at stable points: conclusion reached, code compiles, tests pass.
- Do not commit after every editing step.
- A session may produce zero, one, or multiple commits — each must stand on its own.

## Message Format

Use: `<type>: <subject>`

Allowed types: `feat`, `fix`, `refactor`, `docs`, `governance`, `chore`, `index`, `glossary`

- Subject describes the knowledge or feature increment, not the editing action.
- Prefer concise, single-theme subjects in the project's working language.
- Examples:
  - `feat: add patrol on-arrived callback`
  - `docs: document snapshot capture/apply mechanism`
  - `governance: establish commit and doc rules`

## Agent Behavior

- Do not commit unless the user explicitly requests it.
- Whether to commit agent collaboration docs (CLAUDE.md, AGENTS.md, conversation notes) is
  **project-dependent**. Some projects want agent rules tracked in git; others don't.
  Decide per project and document the choice in that project's AGENTS.md.

## Pre-Commit Checks

Before committing, confirm:
1. The commit has exactly one theme.
2. Stable conclusions are written into formal documents (not only present in chat).
3. The index file is updated if new documents were added.
4. The commit message clearly states the increment.
```

**Step 2: Verify file exists and looks correct**

```bash
cat guidelines/workflow/commits.md
```

**Step 3: Commit**

```bash
git add guidelines/workflow/commits.md
git commit -m "docs: add commit guidelines"
```

---

### Task 3: Write `guidelines/workflow/documentation.md`

**Files:**
- Create: `guidelines/workflow/documentation.md`

**Step 1: Write the file**

```markdown
# Documentation Guidelines

## Sync Rules

- When you gain new code understanding or design details during a session, update the
  corresponding doc immediately. Do not wait for the user to prompt you.
- When you modify code, update the doc that describes that flow in the same change.
- When you find a doc is wrong, correct it immediately — do not preserve errors.
- When a new important file, class, or interface is added, update the project index.

## Writing Style

- Put conclusions before details.
- Convert conversation output into structured knowledge. Avoid transcript-style notes.
- Prefer sections: `Conclusion`, `Why`, `Typical Approaches`, `Open Questions`.
- Separate general principles from project-specific choices.

## Document Splitting

- If a document covers 3 or more independent topics, split it.
- If a document exceeds roughly 200-300 lines, evaluate splitting before extending further.
- If one section needs substantial background to stay readable, move it to its own file.

## Index Maintenance

- Every new document must be registered in the project's index file in the same work step.
- When a new term may be ambiguous, add it to the project glossary (if one exists).

## Deferred Topics

- Maintain a visible queue of deferred topics in the documentation.
- Phrase deferred topics as discussable questions, not vague reminders.
- When a deferred topic is later resolved, integrate the result into formal documents.

## In-Progress Docs

- Refactoring plans and progress records should be committed during active work so
  reviewers can track progress.
- Remove or archive them in a separate cleanup commit when the work is complete.
```

**Step 2: Verify**

```bash
cat guidelines/workflow/documentation.md
```

**Step 3: Commit**

```bash
git add guidelines/workflow/documentation.md
git commit -m "docs: add documentation guidelines"
```

---

### Task 4: Write `guidelines/workflow/agent-lifecycle.md`

**Files:**
- Create: `guidelines/workflow/agent-lifecycle.md`

**Step 1: Write the file**

```markdown
# Agent Lifecycle Guidelines

## Before Starting Any Task

1. Read the mandatory documents in the order specified by the project's AGENTS.md.
2. Confirm which subsystem or component is being changed before touching code.
3. If the project has a progress/plan document, check current state before proceeding.

## Autonomous Actions (Permitted Without User Confirmation)

The agent may perform the following autonomously when required by the task:

- Save and close the editor before a rebuild.
- Run a cold rebuild (compile) after plugin or C++ code changes.
- Restart the editor/server after a rebuild.
- Stage files and create commits **only when the user has explicitly requested a commit**.

## Actions Requiring User Confirmation

Always confirm with the user before:

- Force-pushing or resetting git history.
- Deleting files, branches, or database tables.
- Pushing to a remote repository.
- Creating or closing issues/PRs.
- Any action visible to others or affecting shared infrastructure.

If in doubt, ask first. The cost of asking is low; the cost of an unwanted action is high.

## Validation Before Completion

- Never claim work is "done" or "fixed" without running verification.
- Evidence before assertions: run the build, run the tests, check the logs.
- If build or tests fail, diagnose and fix — do not report completion.
- For tool/command additions: verify both the implementation layer and interface layer.

## Handling Blockers

- If an approach is blocked, do not retry the same action in a loop.
- Consider alternative approaches or ask the user for direction.
- Do not use destructive actions (e.g., `--no-verify`, `reset --hard`) as shortcuts.
```

**Step 2: Verify**

```bash
cat guidelines/workflow/agent-lifecycle.md
```

**Step 3: Commit**

```bash
git add guidelines/workflow/agent-lifecycle.md
git commit -m "docs: add agent lifecycle guidelines"
```

---

### Task 5: Write `guidelines/code/constraints.md`

**Files:**
- Create: `guidelines/code/constraints.md`

**Step 1: Write the file**

```markdown
# Code Constraints

## Architecture First

- Read and understand the relevant architecture documentation before modifying code.
- Identify which subsystem, flow, or module is being changed. Confirm scope before acting.
- Do not make changes that span unrelated components in one step.

## Correctness

- Avoid silent success: surface actionable errors when command or function preconditions
  are not met.
- Validate at system boundaries (user input, external APIs, tool interfaces).
- Do not add error handling for scenarios that cannot happen in practice.

## Commit Integrity

- Every commit must leave the repository in a usable state:
  - Code compiles.
  - Server/tool starts.
  - Existing tests pass.
- Do not commit partial implementations unless they are behind a feature flag or clearly
  marked as stubs.

## Simplicity

- Avoid over-engineering. Only make changes that are directly requested or clearly necessary.
- Don't add features, abstractions, or configurability beyond what the current task needs.
- Three similar lines of code is better than a premature abstraction.
```

**Step 2: Verify**

```bash
cat guidelines/code/constraints.md
```

**Step 3: Commit**

```bash
git add guidelines/code/constraints.md
git commit -m "docs: add code constraints"
```

---

### Task 6: Write `guidelines/code/validation.md`

**Files:**
- Create: `guidelines/code/validation.md`

**Step 1: Write the file**

```markdown
# Validation Guidelines

## Build Verification

- Run a full build before reporting that code changes are complete.
- Use cold rebuild (not hot reload) when plugin or native code is changed.
- Example build invocation pattern (adapt to project):
  ```
  Build.bat <Project>Editor Win64 Development -Project="<uproject>" -WaitMutex -FromMSBuild
  ```
- If the build fails, fix the errors before proceeding. Do not report success.

## Smoke Testing

- After a build, run a minimal smoke test to verify the tool or server starts:
  ```
  python server.py   # or project equivalent
  ```
- For new commands or API endpoints: verify the happy path works end-to-end.

## Tool/Command Additions

When adding a new command, tool, or API endpoint, verify:
1. The implementation layer handles the command correctly.
2. The interface layer (Python wrapper, route registration, etc.) exposes it correctly.
3. The documentation is updated in the same change.

## Graph/Blueprint Commands (Unreal Engine projects)

- Validate against a real test asset — do not rely only on compile success.
- Check engine logs for blueprint compile errors after any graph modification.

## Reporting Completion

- Only say "done" or "fixed" after running verification and confirming it passes.
- Include the verification output or a summary in your report to the user.
```

**Step 2: Verify**

```bash
cat guidelines/code/validation.md
```

**Step 3: Commit**

```bash
git add guidelines/code/validation.md
git commit -m "docs: add validation guidelines"
```

---

### Task 7: Write `guidelines/collaboration/multi-agent.md`

**Files:**
- Create: `guidelines/collaboration/multi-agent.md`

**Step 1: Write the file**

```markdown
# Multi-Agent Collaboration

## Single-Source Policy

- Use `AGENTS.md` as the canonical instruction file for both Claude and Codex.
- `CLAUDE.md` should be a thin pointer:
  ```markdown
  @AGENTS.md

  > Single-source policy: this file imports AGENTS.md. Maintain only AGENTS.md.
  ```
- Do not maintain two separate rule sets. If the files ever conflict, `AGENTS.md` wins.

## Conflict Resolution Order

When instructions conflict, apply this precedence (lower = higher authority):
1. Chat/session instructions (lowest)
2. Project repo documents
3. Earlier document in the project's mandatory reading list (highest among docs)

Fix doc inconsistencies in the same change when possible.

## Mandatory Reading

Each project's `AGENTS.md` should specify a mandatory reading list — an ordered list of
documents the agent must read before starting any task. Example:

```markdown
## Read Before Work

1. README.md
2. Docs/Architecture.md
3. Docs/Progress.md
```

## Accessing This Guidelines Repository

Three patterns, in order of preference:

**Option 1 — Global config**
Add to `~/.claude/CLAUDE.md` (Claude) or `~/.codex/AGENTS.md` (Codex):
```
@E:/xd_projects/agent_coding_guidelines/AGENTS.md
```
All sessions on this machine load the guidelines automatically.

**Option 2 — Per-project import**
Add to the project's `AGENTS.md`:
```
@E:/xd_projects/agent_coding_guidelines/AGENTS.md
```
Use when the project wants guidelines tracked alongside it, or when global config is unavailable.

**Option 3 — Project-local copy (agent-driven)**
For projects that need a customized or trimmed version, the agent copies and adapts the
relevant sections into the project's own `AGENTS.md`. The agent decides what to include
based on project context. No script required.
```

**Step 2: Verify**

```bash
cat guidelines/collaboration/multi-agent.md
```

**Step 3: Commit**

```bash
git add guidelines/collaboration/multi-agent.md
git commit -m "docs: add multi-agent collaboration guidelines"
```

---

### Task 8: Write `guidelines/collaboration/private-docs-policy.md`

**Files:**
- Create: `guidelines/collaboration/private-docs-policy.md`

**Step 1: Write the file**

```markdown
# Private Docs Policy

## What Belongs Out of the Project Tree

Keep the following **outside** the project directory (e.g. in a sibling `_agent_private/<project>/` directory):

- Agent debug logs
- Temporary analysis scratch files
- One-off investigation notes
- MCP/tool-generated artifacts not relevant to the codebase

This keeps the project clean for sharing, export, and code review.

## What Is Project-Dependent

**Progress notes** (task tracking, implementation plans, refactoring progress):
- May stay **in-tree** and be committed during active work, then removed in a cleanup commit.
- Or may go **out-of-tree** if you prefer to keep the repo pristine.
- Document the project's choice in its `AGENTS.md`.

**Agent collaboration docs** (CLAUDE.md, AGENTS.md, conversation guides):
- Whether to commit these to git is project-dependent.
- Some projects want agent rules tracked in git (portable, version-controlled).
- Others prefer to keep them local-only.
- Document the project's choice in its `AGENTS.md`.

## Recommended Directory Layout

```
<workspace>/
├── MyProject/                  ← shared project tree (clean)
│   ├── AGENTS.md
│   ├── CLAUDE.md
│   └── src/
└── _agent_private/
    └── MyProject/
        ├── docs/               ← agent progress notes, proposals
        └── artifacts/          ← generated files, debug logs
```

## Export Policy

If the project is shared or exported (e.g. as a sample), exclude agent-related files
by default. Only include AGENTS.md / CLAUDE.md if the recipient explicitly needs them.
```

**Step 2: Verify**

```bash
cat guidelines/collaboration/private-docs-policy.md
```

**Step 3: Commit**

```bash
git add guidelines/collaboration/private-docs-policy.md
git commit -m "docs: add private docs policy"
```

---

### Task 9: Write `AGENTS.md`

**Files:**
- Create: `AGENTS.md`

**Step 1: Write the file**

```markdown
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

**Adding new guidelines:**
- Place new files in the appropriate subdirectory.
- If no existing category fits, create a new subdirectory.
- Add a reference to the new file in this AGENTS.md under the relevant section.
- Keep each file focused on one topic. Split if it covers 3+ independent concerns or exceeds ~200-300 lines.

---

## Guidelines

@guidelines/workflow/commits.md

@guidelines/workflow/documentation.md

@guidelines/workflow/agent-lifecycle.md

@guidelines/code/constraints.md

@guidelines/code/validation.md

@guidelines/collaboration/multi-agent.md

@guidelines/collaboration/private-docs-policy.md
```

**Step 2: Verify**

```bash
cat AGENTS.md
```

**Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "docs: add AGENTS.md entry point"
```

---

### Task 10: Write `CLAUDE.md`

**Files:**
- Create: `CLAUDE.md`

**Step 1: Write the file**

```markdown
# CLAUDE.md

@AGENTS.md

> Single-source policy: this file imports `AGENTS.md`. Maintain only `AGENTS.md`.
```

**Step 2: Verify**

```bash
cat CLAUDE.md
```

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md thin pointer"
```

---

### Task 11: Write `README.md`

**Files:**
- Create: `README.md`

**Step 1: Write the file**

```markdown
# Agent Coding Guidelines

A central repository of universal guidelines and best practices for agent-assisted development.
Extracted and generalized from real projects. Project-specific rules are excluded.

## What's Here

| File/Directory | Purpose |
|----------------|---------|
| `AGENTS.md` | Canonical entry point for Codex and Claude agents |
| `CLAUDE.md` | Thin pointer to AGENTS.md for Claude |
| `guidelines/workflow/` | Commit, documentation, and lifecycle rules |
| `guidelines/code/` | Code constraints and validation requirements |
| `guidelines/collaboration/` | Multi-agent setup and artifact placement |
| `docs/plans/` | Design and implementation plans |

## How to Connect to Your Projects

**Option 1 — Global (all sessions on this machine):**
Add to `~/.claude/CLAUDE.md`:
```
@E:/xd_projects/agent_coding_guidelines/AGENTS.md
```

**Option 2 — Per project:**
Add to the project's `AGENTS.md`:
```
@E:/xd_projects/agent_coding_guidelines/AGENTS.md
```

**Option 3 — Project-local copy:**
For projects that need customized rules, the agent copies and adapts relevant sections
into the project's own `AGENTS.md`.

## Adding New Guidelines

1. Create a `.md` file in the appropriate `guidelines/` subdirectory.
2. Add a `@` reference to it in `AGENTS.md`.
3. Keep each file focused on one topic.

See `AGENTS.md` for the full organization rules.
```

**Step 2: Verify**

```bash
cat README.md
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

### Task 12: Clean up tmp.md and finalize

**Files:**
- Delete: `tmp.md`

**Step 1: Remove tmp.md**

```bash
git rm tmp.md
```

**Step 2: Verify repo state**

```bash
git log --oneline
ls -R guidelines/
```

Expected log: 10+ commits, each with one clear theme.
Expected listing: all 6 guideline files present.

**Step 3: Final commit**

```bash
git commit -m "chore: remove tmp.md scratch file"
```
