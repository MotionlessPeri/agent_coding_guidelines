---
class: experience
scope: universal
triggers: [报结论, 做不到, 不支持, 能力边界, 框架不支持, 没变, 没接上, 不起作用, 零命中, 找不到, 不存在, 没发生, 搜了没有, ABSENT, 这个数, 搬数字, 聚合统计量, p95, 均值]
born: "2026-08，写下时的模型未记录"
retested:
  - "2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：R1 pass、R2 partial、R3 pass、R4 pass、R5 pass；见 docs/evaluations/experience-retest-2026-10-15.md"
incidents:
  - 2026-08-port-covered-half-the-operator
  - 2026-08-optional-dict-blamed-on-the-contract
  - 2026-08-offline-annotation-assumed-required
  - 2026-08-mirror-declared-unsolvable-at-receiver
  - 2026-08-host-hang-blamed-on-user-file
  - 2026-08-forked-bridge-mistaken-for-stock
  - 2026-08-symptom-hung-on-wrong-cause
  - 2026-08-p95-blind-to-threshold
  - 2026-08-dedup-log-hid-1800-events
  - 2026-08-change-gate-blind-to-never-existed
  - 2026-08-stash-control-group-never-ran
  - 2026-08-evidence-in-unreachable-repo
  - 2026-08-grep-only-reached-vendored-subset
  - 2026-08-toolset-scan-mistaken-for-framework
  - 2026-08-filename-pattern-missed-the-asset
  - 2026-08-absent-for-a-guessed-class-name
  - 2026-08-log-file-as-observation-window
  - 2026-10-compaction-hid-own-test-tool
  - 2026-08-directory-skeleton-mistaken-for-source
  - 2026-08-lane-rejected-own-candidate
  - 2026-08-alpha-zero-called-a-property
  - 2026-08-uncertainty-moved-to-mesh-consumer
  - 2026-08-ordering-constraint-under-another-name
  - 2026-08-one-consumer-site-generalized
---

# 报结论的四个边界：层、量、范围、机制

有一类错误不在工作里，在结论里：代码写对了、测量跑对了，报出去的那句话错了。下游拿着它行动，而它读起来完全合理，没人会去质疑。四条规则各管一条边界，共同的形状是**把局部结论说成了全局结论，而局部的边界没写出来**。

检查点在**往外说之前**，不在做完之后。干活时手上有证据，递结论时手上只有印象，而印象需要一个凭据，于是就近抓了一个。

本条管「说得对不对」；[`diagnose-before-fixing.md`](diagnose-before-fixing.md) 管改之前，[`validation.md`](validation.md) 管改之后。

## 1. 限制要标明归属层，并把解法写进句子

- 写「做不到 / 不支持 / 这是它的设计约束」之前问：这个限制是我这一层造成的，还是我下面那一层真的没有？答不出来先核，别写。自己是那层的作者时盲区最大：自己的收窄在脑子里是「现状」，出口就成了「约束」。
- 第二问：这个「做不到」是对某个解法证明的，还是对整层证明的？「沿『先剥掉 X 再重算』这条路在接收端做不到」可以写；「接收端解不开」不行，它把别的解法的门关死了。继承来的规格同样适用：收到「你那边做不到」，追两句「哪一层做不到、对哪个解法做不到」。
- 反方向同样错：把自己这层的扩展（环境里被内部改过的组件）说成下层的能力，下游会按一个不存在的能力去设计。确认某做法在原版下不成立后，不留 deferred 项、不留 stub 接口，两者都编码着「这条路通、只是还没接」。
- 最贵的受害对象是用户的数据和产物。写「用户的文件可能坏了」之前先自查「我这层最近改过什么」；你的代码跑在读取路径里时，你是嫌疑人，不是旁观者。这个方向的下一步动作是丢弃或重做，而且丢掉不报错。
- 写法：症状一句、成因一句，拆开写。「不实现 X ⇒ 会 Y」把可验的症状和不可验的成因焊在一起，读者验到 Y 为真就连带信了错的 X。

## 2. 「改了参数结果没变」只能在原始输出上读

p95、最大、均值这类聚合量只反映分布的一头，那一头恰好对某参数不敏感时，就给出「参数没接上」的假信号。判接线只用一个方法：逐位比整段原始输出。报「某参数不起作用」时写清比的是什么量；比的是聚合量就只能说「该量对它不敏感」。

事件同理。日志一行不等于一次发生：先确认那条消息走不走去重通道，走去重的行内计数可能是永不更新的快照。现场判「还在不在发生」用直观信号，不从日志推次数。

## 3. 「没有」之前先问：我能到达的范围，是不是就是全部范围

