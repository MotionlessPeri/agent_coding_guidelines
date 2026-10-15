# 知识检索案例与维护验证

本案例集用于比较本仓的索引、关键词搜索及未来候选检索方式。它不要求新建检索服务，也不是每次普通开发任务的必跑流程。

## 基线与口径

2026-10-13 的初始盘点以 `270b623` 及当时工作树为准：`guidelines/`、`techniques/`、`skills/`、`references/`、`_radar/` 共 171 份 Markdown、1,791,570 UTF-8 内容字节。包含索引、附件及可发现的未提交文件；排除根入口、`docs/`、脚本、外部安装副本、`tmp.md` 和私人记录。后续新增页面不会回写这个历史基线。

初始 10 题由熟悉仓库的 agent 使用索引和 `rg` 人工走查，能够定位相关资料，但发现旧指针、触发范围冲突和中英文/同义表达差异。它不是盲测、召回率、模型 A/B 或速度基准。

本轮增加 [问题导航](../../references/agent-knowledge/find-relevant-guidance.md)，修订已发现的主来源与摘要冲突，并补了有限的版本/证据说明。下列案例保留为可重复的验收输入；“路径能打开”只覆盖发现能力，不能证明答案正确。

## 固定问题及判据

| ID | 输入问题 | 至少要找到的来源 | 不能遗漏或误判 |
|---|---|---|---|
| Q01 | Python 改文件后 status 脏、diff 却为空，怎么查？ | [Windows Python 行尾](../../guidelines/ci-windows/python-write-text-line-endings.md) | 区分原始行尾与 Git 过滤，能定位 `git ls-files --eol` |
| Q02 | Maya 拖动多个对象后撤销只恢复一部分？ | [选择与撤销](../../guidelines/maya/selection-context-and-undo.md) | context 与 manip 自持交互不能混为一套配方；版本未记录不能补猜 |
| Q03 | UE 设置重启丢失、同事看不到，怎么办？ | [配置入口](../../skills/ue/ue-settings-persistence/SKILL.md)、[具体配方](../../skills/ue/ue-settings-persistence/settings-persistence.md) | 先分清配置写入目标；资产标签不是 ini 持久化的必要条件 |
| Q04 | FBX 帧率正常，采样却少帧或翻转？ | [FBX 读取](../../guidelines/fbx/read-animation-from-fbx.md) | 声明帧率、实际关键帧、Euler 连续性分别检查；保留样本/版本缺口 |
| Q05 | 两个 DLL 为什么看到不同“单例”？ | [跨 DLL 契约](../../guidelines/cpp/multi-dll-plugin.md) | 定位符号与存储归属，不只给进程内单例的一般解释 |
| Q06 | 已批准的方案恢复后是否还需批准？ | [生命周期](../../guidelines/workflow/agent-lifecycle.md)、[自主恢复](../../skills/workflow/autonomous-workflow/prepare-plan.md) | 能由中文问题找到英文 approval/reuse；复用有效授权，不把沉默当批准 |
| Q07 | 每次修改 UE 功能都必须重新查所有 API 吗？ | [查证方法](../../skills/ue/ue-reference-engine-source/reference-engine-source.md) | 查适用触发、目标版本和已有证据；入口、附件、UE 索引一致 |
| Q08 | 优化后读数没变，会不会测试了错误的插件？ | [受测二进制](../../guidelines/cpp/perf-measure-optimized-binary.md) | 保留加载路径与优化级别这两个检查对象 |
| Q09 | UE 黑屏、花屏、驱动恢复，从哪里查？ | [场景映射](../../references/ue-rendering/card-09-scenario-mapping.md)、[资料边界](../../references/ue-rendering/README.md) | 黑屏/发黑的表述都可定位；不能脱离引擎版本及核验说明 |
| Q10 | 网上看到的文章能直接变成规范吗？ | [促升与维护](../../guidelines/workflow/knowledge-promotion.md)、[待审区](../../_radar/README.md) | 待审候选、模型综合和已授权规则不同；旧审计入口能正确解析 |
| Q11 | RDG 卡片检查过 CVar，是不是全部 API 都可以直接使用？ | [RDG 的验证说明](../../references/ue-rendering/card-08-rdg.md)、[核证方法](../../references/ue-rendering/card-13-verify-locally.md) | 否；不能把名称存在扩大成全部签名与行为已核验 |
| Q12 | 只有某版本的资料，可否直接保证另一个版本行为相同？ | 对应主题的证据说明；UE 渲染见[跨版本核证](../../references/ue-rendering/card-13-verify-locally.md) | 缺少目标版本证据时明确未核验，不编造兼容性结论 |

