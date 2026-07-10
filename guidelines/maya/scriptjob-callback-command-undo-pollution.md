# scriptJob / 回调里逐条 `cmds.setAttr` 淹没 undo 队列（+ standalone undo 观测坑）

选择 / 属性驱动的 UI（选中某物 → 显隐一批辅助物、刷新派生显示态）常挂在 `scriptJob` 回调里。
若回调遍历 N 个节点各跑一条 undoable 命令（`cmds.setAttr` / `cmds.rotate` / …），**每条各自进
undo 队列、不自动合并**，一次触发就用 N 条 undo 淹没队列——用户一次编辑后要按几十上百次 Ctrl+Z
才回到真正的改动。Maya 文档没明说，靠踩坑得到。非 Maya 项目可 skip 本目录。

## 核心规则

1. **scriptJob / callback / evalDeferred 回调里连续跑的多条命令，不被自动合成一个 undo chunk**——
   每条 `cmds.setAttr` 都是独立 undo 项。选择驱动的显隐这样写 = 一次选择变化压进 N 条 undo。
2. **纯显示 / 派生态的写**（视觉辅助显隐、xray、其它不属于用户编辑语义的状态）本就不该进 undo 历史，
   包 `cmds.undoInfo(stateWithoutFlush=...)` **停记账**。关键用 `stateWithoutFlush=`（**不 flush**
   用户已攒的队列），不是 `state=`（会连带 flush 掉整条历史）。比 `openChunk/closeChunk`（合成 1 条）
   更合适——显示切换根本不该出现在 undo 里，合成 1 条仍是"看不懂的显示翻转"undo 项。

## 机制

Maya undo 队列只记经命令引擎执行的命令。GUI 里手动敲一条命令，命令引擎把它（含内部）包成一个
undo chunk。**但 scriptJob / 回调里连续跑的多条命令不被自动包 chunk** → 每条独立入队。于是
"选中变化 → 回调遍历 N 个 helper 各 `setAttr` 显隐" = N 条 undo；N 上百时一次取消选中 = 上百条。

修法本质：这些是**显示态**（视觉辅助的显隐），语义上不属于用户编辑历史，应完全不进 undo。

```python
import contextlib

@contextlib.contextmanager
def _no_undo():
    """临时停 undo 记账（不 flush 已有队列）：包纯显示状态写用。"""
    state = cmds.undoInfo(q=True, state=True)
    cmds.undoInfo(stateWithoutFlush=False)          # 停记账，保留用户已攒的队列
    try:
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=state)

def _set_handles_visible(indices, visible):
    with _no_undo():                                # 纯显示切换，不进 undo
        for i in indices:
            cmds.setAttr("helper_%d.visibility" % i, visible)
```

把 `_no_undo` **下沉到写显示态的 chokepoint helper 里**，所有调用方（选择回调 / 手动菜单 / 面板
刷新）一处覆盖，不必逐个入口包。

## 诊断坑：standalone mayapy 里 `undoName` 恒空

定位"一次操作产生多少条 undo"时：

- **GUI scriptJob 回调不易 headless 复现**（scriptJob 是 GUI 机制，batch/standalone 不注册）。
  但可**直接调回调函数体**（绕过 scriptJob 注册）量 undo 队列增长——机制一致。
- **`cmds.undoInfo(q=True, undoName=True)` 在 standalone 恒返回 `''`**（即使队列非空），无法靠它
  walk 队列。改用 `undoQueueEmpty` 循环计数：
  ```python
  cmds.undoInfo(state=True, infinity=True)          # standalone 先确保记账开着
  def count_undo():
      n = 0
      while not cmds.undoInfo(q=True, undoQueueEmpty=True):
          cmds.undo(); n += 1                        # undoQueueEmpty 会随操作正确翻 True/False
      return n
  ```

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| scriptJob 回调遍历 N 节点各 `cmds.setAttr` 显隐 | N 条 undo，一次选择变化淹没队列 | 显示态写包 `undoInfo(stateWithoutFlush)` |
| 用 `openChunk/closeChunk` 合成 1 条 | 仍留 1 条"看不懂的显示翻转"undo | 显示态根本不该进 undo → `stateWithoutFlush` 停记账 |
| 用 `undoInfo(state=False)` 关 undo | 连带 flush 用户已有历史 | 用 `stateWithoutFlush=` |
| headless 靠 `undoInfo(q=True,undoName=True)` walk | standalone 恒返回 `''`，数不出 | 用 `undoQueueEmpty` 循环计数 |
| 把"手动菜单显隐"当该 undo | 手动全隐 N helper = N 条 undo | 同包 no-undo（显示态一律不进 undo） |

## 项目实例参考

curvenet Maya 插件：每控制点建 edit locator + 切线手柄 locator；`SelectionChanged` scriptJob
回调按选中端点显隐其名下切线手柄（+ xray）。184 手柄场景实测：一次"取消选中"回调对全部手柄逐个
`setAttr(visibility)` + `setAttr(alwaysDrawOnTop)` = **736 条 undo**；拖一个 locator 编辑（原生
Move 工具）只 1 条，于是撤销要按几百次才越过取消选中、回到真正编辑。修法：`_no_undo()`
（`undoInfo(stateWithoutFlush=...)`）下沉进两个显隐 chokepoint helper + 手动显隐命令 + 工具刷新，
**736 → 0**，显隐行为不变。诊断时发现 standalone `undoName` 恒空，改 `undoQueueEmpty` 计数才量出 736。

## 相关 Guidelines

- [`selection-context-and-undo.md`](selection-context-and-undo.md) —— C++ MPxSelectionContext /
  manip 自持拖拽的 undo 契约（plug-based undo / MPxToolCommand / stock manip resync）。本条是
  **Python scriptJob / 回调侧**的 undo 污染，不同机制、互补。
- [`plugin-build-and-scripting-contracts.md`](plugin-build-and-scripting-contracts.md) —— 另一条
  Python `cmds` 侧脚本契约（`cmds.setAttr type=pointArray` 格式不可靠 → OpenMaya `MFn*Data`）。
- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) —— 本条定位靠"直接调
  回调体 + `undoQueueEmpty` 计数"取证，不靠猜；两个竞争假设（拖拽入队 vs 取消选中入队）用计数区分。
- [`../code/validation.md`](../code/validation.md) —— headless 计数 + 用户报"好多次 undo"的症状互相印证。
