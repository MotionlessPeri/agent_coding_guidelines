# Move vs Rotate manip 的「Object」轴向取自不同 rotation attr

自定义工具想让 Maya 的 **Move / Rotate 操纵器（manip）在「Object」轴向模式下对齐到某个自定义帧**
（如把控制器对齐到表面切线/法线架、骨骼朝向架等）时，有一条 Maya 文档没明说、只能靠实测得到的约束：
**Move 工具和 Rotate 工具的「Object」轴向取自 transform 旋转管线的不同部分**，放错 attr 会出现
「驱动对、gizmo 朝向错」。跟 `manip-container-constraints.md` / `selection-context-and-undo.md` 同属
manip 交互契约（那两篇管自定义 MPxManip/Context；本篇管**原生 Move/Rotate 工具**的 gizmo 朝向来源）。

## 核心规则

Maya transform 的旋转管线（行向量，无 pivot 时）：`worldRot = parentRot ∘ rotateAxis ∘ rotate`。
两个工具的「Object」轴向**采样这条管线的不同段**（Maya 2024 实测）：

| 工具 | 「Object」轴向 = | 反映 rotateAxis？ | 反映 父级 rotation？ |
|---|---|---|---|
| **Move（平移）** | 物体**完整**世界朝向 `parent ∘ rotateAxis ∘ rotate` | ✅ 反映 | ✅ |
| **Rotate（旋转）** | `parent ∘ rotate`（**不含**物体自身 rotateAxis） | ❌ **不反映** | ✅ |

**推论——要把某工具的「Object」轴向对齐到自定义帧 F：**
- 只对 **Move**：把 F 设到物体自身 `rotateAxis` 即可（Move 反映它）。
- 对 **Rotate**：设 `rotateAxis` **无效**（Rotate 不看它）。必须把 F 放到**父级 transform 的 `rotate`**
  （或物体自身 `rotate`，但那通常留给动画/编辑）。
- 要 **Move + Rotate 都对齐**：把 F 放**父级 transform 的 `rotate`**（两者都反映父级）。

## 典型症状：「驱动对、朝向错」

把自定义帧 F 放进物体 `rotateAxis`，并在**下游**（如自定义 deformer / DG 节点）用 F 做旋转运算：
- **旋转数学正确**（下游读的是 F=rotateAxis，算出来对）。
- **但 Rotate gizmo 的环留在父级/世界帧**（gizmo 不看 rotateAxis）。

于是用户在 viewport 里**按 gizmo 抓「看着该对的那个环」，得到的旋转却绕了非预期的轴**——尤其在
表面朝向各异（侧立/斜面）时，"看着平躺贴面的环"其实是世界轴，不是自定义帧的轴。用户会说
"我转的环和旋转效果对得上，但环的位置跟 local xyz / triad 对不上"——这就是本契约。

## 诊断：逐 attr 改、看 gizmo 动不动（决定性）

不要靠肉眼猜颜色或推导。归零 `rotate` / `rotateAxis` / `父级.rotate`，**一次只给一个**设个明显角度，
刷新 manip（`setToolTo(currentCtx())`），看 Rotate gizmo 的环**朝向变没变**：

```python
import maya.cmds as cmds
def test_manip_axis(node, which, angle=60.0):
    par = (cmds.listRelatives(node, parent=True, fullPath=True) or [None])[0]
    cmds.setAttr(node + ".rotate", 0, 0, 0)
    cmds.setAttr(node + ".rotateAxis", 0, 0, 0)
    if par: cmds.setAttr(par + ".rotate", 0, 0, 0)
    if   which == "rotate":     cmds.setAttr(node + ".rotate", angle, 0, 0)
    elif which == "rotateAxis": cmds.setAttr(node + ".rotateAxis", angle, 0, 0)
    elif which == "parent":     cmds.setAttr(par + ".rotate", angle, 0, 0)
    cmds.evalDeferred(lambda: cmds.setToolTo(cmds.currentCtx()))  # 刷新 gizmo
# 切到 Rotate 工具(Object) → 分别 test_manip_axis(loc,"rotateAxis") / "rotate" / "parent"，看哪个让环转
```
实测结果：`rotate` 与 `parent` 让 Rotate 环转，`rotateAxis` **不让**。Move 工具则 `rotateAxis` 也让它转。

另一条交叉验证：`worldMatrix`（`xform -q -ws -matrix`）= 完整合成，**Move gizmo 跟它**；但
**Rotate gizmo 不跟 worldMatrix 里 rotateAxis 那一截**——所以单看 worldMatrix 会误判 Rotate gizmo 的朝向。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| 想让 Rotate gizmo 对齐自定义帧 → 设物体 `rotateAxis` | gizmo 不动（仍父级/世界帧）；驱动对但朝向错 | 帧放**父级 transform 的 rotate** |
| 用 worldMatrix 推断 Rotate gizmo 朝向 | worldMatrix 含 rotateAxis，Rotate gizmo 不含 → 误判 | 用 `test_manip_axis` 逐 attr 实测 |
| 肉眼按颜色/"哪个环平躺"找轴（斜面/侧面） | 表面非朝上时"平躺的环"≠ 切平面环 | 实测轴向（读 attr/worldMatrix 比对法线），别靠视觉 |
| 以为 Move 和 Rotate 的「Object」轴向一致 | 两者取自管线不同段，rotateAxis≠0 时分叉 | 记住表：Move 含 rotateAxis、Rotate 不含 |

## 项目实例参考

某 Maya curvenet 形变插件做「旋转端点控制器 → 名下切线手柄绕端点在切平面内 orbit」工具：
- 初版把"表面架 S"（每次选中现采样）设到端点 locator 的 **`rotateAxis`**：下游 DG 节点用 S 算 orbit
  数学正确（手柄确实绕 S 转），但 **Rotate gizmo 环从没对齐过 S**——留在世界帧。用户反复"按看着平躺的
  环去转、结果手柄翻出表面"，并明确反馈"驱动对、朝向跟 triad 对不上"。
- `test_attr`（上面诊断的原型）实测确认：改 `rotateAxis` Rotate 环不动、改 `parent`/`rotate` 才动。
- 改正解：把 S 设到端点 locator 的**父级 follow 组的 `rotate`**（Rotate gizmo 反映父级）→ 环对齐表面架、
  蓝环(Z)=法线平躺贴面；顺带 Move 工具 Object 轴向也=表面架（满足"沿表面移动"需求）。
  联动：下游节点的局部 offset 要乘父级帧（`offset·frame`）才得世界位移。

## 相关 Guidelines

- [`manip-container-constraints.md`](manip-container-constraints.md) / [`selection-context-and-undo.md`](selection-context-and-undo.md)
  — 自定义 MPxManip/Context 的交互契约（本篇是**原生 Move/Rotate 工具** gizmo 朝向来源，互补）。
- [`draw-override-and-command-invocation.md`](draw-override-and-command-invocation.md)
  — 同属「headless/单测看不到、必须 GUI 或实测才暴露」的 Maya 契约族；gizmo 朝向也只能 GUI/实测验。
- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md)
  — 本契约的定位过程是范例：不靠推导/肉眼，设计 `test_attr` 让"改哪个 attr→gizmo 动不动"区分竞争假设。
