---
id: 2026-08-forked-bridge-mistaken-for-stock
date: 2026-08
kind: 命中
model: unknown
project: mobu-plugin
caught_by: 第三方复核
tags: [rule-1, 反方向]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：报「旧插件用自定义属性把时码流到下游，这个做法可用，记为 deferred 以后接」。

**真因**：归错方向反了。能跑是因为环境里那份桥接插件是被内部改过的，原版流不了自定义属性，而新管线用原版。把自己这层（fork）的扩展说成了下层框架的能力。

**代价**：一次更正往返，差一点留下一个 deferred 项和一个 stub 接口，两者都编码着「这条路通、只是还没接」，而这条路是被否证的。

**怎么被发现的**：第三方复核。
