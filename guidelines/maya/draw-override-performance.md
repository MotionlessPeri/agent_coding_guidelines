# MPxDrawOverride 视口性能：每帧重建的默认值，与「量之前先证明在画」

自定义 locator 一进场景视口就掉到个位数帧率，而且**不动它、只拖相机也掉**。两个独立
成因，都在绘制路径上；外加一条测量纪律，因为这类问题的假阴性长得像好消息。

## 1. `isAlwaysDirty` 默认 **true** —— 每次刷新都重建绘制数据

```cpp
MPxDrawOverride(const MObject& obj, GeometryDrawOverrideCb callback, bool isAlwaysDirty = true);
```

两参数构造 = 取默认值 = **每次视口刷新都调 `prepareForDraw`**，跟节点脏不脏无关。
于是转个相机就把所有实例的绘制数据整个重算一遍。

⚠️ 这个默认值是最贵的那个，而写代码时**不会有任何提示**：两参数构造看起来完全正常，
功能也对，只是慢。实测一个采样曲线 locator：6 个实例 × 每次 15.5 ms = 97 ms 一帧
（10 fps）；隐藏这些 locator 立刻回到 350+ fps。

**修法**：显式传 `false`。

### 但必须**成对**配判据 —— 反方向的失败是静默的

`isAlwaysDirty=false` 的风险在另一头：数据变了却不重画，显示旧形状，**不报错**。
所以不能只改一行就算完，要同时钉住两个方向：

| 场景 | `Vp2UpdateDagObject` 每帧次数 |
|---|---|
| 静止刷新（只转相机） | 必须 **0** |
| 改一个输入属性后刷新 | 必须 **≥1** |

只验前者会把「永远不重画」判成成功。两条都验过，这个改动才算完成。

⚠️ 传 `false` 的前提是**节点的变化真的会把它弄脏**。走 `MPlug::setValue` 的写入会；
而「按当前时间绘制」「按选中状态绘制」这类**不经过属性变化**的显示逻辑不会 —— 那种
locator 传 `false` 就会静默不刷新。改之前先问一句：这个 locator 画什么，它的输入是不是
都在属性上。

## 2. 热路径里逐元素重算「整个对象只需算一次」的东西

单次 `prepareForDraw` 15.5 ms 去画 900 个采样点，是不正常的。真因是每个控制点都在
重新推导整条曲线的元信息：

```
读一个控制点()
  ├─ 取数组 plug                    一次 networked findPlug
  ├─ 判这个手柄合不合法()            ← **又跑一遍「建立活动顺序」**
  │     └─ 2× networked findPlug + 2× getExistingArrayAttributeIndices + 排序
  └─ 读值 → 判下标存不存在()          又一次 getExistingArrayAttributeIndices
```

一个 19 元素的对象每帧 ≈ **146 次 networked `findPlug` + 146 次数组下标枚举**。

两个 Maya 特有的代价来源，都容易被当成「随手一调」：

- **`findPlug(attr, wantNetworkedPlug=true)`** 比 `false` 贵得多。只是**读值**时用 `false`；
  要 plug 身份 / 连接信息才需要 `true`。
- **`getExistingArrayAttributeIndices()`** 每次都分配 `MIntArray` 并枚举整个稀疏数组。
  写成 `hasLogicalIndex(plug, i)` 这种「查一个下标在不在」的 helper 时尤其危险 ——
  调用点看起来是 O(1)，实际每次都枚举全表。

**修法**：把「整个对象只需算一次」的东西提到函数入口 —— 数组 plug、已存在下标集合
（排序后二分）、以及任何靠遍历推导出来的元信息（首末元素、顺序表）。逐元素只留下
真正逐元素的操作。实测 15.5 ms → 0.72 ms（21×）。

**改的范围要收窄**：只改热路径那个函数，别去改被别处复用的通用 accessor —— 那种改动
的验证面大得多，而收益只在这一处。

## 3. 量视口性能之前，先证明被测对象真的在被绘制

这条不是优化技巧，是**测量纪律**，因为这类问题的假阴性**长得像好消息**：对象没被画的时候，
帧率非常好看。

**判据**：Maya profiler 里 **`Vp2UpdateDagObject` 的每帧次数**。它接近 0 就说明对象被剔了
或根本没显示 —— 那一档的 fps **跟绘制开销无关**，不能拿来判断。次数正好等于实例数，
才说明测到了。

采样方式（`cmds.profiler`）：

