# Adversarial Verification

## Purpose

Procedural checklist for adversarial verification of code changes. The goal is to try to break the change, not confirm it works.

## Self-Check

Before starting verification, review the common failure modes in `guidelines/workflow/agent-lifecycle.md`. If you catch yourself writing explanations instead of running commands — stop. Run a command.

## Verification Strategies by Change Type

### Frontend

1. Start the dev server
2. Check rendered output via browser tool or curl
3. Verify sub-resources load (images, API calls, static files)
4. Run frontend test suite

### Backend / API

1. Start the server
2. Curl endpoints -- verify response body structure, not just status codes
3. Test at least one error path (bad input, missing auth, not found)
4. Run backend test suite

### CLI / Scripts

1. Run with representative input
2. Verify stdout, stderr, and exit code
3. Test boundary inputs: empty string, malformed input, extreme values

### Infrastructure / Config

1. Validate syntax (linter, dry-run)
2. Verify environment variables are actually referenced in code
3. Check that changes don't break existing config consumers

### Bug Fixes

1. Reproduce the original bug first
2. Apply the fix
3. Verify the bug is resolved
4. Run regression tests
5. Check for side effects on related functionality

### Refactors (no behavior change)

1. Run all existing tests -- they must all pass
2. Diff the public API surface -- no unintended changes
3. Spot-check behavioral consistency on key paths

## 选可信 check：四要素 + oracle 判据（MFIC）

前面按改动类型给了验证策略，但还缺一个横切判断：**一个 check 本身可不可信？** 尤其当写代码和写 check 的是同一个 agent 时，用同一个错误假设写出来的 test 会跟着错代码一起变绿——静默通过。

**试金石（一句话判断）**：*如果同一个 agent 既写了 check 又写了被检对象，它能带着错误工作通过吗？* 能 → 这个 check 可被糊弄，不可信。

一个可信的 check 要同时满足四要素，缺一个就退化成常见近似失败：

| 要素 | 含义 | 缺了它 |
|---|---|---|
| **Mechanically** | 用例机器穷举 / 变异 / 生成，不手挑 | 手挑用例，漏掉没想到的分支 |
| **Falsifiable** | 用例真会咬——错了就红，且你无法预先安排让它绿 | 空洞绿测（"没崩就行"）|
| **Independent** | 判据在因果上独立于生产者（职责分离的软件版）| 合谋 check，跟代码共享盲点 |
| **Control** | 有权拦截（fail build / block commit），不只 log | 只告警不拦，坏结果照样进 |

### oracle 判据：什么时候才真的需要"换一个 agent"

Independence 不等于"永远要另找一个人 / agent review"。真正的分界是**有没有一个生产者之外的 oracle**：

| 情形 | 例子 | 谁写 check 重要吗 |
|---|---|---|
| **存在外部 oracle** | round-trip 逆运算 `decode(encode(x)) == x`、reference 实现差分、变换不变量、事先定死的 checksum | **不重要**——同一个 agent 写代码和 check 也糊弄不过去，因为判官是它控制不了的独立因果物 |
| **无 oracle** | 普通 example test，手写的期望值本身就是"真理标准" | **重要**——同一个 agent 会把同一个错误假设同时写进代码和期望值，一起错到底 |

推论：**只有在"无 oracle"这种情形，才真正需要一个独立的 checker**（且这个 checker 只从契约推导、绝不读实现——读了就被带进同一盲点=合谋）。有 oracle 时，优先花小成本上 oracle-based check，比拉一个独立 reviewer 更便宜也更稳。这跟 [`coordination-patterns.md`](coordination-patterns.md) 的"验证别人的实现用 fresh worker 防 anchoring"是一体两面：那条讲无 oracle 时怎么隔离 checker，这条讲有 oracle 时可以省掉隔离。

### 验证策略阶梯：优先选作者没写的判官

按"判官独立性"从强到弱，选**能上的最便宜那一档**：

1. **穷举有限域**——域有限就跑遍，不抽样。
2. **round-trip 逆运算**——操作有逆就 `f⁻¹(f(x)) == x`。谁写的 round-trip 不影响判据。
3. **差分 vs reference 实现**——有参照实现就两边都跑、diff 结果。
4. **metamorphic 不变量**——断言关系而非具体值（如复杂度门断言 `f(2N) ≈ 2·f(N)`，比值抵消掉机器速度、跨机可移植；无需期望值也无需 reference）。
5. **input-mutation 覆盖率**——把"我的 validator 覆盖了整个格式"这种不可证伪的空话变成一个数：拿一个合法输入，逐 bit / byte 翻转，断言 validator 现在**拒绝**它；被拒的比例就是覆盖率。两个防作弊前提：(a) 配一份全合法输入的 corpus 必须全过（否则"拒绝一切"的 checker 拿满分）；(b) 只统计"必须有意义"的字节（padding / checksum 排除区是合法 don't-care）。
6. **property-based + shrink**——都不满足才生成属性、把失败 shrink 到最小反例。

