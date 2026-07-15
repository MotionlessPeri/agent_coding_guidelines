---
name: maya-tool-interaction
description: Use when building a Maya manip, selection context, or other DCC drag-edit tool whose handle movement triggers expensive multi-element recomputation; when drag feedback drifts, tiny movement causes unnecessary work, or plug-level undo cannot restore the full result; or when an editable controller must remain attached to a rig-driven object. Skip for simple direct manipulation with no solver, feedback loop, or multi-object undo.
---

# DCC 拖拽编辑工具的交互模式

拖一个 handle → 触发一次**昂贵的多元素重算**（IK / solver / 模型推理）的交互工具，有五个
可组合的模式。在 Maya manip/context 场景提炼，泛化到任意 3D viewport 工具。配套的 Maya 框架
hidden contract 见 [`../../../guidelines/maya/manip-container-constraints.md`](../../../guidelines/maya/manip-container-constraints.md)
+ [`../../../guidelines/maya/selection-context-and-undo.md`](../../../guidelines/maya/selection-context-and-undo.md)。

> ⚠️ 单项目验证的 pattern，应用并精炼。

| 模式 | 一句话 |
|------|--------|
| 1. press-time 完整重算 | 每次拖拽从"按下时快照"重算一遍，不累加 delta |
| 2. press-time caching | 拖一个约束时，其他约束按下时冻结 |
| 3. 位移阈值防抖 | 松开时位移超阈值才触发昂贵重算 |
| 4. snapshot-diff undo | 前后整快照对比做 undo，不用 plug-level |
| 5. undo 数据存业务对象 | 存 instance 不存 manip |
| 6. 控制器叠在被驱动对象上 → live attach + 两层 | 外层跟驱动源 / 内层是可 K 的编辑 offset；静态放置会钉死输出显示 |

---

## 1. press-time 完整重算（无状态）

按下时 capture 一份起始快照 `startSnap`。拖拽中每一次重算都**从 `startSnap` 出发完整算一遍**
（喂给 solver/模型），**不是**把 delta 累加到"当前值"。

**为什么**：累加 delta 会累积浮点误差 + 反馈漂移；从固定起点完整重算每次结果确定，且 undo 简单
（见模式 4，只需记 start/end 一对）。

## 2. press-time caching 防反馈漂移

拖**一个**约束（如某个 effector）时，**其他**约束的输入值用**按下时**读到的值，而不是实时重读。

**为什么**：solver 是闭环——重算结果会改其他 handle 的位置，若实时重读它们当输入，就形成
"拖 A → 重算 → B 动了 → 下一帧把动了的 B 当输入 → 结果又变"的漂移。按下时冻结其他约束、
松开时一次性整体重算，消除漂移。

## 3. 位移阈值防抖

按下记录基线坐标；拖拽中照常做 visual feedback；**松开时**判断总位移是否 ≥ 阈值，**只有超阈值
才触发昂贵重算**，否则视作"没动"撤销。避免无意义的小抖动触发一次 solver/模型调用。

## 4. snapshot-diff undo

复杂多步计算的编辑，undo **不要**用 plug-level（autoKeyframe 只记单 plug，覆盖不了多元素联动
结果，见 selection-context-and-undo.md 第 4 条）。改用整快照对比：

```cpp
// MPxToolCommand 持有 (target, beforeSnapshot, afterSnapshot)
undoIt() { apply(beforeSnapshot); }
redoIt() { apply(afterSnapshot);  }
```

press 时 capture before，release（确认超阈值）时 capture after。

## 5. undo 数据存业务对象不存 UI 对象

undo 需要的数据存在**业务对象（instance / asset）**上，**不要**存在 UI 对象（manip）上。

**为什么**：
- manip 生命周期绑 tool context——context 切走再切回时 manip 重建，存在 manip 上的 undo 数据指针失效
- 跨 context undo（编辑 A → 切到 B → Ctrl+Z 要恢复 A）需要数据在持久层
- 场景重载后 manip 重建，undo 数据应能从持久层恢复

**模式**：command 的 `undoIt` 只改 instance 上的数据；UI（manip 位置）通过 SelectionChanged /
timeChanged 等回调从 instance 数据驱动刷新，而不是 command 直接戳 manip 裸指针。

## 6. 控制器叠在被驱动对象上 → live attach + 两层分离

编辑控制器（manip/locator）若叠加在一个被**外部驱动**（rig skinning / follow / 上游 deformer）的
对象上，控制器**必须 live 跟随驱动源**（attach），**不能静态放置**（一次性 setTranslation/xform）。

