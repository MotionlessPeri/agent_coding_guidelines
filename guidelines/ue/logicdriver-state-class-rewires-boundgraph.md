# LogicDriver 切 state class 会撕掉 BoundGraph wire

## 核心 hidden contract

把 LogicDriver state node 的 `StateClass` 从默认 `USMStateInstance` 切到任意自定义
`USMStateInstance` 子类（哪怕只是 override 一个 `OnStateBegin_Implementation`），LogicDriver 框架会**自动改 BoundGraph 结构**：

1. **新增 11 个 `SMGraphK2Node_StateInstance_*` 节点**到该 state 的 BoundGraph
2. **重定向 `On State Begin/End/Update` 的 `then` 输出**——从原来的下游目标（通常是父类 BP 链里的 `ExecuteAction` / `IsValid` 这种业务节点）改连到新加的 `StateInstance_*` 节点
3. **原下游目标的 `execute` 输入变成 disconnected**——之前由 lifecycle 节点驱动的 BP 链断了

这是 LogicDriver **框架级别行为**，不是 bug，但**没在 doc 明说**。任何"继承自有 lifecycle BP 逻辑的父类 SM"的子类 SM，给 state 加自定义 class 都会撞。

## 关键失败模式

典型场景：父类 SM（如 `BaseWeaponActionSM`）在 state BoundGraph 里有：

```
On State Begin → Execute Action → (内部) Try Activate Ability → Consume Action
                                                                  ↑
                                                             清除 CurrentAction tag
On State End → Is Valid → Remove Available Action
```

子类 SM（如 `SwordActionSM`）的 18 个 skill state **继承**这套 BP。如果给 skill state 切自定义 class（如 `UCombatSkillState`），上面 wire 全断：

- `On State Begin → ExecuteAction` 被替换成 `On State Begin → StateInstance_Begin`
- `Execute Action` 节点 orphan
- → `Consume Action` 永不调用
- → `CurrentAction` tag 永不清
- → 父 SM 的 SetCurrentAction-while-loop（"循环 Update 直到 CurrState 收敛"）**永不收敛**
- → 累计字节码超阈值 → **BP "Infinite loop detected"** + 卡死

更恶心的是：**class 切回 default `USMStateInstance` 不会撤销**——新加的 11 个 `StateInstance_*` 节点 + 改了走向的 wire 都**留在 .uasset 里**（这就是 LogicDriver editor 里 state 节点右上角"闪电图标"切完不消失的原因）。**只能 `git checkout` / `p4 revert` 回滚到改 class 之前的 asset 版本**。

## 检测手段

切 class 之前 vs 之后对 state 的 BoundGraph 做 diff。BattleDemo 项目的 UnrealMCP fork 加了两个命令直接可用：

- `get_logicdriver_state_bound_graph_nodes` —— dump 一个 state 的完整 BoundGraph 节点 + pin 连接
- `connect_logicdriver_bound_graph_pin` —— 修 wire（按 GUID 连两个 pin）

比对的 key diff：
- node_count 增加 ~11（每个 BlueprintNativeEvent 都加一个 `StateInstance_<event>` 节点 + 一些 transition init/shutdown 节点）
- `On State Begin/End/Update` 的 `then` 输出指向变化
- 之前的下游业务节点（ExecuteAction / IsValid 等）`execute`/`exec` 输入变 disconnected

## 三条应对路径

按推荐顺序：

### A. 设计上回避——self class 不 override BlueprintNativeEvent（推荐）

不要在自定义 state class 里 `override OnStateBegin_Implementation` 等 BlueprintNativeEvent。
LogicDriver 检测不到 override → **不注入 instance 节点 → wire 不被撕**。

把"state 进入时调 X、退出时调 Y"的逻辑放到别处：
- 父 SM 的 BoundGraph BP 已有的 hook（如本案的 ExecuteAction）—— 让继承链自然 work
- Runtime 端 polling state 变化 + dispatch 表
- ActionSystem 层级的 delegate / multicast

### B. 切完 class 后手动 bridge wire 回去

如果非得 override（需要 C++ 介入 state lifecycle），切完之后**显式重连断掉的 wire**：

