# UE 渲染管线知识库

> 生成日期：2026-07-29
> 覆盖版本：UE 5.x（以 5.8 为主）
> 来源：自动化深度调研 + 引擎源码分析 + 项目经验提炼

## 文件列表

| 文件 | 字数 | 内容 |
|------|------|------|
| [`card-11-最终报告.md`](card-11-_UE_渲染技术支持工程师：完整知识库与学习路线图.md) | ~61,000 | **完整知识库首页**：摘要 + 全景图 + 学习路线 + 源码导航 + 自我评估 |
| [`card-10-知识地图.md`](card-10-_UE_渲染知识地图.md) | ~32,000 | 结构化知识树 + 源码索引 + CVar 速查表 |
| [`card-09-场景映射.md`](card-09-_UE_渲染技术顾问_-_需求场景分析.md) | ~18,700 | 客户需求分类 + 技术栈映射 + 优先级排序 |
| [`card-01-管线架构.md`](card-01-_UE_5.8_渲染管线架构_-_知识卡片.md) | ~19,000 | FSceneRenderer 流程、渲染线程架构、核心 Pass 顺序 |
| [`card-05-RHI层.md`](card-05-_UE_RHI（Render_Hardware_Interface）架构知识卡片.md) | ~19,100 | RHI 抽象层、资源管理、GPU 同步、平台差异 |
| [`card-08-RDG.md`](card-08-_UE_5.8_Render_Graph_(RDG)_知识卡片.md) | ~13,400 | RDG 编程模型、资源生命周期、Pass 注入、Barrier 管理 |
| [`card-06-Lumen.md`](card-02-_Lumen_全局光照系统_--_知识卡片.md) | ~9,500 | Lumen 三种模式、反射、性能调优、降级路径 |
| [`card-00-Nanite.md`](card-00-_Nanite_虚拟几何体系统_-_UE_5.8_知识卡片.md) | ~14,800 | Cluster/Page/Group、Visibility Buffer、流式加载、限制 |
| [`card-06-Shader材料.md`](card-06-由于搜索预算已耗尽，以下基于引擎源码架构知识（UE_5.5–5.8_稳定跨版本的核心契约）给出完整调研卡片。.md) | ~15,800 | 材质系统、Shader 编译、Permutation、Substrate |
| [`card-04-性能优化.md`](card-04-_UE_5.8_渲染性能优化方法论_-_知识卡片.md) | ~16,000 | 性能分析工具、瓶颈定位、优化策略、CVar 速查 |
| [`card-07-平台适配.md`](card-07-_UE_5.8_平台适配与渲染管线裁剪_--_知识卡片.md) | ~13,800 | Feature Level、Mobile/Desktop/Console 差异、VR、管线裁剪 |
| [`card-03-调试诊断.md`](card-03-_UE_5.8_渲染调试与诊断工具链_-_知识卡片.md) | ~13,700 | 调试工具、GPU Crash、Validation、Shader 调试 |

## 推荐阅读顺序

```
新手（快速建立认知）
  card-01 管线架构 → card-08 RDG → card-05 RHI → card-04 性能优化

进阶（深入核心子系统）
  card-06 Shader材料 → card-00 Nanite → card-02 Lumen → card-07 平台适配

实战导向（应对客户问题）
  card-09 场景映射 → card-04 性能优化 → card-03 调试诊断 → card-11 最终报告

系统化学习
  card-11 最终报告（完整学习路线）→ 按知识树逐层深入
```

## 使用建议

- 遇到具体客户问题时，先查 `card-09 场景映射` 找到对应场景
- 需要快速定位源码时，查 `card-10 知识地图` 的源码索引
- 需要调优参数时，查 `card-04 性能优化` 的 CVar 速查
- 系统学习时，按 `card-11 最终报告` 的学习路线走