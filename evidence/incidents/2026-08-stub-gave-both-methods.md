---
id: 2026-08-stub-gave-both-methods
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 第三方复核
tags: [测量四问, 样本, 构造样本盲区]
pages: [techniques/measurement-four-questions.md]
---

**现象**：做降级实验的 stub 把一组两个方法都给全了，于是「只给一半会怎样」这一格从未进样本。

**真因**：按「合理用法」构造的样本，系统性避开「不合理用法」那一格。造 stub 或最小宿主时人按「能用」来造，能用的宿主天然不缺必需件；而文档和接口的真实读者恰恰会走到那格。

**代价**：「只给一半时接线会抛异常」这一档直到第三方读守卫结构才暴露。实验没做错，是样本的构造方式避开了它。

**怎么被发现的**：第三方读守卫结构。
