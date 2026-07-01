# Seen Ledger —— 去重账本

`/research-radar` 每次跑前读这里,避免重复推同样的条目。每次跑后把**新出现的候选**
(无论你最终是否促成)追加到下面,标注首次出现日期 + 处置。

处置标记:`📥 雷达中`(待评审) / `✅ 已促成`(进了 guidelines/skill,注明去向) /
`❌ 丢弃`(评审后认为不相关) / `👁 观察`(暂留,等第二次信号)。

## 已知不必再推(老生常谈 / 已在 repo 充分覆盖)

下面这些是 baseline,搜索时应**主动排除**,除非出现实质性新角度:

- Conventional Commits / commit message 规范 —— 已有 `guidelines/workflow/commits.md`
- 通用 TDD red-green-refactor —— 已有 superpowers:TDD + `skills/workflow/*tdd*`
- 「写小函数 / 单一职责」泛泛原则 —— 已有 `guidelines/code/function-clarity.md`
- AGENTS.md / CLAUDE.md 存在与基本用法 —— 已是本 repo 的核心 setup
- 「先读文档再改代码」泛泛建议 —— 已有 `guidelines/code/constraints.md` 等

## 条目记录

<!-- 格式:
### YYYY-MM-DD 首见
- [处置] <条目名> —— <一句话>。<促成去向 / 丢弃理由>
-->

### 2026-06-25 首见(详见 `2026-06-25.md`;⚠️ 该轮 verify 阶段撞额度未跑,候选均未经 harness 核验)
- ✅ 决定促成(2026-06-25 review)`.claude/rules/` 路径作用域指令 —— 已核源属实(claude.com steering blog)。促成形态:在 `techniques/context-budget-audit.md` 加「三档加载模型(永远在 / 碰文件自动进 / 被调才进)+ 该放哪档决策表」,并注两 caveat(① Claude-Code 专属、② paths 是文件 glob ≠ 项目类型)。待落地编辑。
- ✅ 决定促成(2026-06-25 review)Hooks 扩展 —— 已核 code.claude.com/docs/en/hooks:实际 **33 个事件**(claim 说 29,更多)+ **5 种 handler 类型**(command/http/mcp_tool/prompt/agent,后者实验性)+ env var 不止 3 个(新增 CLAUDE_CODE_REMOTE / CLAUDE_EFFORT / CLAUDE_ENV_FILE)。促成形态:**定向更新 `guidelines/claude-code/hook-conventions.md` 3 处过时事实**(事件集 / handler 类型 / env var 数),**保留全部踩坑陷阱**(self-deadlock / path-baking / permissionDecision / exit-code-2 仍准确)。单独 docs: commit。待落地。
- ✅ 已落地(2026-06-25 review,非 corpus 知识)自定义命令并入 Skills —— 已核源属实(code.claude.com/docs/en/skills,命令文件仍兼容)。**行动**:已把 research-radar 从 `.claude/commands/research-radar.md` 迁成 project-local skill `.claude/skills/research-radar/SKILL.md` + `disable-model-invocation: true`(纯手动)+ 顺手补步骤 2.5(verify 失败假阴性处理)。本条是工具决策不进 guidelines(官方文档已述,knowledge-promotion 不重复)。
- ✅ 决定促成(小)(2026-06-25 review)Spec-Kit 借鉴 —— 已核源(github.com/github/spec-kit + analyze.md/constitution.md 模板)。整套不采纳(与现有 workflow 体系重复),但**吸收两点**:① 双向覆盖检查(plan 每项都落地?有没有做计划外的?)② spec 质量启发式(含糊词无量化 / 未解占位符 / 不可测验收标准)。促成形态:给 `supervised-workflow` / `autonomous-workflow` skill 加一个轻量「收尾一致性 gate」(查「做的 ↔ 当初说的」是否对得上,不同于 code-review 的代码质量 lens)。constitution 那套基本已有;sync-checklist + 语义版本号留观察。待落地。
- 👁 观察 + 轻促成(2026-06-25 review)Context engineering(Anthropic) —— 几乎全在 corpus 有对应物(context-budget-audit / coordination-patterns iterative-retrieval / memory+daily+open-items),你独立造出来了。**行动**:搭 #1 改 context-budget-audit.md 的车,顺手加一行一手出处指针(Anthropic effective-context-engineering),不单开文档。
- ✅ 决定 promote(两个小增量)(2026-06-25 review)Multi-agent 经济学 + LLM-as-judge —— 已核 anthropic.com/engineering/multi-agent-research-system,数字一字不差(单 agent ~4× / 多 agent ~15× token;token 用量解释 80% 方差;何时值=重并行/超 context/多复杂工具,不值=共享 context/多依赖;LLM-as-judge=单次调用 0-1 分+pass/fail,5 维 rubric:事实准确/引用准确/完整性/源质量/工具效率)。promote 形态:① `coordination-patterns.md` 加「多 agent 成本 & 何时值」节(+本 session 8M token 撞额度作项目实例);② `adversarial-verification.md` 加单次 LLM-as-judge + 5 维 rubric。两者标 Anthropic 出处,不照抄。待落地。
- 👁 observe(2026-06-25 review)UE PythonAutomationTest + CQTest —— 已核 Epic 文档:PythonAutomationTest 属实(5.8,`test_*.py` in `/Content/Python` 自动发现,编辑器执行期不 tick→用 AutomationScheduler),**但** ① headless/CI 能否跑 Epic 没确认(正是 automation-test-from-ci.md 的核心)② CQTest「更新替代」framing 夸大(文档只列为 interface 之一)。未真用过,promote 属 speculative。**若**将来上 Python 编辑器测试再回看,先验证 headless 可跑性。
- 👁 observe(2026-06-25 review)MSVC 与 VS IDE 解耦 —— 已核 MS C++ blog 属实(VS2026/18.0,2025-11-11;MSVC 6 月一版/9 月支持,LTS 每 2 年/3 年;ABI 兼容回溯到 VS2015;可独立 pin toolset)。但属「框架新闻/awareness」非踩坑,且**用户仍在 VS 2022 未升 2026,暂不适用**。真遇到「CI ABI 跨机可复现」需求再促成。
- ✅(确认非新) UE 5.8 官方编辑器内置 MCP + MCPClientToolset —— **已被 `guidelines/ue/mcp-platform-choice.md` 覆盖**,本轮仅再确认。
- 👁 Agent Skills 开放标准 agentskills.io 跨工具 —— 背景信息,关系 Codex 兼容,未达促成门槛。
- 👁 Subagent 声明式 `.claude/agents/` + per-subagent tool allowlist + 嵌套深度 5 —— 编排基本面已覆盖,新的是原生声明式 agent 文件格式。
- 👁 TAPython(UE Python 编辑器工具插件) —— 你以 C++ 插件为主,仅存在性 awareness。
- 👁 Maya 2026.1 executeCommandOnIdleWithPriority() —— idle 优先级调度,⚠️verify 后或可补 maya guidelines。

