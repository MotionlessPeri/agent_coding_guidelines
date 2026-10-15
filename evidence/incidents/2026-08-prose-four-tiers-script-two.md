---
id: 2026-08-prose-four-tiers-script-two
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 第三方复核
tags: [交付文档代码块, 正文与工具漂移]
pages: [guidelines/code/generating-code-through-shell.md]
---

**现象**：文档正文讲了四档行为，文中附带的自检脚本只实现了两档。

**真因**：正文与文中工具会漂移。读者信工具多过正文：工具给结论，正文要读。于是工具报假绿。

**代价**：读者按脚本自检通过，而正文定义的另外两档没有被检查。

**怎么被发现的**：第三方对照正文与脚本。修法：改正文时问一句「下面那个脚本实现了吗」。
