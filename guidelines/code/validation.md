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
