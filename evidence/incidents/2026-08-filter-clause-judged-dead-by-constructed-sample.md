---
id: 2026-08-filter-clause-judged-dead-by-constructed-sample
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 实验
tags: [测量四问, 样本, A/B]
pages: [techniques/measurement-four-questions.md]
---

**现象**：判一条过滤子句是不是死代码，用构造样本推理，结论「死代码」。

**真因**：真数据 A/B（带 / 不带各跑一次）显示它挡掉了 4 条。构造样本给出了反向结论。

**代价**：差一步删掉一条在起作用的过滤。修法：判「这一步有没有起作用」跑 A/B，不推理；关不掉才退回构造样本，且标注要写「未验，且构造样本在此类问题上曾给出反向结论」。

**怎么被发现的**：A/B。
