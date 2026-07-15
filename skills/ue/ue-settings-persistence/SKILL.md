---
name: ue-settings-persistence
description: Use when adding or modifying UE Project Settings, `UDeveloperSettings`, custom Config UObjects, or per-asset metadata; when choosing between `TryUpdateDefaultConfigFile`, `SaveConfig`, and `AssetRegistrySearchable`; or when settings disappear after restart or differ between developers and CI. Also use for nested UObject collections whose config fields need a flat mirror and `PostEditChangeProperty` synchronization.
---

# UE Settings Persistence

Hidden contracts for persisting UE settings into the project repo (git / P4-tracked `Config/Default*.ini`), not the per-user `Saved/Config/...` location that `SaveConfig()` no-arg silently writes to.

Full content in the bundled doc:

[`settings-persistence.md`](settings-persistence.md) — 5 sections: core three-piece rule, `SaveConfig()` no-arg trap explained, validation checklist, `AssetRegistrySearchable` (per-instance, orthogonal to `config`), nested UObject collection workaround pattern, symptom-to-trap diagnostic table, project examples.

## When This Fires

| Trigger | What to check in the bundled doc |
|---|---|
| Adding / modifying a Project Settings page or `UDeveloperSettings` subclass | Core three-piece rule + `Config = <Category>` + `DefaultConfig` flag |
| Calling `SaveConfig()` in code | "为什么 `SaveConfig()` 无参版是陷阱" — confirm whether you want repo-tracked or user-level |
| Persisting per-asset metadata (DialogueId, RecipeId, bReviewed, etc.) | `AssetRegistrySearchable` section — usually preferable to a mirror table |
| Symptom: setting disappears after editor restart | Failure Symptoms table — usually missing `Config` flag or wrong SaveConfig overload |
| Symptom: Dev A's setting not visible to Dev B / CI | Same — `SaveConfig()` no-arg wrote to user-level Game.ini, never entered version control |
| Designing `TArray<UObject*>` / `TMap<FName, UObject*>` setting where elements have own config fields | "特殊路径：嵌套 UObject 集合" — flat mirror + `PostEditChangeProperty` sync pattern |

## Quick Three-Piece Rule

To make a setting field reach the repo's `Config/Default*.ini`:

1. **Field**: `UPROPERTY(EditAnywhere, Config, Category = "Foo")`
2. **Host class**: `UCLASS(Config = Editor, DefaultConfig)` (or `Config = Game` / engine / custom category)
3. **Write code**: `Object->TryUpdateDefaultConfigFile()`, never `Object->SaveConfig()` (no-arg)

If any one of these is missing → field will not persist into version-controlled ini.

## Related

- `guidelines/ue/localization-pitfalls.md` Trap 4 — `ULocalizationTargetSet::TargetObjects` is not `UPROPERTY(config)`; needs the nested-UObject-collection workaround pattern. Engine-internal example of this skill's "TArray-of-UObject*" section.
- `guidelines/ue/asset-definition-can-duplicate-limit.md` — handling DA UPROPERTY values during copy, complementary to `AssetRegistrySearchable` (rename/move follow, but Copy+Paste does not — see CanDuplicate / PostDuplicate)
- `guidelines/code/validation.md` — verifying a setting change actually persists (don't trust "code looks correct" — verify by reading the ini file after action)
