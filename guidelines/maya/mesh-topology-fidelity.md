# Maya mesh 拓扑与 triangulation 一致性

复刻 Maya 节点、导出几何 fixture 或在脱 Maya core 重算时，polygon 顶点列表**不足以唯一确定 Maya 实际求值表面**。
非共面 quad/n-gon 的对角线和内部 triangulation 会改变最近点、距离、重心权重、法线和支持集合。

## 核心规则

1. **需要数值对齐 Maya 时，读取 `MFnMesh::getTriangles` 的实际 triangle indices。** 不要在 core 里自行 fan
   triangulation 后假设等价。
2. **同时保存 triangle → polygon 映射。** generalized barycentric、polygon edge 判定和 n-gon 特殊路径仍需要原
   polygon corner 顺序；只有 triangles 或只有 polygons 都不完整。
3. **绑定数据按 Maya 实际 surface 建立。** 最近点、bind distance、triangle barycentric 和边界判定必须消费同一份
   triangulation；不能绑定用 Maya API、脱机复算换成另一种三角化。
4. **顶点/面编号变化视为 binding 失效。** 顶点位置变化可以是动画，顶点数、polygon corner 顺序、triangle 对角线或
   Maya 版本导致的解析变化都需要重新验证或重绑。
5. **把 triangulation 写入 fixture。** fixture 至少包含 positions、polygon corners、triangles 和 triangle polygon ids，
   让 core 测试无需猜 Maya 当时如何拆面。

## 为什么 polygon fan 不够

同一 quad `[v0,v1,v2,v3]` 至少可能拆成：

```text
fan:  [v0,v1,v2], [v0,v2,v3]
Maya: [v0,v1,v3], [v3,v1,v2]
```

平面凸 quad 上两者视觉接近，容易让合成测试假通过；非共面 quad 上，最近表面距离和投影点会不同，falloff 阈值附近会直接
改变某个 target 是否受影响。

## 数据采集契约

```cpp
MIntArray triangleCounts;
MIntArray triangleVertices;
meshFn.getTriangles(triangleCounts, triangleVertices);

unsigned cursor = 0;
for (unsigned polygon = 0; polygon < triangleCounts.length(); ++polygon) {
    for (int i = 0; i < triangleCounts[polygon]; ++i) {
        // triangleVertices[cursor..cursor+2]
        // triangle -> polygon 映射 = polygon
        cursor += 3;
    }
}
```

另外用 `getVertices` 保存原 polygon corner 顺序。导出后断言：triangle 的三个 vertex 都属于其映射 polygon、总 triangle
数量一致、索引在范围内。

## 验证矩阵

- 单 triangle：基础 barycentric；
- 平面 quad：防止只在最简单 case 上出错；
- **非共面 quad**：强制暴露对角线差异；
- 凹 n-gon：generalized coordinates 与边界回退；
- 投影落 polygon edge/triangle internal edge 附近：验证阈值和 edge 分类；
- 实际生产 mesh：比较最近距离、支持集合 FP/FN 和最终输出，而不只比较均值。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 只导 polygon vertices | core 被迫猜 triangulation | 同时导 triangles + polygon ids |
| 固定 fan triangulation | 非共面 quad 最近点不同 | 使用 Maya 实际 triangles |
| 只在平面网格验证 | 两种对角线差异被遮住 | 加非共面 quad/n-gon probe |
| 最终均值接近就通过 | 阈值附近支持集合仍错 | 比较逐点距离和 FP/FN |
| 改拓扑后沿用旧 binding | vertex id/frame 对错对象 | 明确重绑或版本迁移 |
