---
name: role-lane-coordination
description: 把一个较重的项目拆到**多个常驻对话**(每个对话 = 一条 role-lane / context 边界)并协调它们时用。覆盖:role(持久 lane)⊥ task 拆对话、seam-contract 协同设计、分档 oracle(hard gate / advisory / park)门控自主、notify/act 自主度旋钮 + checkpoint、**唤醒机制**(有 Lane Router 时走事件通知;无 Router 时按预估 ETA 轮询 / 人推)、**分档路由**(结构化走 hub / 领域重·紧耦合人眼直连用户)、跨 lane 汇合用单一 coordinator 宿主、**brief 正确性≠完整性**、durable 文件抗失忆、**收件箱按发件人消歧 + ack 约定**、**一组 lane 的轮换**(协调者最后转 + 时机三项合取 + 许可不经 lane 通道 + handoff 会被 rotate 消费)。**跳过**:单对话任务;同 repo lease/inbox hook 底层(那是 `multi-session-coordination`,本 skill 同 repo 时复用它)。**方法论验证边界 = 同机 + 共享绝对路径 mailbox + 人作异步决策层**;已跨 **2 项目 / 2 拓扑**验证(平级 peer + 跨 repo hub+fan-out)。**真分布式(跨机 / 无共享盘 / 跨人)未覆盖,别假设 skill 管它。**
---

# 多对话项目协调(role-lane + seam-contract + 分档 oracle)

一个较重项目,要多个对话分工又要它们协同时,用这套。核心区别于 persona 戏:**价值来自 context 边界 + 分工 + 契约 + oracle,不是给对话套人设**。

## 术语

| 词 | 释义 |
|---|---|
| **lane / role** | 一条持久的 context 域(如 core / UI / 某后端),一个常驻对话负责 |
| **task** | 流过 lane 的工作单元(调研 / 实现 / 修 bug);role ⊥ task,矩阵组合,不冲突 |
| **seam** | 两 lane 交界;每 seam 一份 contract |
| **contract** | seam 上的接口约定 + **它的 oracle** |
| **oracle** | 能自动判对错的独立判据(不是文字规范,是能跑能拦的裁判) |
| **mailbox / 结果区** | 对话间异步消息 / 主动发的 profile·结果 |
| **家(home)** | contract + oracle 的存放处;位置写进 manifest,不写死 |
| **coordinator / hub** | 跨 lane 汇合时拥共享接线(main/build/汇合点)的那个 lane;多 repo 时每侧一个、只经一条 seam 对接 |

## 方法(已验证的核)

