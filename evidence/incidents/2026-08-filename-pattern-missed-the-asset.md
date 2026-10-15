---
id: 2026-08-filename-pattern-missed-the-asset
date: 2026-08
kind: 命中
model: unknown
project: ue-retarget
caught_by: 第三方复核
tags: [rule-3, 可达范围]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：按 `*rig*` / `*ik_*` 文件名模式扫一个目录，报「这个资产没有配套的 X」。

**真因**：它叫 `PA_<名>`，住在另一个目录。文件名模式和目录范围两条都躲开了。

**代价**：差一步建出重复资产。

**怎么被发现的**：第三方复核。
