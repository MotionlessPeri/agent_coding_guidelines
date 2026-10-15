---
id: 2026-08-rotation-order-declared-never-read
date: 2026-08
kind: 命中
model: unknown
project: retarget-study
caught_by: 自查
tags: [复用, 错误实现无害潜伏, 全链一致地错]
pages: [guidelines/code/reuse-before-implementing.md]
---

**现象**：配置文件声明了旋转序，解析进字段后再无任何读取点，全链走框架默认序。

**真因**：两侧一致所以姿势正确。错误实现原地无害的第二种形态：全链一致地错。危害在被继承那一刻产生：新实现照抄它以为它对，或只抄一半打破了那个一致。

**代价**：同一仓库里和「矩阵平方」是两个机制不同的实例，不是同一个坑踩两遍。

**怎么被发现的**：grep 字段名，发现解析之后没有读取点。
