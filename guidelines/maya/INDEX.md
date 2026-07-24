# Maya Guidelines 索引

Maya C++ 插件（`MPx*` plugin / manip / context / 多 `.mll` 共享 base 层）的 framework
hidden contracts。靠踩坑得到、Maya 官方文档没明说的客观约束。

**非 Maya 项目可整段 skip 本目录。** 通用编程 / C++ / 工程组织规则在
`guidelines/cpp/` / `guidelines/code/` / `guidelines/workflow/`。

## 按子领域分类

### Manip / Context / Undo（viewport 交互）

| Guideline | 解决的问题 |
|---|---|
| [`manip-container-constraints.md`](manip-container-constraints.md) | 自定义 MPxManipContainer：setPoint 定位 / setManipScale vs setGlobalSize / connectToPointPlug 自引用崩溃 / 无 plug 不调基类 connectToDependNode / 动态 rebuild 序列 / setVisible 显隐 / VP1.0 vs VP2.0 绘制 / **Maya 不自动调容器 connectToDependNode → context 必须显式调**（否则 finishAddingManips 不跑、stock 子 manip 不显示；只挂自绘 manip 时零症状，加 stock 才炸） |
| [`selection-context-and-undo.md`](selection-context-and-undo.md) | MPxSelectionContext + **manip 自持拖拽**：3-param vs 1-param doPress 双重载 / doPress 不立即更新选择集 → 自己 hit-test / selectFromScreen 重入 / plug-based undo 覆盖不了多关节 IK → MPxToolCommand + 快照 / **finalize() 从 manip 自持 doRelease 不入 undo 队列 → 走 executeCommand 普通命令** / **stock rotate/scale manip 值·朝向 undo/redo 不还原 → MEventMessage Undo/Redo 回调 resync** |
| [`move-rotate-manip-axis-orientation.md`](move-rotate-manip-axis-orientation.md) | 原生 Move/Rotate 工具「Object」轴向取自旋转管线不同段：Move 反映 rotateAxis、Rotate **不**反映（只看 父级∘rotate）。要 Rotate gizmo 对齐自定义帧须放**父级 transform 的 rotate**（放 rotateAxis 只改驱动、gizmo 不跟 →"驱动对朝向错"）。含逐 attr 实测诊断 |
| [`scriptjob-callback-command-undo-pollution.md`](scriptjob-callback-command-undo-pollution.md) | **Python scriptJob / 回调侧** undo 污染（上一条是 C++ 侧，互补）：回调里逐条 `cmds.setAttr` 各自入队、不自动合 chunk → 选择驱动的 helper 显隐一次触发 N 条 undo 淹没队列（实测 184 手柄 = 736 条/次取消选中）。修法：纯显示态写包 `undoInfo(stateWithoutFlush=...)`（停记账、**不 flush** 用户历史；≠ `state=`），下沉到显隐 chokepoint helper。含诊断坑：standalone `undoInfo(q, undoName)` 恒空 → 用 `undoQueueEmpty` 循环计数 |

### 运行时 draw / 命令调用（GUI/C++ 契约，headless + cmds-Python 测不到）

| Guideline | 解决的问题 |
|---|---|
| [`draw-override-and-command-invocation.md`](draw-override-and-command-invocation.md) | 从 C++ `executeCommand` 发带 object 的命令：MEL 字符串 flag 必须在 object 前（cmds-Python 自动排序、MEL 不会）/ `MPxDrawOverride::prepareForDraw` 复用 `oldData` → `buildDrawData` 每帧必须重置 transient flag（否则"状态清了但高亮不消失"）/ 屏幕空间恒定 UI 用 `points()`+`setPointSize`（像素），别用 `rect()/circle()` 世界尺寸×相机距离近似 |

### GPU deformer / GUI 自动化 / 性能取证

| Guideline | 解决的问题 |
|---|---|
| [`gpu-deformer-gui-validation.md`](gpu-deformer-gui-validation.md) | `mayapy` 不能证明 GPU Override 真执行；GPU Active + 每节点新 success marker + 非零形变 + CPU 对照四重 Gate / `deformerEvaluator` 加载顺序 / CPU 读回污染 / `maya.exe -script bootstrap.mel` + Qt timer / licensing 与 crash 分类 / auxiliary mesh buffer 与显式 CPU fallback / 半初始化节点先由 validate 拒绝、conditional generation 最后提交 |
| [`parallel-deformer-performance-profiling.md`](parallel-deformer-performance-profiling.md) | Parallel Evaluation 下区分 wall time、interval union 和 per-frame work sum / nested scope 与单节点 outer duration 不直接归因 / ready 与非零激发 Gate / bypass-frozen 消融测 wall 收益上限 / P50-P95 与长尾复测 |