核心原则：**优先用作者没写的 oracle。** 手写的"期望值"本身可能就是 bug；round-trip / reference / 不变量不会，因为它们都不依赖"作者当初想对了"。

> **round-trip 陷阱**：序列化器若做**自动版本迁移 / 规范化**（如 MaterialX 默认 `upgradeVersion`、格式化器重排属性 / 丢注释空白），`f⁻¹(f(x))` 会**故意非 identity** → round-trip oracle 误报。修：pin 版本 + 关自动迁移；且**比语义不比字节**（注释 / 空白 / 属性顺序与语义无关）。

> **录制-回放 oracle**（存在性指针，本 repo 未自用）：期望值不手写——把系统一次真实运行的持久化输出收割为 fixture，之后无凭据确定性回放比对；参考 deepseek-harness 0.1.0-rc.5 的 keyless snapshot（"the fixture is a genuine product of the system rather than a hand-built mock"，replay 主动跳过 `.env` 防误触真实调用；2026-08-17 源码核实）。比手写期望值高一档，弱点也明确：**「哪一次运行算对」仍由录制者 + reviewer 裁决**——行为坏了重录一次，坏行为就固化成合法期望值，机械层不报警。真做第一个 record-replay fixture 时再展开成正式阶梯档。

> 来源：pmarreck，[MFIC — Mechanically-Falsifiable Independent Control](https://gist.github.com/pmarreck/b30aa3ca69cb70a5526f8a63ab8c8d7e)。把企业内控（COSO / SOX：职责分离 / 预防-检测-纠正控制 / 控制测试）搬到"LLM 是不可信方"的语境。TDD 只提供四要素里的 Falsifiable（红相证明测试能咬），其余三个要另外补。

## 跨源逐帧对拍：先钉死并**打印**对齐三件事

拿两份数据逐帧（逐行）比，前提是它们落在**同一条时间轴 / 索引轴**上。这个前提极易不成立，而不成立时算出来的数字**看起来完全合理**——于是你去调被测方，而真正坏的是对齐。

凡"读一个源、再跟另一份数据逐帧比"，显式钉死这三件，并把实际取值**打印到输出里**：

| 要钉死的 | 陷阱 |
|---|---|
| ① **采样率** | 文件 / 接口**声明**的率可能 ≠ 真实数据密度（实测声明 30、实际 100） |
| ② **起始时刻** | 各源的起点可能不同——差几十毫秒就是几帧 |
| ③ **比较窗口** | 一方可能提前结束、之后常量外推；冻住的帧不该参与 |

**埋在代码里不算**，要作为输出的一部分——数字可疑时看一眼对齐参数就能判"是被测方的问题还是对齐的问题"，不必回头重读脚本。

**识别信号：共模偏移。**「被比较的两方**一起**变差」几乎一定是**基准**或**对齐**坏了，不是被测方——被测方自己的缺陷不会同时让对照组也变差。

**证据**（同一类错误在一轮工作里踩了三次，每次的错误数字都看着合理）：

| # | 症状 | 真因 |
|---|---|---|
| 1 | 验收报 `max｜Δpos｜` = **3070 cm** 假失败 | 按文件**声明**率读回、跟内存里另一采样率的结果按序号比（按真实率读实际是 6e-04 cm） |
| 2 | 被测方与对照方**同步**虚高到 50.63 / 52.92 | 基准只覆盖前 1698 帧、之后常量外推冻住，而两方都有 2277 帧真数据 |
| 3 | 限定窗口后仍偏（13.70 而非 6.59） | 一方从**数据实际起点**采样、另一方从**容器声明起点**，差 23 ms（≈2.3 帧） |

**诚实边界**：目前只在单个项目验证过（未满足 [`knowledge-promotion.md`](../guidelines/workflow/knowledge-promotion.md) 的两击规则），但项目内 3 次独立复现。**不限于时间序列**——任何"跨源逐行对拍"（两个数据库导出比对、两版日志 diff、两个实现的输出序列）都同形。

## metric 选错，缺陷会看小一个量级

check 的"牙"不只取决于断言写得严不严，还取决于**你量的是哪个量**。同一个物理现象换个量法，数字能差一个量级：

实测同一个"小臂扭转"缺陷——量**手腕相对小臂**的扭转 = **5°**（看着可接受）；量**小臂自身绕长轴的滚转** = 峰值 **123°**（参照实现精确 0°）。后者才是生产端看到的那个。第一个量法漏掉它，是因为求解器把扭转**搬到了下一根骨上**，而相对量看不见搬家。

**推论：整体指标会盖住分部位问题。** 聚合（平均 / 总分）会稀释只影响局部、或只影响某个自由度的缺陷：

| 缺陷 | 为什么整体指标看不见 |
|---|---|
| 绕自身长轴滚转 | 几乎不改变任何骨骼的**位置**，而指标量的是位置 |
| 单帧毛刺 | 几千帧里的几十帧，平均值几乎不动 |
| 单个部位的量级错误 | 被其余部位摊平 |

实测后果：在"全骨平均位置差"上赢了对照工具，同时在小臂滚转上差 100°+。**整体指标和分部位指标都要报**，别只报一个。

**下手前先问**：我要抓的那个缺陷，在这个 metric 上会体现成多大？如果答案是"很小"，这个 metric 对它就是**没牙**的（对应四要素的 falsifiable）。选 metric 跟选 oracle 一样是验证设计的一部分，不是记账格式。

> **对称的另一面**：聚合量不仅会把**缺陷**看小，也会把**参数的作用**看没 —— "改了参数结果没变"这个廉价可证伪信号，只在**逐位比原始输出**时有效；用在 p95 / 最大 / 均值上会给出"参数没接上"的假信号。见 [`../guidelines/code/reporting-limits-and-null-results.md`](../guidelines/code/reporting-limits-and-null-results.md) 规则 2。

## 量具先自证，再拿它判别人的实现

上一节管**量错了东西**。这节管**量具自己坏了**——而它坏掉时不报错，只会产出一个**关于别人实现的、
看着完全合理的错判**。同一轮里测量脚本出过下面 6 种不同的坏法，每一种都产出一条这样的错判：

| 量具的毛病 | 它产出的错判 |
|---|---|
| 角度提取的 `atan2` 参数顺序写错 | 「对方实现非单调，坏了」 |
| 量骨骼扭转时用了它自己的长轴（末端骨没有子骨 → 函数恒返回 0） | 「参照实现压根不往子骨分配」 |
| 减掉了 v=0 基线（恰好把「谁持有多少」这个要看的量减掉） | 「v=0 时两边都是 0，看不出差别」 |
| 为测试 A 改了一个**全局**旋钮，污染了测试 B 的基线 | 「两边符号相反」（同一个 rig 从 −1.94 变 +0.87） |
| 两次测量用了不同的缩放基线 | 「补偿量非单调，规律不成立」 |
| 角度差跨档做减法没折回 (−180, 180] | 「份额列非单调」 |
| 用命令行子串给进程分类，而**模式串就写在查询自己的命令行里** | 「被测系统里有一条根本不存在的进程父子链」 |

**最后一行是另一种形态：量具把自己算进了被测对象。** 前六种是「量错了东西」，它是量具**成为**被测对象的一部分。
典型场景：按命令行子串筛进程（`CommandLine -like '*<模式>*'`），而这条查询自己的命令行里就含有那个模式串，
于是它把自己那棵 shell 嵌套树（`bash → bash → powershell`）整棵算成了被测进程——嵌套天然逐级为父，
就"观测"到一条真实系统里并不存在的父子链，而且**每查一次就造一条**。同族的还有：日志分析脚本把自己写的日志
读了进去、grep 统计命中数时数上了自己的命令行、监控探针把自己的请求计进了 QPS。两条纪律：

- **让模式串在运行时拼出来**，使查询自身的文本不含它；再按可执行文件名之类的正交维度收窄（只认目标解释器，排除 shell）。
- **标签可疑时打印原始记录**（完整命令行 / 原始日志行），不要继续相信分类结果——破案靠的正是这一步。

代价是实测过的：两方据此互相要求对方去找一条不存在的代码路径，往返数轮，而双方都在被测对象那边找，没人回头查量具。

四条纪律：

1. **量具先过一个已知答案。** 本轮用的是「参照实现应当复现某张已发表的表」——它复现了，量具才可信。
   这是把上面的 oracle 阶梯用在**量具自己**身上，不只用在被测对象上。
2. **量具坏掉期间产出的中间数字，一个都不往外报。** 本轮丢弃 5 组，只报最后自证过的那组。
   报出去的每个错判都是对方一整轮往返。
3. **自己两份数据打架时，先认「我这边不确定」，不要判对方。** 本轮最后一条修正正是这个情形（旧 oracle
   与新测量矛盾），处理是明确告诉对方「先别改，等我解决自己的矛盾」。
4. **一个量具只服务一个口径。** 为某个测试改的全局默认值会污染别的测试——把口径做成参数，别做成全局默认。

每次救回来靠的都不是「感觉不对」，而是**数字以结构化的方式可疑**：

| 信号 | 先怀疑什么 |
|---|---|
| **恰好为 0** | 那是量具的 0，不是事实的 0——先查这个量在我的实现里有没有真被算出来 |
| **恰好是整数 / 整齐的圆数**（max 恰好 10.0000） | 撞了限位，或等于某个几何量，不会是巧合（本轮顺着它查出了一条此前不知道的修正） |
| **非单调 / 在 ±180 附近跳变** | 角度回绕，别读成「实现坏了」 |
| **两边一起变差**（共模） | 基准或对齐坏了，不是被测方（见上「跨源逐帧对拍」） |
| **每次测都有，但每次的实例都不同** | 不是「现象在持续发生」，是「每次观测自己造一个」——观察者效应的指纹 |
| **结构上过于整齐**（层数恰好等于探测器自身的嵌套深度、时间戳挤在同一瞬） | 真实的并发 / 竞态没有理由每次都产生同样深度的结构；先怀疑量具 |

后两条里，**「结构上过于整齐」单次观测就能用**，比「每次实例都不同」（需要多次观测）更早生效。它跟上面
「恰好为 0 / 恰好是整数」是同一族判据：**结果整齐得不像自然产物时，先查量具，别先解释被测对象**。

### 对照组自己也需要被验：一个不可能失败的对照组不是对照组

上面那些判据里有好几条要靠**对照组**（拿几个确定成立的样本一起量，用来排除「方法本身坏了」）。
但对照组是一段代码 / 一次操作，它自己也会不生效 —— 而**它不生效时不会报错**。

同一天、两个不同项目域各命中一次，两次的教训**方向相反**，所以不能合成一句：

| | 发生了什么 | 得到的教训 |
|---|---|---|
| **对照组正常工作** | 判某二进制是 Debug 还是 Release，**成对搜**两个 CRT 名 —— 结果**两个都没命中** ⇒ 它告诉你「**这条判据在这儿失效**」，而不是给你一个错答案 | 对照组值得那份成本：它把「没找到 ⇒ 是另一个」换成「判据不适用」 |
| **对照组根本没跑** | 用 `git stash` 前后数测试数当对照 —— 而 `git stash push` 默认**不带未跟踪文件**，于是「改前」的树跟「改后」一模一样，两次数出同一个数 | **对照组自己也需要被验** |

⇒ 两条可执行的，第二条常被漏掉：

1. **上对照组**；
2. **上完再问一句：这个对照组有没有可能其实没生效？** 判据是「**让它必定失败的那个操作，我做了吗**」——
   那次该做的是「stash 完先确认那两个文件真的从树上消失了」，一行 `ls` 的事。

⚠️ **为什么第 2 条特别容易漏**：**对照组失效的表现是「两边一样」**，而「两边一样」在验证语境里
**长得像好消息**（没有回归 / 没有影响）。它比本节前面那些指纹更难自查 —— 「恰好为 0 / 恰好是整数 /
结构过于整齐」至少**看起来怪**，而「两边一样」不怪，它看起来正是你希望看到的。

⇒ 补进上面那张指纹表：**「对照组和实验组给出同一个结果」时，先证明对照组能失败，再解释结果。**

> **它属于一个更大的族**：「缺席」有两种成因 —— **真的没有** / **我看不到** —— 而两者产生**同一个观测**。
> 本节的「两边一样」、下文「第四级：读回错误对象」、以及「只报『变了』的 gate 对『从来就没有』是盲的」、
> 「审计得出『无依据』其实是证据在够不着的仓里」，都是它的面。上位规则与那一问（**我能到达的范围，
> 是不是就是全部范围？**）见 [`../guidelines/code/reporting-limits-and-null-results.md`](../guidelines/code/reporting-limits-and-null-results.md) 规则 3。

### 统一这张表的机制：问「这个量还能取别的值吗」

上表是**枚举现象**，而枚举会漏。它漏掉的一种是：结果**恰好等于基线**——一个「透出来多少」的量，恰好
等于「完全无遮挡」时的值。它不长得像 0、也不是圆数，所以不在表里，但它同族。

统一判据不是记住哪些数字可疑，而是一个可执行的问题：

> **结果恰好落在理论端点（0 / 上限 / 整数 / 基线本身）时，先问：这个量在当前配置下，还有别的取值可能吗？**
> 答案是「没有」，那么这个数是**接线证据**（证明这条路通了），**不是效果证据**（不证明效果好）。

实测的形态：一个半透明渲染特性关掉深度写之后，被遮挡物的可见像素**在结构上不可能**少于无遮挡基线——
深度写一关，遮挡这件事就不发生了。于是「被遮挡物的可见像素 = 无遮挡基线」这个漂亮数字，只证明渲染
通道配置对了，对「看起来好不好」零信息。

值得记的是**它怎么被发现的**：报告人自己**没被骗**（他另外量了对比度、有真效果证据），但仍然
**把这个数当主结果报了出去**——因为他说「100% 透出来了」时，心里想的是「效果好」。所以这条防的不是
「被数字骗了」，是**「拿一个只证明接线的数去支撑一个关于效果的结论」**，而这两件事在自己脑子里
很容易并成一句话。收到这类数字的一方要追一句：这个量还能是别的值吗？

**诚实边界**：前 6 种坏法出自同一项目、项目内各自独立复现；第 7 种（量具把自己算进被测对象）出自**另一个项目**——
所以「量具先自证」这条原则本身已跨 2 项目命中，但每种具体坏法仍是单次，apply-and-refine。发规格 / 发期望值表那一侧的
对称条目见 [`worker-instructions.md`](worker-instructions.md) 的「记号歧义」。

## 三条流程约束：机械动作会替你发现你没想到的问题

上面「量具先自证」里那条（理论端点 → 接线证据）和下面这些有同一个形状：**它们都不是「要记得想到 X」，
而是「做 X 这个动作会强制你发现」**。这个区别决定了怎么写它们——

⚠️ **这类条目只在「你真的去写 / 真的去量」时生效，对「我看了一眼觉得没问题」完全无效。** 所以要写成
**必须做的动作**，不能写成「要记得想到的事」：后者会退化成一句没人执行的箴言，而且退化时毫无声响。

### ⚠️ 「写成动作」还不够：动作可以被自认为做过，**判据**才留痕

上面那条说「写成必须做的动作」。实测出它还有一个缺口：**动作本身仍然可以被自认为做过。**

| 写成动作（可自认做过） | 写成判据（留痕、可核） |
|---|---|
| 重量一个旧数字前，**先确认**量的是不是同一个量 | **新旧两份配置清单逐项相同**（把旧配置逐项抄出来，照抄跑一遍） |
| 测试的前提条件**要记得**成立 | 前提**写成断言**（注释不参与执行） |
| 报数之前**保持警觉** | **顺手加一个对照组** |

机制：**「我记得」和「我核过」在回忆里长得一模一样。** ⇒ 判断一条纪律写好没写好，问一句：
**没做的时候，看得出来吗？**

三条推论，各自实测：

- **对照比怀疑便宜，而且它在你没起疑时也生效。** 怀疑要先有理由，对照不用 ⇒ 「顺手加对照」的期望
  收益高于「保持警觉」。同一轮里正反两面各一次：一方**有**理由怀疑一个数（两处数字三位有效数字相同）
  却没等疑点落地就转发了；另一方**没有**怀疑那个探针、只是顺手打印了不挂算子的基线，于是发现
  **整个探针在当前配置下不可能起作用**（否则会得到一个"已排除"的错结论）。
- **发现了疑点却先转发，比没发现疑点更糟。** 区别不在动机，在于那条信息**存在过但没传**——这是所有
  污染形态里最贵的一种：本可零成本阻止，且**事后无痕**（没人知道你当时怀疑过）。⇒ **「我有理由怀疑
  这个数」与「我把这个数转出去」之间必须是先后关系，不能并行。**
- **绊线要连它的作用域一起写。** 一条绿着的断言会被读成「这一维已被守住」，而它守住的往往只是该维的
  **一种**失效形态（实测：`max > 阈值` 抓得住「整体被抹平」，抓不到「部分退化」）。⚠️ 修法是**写下
  作用域，不是扩大判据**——逐元素判据会在无关改动上误报，而误报几次之后人就开始忽略它，那条绊线
  等于没了。

**诚实边界**：三条出自同一批跨对话协作（两个项目、三方），机制清楚且可复述，但**未跨人 / 跨团队验证**。
apply-and-refine。

### 写一条可证伪的断言，会强制你去查你本来会照抄的前提

实测形态：一个渲染特性从既有代码路径派生出一个新分支。既有路径上有一个补偿参数（用来消除两层几何
之间的深度冲突）。新分支「要不要照抄这个参数」——照抄看起来是安全的默认。

真正的答案不是「要」或「不要」，而是**问题问错了**：新分支所在的通道**不写深度**，那个参数存在的
唯一前提（「两层几何要争同一份深度」）根本不成立。照抄不是保守，是错的。

而发现这一点的**不是想清楚**，是**被逼的**：作者要给新分支写一条可证伪的断言，就必须先答「这个参数
在这里应该是什么」，一答就撞上前提。他自己的说法是：

> 我不是想到「前提不成立」才那么写的，是写 gate 的时候被逼出来的。

机制：**你没法给一个自己都说不清前提的东西写断言。** 所以「写断言」这个动作会自动把你推到前提上去——
而「读一遍觉得没问题」不会。这也是「先写 check 再写实现」除了 TDD 那套理由之外的一个独立收益：它是
一台**前提探测器**。

推论（可直接用）：**一处代码从既有路径复制而来时，给它写一条断言，而不是读一遍确认「跟原来一样」。**
断言会逼你说出它该是什么值；「跟原来一样」不会。

⚠️ **边界（同一项目当天就补了这一刀，值得跟上面那条一起读）**：
**「查前提」必须查到可观测的实际状态，不能查到注释 / 设计意图 / 邻居写法为止。**

那三个词是**递进**的——越往后越像「我已经查到实际了」，而三个都不是：

| 查到哪就停了 | 为什么会停在这 |
|---|---|
| **注释** | 它就贴在那行代码旁边，理直气壮地说明它在干什么 |
| **设计意图**（设计稿 / 提案 / 那个模块的整体说明） | 更权威，而且跟注释一致——两处互相印证，于是显得更可信 |
| **邻居写法**（同一段里同族 API 怎么写的） | **最狠**：前两个至少还是「文档」，而邻居是**代码** —— 人会想「我参考的是实际代码，不是文档」，于是**误以为自己已经查到实际层了** |

只有**读回来 / 量一下**才是实际状态。

同一个特性上，作者**确实查了前提**（「这个渲染通道不写深度」）——查的是**注释写的**那个，而那行注释理直气壮地
写着它在干什么。实际状态相反：关闭深度写的那行**是空操作**（该属性挂在 framebuffer 对象上，不在 context 上；
给 context 赋一个不存在的属性**静默成功**，库也不报错），于是整个通道从那行代码写下之日起**一直在写深度**，
静默活了整个特性的生命周期。

**最坏的一层是「邻居写法」**：同一段代码里同族的另外两个状态（深度比较函数 / 混合函数）**确实**在 context 上
（实测：context 有、framebuffer 没有），唯独这一个反过来。所以那行代码有注释、有配对的 True/False、有明确
设计意图、**还跟紧挨着的邻居写法完全一致** —— 样样都对，只是不生效。⇒ **「跟邻居一致」在这里是反向信号：
同族 API 也可能不同族。**

##### 「邻居写法」已跨项目两击（不同技术域、机制同一）

第二击来自另一个项目、另一个技术域（框架的日志 API）：同一个源文件里，静态数据的错误走「每次都落」的
API，帧数据的错误走「按 key 去重、只落首次」的 API —— 相距 200 行、**同一个日志类、同一种严重级别、
消息文本几乎一模一样**（只差 static/frame 一个词），**行为相反**。按「旁边那条是怎么记的」去解释日志频次，
必然错（那次差一步把 1800 次事件报成「只发生一次、偶发」）。

⇒ 两次机制同一：**同族 API 在关键维度上不同族，且样样看起来都对**（同类名、同签名形态、同上下文、
措辞几乎一致）。两次的技术域完全不同（图形状态 API / 日志 API），所以这不是某个库的怪癖。

⚠️ **两次都是人读源码时发现的，没有一次被机械 check 抓住** —— 修法仍然只有「去查权威定义」。
**别把这条写成能自动化的规矩**：它没有 gate 形态，只有一个必须由人执行的动作。

#### 还有第四级：读回来了，但读的是**错的对象**

上表列的是「停在哪一层」。还有一种更靠后的失败：**你确实读回来了，只是读的不是权威对象** ——
它看起来已经是「量了实际值」，所以比前三级都难自查。

实测（同一个空操作赋值）：`ctx.depth_mask = False` 之后**读回来还是 `False`** —— 该属性不在 `Context` 上，
而那个动态语言把它当普通属性存下了（实测该库七个类无一有 `__slots__`）。于是「设了 → 读回确认 → 一致」
这条**完整的验证链全程绿**，而硬件状态从未改变。

⇒ **读回必须读权威对象。在错误的对象上读回不是「没查」，是自我印证** —— 它比不查更坏，因为它
**产出一个「我验过了」的假凭据**。可执行的问法：读回之前先问「这个状态的**权威持有者**是谁」
（那次是 framebuffer 而不是 context）。

可执行的问法：**「我刚才那行，真的改到实际状态了吗」**——然后**读回来确认**。对「设了不生效也不报错」的 API
（GL / 驱动层状态、动态语言里给不存在的属性赋值、某些 ORM 的字段写入）这一问值得成为习惯。它跟本文件
「量具先自证」那族**差一层**：那族是「判据 / 量具错了」，这条是**执行根本没发生** —— 所以可证伪的方式也不同，
不是「换个量法再测一次」，而是「读回实际状态」。

同一轮里派生的两条，都可以直接用：

- **断言正确、解释错误的 check，比没有解释更糟。** 那次的 gate 断言是对的（不该加那个补偿参数），
  docstring 给的理由是错的（引用了那个不成立的前提）。下一个人读到它会以为这块已经想清楚了。
  ⇒ 跟上面那条规矩配对：**「已解」由说明产出时，那个说明本身会被固化进注释 / 文档 / check 的 docstring，
  于是错误获得权威外观。** 代价不是「漏一个 bug」，是「漏一个 bug **+** 种下一条读起来很对的错误解释」。
- **在坏地基上加补偿层，比不修更贵。** 有人（本文作者一方）提议用局部补偿绕过症状——把另一层往反方向推。
  思路成立，但它补偿的**正是那个 bug**；根因被修好那天，补偿就变成净偏移开始产生新错误，**而那天没人会把
  两件事联系起来**。⇒ 只做根因修法，不做依赖 bug 的局部绕行。

**诚实边界**：以上各条都出自同一项目、各一次，但机制清楚且可复述（不是「试了一次成功」）——apply-and-refine。
第一条与「量具先自证」的信号表是同一族，那条已跨 2 项目命中。

### 给每个 claim 打证据等级，会强制你发现哪些 claim 你其实**没有任何证据**

第三个同形态的机械动作（前两个是「写可证伪的断言」和「理论端点 → 接线证据」）：**给你要报出去的每一条
claim 标一个证据等级**（实测 / 读自源码 / 推测）。机制跟前两条一样——**你没法给一个自己都没有证据的
claim 打上标签**，于是这个动作把「我含糊地觉得应该可以」逼成「这一条我压根没有任何等级可打」。

实测形态：一条被点名为「下游成立的关键前提」的问题，答之前先要标等级，一标才发现它既不是【实测】
也不是【源码】——真相是「我可达范围内零痕迹，而是否有人手工验过属于用户操作层面、我看不见」。
不做分级，回答很可能是「应该可以，官方样例就是这么设计的」，那会给一个已被点名为关键前提的判断
一个**虚假确定性**。

#### 必要条件：标签粒度必须 ≤ 断言粒度

这不是上面那条的补充，是它的**前提** —— 缺了它，打标签这个动作**失去探测能力**，只留下「我标了所以
我尽责了」的虚假安全感。

机制：一个复合断言（「A（强度≈官方文档+源码）**而且** B（纯推测、零证据）」）给**整句**打【推测】，
在整句层面**技术上正确**（合取式含一个推测成分，整句即推测）。而正是这种技术上正确掩盖了问题：读者
看到的是一个**方向正确**的结论，标签说「推测」会被读成整体不确定，而实际不确定性**全部集中在后半**、
前半接近确定 —— 于是**后半搭前半的便车获得了可信度**。

实测的失败形态：一条推测写成「characterize 要求 T-pose（真）**而** live 数据流入即**永久**关闭这个窗口
（零证据）」，整句标【推测】。接收方差一步答「证实了」—— 因为**结论方向确实对，错的只是那个「永久」**。
真相是保持 T-pose 就能重开窗口，即那半句有现成反例。若没被逐句核住，一条零证据的断言会以「已实测」
的身份进入语料库，**比漏掉一条候选糟得多**：它之后污染所有引用，且无痕。

⇒ 可执行规则：**证据等级要打在能被独立证伪的最小断言上，不是打在整句上。** 含连接词（而 / 因此 /
所以 / 即）或**强限定词**（**永久 / 总是 / 从不 / 任何 / 必然**）的句子**先拆再逐段打标签**。强限定词是
重点信号 —— 它们写起来**免费**、验证起来**极难**，所以最容易搭便车。

**诚实边界**：单项目、各一次。前半条（打标签是前提探测器）的原始证据是当事人自陈，无对照组；
第三方即刻套用它拆分自己的答案这件事只支持「规则可操作、表述清楚」，**不支持「规则有拦截力」**
（那个人本来可能也会拆）。后半条（粒度）有一个实际的失败案例，靠接收方逐句核才拦住。
发规格那一侧的对称条目见 [`worker-instructions.md`](worker-instructions.md)「self-contained ≠ correct」
（那节写的是供给侧标 verified vs assumption；本条补上**需求侧也能下这个 discipline** —— 提问时就要求分级）。

## 否定式约束是 LLM review 的结构性盲区 → 配确定性 check

LLM **系统性地弱于否定**：处理否定语句（"不要 X" / negated constraint）显著差于肯定语句。所以让 LLM 当审查员核"合不合规"时，**写成 `DO NOT ...` 的约束是它最容易 false-negative 的地方**——代码违反了否定约束，LLM review 读着读着把"不要"忽略了，照样判"通过"。

推论：**否定式约束不能只靠 LLM review 兜，必须配一个确定性检查**（grep / lint / 断言 / [`enumerate-then-adjudicate.md`](enumerate-then-adjudicate.md) 的机械枚举）。这跟上面的 oracle/mechanical-check 阶梯是一体的——否定约束正是"手写期望值不可靠、要上 mechanical oracle"的高发点；也跟 [`fact-forcing-gate.md`](fact-forcing-gate.md) 的 advisory vs hard 对齐：否定约束是"advisory review 兜不住、需要 hard gate"的典型。

- **既定事实**（可引）：LLM 弱于否定 —— Truong, Baldwin, Verspoor & Cohn (2023),《Language models are not naysayers: An analysis of language models on negation benchmarks》(\*SEM 2023, https://aclanthology.org/2023.starsem-1.10/)：直接对比肯定 vs 否定，记录否定 benchmark 上低于随机 + inverse scaling。
- **约束翻转机制**（可引）：Elkins & Chun (2026),《Auditing Negation Sensitivity in Moral Dilemmas》(https://arxiv.org/abs/2601.21433)：模型在同一提案被措辞成"禁止"时会翻转合规判断。
- **诚实边界**："LLM review 对 DO-NOT 约束 false-negative"这一步是**合理推论**——上述研究未直接 benchmark "LLM 审代码/spec 的 DO-NOT 合规"这个确切任务。正因为是推论而非实测，才更该上确定性检查兜底。

## Adversarial Probes

Choose probes relevant to the change:

- **Concurrency**: Send parallel requests to creation endpoints -- check for duplicates or data loss
- **Boundary values**: Test with 0, -1, empty string, very long string, unicode, MAX_INT
- **Idempotency**: Send the same mutation request twice -- is the result correct?
- **Orphan references**: Delete or reference a non-existent ID -- does the system handle it gracefully?

## Evidence Format

Each verification item should include:

1. What was checked
2. The actual command run
3. The actual output observed (copy-paste, not paraphrased)
4. Result: PASS or FAIL (with expected vs actual if FAIL)

**Anti-pattern**: "I read the code and the logic correctly validates..." -- this is not evidence. Evidence requires running a command.

## LLM-as-judge 评测（评 agent / 研究类输出）

当要评的是 **agent 生成的输出 / 研究报告 / 难以写确定性断言**的产物（不像代码可跑测试）时，Anthropic 实测**最稳、最贴合人工判断**的方式是：**单次 LLM 调用 + 单个 prompt**，按 rubric 输出 **0.0–1.0 分 + pass/fail**。比多次调用 / 多 judge 投票更一致。

rubric 五维（可裁剪）：

- **事实准确**（claim 与来源一致）
- **引用准确**（引用的源确实支持该 claim）
- **完整性**（要求的方面都覆盖）
- **源质量**（优先一手源 over 二手）
- **工具效率**（用了对的工具、次数合理）

适用：评 research / digest 输出、评一段 agent 自动改动是否达标、给「难以单测」的产物一个可复现评分。**不适用**：能写确定性断言的代码——那走前面的「运行命令 + 对抗探针」。

> 来源：Anthropic [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)。

### De-anchored Judge：先独立判定，再查看候选

普通的 LLM-as-judge 流程把任务和候选产物一起交给 judge。候选产物的叙述方式可能把 judge 锚定在“看起来合理”上，让它评估 plausibility，而不是独立判断 correctness。对复杂代码评审、研究报告和没有现成标准答案的验收，不要只依赖这种单阶段顺序。

采用两阶段流程：

```text
Phase A：只提供任务、契约和验收标准
  → judge 独立推导预期行为、关键不变量、边界和失败条件，并固定输出
Phase B：再提供候选 patch / 答案 / 报告
  → judge 逐项对照 Phase A 的判据，记录通过、失败、遗漏和未决风险
```

执行约束：

1. Phase A 不得包含候选答案、候选 patch 或候选报告；否则独立判定已经被锚定。
2. Phase A 至少固定三类内容：预期结果、关键不变量、能使判定失败的反例或边界条件。代码任务还应先列出可运行的测试、reference 或 invariant oracle。
3. Phase B 必须引用 Phase A 的具体判据逐项比较，不能用“整体看起来合理”替代对照；无法从独立判据判断的项目标为未决，不要强行通过。
4. De-anchoring 是评审顺序的增强，不是确定性验证的替代。能用编译、测试、round-trip、差分 reference 或不变量直接判定时，优先运行这些 oracle；LLM judge 只补充它们覆盖不到的部分。
5. 这通常增加一次独立推理成本，且独立 judge 自身仍可能出错；只在候选内容容易影响判断、又缺少更强外部 oracle 时启用，不要给简单格式检查机械加一轮 LLM。

来源：[`More Convincing, Not More Correct: Self-Play Reward Hacking of Reference-Free LLM Judges`](https://arxiv.org/abs/2607.05904)（2026 年 arXiv v1 预印本；实验主要来自 GSM8K / Qwen3）。该研究支持“候选条件化可能让 judge 奖励 plausibility 而非 correctness”这一机制，但其 false-positive 数字不能直接外推到本仓库的 C++、UE 或 Python 任务；落地前应做本地 A/B 复现。

## Diagnostic Log Discipline

When debugging a bug that requires adding diagnostic logs:

- **Do not remove diagnostic logs until the user confirms the fix works.** A premature
  cleanup forces re-adding the same logs if the fix turns out to be wrong.
- Add logs, build, let the user reproduce, read the logs, propose a fix, build again —
  but keep the logs in place.
- Only remove logs in a separate cleanup step after the user explicitly confirms the
  issue is resolved.

## Completion Checklist

Before reporting verification complete:

- [ ] At least one command was run with actual output shown
- [ ] At least one adversarial probe was attempted
- [ ] At least one non-happy-path scenario was tested
- [ ] No "the code looks correct" reasoning was used as a substitute for running commands

## Related Guidelines

- See `guidelines/code/validation.md` for the declarative principles behind this technique.
- [`techniques/enumerate-then-adjudicate.md`](enumerate-then-adjudicate.md) —— "选可信 check" 的一个具体落地：把"让 LLM 找全所有 X"这个静默失败换成"机械枚举候选 + LLM 逐条裁决"。
- [`techniques/coordination-patterns.md`](coordination-patterns.md) —— 无 oracle 时怎么隔离一个独立 checker（fresh worker / 从契约推导）。
- [`techniques/blackbox-api-characterization.md`](blackbox-api-characterization.md) —— **对称的另一半**（懒加载）：本份管"我改的东西对不对"，那份管"别人的闭源黑箱是什么语义"。上面「metric 选错」那节是那份「扫了没反应的五种原因」里的第 5 种（也是最危险的一种，因为它给出**反向**结论）；「四要素」的 Independent 在那边落成"优先找厂商自己的返回值 / 库自己填好的对应关系,别急着做因果实验"。
