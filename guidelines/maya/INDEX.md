# Maya Guidelines 索引

Maya C++ 插件（`MPx*` plugin / manip / context / 多 `.mll` 共享 base 层）的 framework
hidden contracts。靠踩坑得到、Maya 官方文档没明说的客观约束。

**非 Maya 项目可整段 skip 本目录。** 通用编程 / C++ / 工程组织规则在
`guidelines/cpp/` / `guidelines/code/` / `guidelines/workflow/`。

## 按子领域分类

### Manip / Context / Undo（viewport 交互）

| Guideline | 解决的问题 |
|---|---|
| [`manip-container-constraints.md`](manip-container-constraints.md) | 自定义 MPxManipContainer：setPoint 定位 / setManipScale vs setGlobalSize / connectToPointPlug 自引用崩溃 / 无 plug 不调基类 connectToDependNode / 动态 rebuild 序列 / setVisible 显隐 / VP1.0 vs VP2.0 绘制 |
| [`selection-context-and-undo.md`](selection-context-and-undo.md) | MPxSelectionContext：3-param vs 1-param doPress 双重载 / doPress 不立即更新选择集 → 自己 hit-test / selectFromScreen 重入 / plug-based undo 覆盖不了多关节 IK → MPxToolCommand + 快照 |

### 配套 skill（设计阶段触发，不 eager-import）

| Skill | 内容 |
|---|---|
| [`skills/maya/maya-tool-interaction`](../../skills/maya/maya-tool-interaction/SKILL.md) | DCC 拖拽编辑交互模式：press-time 完整重算 / press-time caching 防反馈漂移 / 位移阈值防抖 / snapshot-diff undo / undo 数据存业务对象而非 UI |
| [`skills/architecture/multi-plugin-shared-core`](../../skills/architecture/multi-plugin-shared-core/SKILL.md) | 框架无关：多插件共享一个 core 实体的架构（ExtensionContainer / feature-parser 注册 / Preset→Template→Instance / Snapshot+Ops / 非拥有 Registry）。Maya 多 `.mll` 场景的实际归宿 |

### C++/构建底座（非 Maya，但 Maya 插件常踩）

Maya C++ 插件是典型的多 `.mll`（多 DLL）+ cmake/VS 场景，下列底座坑高频命中，已单独成类：
- [`../cpp/multi-dll-plugin.md`](../cpp/multi-dll-plugin.md) — 跨 DLL 单例 / 符号导出 / 初始化顺序
- [`../cpp/build-incremental-and-cmake.md`](../cpp/build-incremental-and-cmake.md) — 增量编译 ABI 不一致 / cmake 重构后 stale .vcxproj
- [`../cpp/hot-path-cpp.md`](../cpp/hot-path-cpp.md) — 大对象传递 move/copy / dynamic_cast 热路径

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