1. **按 context 边界分 lane,不按 persona**。一 lane = 一常驻对话。专家性从积累的域上下文长出来。
2. **seam = 契约**。每条 seam 一份 contract,连它的 oracle 一起定,住共享**家**。契约要**完整**——别留"MoBu 事实↔核心库命名"这类缺口逼 dev 自己去读源码补。
3. **通信 = 异步 mailbox + 共享结果区**:mailbox **递证据 / 递一条失败 oracle,不递意见**;处理完移 `resolved/`。结果区**主动发** profile/benchmark(没硬 oracle 的软分歧靠"两边结果摆一起"一眼见)。无 Router 的文件约定要**按发件人消歧**——`to-<lane>/` 定向 + 命名带发件人前缀,别让收件方"打开才知道是不是给自己的";**ack 约定二选一定死**(回原 lane 一条 ack / 静默归档到 `resolved/`),别留语义不定让人交叉核验"我的 done 有没有丢"。使用 Lane Router 时不要再造一套目录和 ack 约定:sender/target 在消息头里,处理完成后一律 `lane_ack`。
4. **唤醒机制必须显式解决**。环境已接入 Lane Router 时,优先用它的事件通知 + 持久 mailbox,不要再叠一套常驻 Monitor 或手写轮询;安装、四项工具、收件与 ack 见 [`techniques/lane-router.md`](../../../techniques/lane-router.md)。没有 Lane Router 时,文件 mailbox 本身没有"新消息"通知原语:**传输**(文件落盘)自动即时;但 **act 要对面对话在跑** = 靠唤醒。等别人任务的对话**先预估"对方这活大概多久"→ 按那个量级定 poll cadence**(等 30min 的活别 60s 猛轮),或直接跟对方 lane 协商 cadence;**人推醒作 fallback**。⚠️ **长跑事件 Monitor 会资源耗尽而死**(实测 exit `0xC000026B`)→ 别指望常驻事件监听,用 **CronCreate / ScheduleWakeup 定时轮询兜底**。自主 lane 的推荐实现是**让 `/loop` dynamic 当 lane 的驱动器**(不只当 mailbox 轮询器):每次 wake 固定做扫 `to-<lane>/` inbox → 推进自己 backlog(读 brief / TDD / commit / 回 ping)→ 以 `ScheduleWakeup` 收尾。"轮询别人"和"推进自己"合成一条循环,人插的消息也走同一通道(进对话 → 下次 wake 捡起 = 提前唤醒),不必另设一套。**不用 `/goal`**:lane 常驻、无终态完成条件;`/goal` 的判官只看对话输出、读不到 mailbox 文件;且它是 Stop hook——按住回合不放,跟"结束回合等下次唤醒"正相反(推自选择表,未实测)。机制细节 / delaySeconds 选值 / stop 纪律见 `guidelines/claude-code/autonomous-loop-scheduling.md`(Claude Code 专属)。**fallback 轮询这段单项目单拓扑验证,apply-and-refine。**
5. **oracle 三档,门控自主**:hard(代码 gate,**授权 auto-act**)/ advisory(fresh 对话 judge,只提醒)/ none(**park 给人**)。铁律:**auto-act 只在 hard 后面;oracle 覆盖率 = 能安全自主的面积**。(实测最强一环:golden 全绿 → hub 自主 commit,正确性不需人 gate。)
6. **自主度 = 拓扑旋钮**:**notify**(propose→你拍板,peer,你在场)/ **act**(oracle-gated 自动 + park,coordinator 拥 goal)。**checkpoint 落在人判断点**(契约 settle / 集成前 / 画面验)。
7. **park-and-continue**:碰只有人能定 / 无 oracle / 跨 lane 分歧 → 写 `parked/` 注明,**继续做别的,别卡住、别乱猜、别 fabricate**。loop 驱动时**park 还是停 loop,看 backlog 有没有别的活**:有 → park 这项、loop 继续;卡住的这项**就是** backlog(或剩下的都依赖这个决定)→ **停 loop** + 写 flag(根因 + 备选 + 需要谁定什么)+ 通知人,别让 loop 在只能等人的点上反复醒来。(`/goal` 驱动时没有"停 loop"这个动作——Stop hook 拦着,唯一出口是把 park 预先写进条件文本。)
8. **跨 lane 汇合 → 单一 coordinator 宿主**(拥共享 main/build/汇合点),**不是并行 peer**(peer 抢共享文件会 thrash)。宿主选拥自然汇合点的 lane。每块 production surface 仍只有一个明确 owner;coordinator 负责裁决与路由,不另建一套影子实现。**分档路由**:**结构化契约任务走 hub**(self-contained brief → 零往返);**领域知识重 / 紧耦合人眼(视觉·DCC)任务 → dev 直连用户/权威,别强穿 hub**(hub 缺该领域知识时经它转是**有损一跳**)。hub 的活 = **识别任务类型 + 早放行**,不是无差别转发;hub **报症状不定实现、下结论先读真代码**(远离 dev 代码易误诊)。
9. **brief 正确性 ≠ 完整性**:brief self-contained(完整)还不够——**标清"我的假设(未证实)" vs "已验证 oracle(附 dump)",证据/oracle 随任务下发,不只发结论**。(最高价值教训:自信但错的 ground-truth baked 进完整 brief,每次纠错一整轮。见 `worker-instructions.md`。)🛑 **而证据等级不是那条断言的性质,是「断言 + 谁手上拿着它」的性质**:同一句「测试 1301 全绿」在跑它的那条 lane 是【实测】,在收到它的协调者那里是【自报转述】,再转一手就是转述的转述 —— **转述让等级降一档,而句子里没有任何地方记录这次降级**。⇒ ⇒ 📌 **对协调者尤其要紧:它是链上转述最多的那个位置** ⇒ 「N 条 lane 都报了 X」最容易把 N 个自报升格成 N 个实测。判据:**要说【已核】,得有人把输出贴出来、或者核的人自己重跑一次**;否则准确说法是「一个我手上有输出、其余是自报」。⇒ 而含连接词的复合断言(「我跑了**也**你跑了」)**先拆再逐段标等级**,别给整句贴一个。再往下一层:claim 全对、oracle 也给了,**记号本身仍会走样**——公式带符号写死正方向 / 「增量」写清相对什么 / 作用域写标识符不写自然语言 / oracle 表预先点出哪些数不该拿来验(同一轮命中 3 次,详见同一份 `worker-instructions.md` 的「记号歧义」)。
10. **durable 文件抗对话失忆**:contract = 项目记忆、worklog/resume-point = 工作记忆(补 guidelines 的 playbook 记忆)。**每增量 commit + 追加 worklog**。(实测真救过一次:某 dev 对话工具抽风误 rm 任务 + 捏造任务,靠 mailbox durable 记录重投递恢复。)跨 lane commit 顺序是硬约束:下游 import 上游未入库模块会被卡 → 上游先 commit / 或 hub 合成单 commit。

