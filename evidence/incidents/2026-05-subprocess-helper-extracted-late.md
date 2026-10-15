---
id: 2026-05-subprocess-helper-extracted-late
date: 2026-05
kind: 命中
model: unknown
project: ue-dialogue-system
caught_by: 用户
tags: [复用, 重复堆叠]
pages: [guidelines/code/reuse-before-implementing.md]
---

**现象**：660 行的 subprocess 逻辑（路径校验、CreateProc、30 s 超时、exit code、MessageLog）在 `ParseXlsxBatch` 里内联了好几个月，到要写第二、第三个 subprocess caller 时才由用户指出可以抽 helper。

**真因**：复用依据是共同的进程执行与错误处理契约（超时、输出、错误处理要一起改），不是「第二个调用方出现就必须抽象」；但发现第二处相似实现时没有做这个判断。

**代价**：抽出 `PythonSubprocessHelper::RunPythonImportSubprocess` 之前，subprocess 超时行为要改就得改多处且容易漏。同项目 3 个月里其他几次「发现已有相似再动手」的复用：RAII guard 统一 5 处 DB 查询的关闭时机、一个批量选择 modal 被第二种导入复用、两个资产编辑器抽出共用基类、目录选择控件换成已有的 ComboButton 加 PathPicker 模式、两处「按行填拓扑」抽成模板 helper。

**怎么被发现的**：用户指出。
