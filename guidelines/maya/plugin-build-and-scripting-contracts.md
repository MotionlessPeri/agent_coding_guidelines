# Maya C++ 插件 build / 迭代 / 输出 / 脚本的 hidden contracts

写 / 迭代一个 Maya C++ 插件（`MPx*` `.mll`）时，**非 manip/context 运行时行为**那一层——构建工具链、热迭代循环、面向 Maya 的字符串输出、Python `cmds` 设属性——的一组官方文档没明说、只能靠踩坑得到的约束。跟 `manip-container-constraints.md` / `selection-context-and-undo.md`（运行时交互契约）是同目录的兄弟篇，但作用层不同。非 Maya 项目可 skip。

## 核心规则

1. **DevKit 的 cmake（`devkit.cmake`）在未设 `MAYA_WANT_CPP_17` 时把 `CMAKE_CXX_STANDARD` 强制压回 14**——会盖掉顶层的 17/20。插件 target 显式 `set_target_properties(... CXX_STANDARD ...)` 锁回。
2. **加载中的 `.mll` 在 Windows 上不能被覆盖**——重建前先 `unloadPlugin`（或关 Maya），否则 POST_BUILD 拷贝 / 重链接报 `Permission denied`。
3. **`MGlobal::displayInfo` 等面向 Maya 输出的 `MString` 里别放非 ASCII 字面量**——本地化 Windows 的 Script Editor 按本地 codepage 解释 UTF-8 字节 → 乱码。诊断日志用 ASCII。
4. **`cmds.setAttr(..., type="pointArray"/"vectorArray"/…)` 的参数格式不可靠**——撞 `Error reading data element` 时退到 OpenMaya `MFn*Data` + `plug.setMObject()`。
5. **attribute 的 long name 在节点全局唯一**——顶层 attribute 与 `compound child` 不属于不同命名空间；重复名称必须在注册前拦截。

---

## 1. DevKit cmake 把 C++ 标准压回 14

DevKit 经 `pluginEntry.cmake` → `devkit.cmake`，在 `MAYA_WANT_CPP_17` 未设时把 `CMAKE_CXX_STANDARD` 强设回 **14**（Maya 2022 实测）。它 include 的时机在顶层 `set(CMAKE_CXX_STANDARD 17/20)` **之后**，于是把你设的标准盖掉。

**症状**：用 `<optional>` / 任何 C++17+ 特性的**插件 TU** 报 `'optional' is not a member of 'std'` / `STL4038` / `C2039`。**迷惑点**：同 repo 里**不走 `build_plugin()` 宏**的 target（如纯算法静态库、单测 exe）不受影响，照常编 —— 于是出现"一部分编得过、一部分编不过"。

**修法**（二选一）：
```cmake
# (a) target 级覆盖目录级（推荐：不依赖 devkit 内部变量名）
build_plugin()
set_target_properties(${PROJECT_NAME} PROPERTIES
        CXX_STANDARD 17           # 或 20
        CXX_STANDARD_REQUIRED ON
        CXX_EXTENSIONS OFF)
```
```cmake
# (b) devkit 的官方旋钮，须在 include devkit 之前设
set(MAYA_WANT_CPP_17 ON)
```

**跨版本**：标准号随 Maya 版本 / devkit 变，每接新 devkit 先 `grep CMAKE_CXX_STANDARD` 在 devkit cmake 里确认它压到几、是否还认 `MAYA_WANT_CPP_17`。

> 注意：若顶层升到 C++20 而插件 target 仍 override 成 17，插件会**停在 17**——功能多数无碍（17 已够 `<optional>` 等），但与 core 等 C++20 TU 的标准不一致。要让插件也走 20，先验证该版本 devkit 头在 C++20 下编译干净，再 bump override。

## 2. 加载中的 `.mll` 不能覆盖（重建前先卸载）

Windows 锁定已加载的 DLL。Maya `loadPlugin` 后，那个 `.mll` 文件被锁；cmake **POST_BUILD 把新产物拷到该位置 / 重链接覆盖它** → 失败。

**症状**：编译 + 链接**成功**，但 POST_BUILD 自定义命令失败 `MSB3073` + `Permission denied (output)`；或链接阶段直接写不进目标 `.mll`。

**修法**：重建前在 Maya 里
```python
import maya.cmds as cmds
cmds.file(new=True, force=True)          # 先清掉用到该节点类型的场景，否则 unload 失败
cmds.unloadPlugin("<pluginName>")
```
或直接关 Maya。**cold build / CI 不受影响**（无 Maya 持锁）。

**诊断推论**：被锁的是"运行时加载位置"（如 POST_BUILD 拷到的 module / pack 目录里那份），中间产物（`build/.../Release/*.mll`）通常没被锁。**看哪个路径的时间戳没更新**，就知道是它被锁。

## 3. `MGlobal::displayInfo` 非 ASCII 字面量在本地化 Windows 乱码

`MGlobal::displayInfo` / `displayWarning` / `displayError`，以及任何面向 Maya UI 的 `MString`，里面的**非 ASCII 字符串字面量**（源文件 UTF-8 字节）在本地化 Windows（如中文 cp936）的 Script Editor 被按**本地 codepage** 解释 → 乱码。`MString` 不携带源编码信息，无从纠正。

**适用面**：`displayInfo` 系列、`MStatus::perror` 的非 ASCII 消息、command `setResult` 的非 ASCII 文本——凡是会显示在 Maya 里的 `MString`。

**修法**：**面向 Maya 输出的诊断 / 日志字符串一律 ASCII（英文）**。中文留给**源码注释**（注释不进 `MString`，不受影响）。需要真正面向用户的多语言文案时，走 Maya 的本地化资源机制，**不要**靠源码里塞 UTF-8 字面量。

