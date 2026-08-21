# Validation Guidelines

## Build Verification

- Run a full build before reporting that code changes are complete.
- Use cold rebuild (not hot reload) when plugin or native code is changed.
- Example build invocation pattern (adapt to project):
  ```
  Build.bat <Project>Editor Win64 Development -Project="<uproject>" -WaitMutex -FromMSBuild
  ```
- If the build fails, fix the errors before proceeding. Do not report success.
- **A failed build can leave a stale test binary**, and a test runner (ctest, etc.) may
  then run the OLD binary and report false green. Check the build output for compile/link
  errors — do not read only the test result — or run the binary directly and confirm it is
  the rebuilt one. Running the test suite is not the same as running the new code.
- **不要在读之前过滤构建输出。** 把构建命令管给 `tail` / `grep` / `head` 再读，会把真正的
  错误行吞掉——而**吞掉的表现跟"没有错误"一模一样**（这正是"缺席有两种成因"的一个面，见
  [`reporting-limits-and-null-results.md`](reporting-limits-and-null-results.md) 规则 3）。
  ⇒ **整份输出落盘再读**（`> build.log 2>&1`，然后读文件）。要摘要就在**读过全文之后**摘。
- **包装命令的退出码不是被包裹命令的退出码。** 后台任务 / shell wrapper / 脚本返回 0，
  不代表它包的那个构建成功了。判断构建成功看**日志里有没有编译 / 链接错误**，不看包装器的
  退出码。（PowerShell 侧的具体形态见
  [`../ci-windows/powershell-native-command-pitfalls.md`](../ci-windows/powershell-native-command-pitfalls.md)。）
  > 这两条跟本文件其余部分**差一层**：其余部分管"验证做得对不对"，这两条管"**证据在采集环节
  > 就被丢掉了**"——不是量错、也不是量具坏，是根本没采。实测在同一天内多次复现，每次都表现为
  > "我看不到错误 ⇒ 应该没问题"。

## Smoke Testing

- After a build, run a minimal smoke test to verify the tool or server starts:
  ```
  python server.py   # or project equivalent
  ```
- For new commands or API endpoints: verify the happy path works end-to-end.

## Adversarial Mindset

- The goal of verification is to try to break the change, not just confirm it works.
- Reading code is not verification — run commands and observe actual output.
- Do not write explanations of why code is correct; run the code and show evidence.
- Always test at least one non-happy-path scenario (error case, boundary value, edge case).
- Tests passing is necessary but not sufficient — tests can be self-referential. Verify
  behavior independently when practical.
- For change-type-specific verification steps (frontend, backend, CLI, infra, bug fix,
  refactor), see `techniques/adversarial-verification.md`.

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

## Related Techniques

- See `techniques/adversarial-verification.md` for detailed procedural checklists and
  adversarial probes.