Q11、Q12 是负例：成功意味着保留证据边界，不能用“回答完整且肯定”作为通过标准。新别名来自 Q06、Q09 的实际走查困难；未新增向量索引。

## 怎样比较候选方案

先固定问题、语料版本、可用工具和读取预算，再分别使用当前“索引＋关键词＋按需阅读”和候选方案。记录：

- 找到了哪些正确来源，是否遗漏版本、前提、否定条件或当前有效规范。
- 是否把待审内容、过期结论或某章节的局部核验扩大成确定事实。
- 实际读取文本量、工具调用和耗时；只有取得 tokenizer 或运行遥测时才报告 token。
- 新增来源、修改来源和删除来源后的维护动作及成本。

不要按返回数量评分；返回整库也可能“找全”，却不能证明有效。关键约束漏失或伪造来源在该案例中直接记失败。未经独立运行的静态阅读不能写成检索系统实测。

## 来源改变后的复查

本轮 Q07 可作真实变更示例：原入口与附件要求所有 UE 功能查参考、逐 API 搜索；现按已确认的范围收窄。查证方法是主来源，技能入口与 UE 索引是导航，问题页是解释性指针。

复查时打开这几处，比对触发范围及未找到参考时的处理，不能只确认链接存在。可在仓库根定位相关副本：

```powershell
rg -n 'ue-reference-engine-source|reference-engine-source.md' guidelines skills references
```

仅包含一条指针的页面无需复制全部结论；若综合页确实缓存了结论，来源变化时同步更新或标明待复核。这个练习验证的是维护路径，不代表已经有自动失效传播系统。

## 本轮验收记录

2026-10-13 完成以下检查：

- **12 个案例的定向静态复核**：打开预期来源，核对导航与上表的证据边界。Q07 反查发现三个旧摘要，已连同通用 SDK 样例节修正；Q11/Q12 发现跨版本核证页把名称存在扩大为“可以放心用”，已收窄。修订后按受影响案例复查。复核者知道预期路径，结果不能称为盲测召回率。
- **链接与文档检查**：本轮 20 份改动文件中，175 个本地文件链接均可解析；另核对四处指向维护/证据章节的锚点。`git diff --check` 通过。未对全部旧锚点、网络链接或技术断言作全面核验。
- **既有平台契约检查**：`scripts/tests/test-platform-compatibility.ps1` 的 11 项检查通过，涵盖跨平台入口、技能格式和既有工作流约束。它不验证 UE/Maya/FBX 的运行行为。
- **技能安装核对**：只同步 `ue-reference-engine-source`、`ue-settings-persistence` 两个包到 Codex 与 Claude 安装目录；同步前保留备份，同步后核对完整文件清单及 SHA-256，其他安装包未变。
- **独立规则审查**：修正参考页被误套“两次实践后才准入”的歧义；知识促升门槛仅管新规范与操作默认，保存参考资料不自动授予权限。

本轮没有引入检索服务，没有运行模型 A/B，也没有重跑引擎或原项目样本。当前结果证明这些已选问题的来源与边界可以定向复核，不证明检索准确率、token 或耗时改善。
