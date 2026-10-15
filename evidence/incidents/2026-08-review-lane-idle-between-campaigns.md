---
id: 2026-08-review-lane-idle-between-campaigns
date: 2026-08
kind: 命中
model: unknown
project: mocap-pipeline
caught_by: 事后复盘
tags: [lane拓扑, 审查campaign制]
pages: [guidelines/collaboration/lane-topology-design.md]
---

**现象**：一条常驻的 review lane，一场审计满负荷，平时零负载。

**真因**：审查是波动负载，常驻一条 lane 的成本换不来它空转期的价值。

**代价**：一个空转的独立模型会话。并入裁决 lane 后无损失，后续大审计临时开 lane、审完归档即可。

**怎么被发现的**：看负载形态。