11. **一组 lane 的轮换:协调者最后转**。**时机**(三项合取,都可观察):① 本会话**已发生过** context 压缩(有系统标记 / 早期工具输出已不可逐字见)——🛑 **别写成「context 近上限」**,那有歧义:实测两条 lane 都去量了**会话 token 预算**,而要判的是 **context window**(两个数都对、都可测、都叫 context);② **压缩之后又积累了实质工作量**(①只证「某个时刻被超过」,不证「现在紧」);③ **处在自然收尾点**(无半成品 / 无待回执)。⇒ 📌 一般化:**不可观察的阈值,换成可观察的事件** —— lane 拿不到窗口占用率,协调者也拿不到(`lane_directory` 无此字段,且 `attachedAt` 零分辨力)。**顺序**:各 lane 先转、**协调者最后** —— 因为**协调者那份 handoff 承载拓扑**(各 lane 地址 + 状态 + 跨 lane 在办),别人那份只承载自己。**转前先落两处 durable,然后才调命令**:(a) 自己那部分待办进项目待办池(多 lane 共写时**按 lane 分节**);(b) handoff **先 copy 一份**进 durable 目录 —— 🛑 **`rotate` 会消费掉那个文件**,忘了另存**不报错、不留痕**。🛑 **许可各 lane 自己在对话里拿,协调者传不了**:lane 通道**传事实可以、传许可不行**(系统标它为不可信外部数据;Router 也明文要求 confirmation **in the conversation**)⇒ **「批准这个机制」≠「批准我现在按下去」**,而**逐字转述也不行**(问题在通道不在保真度)。🛑 **通知时把收件人列表写进正文**(不是记在心里):**「已通知全部」和「已通知我想到的那些」在回执里同一个样子**;写进正文之后**漏发对收件人可见**——选那个**失败会被别人看见**的形态。🛑 **显式传 `--terminal wt`**(默认档缺 wt 时**静默回退**、不聚窗无提示;显式传则报错)⇒ **想要的性质要显式声明,才拿得到「拿不到就报错」这个保证**;聚窗是 Router 行为,**各自转即可,不必汇总到某条 lane**。⇒ ℹ️ 上述每条的实测形态、踩过的具体坑与反例见 [`techniques/lane-router.md`](../../../techniques/lane-router.md) 的「一组 lane 轮换」节。**诚实边界**:单项目内多次、未跨项目;顺序那条的证据是机制(拓扑只在协调者手上)而非对照实验。


## 收尾纪律(完结协议)

用户宣布「完结」之后,lane 群常会再跑几十分钟到数小时的收尾往来。实测一场文档 campaign 的完结后流量约一半是真抓错(四处会伤到交付对象的事实错误,值得),另一半是结构性开销:复盘通胀(每封带「教训/一般化」并互相评注)、收口报告 N²(每 lane 向所有人报收口、别人再回复收口)、纯礼节消息(「我收/谢配合」零状态变化)、验证不分级(一个词的改动也触发全套重跑 + 造红 + 多方复核)。

完结令一下,协调方应**当场随终裁通告一并下发静默令**,五条:

1. **默认静默**:mailbox 只允许一类消息——会伤到交付对象的事实错误,格式 = 证据 + 修法一封,修完报一行。
2. **教训不走 mailbox**:各记各的 durable,不互评、不「我收」;跨 lane 汇总由协调方在下一个正常工作时段一次做。
3. **不回收口、不发纯致谢**:ack 机制本身就是回执;致谢并进最后一封实质消息的末行。
4. **验证分级**:改代码 = 全套;改文档事实 = 自验 + 一名复核;改措辞 = 改动方自核即止。
5. 交叉在飞、内容已被覆盖的消息**直接 ack 不回**。

