---
id: 2026-08-mobu-samples-had-the-exact-device-example
date: 2026-08
kind: 命中
model: unknown
project: mobu-plugin
caught_by: 自查
tags: [复用, 框架侧reference-impl, 随装samples]
pages: [guidelines/code/reuse-before-implementing.md]
---

**现象**：一个「设备插件怎么写、跨版本有无差异」的问题，本来要靠旧版本经验加网络搜索推测。

**真因**：`ls` 一下宿主安装目录，2023 SDK 的 samples 里就有正好对应那个场景的完整官方实现，答案从「我推测」变成「官方样例就是配方」，顺带在头文件注释里核销了四项 API 事实。这个机制此前只在 UE 域被写下，Maya、MotionBuilder 的 agent 不会想到去查。

**代价**：差一步做一整轮跨版本推测。

**怎么被发现的**：一次 `ls`。同一台机器核销的随装情况：MotionBuilder 2018 / 2019 / 2022 / 2023 全部随装 `OpenRealitySDK/Samples/`；Maya 2022 / 2024 / 2025 随装 `devkit/`；3ds Max 2024 顶层无 maxsdk，SDK 是可选安装组件。所以「随装」不是普适前提，这条是「先查一下」，不是「假定有」。机器档案脚本现在会直接列出每台机器的这些目录。
