# AGENTS.md — Universal Agent Guidelines

This is the canonical instruction file for both Claude and Codex agents.

---

## Platform Loading Rules

- Claude Code treats the `@path` lines below as imports and loads their contents.
- Codex discovers this `AGENTS.md`, but does not expand Claude Code `@path` imports. Before acting, Codex must open the applicable referenced files itself: start with the relevant files under `guidelines/workflow/`, `guidelines/code/`, and `guidelines/writing/`; load framework or tool directories such as `cpp/`, `ue/`, `maya/`, `p4/`, `ci-windows/`, and `claude-code/` only when the task matches; load a `techniques/` file when its procedure applies.
- Both platforms discover installed skills lazily from their own skill directories. Do not eager-import `SKILL.md` files here.

---

## How This Repository Is Organized

Guidelines are grouped by topic under `guidelines/`:

| Directory | Contents |
|-----------|----------|
| `guidelines/workflow/` | Commit rules, documentation rules, agent lifecycle, handoff workflow |
| `guidelines/code/` | Code constraints, validation requirements |
| `guidelines/writing/` | 面向人读的散文（文档 / 代码注释 / 交付文字）通用文体规则——工作语言写散文 + 标识符保留原文 / 不说黑话 / 简洁⇔不丢信息 / 不翻译腔。跨「文档 + 注释」共享的 SoT，由 `skills/workflow/doc-writing-style`（+图示 discipline）与 `skills/workflow/conversation-walkthrough` Phase 3（+注释 stability / Doxygen 契约头）两个 skill 承接执行面 |
| `guidelines/cpp/` | C++ / Windows DLL / cmake / MSVC 工程底座的 hidden contract——跨 DLL 单例内联陷阱 / 符号导出 / native 绑定可达面 / 增量编译 ABI 不一致 / stale `.vcxproj` / 热路径 move 与 dynamic_cast / `std::make_format_args` 左值契约 / perf 测量误测未优化二进制 / 现代 C++ 标准钳制 / Windows native crash-hang dump 取证。框架无关，多 DLL 插件（含 UE `.dll` / Maya `.mll`）高频命中。**非 C++ 项目可整段 skip**。索引 + 按场景导航见 [`guidelines/cpp/INDEX.md`](guidelines/cpp/INDEX.md) |
| `guidelines/collaboration/` | Multi-agent setup, private docs policy |
| `guidelines/ci-windows/` | Windows CI (PowerShell / GitLab runner) 跑 native command 时的 pitfall 集——PowerShell ↔ native exe 之间的抽象漏洞 |
| `guidelines/claude-code/` | Claude Code 自身（harness / hooks / settings.json）的 hidden contract——文档没明说但实测如此的行为 |
| `guidelines/p4/` | Perforce 特有 hidden contracts——charset transcoding / typemap / 跟 git 不同的字节保留语义 |
| `guidelines/ue/` | Unreal Engine framework hidden contracts + idiom，meta-corpus 最重的框架子目录。两层：**14 份 broad guidelines**（常碰核心契约，**懒加载 via INDEX**、非 UE session 不常驻）+ **8 个懒加载 UE skills**（ultra-niche / 按场景触发的簇，bundle 进 `skills/ue/`：module-architecture / reference-engine-source / settings-persistence / custom-graph-editor / procedural-numerical / ml-animation / unrealmcp-usage / official-mcp-usage）。**非 UE 项目可整段 skip**。完整索引（broad + skill 双层）+ 按场景导航见 [`guidelines/ue/INDEX.md`](guidelines/ue/INDEX.md) |
| `guidelines/maya/` | Maya C++ 插件（`MPx*` plugin / manip / context / 多 `.mll` 共享 base 层）的 framework hidden contracts——靠踩坑得到、Maya 文档没明说的约束。**非 Maya 项目可整段 skip**。索引 + 配套 skill 见 [`guidelines/maya/INDEX.md`](guidelines/maya/INDEX.md) |
| `guidelines/fbx/` | Autodesk FBX SDK 隐藏契约，读 / 写两侧对称各 1 份。**写侧**（往既有 DCC rig 写动画）：PreRotation 补偿 / 旋转限位吸收（只在写既有 rig 而非从零裸骨架时出现）。**读侧**（把动画按帧采样成 pose 序列）：声明的 time mode ≠ 真实关键帧率 / 采样前必须 unroll Euler / 关键帧可能超出 take 跨度——三条都静默失败。**非 FBX 项目可整段 skip**。当前 2 份：[`write-animation-to-existing-rig.md`](guidelines/fbx/write-animation-to-existing-rig.md) / [`read-animation-from-fbx.md`](guidelines/fbx/read-animation-from-fbx.md) |
| `techniques/` | Procedural patterns and step-by-step operational guides |
| `docs/plans/` | 已确认设计的实施前记录；用于保存跨文件改造的边界、接口与验收标准 |
| `skills/` | Shared Agent Skills, organized under `skills/<category>/<name>/SKILL.md`. `scripts/sync-skills.ps1` installs them flat to Claude Code's `.claude/skills/<name>/` and Codex's `.agents/skills/<name>/` discovery directories |
| `_radar/` | **外部知识雷达暂存区**——`/research-radar` skill(`.claude/skills/research-radar/SKILL.md`,project-local + `disable-model-invocation` 纯手动)跑 deep research 产出的待审 digest 落点。是 inbox **不是** corpus：**绝不** `@`-import(会污染 always-loaded context)、**绝不**自动写进 `guidelines/`。从雷达到 corpus 是用户事后人工走 `knowledge-promotion.md` 的一步。政策见 [`_radar/README.md`](_radar/README.md) |
| `references/` | **领域参考资料**——不是 agent 行为规范，而是「做某个领域的活时要查的东西」。跟 `guidelines/`（agent 该怎么工作）正交，**绝不** `@`-import。当前只有 [`references/ue-rendering/`](references/ue-rendering/README.md)（UE 5.8 渲染知识库，14 份卡片，面向渲染底层技术支持）。**引用纪律**：这类内容混有自动化调研产物，每条源码路径 / CVar 名 / 符号名都可能是似真编造（该库起点实测：路径断言 79 条不存在、CVar 163 条、符号 70 条），所以配了机械校验（`scripts/verify-ue-rendering-refs.py` 三轴核对 + `scripts/ue-cvar-dump.py` 从源码生成可信内容 + `scripts/ue-cvar-crossversion.py` 跨版本适用性）。新增 `references/` 子目录时必须同时配好「怎么核」的手段，否则不要建 |

