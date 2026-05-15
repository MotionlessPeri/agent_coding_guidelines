---
name: ue-settings-persistence
description: Hidden contracts for persisting UE settings to the project repo's `Config/Default*.ini` (not user-level Saved Config). Covers (1) the three required pieces — `UPROPERTY(config)` flag + `UCLASS(Config = <Category>, DefaultConfig)` + writing via `Object->TryUpdateDefaultConfigFile()` instead of `SaveConfig()` no-arg, (2) why `SaveConfig()` no-arg silently writes to user-level `Saved/Config/.../Game.ini` and the field appears to persist but doesn't enter git/P4, (3) `AssetRegistrySearchable` UPROPERTY meta for per-instance asset tags that auto-follow rename/move, (4) nested UObject collection workaround (TArray of UObject* with config fields requires a flat mirror + PostEditChangeProperty sync — same pattern UE engine uses for `ULocalizationSettings::GameTargetSet ↔ GameTargetsSettings`), (5) symptom-to-trap diagnostic checklist. Use when adding/modifying Project Settings, UDeveloperSettings, custom Config UObjects, or persisting per-asset metadata.
when_to_use: Fires when (1) adding or modifying a Project Settings page / `UDeveloperSettings` subclass / any custom Config UObject, (2) calling `SaveConfig()` in code (audit which file it writes to), (3) persisting per-asset metadata (consider `AssetRegistrySearchable` over a mirror table), (4) discovering "setting changed in Editor but disappears after restart" / "Dev A's setting not visible to Dev B / CI" symptoms, (5) designing a TArray/TMap of UObject* setting where each element has its own config fields. Skip for trivial `UPROPERTY()` edits that don't touch persistence semantics.
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
