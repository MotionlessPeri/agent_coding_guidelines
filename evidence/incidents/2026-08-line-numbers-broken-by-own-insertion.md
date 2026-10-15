---
id: 2026-08-line-numbers-broken-by-own-insertion
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 自查
tags: [前提, 移动引用, 行号]
pages: [guidelines/code/premises-not-in-the-text.md]
---

**现象**：为消歧在文档里插入了一节 14 行，节内用行号引用文中别处。

**真因**：插入文本的动作自己把下方行号推走了，六个行号引用当场全错，其中一个最后指向它自己那一行。一个指针可以在写下它的那一次编辑里就失效。

**代价**：引用全部错位，而文字读起来完全正确。修法是换掉指针（就地写名字或符号），不是重算行号，重算后下次有人插入照样全错。

**怎么被发现的**：写完回读。