**Adding new files:**
- Place new files in the appropriate subdirectory.
- If no existing category fits, create a new subdirectory.
- Add a reference to the new file in this AGENTS.md under the relevant section.
- Keep each file focused on one topic. Split if it covers 3+ independent concerns or exceeds ~200-300 lines.
- `guidelines/` = declarative rules ("always do X, never do Y"). `techniques/` = procedural patterns ("step 1, step 2, step 3"). `skills/` = shared Agent Skills, triggered on demand (not eager-imported).

---

## Guidelines

@guidelines/workflow/commits.md

@guidelines/workflow/documentation.md

@guidelines/workflow/agent-lifecycle.md

@guidelines/workflow/handoffs.md

@guidelines/workflow/code-review.md

@guidelines/workflow/knowledge-promotion.md

@guidelines/workflow/daily-and-open-items.md

@guidelines/code/clarify-before-implementing.md

@guidelines/code/reuse-before-implementing.md

@guidelines/code/constraints.md

@guidelines/code/function-clarity.md

@guidelines/code/diagnose-before-fixing.md

@guidelines/code/validation.md

@guidelines/code/test-purpose.md

@guidelines/code/complexity-coverage-metrics.md

@guidelines/code/gui-visual-machine-gating.md

@guidelines/code/dual-layer-data-ownership.md

