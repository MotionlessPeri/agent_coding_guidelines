# Windows 上的 POSIX 工具：`sed -i` 不是原地编辑，是重写 + 顶替

Git Bash / MSYS2 里的 GNU 工具在 Windows 上跑，有一类坑来自**工具的实现方式跟它的名字不一致**。
本文件目前只有一条，但它是最常撞、后果最隐蔽的一条。

跟 [`powershell-native-command-pitfalls.md`](powershell-native-command-pitfalls.md) /
[`gitlab-runner-service-and-powershell-pitfalls.md`](gitlab-runner-service-and-powershell-pitfalls.md)
是兄弟篇：那两篇管「PowerShell ↔ native exe」，本篇管「POSIX 工具 ↔ Windows 文件系统语义」。

## 核心事实

> `sed -i` 名字里的 in-place 是假的 —— **它把整个文件重写成一个新文件，再 rename 顶替原文件。**

inode 实证：

```
before inode: 23362423068539825
after  inode: 8444249301746141      ← 变了
```

一条机制，**三个可复现的后果**：

| 后果 | 现象 | 危险程度 |
|---|---|---|
| **全文件行尾被改** | CRLF 源文件被按 LF 重写。只改了 1 行，`diff` 却报全文件不同（`1,345c1,345`）——**症状具有欺骗性**，容易误判成"我改错了 / 备份错了" | 中：留下可见异常 |
| **跨设备 rename 失败** | 临时文件与目标不在同一卷时报 `Invalid cross-device link`，整个操作失败 | 低：操作失败，会喊 |
| **穿透只读保护，且不留痕** | 只读文件（`chmod 444` + `attrib +R`）被静默改写：**exit 0、内容已变、权限位仍是只读** | **高：静默成功** |

第三个最危险，理由有两层：

1. **它静默成功**，而前两个至少留下可见异常或直接失败。
2. **它跟 `cp` 的行为相反** —— 实测 `cp` 覆盖同一类只读文件会老实报 `Permission denied`（所以覆盖只读
   文件必须先 `rm` 再 `cp`）。⇒ **只读属性拦得住 `cp`，拦不住 `sed -i`。**

机制：删除 / 重命名一个文件的权限取决于**父目录**是否可写，跟文件自身的只读位无关；rename 顶替完还把
权限位保持成原样，所以事后没有任何痕迹。

⚠️ **谁把只读属性当"我不会误改引擎 / SDK / 系统目录里的文件"的兜底，就正好在这个工具上漏。**
实测那次改引擎里一个 `.Build.cs` 文件，`sed -i` **一次就成了**，只读属性完全没拦 —— 而
**如果它拦了，作者反而会早一步意识到"我在改一个受保护的文件"**。⇒ 保护机制的价值一半在于
**它失败时会喊一声**。

## 纪律

需要**字节级保真**、或要改**受保护目录**（引擎 / SDK / 系统安装路径）里的文件时：

1. **用编辑工具改，不要用 `sed -i`。**
2. 必须用时：**先整文件备份**（不是备份那一行）。
3. 还原走**整文件覆盖 + 字节比对**（`cp` 覆盖前先 `rm`，然后 `cmp` 验字节一致），
   **不要用"反向 sed 改回去"** —— 那样引擎文件会永久留下行尾变更。

## 诚实边界

- 单机验证（本机 Git Bash 的 GNU sed）。**未测** WSL、MSYS2 其他发行、以及 `sed -b`
  二进制模式能不能规避行尾那一条。
- 三个后果各自实测：行尾（`od` 逐字节）、跨设备（另一条 lane 在另一个盘上撞的
  `Invalid cross-device link`）、只读穿透 + inode（本轮实测）。**机制统一、形态各一** ——
  所以记那句机制，别记三条症状清单。
- 同族但**未验证**的怀疑：其他"原地修改"类工具（`perl -i`、部分格式化器的 `--write`）
  多半是同一实现方式，但没实测过 —— 撞到类似症状时可以先怀疑它，不要当已知事实。

## 相关 Guidelines

- [`powershell-native-command-pitfalls.md`](powershell-native-command-pitfalls.md) —— 兄弟篇：PS ↔ native exe
- [`../ue/installed-engine-build-constraints.md`](../ue/installed-engine-build-constraints.md) ——
  一个必须临时改引擎目录文件的场景，本条直接适用
- [`../code/validation.md`](../code/validation.md) —— "改完要验证"；本条是"改这个动作本身
  可能做了你没要求的事"，所以验证要落到**字节比对**而不是"看那一行对不对"
