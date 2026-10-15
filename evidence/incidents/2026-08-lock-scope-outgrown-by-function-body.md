---
id: 2026-08-lock-scope-outgrown-by-function-body
date: 2026-08
kind: 命中
model: unknown
project: mobu-plugin
caught_by: 自查
tags: [复用, 隐含假设随演化失效]
pages: [guidelines/code/reuse-before-implementing.md]
---

**现象**：一个只做数据搬运时合理的「整函数加锁，在实时回调里调用」，后来被塞进了重计算。

**真因**：锁的范围和函数的调用位置隐含着对函数体大小的假设；函数体随演化增长时这个假设静默失效，而代码形态上看不出异常，锁还是那一行，调用点还是那一处。

**代价**：实时回调被重计算拖住。

**怎么被发现的**：复盘函数演化史。
