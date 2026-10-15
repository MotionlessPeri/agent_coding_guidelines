---
id: 2026-08-seam-numbers-in-brief-anchored-all-lanes
date: 2026-08
kind: 命中
model: unknown
project: mocap-pipeline
caught_by: 事后复盘
tags: [lane拓扑, brief锚定, 独立复核]
pages: [guidelines/collaboration/lane-topology-design.md]
---

**现象**：接缝表里的数字进了派单 brief，所有 lane 都读到了同一个数。

**真因**：人人必读的表会锚定所有 lane，之后换手复核那个数在结构上不可得，没有谁是独立的。

**代价**：那个数失去了独立复核的可能。修法：想保留独立复核能力的数，别写进人人必读的表。

**怎么被发现的**：想安排换手复核时发现无人未读过。
