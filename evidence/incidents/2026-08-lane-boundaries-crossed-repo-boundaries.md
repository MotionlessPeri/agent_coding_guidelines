---
id: 2026-08-lane-boundaries-crossed-repo-boundaries
date: 2026-08
kind: 命中
model: unknown
project: mocap-pipeline
caught_by: 事后复盘
tags: [lane拓扑, 按仓切]
pages: [guidelines/collaboration/lane-topology-design.md]
---

**现象**：8 条 lane 按「技术子域 + 职能」混切（render、ui 按子域，arch、review、hotfix 按职能）。代码持续下沉进共享库后，「render 域」的文件一半住在别人的仓里，owner 与仓错位，一次改动的 push 到版本钉定链要穿过两三条 lane。

**真因**：lane 边界没有跟仓库边界对齐。出仓期 626 刀里 13 刀跨 lane 边界，其中 11 刀是搬迁形态，边界本身在制造协调。

**代价**：跨界协调成为日常，重划拓扑成了必要动作。

**怎么被发现的**：按刀统计跨界比例。修法：每个独立仓一条 lane，拥有整仓加对外口。
