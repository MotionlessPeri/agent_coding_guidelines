# 测试要有目的:钉行为,不测结构

## 核心规则

一条测试要挣得存在,必须钉住一条**你关心的行为**(功能 / 流程上的一个 guarantee),不是复述代码的**结构**(方法名 / 成员名 / 字段 / 私有实现 / 调用顺序)。测结构的测试是**负资产**——重构一动就红,却抓不到真 bug,占维护成本、拖慢套件,最后大家干脆不跑。

判据来自 Google *Software Engineering at Google* 第 12 章:"write a test for each **behavior** ... A behavior is any guarantee that a system makes about how it will respond to a series of inputs while in a particular state." 通过 public API / 契约去测,像使用者那样调用——这样"能让测试变红的改动,通常也真的破坏了使用者"。

统一线索(本条的思想骨架):**测试 / spec 钉的是行为,代码是承载行为的可替换结构。** 所以测结构的测试无意义、且代码一重写就崩;而测行为的测试跨重写仍然成立。

这条跟 [`validation.md`](validation.md)(看代码 ≠ 验证)、[`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)(check 可不可信)**正交且互补**:那两条管"给定要测 X,怎么测得可信";本条管"到底该不该测 X、该测哪条行为"(目的这一轴)。

## 测试目的性 gate:5 问

写 / 审一条测试,逐条过这 5 问;过不了就删或改:

1. **它钉的是哪条行为?** —— 答不出具体行为(只能说"测这个函数 / 这个类") → 多半在测结构,删。
2. **这条行为在哪个模块边界 / public API 上可观察?** —— 决定测试放哪层(见下)。私有实现细节不该有专门测试。
3. **代码重写之后它还该通过吗?** —— 不该(名字 / 结构变就红)= 测错对象;该(行为不变就绿)= 对。这是判断测对没测对**最锋利的一刀**。
4. **注入一个真 bug,它会红吗?** —— 不会 = 这条断言不可证伪(空断言 / 复述实现 / 自证):无论对错都绿。可证伪(Falsifiable)是 MFIC 四要素之一,mutation testing 量化它——test 能 kill mutant 才算真能抓错(见 adversarial-verification)。
5. **为了让它能测,我扭曲 production 设计了吗?** —— 扭曲了(加一堆 indirection / mock 纯为隔离)就退到**粗粒度层**测,别损设计(DHH "Test-induced design damage":"you let your design drive your tests",不是反过来)。

## 流程图 = 测试目的性地图

"该测哪些行为"不是凭空定的——**项目的流程图(mermaid sequence / flowchart 等)就是行为清单**。图上每个有意义的 behavior / 分支值得一条测试;图外的内部结构一律不测。这把"测试挂到功能和流程"落成可操作:**一条测试挣得存在 ⟺ 它钉的行为出现在你画的某条 flow 上**。给成员命名写的 test 不在任何 flow 上 → 无意义。

## 该测在哪一层

| 内容 | 层 | 理由 |
|---|---|---|
| 纯逻辑 / 算法 | unit(测试金字塔底) | 快 + 隔离(Fowler, TestPyramid) |
| 接线 / 边界 / 真实用法 | integration | 信心 / 成本比最高(Kent C. Dodds, Testing Trophy:"Write tests. Not too many. Mostly integration.") |
| 少数关键用户旅程 | 稀疏 E2E | E2E 脆、慢、不确定;堆多了成 ice-cream cone 反模式 |

**DHH 例外**:好设计有时**就是**抗单测(HTML 渲染、GPU / 渲染路径、DCC 视口)。这时退到粗粒度层测,或用 fixture + 人工用例兜底(见 skill `tdd-with-fixtures` 的 escape hatch + [`gui-visual-machine-gating.md`](gui-visual-machine-gating.md):机器 gate 压渲染无关纯逻辑,画面交人工)。"难单测 ⇒ 烂设计"是启发式,不是铁律。

## 覆盖率不是目标

覆盖率是**找漏测的探照灯,不是质量指标**(Fowler, TestCoverage:"Test coverage is a useful tool for finding untested parts of a codebase. Test coverage is of little use as a numeric statement of how good your tests are.")。把覆盖率当 KPI = Goodhart 定律:会诱导 assertion-free 测试 + trivial 测试凑数(AI 尤其爱这么干)。衡量测试真能不能抓到 bug,看 **mutation score**,不看覆盖率数字。

## ⚠️ 测试名 / 注释的作用域,必须等于断言的作用域

一条**通过**的测试会替一个**错误理解**背书 —— 而这比没有测试更糟,因为下一个人读到它会以为这块已经想清楚了。

机制:断言验的永远是「**在这份 fixture 下**」,而名字和注释会被读成「**总是**」。两者作用域一旦不等,差额就变成
一句无人质疑的错误断言,而**测试是绿的,没有任何信号**。

实测两种形态:

| 形态 | 实例 |
|---|---|
| **名字说「总是」,断言只验了「这份 fixture 下」** | 一个算子的测试叫 `ZeroAlphaIsIdentity`、注释写「Alpha=0 时整个算子恒等」。真相:该 Alpha **只作用于旋转**,平移增量**无条件**施加 ⇒ 只在 fixture 恰好没有平移增量时才恒等。**那个名字在任何带平移增量的场景下都是错的。** |
| **绊线的作用域窄于它被读成的那个** | 一条防「fixture 退化」的前提断言写成 `max(静止旋转) > 30°`。它抓得住**整体被抹平**,抓不到**部分退化**(清零 6 根只留 1 根仍过关,而分辨力已掉大半)。⚠️ 修法是**写下作用域,不是扩大判据** —— 逐元素判据会在无关改动上误报,而误报几次之后人就开始忽略它,那条绊线等于没了。 |

两条可直接执行:

- **命名**:断言只在某前提下成立时,名字里带上那个前提(`ZeroAlphaIsIdentity` → `ZeroAlphaStopsRotationOnly`),
  或把注释写成「本测试只验 X,不验 Y」。**别让名字承诺断言没验的东西。**
- **前提**:「这份 fixture 是不是我以为的那份」**要靠前提断言来钉,不能靠注释** —— 注释不参与执行。
  前提断言还有一层额外收益:**它的价值会外溢到它本来不负责的地方**。阈值断言只回答「够不够」,前提断言
  回答「这个场景是不是我以为的那个场景」,而**只有后者照得见量级错误**。实测:一次量级错 6 倍的数据,
  所有阈值断言(`>0` / `==0`)全绿,最后是另一个功能为**别的目的**写的一条前提断言顺手照出来的。

**诚实边界**:出自同一批跨对话协作(两项目、三方),机制清楚可复述,**未跨人 / 跨团队验证**。apply-and-refine。

## Anti-Patterns

| 反 pattern | 为什么错 | 修法 |
|---|---|---|
| 测试名 / 注释说「总是」,断言只验了「这份 fixture 下」 | 一条通过的测试替错误理解背书,而且是绿的、无信号 | 名字带上前提;「fixture 是不是我以为的那份」用前提断言钉,别用注释 |
| 给每个方法 / 成员 / 字段名写测试 | 测结构,重构就红,抓不到 bug(change-detector test) | 按 behavior 测,不按 method 测 |
| 测 getter / setter / 常量 / 框架 / 三方库 | trivial,零信息,拖慢套件 | 只测你自己的、有意义的行为 |
| assertion-free / 复述实现的测试 | 不可证伪,任何 bug 都不红 | 用独立 oracle(round-trip / 不变量 / reference),别复述代码 |
| 为凑覆盖率写测试 | Goodhart,数字好看没牙 | 覆盖率只当探照灯;看 mutation score |
| 为了单测把设计加一堆 indirection / mock | test-induced design damage | 退粗粒度层测,别损设计 |
| UI / E2E 测试堆成山 | 脆 / 慢 / 不确定(ice-cream cone) | 金字塔 / 奖杯:多 unit + integration,少 E2E |
| AI"帮你补测试"补出一堆 trivial | 覆盖率上去了,套件反成负资产 | 5 问 gate 逐条过,砍掉没目的的 |

## 一个诚实的边界

"不测 trivial 代码"不是绝对的(Mark Seemann 有过反论:TDD 流程里顺手测 trivial 代码有时也合理)。本条的重心是**目的**——测试为你关心的行为提供信心,不是为数字、不是为结构。Beck 的一句话是尺度:"I get paid for code that works, not for tests, so my philosophy is to test as little as possible to reach a given level of confidence." 测试价值 = **每份维护成本换来的信心**。

## 项目实例参考

某 UE 项目 agent 主动给一个类的**每个成员命名**写了 test case——覆盖率上去了,但一 refactor 就全红,且从未抓到任何行为退化。典型的"测结构不测行为"+"为覆盖率凑数"。按本条:这些测试全不该存在(过不了 5 问的第 1、3、4 问)。

## 相关 Guidelines / Techniques / Skills

- [`validation.md`](validation.md) —— 看代码 ≠ 验证;本条管"该不该测 / 测哪条",那条管"验证要跑命令看输出"
- [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md) —— MFIC "falsifiable" = 牙、oracle 阶梯、mutation;本条 Q4 用它,两者正交(信任轴 vs 目的轴)
- [`gui-visual-machine-gating.md`](gui-visual-machine-gating.md) —— DHH 例外在 GUI / 渲染的落地(机器 gate 压纯逻辑,画面交人工)
- skill `tdd-with-fixtures` —— 自动测试覆盖不到的行为的 fixture + 人工用例 escape hatch
- skill `bugfix-tdd` / `superpowers:test-driven-development` —— 红 → 绿 discipline(怎么写);本条管"写不写、写哪条"
- [`function-clarity.md`](function-clarity.md) —— 模块 / 函数拆分改善可测性(但受 DHH 例外约束)
- [`constraints.md`](constraints.md) "Simplicity" —— 反过度工程;本条是它在测试维度的应用(反过度测试)

> 背景讨论(非规则):AI 时代"code 作为可重生产物"的可行度是个经济学 crossover,取决于(a)重生的成本 + 确定性、(b)架构能被表达成可执行约束的比例。本条只主张一件已确立的工程共识——测试钉行为不测结构;至于代码该不该当可重生产物,分歧点在"架构能否不靠人读代码来机械保证",随 AI 成本与约束表达力移动,不在本条断言范围内。
