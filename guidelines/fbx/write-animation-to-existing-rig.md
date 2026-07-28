# 往「既有 DCC rig」写动画的 FBX SDK 隐藏契约

用 FBX SDK **把算出来的动画写回一个 DCC(MotionBuilder / Maya / …)导出的既有角色 rig**(而不是从零新建一副裸骨架)时,有两个文档没写、只能靠踩的契约。**从零建裸骨架的导出路径碰不到这两个坑**——它们只在"写到别人已有的 rig 节点上"时出现(典型:retarget / 动画迁移工具要把结果导成"带原角色 mesh+蒙皮"的成品)。

**非 FBX / 非「写既有 rig」场景可整段 skip。**

## 契约 1:写 `LclRotation` 必须补偿 PreRotation

FBX 节点的局部旋转不是 `LclRotation` 一个量,而是:

```
LocalRotation = Rpre · R · Rpost⁻¹
```

其中 `Rpre` = **PreRotation**(joint orient)、`R` = `LclRotation`(你能设的那个)、`Rpost` = PostRotation。**DCC 导出的 rig 骨骼普遍带 PreRotation**(joint orient 是绑定的一部分)。

→ 如果你有一个目标局部朝向 `rot`,**直接 `node.LclRotation.Set(rot)` 是错的**——漏掉了 `Rpre`。误差会**沿骨链累积**(每根骨的 preRotation 都没抵消),末端放大到离谱(实测一条手臂链写完,指尖差 **~79 cm**)。

**修法**:要让节点的有效局部旋转等于 `rot`,反解 `LclRotation`:

```
R = Rpre⁻¹ · rot · Rpost
```

即先把 PreRotation 抵掉、再乘回 PostRotation。裸骨架(自己新建的)PreRotation 为单位阵,所以老的 from-scratch 导出路径碰不到这个坑;一旦写到既有 rig 就必须补。

## 契约 2:节点旋转限位改不掉——保存重载后必被还原

既有 rig 的关节常带**旋转限位**(如肩 X ∈ [−5°, 3°])。你写的姿势超限时会被夹。想"关掉限位"以写出超范围姿势——**做不到**:

- 在 `RotationMinX/MaxX`(逐轴 bool)、`RotationActive`、或直接放宽 `RotationMin/Max` 数值三处分别改,**内存里都生效**(打印确认);
- 但**保存 + 重载后全部回到原值**——限位是 rig 定义的一部分,导出被还原。

→ **不要跟限位对抗**(改不掉),要**吸收它**:

- **按层级顺序推进**(父骨先于子骨);
- 每根骨的局部量,**相对父骨「被夹持后的真实姿势」**来算,不是相对你「本来想要的」姿势。

这样夹持误差**不向下传**:被夹的那根骨自身朝向会偏(偏掉被夹的量,无法避免——rig 就这么限的),但**它以下所有骨的位置仍精确**。实测 `max|Δpos|` 从 17.6 cm 降到 **~6e-4 cm**,只有被夹的关节自身朝向偏了夹持量(位置仍准)。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 把目标局部朝向直接 `LclRotation.Set()` 到既有 rig | 漏 PreRotation,误差沿骨链累积(末端几十 cm) | `R = Rpre⁻¹ · rot · Rpost` |
| 假设"裸骨架导出没问题 ⇒ 写既有 rig 也没问题" | 裸骨架 PreRotation=I,掩盖了坑;换既有 rig 就炸 | 写既有 rig 单独验 round-trip(末端骨位置) |
| 试图关闭/放宽 rig 的旋转限位来写超范围姿势 | 内存生效、保存重载全还原,白改 | 吸收:按层级、相对父骨夹持后姿势算 |
| 只验根骨/近端就宣布导出正确 | PreRotation / 夹持误差在**末端**才显著 | 验最远端骨(指尖 / 脚趾)的位置 |

## 验证

- **Round-trip**:写完导出 → 重导入 → 比**末端骨世界位置**(不是根骨)。契约 1 的坑只在末端显著。
- 独立 oracle:目标姿势的末端骨世界位置(从你的算法侧算)vs 导出后 FBX 里该骨的世界位置,应 ≤ 亚 mm(除被限位夹持的关节,其位置仍应精确、只朝向偏)。

## 相关

- [`guidelines/code/validation.md`](../code/validation.md) —— "看代码 ≠ 验证";这两个契约都是"内存里看着对、导出/重载后才暴露",必须跑 round-trip。
- 任何"往 DCC 既有 rig 写动画 + 保留其 mesh/蒙皮"的场景(retarget 成品导出、动画迁移、mocap cleanup 回写)都会碰。
