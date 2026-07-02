# Maya MPxSelectionContext 回调时序 + manip undo 局限

写自定义 `MPxSelectionContext` / `MPxContext`（自定义工具上下文，处理 viewport 里的
press/drag/release + hit-test + 选择），以及**由 manip 自持拖拽**（自定义 `MPxManipulatorNode` /
`MPxManipContainer` 自己 doPress/doDrag/doRelease）时，Maya 文档没明说的回调时序与 undo 约束。跟
[`manip-container-constraints.md`](manip-container-constraints.md) 是兄弟篇。

## 核心规则

1. **VP2.0 只调 3-param 版本的 `doPress/doDrag/doRelease`，必须同时重载 1-param + 3-param 并转发到共同实现**
2. **`doPress` 不立即更新选择集（rubber-band 到 `doRelease` 才更新）→ press 时要自己做 hit-test**
3. **在回调里调 `selectFromScreen` 会反触发 SelectionChanged 回调 → 加重入标志防护**
4. **plug-based undo 只记单个 plug，覆盖不了多关节联动结果（如 IK）→ 改用 `MPxToolCommand` + 整快照**
5. **`MPxToolCommand::finalize()` 从【manip 自持的 doRelease】调用不入 undo 队列 → 改走 `executeCommand` 一个普通 `MPxCommand`**
6. **stock 子 manip（rotate/scale）的值/朝向是 UI 态，undo/redo 不还原它 → 挂 MEventMessage `Undo`/`Redo` 回调手动 resync**

---

## 1. 3-param vs 1-param 回调双重载

VP2.0 只会调用 3-param 版本：

```cpp
// VP2.0 实际调用这个：
MStatus doPress(MEvent& e, MHWRender::MUIDrawManager& dm, const MHWRender::MFrameContext& fc) override
{ return doPressCommon(e); }

// 但必须同时保留 1-param 转发（某些路径 / 旧管线会走它）：
MStatus doPress(MEvent& e) override { return doPressCommon(e); }

// 共同实现集中一处：
MStatus doPressCommon(MEvent& e) { /* 真正逻辑 */ }
```

`doDrag` / `doRelease` 同理。**只重载 1-param 版本 → VP2.0 下交互逻辑跑到默认空实现，表现为"工具没反应"。**

## 2. doPress 不立即更新选择集

`MPxSelectionContext` 的选择更新分两个 phase：
- `doPress` / `doDrag`：选择集**不变**（为支持 rubber-band 框选）
- `doRelease`：根据 rubber-band 矩形**一次性**更新

所以**不能**在 `doPress` 里读 `getActiveSelectionList` 当作"按下命中了谁"——读到的是上一次的旧选择。
press 时要判断命中什么，得**自己做 hit-test**：

```cpp
// press 位置自己算命中，不依赖选择集
short x, y; e.getPosition(x, y);
// 用 worldToView 把候选目标投到屏幕空间，按像素距离判断命中（MEvent 与 worldToView
// 坐标系一致，可直接用像素距离做阈值，例如 20px）
```

## 3. selectFromScreen 重入

在 `doPress/doDrag` 里主动调 `selectFromScreen` 做 hit-test，会改变选择集，**反过来触发同一
context 的 SelectionChanged 回调** → 工具 state 瞬间被改了又改（典型症状：某个 handle 错误地
闪一下隐藏/显示）。

```cpp
// 重入防护
if (inSelectFromScreen_) return;
inSelectFromScreen_ = true;
// ... selectFromScreen ...
inSelectFromScreen_ = false;
```

更稳的做法：hit-test 不走 `selectFromScreen`，改用第 2 条的独立像素距离计算，绕开选择集副作用。

## 4. plug-based undo 覆盖不了多关节联动

Maya 的 plug-based undo（如 manip 连外部 joint plug 后靠 autoKeyframe 进 undo 队列）
**只记录"哪个 plug 改了多少"**。对 IK 这种"拖一个 effector → 多个关节一起变"的操作：

