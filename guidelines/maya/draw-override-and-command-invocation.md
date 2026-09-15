# Maya VP2.0 绘制 + 从 C++ 发命令的 hidden contracts

写自定义 `MPxDrawOverride`（VP2.0 + `MUIDrawManager`）或从 C++ 用 `MGlobal::executeCommand`
发自己注册的 `MPxCommand` 时，一组**靠踩坑得到、官方文档没明说**的约定。共同点：**headless /
`cmds`-Python 测试都测不到，只在 C++ 实现 + GUI 实跑时才咬人**——所以单测全绿也可能 GUI 错（第 4 条更甚：
GUI **单 panel 也对**，只有多 panel 才暴露）。
跟 `manip-container-constraints.md` / `selection-context-and-undo.md` 是同目录兄弟篇（那两篇
管 manip / context 交互；本篇管 draw override + 命令调用）。非 Maya 项目可 skip。

## 核心规则

1. **从 C++ `executeCommand` 发带 object 的 MPxCommand：MEL 字符串里 flag 必须在 object 之前**
2. **`MPxDrawOverride::prepareForDraw` 复用 `oldData`：`buildDrawData` 每帧必须重置所有 transient flag**
3. **要"屏幕空间恒定大小"的 UI 用 `points()`+`setPointSize`（像素），别用 `circle()/rect()` 的世界尺寸×相机距离近似**
4. **`addUIDrawables` 里做 2D 投屏（`circle2d`/`text2d` 等）必须用回调传入的 `frameContext` 矩阵投影，不能用 `M3dView::active3dView()`——否则多 panel 下投错**

---

## 1. MEL 命令字符串：flag 必须在 object 之前

`MSyntax::setObjectType(...)` 的命令（接受命令对象，如节点名）从 **C++ 拼 MEL 字符串** 调用时，
**flag 必须排在 object 前面**，否则报 `Flags must come before objects: -xxx` + 解析失败。

```cpp
// ❌ object（节点名）在前、flag 在后 → "Flags must come before objects: -split"
MString cmd("myCmd ");
cmd += nodeName;
cmd += " -split "; cmd += a; cmd += " "; cmd += b;
MGlobal::executeCommand(cmd, /*display=*/false, /*undoable=*/true);

// ✅ flag 在前、object（节点名）在后
MString cmd("myCmd -split ");
cmd += a; cmd += " "; cmd += b; cmd += " ";
cmd += nodeName;
MGlobal::executeCommand(cmd, false, true);
```

**为什么 headless 测不到**：Python `cmds.myCmd(node, split=(a,b))` 由 Maya **自动按正确顺序**
组装参数 → headless Python 单测永远通过。只有**手拼 MEL 字符串**（典型：context / manip 里
`MGlobal::executeCommand` 发可 undo 命令）才会撞 flag/object 顺序，且只在 GUI 交互触发那条路径时暴露。

**防御**：从 C++ 发带 object 的命令，一律 `cmd -flag args... <object>` 顺序；如能加一条用
`MGlobal::executeCommand` 走 **MEL 字符串形式** 的 headless 回归测试（而非只测 `cmds` 形式），
就能把这条契约锁进 CI。

## 2. `prepareForDraw` 复用 `oldData` → 每帧重置 transient flag

`MPxDrawOverride::prepareForDraw(..., MUserData* oldData)` 把上一帧的 `MUserData` 传回来**复用**
（性能优化，避免每帧重建）。标准写法是 `dynamic_cast` 复用、没有才 new：

```cpp
MUserData* MyDrawOverride::prepareForDraw(..., MUserData* oldData) {
    auto* d = dynamic_cast<MyDrawData*>(oldData);
    if (!d) d = new MyDrawData();
    buildDrawData(node, *d);   // ⚠️ 复用对象：里面没重置的字段＝上一帧的残留
    return d;
}
```

**陷阱**：`buildDrawData` 里**每一个 per-frame 的 transient 状态（尤其 `bool` 标志 +
其配套位置/数组）都必须在每次重建时显式重置**，否则上一帧的 `true` 残留到这一帧。

```cpp
void buildDrawData(const MObject& node, MyDrawData& d) {
    d.polylines.clear();        // 容器记得 clear
    d.hasHighlight = false;     // ★ bool 标志也必须每帧重置
    d.hasSelection = false;     // ★ 漏一个 → "状态已清除但 UI 不消失"
    // ... 重新填充 ...
}
```

