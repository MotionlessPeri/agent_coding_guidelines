---
id: 2026-10-maya-gui-test-trust-prompt-every-run
date: 2026-10
kind: 命中
model: claude-opus-5-5
project: Maya C++ 插件项目
caught_by: 用户
tags: [maya, gui-test, trust-center]
pages: [guidelines/maya/gui-test-plugin-trust.md]
---

**现象**：agent 在交互 Maya 2024 里验证插件改动，连跑四轮，每轮加载 `.mll` 都弹「Untrusted Plugin Loading」，要用户手动点 Allow；agent 当时把 Maya 启动慢归为网络。

**真因**：agent 每轮新建一份 `MAYA_APP_DIR`，插件又直接从不同的编译目录加载；信任中心按「偏好目录里的允许列表 + 插件所在目录」记同意，所以每轮都是没见过的位置。

**代价**：用户每轮被打断一次去点确认；agent 的超时看门狗还在用户点完之前杀掉过一轮 Maya，那轮的偏好没写盘。

**怎么被发现的**：用户在问答里指出「每次都要我手动同意 mll」，并说另一个项目的 lane 也这样（那边的细节未核）。agent 随后复现了弹窗、确认关窗等于拒绝，2026-10-21 记录。