### 已并入「不必再推」的(本轮确认已成熟/已覆盖)
- Skills 懒加载 / 三级 progressive disclosure —— 已重度使用 + AGENTS.md 已述。

### 2026-07-01 首见(详见 `2026-07-01.md`;⚠️ 该轮 verify 撞 session limit 腰斩——9 条 claim 核验 errored、synthesize 失败;标注见 digest)
- ✅ 已促成(2026-07-01)Claude Code auto-mode / sandbox 三连硬化(6 月)`[3-0 已核验 + WebFetch 复核引文]` —— `2.1.183` auto mode 拦未经要求的破坏性命令(`git reset --hard`/`checkout -- .`/`clean -fd`/`stash drop`/非本-session `commit --amend`/未点名 stack 的 tf/pulumi/cdk destroy);`2.1.187` 新 `sandbox.credentials` 阻 sandbox 读凭据 + secret env;`2.1.193` 新 `autoMode.classifyAllShell` 全 shell 走 classifier。**促成去向**:`techniques/claude-code-autonomous-permissions.md` 新增「Auto Mode: Engine-Side Destructive-Command Guardrails」节(auto-mode 层 vs 三 list 层正交 / 放开 commit 权限仍被兜 destructive / 两个 settings 表 / 默认值 changelog 未给已标注 caveat)。源:code.claude.com/docs/en/changelog(引文经 WebFetch 逐条核实)
- 📥 雷达中 Maya 2027 devkit:Qt5→Qt6.8.3 + MSVC 钉死 VS2022 v17.14.13 `[未核验-仅 search]` —— C++/Qt `.mll` 硬 ABI 断裂 + MFnMesh boolean ops / M3dView 选择回调变更。对到 `guidelines/maya/plugin-build-and-scripting-contracts.md`(跨版本 devkit 工具链契约新数据点)。**促成前必须手动核源** blog.autodesk.io/maya-2027-api-update-guide + 确认项目是否升 2027。
- 📥 雷达中 Claude Code 压缩按 LRU 驱逐已调用 skill `[3-0 已核验]` —— compaction 时超预算先丢最早调的 skill 正文;长 session 静默丢早期 skill。正交补 `techniques/context-budget-audit.md`「被调才进」档的隐藏行为。门槛偏高(版本相关易过时)。源:claude.com steering blog
- 👁 观察 pre-call gate 授权拦截学术框架 `[2-1 核验但⚠️源存疑]` —— 工具调用前确定性授权拦截(proactive)。对到 `techniques/fact-forcing-gate.md` 思路,可作学术出处指针。⚠️ arxiv `2603.20953` 存在性未独立确认,促成前必须核实论文真实可引,否则不加。
- 👁 观察 UE 5.8 = 最后一个 UE5 大版本(UE6 约 2027 末 early access)—— 利好深耕 5.8 hidden contracts(版本天花板 = 5.8 契约不会被 5.9/5.10 快速淘汰),但非可操作规则。源:unrealengine.com State of Unreal 2026
- 👁 观察 `$PSNativeCommandUseErrorActionPreference`(PS 7.4+)—— 非终止错误,`try/catch` 抓不到;是 PS 5.1 NativeCommandError-on-stderr 坑的 PS7 对应面(触发是 exit code 非 stderr,opt-in 默认关)。你在 PS 5.1 暂不适用;升 PS7 再看。源:learn.microsoft.com about_preference_variables

### 本轮 promote 落地(2026-06-26)
- #2 → `3272c70` docs: refresh hook-conventions（33 事件 / 5 handler / env var）
- #1+#5 → `e0b64e6` docs: context-budget-audit 加三档加载模型 + 决策表 + Anthropic 出处
- #6 → `cafe883` docs: coordination-patterns 成本节 + adversarial-verification LLM-as-judge
- #4 → `5e8c450` docs: workflow skills 加 Phase 4 收尾一致性 gate
- #3 已在 review 期落地（research-radar 迁 project-local skill）
- #7 #8 observe（未 promote）；#5 借 #1 的 commit 落地