@guidelines/writing/prose-and-register.md

@guidelines/collaboration/multi-agent.md

@guidelines/collaboration/private-docs-policy.md

> UE broad guidelines（14 份）**不 eager `@`-import**——lazy-load via [`guidelines/ue/INDEX.md`](guidelines/ue/INDEX.md)（已在上方组织表链接、且 INDEX 完整覆盖全 14 份 broad + 8 个 UE skill 双层导航）。省 ~2500 行常驻——非 UE 项目 / 非 UE session 不再吃这块。接 UE 任务时读 INDEX 导航到具体文件 / 触发 ue-* skill；**重度 UE 项目可在项目自己的 `AGENTS.md` 里 `@`-import 需要的子集把它们拉回常驻**（见 `collaboration/multi-agent.md` Option 2）。Codex 本就按目录表 on-demand 打开 ue/，不受影响。（2026-07-28 context-budget audit：broad-UE 从常驻转懒加载，收尾 Tier D 最后一块 eager 域集群）

> Maya guidelines（9 份）**不 eager `@`-import**——lazy-load via [`guidelines/maya/INDEX.md`](guidelines/maya/INDEX.md)（已在上方组织表链接、且 INDEX 完整覆盖全 9 份）。非 Maya 项目省去这部分常驻内容；接 Maya 插件任务时读 INDEX 导航到具体文件 / 触发 maya skill。Codex 本就按目录表 on-demand 打开 maya/，不受影响。（2026-07-18 context-budget audit S2；2026-07-24 新增并行性能取证）

> C++ 工程底座 guidelines（8 份）**不 eager `@`-import**——lazy-load via [`guidelines/cpp/INDEX.md`](guidelines/cpp/INDEX.md)。C++ 项目（含 UE / Maya 插件）接触多 DLL / 符号导出 / cmake / toolchain / 热路径 / crash 取证坑时读 INDEX 导航到具体文件。省 ~655 行常驻；Codex 按目录表 on-demand 打开 cpp/。（2026-07-19 context-budget audit S2 Tier D）

> FBX SDK guidelines（2 份，读 / 写对称）**不 eager `@`-import**——非 FBX 项目省去；接 FBX 动画 I/O 任务时**按方向**读：**写侧**（往既有 DCC rig 写动画：retarget 成品导出 / 动画迁移 / mocap cleanup 回写）读 [`write-animation-to-existing-rig.md`](guidelines/fbx/write-animation-to-existing-rig.md)；**读侧**（把 FBX 动画按帧采样成 pose 序列喂下游求解 / 分析 / 对拍）读 [`read-animation-from-fbx.md`](guidelines/fbx/read-animation-from-fbx.md)。Codex 按目录表 on-demand 打开 fbx/。（2026-07-28 从 RetargetStudy retarget 预研提升：写侧 PreRotation 漏补偿末端差 79cm / 旋转限位改不掉需吸收；读侧声明 30fps 而实际 100fps 静默丢 70% 数据 / 未 unroll 致根骨假转 106° = 整帧全身翻转）

> 条件域 guidelines（P4 / Windows CI / Claude Code harness）**不 eager `@`-import**——只对特定项目类型相关，接对应任务时按上方组织表 / 本说明按需读（省 ~945 行常驻）：
> - `guidelines/p4/charset-pitfalls.md` —— Perforce unicode server 的 charset transcode 坑（含 typemap / binary 强制）。配套 technique `techniques/ci-deploy-to-p4.md`（CI 自动 submit 到 P4 的完整流程）。
> - `guidelines/ci-windows/`（2 份：`powershell-native-command-pitfalls.md` / `gitlab-runner-service-and-powershell-pitfalls.md`）—— Windows PowerShell / GitLab runner 跑 native command 的 pitfall。
> - `guidelines/claude-code/`（3 份：`hook-conventions.md` / `subagent-contracts.md` / `autonomous-loop-scheduling.md`）—— Claude Code harness / hooks / subagent / 自主 loop 的 hidden contract（连 Codex 都不相关）。配套 technique `techniques/claude-code-autonomous-permissions.md`（permission list 配置）。
>
> （2026-07-19 context-budget audit S2 Tier D）

