---
name: ue-reference-engine-source
description: Use for unfamiliar, changed, or suspect UE framework contracts during implementation, review, or debugging. Skip non-UE work and contracts covered by valid evidence for the target version and execution path.
---

# UE Reference Engine Source

用于实现、审查或排查中不熟悉、发生变化或有疑点的 UE 框架契约。覆盖同一目标版本和调用路径的有效证据可以复用。

[`reference-engine-source.md`](reference-engine-source.md) 是本技能查证方法的主来源，包含适用范围、证据选择、参考差异与搜索无结果的处理，以及行为验证要求。

按当前问题阅读其中相关部分：

- 需要确定如何查证时，读“查证范围与已有证据”“选择证据”和“读参考实现与验证”。
- 需要定位实现时，查“按 UE 子系统分类的 reference 清单”或官方 sample 导航。
- 需要理解既有失败经验时，读对应反例与项目实例；这些案例的版本和上下文见附件。