- undo 只能各 plug 各自回退
- 但**约束关系（为什么这些关节要一起这样动）记不住**
- redo / 跨帧时结果不一致，约束丢失

正确做法：用 `MPxToolCommand` + 自己管理**整段数据快照**（操作前 capture before-snapshot，
release 时 capture after-snapshot，`undoIt` apply before，`redoIt` apply after）。详见
[`../../skills/maya/maya-tool-interaction/SKILL.md`](../../skills/maya/maya-tool-interaction/SKILL.md)
的 snapshot-diff undo 模式。

## 5. `MPxToolCommand::finalize()` 从 manip 自持的 doRelease 调用不入 undo 队列

第 4 条的 `MPxToolCommand` undo **只在 context 自身的工具交互里挂钩**：context 的 `doPress` 里
`newToolCommand()` 建命令、`doRelease` 里 `finalize()` 提交 —— 这条路径 Maya 认。

但如果拖拽是**由 manip 而非 context 自持**（自定义子 `MPxManipulatorNode` 或容器 `MPxManipContainer`
自己实现 `doPress`/`doDrag`/`doRelease`，典型：要按拖的是哪个子 handle 分流、或挂 stock rotate/scale
manip 的容器），在那个 **manip 的 `doRelease` 里调 `finalize()` 完全不入 undo 队列** —— 拖完的编辑
留在场景里，但 `Ctrl+Z` 跳过它、直接撤销上一个操作。日志能看到 `finalize()` 被调，却没有对应 undo 项。

**修法：manip 自持的可 undo 提交走 `MGlobal::executeCommand` 一个普通 `MPxCommand`**（不是 tool
command）—— 普通命令经 `executeCommand(cmd, /*display=*/false, /*addToUndo=*/true)` 从**任何调用栈**都
正常入队。

```cpp
// ❌ 在自定义 manip 的 doRelease 里 —— finalize 不入队
MStatus MyManip::doRelease(M3dView&) {
    fToolCmd->setEdit(before, after);
    fToolCmd->finalize();          // 不进 undo 栈，Ctrl+Z 跳过本次编辑
    ...
}

// ✅ 走普通命令 executeCommand，从 manip 调也入队
MStatus MyManip::doRelease(M3dView&) {
    MyCommitCmd::setPending(fTarget, fBefore, snapshotNow(fTarget));  // 静态交接快照
    MGlobal::executeCommand(MyCommitCmd::kName, /*display=*/false, /*addToUndo=*/true);
    ...
}
```

**快照数据太复杂不便走 MEL flag** → 用**静态交接**：`setPending(node, before, after)` 把快照塞进命令类的
static 成员，命令 `doIt` 取出后清标志（消费一次）。命令 `doIt/redoIt` apply after、`undoIt` apply before，
复用第 4 条同一套 snapshot 机制。

## 6. stock 子 manip 的值/朝向 undo/redo 不还原（要手动 resync）

容器挂 stock `rotate`/`scale` manip（`addRotateManip`/`addScaleManip`）时：undo/redo 由第 5 条的命令
还原了**数据模型**，但 stock manip 的当前值（rotationValue / scale）+ 环/轴朝向是 manip **自己的 UI
内部态，没人通知它跟着变** → 环视觉上停在拖完的朝向，跟已还原的数据对不上。

**修法：容器挂 `MEventMessage` 的 `Undo` / `Redo` 事件回调 → 从（已还原的）数据模型现读重算 → 复位
stock manip 的中心/朝向/值**。回调在 `createChildren` 注册、析构里 `removeCallback`（成对，防悬空）。

```cpp
// createChildren：
fUndoCb = MEventMessage::addEventCallback("Undo", ResyncCb, this);
fRedoCb = MEventMessage::addEventCallback("Redo", ResyncCb, this);
// ~容器：if (fUndoCb) MMessage::removeCallback(fUndoCb); 同理 fRedoCb
// ResyncCb → 从 node 现读位置/朝向 → MFnRotateManip::setRotationCenter/setInitialRotation 等复位
```