---

## Techniques

@techniques/adversarial-verification.md

@techniques/enumerate-then-adjudicate.md

@techniques/coordination-patterns.md

@techniques/worker-instructions.md

@techniques/fact-forcing-gate.md

> [`techniques/model-worker-mcp.md`](techniques/model-worker-mcp.md) 是 Model Worker MCP 的安装、Codex/Claude 注册、strict 请求摘要与日常运维手册。只在安装或使用该工具时按需读取，不 `@`-import，避免把工具专属操作常驻到所有项目。

> 条件域 techniques 不 eager `@`-import——`techniques/ci-deploy-to-p4.md`（P4 + Windows CI 部署链）与 `techniques/claude-code-autonomous-permissions.md`（Claude Code permission list 配置）随对应 guidelines 子目录懒加载，触发场景见上 Guidelines 段末 P4 / CI / Claude-Code 说明。`context-budget-audit` 已转成 skill（审计常驻成本时自动触发），见下 Skills 段。（2026-07-19 audit S2 Tier D）
>
> `techniques/cpp-coverage-and-crap-measurement.md`（C++ per-function 覆盖率 / CRAP 测量：lizard + gcov/gcovr + OpenCppCoverage，含 OpenCppCoverage 盘符 bug 等 pitfall）同样不 eager `@`-import——**只在 C++ 项目要拿覆盖率 / 算 CRAP 时按需读**，常驻侧的指标使用认知在 `guidelines/code/complexity-coverage-metrics.md`。（2026-07-24）
>
> `techniques/blackbox-api-characterization.md`（黑箱刻画第三方 API 的**参数语义**：扫了没反应的**五种原因**及各自指纹 / 比较维度不独立时拆混淆变量 / 自证阈值要给浮点噪声留余量 / 数量级不合理先查场景 / 优先找"不是你写的判官"——厂商返回值与库自己填好的对应关系）同样不 eager `@`-import——**只在要搞清一个闭源或无文档库的参数到底控制什么时按需读**。跟 `adversarial-verification.md`（常驻，管"我改的东西对不对"）是**对称的另一半**：本条管"别人的黑箱是什么语义"。比 skill `reverse-maya-closed-nodes` 轻且框架无关（那条覆盖 Ghidra / 汇编且 Maya 专属）——先用本条，不够再上那条。**单项目验证**（其中"五种原因"该项目内 5 次独立复现、每次真因不同），未满足两击规则，apply-and-refine。（2026-07-29 从 HumanIK 闭源库参数刻画提升）

---

## Skills

`skills/` 下是 Claude Code 与 Codex 共用的 Agent Skills。跟 guidelines / techniques 的核心区别：

