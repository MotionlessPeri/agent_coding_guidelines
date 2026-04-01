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
