---
id: 2026-08-hotfix-lane-premise-silently-gone
date: 2026-08
kind: 命中
model: unknown
project: mocap-pipeline
caught_by: 事后复盘
tags: [lane拓扑, 存在前提]
pages: [guidelines/collaboration/lane-topology-design.md]
---

**现象**：hotfix 独立 lane 一直在，值守流量很低。

**真因**：它的存在前提是「生产分支需要隔离树」，分支模型一变前提归零，lane 却还在。「流量低」不能作裁撤论据，那是结构性下界，忙闲读不出存在前提；真论据是隔离前提已不存在。

**代价**：一个前提消失后仍在吃 token 的会话。

**怎么被发现的**：重划时逐条问「它的存在前提还在吗」。