**典型症状**：业务状态已经清掉（取消选中 / 删除了对象 / 鼠标移开），但**高亮框 / 描边 / 标记不消失**
——因为对应的 `hasXxx` 标志只在"该画"时被置 `true`、从没被重置回 `false`，复用的 `oldData` 把上一帧的
`true` 带过来了。

**为什么 headless 测不到**：`prepareForDraw` 只在 GUI 实时重绘时被调，且 `oldData` 复用只在连续多帧
重绘里发生——headless 根本不进绘制管线。

## 3. 屏幕空间恒定大小：用 `points()`+`setPointSize`，不要世界尺寸×距离近似

`MUIDrawManager` 没有现成的"屏幕空间圆/方框 outline"原语。想要**不随相机远近变大小**的 UI 标记：

```cpp
// ✅ 真·屏幕空间恒定：points() 的点大小是【像素】单位，与相机距离无关
dm.setPointSize(16.0f);
dm.setColor(col);
dm.points(ptArray, /*isSelectable=*/false);

// ❌ circle()/rect() 的半径/半边长是【世界】单位；想恒定大小只能 半径 = 系数 × 相机距离 来近似，
//    透视下大致抵消、但正交 / 宽 FOV / 视角变化下会漂——用户会看到"拉远拉近大小在变"
const double s = factor * camDistance;   // 脆弱近似
dm.rect(pos, up, normal, s, s, /*filled=*/false);
```

**要"描边框 / outline"效果又要屏幕空间恒定**：`points()` 默认画的是**方点**——在目标点先画一个
**更大的底色方点**，再让正常（更小的）方点盖在其上，露出一圈底色边 = 屏幕空间恒定的描边框：

```cpp
// 选中底框（更大、醒目色）—— 在正常控制点之前画，正常点盖上去 → 露一圈边
if (d->hasSelection) {
    dm.setPointSize(kSelSize);          // > 正常点大小
    dm.setColor(kSelColor);
    dm.points(selArray, false);
}
// ... 随后正常控制点 dm.setPointSize(kNormalSize) + points() 盖在其上 ...
```

`circle()`/`rect()` 这类世界尺寸原语留给"确实是世界空间几何"的东西（切线臂、真实尺寸标注）。

## 4. `addUIDrawables` 里 2D 投屏用 `frameContext` 矩阵，不用 `active3dView()`

想在 `MPxDrawOverride::addUIDrawables` 里画 **2D 屏幕空间 UI**（`circle2d` / `text2d` / `line2d` / `rect2d`）
时，若需要把世界坐标投成 viewport 像素（`circle2d` 等吃的是像素坐标），**必须用回调第三参 `frameContext`
的矩阵**做投影，**不能**用 `M3dView::active3dView().worldToView(...)`：

```cpp
void MyDrawOverride::addUIDrawables(const MDagPath&, MHWRender::MUIDrawManager& dm,
                                    const MHWRender::MFrameContext& frameContext, const MUserData* d) {
    // ✅ 用【正在绘制的这个 panel】的 view-proj 矩阵 + viewport 尺寸
    const MMatrix viewProj = frameContext.getMatrix(MHWRender::MFrameContext::kViewProjMtx);
    int ox, oy, w, h; frameContext.getViewportDimensions(ox, oy, w, h);
    for (const MPoint& wp : worldPts) {
        const MPoint clip = wp * viewProj;             // 行向量：world → clip
        if (clip.w <= 0.0) continue;                   // 相机背后 → 跳过（防 w<0 投影翻转）
        const double nx = clip.x / clip.w, ny = clip.y / clip.w;
        if (nx < -1 || nx > 1 || ny < -1 || ny > 1) continue;  // 视锥外
        dm.circle2d(MPoint((nx*0.5+0.5)*w, (ny*0.5+0.5)*h, 0.0), rPx, subdiv, true);  // 左下原点 y 上
    }

    // ❌ M3dView view = M3dView::active3dView(); view.worldToView(wp, sx, sy);
    //    active3dView() 返回【有焦点】的 panel；多 panel 下每个 panel 的 addUIDrawables 都拿焦点 panel
    //    的相机投影 → 非焦点 panel 的 2D UI 落到错位置（拖一个视口，其它视口的点跟着跑到它的位置）。
}
```

**为什么单 panel 测不出**：单 panel 时 `active3dView()` == 正在绘制的那个 panel，`worldToView` 恰好用对相机
→ 位置正确。**只有多 panel（split/四视图）才暴露**——比 headless-测不到更隐蔽：**GUI 单 panel 也是对的**，
必须开多 panel 实测才咬人。

