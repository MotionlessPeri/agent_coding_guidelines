# UE 渲染管线知识库

面向 UE 渲染底层技术支持的参考资料——渲染管线定制与引擎项目底层优化两个方向。

> **覆盖版本**：UE 5.8（源码基准 `H:/Epic Games/UE_5.8`，5.8.0 / CL 55116800）
> **验证状态**：见每份文档开头的验证状态段。**引用前请按文档里给出的源码路径复核**——本库
> 部分内容来自自动化调研，已发现并修正过多处不存在的 API 名、CVar 名和文件路径。
> 校验工具：`scripts/verify-ue-rendering-refs.py`（机械核对全部路径与 CVar 断言是否真的存在于引擎源码）

## 文件列表

| 文件 | 规模 | 内容 |
|---|---|---|
| [card-09-scenario-mapping.md](card-09-scenario-mapping.md) | 159 行 | **问题路由表（入口）**：客户原话 → 第一步查什么 → 去哪份文档；需求分类与优先级；三条高频排查路径 |
| [card-12-pipeline-extension.md](card-12-pipeline-extension.md) | 242 行 | **管线定制扩展点**：改引擎 / `ISceneViewExtension` / 后处理材质三条路的决策；21 个 hook 点全表；`EPostProcessingPass` 与 `EBlendableLocation` 的对应 |
| [card-13-verify-locally.md](card-13-verify-locally.md) | 200 行 | **本机核证方法**：路径 / CVar / 符号三类断言各怎么核；从 CVar 反查生效路径；从 Pass 名反查注册点；跨版本怎么回答；校验方法自身的盲区 |
| [card-01-pipeline-overview.md](card-01-pipeline-overview.md) | 549 行 | **渲染管线架构**：三级流水线、`FSceneRenderer` 流程、Deferred / Mobile 分支、各 Pass 顺序、Lumen 与 Nanite 的插入点 |
| [card-08-rdg.md](card-08-rdg.md) | 1548 行 | **RDG**：`FRDGBuilder` API、资源声明、Pass 类型、Transient 与别名、Barrier、裁剪执行、自定义 Pass 注入与 Hook 点、RDG 调试、5.8 新增特性 |
| [card-05-rhi.md](card-05-rhi.md) | 547 行 | **RHI 层**：抽象层结构、资源管理、GPU 同步、命令列表、各平台 RHI 差异 |
| [card-04-performance.md](card-04-performance.md) | 794 行 | **性能优化**：分析工具链、瓶颈定位方法、优化策略、CVar 速查 |
| [card-03-debugging.md](card-03-debugging.md) | 504 行 | **调试诊断**：CVar / ShowFlag / viewmode 三种机制的区别、帧捕获、GPU 崩溃取证、平台 validation、Shader 调试、外部工具、诊断决策树 |
| [card-06-shader-material.md](card-06-shader-material.md) | 511 行 | **Shader 与材质**：材质系统链条、Shader 编译管线、Permutation 裁剪、Substrate |
| [card-00-nanite.md](card-00-nanite.md) | 693 行 | **Nanite**：Cluster / Page / Group 层级、Visibility Buffer、流式加载、显存管理、定制扩展、已知限制 |
| [card-02-lumen.md](card-02-lumen.md) | 509 行 | **Lumen**：三种追踪模式、反射、Surface Cache、性能调优与降级路径 |
| [card-07-platform-adaptation.md](card-07-platform-adaptation.md) | 506 行 | **平台适配**：Feature Level 系统、移动端 / 桌面 / 主机差异、VR、渲染管线裁剪 |
| [card-10-knowledge-map.md](card-10-knowledge-map.md) | 599 行 | **知识地图**：结构化知识树、源码索引（符号列自动抽取）、CVar 速查表、学习路径 |
| [card-11-final-report.md](card-11-final-report.md) | 1517 行 | **总览**：执行摘要、管线全景图、学习路线、源码导航、自我评估 |

## 怎么用

```mermaid
flowchart TD
    Start["手上有什么"] --> Q1{"是具体问题<br/>还是要系统学？"}

    Q1 -->|"客户报了具体问题"| S1["card-09 场景映射<br/>找到对应场景"]
    S1 --> S2{"问题类型"}
    S2 -->|"帧率 / 卡顿"| P1["card-04 性能优化"]
    S2 -->|"画面不对 / 崩溃"| P2["card-03 调试诊断"]
    S2 -->|"某平台不达标"| P3["card-07 平台适配"]
    S2 -->|"要加自定义效果"| P4["card-12 管线定制扩展点"]
    P4 --> P5["card-08 RDG 写 Pass"]

    Q1 -->|"要系统建立认知"| L1["card-01 管线架构"]
    L1 --> L2["card-08 RDG"]
    L2 --> L3["card-05 RHI"]
    L3 --> L4["card-04 性能优化"]
    L4 --> L5["card-06 Shader / card-00 Nanite<br/>card-02 Lumen / card-07 平台"]

    Q1 -->|"要查一个符号 / CVar"| F1["card-10 知识地图<br/>源码索引 + CVar 速查"]
    F1 --> F2["card-13 本机核证<br/>确认它在客户版本存不存在"]

    classDef entry fill:#e3f2fd,stroke:#1565c0,color:#000
    classDef doc fill:#fff3e0,stroke:#e65100,color:#000
    class Start,Q1,S2 entry
    class S1,P1,P2,P3,P4,P5,L1,L2,L3,L4,L5,F1,F2 doc
```

## 引用纪律

这批内容不是引擎官方文档，**不要当权威直接答客户**。里面每条 API 名、CVar 名、源码路径都可能是
调研阶段生成的似真内容。已知的失败模式：编造出读起来完全合理的文件名（`NaniteRendering.cpp`）、
<!-- verify:ignore-start -->
不存在的 CVar 家族（`r.RDG.Debug.VerifyBarriers`）、以及不成立的版本变更说法。
<!-- verify:ignore-end -->

所以：

1. 要引用某条结论前，按文档给的路径去 `H:/Epic Games/UE_5.8/Engine/Source` 打开确认
2. 批量核对用 `python scripts/verify-ue-rendering-refs.py`——路径 / CVar / 符号三类断言逐条对着引擎源码判定；
   单条查名字和反查生效路径的方法见 [card-13-verify-locally.md](card-13-verify-locally.md)
3. 客户在别的版本上时，先确认该结论在那个版本成立，本库只以 5.8 为基准

这份库的价值在于**知识结构和排查路线**——哪些子系统、按什么顺序看、可能卡在哪一环。
具体符号请以源码为准。
