# UE 渲染知识 Wiki 试点

这里由 LLM 将几份既有渲染资料综合成可复用的问答页。主题限定为“自定义渲染效果怎样选扩展路径，以及证据不足时怎样回答”；不是完整 UE Wiki，也不增加开发或审批流程。

| 当前问题 | 综合页 |
|---|---|
| 一个自定义效果该用材质、扩展点还是改引擎？ | [选择渲染扩展路径](choosing-custom-rendering-route.md) |
| 资料只核过部分内容，或目标引擎版本不同，能回答到什么程度？ | [按版本与证据回答](answering-with-version-and-evidence.md) |

综合页提供跨文档结论、判断条件和具体答复示例；必要时继续打开原资料。LLM 综合不提高证据等级：原资料中的历史核对、未核签名及版本缺口均保留，本试点未运行 UE、重验源码或测试渲染效果。

## 使用的来源

来源全部位于上一层目录，没有导入网络资料或其他渲染卡片。读取快照见 [sources.json](sources.json)：记录仓库版本、原文件路径、章节定位、依赖页及 SHA-256。行号只作阅读提示，以章节名和内容为准。

| 来源 | 本试点读取范围 | 在综合中的作用 |
|---|---|---|
| [资料 README](../README.md) | 开头覆盖版本、引用纪律 | 整体适用范围与来源地位 |
| [问题路由](../card-09-scenario-mapping.md) | §1、§3.3、§4 | 把用户问题转为路径选择，补齐影响结论的项目信息 |
| [管线扩展点](../card-12-pipeline-extension.md) | 验证声明；§1–7 | 三条候选路径、数据与阶段、平台差异、改引擎的代价 |
| [本机核证](../card-13-verify-locally.md) | 验证声明；§1、§4、§6、§7 | 区分名称存在与行为证据，处理跨版本和搜索盲区 |
| [RDG 卡片](../card-08-rdg.md) | 开头验证声明、概述 | 区分 Pass/资源依赖组织与接入路线；不把 CVar 核对外推为全部 API 签名已核验 |

## 来源变化后的人工更新

收到相关问题或准备维护本主题时，检查引用来源是否改变；没有后台轮询。`sources.json` 中哈希按 **UTF-8 内容去 BOM、CRLF 转 LF** 后计算，避免不同 checkout 行尾造成误报。哈希相同只说明内容相同，不证明技术内容正确；整份文件改变也不必然影响本页，需要读差异。

在仓库根可运行下面的只读检查：

```powershell
$pilotManifest = Get-Content references/ue-rendering/wiki-pilot/sources.json -Raw | ConvertFrom-Json
$pilotHasher = [Security.Cryptography.SHA256]::Create()
try {
    foreach ($pilotSource in $pilotManifest.sources) {
        if (!(Test-Path -LiteralPath $pilotSource.path -PathType Leaf)) {
            [pscustomobject]@{ source=$pilotSource.id; state='missing'; review=($pilotSource.used_by -join ', ') }
            continue
        }
        $pilotText = [IO.File]::ReadAllText((Join-Path (Get-Location) $pilotSource.path)).Replace("`r`n", "`n")
        $pilotHash = [BitConverter]::ToString($pilotHasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($pilotText))).Replace('-', '').ToLowerInvariant()
        [pscustomobject]@{ source=$pilotSource.id; state=$(if ($pilotHash -eq $pilotSource.sha256) {'unchanged'} else {'changed'}); review=($pilotSource.used_by -join ', ') }
    }
} finally { $pilotHasher.Dispose() }
```

出现变化后，LLM 或维护者实际重读差异与相关原章节，沿 `used_by` 检查结论、答复示例和互链页。依赖表帮助定位，不能代替判断影响范围。确认无影响就记录理由；有影响则改写或撤回对应结论，同时保留新的限制。最后检查引用与示例，再更新已复核来源的哈希。仅刷新哈希会掩盖未处理的过期内容。

来源之间冲突时，将差异和待核部分写在相关结论旁；证据不足就给出条件性答复，不由综合页自行裁定引擎事实。更新与核验规则仍以 [知识维护](../../../guidelines/workflow/knowledge-promotion.md#maintenance-and-evidence)为准。

## 试点怎样检验

可分别用两页的具体问题检查：回答是否直接给出候选路径或证据边界，是否能回到原章节，是否无须阅读整套渲染库。再用明确标记的私有合成来源变更检查：能否发现变化、由另一位 agent 重读来源并改写受影响的私有 Wiki 副本。

合成演练只能证明这一轮人工辅助维护过程，不是实际 UE 变化、自动知识更新能力或模型效果评测。演练材料和日志保存在仓库外，不写回这些正式知识页。

本轮的问答对照、审查修正、维护演练与计量限制见[试点评估](../../../docs/evaluations/llm-wiki-ue-rendering.md)。