```python
cmds.profiler(sampling=True)
# ... 转相机 + cmds.refresh(force=True) 若干次 ...
cmds.profiler(sampling=False)
n = cmds.profiler(q=True, eventCount=True)
# 逐条 eventIndex 取 eventName / eventCategory / eventDuration 汇总
```

嵌套关系（自顶向下）：`Vp2SceneRender` ⊃ `Vp2UpdateScene` ⊃ `Vp2BuildRenderLists`
⊃ `Vp2UpdateDagObject`。**绘制数据重建的开销落在最内层**，而实际光栅化在
`Vp2Draw3dBeautyPass`。两者的比例直接回答「时间是花在画，还是花在准备画」。

最锋利的一刀是**隐藏/恢复对照**（一行的事，不改场景）：

```python
for t in transforms: cmds.hide(t)     # 量一次
for t in transforms: cmds.showHidden(t)  # 再量一次
```

实测 9.7 → 335.6 → 9.0 fps，35 倍，判定完毕，不必再猜。

### 三次假阴性，每次都报「一切正常」

同一次排查里，自动化测量连着三次给出「370 fps，没问题」，三次都是**量具坏的**：

1. 改测试启动器时 `str.replace()` **漏了断言**，替换静默没生效 ⇒ 跑的是旧 fixture，退出码 0
2. 测量函数里写死转 `persp`，而面板显示的是别的相机 ⇒ 转了一个没人看的东西
3. 当前时间落在会话窗口之外 ⇒ 那些 locator 本来就不显示，自然不画也不耗时

三次的表层原因完全不同，共同点是**失败形态一致：什么都很快**。⇒ 这类测量必须有一个
「被测对象真的参与了吗」的独立判据（这里就是第 3 节那个次数），否则你分不清
「优化得好」和「根本没测到」。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| `MPxDrawOverride(obj, cb)` 两参数构造 | 每帧重建绘制数据，实例一多就掉到个位数帧率 | 显式传 `isAlwaysDirty=false` |
| 只验「改完不再每帧调」就收工 | 可能已经变成「永远不重画」，而且不报错 | 成对验：静止 0 次 / 改动后 ≥1 次 |
| 给「按时间 / 按选中状态」绘制的 locator 传 `false` | 那些变化不经过属性，节点不脏 ⇒ 静默不刷新 | 先确认输入都在属性上 |
| 热路径里逐元素调通用 accessor | 每个元素重算整个对象的元信息 | 对象级信息提到函数入口算一次 |
| 只为读值却用 `findPlug(attr, true)` | networked plug 查找贵得多 | 读值用 `false` |
| 用 `hasLogicalIndex(plug, i)` 逐个查下标 | 调用点看着 O(1)，实际每次枚举整个稀疏数组 | 取一次下标集合，排序后二分 |
| 拿 fps 判绘制开销，不看对象有没有被画 | 对象被剔时帧率很好看 —— 假阴性像好消息 | 先看 `Vp2UpdateDagObject` 每帧次数 |
| 顺手把被别处复用的通用 accessor 一起优化 | 验证面放大，收益只在一处 | 只改热路径那个函数 |

## 诚实边界

**单项目、一次事件**，不满足 [`knowledge-promotion.md`](../workflow/knowledge-promotion.md)
的两击规则。促升理由走的是另一条：**外部框架的 hidden contract** —— `isAlwaysDirty` 的
默认值就是最贵的那个，而两参数构造在代码里毫无异常相；这类只能靠明写规矩兜。

第 2 节的具体数字（146 次 / 15.5 → 0.72 ms）来自一个采样曲线 locator，别当普适常数；
可搬的是**机制**（逐元素重算对象级信息 + 两个 Maya 特有的贵操作）。
第 3 节的三次假阴性出自同一次排查，机制清楚可复述，但同样未跨项目验证。apply-and-refine。

## 相关

- [`draw-override-and-command-invocation.md`](draw-override-and-command-invocation.md) ——
  同一路径的**正确性**契约（`prepareForDraw` 复用 `oldData` 要重置 transient flag /
  屏幕空间恒定 UI 用 `points()`）。本条管性能，两者互补
- [`parallel-deformer-performance-profiling.md`](parallel-deformer-performance-profiling.md) ——
  另一类性能取证（Parallel Evaluation 下 wall time vs work sum），同样强调「先证明激发」
- [`gpu-deformer-gui-validation.md`](gpu-deformer-gui-validation.md) ——
  真 GUI 自动化跑法（`maya.exe -script bootstrap.mel` + Qt timer），本条的测量脚本建在它上面
- [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md) ——
  「量具先自证」「对照组自己也需要被验」，第 3 节是它在视口性能上的实例
