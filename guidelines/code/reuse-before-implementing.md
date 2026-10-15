---
class: experience
scope: universal
triggers: [复用, 已有实现, 抽 helper, 重复代码, copy-paste, 新建文件, 新建类, 参考实现, samples, devkit, SDK, 过早抽象]
born: "2026-05，写下时的模型未记录；2026-10-13 按判断力改写"
retested: []
incidents:
  - 2026-05-subprocess-helper-extracted-late
  - 2026-08-wrong-matrix-overwritten-each-frame
  - 2026-08-rotation-order-declared-never-read
  - 2026-08-lock-scope-outgrown-by-function-body
  - 2026-08-mobu-samples-had-the-exact-device-example
---

# Reuse Before Implementing

实现新功能或修复缺陷前，围绕当前功能、调用方和相关模块查找已有实现；已有且仍有效的调查结果可以复用，不要求每次巡视整个代码库。重点确认三件事：已有实现满足当前契约就核实正确性、前提和副作用后优先复用；流程近似但参数或行为有差异时，判断共同职责是否稳定，公共 helper 是候选方案不是必选动作；局部相似的代码段，先看是否需要共同变化，再权衡保留重复与提取函数的成本。

跟 [`clarify-before-implementing.md`](clarify-before-implementing.md) 互补：那条处理影响结果的需求歧义，本条查找或排除复用对象。调查范围服务于当前决定，不自动增加规划审批或无关探索。

## 三个层级

| 层级 | 查什么 | 由谁管 |
|---|---|---|
| helper / function 级 | grep 本仓库现有函数、helper | 本条 |
| 架构 pattern 级 | 流程跟 X 像不像，要不要走 X 的基类 | 当前项目的架构资料或模式目录；相关 skill 只在能解决当前设计问题时按需用 |
| 框架侧 reference impl 级 | 本机随装的 SDK samples 与头文件里，官方怎么做这件事 | 本条下一节 |

三者互补但不是固定读取顺序。局部函数修改通常只需查看相关实现；涉及架构选择或不熟悉的框架契约时，再查对应资料。

## 框架侧 reference impl：按问题查目标版本的样例与头文件

涉及不熟悉、变化或可疑的 DCC、引擎、SDK 契约时，先 `ls` 本机目标版本的安装目录有没有 samples、devkit、include 树；有就先读那个场景对应的样例。它们是本地、离线、版本精确匹配的 oracle，优先于网络搜索和跨版本推测。先确认实际安装版本与资料来源，不能仅因文件在本机就认定版本匹配。「随装」不是普适前提（3ds Max 的 SDK 是可选安装组件），所以这条是「先查一下」，不是「假定有」；机器档案脚本会直接列出每台机器的这些目录。UE 域的同一机制在 [`ue-reference-engine-source`](../../skills/ue/ue-reference-engine-source/reference-engine-source.md)。

## 跟「premature abstraction」的边界

[`constraints.md`](constraints.md) 的「Three similar lines of code is better than a premature abstraction」跟本条是同一光谱的不同位置：

| 时机 | 该做什么 |
|---|---|
| 第一次写，还没有同类代码 | 实现当前需要；有清晰职责时可以拆单一调用方使用的函数，不为假想调用方设计通用接口 |
| 发现第二处相似实现 | 对照语义、依赖和副作用，判断复用是否能减少共同维护成本 |
| 多处代码需要同步修改 | 这是提取公共实现的有力信号；仍需确认共同契约，而非仅按出现次数抽象 |

防的是两端：为不存在的需求加参数、继承层次或通用接口；同一职责在多处实现，需要同步修正却没有合理的维护边界。调用方数量是线索，不是抽象是否合理的判据。

## 什么时候 survey，找到相似代码之后怎么决定

新建文件、类、helper 之前，确认代码库里有没有它的近亲：新 dialog 先 grep 现有 `S*Dialog`；「调外部进程收 stdout」先 grep `CreateProc` 类 helper；「开库、查、关」先找 RAII guard；写某个框架基类的子类先 grep 同基类的现有子类。工具是 ripgrep、类继承图，或把「找全所有做 X 的地方」交给搜索型子代理。

```
找到 N 处相似代码
  ├── 契约、前提与副作用一致        → 核实正确性后优先复用；多处需共同维护时评估公共实现
  ├── 流程一致但内层有差异          → 判断差异是否适合一个稳定接口，确有收益才提取
  ├── 表面相似但语义不同            → 不勉强复用；差异不明显且易被误改时，简短说明原因
  └── 只看到文本重复，未确认共同职责 → 先查调用上下文，不按重复次数决定抽象
```

## 复用之前先验它是否正确，不只读懂它的副作用

一段错误实现可以长期不崩、不报错、测试也不红，条件有两种：输出被覆盖（错的值算出来了，生效前被另一条路径整个盖掉）；全链一致地错（声明的约定没实现，全链用同一个默认值，彼此自洽）。原地无害，危害在被继承那一刻产生：新实现照抄它，或只抄一半打破了那个一致，错误第一次显形而显形位置离根因很远。常规判断手段全部失效，这段代码有注释、命名合理、被真实调用；只能反过来问：**谁读它的输出、读之前发生了什么？这个配置字段的读取点在哪？** 同族还有一种：锁的范围和调用位置隐含着对函数体大小的假设，函数体随演化增长时假设静默失效，代码形态上看不出。

## 复用决策记录

只有不复用的理由不明显、预计会影响后续维护判断时，才在已有审查记录、PR 说明或相应代码附近简短解释契约差异，不必承诺未来统一，也不要求每次选择都提交一份说明。

## 反模式

| 反模式 | 修法 |
|---|---|
| 同一段几百行逻辑随 caller 增加一遍遍 copy-paste | 发现相同契约需要在多处同步维护时评估提取公共实现，重点是共享的超时、输出、错误处理行为 |
| 两人各自实现「看起来相似但实际相同」的功能 | 开工前 survey；发现有人在做同类工作先沟通 |
| 强行套用语义不同的近亲（副作用不匹配） | 复用前读懂全部副作用，不匹配宁可分开 |
| 抽完发现只有一处 caller 用得到 | 用真实调用场景检查接口是否自然；只有一个调用方的函数也可以因职责清晰而值得提取 |

## 证据

事故记录见本页 frontmatter 的 `incidents`，统计由 `kb.py index` 生成。helper 抽得太晚的那次来自一个 UE 插件项目三个月的开发期；「错误实现原地无害」的两种形态来自同一仓库、机制不同的两次；锁的范围那次来自一个 DCC 插件；「先查随装 samples」在 UE 域早有单独条目，MotionBuilder 那次是第二击。

## 相关

- [`clarify-before-implementing.md`](clarify-before-implementing.md)：对称的另一条 prep work。
- [`constraints.md`](constraints.md)：Simplicity 节防 premature abstraction。
- [`../workflow/agent-lifecycle.md`](../workflow/agent-lifecycle.md)：围绕具体疑问读取代码，再行动或验证。
