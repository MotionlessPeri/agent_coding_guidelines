# Fixture 与人工用例参考

只在需要创建或维护可复现验证材料时读取。路径和命名沿用项目约定；模板是起点，不要求为简单测试额外建档。

## Fixture Library

A **fixture** is a reproducible "known starting state" for testing. Properties: content is predetermined; reloading yields the same state.

**Where they live** (default; project AGENTS.md may override):
- `tests/fixtures/<area>/<name>.<ext>` for test data files (.xlsx, .json, .uasset, .sql, etc.)
- `tests/fixtures/<area>/setup_<name>.py` for programmatic state setup
- Project-specific layout: defer to the project's AGENTS.md or test conventions

**Naming**:
- Name after the behavior or bug being tested: `fixture-reroute-pin-double-direction.uasset`, not `test1.uasset`
- Include a short README or top-of-file comment explaining what state it represents

**Size discipline**:
- Distill to minimum reproducer. A 100 MB asset is rarely a real fixture — it's project state that drifted in.
- If a fixture must be large, document why; otherwise reduce it.

**Lifecycle**:
- Fixture stays as long as the manual case referencing it stays
- When the manual case is retired, retire the fixture too — don't leave orphans

## Manual Test Case Archive

A **manual test case** is a procedure a human can re-run to verify behavior. It is a contract: future you / future agent / future teammate must be able to follow it without asking questions.

**Format** (default; project may override):

```markdown
### TC-<id>: <short title>

**Goal**: what behavior this verifies
**Fixture**: path to fixture(s) used (or "none" if setup is in steps)
**Setup**: prerequisites not in fixture (env vars, build mode, etc.)
**Steps**:
1. Concrete action
2. Concrete action
3. ...
**Expected**: specific, observable outcome — no "looks right" / "works"
**Last verified**: <date> on <commit hash>
**Notes**: known caveats, related bugs, etc.
```

**Where they live** (default; project AGENTS.md may override):
- `docs/manual-tests.md` for a short flat list
- `docs/manual-tests/<area>.md` when split by area (e.g., `graph-editor.md`, `localization.md`)
- Project-specific: defer to project conventions

**Discipline**:
- "Expected" must be unambiguous — observable, not subjective
- "Last verified" gets updated only when you actually run the case end-to-end
- Re-verify when the tested source, artifact, environment or requirement changes. Age alone does not invalidate evidence; do not retire a useful regression case merely because it is old.
- A case that fails: fix it (or the underlying behavior) before declaring the milestone done
