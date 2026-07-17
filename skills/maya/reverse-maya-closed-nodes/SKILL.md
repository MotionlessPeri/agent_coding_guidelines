---
name: reverse-maya-closed-nodes
description: Use when an agent must behaviorally clone or diagnose a closed-source Maya node or plugin with Ghidra, assembly, shipped kernels, WinDbg, runtime probes, or a differential oracle; when decompiler output disagrees with Maya behavior; or when one synthetic fixture appears to prove parity. Skip when authoritative source code is available or only documented Maya API usage is needed.
---

# 逆向 Maya 闭源节点

## Overview

把闭源节点当成**可观测系统**，不要把反编译伪代码当成源码。任何实现结论都要沿
“静态证据 → 汇编裁决 → 隔离探针 → 差分 oracle → 真实资产”闭环；后一级可以否决前一级。

配套隐藏契约：

- [`../../../guidelines/maya/mesh-topology-fidelity.md`](../../../guidelines/maya/mesh-topology-fidelity.md)
- [`../../../guidelines/maya/gpu-deformer-gui-validation.md`](../../../guidelines/maya/gpu-deformer-gui-validation.md)
- [`../../../guidelines/cpp/windows-native-crash-hang-evidence.md`](../../../guidelines/cpp/windows-native-crash-hang-evidence.md)

## Ghidra headless 驱动 + 脚本(agent 可执行的关键)

把 Ghidra 从「交互 GUI」用成「批处理文本生成器」——这是本工作流能被 agent 驱动的前提:反编译 / vtable / xref
全部导成带元数据头的**文本文件**,agent 用 Read + grep 消费,不点任何 GUI 窗口。

**前置**:RE 是最后手段。先走 [`ue-reference-engine-source`](../../ue/ue-reference-engine-source/SKILL.md) 的对称面,
确认没有源码 / 官方 reference 可依。

**Step 0 —— dumpbin 定位「有符号的底层 DLL」**。算法通常不在节点插件里,而在底层几何 / 数学库 DLL。扫导出表按词根找,
再确认有 mangled C++ 名(`?xxx@Class@@...`)才值得逆:

```bat
for %f in ("C:\Program Files\Autodesk\Maya2024\bin\*.dll") do @dumpbin /EXPORTS "%f" 2>nul | findstr /i "<keyword>" >nul && echo %f
```

**headless 调用模板**(导入一次 → 之后 `-process` 复用已分析 program,重活只做一次):

```powershell
# JDK 21(Temurin/Adoptium);Ghidra 起不来八成是 JDK 版本不对
$env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-21...'; $env:Path="$env:JAVA_HOME\bin;$env:Path"
# 首次:导入 + 分析(慢,几分钟,别以为卡死)
& '<ghidra>\support\analyzeHeadless.bat' '<projDir>' '<projName>' -import '<target.dll>'
# 之后:复用已分析 program 反复跑脚本(秒级)
& '<ghidra>\support\analyzeHeadless.bat' '<projDir>' '<projName>' `
    -process '<target.dll>' -noanalysis `
    -scriptPath '<此 skill>/ghidra_scripts' `
    -postScript ExportByKeywords.java '<outDir>' 'baryCoord,influence,smooth'
```

地址跨工具统一记 `module + RVA`(防 ASLR);`.rep`/`.gpr` 工程留着复用。

**bundled 脚本**(`ghidra_scripts/`,换关键词即可复用到任何带符号 native DLL):

| 脚本 | 参数 | 作用 |
|---|---|---|
| `ExportByKeywords.java` | `<outDir> <kw1,kw2,...>` | 关键词宽召回(函数/符号/字符串三路)+ **一层调用邻域** → `decompiled/NNN_<addr>_<name>.c` + `target_index.txt`。宽召回→逐个消费 = [`enumerate-then-adjudicate`](../../../techniques/enumerate-then-adjudicate.md) |
| `ExportFunctionsByAddress.java` | `<outDir> <addr>...` | 按入口地址精确导反编译(带 `// address/name/prototype` 头) |
| `DumpVtables.java` | `<outFile> <kw1,kw2,...>` | MSVC `vftable` 每槽函数指针(恢复虚表/类结构) |
| `ExportXrefs.java` | `<outFile> <kw1,kw2,...>` | 关键字符串/符号的引用点 + 所在函数(定位无导出符号的内部实现) |
| `DumpInstructions.java` | `<outFile> <start> <end>` | 地址区间反汇编(对付 §3「C 反编译漏参数」时下探 ASM) |

**agent 消费**:先 Read `target_index.txt` 挑目标 → 按地址 `ExportFunctionsByAddress` 定点取 → Read `.c` 文件
grep 关键词、顺调用邻域滑进无符号内部函数。反编译不是终点,真相由 §6 差分 oracle 裁决。

## 证据等级

| 等级 | 可支持的结论 |
|---|---|
| shipped kernel、导出符号、RTTI、原始常量字节 | 数据布局、分支存在、机械公式 |
| 调用点汇编与 ABI 寄存器/栈 | 参数、类型宽度、调用顺序；可纠正反编译器 |
| Ghidra 伪代码与调用图 | 生成假设、定位函数；不能单独定案 |
| 单变量 Maya probe | 属性语义、常量、顺序和边界行为 |
| 合成差分 oracle | 局部公式在已覆盖维度上一致 |
| 多拓扑真实资产、多 pose | 可交付范围内的行为一致 |

