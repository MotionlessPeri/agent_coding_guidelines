# 双层数据模型：按类型定 source-of-truth，派生别双向 sync

## 核心问题

当一个工具 / 编辑器同时维护**两套数据表示**——一个 authored / view 层（用户直接编辑的界面层）
+ 一个 domain / runtime 层（业务逻辑消费的数据层）——必须对**每一种数据类型**分别决定：哪层是
source of truth，哪层是 derived。判错 → 每个编辑操作都得手工同步两层 → 漏掉一个同步点 → 静默 desync。

**框架无关**：DCC 节点图编辑器（UE / Maya）、IDE、core + view 的 GUI 工具、ORM + UI、前端 state +
后端——只要有「两套数据表示」就适用。

## 三条规则

1. **按数据类型定 source-of-truth**——不是整个模型选一层，是**逐类型**判。有的数据（属性面板里编辑的
   字段）源在 domain 对象、view 只显示；有的数据（拖拽产生的拓扑 / 连接）源在 view 层、domain 派生它。
   开工前先列清每类数据归哪层，哪层是权威、哪层是派生。

2. **派生用 full-flush「compile」，别在每个 mutation 路径里增量 sync**——从权威层**整体重建**派生层
   （一个 compile 函数），而不是在每个增删改路径里各自维护派生层。
   - 好处：同步逻辑只在**一个地方**；不可能漏同步点——任何权威层改动都触发全量重建。
   - 前提：compile 必须**幂等**（跑两次结果一样）；派生所需的全部信息必须能从权威层拿到（否则重建时丢数据）。

3. **两条流可以反方向，接受不对称**——常见形态是一类数据 domain→view、另一类 view→domain。别硬把两类
   凑成单一数据流方向；承认这种不对称，架构反而更干净。

## 反 Pattern

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 每个 mutation 操作里手工增量 sync 派生层 | 每条代码路径都要记得 sync，漏一个（尤其绕过 choke-point 的调用）→ 静默 desync | 单一 full-flush compile，从权威层整体重建 |
| 派生所需的数据只存在派生层 | full-flush 重建时丢失（无源可派生） | 权威信息存权威层，派生层随时可重算 |
| 把两类反向流硬凑成单方向 | 跟框架 / 交互的天性打架，处处别扭 | 承认不对称，各走各的方向 |

## 相关 Guidelines / Skills

- skill `ue-custom-graph-editor` —— 本条在 UE 自定义 `UEdGraph` 编辑器（graph pin 层 + runtime 数据层）的具体落地：`SGraphEditor` pin-first 约束 / `NotifyGraphChanged` 触发 compile 的时机 / 具体数据类型的归属表 / UE 反 pattern 代码。
- [`gui-visual-machine-gating.md`](gui-visual-machine-gating.md) —— 相关的「切开渲染无关逻辑 vs 渲染本身」：那条管**可测性**分层，本条管**数据归属**分层，正交互补。
- skill `multi-plugin-shared-core` —— 框架无关的架构 pattern 家族（Snapshot + Ops 数据/操作分离等），本条的双层归属是其一个侧面。
