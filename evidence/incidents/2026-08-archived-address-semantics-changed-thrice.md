---
id: 2026-08-archived-address-semantics-changed-thrice
date: 2026-08
kind: 命中
model: unknown
project: mocap-pipeline
caught_by: 事后复盘
tags: [lane拓扑, 重划执行, 平台语义]
pages: [guidelines/collaboration/lane-topology-design.md]
---

**现象**：「归档后的 lane 地址能否复用」在一周内收到三封互相推翻的更正。

**真因**：这是平台语义，随 lane-router 版本变。写进项目文档时如果当永恒事实写，下一个版本就错。

**代价**：三轮更正。修法：这类事实带日期与出处写，并区分「换角色」（原地重 attach，对话保留）和「退役」（终态，对话回不来）。

**怎么被发现的**：三封更正本身。
