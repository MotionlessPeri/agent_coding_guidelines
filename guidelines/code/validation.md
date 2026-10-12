# Validation Guidelines

## Choose Evidence for the Change

- Run the checks required by the project and checks that can detect the failure modes of the change. New behavior and bug fixes need behavioral evidence; documentation and mechanical edits need relevant content or structural checks.
- Choose regression coverage from affected interfaces, callers, and shared dependencies. Run a full suite or full build when the project requires it or the impact warrants it; do not require one for every edit.
- For behavioral changes, exercise the relevant error or boundary cases as well as the happy path. Prefer an independent observable result over assertions that merely repeat the implementation.
- Reuse valid evidence for unchanged inputs, artifacts, and environment. Rerun when those premises change or a failure leaves a concern unresolved.

## Build and Artifact Verification

- Build affected code before claiming that it builds. Use a cold rebuild or process restart when hot reload or incremental output cannot validate the change, such as ABI, module loading, or stale generated artifacts. Native code alone does not make every incremental build invalid.
- A failed build can leave a stale test binary. Establish that tests executed the intended artifact; a green test result from the old binary does not validate the change.
- Preserve complete build output when it is needed for diagnosis. Read the actual build result and relevant diagnostics; use targeted searches and summaries without discarding the underlying log. Reading every line of a large log is not itself evidence of success.
- A wrapper's exit code may differ from the build process's exit code. Capture and propagate the actual process result, then inspect failure diagnostics. A search that finds no error text is insufficient on its own. For PowerShell pitfalls, read [the platform notes](../ci-windows/powershell-native-command-pitfalls.md) when applicable.
- If a required build or check fails, fix it or report the unresolved failure and its effect on the claim. Do not describe blocked verification as passing.

## Integration Checks

- When startup, registration, or packaging changes, run a relevant smoke check.
- When adding or changing a command, tool, or API endpoint, verify the implementation and its exposed entry point together, and update user-facing documentation as needed.
- For Unreal Engine graph changes, exercise a representative asset and inspect graph compilation diagnostics; C++ compilation alone cannot establish graph correctness.

## Reporting

- State what was checked, what the result supports, and any material unverified part. Code inspection can support a review finding but does not establish runtime behavior.
- Match completion claims to the available evidence. Include a concise result summary; retain detailed logs where they are useful rather than pasting them all into the conversation.
- For a task that needs additional adversarial probes, consult [adversarial verification](../../techniques/adversarial-verification.md) for the applicable change type.