```cpp
// 用 connect_logicdriver_bound_graph_pin 或直接 Schema->TryCreateConnection
// 把 StateInstance_Begin.then 接到原来的 ExecuteAction.execute (或同位下游节点)
// 把 StateInstance_End.then 接到原 cleanup chain 入口
```

实操可写 helper script——读 BoundGraph 找到 disconnected exec input 的非框架节点
（通过 Y-坐标接近 `StateEntryNode`/`StateEndNode` 选最佳候选），逐个 bridge。

**Caveat**：
- bridge 后 asset 不一致——保存就是修改过的 wire 拓扑，跟原始 baseline 差 N 条新增 wire
- 多步 chain（如 `On State Begin → DPA1 → DPA2 → ExecuteAction`）的中段 wire 若也被撕，单纯 bridge entry 不够，需要识别整条 chain 重连
- 不同 state 的 BoundGraph 模板可能不同（combo state 有 cleanup / dodge 有 debug print / defence 用 GameplayEffect 等），单一启发式覆盖率有限

### C. 全量重写 BP 链

切完 class 后干脆放弃父类 BP，用 C++ override 重做整个 lifecycle 逻辑（ExecuteAction 等价的 ability 激活、ConsumeAction 等价的 tag 清理、cleanup）。
代价：跟 game-specific API 强耦合（ASC / InputCacheInterpreter / etc.），父类设计的"BP 可视编辑"价值打折。

## Anti-Patterns

| 反 pattern | 为什么错 |
|---|---|
| 假设 "schema 编译 pass + 无 warning" = asset 正常 | LogicDriver 撕 wire 不会触发编译 error，只在运行时 SM evaluation 走到 orphan 节点才炸 |
| in-memory 切回 default class 想恢复 | 不撤销 wire 变更，伤害持久 |
| 单元测试只测 default-class state | 必须包含"切到 custom class 后"的 PIE 行为测试 |
| 一次切多个 state class，编译 success 就 ship | 单个 state 切 class **几乎**没事（其他 default state 还能撑住 SM 评估）；多个一起切**累积**到某阈值就死循环——必须做完整 PIE |

## 项目实例参考

BattleDemo 项目 R2（2026-05-25）落地 OFCombatFramework：

- `SwordActionSM`（继承 `BaseWeaponActionSM`）的 18 个 skill state 切到 `UCombatSkillState` (`USMStateInstance` 子类，加了 `SkillDef` UPROPERTY + override `OnStateBegin`)
- PIE 装 sword 按左键 → "Infinite loop detected"
- 调查路径：MCP `set_logicdriver_state_node_class` 路径疑似 → 排除 (UI 也撞同样)
  → property mini graph 假说 → 排除（EditDefaultsOnly+BlueprintReadOnly 不触发）
  → 加 UE_LOG 到 `UActionSMInstance::SetCurrentAction` while loop → 发现 41 iter 不收敛
  → `On State End → Execute Action → Consume Action` 链断了
  → 加 MCP `get_logicdriver_state_bound_graph_nodes` 对比 baseline vs 改完 BoundGraph
  → 实锤 LogicDriver 注入 11 个 instance 节点 + 撕 wire
- 修复（短期）：加 MCP `connect_logicdriver_bound_graph_pin` 批量 bridge
- 待办（R3）：考虑迁路径 A，让 `UCombatSkillState` 不 override lifecycle

详 `H:\Perforce\XD_main\BattleDemo\Docs\sessions\` 下 R2 相关 session 记录。

## 相关 Guidelines / Techniques

- [`guidelines/ue/external-automation-write-path.md`](external-automation-write-path.md) ——
  写 UE asset 必走 PostEditChangeProperty。MCP `set_logicdriver_state_node_class` 第一版漏调
  PostEditChangeProperty 导致 framework 状态不一致；修复后行为跟 UI 一致——**但 LogicDriver
  撕 wire 是 PostEditChange 之后框架本身就要做的事，PostEditChange 修复跟本文档讲的"wire 被撕"
  是两个独立问题**
- [`skills/ue/unrealmcp-usage/SKILL.md`](../../skills/ue/unrealmcp-usage/SKILL.md) ——
  MCP fork 添加新命令的工艺，本案 `get_logicdriver_state_bound_graph_nodes` /
  `connect_logicdriver_bound_graph_pin` 是该 pattern 的实例