**注意**：纯 **3D** 原语（`dm.points`/`dm.line`/`dm.circle` 世界坐标）**没有**这个问题——MUIDrawManager 会按
每个 panel 自己的相机投影。坑只在**需要手动 world→viewport 的 2D 投屏**路径。`kViewProjMtx` 语义 = world→clip
（`kViewMtx` 已含 world→view）；`circle2d` 的 2D 空间 = viewport 本地像素、左下原点 y 上，与 `worldToView`
的 port 坐标同约定（所以单 panel 下两者等价）。

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| C++ 拼 `cmd <object> -flag` | `Flags must come before objects` 解析失败 | flag 在前、object 在后 |
| 只用 `cmds`-Python 测命令、不测 MEL 字符串形式 | flag/object 顺序 bug 漏到 GUI | 加一条 `executeCommand` MEL 字符串形式回归 |
| `buildDrawData` 只 clear 容器、漏重置 bool flag | 状态清了但高亮/描边不消失 | 每个 transient flag 每帧显式置 false |
| 把 GUI 显示问题当"数据没清" | 查错方向（数据其实清了，是 draw data 残留） | 先查 prepareForDraw oldData 复用 + flag 重置 |
| `rect()/circle()` + `系数×相机距离` 求屏幕恒定 | 透视/正交下大小漂 | `points()`+`setPointSize`（像素） |
| `addUIDrawables` 里 2D 投屏用 `active3dView().worldToView` | 多 panel 下非焦点视口投错（单 panel 正常，更隐蔽） | 用 `frameContext` 的 `kViewProjMtx` + `getViewportDimensions` 自投 |

## 项目实例参考

某 Maya 角色形变插件（curvenet 曲线编辑工具，单 `.mll` + VP2.0 draw override + MPxContext）一次性踩齐三条：

- context 里发 `caCurvenetEdit <node> -split/-delete ...`（object 在前）→ GUI 点击插点/删点报
  `Flags must come before objects`；headless `cmds.caCurvenetEdit(node, split=...)` 全绿没暴露。改成
  `-split <i> <t> <node>` + 加 MEL 字符串形式 headless 回归后修复。
- 删点后橙色选中框不消失：`buildDrawData` 只 clear 了数组 + `hasPen`，漏重置 `hasSel`/`hasHover`；
  `prepareForDraw` 复用 `oldData` → 上帧 `hasSel=true` 残留。补 `d.hasSel=false; d.hasHover=false`。
- 选中框用 `rect()` + `系数×相机距离`，相机拉远拉近大小在变。改成 `points()`+`setPointSize`
  （大底方点 + 正常点盖上 = 屏幕空间恒定描边框）。

后续（同项目，第 4 条）：编辑态控制点改画 2D 圆（`circle2d`），投屏初版用 `M3dView::active3dView().worldToView`。
单 panel 一切正常、51/51 headless 全绿；开四视图后发现**拖一个视口，其它视口的圆点跟着跳到该视口的点位**——
`active3dView` 取的是焦点 panel 的相机。改用 `addUIDrawables` 传入的 `frameContext`（`kViewProjMtx` +
`getViewportDimensions`）自投 world→viewport 后修复（配套：Ctrl→Shift 态变化时 `refresh(all=true)` 让所有 panel 同步重绘）。

## 相关 Guidelines

- [`selection-context-and-undo.md`](selection-context-and-undo.md) / [`manip-container-constraints.md`](manip-container-constraints.md) — 兄弟篇：manip / context 交互契约；本篇的 draw override 常跟它们配合（context 写 transient 状态、draw override 读它画）。
- [`plugin-build-and-scripting-contracts.md`](plugin-build-and-scripting-contracts.md) — `cmds.setAttr` 复杂类型格式不可靠 → OpenMaya API；跟本篇规则 1 同属"从代码调 Maya 命令/接口"的 marshalling 契约。
- [`../code/validation.md`](../code/validation.md) — "headless/单测绿 ≠ GUI 对"；本篇三条都是单测覆盖不到、必须 GUI 实测的契约，是该原则的 Maya 实例。

## 相关

- [`draw-override-performance.md`](draw-override-performance.md) —— 同一路径的**性能**契约：`isAlwaysDirty` 默认 true ⇒ 每帧重建绘制数据；热路径里的 plug 访问代价；量视口性能前先证明对象真的在被画。
