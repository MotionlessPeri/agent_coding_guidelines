---
name: role-lane-coordination
description: 把一个较重的项目拆到**多个常驻对话**(每个对话 = 一条 role-lane / context 边界)并协调它们时用。覆盖:按 role(持久 lane)⊥ task(工作单元)拆对话、seam-contract 协同设计、分档 oracle(hard gate / advisory / park)门控自主、notify/act 自主度旋钮 + checkpoint、跨 lane 汇合用单一 coordinator 宿主、durable 文件抗对话失忆。**跳过**:单对话任务;同 repo 的 lease/inbox hook 底层机制(那是 `multi-session-coordination`,本 skill 在同 repo 时**复用**它)。**validated once**——在一个内部跨图形 API 渲染器上(3 lane / 4 phase / oracle 丰富 / 人作异步决策审阅层)验过一轮;**跨 repo mailbox、全无人值守、紧耦合 peer thrash、弱 oracle 域**是设计到但**未验证**的边界,二次用(理想跨 repo)再修订。
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
| **家(home)** | contract + oracle 的存放处(项目里一处 / 共享 repo);位置是**配置项**,写进 manifest,不写死 |
| **coordinator** | 跨 lane 汇合(集成)时拥共享接线(main/build/汇合点)的那个 lane |

## 方法(已验证的核)

1. **按 context 边界分 lane,不按 persona**。一 lane = 一常驻对话。专家性从积累的域上下文长出来。
2. **seam = 契约**。每条 seam 一份 contract,连它的 oracle 一起定。contract + oracle 住共享**家**。
3. **通信 = 异步**:mailbox(**递证据 / 递一条失败 oracle,不递意见**;处理完移 `resolved/`)+ 共享**结果区**(主动发 profile/benchmark,**性能这类没硬 oracle 的软分歧靠"两边结果摆一起"一眼见**)。durable 契约/oracle vs ephemeral mailbox,分开放。
4. **oracle 三档,门控自主**:hard(代码 gate,**授权 auto-act**)/ advisory(fresh 对话 judge,只提醒)/ none(**park 给人**)。铁律:**auto-act 只在 hard 后面;oracle 覆盖率 = 能安全自主的面积**。
5. **自主度 = 拓扑旋钮**,按"你在不在场 + 派活授权"定:**notify**(propose→你拍板,peer,你在场)/ **act**(oracle-gated 自动 + park,coordinator 拥 goal,你不在场)。**checkpoint 落在人判断点**(契约 settle / 集成前 / 画面验)。
6. **park-and-continue**:碰只有人能定 / 无 oracle / 跨 lane 分歧 → 写 `parked/` 注明,**继续做别的,别卡住、别乱猜、别 fabricate**。
7. **跨 lane 汇合(集成)→ 单一 coordinator 宿主**(拥共享 main/build/汇合点),**不是并行 peer**(peer 抢共享文件会 thrash)。宿主选**拥自然汇合点**的那条 lane。
8. **durable 文件抗对话失忆**:contract = 项目记忆、worklog/resume-point = 工作记忆(补 guidelines 的 playbook 记忆)。**每增量 commit + 追加 worklog**。

## setup

- **manifest**(一份小配置):参与者 + 各自 mailbox / 家 / 结果区**位置**。位置随项目放,不写死。
- **目录**:`contracts/`(seam stub,Phase 1 填)`oracles/` `mailbox/`(+`resolved/`)`results/` `briefs/`(每 lane 职责)`parked/` `lessons/`。
- **同 repo 三对话共享工作树** → 直接复用 `multi-session-coordination`(hook:lease/inbox/commit-awareness)。**跨 repo** → 共享位置 + manifest 指路(**未验证**,见 validation status)。

## phase 形状(实战跑出来的)

- **Phase 1 = 契约 co-design**:各 lane 调研 → 发结果区 → 协同把 seam 契约从 stub 填 settled。**这本身是第一场协调测试**;人 review 契约。(实测:独立 lane 常**独立撞到同一设计**,artifact 中转产出连贯契约。)
- **Phase 2 = oracle-gated 自主实现**:各 lane **按契约 stub 邻居**先做自己;**oracle-first(红→绿),硬 oracle 绿才 commit**,无 oracle 的 park。
- **Phase 3 = 集成**:coordinator 宿主收拢三层;跨 API / 端到端硬 oracle 重跑;**画面 / 无 oracle 项交人眼**。

## 两个实战校准(人在哪些点 load-bearing)

- **scope 靠 propose→approve 增长,不是 loop 自扩**——实测从极简 v1 扩到一堆 feature,但每个都是**对话推荐、人 green-light**(OIDN 是人先问、对话再推荐)。这是 **notify 档正常工作**(对话是积极提案者);**scope 控制在"你的批准"层,不在 loop safety gate**——要收就在批准时收 / 显式 scope 冻结。
- **人是"错误结论的刹车"**——park-and-continue 覆盖不到**自主的错判**(误诊 / 过早放弃)。人在异步决策/审阅层要能**纠偏**(实测一次关键纠偏救回一整块被误判放弃的工作)。

## validation status(诚实)

- **Validated once**:内部跨图形 API 渲染器,3 lane / 4 phase,**oracle 丰富**(解析真值 / 参照实现 / 跨后端 parity / round-trip),**人作异步决策+审阅层**(长实现段无人管,自主 loop 扛住)。
- **未验证(设计到、没跑)**:① **跨 repo mailbox**(这次单 repo 共享工作树);② **全无人值守**(人虽非始终在场,但异步决策 + 一次关键纠偏 load-bearing);③ **紧耦合 peer thrash**(集成用 coordinator 规避了);④ **弱 oracle 域**(渲染域 oracle 先天丰富;纯 UI / 模糊正确性会把远更多东西压到 park→人)。
- **成本**:多 loop × 多 phase = 大 token 花销(呼应 `coordination-patterns.md` 的 multi-agent ~15× 警告)。值不值看任务。
- 二次用(**理想是真跨 repo**)后回来修订,去掉 "validated once" 标记 / 补真实边界。

## 组合

- `skills/collaboration/multi-session-coordination` —— 同 repo 的 lease/inbox/commit hook **底层**;本 skill 的通信层在同 repo 时跑在它上面。
- `guidelines/workflow/handoffs.md` / `techniques/coordination-patterns.md`(coordinator↔worker、成本判断)/ `techniques/worker-instructions.md`。
- `techniques/adversarial-verification.md`(oracle 阶梯:hard/advisory 的判据、独立判官、容差)/ `guidelines/code/gui-visual-machine-gating.md`(无 oracle→纯函数机器 gate + 画面人眼)/ `guidelines/code/dual-layer-data-ownership.md`(seam 数据归属:权威 vs 派生、full-flush)。
- `guidelines/claude-code/autonomous-loop-scheduling.md` + `ScheduleWakeup`(act 的 wake-loop / 轮询节奏)。
- `guidelines/workflow/knowledge-promotion.md`(收尾:harvest-不-promote → 策展 → 单一写手,防污染语料)。
