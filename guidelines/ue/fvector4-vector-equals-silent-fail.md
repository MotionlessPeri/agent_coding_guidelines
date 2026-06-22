# `FMatrix::TransformVector` 返 `FVector4`(W=0)——跟 `FVector` 比 `.Equals` 静默失败

## 核心规则

UE `FMatrix::TransformVector(V)` / `TransformPosition(V)` 返回的是 **`FVector4`**,不是 `FVector`。把这个
`FVector4` 直接拿去跟一个 `FVector` 比 `.Equals(...)`,会因为 **W 分量(`TransformVector` 给 W=0,
`FVector` 隐式当 1)** 不相等而**静默失败**——值其实对,断言/分支却走错。

**修法**:用 `FVector(...)` 把 `FVector4` 包一层(丢 W)再比 / 再运算:

```cpp
// ❌ 静默失败:FVector4(x,y,z,0).Equals(FVector(x,y,z)) → 比到 W(0 vs 隐式 1)→ false
TestTrue(TEXT("..."), M.TransformVector(V).Equals(Expected, 1e-3));   // Expected 是 FVector

// ✅ 包成 FVector 丢 W 再比
TestTrue(TEXT("..."), FVector(M.TransformVector(V)).Equals(Expected, 1e-3));
```

## 机制

| 调用 | 返回类型 | W 分量 |
|---|---|---|
| `FMatrix::TransformVector(FVector)` | **`FVector4`** | 0(方向向量,不受平移影响) |
| `FMatrix::TransformPosition(FVector)` | **`FVector4`** | 通常 1(点,但视矩阵末列而定) |
| `FVector4::Equals(FVector4, tol)` | bool | **逐 4 分量比**,含 W |

`FVector` → `FVector4` 有隐式构造(W 默认 1)。所以 `someFVector4.Equals(someFVector)` 实际是
`FVector4{x,y,z,0}.Equals(FVector4{x,y,z,1})` → W 差 1 → false,即使 XYZ 完全一致。

**生产代码通常自动安全**:把结果**赋给 `FVector` 变量**(`const FVector R = M.TransformVector(V);`)就在赋值时
丢了 W,后续 `FVector` 运算正常。坑主要咬在**直接对 `TransformVector` 结果链式 `.Equals`** 的地方——
最典型是**单元测试断言**(`TestTrue(..., M.TransformVector(V).Equals(ExpectedFVector))`)。

## 症状(怎么发现)

- 单测断言**恒为 false**,但你手算 / 打印 XYZ **完全对**。
- 加 log 打 `M.TransformVector(V)` 看到 XYZ 没错,断言却 fail —— 第一反应别怀疑矩阵数学,先看是不是
  拿 `FVector4` 跟 `FVector` 比了 W。
- 分支(`if (a.Equals(b))`)永不进 / 永远进,a 是 `TransformVector` 结果、b 是 `FVector`。

## 同类高发面

不止 `FMatrix::TransformVector`。任何"返回 `FVector4` 却跟 `FVector` 比/混算"都同形态:

| 来源 | 返回 |
|---|---|
| `FMatrix::TransformVector` / `TransformPosition` / `TransformFVector4` | `FVector4` |
| `FVector4` 运算结果直接 `.Equals(FVector)` | W 参与比较 |
| `FQuat::operator*(FVector4)` 等接受/返回 4 维的重载 | `FVector4` |

判据:**只要一边是 `FVector4`、另一边是 `FVector`,且你只关心 XYZ → 显式 `FVector(...)` 收口,别靠隐式提升**。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| `M.TransformVector(V).Equals(ExpectedFVector)` | W(0 vs 1)→ 恒 false,静默 | `FVector(M.TransformVector(V)).Equals(...)` |
| 断言 fail 先怀疑矩阵/数学逻辑 | 查错方向,浪费时间 | 先确认不是 FVector4↔FVector 比 W |
| 多处 `TransformVector` 结果链式比较,只修一处 | 漏网的同类比较继续静默失败 | grep `TransformVector(` + `TransformPosition(` 全查一遍是否都收口成 FVector |

## 项目实例参考

UE 5.7 curvenet 形变插件(CurveArticulationUE)F6(端点缩放)把端点 edit 旋转路径从 `FQuat` 升级为
`FMatrix` 线性映射,新增 `BuildWorldEditLinearMap` + 一批用 `M.TransformVector(probe)` 验证映射的单测。
测试断言 `M.TransformVector(V).Equals(ExpectedFVector)` 因 `TransformVector` 返 `FVector4`(W=0)而恒 false——
XYZ 明明对。修法:测试里所有 `TransformVector` 结果统一 `FVector(...)` 包裹再 `.Equals`(FollowTest 2 处、
SurfaceFrameTest section 8 三处)。生产侧 `ComputeHandleEndpointContribution` 因把结果赋给 `const FVector`
自动丢 W,不受影响。

## 相关 Guidelines

- [`../code/validation.md`](../code/validation.md) "Adversarial Mindset" —— 断言 fail 不等于逻辑错;
  本坑是"测试自己写错比较"的典型,必须实测 + 看清类型而非只读数学。
- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) —— 先取证(打印 XYZ vs 看断言)
  区分"矩阵数学错"还是"比较带 W"两个竞争假设,别直接改矩阵构造。
- skill `ue-reference-engine-source` —— `FMatrix` / `FVector4` 的返回类型契约在 engine source
  `Math/Matrix.h` / `Math/Vector4.h`,UE doc 没强调,读源码确认返回类型。
