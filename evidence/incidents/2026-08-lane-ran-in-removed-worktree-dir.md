---
id: 2026-08-lane-ran-in-removed-worktree-dir
date: 2026-08
kind: 命中
model: unknown
project: mocap-pipeline
caught_by: 第三方复核
tags: [lane拓扑, 重划执行, cwd]
pages: [guidelines/collaboration/lane-topology-design.md]
---

**现象**：一条 lane 长期跑在一个已拆掉的 worktree 残留目录里。

**真因**：git 命令在残留目录里不报错，但读数全错。新 lane 的 cwd 没有显式指定，也没有让它自证。

**代价**：那条 lane 一段时间内的全部读数不可信。修法：新 lane 的 cwd 显式指定，并用 `git worktree list` 自证 cwd 在清单里。

**怎么被发现的**：别的 lane 核对读数时发现。
