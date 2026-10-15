---
id: 2026-07-pure-function-gate-with-gl-smoke-only
date: 2026-07
kind: 生效
model: unknown
project: retarget-study
caught_by: 自查
tags: [GUI验证, 纯函数gate]
pages: [guidelines/code/gui-visual-machine-gating.md]
---

**现象**：一个 PySide6 加 pyqtgraph.opengl 视口的 GUI 测试工具，消费一个 pybind 的 C++ 重定向库。每个功能切成纯函数加渲染层：pose 到 GL 绘制数组、播放状态机、骨骼树模型、characterize 与映射的数据格式转换、rig 配置存载，全部无 QApplication 可单测。

**真因**：纯函数层用独立 oracle 机器 gate：跟旧的 matplotlib 版本做几何交叉校验、存载 round-trip、真实数据逐位确定性、mutation 变红。`GLViewWidget` 只做「构建加 grabFramebuffer 非空」冒烟。

**代价**：无。全程 80 多个 pytest 全绿，画面交人工 `--view` 眼校，agent 读渲出的 PNG 自检一次作 sanity。这条记的是这套切法在一个项目里跑通的证据，不是失败。

**怎么被发现的**：项目收尾自查。