`Undo`/`Redo` 事件对**每次** undo/redo 都触发（不只你的命令），resync 回调里判目标有效 + 读当前态即可，
无害重入。拖拽 release 后也顺手 resync 一次（环/轴回基准，纯为显示一致——delta 数学本就用 press-time
快照，不靠 manip 停在哪）。

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| 只重载 1-param `doPress` | VP2.0 下工具无反应 | 双重载 → 共同实现 |
| `doPress` 里读选择集当命中结果 | 读到旧选择 | press 时自己 hit-test |
| 回调里裸调 `selectFromScreen` | SelectionChanged 重入，state 抖动 | 重入标志 / 改像素距离 hit-test |
| 多关节 IK 结果靠 plug undo | undo/redo 后约束丢失 | `MPxToolCommand` + 整快照 |
| manip 自持 doRelease 里 `finalize()` tool command | 不入 undo 队列，Ctrl+Z 跳过本次编辑 | 走 `executeCommand` 普通 `MPxCommand`（addToUndo=true）+ 静态交接快照 |
| 挂 stock rotate/scale，undo/redo 只还原数据不管 manip | 环/轴视觉停在拖完朝向，跟数据对不上 | `MEventMessage` `Undo`/`Redo` 回调 → resync manip 中心/朝向/值 |

## 项目实例参考

某 Maya 角色动画插帧插件的摆姿/拖拽工具（规则 1-4）：
- 初版只重载 1-param `doPress`，VP2.0 下拖拽无反应；补 3-param 重载转发后正常
- 骨骼命中测试不走 `selectFromScreen`（曾因重入导致 root handle 错误显隐），改为 `worldToView` 投屏 + 20px 像素距离阈值，`MEvent` 与 `worldToView` 坐标系一致可直接比
- 全身 IK 拖拽结果（多关节）用 `MPxToolCommand` + 单帧骨骼快照做 undo，不依赖 plug-level autoKeyframe

某 Maya 曲线形变插件的 authoring manip 工具（规则 5-6，manip-in-context：`MPxSelectionContext` 选点 +
自定义 `MPxManipulatorNode` 平移 triad + 容器挂 stock rotate/scale）：
- 拖拽由 manip 自持（要按拖的是中心方块还是哪条轴分流）。初版在 manip 的 `doRelease` 里 `finalize()` 一个
  `MPxToolCommand` → 拖完编辑生效但 `Ctrl+Z` 直接撤销到「创建曲线」，跳过本次拖拽。日志显示 `finalize()`
  被调却无 undo 项。改成 `executeCommand` 一个普通命令（静态 `setPending` 交接 before/after 快照，
  `addToUndo=true`）→ 每拖一条 undo，redo 正常。**这条跟参考的插帧插件（其 manip 连外部 joint plug 靠
  autoKeyframe 入队）不同——本工具 manip 不连 plug、写回走命令，才撞上「finalize 从 manip 不入队」。**
- 端点旋转/缩放挂 stock rotate/scale manip。undo 后曲线数据被命令还原，但旋转环停在拖完的朝向 → 容器挂
  `MEventMessage` `Undo`/`Redo` 回调，从曲线现读端点位置 + 重算表面架 → 复位环的中心/朝向。

## 相关 Guidelines

- [`manip-container-constraints.md`](manip-container-constraints.md) — MPxManipContainer 子 manip 约束（兄弟篇）
- [`../../skills/maya/maya-tool-interaction/SKILL.md`](../../skills/maya/maya-tool-interaction/SKILL.md) — snapshot-diff undo / press-time caching 等交互模式
- [`../code/validation.md`](../code/validation.md) — 交互行为必须 viewport 实测，不能只读代码
