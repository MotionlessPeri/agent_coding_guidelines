# 按问题找资料

本页把自然语言问题映射到现有主来源，帮助跨语言和同义表达检索。表中关键词用于定位，不是必须执行的步骤，也不代表资料已经覆盖所有版本。

先读命中的来源及其适用范围。知识查询不会自动启动技能的完整流程；行为约束以当前宿主、用户和项目要求为准。

| 问题或症状 | 可搜索的词 | 主来源 | 阅读时保留的边界 |
|---|---|---|---|
| Python 改文件后 git 显示脏，但 diff 为空 | 换行、行尾、CRLF、newline、write_text | [Windows Python 行尾](../../guidelines/ci-windows/python-write-text-line-endings.md) | 区分磁盘字节与 Git 过滤后的内容 |
| Maya 拖动后撤销只恢复部分结果 | 撤销、undo、drag、MPxToolCommand、snapshot | [选择与撤销](../../guidelines/maya/selection-context-and-undo.md) | 区分 context 与 manip 的结果归属，查看版本和案例边界 |
| UE 设置重启丢失，另一台机器看不到 | 配置、持久化、SaveConfig、DefaultConfig | [UE 配置持久化入口](../../skills/ue/ue-settings-persistence/SKILL.md) | 先确定用户配置、项目共享配置还是资产数据 |
| FBX 采样丢帧或旋转突然翻转 | 帧率、time mode、关键帧密度、Euler、unroll | [FBX 读取](../../guidelines/fbx/read-animation-from-fbx.md) | 声明帧率和真实关键帧不是同一事实；原案例版本未记录时不推定 |
| 两个 DLL 看到不同的“单例” | 单例、singleton、inline static、DLL | [跨 DLL 契约](../../guidelines/cpp/multi-dll-plugin.md) | 核对符号、模块与存储归属 |
| 已批准的方案恢复后是否还要再问 | 批准、授权、复用、approval、authorization、reuse、resume | [授权与生命周期](../../guidelines/workflow/agent-lifecycle.md)；自主任务再看[恢复阶段](../../skills/workflow/autonomous-workflow/prepare-plan.md) | 有效批准只覆盖原对象与范围；待回复不等于批准 |
| 修改 UE 功能时，什么时候需要查引擎源码 | 查源码、reference implementation、unfamiliar、版本变化 | [查证方法主来源](../../skills/ue/ue-reference-engine-source/reference-engine-source.md) | 查看适用触发及既有证据是否仍有效 |
| 性能优化后读数没变，是否加载了旧插件 | 性能、optimized、Debug、Development、加载路径 | [测量实际二进制](../../guidelines/cpp/perf-measure-optimized-binary.md) | 源码修改不等于受测产物更新 |
| UE 黑屏、发黑、花屏或驱动恢复 | 黑屏、发黑、花屏、GPU crash、设备丢失 | [渲染问题路由](../ue-rendering/card-09-scenario-mapping.md) | 同时阅读[资料版本与引用限制](../ue-rendering/README.md) |
| 网上看到的新建议能直接变成规范吗 | 促升、提升、promotion、待审、radar | [知识促升](../../guidelines/workflow/knowledge-promotion.md)；[外部候选](../../_radar/README.md) | 被多次转述不等于独立验证，综合页也不自动授权 |
| 一份 RDG 文档部分核验，能否信任全部 API | RDG、CVar、API、验证状态 | [RDG 卡片开头的验证范围](../ue-rendering/card-08-rdg.md)；[本机核证](../ue-rendering/card-13-verify-locally.md) | CVar 核对不能扩展成所有签名和行为均已核验 |
| 只有某版本的说明，能否直接用于新版 | 版本、升级、cross-version、适用范围 | 对应主题的版本说明；UE 渲染见[跨版本核证方法](../ue-rendering/card-13-verify-locally.md) | 缺目标版本证据时报告未核验，不生成确定的兼容承诺 |

## 找不到时怎样继续

先确认问题属于哪个主题，再用表中的英文标识符或症状同义词查找相关目录。例如在仓库根执行：

```powershell
rg -n -i 'approval|authorization|reuse|resume' guidelines/workflow skills/workflow/autonomous-workflow
rg -n '黑屏|发黑|花屏|GPU|驱动' references/ue-rendering/card-09-scenario-mapping.md
```

搜索结果只是定位线索。打开对应章节并带上文件开头的版本、核验状态和相邻例外；不能把零命中直接解释为“库里没有”，也不能把返回条目数量当作答案质量。

新增别名应来自实际漏找的问题，不穷举全部同义词。来源移动或触发范围改变时，更新本页对应行，并复查[检索案例](../../docs/evaluations/knowledge-retrieval.md)。本页不作为规范的第二份主来源。