- **不通过 `@` 进 context**——两个平台都在匹配任务后按需加载
- **加载后正文常驻、不重读**——skill 正文一旦触发即跨 turn 常驻会话，后续 turn 不会重读 SKILL.md（Claude Code [官方明文](https://code.claude.com/docs/en/skills)）。推论：正文每行都是加载后的反复 token 成本，写正文按「值得跨全任务常驻」取舍；持续适用的纪律写成 standing instructions 一次说清，别写「到时候回来看」；会话中途改 SKILL.md 对已加载的会话无效
- 适合按 phase / domain 触发的内容（workflow 编排、跨工作流的 TDD discipline 等）
- `skills/` 是 source of truth；`scripts/sync-skills.ps1` 默认同时同步到 `~/.claude/skills/` 与 `~/.agents/skills/`，也可用 `-ProjectPath` 安装到项目内对应目录
- 双端共用的 portable frontmatter 只保留 `name` 与 `description`；`description` 必须自带触发和跳过条件，详细流程与平台分支放正文
- 通用正文使用平台中性措辞；确实依赖 hooks、配置文件或客户端命令的内容必须明确平台分支或平台限制

当前 skills：

**workflow/** —— 跨域 workflow 编排 + TDD discipline：

- [`skills/workflow/supervised-workflow/SKILL.md`](skills/workflow/supervised-workflow/SKILL.md) — high-touch 工作流，三个 hard user-review gate（plan / impl-plan / per-milestone）
- [`skills/workflow/autonomous-workflow/SKILL.md`](skills/workflow/autonomous-workflow/SKILL.md) — low-touch 工作流，仅 plan gate（实施阶段无 gate）；handoff 文档（brief / context / worklog / result）+ 强 TDD 作执行期安全网
- [`skills/workflow/tdd-with-fixtures/SKILL.md`](skills/workflow/tdd-with-fixtures/SKILL.md) — augment superpowers TDD，加 milestone-level discipline + fixture/manual case escape hatch
- [`skills/workflow/bugfix-tdd/SKILL.md`](skills/workflow/bugfix-tdd/SKILL.md) — bug-fix 场景的 TDD 红→绿 discipline。先写 demonstrate bug 的 failing test → 跑确认 FAIL → 改 production → 跑 PASS → 跑全 regression → test + fix 单 commit。跟 `superpowers:test-driven-development`（feature TDD）/ `superpowers:systematic-debugging`（debug 阶段方法论）/ `tdd-with-fixtures`（escape hatch）互补不重叠。防"看代码自信改一行"无证据修复
- [`skills/workflow/conversation-walkthrough/SKILL.md`](skills/workflow/conversation-walkthrough/SKILL.md) — 编码对话收尾的标准 review 环节（默认开，除非用户说后面是迭代不用 review）。三 phase：结构 map / self-review 三档（🔴 重构套 function-clarity 行数阈值 + ≥2 次重复抽 helper / 🟡 优化 / 🟢 对抗式正确性）/ 注释体检三轴（prose 质量走 `guidelines/writing/prose-and-register.md`——工作语言/不说黑话/不翻译腔/简洁不丢信息，跟 `doc-writing-style` 共用同一份 SoT；stability 按注释自包含原则剥 milestone·Task·Phase 标签 + ephemeral 文档引用、why 浓缩 inline 只引 durable 目标；结构用 Doxygen 契约头）。配套：ephemeral tracking 文档锚讨论主线、重构与注释清理分主题各自 commit、cold rebuild + 冒烟验证语义不变。扩展 `guidelines/code/function-clarity.md`（行数阈值 Rule 1 + 注释 stability/自包含 Rule 2）的「系统化执行」面
- [`skills/workflow/context-budget-audit/SKILL.md`](skills/workflow/context-budget-audit/SKILL.md) — 审计 / 管理 agent-instruction 语料（AGENTS.md / CLAUDE.md @-import + skill description + hook 注入）的 **always-loaded context 常驻成本**：@-import 数偏高 / 加新 @-import 前 / 启动慢或 cache 命中率降 / 一批新 guideline 之后 / 判断某内容该常驻还是懒加载时触发。给四步 audit（Inventory / Classify / Detect / Report+Actions）+ 加载时机三档模型（常驻 / 碰文件触发 / 被调才进）+ anti-patterns。**本 skill 自己就是 Tier D 把 conditional 内容转 lazy 的产物**（原 `techniques/context-budget-audit.md`，2026-07-19 转成本 skill——审计工具只在审计时才需要）。非「维护 guidelines 语料库」项目 skip
- [`skills/workflow/doc-writing-style/SKILL.md`](skills/workflow/doc-writing-style/SKILL.md) — 起草「交付级」文档（设计稿 / 任务书 / handoff / 用户文档 / brainstorm 结论稿 / CHANGELOG）时的文体 + 图示 discipline。两块：(1) 文体——遵循 `guidelines/writing/prose-and-register.md`（工作语言写散文 + 标识符保留原文 / 不说黑话 / 简洁⇔不丢信息 / 不翻译腔）在文档场景的应用（+ 项目自造词开篇 grounding）；(2) 图示——多阶段流程 / 多分支决策 / 易漏关键步任一就**必须画图**（给了 sequenceDiagram / flowchart / 编号列表选型决策表），且图要**可移植**：按目标渲染器版本写、不 hardcode 语法白名单（会过时）、本地能渲染 ≠ 目标能渲染、必要时推探针实测能力边界。目标渲染器版本是项目可调项（语言 / 黑话替换表的 tuning 在 prose-and-register）。文体规则本身是 `guidelines/writing/prose-and-register.md`（跨文档 / 注释共享 SoT），本 skill 加文档场景应用 + 图示；也是 `guidelines/workflow/documentation.md`（何时同步 / 怎么拆 / 怎么建索引）的执行面补充

**ue/** —— UE 专用：

- [`skills/ue/ue-module-architecture/SKILL.md`](skills/ue/ue-module-architecture/SKILL.md) — UE plugin module 切分两层规则：同 module 内 Runtime Ops / Editor Actions / UI 三层模型 + 跨 module Runtime ← Editor 依赖方向硬约束。bundle 了 `editor-runtime-separation.md` + `runtime-module-no-editor-dep.md` 两份原 guideline 内容
- [`skills/ue/ue-reference-engine-source/SKILL.md`](skills/ue/ue-reference-engine-source/SKILL.md) — meta prep-work：写 UE 功能前先找 reference impl。按 22 个 UE 子系统给 engine source 清单 + 5-tier 优先级 + anti-patterns。bundle 了原 `reference-engine-source.md`
- [`skills/ue/ue-settings-persistence/SKILL.md`](skills/ue/ue-settings-persistence/SKILL.md) — UE settings 持久化的三件套（`UPROPERTY(config)` + `Config=<Cat>, DefaultConfig` + `TryUpdateDefaultConfigFile()`）/ `SaveConfig()` 无参陷阱 / `AssetRegistrySearchable` per-instance tag / 嵌套 UObject 集合 PostEditChangeProperty 同步 pattern / 症状→trap 排查表。bundle 了原 `settings-persistence.md`
- [`skills/ue/unrealmcp-usage/SKILL.md`](skills/ue/unrealmcp-usage/SKILL.md) — 消费侧 agent 用 UnrealMCP 插件（TCP 命令到 UE editor）做编辑器自动化（spawn / 改 property / call subsystem / save-exit 等）。bundle 了 canonical TCP 客户端 `ue_cmd.py`，消费项目不再需要自己拷贝。覆盖 detection / TCP invoke pattern / capability gap policy（MCP 不够用先问 user 要不要扩 fork） / top 5 inline gotchas / onboarding 新项目接入步骤 / extending fork 时两侧同步规则。Fork 是 `E:\xd_projects\unreal-mcp`，完整命令参考 + known-issues 在项目里 sync 后的 `UnrealMCP_Docs/`
- [`skills/ue/official-mcp-usage/SKILL.md`](skills/ue/official-mcp-usage/SKILL.md) — 消费侧 agent 用 UE 5.8+ **官方** `ModelContextProtocol` MCP server（HTTP，默认 `127.0.0.1:8000/mcp`）做编辑器自动化。跟 `unrealmcp-usage`（fork）对称：那条 fork 怎么用，这条官方怎么用。覆盖 (1) setup 真相——`ModelContextProtocol` 只是 server 外壳，真正提供工具的是 `AllToolsets` 聚合器（只开 server 不开 AllToolsets → 连上也没工具），4 plugin 验证配置 + auto-start / 控制台命令 / `.mcp.json` HTTP 配置；(2) 9 条 usage hidden contract——`load_toolset` 跨 turn 才生效 / Reconnect 是 client tool list 刷新唯一入口 / 工具名点转单下划线 / session id 绑 server 生命周期 / schema 误标 / refPath 约定；(3) 失败纪律——官方报错停下问 user Reconnect，不要静默 fallback 换后端。平台选型见 `guidelines/ue/mcp-platform-choice.md`
- [`skills/ue/ue-ml-animation/SKILL.md`](skills/ue/ue-ml-animation/SKILL.md) — UE 里「代码 / 神经网络直出 pose、不走 AnimBP 状态机」两组 hidden contract（来自 PathAnimGen 预研，原 `animinstance-proxy-and-offline-eval.md` + `nne-onnx-inference-contracts.md` 两份 guideline lazy 化 bundle 进本 skill）。**动画注入侧**：纯 C++ `UAnimInstance` + 自定义 `FAnimInstanceProxy` 零 AnimBP 直出 pose / `Update()` 被 `GFrameCounter` 门控（累计放 `PreUpdate`）/ 离线评估配方 `TickAnimation → RefreshBoneTransforms → FinalizeBoneTransform`（漏末步读旧双缓冲）。**模型推理侧**：NNE 只吃 ONNX / `NNERuntimeORT` 默认关闭需显式引用 / 坏模型报错点在 `CreateModelInstanceCPU` / 动态输出 shape 第一次 `RunSync` 后才可查且 buffer 不足静默不拷
- [`skills/ue/ue-procedural-numerical/SKILL.md`](skills/ue/ue-procedural-numerical/SKILL.md) — UE 里「程序化建 RigVM/ControlRig/Deformer 图 + 模块内数值 / GPU / 并行」六组 ultra-niche hidden contract（多数踩自 curvenet 形变插件，原 6 份 UE guideline lazy 化 bundle 进本 skill）：RigVM 逐元素大批量数据走 `URigHierarchy` metadata 别烤 pin 默认值（否则图卡死）/ Sequencer 批量烤 key 写 section 浮点通道别逐 key `SetLocalControlRig*` / Optimus `ComputeNormalsTangents` 丢 authored 法线→换 `Keep{Imported,Input}Normals` / `FRBFSolver`·`TMemStack` 出 anim-eval 作用域需自建 `FMemMark` / UE 无官方 GPU 稀疏求解器→bring-your-own 运行时加载 + 安全回退 / UE 模块 OpenMP 装不了→`IntelTBB`·`ParallelFor` + 跨框架后端无关抽象
- [`skills/ue/ue-custom-graph-editor/SKILL.md`](skills/ue/ue-custom-graph-editor/SKILL.md) — 从零建一个 UE 自定义 node-graph 编辑器（Blueprint / Material / Behavior Tree 式 `UEdGraph` 编辑器）。bundle 了原 `techniques/ue-custom-graph-editor.md`（7 步 build 流程，每步带坑 + 验证）+ 原 `guidelines/ue/graph-data-ownership.md` 的 UE 执行面（数据归属表 / `SGraphEditor` pin-first 约束 / compile full-flush > incremental sync）。**Ultra-niche**——只在做**新的**自定义图编辑器时触发。硬 per-API 约束（NodeGuid / pin SetOwner / `RF_Transactional` / undo refresh / copy-paste DuplicateObject）仍常驻在 `guidelines/ue/graph-editor-constraints.md`。数据归属的框架无关上位原则见新建的常驻 `guidelines/code/dual-layer-data-ownership.md`

**maya/** —— Maya 插件专用：

- [`skills/maya/maya-tool-interaction/SKILL.md`](skills/maya/maya-tool-interaction/SKILL.md) — DCC 拖拽编辑工具（Maya manip/context，泛化到其他 3D 工具）的六个交互模式：press-time 完整重算（不累加 delta）/ press-time caching 防反馈闭环漂移 / 位移阈值防抖 / snapshot-diff undo（非 plug-level）/ undo 数据存业务对象而非 UI manip / 控制器叠在被驱动对象上（live attach + 两层）。配套 framework 契约见 `guidelines/maya/`。单项目验证、apply-and-refine
- [`skills/maya/reverse-maya-closed-nodes/SKILL.md`](skills/maya/reverse-maya-closed-nodes/SKILL.md) — 复刻或诊断闭源 Maya 节点时的分层证据工作流：Ghidra 伪代码只生成假设，汇编/ABI 裁决参数，单变量 probe + 激发守卫，正交合成差分 oracle，最后用真实资产多 pose 收敛；同时区分 confirmed / strong inference / open。

**architecture/** —— 框架无关架构 pattern：

- [`skills/architecture/multi-plugin-shared-core/SKILL.md`](skills/architecture/multi-plugin-shared-core/SKILL.md) — 多插件共享一个 core 实体的六个可组合模式：type-keyed ExtensionContainer（替代继承爆炸）/ feature-parser 注册制（base 零依赖）/ Preset→Template→Instance 数据驱动三段式 / Snapshot+Ops 数据操作分离 / 非拥有 Registry 单一查询入口解耦命令 / 权威类型不可扩展（vendored·子模块·他队拥有）时编辑层 state 复用既有值标记（不 fork 类型也不加并行字段）。框架无关（Maya 多 `.mll` 提炼，UE module / 通用 plugin 系统同样适用）。跟 `skills/ue/ue-module-architecture` 同形态不同框架。单项目验证、apply-and-refine

**collaboration/** —— 多 agent / 多对话协作机制：

- [`skills/collaboration/multi-session-coordination/SKILL.md`](skills/collaboration/multi-session-coordination/SKILL.md) — 多个 Claude Code 对话并发在同一 repo 工作时的协调协议。bundle 了 hook 脚本 (`multi_session.py`) + agent-side 政策（lease 让/抢/协商 heuristics + commit-then-release 强约束）+ 安装文档 (`install.md` / `install.ps1`)。Hook 机制由 `settings.json` 注册自动跑（SessionStart 注册 / PreToolUse 撞 lease deny / PostToolUse 记 touched_files / UserPromptSubmit 注入 inbox + git log since last turn / Stop 释放 lease）；skill 仅在 hook surface 协调信息时按需 load。需走 `install.ps1` 一次注册 hook
- [`skills/collaboration/role-lane-coordination/SKILL.md`](skills/collaboration/role-lane-coordination/SKILL.md) — 把一个较重项目拆到**多个常驻对话**（每对话 = 一条 role-lane / context 边界）并协调它们的**项目级方法**:role⊥task 矩阵拆对话 / seam-contract 协同设计 / 分档 oracle（hard gate→auto-act·advisory·park）门控自主 / notify·act 自主度旋钮 + checkpoint 落人判断点 / **唤醒机制（mailbox 无通知原语 → 按预估 ETA 轮询·人推;长跑 Monitor 会资源耗尽死→定时轮询兜底）** / **分档路由（结构化走 hub、领域重·紧耦合人眼直连用户）** / 跨 lane 汇合用单一 coordinator 宿主 / **brief 正确性≠完整性** / durable 文件抗失忆 / 收件箱按发件人消歧 + ack 约定。跟上一条 `multi-session-coordination` 分层:那条是同 repo lease/inbox **hook 底层机制**,本条是**项目级协调方法**（同 repo 复用它）。**operating model = 同机 + 共享 `~/.claude` 绝对路径 mailbox + 人作异步决策/唤醒层**;**已跨 2 项目 / 2 拓扑验证**（renderer_test 平级 peer + 跨 repo 库接入 hub+fan-out）。**真分布式（跨机 / 无共享盘 / 跨人）未覆盖、全无人值守 / 紧耦合 peer thrash 未在本模式发生**——是 scope 边界,不是待办 gap

> Sync 注：repo 是分类目录（`<category>/<name>/SKILL.md`），安装到 Claude Code 的 `~/.claude/skills/` 或 Codex 的 `~/.agents/skills/` 时都按 `<name>/` 扁平化。`ue-*` prefix 在安装后仍然可见 UE 归属。详 `scripts/sync-skills.ps1`。
