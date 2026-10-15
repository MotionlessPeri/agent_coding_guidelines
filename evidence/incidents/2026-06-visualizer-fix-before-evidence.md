---
id: 2026-06-visualizer-fix-before-evidence
date: 2026-06
kind: 命中
model: unknown
project: ue-curvenet
caught_by: 用户
tags: [盲改, 取证]
pages: [guidelines/code/diagnose-before-fixing.md]
---

**现象**：视口控制点手柄不显示。agent 第一反应是「八成是 `GUnrealEd` 在 `StartupModule` 时为 null 导致 component visualizer 没注册」，准备直接改成 `OnPostEngineInit` 延迟注册。

**真因**：当时不知道。那个假设只是注册、调用、数据、绘制四个候选环节之一。

**代价**：差一步对未证实的假设盲改。

**怎么被发现的**：用户叫停，要求先加日志取证：`StartupModule` 时 `GUnrealEd` 是否有效、注册是否跑、`DrawVisualization` 是否被调、控制点数，确认卡在哪一环再修。日期按文件首次写下的时间填，实际发生可能更早。
