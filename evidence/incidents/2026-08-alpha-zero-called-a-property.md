---
id: 2026-08-alpha-zero-called-a-property
date: 2026-08
kind: 命中
model: unknown
project: retarget-study
caught_by: 外部追问
tags: [rule-4, 数字的机制]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：一个参数 `alpha=0` 时「行为在两种坐标约定下相反」被写成该参数的性质。

**真因**：那个参数是对整个向量做一次 `Lerp`，三个分量一视同仁，结构上不可能按轴表现相反。那两个数里有一个是在坏构型下测的，它反映的是「整条管线喂了错数据」，不是参数的性质。一行 `Lerp` 对一下就知道。

**代价**：一次观察被写成了性质。数字比文字更像证据，所以「该查机制吗」这一问没有被触发。

**怎么被发现的**：对方追问机制。