判据不是「这封有没有价值」——被拦下的往往都有价值(真教训、真复核);判据是**「它现在必须发吗,还是可以进 durable 等下一个工作时段」**。这类往来有自我延续性:每一封「我收 + 补半句」都会引出对方的下一封,链只能靠不发第一封来断。

**诚实边界**:单项目一场(2026-08-31)+ 用户确认的 workflow discipline。

## setup

- **有 Lane Router**:manifest 只记录 lane 地址与 contract / oracle / 结果区的家;mailbox 路径和 ack 由 Router 管理,不要在项目里再建平行消息系统。具体操作见 [`techniques/lane-router.md`](../../../techniques/lane-router.md)。
- **无 Lane Router fallback**:manifest 记录参与者 + 各自 mailbox / 家 / 结果区**位置**。**operating model = 同机 + 共享 `~/.claude` 绝对路径**——多 repo 的对话各自 cwd 不同,但都用**绝对路径**读写同一条 mailbox(不分布 mailbox,集中到一条机器级路径)。
- **目录**:`contracts/`(seam stub)`oracles/` `mailbox/`(+ `to-<lane>/` + `resolved/`)`results/` `briefs/` `parked/` `lessons/`。
- **同 repo 多对话共享工作树** → 直接复用 `multi-session-coordination`(hook)。**多 repo(同机)** → 共享绝对路径 + manifest 指路(已验证)。

## 拓扑(两种已验证形态)

- **平级 peer**(renderer_test):N 条 lane 同 repo 平级,汇合期临时推一个 coordinator 宿主。
- **两级 hub + fan-out**(跨 repo 接入):每 repo 一个本地 hub,两 hub **只经一条 seam** 对接;hub 内再向本侧几个 dev fan-out。单 seam 把本侧 dev 跟对面完全隔离(dev 无跨 repo 认知负担)——也正因此,领域知识型任务经 hub 是有损一跳(见方法 8 分档路由)。

## phase 形状

- **Phase 1 = 契约 co-design**:各 lane 调研 → 发结果区 → 协同把 seam 契约从 stub 填 settled;人 review 契约。(实测独立 lane 常**独立撞到同一设计**。)
- **Phase 2 = oracle-gated 自主实现**:按契约 stub 邻居先做自己;oracle-first(红→绿),硬 oracle 绿才 commit,无 oracle 的 park。
- **Phase 3 = 集成**:coordinator 宿主收拢;端到端硬 oracle 重跑;画面 / 无 oracle 项交人眼。

## 实战校准

- **scope 靠 propose→approve 增长,不是 loop 自扩**:实测从极简 v1 扩到一堆 feature,但每步都是**对话推荐、人 green-light**(notify 档正常工作)。**scope 控制在"你的批准"层,不在 loop safety gate**——要收就在批准时收 / 显式冻结。
- **"错误结论的刹车"可由人 OR peer 的 oracle 纪律承担**:park-and-continue 覆盖不到**自主的错判**(误诊 / 过早放弃)。刹车不一定只靠人——**oracle 丰富的 peer lane 能自刹车**(实测 dev lane 用同-fixture 证据两次反驳 coordinator 误判、救回被误判放弃的整块工作);oracle 稀薄处才更依赖人纠偏。**对称的自律(少产生错判,而不只是被刹住)**:下结论前**量具先自证**(过一遍已知答案)、坏量具期间的中间数字一个都不外报、自己两份数据打架时先认"我这边不确定"——见 `adversarial-verification.md` 的「量具先自证」。

## 共享树读数与归属判定(多 lane 单工作区拓扑)

多条 lane 共用一棵工作树时,**测量与归属都长出单人场景没有的失效**。五条,全部单项目单日多 lane 实测(apply-and-refine):

