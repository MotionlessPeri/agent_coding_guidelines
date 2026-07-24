---
name: role-lane-coordination
description: 把一个较重的项目拆到**多个常驻对话**(每个对话 = 一条 role-lane / context 边界)并协调它们时用。覆盖:role(持久 lane)⊥ task 拆对话、seam-contract 协同设计、分档 oracle(hard gate / advisory / park)门控自主、notify/act 自主度旋钮 + checkpoint、**唤醒机制**(mailbox 无通知原语 → 按预估 ETA 轮询 / 人推)、**分档路由**(结构化走 hub / 领域重·紧耦合人眼直连用户)、跨 lane 汇合用单一 coordinator 宿主、**brief 正确性≠完整性**、durable 文件抗失忆、**收件箱按发件人消歧 + ack 约定**。**跳过**:单对话任务;同 repo lease/inbox hook 底层(那是 `multi-session-coordination`,本 skill 同 repo 时复用它)。**operating model = 同机 + 共享 `~/.claude` 绝对路径 mailbox + 人作异步决策/唤醒层**;已跨 **2 项目 / 2 拓扑**验证(平级 peer + 跨 repo hub+fan-out)。**真分布式(跨机 / 无共享盘 / 跨人)未覆盖,别假设 skill 管它。**
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
3. **通信 = 异步 mailbox + 共享结果区**:mailbox **递证据 / 递一条失败 oracle,不递意见**;处理完移 `resolved/`。结果区**主动发** profile/benchmark(没硬 oracle 的软分歧靠"两边结果摆一起"一眼见)。**收件箱按发件人消歧**——`to-<lane>/` 定向 + 命名带发件人前缀,别让收件方"打开才知道是不是给自己的";**ack 约定二选一定死**(回原 lane 一条 ack / 静默归档到 `resolved/`),别留语义不定让人交叉核验"我的 done 有没有丢"。
4. **唤醒机制**(mailbox 没有"新消息"通知原语,必须显式解决):**传输**(文件落盘)自动即时;但 **act 要对面对话在跑** = 靠唤醒。等别人任务的对话**先预估"对方这活大概多久"→ 按那个量级定 poll cadence**(等 30min 的活别 60s 猛轮),或直接跟对方 lane 协商 cadence;**人推醒作 fallback**。⚠️ **长跑事件 Monitor 会资源耗尽而死**(实测 exit `0xC000026B`)→ 别指望常驻事件监听,用 **CronCreate / ScheduleWakeup 定时轮询兜底**。
5. **oracle 三档,门控自主**:hard(代码 gate,**授权 auto-act**)/ advisory(fresh 对话 judge,只提醒)/ none(**park 给人**)。铁律:**auto-act 只在 hard 后面;oracle 覆盖率 = 能安全自主的面积**。(实测最强一环:golden 全绿 → hub 自主 commit,正确性不需人 gate。)
6. **自主度 = 拓扑旋钮**:**notify**(propose→你拍板,peer,你在场)/ **act**(oracle-gated 自动 + park,coordinator 拥 goal)。**checkpoint 落在人判断点**(契约 settle / 集成前 / 画面验)。
7. **park-and-continue**:碰只有人能定 / 无 oracle / 跨 lane 分歧 → 写 `parked/` 注明,**继续做别的,别卡住、别乱猜、别 fabricate**。
8. **跨 lane 汇合 → 单一 coordinator 宿主**(拥共享 main/build/汇合点),**不是并行 peer**(peer 抢共享文件会 thrash)。宿主选拥自然汇合点的 lane。但**分档路由**:**结构化契约任务走 hub**(self-contained brief → 零往返);**领域知识重 / 紧耦合人眼(视觉·DCC)任务 → dev 直连用户/权威,别强穿 hub**(hub 缺该领域知识时经它转是**有损一跳**)。hub 的活 = **识别任务类型 + 早放行**,不是无差别转发;hub **报症状不定实现、下结论先读真代码**(远离 dev 代码易误诊)。
9. **brief 正确性 ≠ 完整性**:brief self-contained(完整)还不够——**标清"我的假设(未证实)" vs "已验证 oracle(附 dump)",证据/oracle 随任务下发,不只发结论**。(最高价值教训:自信但错的 ground-truth baked 进完整 brief,每次纠错一整轮。见 `worker-instructions.md`。)
10. **durable 文件抗对话失忆**:contract = 项目记忆、worklog/resume-point = 工作记忆(补 guidelines 的 playbook 记忆)。**每增量 commit + 追加 worklog**。(实测真救过一次:某 dev 对话工具抽风误 rm 任务 + 捏造任务,靠 mailbox durable 记录重投递恢复。)跨 lane commit 顺序是硬约束:下游 import 上游未入库模块会被卡 → 上游先 commit / 或 hub 合成单 commit。

## setup

- **manifest**:参与者 + 各自 mailbox / 家 / 结果区**位置**。**operating model = 同机 + 共享 `~/.claude` 绝对路径**——多 repo 的对话各自 cwd 不同,但都用**绝对路径**读写同一条 mailbox(不分布 mailbox,集中到一条机器级路径)。
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
- **"错误结论的刹车"可由人 OR peer 的 oracle 纪律承担**:park-and-continue 覆盖不到**自主的错判**(误诊 / 过早放弃)。刹车不一定只靠人——**oracle 丰富的 peer lane 能自刹车**(实测 dev lane 用同-fixture 证据两次反驳 coordinator 误判、救回被误判放弃的整块工作);oracle 稀薄处才更依赖人纠偏。

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
