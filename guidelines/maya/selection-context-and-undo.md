# Maya MPxSelectionContext 回调时序 + manip undo 局限

写自定义 `MPxSelectionContext` / `MPxContext`（自定义工具上下文，处理 viewport 里的
press/drag/release + hit-test + 选择）时，Maya 文档没明说的回调时序与 undo 约束。跟
[`manip-container-constraints.md`](manip-container-constraints.md) 是兄弟篇。

## 核心规则

1. **VP2.0 只调 3-param 版本的 `doPress/doDrag/doRelease`，必须同时重载 1-param + 3-param 并转发到共同实现**
2. **`doPress` 不立即更新选择集（rubber-band 到 `doRelease` 才更新）→ press 时要自己做 hit-test**
3. **在回调里调 `selectFromScreen` 会反触发 SelectionChanged 回调 → 加重入标志防护**
4. **plug-based undo 只记单个 plug，覆盖不了多关节联动结果（如 IK）→ 改用 `MPxToolCommand` + 整快照**

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

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| 只重载 1-param `doPress` | VP2.0 下工具无反应 | 双重载 → 共同实现 |
| `doPress` 里读选择集当命中结果 | 读到旧选择 | press 时自己 hit-test |
| 回调里裸调 `selectFromScreen` | SelectionChanged 重入，state 抖动 | 重入标志 / 改像素距离 hit-test |
| 多关节 IK 结果靠 plug undo | undo/redo 后约束丢失 | `MPxToolCommand` + 整快照 |

## 项目实例参考

某 Maya 角色动画插帧插件的摆姿/拖拽工具：
- 初版只重载 1-param `doPress`，VP2.0 下拖拽无反应；补 3-param 重载转发后正常
- 骨骼命中测试不走 `selectFromScreen`（曾因重入导致 root handle 错误显隐），改为 `worldToView` 投屏 + 20px 像素距离阈值，`MEvent` 与 `worldToView` 坐标系一致可直接比
- 全身 IK 拖拽结果（多关节）用 `MPxToolCommand` + 单帧骨骼快照做 undo，不依赖 plug-level autoKeyframe

## 相关 Guidelines

- [`manip-container-constraints.md`](manip-container-constraints.md) — MPxManipContainer 子 manip 约束（兄弟篇）
- [`../../skills/maya/maya-tool-interaction/SKILL.md`](../../skills/maya/maya-tool-interaction/SKILL.md) — snapshot-diff undo / press-time caching 等交互模式
- [`../code/validation.md`](../code/validation.md) — 交互行为必须 viewport 实测，不能只读代码