> 这条尤其坑：诊断日志（如"结构脏 rebuild / 姿势脏 re-solve"这类状态观察）的**全部价值是可读**；乱码 = 观察性废掉，功能虽对却看不出对在哪。

## 4. `cmds.setAttr` 设 typed/array 属性的格式不可靠

`cmds.setAttr(plug, ..., type="pointArray" / "vectorArray" / …)` 的参数排布（前导 count + 每元素分量数）在不同 Maya 版本 / 属性类型上表现不一致，常报 `setAttr: Error reading data element number N`。

**修法**：退到 OpenMaya 2.0 直接设 plug——
```python
import maya.api.OpenMaya as om
node, attr = plug.rsplit(".", 1)
sel = om.MSelectionList(); sel.add(node)
fn_plug = om.MFnDependencyNode(sel.getDependNode(0)).findPlug(attr, False)
arr = om.MPointArray([om.MPoint(*p) for p in pts])
fn_plug.setMObject(om.MFnPointArrayData().create(arr))
```
**同样触发 DG 脏传播 + 节点的 `setDependentsDirty`**，行为与 `setAttr` 等价但稳。

**通用化**：任何"经 `cmds` 设复杂 typed / array 属性"撞格式坑，优先退到 OpenMaya `MFn*Data` + `plug.setMObject()` / `setMPxData()`。

## 5. Attribute long name 是节点全局命名空间

`MFnNumericAttribute::create()` 等函数创建的 long name 必须在整个节点类型内唯一。`compound child`、顶层 attribute
以及其它 compound 下的 child 共用同一个节点全局命名空间；compound 层级不能用来隔离重名。

重复名称可能先表现为 attribute 创建失败或返回无效对象，随后才在 `addAttribute()`、连接或节点求值阶段暴露为空指针、
注册失败或宿主崩溃。不要只在失败点补空值判断，应从定义源消除重名，并增加机械检查：

- 枚举该节点所有 `MFn*Attribute::create()` 的 long name；
- 在测试中断言集合大小等于定义数量；
- 对生成式 attribute 定义，在生成阶段维护同一份名称集合；
- 改 compound 布局或从单输入扩展到 multi 输入时重新运行检查。

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| 顶层设 `CMAKE_CXX_STANDARD 17/20` 就以为插件按它编 | devkit 把插件压回 14，`<optional>` 等编不过 | 插件 target 级 `set_target_properties(CXX_STANDARD ...)` |
| "一部分 target 编得过"就以为标准没问题 | 非 `build_plugin()` 的 target 不受 devkit 影响，掩盖真因 | 看报错的是不是插件 TU |
| Maya 开着直接重建 | POST_BUILD 拷贝 / 链接 `Permission denied` | 重建前 `unloadPlugin` 或关 Maya |
| 把构建当"代码错"反复查 | 根因是文件锁 / cmake，不是逻辑 | 看哪个 `.mll` 路径时间戳没更新 |
| `displayInfo("中文...")` | 本地化 Windows Script Editor 乱码 | 面向 Maya 输出用 ASCII；中文留注释 |
| `cmds.setAttr(..., type="pointArray")` 凑格式 | `Error reading data element` | OpenMaya `MFn*Data` + `setMObject` |
| compound child 沿用顶层 long name | 属性创建失败，后续可能空指针或崩溃 | 节点级扫描所有 long name，注册前断言无重复 |

## 项目实例参考

某 Maya C++ deformer 插件（curvenet 论文复刻的形变求解外壳：单 `.mll` + 一个不依赖 Maya 的纯几何 core 静态库）在立"插件外壳 + 占位形变"那一轮**一次踩齐 4 条**：

- DevKit 把 `CMAKE_CXX_STANDARD` 压回 14，插件里 `std::optional` 成员编不过（而 core 静态库 / 单测 exe 不走 `build_plugin()` 照常编，迷惑）；`build_plugin()` 后对插件 target `set CXX_STANDARD` 修复。
- 重建时 POST_BUILD 把 `.mll` 拷到打包目录报 `Permission denied`——因 Maya 正加载着那份副本；`unloadPlugin` 后 OK。其后顶层标准被另一改动 bump 到 C++20，插件 override 仍 17、共存正常（见 §1 注）。
- `MGlobal::displayInfo` 输出的中文状态日志（"重建预计算 / 重 solve"）在中文 Windows Script Editor 乱码；改 ASCII 英文后可读。
- smoke 脚本 `cmds.setAttr(plug, ..., type="pointArray")` 报 `Error reading data element number 2`；改 `MFnPointArrayData` + `plug.setMObject()` 后稳定。

## 相关 Guidelines

- [`../cpp/build-incremental-and-cmake.md`](../cpp/build-incremental-and-cmake.md) — 通用 C++ / cmake / MSVC 构建坑（增量编译 ABI / stale `.vcxproj`）；本篇 §1 是 Maya devkit 对它的特化。
- [`../cpp/multi-dll-plugin.md`](../cpp/multi-dll-plugin.md) — `.mll`（多 DLL）符号导出 / 单例 / 初始化顺序；本篇 §2 是同一 DLL 视角下的"文件锁"维度。
- [`INDEX.md`](INDEX.md) — Maya guidelines 索引（本篇归"Build / 迭代 / 输出 / 脚本"子领域）。
- [`manip-container-constraints.md`](manip-container-constraints.md) / [`selection-context-and-undo.md`](selection-context-and-undo.md) — 兄弟篇，覆盖 manip/context **运行时**契约。