「真的没有」和「我看不到」在观测上长得一模一样，人默认取第一种。报「没有 / 找不到 / 不存在 / 没发生 / 零命中」时带上可达范围：搜了哪些仓、目录、版本、工具集，观测窗口用时间戳而不是文件容器界定。

- 探测返回「不存在」时，先问：这个名字、路径、接口，是我查到的还是我猜的？猜的先去权威处对一次名字。按名字查的否定结果，有效性上限是「这个名字是对的」。
- 镜像形态：在场也会被误读成完整。目录骨架、空表、只剩许可证的依赖目录都是「壳在、物不在」；存在性检查落在容器上就再往里查一层。
- 说「测不了」之前，先列一下本会话的临时目录和产物目录。上下文压缩后的摘要不等于磁盘上做过的事。
- 写者侧：断言带证据指针；目标在读者拿不到的仓时，连关键证据一起摘，标准是读者不打开目标也能判断该不该信。

## 4. 一个数要跟着它的机制走

机制没查，这个数只是一次观察，不是那个东西的性质；机制不适用，不能把这个数搬到别处。数字比文字更像证据，所以「该去查机制吗」这一问不会自动触发，要事先问：这个数的机制，能预测我正在说的这件事吗？

两条派生，同一个骨架是「只取证据链上一个点，然后外推到整条链」：按名字 grep 零命中只证明「这个名字没有」，功能可以用另一个名字在另一层实现；从一处消费点推「它在别处不被消费」同样错。读一个参数，先 grep 它的名字拿到全部出现点，再决定读哪几处。

## 反模式

| 反模式 | 修法 |
|---|---|
| 「这是它的能力边界」「框架不支持」，不说是哪一层 | 写明层；答不出先核再写 |
| 「搜了没有 / 零命中」，不说搜的范围 | 带上可达范围，或明说「在 X 范围内没有」 |
| 自己是那层作者，把自己的收窄当「现状」报出去 | 报限制前查一遍「这是我写的吗」 |
| 拿 p95 / 最大 / 均值判「参数没接上」 | 逐位比原始输出 |
| 数日志行判某错误发生了几次 | 先确认有没有去重；现场用直观信号 |
| 上游收到「做不到」直接转发下游 | 转发前追「哪一层、对哪个解法」 |
| 照规格执行时把它的禁止条款当物理定律 | 规格也是某人写的一句话，同样追那两句 |
| 报某能力可用，没查环境里那个组件是不是被改过的 | 先问「这是原版吗」；已否证的做法不留 deferred、不留 stub |
| 写「用户的数据可能坏了」，没先自查自己这层 | 先问「我这层最近改过什么」 |
| 存在性检查落在容器上就下结论 | 再往里查一层具体的物 |
| 把一次观察写成某个东西的性质 | 先问机制能不能预测这个观察 |
| 把一个有机制支撑的数搬到另一个场景 | 搬之前核那边的机制前提 |
| 按名字 grep 零命中就报「没做这件事」 | 先问「这件事如果做了，可能长什么别的名字、住在哪一层」 |
| durable 文档只写结论、不写证据在哪 | 断言带证据指针；跨仓时连关键证据一起摘 |

## 证据

事故记录在 [`evidence/incidents/`](../../evidence/README.md)，清单在本页 frontmatter 的 `incidents`，按规则和发现方式的统计由 `python scripts/kb/kb.py index` 生成到 [`evidence/INDEX.md`](../../evidence/INDEX.md)。数字看那里，这里只写数字说明不了的两件事：

- 规则 1 的全部命中没有一次是自查发现的，全靠外部追问、第三方复核或实验打破。这是它必须写成明文规矩的原因。
- 规则生效的次数结构性只报下界：规矩内化得越好，错误状态越不成形、痕迹越少。判据是那个错误状态有没有留下第三方能看见的痕迹；只有自述「我本来会写 X」的不算。

诚实边界：全部来自同一批协作对话（高频跨边界转述、多方各持一部分可达范围），未跨人 / 跨团队验证；单人单仓场景只有一例。apply-and-refine。

## 相关

- [`diagnose-before-fixing.md`](diagnose-before-fixing.md)：动手修之前先取证；本条管取证完报出去那句话。
- [`validation.md`](validation.md)、[`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)：「量具先自证」是规则 1 的近亲，「metric 选错」是规则 2 的另一面。
- [`../../techniques/measurement-four-questions.md`](../../techniques/measurement-four-questions.md)：报读数之前的量具 / 样本 / 总体 / 判据四问。
- [`premises-not-in-the-text.md`](premises-not-in-the-text.md)：同族的「前提」那一轴。
- [`../../techniques/worker-instructions.md`](../../techniques/worker-instructions.md)：派活方向的对称面；[`../workflow/handoffs.md`](../workflow/handoffs.md) 写 known limitations 时直接适用规则 1。
