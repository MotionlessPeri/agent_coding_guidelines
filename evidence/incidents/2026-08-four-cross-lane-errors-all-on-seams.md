---
id: 2026-08-four-cross-lane-errors-all-on-seams
date: 2026-08
kind: 命中
model: unknown
project: mocap-pipeline
caught_by: 事后复盘
tags: [lane拓扑, 接缝]
pages: [guidelines/collaboration/lane-topology-design.md]
---

**现象**：一周内四次 lane 互抓错，全部发生在两条 lane 都会碰的契约面上：共享容器、双向信号、同名异义函数。`set_undo_stack` 同名两义还被归错过一次对象。

**真因**：缝无主。两边都以为对方管，没有人认领那个契约面。

**代价**：四轮往返，一次归错对象。修法：接缝登记成表，每条写缝、owner、协调规则；触发挂 git 可观察事件，不挂人。

**怎么被发现的**：复盘时把一周的互抓错按位置归类。