- **读数三档,按作用域选**:全量读数 = 跑前跑后 `git status` diff 为空 + 逐条定责;定向读数 = 核**这个读数的依赖集**未改动;「不属于我的脏文件为空」**实践中恒红,别当门用**(恒红的 gate 训练人忽略它)。判据是「**我依赖的东西变没变**」,不是「有没有并发」。
- **「树现在是坏的」有效期以分钟计**(别人的修复可能已进工作树、未提交)⇒ 造红 / 验门用不动引用(`git show <fix-sha>^:<path>`),别用 `HEAD` / 「当前树」;「我先跑的红」是自述型证据(顺序不留痕),报 blob sha 别报时刻。⛔ 别用 `git stash` 腾坏状态——共享栈会卷走别人的东西。
- **一句结论的两半可以来自两棵树**而读起来完全自洽(实测三人各踩一次)⇒ 定责必须同一时刻重量;不同时刻取的对照组不是对照组。
- **独立观察者 ≠ 独立通道**:N 方各自独立查、各自得零、互相印证——而 N 个零可以共享同一个盲区(量的都是同一条通道)。一致性的证据力取决于「有几条**独立通道**」,不是「有几方查过」;收到「N 方独立复核、结论一致」追一句:**你们各自用的是同一条通道吗?**(实测:三方都按工具调用的 file_path 判归属,而写入走的是脚本内部的文件操作——宾语藏在代码里,那条通道结构上看不见;三个零全真、结论全错、互相签字背书。)
- **归属判定三件套,少一样就废**:① **时间窗**(末次提交之后——「我写过这文件」对长期参与者几乎必然为真,零分辨力);② **写入宾语**(工具调用的 file_path,不是内容里**提到**的名字——越被讨论的对象,按名字查归属越不可靠,讨论使名字遍布草稿);③ **扫描面白名单**(只认落在仓内路径的写入;黑名单要枚举「哪里不算」,漏掉的不会有提示)。派生纪律:**归属未定可以等,被误提交不可逆** ⇒ 归属定下来之前一律 `commit -- <显式路径>`。

## validation status(诚实)

- **已跨 2 项目 / 2 拓扑验证**:① renderer_test(单 repo,3 条平级 peer lane,4 phase);② 跨 repo 库接入(2 repo,hub + fan-out 两级,唯一跨 repo seam)。两次核心都成立:context-lanes / **oracle 门控自主(最强)** / park-and-continue / durable 文件。
- **operating model(适用范围,不是短板)**:**同机 + 共享 `~/.claude` 绝对路径 mailbox + 人作异步决策 gate & 唤醒推手**。人不是信使(字节自动到位),是决策 gate + 调度器。
- **scope 边界(未在本模式发生,非待办 gap)**:**真分布式(跨机 / 无共享盘 / 跨人)未覆盖**——本模式靠集中到一条机器级路径回避了它,别假设 skill 管它;**全无人值守**未验证(人是决策 + 唤醒层,按设计);**紧耦合 peer thrash** 未发生(单 seam + hub 主动规避)。
- **弱 oracle 域 = 部分成立**:oracle 丰富段自刹车 + 自主拉满;弱 oracle 段(UI 视觉正确)如设计 **park → 人眼**(走 `gui-visual-machine-gating`)。
- **成本**:多 loop × 多 phase = 大 token 花销(呼应 `coordination-patterns.md` multi-agent ~15×)。值不值看任务。

## 组合

- `skills/collaboration/multi-session-coordination` —— 同 repo 的 lease/inbox/commit hook 底层;本 skill 通信层在同 repo 时跑在它上面。
- `guidelines/workflow/handoffs.md` / `techniques/coordination-patterns.md`(coordinator↔worker、成本)/ `techniques/worker-instructions.md`(**brief 正确性≠完整性 / self-contained**)。
- `techniques/adversarial-verification.md`(oracle 阶梯、独立判官、容差)/ `guidelines/code/gui-visual-machine-gating.md`(无 oracle→机器 gate 纯函数 + 画面人眼)/ `guidelines/code/dual-layer-data-ownership.md`(seam 数据归属)。
- `guidelines/claude-code/autonomous-loop-scheduling.md` + `ScheduleWakeup` / `CronCreate`(唤醒 / 轮询 cadence;长跑 Monitor 会死,用定时轮询)。
- `guidelines/workflow/knowledge-promotion.md`(收尾:harvest 不 promote → 策展 → 单一写手)。
- `techniques/lane-router.md` —— Lane Router 的安装、绑定、收发、ack、恢复与排障,**以及单条 lane 的 rotate 机制**(命令 / handoff 必须在 `~/.lane-router/rotation-handoffs/` 且是 UUID `.md` / 「窗口开了不算成功」的验证纪律);本 skill 只保留 role-lane 方法论、无 Router 时的 fallback,以及**一组 lane 轮换的顺序与前置**(方法 11)。⇒ **分工判据:那边管「怎么转一条」,这边管「一组怎么排」**——不复制机制细节,避免两份漂移。
