---
id: 2026-08-wrong-matrix-overwritten-each-frame
date: 2026-08
kind: 命中
model: unknown
project: retarget-study
caught_by: 自查
tags: [复用, 错误实现无害潜伏, 输出被覆盖]
pages: [guidelines/code/reuse-before-implementing.md]
---

**现象**：一个「局部转全局」的矩阵函数把入参在函数内覆盖后自乘，算出的是父变换的平方，骨骼自身的成员从未参与。它有注释、命名合理、被真实调用，功能也在跑。

**真因**：结果在首帧被整块缓冲覆盖，所以对最终画面零影响，静静活了整个项目周期。错误实现原地无害的第一种形态：输出被覆盖。

**代价**：若不追到覆盖链条，会把一个错误实现当作参考实现递给下游，而下游没有源码上下文，无法自行发现。

**怎么被发现的**：追「谁读它的输出、读之前发生了什么」。
