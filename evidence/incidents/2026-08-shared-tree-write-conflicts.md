---
id: 2026-08-shared-tree-write-conflicts
date: 2026-08
kind: 命中
model: unknown
project: mocap-pipeline
caught_by: 事后复盘
tags: [lane拓扑, 共享树, 实现权分散]
pages: [guidelines/collaboration/lane-topology-design.md]
---

**现象**：多条 lane 同时写一个仓。三起事故：共享 git 索引互吞，索引差 3 秒吞掉 4 个文件；一条「只改 docstring」的 commit 带走了别人的重构；全量读数被别人的中途态污染，207 个假红。

**真因**：实现权分散，共享树的写冲突面大。

**代价**：三起各自独立的事故。修法：一个仓的全部实现收进一条 lane，同仓并发写从常态变成例外；写冲突纪律仍要，但从「每天的事」降为「边缘情况」。

**怎么被发现的**：事故发生后逐起归因。