为每条 finding 标记 `confirmed`、`strong inference` 或 `open`，并记录模块、版本、VA/RVA、调用方、
静态证据、运行时证据和反例。不得用语气替代证据等级。

## Workflow

### 1. 先定义可否证问题

一次只问一个问题，例如“第四参数是不是权重”“平滑使用 driver 还是 target 邻接”“归一化发生在平滑前还是后”。
先写出至少两个会产生不同数值输出的候选解释，再设计 probe；不能区分候选的 probe 没有证据价值。

### 2. 建静态地图，不急着翻译算法

收集目标 Maya 版本、模块基址、相关 DLL、官方 kernel、字符串、RTTI、vtable 和属性构造代码。保存原始反编译与汇编，
另写 findings；不要直接改写原始证据。跨工具地址统一记成 `module + RVA`，避免 ASLR 混淆。

### 3. 对反编译器做对抗式检查

遇到下列任一情况必须回汇编：

- 参数数量与调用方数据流不一致；
- Ghidra 恢复出不可信模板名、结构体或指针类型；
- 浮点值在伪代码中“计算后消失”；
- 矩阵顺序、行列向量或 float/double 会改变结果；
- 常量阈值附近出现支持集合差异。

按平台 ABI 检查整数与浮点寄存器、栈参数和返回值。反编译器输出是可编辑假设，不是权威文本。

### 4. 用单变量 probe 反演行为

固定其余属性，只改变一个输入；优先选择能从输出反解内部量的几何，例如纯法向 offset 反解法线、线性 ramp 反解距离。
同时导出输入、输出、节点设置、Maya 版本和实际 triangulation，让 probe 可脱 Maya 复算。

每个 probe 必须有**激发守卫**：driver/输入确实变化、目标输出非预期恒等、活跃点数量非零。没有激发目标行为时，
“误差为零”“零折叠”“没有 crash”都不能算通过。

### 5. 建正交覆盖矩阵

至少覆盖：

| 维度 | 代表测试 |
|---|---|
| frame | 法向 offset、显著切向 offset、刚体旋转 |
| 权重 | 满权重、过渡带、零权重、阈值两侧 |
| 拓扑 | triangle、非共面 quad、n-gon、边界、退化点 |
| 平滑 | 0/1/多轮、非等长边、Jacobi 与原地更新区分 |
| 资产 | 合成小网格 + 真实网格、多 pose |

一个规则圆柱或平面只能证明它覆盖到的局部公式，不能外推“节点已复刻”。

### 6. 实现与 oracle 同步收敛

先在脱 Maya core 中实现候选数学，再用同一 fixture 做逐元素比较；通过后接 Maya CPU，最后接 GPU。每一层复用同一 binding
和数据布局，避免 CPU/GPU 各自解释逆向结果。记录最大误差、均值、支持集合 FP/FN、形变幅度和退化指标。

只有满足以下条件才可把 finding 标为完成：

- 静态证据与运行时 probe 不冲突；
- oracle 验证了目标行为确实被激发；
- 正交合成覆盖通过；
- 至少一个代表性真实资产、多 pose 通过；
- 文档明确尚未覆盖的模式、拓扑和参数。

## Example：伪代码少参数

Ghidra 显示 `insert(id, index, flag)`，但调用前还有一个 barycentric double 被计算。不要删除这个“无用值”：

1. 查看 call 前浮点寄存器，确认该值是否按 ABI 放入参数寄存器；
2. 查 callee 是否读取该寄存器或对应栈槽；
3. 构造 skew polygon，让“使用权重”和“忽略权重”产生明显不同输出；
4. 用 Maya 输出裁决，再修正函数签名和 finding 等级。

## Red Flags

- “伪代码已经很清楚，可以直接照写。”
- “这个合成 case 到 `1e-6`，应该基本完成了。”
- “零折叠/零误差，所以算法正确。”
- “polygon 顶点一样，triangulation 不会影响结果。”
- “Maya 退出了，所以插件崩了。”
- “先实现猜测，后面有偏差再补 probe。”

出现任一条就停止实现，回到缺失的证据层。

## 相关

- [`ghidra_scripts/`](ghidra_scripts/) —— bundled headless post-scripts(换关键词复用;含 README)
- [`../../../techniques/enumerate-then-adjudicate.md`](../../../techniques/enumerate-then-adjudicate.md) —— 关键词宽召回 + 调用邻域 = 机械枚举候选再逐个裁决
- [`../../../techniques/adversarial-verification.md`](../../../techniques/adversarial-verification.md) —— 差分 oracle / round-trip 是「选可信 check」的落地
- [`../../ue/ue-reference-engine-source/SKILL.md`](../../ue/ue-reference-engine-source/SKILL.md) —— 对称 prep:动手逆向前先找有没有 reference 实现
- [`../../../guidelines/cpp/multi-dll-plugin.md`](../../../guidelines/cpp/multi-dll-plugin.md) —— dumpbin 查导出 / 符号的底座
