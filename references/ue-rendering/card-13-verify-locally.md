# 本机核证方法 — 怎么自己确认一条结论真不真

> **验证状态**：本文档描述的是方法与工具用法，不含引擎符号断言。工具本身在
> `scripts/verify-ue-rendering-refs.py` 与 `scripts/ue-cvar-dump.py`。

做渲染技术支持，最值钱的能力不是背下多少 CVar，是**拿到一个说法能自己在源码里落地确认**。
这份文档就是那套动作。

它同时是这个知识库的免疫系统：库里每条断言都可能是生成阶段的似真内容（实测起点是
431 条 CVar 断言里 163 条不存在、239 条路径断言里 79 条不存在），所以「引用前核一遍」
不是谨慎，是必要步骤。

## 目录

| 节 | 内容 |
|---|---|
| [1. 三类断言，三种核法](#1-三类断言三种核法) | 路径 / CVar / 符号各怎么查 |
| [2. 批量核对：跑校验脚本](#2-批量核对跑校验脚本) | 一条命令过全库 |
| [3. 单条核对：查一个名字](#3-单条核对查一个名字) | 客户报了个 CVar，它存在吗 |
| [4. 从 CVar 反查生效路径](#4-从-cvar-反查生效路径) | 这个开关到底控制了什么 |
| [5. 从 Pass 名反查注册点](#5-从-pass-名反查注册点) | ProfileGPU 里看到的名字在哪个文件 |
| [6. 确认某特性在客户版本存不存在](#6-确认某特性在客户版本存不存在) | 跨版本回答问题 |
| [7. 校验方法自身的盲区](#7-校验方法自身的盲区) | 什么情况下工具会说谎 |

---

## 1. 三类断言，三种核法

知识库（和你自己的结论）里的可疑内容分三类，每类的编造率都不低，且**互相独立**——
文件真、符号假的组合是实测存在的：

| 断言类型 | 例子 | 怎么核 |
|---|---|---|
| **源码路径** | `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteRendering.cpp` | 直接看文件在不在。不在就按 basename 全树搜真实位置 |
<!-- verify:ignore-start -->
| **CVar 名** | `r.Nanite.PagePoolSize` | 在引擎源码里搜这个字面量。搜不到就是不存在 |
<!-- verify:ignore-end -->
<!-- verify:ignore-start -->
| **符号名**（类 / 函数 / 宏） | `FNaniteStreamingManager` | 在引擎源码里搜这个 token |
<!-- verify:ignore-end -->

三类都有同一个失败模式：**编造出来的名字读起来完全合理**。`NaniteRendering.cpp`、
<!-- verify:ignore-start -->
`RHIBuffer.h`、`r.VisualizeBuffer`、`FGPUCrashDebugging` 都是实测的假名字，看着都像真的。
<!-- verify:ignore-end -->
靠读发现不了，跑一遍就现形。

---

## 2. 批量核对：跑校验脚本

```bash
# 全库三轴核对（首次要建索引，几分钟；之后走缓存）
python scripts/verify-ue-rendering-refs.py \
    --cvar-cache <某个缓存路径>/cvar-index.json \
    --symbol-cache <某个缓存路径>/symbol-index.json

# 只看 markdown 结构（秒级，改完文档随手跑）
python scripts/verify-ue-rendering-refs.py --structure-only

# 只核路径，跳过较慢的 CVar / 符号扫描
python scripts/verify-ue-rendering-refs.py --paths-only
```

引擎根用 `--ue` 指定，或设环境变量 `UE_ROOT`。默认按 `H:/Epic Games/UE_5.8` 等候选顺序探测。

输出分三类判定：

| 判定 | 含义 | 该做什么 |
|---|---|---|
| **OK** | 路径规范且存在 | 无 |
| **FIX** | 文件存在但路径写法不规范 | 按建议改成相对引擎根的写法 |
| **MISSING** | 引擎里找不到 | 删掉，或按 basename 找到真实对应物后改 |

退出码 0 = 无 MISSING，非 0 = 有。可以直接当提交前 gate 用。

**两个机制要知道**：

- `<!-- verify:ignore-start -->` … `<!-- verify:ignore-end -->` 之间的内容不参与统计。
  文档里**故意**写出不存在的名字（「这些名字调研稿里有但引擎里没有」的对照表）时用它，
  否则反面教材会被算成缺陷。
- `scripts/verify-ue-rendering-allow.txt` 是允许清单，放「已确认真实但解析器抓不到」的名字，
  每条必须写理由。门槛要守住——加进去就等于把它从 gate 里摘出去了。

---

## 3. 单条核对：查一个名字

客户在邮件里给了个 CVar，先确认它存在：

```bash
<!-- verify:ignore-start -->
python scripts/ue-cvar-dump.py --check r.Nanite.MaxPixelsPerEdge r.Nanite.PagePoolSize
<!-- verify:ignore-end -->
```

存在的会给出声明位置和引擎自己的帮助文本；不存在的会尝试给近亲。

按家族列全部（回答「这个子系统有哪些开关」）：

```bash
python scripts/ue-cvar-dump.py r.Lumen.Reflections --md --with-source
python scripts/ue-cvar-dump.py r.RDG --md
```

`--md` 直接出 markdown 表，可以贴进文档或回给客户。表里的作用说明是引擎源码里的帮助文本，
不是转述，所以不会走样。

**这个工具的一个用法值得单独说**：写文档时不要手打 CVar 名，用它生成。手打就会有错，
生成的不会——而且生成器遇到不存在的名字会直接报错退出。

---

## 4. 从 CVar 反查生效路径

知道名字存在只是第一步。客户问「我把这个调了为什么没效果」，要看它实际怎么被消费：

```bash
# 1. 找声明处（拿到变量名，比如 GNaniteMaxPixelsPerEdge）
python scripts/ue-cvar-dump.py --check r.Nanite.MaxPixelsPerEdge

# 2. 用声明处给的 file:line 打开，看变量名和 ECVF_* 标记
#    ECVF_RenderThreadSafe / ECVF_ReadOnly / ECVF_Scalability 决定它能不能运行时改
```

三个常见的「调了没效果」原因，都能从声明处看出来：

| 现象 | 从声明处能看到的线索 |
|---|---|
| 改了完全没反应 | 标了 `ECVF_ReadOnly`——只能启动前设（ini 或命令行） |
| 改了要等一会才生效 | 值在 render thread 上被读（`GetValueOnRenderThread`），有一帧延迟 |
| 改了又被改回去 | 被 scalability 系统（`Scalability.ini`）或设备profile覆盖 |
| 只在编辑器有效 | 声明被 `#if WITH_EDITOR` 包着 |

再往下一层：拿变量名（`GXxx`）全局搜使用处，看它在哪些 Pass 的条件里出现——这才回答
「它到底控制了什么」。

---

## 5. 从 Pass 名反查注册点

`ProfileGPU` 或 RenderDoc 里看到一个 Pass 名很耗时，要找它的代码：

```bash
# Pass 名来自 RDG_EVENT_NAME("XXX")，直接搜这个字面量
# （用 ripgrep 或编辑器全局搜，注意引擎路径含空格要加引号）
rg 'RDG_EVENT_NAME\("BasePass' "H:/Epic Games/UE_5.8/Engine/Source"
```

搜不到时的三种可能：

1. Pass 名是**拼接出来的**（`RDG_EVENT_NAME("%s", *Name)`）——搜前缀或搜那个变量
2. 名字来自 `SCOPED_DRAW_EVENT` 而不是 RDG——换个宏搜
3. 名字来自材质 / shader 名而不是代码字面量——那是 `r.ShowMaterialDrawEvents 1` 产生的

反过来，想知道某个文件贡献了哪些 Pass，就在那个文件里搜 `RDG_EVENT_NAME`。

---

## 6. 确认某特性在客户版本存不存在

客户在 5.3，你手上是 5.8——这是做支持最常见的错配。**不要凭记忆答**。

如果本机有客户那个版本，直接指过去：

```bash
python scripts/verify-ue-rendering-refs.py --ue "C:/Program Files/Epic Games/UE_5.3" --paths-only
python scripts/ue-cvar-dump.py --ue "C:/Program Files/Epic Games/UE_5.3" --check r.MegaLights.Enable
```

如果本机没有那个版本，只能明确告诉客户「这条我按 5.8 核过，你那个版本我没有本机可核，
需要你在你的引擎里确认一下这个名字」——**这比猜一个答案强得多**。给客户一条不存在的
CVar，代价远大于说一句「需要确认」。

跨版本的经验判据：

| 变化类型 | 跨版本稳定度 |
|---|---|
| 子系统总开关（`r.Nanite`、`r.Lumen.DiffuseIndirect.Allow`） | 较稳，跨几个版本一般在 |
| 子系统内部细调项（`r.Lumen.ScreenProbeGather.*`） | 不稳，改名 / 增删频繁 |
| 源码文件路径 | 中等，模块重组时会挪（实测 `Materials/Material.h` 在 5.7 和 5.8 就不在同一层） |
| 枚举成员名 | 不稳（实测 `EStereoscopicPass` 从 UE4 的 `eSSP_LEFT_EYE` 变成了 `eSSP_PRIMARY`） |

---

## 7. 校验方法自身的盲区

工具会说谎的几种情况，知道它们才能正确解读结果：

| 盲区 | 表现 | 怎么办 |
|---|---|---|
| **引擎分发裁掉了部分目录** | `Engine/Source/Programs/` 下的路径被判成不存在。实测安装版和公司 Perforce 版都只带 14 个子目录，完整源码树有 89 个 | 这类路径要么放进允许清单并写明理由，要么在文档里注明「需完整源码树」 |
| **CVar 注册形式没被解析器覆盖** | 明明存在的名字被判成不存在（比如 `r.DumpGPU` 是控制台命令不是 CVar） | 手工确认后进允许清单，写明理由 |
| **符号是宏生成的** | 类名由 `DECLARE_*` 宏拼出来，源码里搜不到完整字面量 | 搜宏调用而不是搜结果名 |
| **平台特定代码没装** | 主机平台（`Engine/Platforms/`）相关的符号查不到 | 只在装了对应平台支持时才可核 |

**共模失败的识别信号**：如果你的核对方法把**已知真实的东西也判成不存在**，坏的是方法不是被测对象。
所以任何一轮核对都该带一个对照组——挑几个你确定存在的名字一起查，它们必须全部命中。
实测踩过一次：shell 里未加引号的引擎路径被 `Epic Games` 中间的空格拆开，`grep` 静默返回空，
于是所有名字都「不存在」，包括对照组。

---

## 关联

- [`card-10-knowledge-map.md`](card-10-knowledge-map.md) —— 源码索引：知道该去哪个文件找
- [`card-03-debugging.md`](card-03-debugging.md) —— 运行期诊断（本文档是静态核证，那份是动态排查）
- [`README.md`](README.md) —— 本库的引用纪律