**为什么**：DCC 节点的"显示位置"常是 compute 实时算的（`显示 = 驱动源输出 base + 编辑量`）。若
控制器静态放置、再 `connectAttr` 把它的值喂进节点的编辑输入 attr，而 compute 让这个编辑输入**以
最高优先级覆盖**显示输出 → 驱动源一变（rig 摆 pose），输出 base 变了但静态控制器不变 → **钉死整个
输出显示**（不只控制器脱节，连没编辑的部分也被静态值覆盖）。这是个隐蔽 bug：编辑前一切正常，一旦
建了控制器再动 rig 就钉死。

**修法——两层分离**：
- **外层**（base 层）：被驱动源 live 驱动（attach 到驱动源——constrain / `pointOnCurveInfo` /
  绑同一套 skin 等）→ 跟随，**不打关键帧**
- **内层**（编辑层）：用户拖 / K 它相对外层的 **local offset** → 编辑量，**可打 animation curve**
- 控制器世界位 = 外层(驱动 base) + 内层(编辑 offset)，喂节点编辑输入
- offset = 0 → 控制器 == 驱动 base → 编辑量 0 → 恒等（不碰原驱动动画）

**收益**：① 驱动源变时控制器 + 显示一起跟随（不钉死）；② base 动画（外层跟驱动）与编辑动画
（内层 K offset）**天然叠加**；③ K 的是标准 transform.translate（animator 日常的 animation
curve 载体），不是节点的 array attr（后者在 Graph Editor 里编辑体验差）。

**附带的 DG 契约**：外部控制器驱动节点**必经一个节点输入 attr**（DG 通信靶子，删不掉——节点间
通信必须有 attr）。真正能减的冗余是"同语义的多个输入 attr"（如同时有中性绝对位 + posed 绝对位两个
输入），收敛成一个；不是去掉输入 attr 本身。"在 C++ 建控制器还是外部脚本建"不改变这条——控制器
的值总要经一个输入 attr 进节点。

---

## 组合关系

一次拖拽的完整生命周期：press → capture `startSnap`（模式 1）+ 冻结其他约束（模式 2）+ 记基线；
drag → visual feedback；release → 判位移阈值（模式 3）→ 超阈值则从 `startSnap` 完整重算得
`endSnap` → 存 (start, end) 到 instance（模式 5）作 snapshot-diff undo（模式 4）。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| 累加 delta 到当前值 | 浮点漂移 + undo 难 | 从 press-time 快照完整重算 |
| 实时重读其他约束当输入 | 反馈闭环漂移 | press-time 冻结其他约束 |
| 每次微小拖拽都重算 | 无意义昂贵调用 | 位移阈值防抖 |
| 多元素结果靠 plug undo | undo/redo 约束丢失 | snapshot-diff undo |
| undo 数据存 manip 裸指针 | context 切换/重载后失效 | 存 instance，UI 回调驱动刷新 |
| 编辑控制器静态放在被驱动对象上 | 驱动源变（摆 pose）时钉死整个输出显示 | 两层分离：外层 live attach 跟驱动 + 内层可 K 编辑 offset |

## 项目实例参考

某 Maya 角色动画插帧插件的锚点拖拽 / 摆姿工具（模式 1-5）：拖拽锚点时从按下时的会话快照出发调
Bezier 模型完整重算（非累加 delta）；摆姿拖一个 effector 时其余 5 个关键点旋转用按下时缓存值
防漂移；松开时位移 < 阈值（0.25）视作没动撤销；undo 用 `MPxToolCommand` + 单帧骨骼快照对比，
且 effector 位置缓存存在 instance extension 上、context 切回时从 data 恢复到 manip，不在 command
里直接操作 manip 裸指针。

另一 Maya 插件（curvenet 角色形变，模式 6）：动画师在被 rig skin 驱动的 **posed** 角色上编辑曲线
控制点。初版 locator **静态** `xform` 到 posed 位 + `connectAttr` 喂节点 `editInputPosed` 输入，
节点 compute 用它**覆盖**显示输出 → 旋转 skeleton 时 follow 变但静态 locator 不变 → **整条曲线
显示钉死**。改**两层**：外层 group 被 `pointOnCurveInfo(carrier CV)` 驱动跟 follow（rig 动画，不 K）
/ 内层菱形 locator 拖 + K 它的 local translate = offset（curvenet 微调 animation curve）；外层 rig
动画 + 内层 K 微调天然叠加。同时删掉同语义的冗余输入 attr（中性绝对位 `editInput`），收敛到
`editInputPosed` 一个。

## 相关 Guidelines / Skills

- [`../../../guidelines/maya/manip-container-constraints.md`](../../../guidelines/maya/manip-container-constraints.md) — MPxManipContainer 框架契约
- [`../../../guidelines/maya/selection-context-and-undo.md`](../../../guidelines/maya/selection-context-and-undo.md) — context 回调时序 + 为什么 plug undo 不够
- [`../../architecture/multi-plugin-shared-core/SKILL.md`](../../architecture/multi-plugin-shared-core/SKILL.md) — undo 数据存的 instance/Snapshot 来自这套架构
