# Maya 自定义 MPxManipContainer 的 hidden contract

写自定义 `MPxManipContainer`（内含 `FreePointTriadManip` / rotate manip 等子 manip，
用于在 viewport 里拖拽编辑）时，Maya 官方文档没明说、只能靠踩坑得到的一组约束。
跟 [`selection-context-and-undo.md`](selection-context-and-undo.md) 是兄弟篇（那篇管
context 回调时序 + undo）。非 Maya 项目可 skip 本目录。

## 核心规则

1. **子 manip 初始位置用 `setPoint()` 设，不要 `connectToPointPlug()` 连自身 plug**
2. **整体尺寸用实例方法 `setManipScale()`，不要用全局静态 `MFnManip3D::setGlobalSize()`**
3. **`connectToPointPlug()` 连自身 plug → NewScene 时崩溃；只能连外部节点 plug**
4. **没有标准 plug 连接时，不要调基类 `MPxManipContainer::connectToDependNode()`**
5. **动态增删子 manip 用固定 rebuild 序列，且只在 context 激活时做**
6. **隐藏子 manip 用 `setVisible(false)`，不要移到极远坐标**
7. **viewport 绘制：`preDrawUI/postDrawUI` 仅 VP2.0；VP1.0 要重写 `draw()`**

---

## 1. 初始位置用 setPoint()

在 `connectToDependNode()` / `finishAddingManips()` 之后，用 `MFnFreePointTriadManip::setPoint(pos)`
设置子 manip 初始位置即可。**不要**为了"让 manip 记住位置"去 `connectToPointPlug()` 连到自身的 plug——
那会引入自引用 DG 连接（见第 3 条）。

不绑外部 plug 时，读取 manip 当前值用 `getConverterManipValue(index, ...)`，而不是依赖 plug 的 get。

## 2. 尺寸：实例 vs 全局

| API | 作用域 | 用途 |
|-----|--------|------|
| `MFnManip3D::setGlobalSize()` | **全局静态**，影响整个 Maya 会话里所有 manip | ❌ 不要用它调单个 manip——会污染其他工具的 manip |
| `setManipScale()` | **实例级** | ✅ 单独调整某个子 manip 大小的正确选择 |

## 3. connectToPointPlug 自引用 → NewScene 崩溃

```cpp
// ❌ 连到自身 plug —— 自引用 DG 连接，NewScene 清理时两端同时失效 → DataModel.dll 崩溃
connectToPointPlug(self.somePlug);

// ✅ 连到外部节点 plug —— 安全，且 autoKeyframe 会进 undo 队列
connectToPointPlug(jointFn.findPlug("translate"));
```

历史上"自定义 manip 一开新场景就崩"几乎都是这个原因。**只能连外部节点的 plug**。
如果根本没有要绑的外部 plug，走第 4 条。

## 4. 无 plug 时不要调基类 connectToDependNode

自定义 manip 如果不走标准 plug 绑定（位置/值都自己用 `setPoint` + `getConverterManipValue`
管理），**不要**调用基类 `MPxManipContainer::connectToDependNode()`——基类假设有标准 plug 连接，
会失败甚至崩溃。直接在 override 里 `return MS::kSuccess`。

## 5. 动态增删子 manip 的 rebuild 序列

需要运行时增删子 manip（例如根据约束数量变化）时，在 **context 已激活**的状态下走固定序列：

```cpp
deleteManipulators();          // 1. 清旧
newManipulator(...);           // 2. 建新
connectToDependNode(...);      // 3. 重新连接
addManipulator(...);           // 4. 加入容器
syncHandlesToTargets();        // 5. 显式同步显示位置（rebuild 后必须）
```

多次 rebuild 也稳定。**注意**：rebuild 后子 manip 显示位置不会自动跟上，第 5 步的显式 sync 必须有。

> 纯"显示过滤"（只想临时藏几个 manip，不改结构）用第 6 条的 `setVisible` 更省，不要 rebuild。

## 6. 隐藏用 setVisible，不要移远

```cpp
manip3DFn.setVisible(false);   // ✅ 干净隐藏
// ❌ 不要 setPoint(MPoint(99999,99999,99999)) 这种 workaround
```

Maya 的 manip 节点**不在正常 DAG 层级**里——`cmds.ls` / outliner 都找不到，只能 C++ 侧操作。
所以显隐只能靠 `MFnManip3D::setVisible(bool)`。

## 7. 绘制管线 VP1.0 vs VP2.0

| 管线 | 绘制 callback |
|------|--------------|
| VP2.0（Maya 2022 默认） | `preDrawUI` / `postDrawUI`（用 `MHWRender::MUIDrawManager`） |
| VP1.0（legacy） | `draw()` |

要画圆环/辅助线等自定义 UI 元素时，VP2.0 走 `preDrawUI/postDrawUI`。若需跨版本兼容旧管线，
再额外实现 `draw()`。跨 Maya 版本发布时两套都要实测。

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| `connectToPointPlug(self.plug)` 想"记住"位置 | NewScene 崩溃 | `setPoint()` 设位置 / 连外部 plug |
| `setGlobalSize()` 调单个 manip 大小 | 污染会话内所有工具的 manip | `setManipScale()` 实例级 |
| 无 plug 还调基类 `connectToDependNode()` | 失败 / 崩溃 | override 里直接 return kSuccess |
| rebuild 后不 sync 显示 | manip 停在旧位置 | rebuild 序列末尾显式 sync |
| 移到极远坐标当"隐藏" | manip 仍参与命中/绘制 | `setVisible(false)` |

## 项目实例参考

某 Maya C++ 角色动画插帧插件（多 `.mll` 共享一个 base 层）的摆姿工具用动态数量的
`FreePointTriadManip` 做 effector 拖拽：
- 初版用 `connectToPointPlug` 连自身 plug → 每次 New Scene 崩在 `DataModel.dll`，改连外部 joint plug + `setPoint` 定位后解决
- effector 增删走 `deleteManipulators→newManipulator→connectToDependNode→addManipulator→syncHandlesToJoints` 序列，多次重建稳定
- effector 显示过滤（只藏 Position 型保留 Rotation 型）用 `setVisible` 而非 rebuild，省 ~30% 开销

## 相关 Guidelines

- [`selection-context-and-undo.md`](selection-context-and-undo.md) — MPxSelectionContext 回调时序 + manip undo 局限（兄弟篇）
- [`../../skills/maya/maya-tool-interaction/SKILL.md`](../../skills/maya/maya-tool-interaction/SKILL.md) — 拖拽编辑交互模式（press-time 重算 / caching / snapshot-diff undo）
- [`../code/validation.md`](../code/validation.md) — manip 行为不能只"看代码对"，必须 viewport 实测