### Mesh 拓扑 / 数值复现

| Guideline | 解决的问题 |
|---|---|
| [`mesh-topology-fidelity.md`](mesh-topology-fidelity.md) | polygon 顶点列表不能唯一确定 Maya 表面；复刻最近点/绑定/权重时必须保存 `MFnMesh::getTriangles` 的实际 triangulation + triangle→polygon 映射，非共面 quad/n-gon 防 fan triangulation 假一致 |

### Build / 迭代 / 输出 / 脚本（工程化，非运行时）

| Guideline | 解决的问题 |
|---|---|
| [`plugin-build-and-scripting-contracts.md`](plugin-build-and-scripting-contracts.md) | DevKit cmake 把 C++ 标准压回 14（`MAYA_WANT_CPP_17` / target 级 override）/ 加载中的 `.mll` 不能覆盖（重建前 unloadPlugin）/ `MGlobal::displayInfo` 非 ASCII 在本地化 Windows 乱码 / `cmds.setAttr type=pointArray` 格式不可靠 → OpenMaya `MFn*Data`+`setMObject` / attribute long name 在节点全局唯一（含 compound child） |

### 配套 skill（设计阶段触发，不 eager-import）

| Skill | 内容 |
|---|---|
| [`skills/maya/maya-tool-interaction`](../../skills/maya/maya-tool-interaction/SKILL.md) | DCC 拖拽编辑交互模式：press-time 完整重算 / press-time caching 防反馈漂移 / 位移阈值防抖 / snapshot-diff undo / undo 数据存业务对象而非 UI |
| [`skills/maya/reverse-maya-closed-nodes`](../../skills/maya/reverse-maya-closed-nodes/SKILL.md) | 闭源 Maya 节点行为复刻：Ghidra/汇编/运行探针/差分 oracle/真实资产的分层证据链；防信伪代码、未激发测试、单合成夹具外推完成 |
| [`skills/architecture/multi-plugin-shared-core`](../../skills/architecture/multi-plugin-shared-core/SKILL.md) | 框架无关：多插件共享一个 core 实体的架构（ExtensionContainer / feature-parser 注册 / Preset→Template→Instance / Snapshot+Ops / 非拥有 Registry / 权威类型不可扩展时编辑层 state 复用既有值）。Maya 多 `.mll` 场景的实际归宿 |

### C++/构建底座（非 Maya，但 Maya 插件常踩）

Maya C++ 插件是典型的多 `.mll`（多 DLL）+ cmake/VS 场景，下列底座坑高频命中，已单独成类：
- [`../cpp/multi-dll-plugin.md`](../cpp/multi-dll-plugin.md) — 跨 DLL 单例 / 符号导出 / 初始化顺序
- [`../cpp/build-incremental-and-cmake.md`](../cpp/build-incremental-and-cmake.md) — 增量编译 ABI 不一致 / cmake 重构后 stale .vcxproj
- [`../cpp/hot-path-cpp.md`](../cpp/hot-path-cpp.md) — 大对象传递 move/copy / dynamic_cast 热路径
- [`../cpp/windows-native-crash-hang-evidence.md`](../cpp/windows-native-crash-hang-evidence.md) — Windows native crash/hang 分类 / 二进制 path+size+mtime+SHA-256 身份 / 只重试 fixture 启动前失败 / timeout 先取证再 kill / Break All 全线程 / normal dump→按需 full heap / WinDbg RVA 映射 / race 结论门槛

---

## 待补充（Deferred）

下列经验已识别但暂未成文，待第二个相关项目验证后补：

- **Maya × ML 模型集成簇**（TorchScript / PyTorch 推理插件）：
  - JIT 模型必须启动时 warmup（dummy inference on all code paths），重构迁移时别漏掉 warmup 调用点
  - 模型单帧推理能力要实测确认，C++ wrapper 的保守 shape 检查（如 `denseF<=1` 拒绝单帧）可能过严
  - 调模型前做输入张量 shape / range 前置校验，错误在调用侧暴露
  - 有状态模型接口（init → select → edit → infer）的合法调用序列要在 C++ binding 层编码 + 文档化
  - **Maya 行向量约定 vs PyTorch 列向量约定**：`MEulerRotation::asMatrix()` 是行向量；传旋转给模型时方向向量读 col、6D rotation 读 row，转换点必须注释
  > 触发补写时机：下一个接 ML 模型的 Maya 插件开工时。
