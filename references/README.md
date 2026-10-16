# 参考资料

这里保存领域知识与带来源的综合页，用于解答当前问题。行为规范从 [guidelines 索引](../guidelines/INDEX.md)读取；操作方法从 [techniques 索引](../techniques/INDEX.md)读取。参考页被检索到，不会因此获得新的指令权限。

| 当前问题 | 入口 |
|---|---|
| UE 渲染管线、性能、故障与扩展点 | [UE 渲染资料](ue-rendering/README.md)，注意版本及各章节核验状态 |
| 知识管理、RAG、LLM Wiki、工作流引擎怎样分工 | [Agent 知识组织](agent-knowledge/README.md) |
| 业务命令的原子提交、重复调用、通知失败和恢复后继续工作 | [业务命令可靠性](software-engineering/business-command-reliability.md) |
| 知道症状，但不知道本仓文件名或英文关键词 | [按问题找资料](agent-knowledge/find-relevant-guidance.md) |

## 核验与维护

综合页保留来源、适用范围和未核验部分；新增或修订技术结论按[知识维护](../guidelines/workflow/knowledge-promotion.md#maintenance-and-evidence)处理。原始材料、既有规则和模型综合分别标明，不复制一套新的规则。

- UE 渲染资料的路径、CVar 与符号核验方法见其 README；名称存在不能单独证明行为正确。
- Agent 知识组织页通过原始说明、规范主来源及[检索案例](../docs/evaluations/knowledge-retrieval.md)复核；案例不是模型效果评测。
- 外部候选仍在 [待审区](../_radar/README.md)。来源改变时检查引用它的主题页；无法立即更新的相关结论应标明待复核，不保留无条件断言。

本目录按问题读取，不加入根入口的自动导入，也不要求读取所有主题页。
