---
id: 2026-08-two-people-each-did-half-the-compile-gate
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 第三方复核
tags: [交付文档代码块, 先编译, 造红]
pages: [guidelines/code/generating-code-through-shell.md]
---

**现象**：一份十节文档里 8 个 ```python 代码块，交付前要「逐块 compile 一遍，且先造红」。两人各做了这条纪律的不同一半：一个编了全部块但没造红，一个造了红但只编过两块。

**真因**：补做别人提的纪律时，人补的是自己没做的那半，而不是那条纪律的全部，因为读到它时自己做过的那半已经产生「这条我做了」的感觉。

**代价**：门没有被完整验证过，读者复制粘贴撞 SyntaxError 的风险仍在。

**怎么被发现的**：双方对账。
