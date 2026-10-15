---
id: 2026-08-toolset-scan-mistaken-for-framework
date: 2026-08
kind: 命中
model: unknown
project: ue-retarget
caught_by: 第三方复核
tags: [rule-3, 可达范围]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：扫遍某个工具集找不到程序化入口，报「这个框架不支持程序化配置」。

**真因**：只扫了那个工具集。框架自己的脚本 API 里是完整的两个控制器，共 157 个成员。

**代价**：一条可行的路被报成不可行。

**怎么被发现的**：第三方复核。同一条 lane 同一天还踩了「文件名模式漏资产」和「猜的类名」两次，可达范围的边界各不相同。
