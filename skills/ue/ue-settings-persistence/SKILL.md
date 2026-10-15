---
name: ue-settings-persistence
description: Use for UE Project Settings, UDeveloperSettings, Config UObjects, per-asset metadata, or nested config collections; especially SaveConfig persistence failures after restart or across developers and CI. Skip non-UE settings.
---

# UE Settings Persistence

Choose the persistence target first: project-shared `Config/Default*.ini`, user-level configuration, or per-asset metadata. The shared-config recipe below does not apply to every persistence task.

Full content in the bundled doc:

[`settings-persistence.md`](settings-persistence.md) — scope and evidence, shared-config recipe, actual write-target checks, per-asset metadata, nested UObject collections, and project examples. Read the relevant section; the source case's UE version was not recorded, and this documentation update did not revalidate engine behavior.

## When This Fires

| Trigger | What to check in the bundled doc |
|---|---|
| Adding / modifying a Project Settings page or `UDeveloperSettings` subclass | Establish shared vs user configuration, then check the applicable class flags and write target |
| Calling `SaveConfig()` in code | "原共享配置案例中的无参 `SaveConfig()` 误用" — confirm whether you want repo-tracked or user-level |
| Persisting per-asset metadata (DialogueId, RecipeId, bReviewed, etc.) | `AssetRegistrySearchable` section — usually preferable to a mirror table |
| Symptom: setting disappears after editor restart | Failure Symptoms table — usually missing `Config` flag or wrong SaveConfig overload |
| Symptom: Dev A's setting not visible to Dev B / CI | Check whether the actual file is user-level instead of the intended version-controlled default configuration |
| Designing `TArray<UObject*>` / `TMap<FName, UObject*>` setting where elements have own config fields | "特殊路径：嵌套 UObject 集合" — flat mirror + `PostEditChangeProperty` sync pattern |

## Project-shared configuration recipe

To make a setting field reach the repo's `Config/Default*.ini`:

1. **Field**: `UPROPERTY(EditAnywhere, Config, Category = "Foo")`
2. **Host class**: `UCLASS(Config = Editor, DefaultConfig)` (or `Config = Game` / engine / custom category)
3. **Write code in the source case**: `Object->TryUpdateDefaultConfigFile()`; verify the actual target rather than treating every no-argument `SaveConfig()` call as wrong

This is the recorded shared-config recipe, not a claim that these exact choices are necessary for every settings class. Confirm the file changed and the value survives restart. User-level settings and per-asset metadata follow their own target and mechanism; source provenance and remaining version uncertainty are recorded in the bundled document.

## Related

- `guidelines/ue/localization-pitfalls.md` Trap 4 — `ULocalizationTargetSet::TargetObjects` is not `UPROPERTY(config)`; needs the nested-UObject-collection workaround pattern. Engine-internal example of this skill's "TArray-of-UObject*" section.
- `guidelines/ue/asset-definition-can-duplicate-limit.md` — handling DA UPROPERTY values during copy, complementary to `AssetRegistrySearchable` (rename/move follow, but Copy+Paste does not — see CanDuplicate / PostDuplicate)
- `guidelines/code/validation.md` — verifying a setting change actually persists (don't trust "code looks correct" — verify by reading the ini file after action)
