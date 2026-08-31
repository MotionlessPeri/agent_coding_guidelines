# 用 Python 改文件时，行尾会被静默改掉 —— 而两个方向都会

## 核心规则

Windows 上用 Python 脚本改一份既有文件，**默认会把整份文件的行尾换掉**，而且：

- **不报错、不返回异常、退出码 0**
- **内容逐字未变** —— 任何按「内容」做的检查都是绿的
- 而它改的是**内容之外的东西** ⇒ 你的检查照不见它

⇒ 判据一句话：**「内容没变」不等于「文件没被整份重写」。**

跟 [`powershell-native-command-pitfalls.md`](powershell-native-command-pitfalls.md) 的 Pitfall 4/5
是同族**不同轴**：那条是 **PowerShell** 落盘毁在编码 / BOM / 行尾上；本条是 **Python** 轴，
而且它有一个反直觉的地方 —— **看起来像修法的那个写法，方向是反的**。

## 四种写法，只有一种保住原样（实测 Python 3.12.9 / Windows）

初始文件是 CRLF：

| 写法 | 结果 |
|---|---|
| `read_text()` + `write_text()` | CRLF 保住，**但 LF 文件会被转成 CRLF** |
| `read_text()` + `write_text(newline="")` | 🛑 **CRLF 被转成 LF** —— 看似是修法，方向反了 |
| `open(newline="")` 读 + 写 | ✅ **原样保住** |
| 编辑器 / Write / Edit 类工具 | ✅ 不经这条翻译层 |

```python
p.write_text("a\nb\n", encoding="utf-8")               # → b'a\r\nb\r\n'   转了
p.write_text("a\nb\n", encoding="utf-8", newline="")   # → b'a\nb\n'       不转
```

⚠️ 成因是**两步各自都对、合起来出事**：`read_text()` 默认走 universal newlines
（读进来 CRLF 已经变成 `\n`），`write_text(newline="")` 不翻译 ⇒ 原样写出 `\n` ⇒ 落盘成 LF。

### 🛑 而「两侧都 `newline=""`」还不够 —— 少了第二句

`newline=""` 的语义是**「不翻译」，不是「用这个文件的行尾」**。所以你**插入的新文本**
自己带什么行尾，就落盘成什么：

```
文件原有 218 行 CRLF + 我插入的一段带 \n  ⇒ 落盘成**混合行尾**
```

⇒ 完整规则要两句，缺一句就出事：

1. **读写两侧都不翻译**（`open(newline="")`）
2. **新插入的文本也要用文件现有的行尾**（先探出来，再用它拼）

## 为什么值得写下来：常规检查全都照不见它

实测一整天在同一件事上换了**四种错法**，前三种靠机械指纹发现，第四种靠备份挽回：

```
① 默认写法          LF 文件被转成 CRLF
② 只给写侧加 newline=""   CRLF 文件被转成 LF          ← 以为是修法
③ 两侧都 newline=""       新文本带错行尾 ⇒ 混合行尾    ← 配方对了但不完整
④ 收尾做了一次全局换行替换  畸形换行 + 空行全没了       ← markdown 结构毁掉
```

⚠️ 而 ①②③ 的共同点是：**跑完之后文件仍然可读、语法仍然正确、内容检查仍然全绿。**

## 在 git 仓里更隐蔽：`git status` 报脏而 `git diff` 零行

`core.autocrlf=true` 时（Windows 上常见默认）：

```
只把整份 LF 翻成 CRLF、内容一字未改：
  git status --short   ' M f.txt'    ← 报脏
  git diff | wc -l     **0**         ← 零行
  git commit -- f.txt  "nothing to commit, working tree clean"   ← 提交是空操作
```

⇒ 两个信号互相矛盾，而**人会相信后者**（`diff` 说没改动 ⇒ "哦，那没事"）。
成因：`diff` 走**带过滤**的比较，行尾差异被规范化掉；`status` 看到 stat 变化。

⚠️ 由此派生一条：**「提交前读全 diff 逐 hunk 认领」这条纪律按定义只管「会进 commit 的改动」** ——
这类文件**一个 hunk 都不出现**，会被静默跳过。

📌 **好消息**：`autocrlf` 同时是那个**让污染出不去**的东西 —— 暂存时归一回 LF，
所以仓库内容不受影响（实测一个 301 文本 blob 的仓，含 CRLF 的 **0** 个）。
⇒ **一个机制的「它挡住了什么」和「它藏起了什么」往往是同一件事的两面，不能只报一面。**

## 怎么查（git 侧确实有判据，别自己下"没有"的结论）

```bash
git ls-files --eol                       # i/lf  w/crlf  ← 索引 LF / 工作树 CRLF，一眼
git ls-files --eol | awk '{print $2}' | sort | uniq -c   # 全仓分布，~1 秒
```

⚠️ 而 `git status` / `git diff` **两个口径都在 filter 之后**，所以它们照不见行尾 ——
只查了这两个就断言"这一层没有判据"是错的（实测犯过）。

### 口径要跟比较的另一端对齐

| 比什么 | 用什么 |
|---|---|
| 磁盘文件 vs 磁盘文件 | `cmp` / `git hash-object --no-filters` —— 两端都是原始字节，**不能**规范化 |
| **提交里的 blob** vs 磁盘文件 | `git rev-parse <sha>:<path>` vs `git hash-object <path>`（**带 filter**）—— blob 本就是入库形态 |

🛑 **「总加 `--no-filters`」是错的**：拿它跟 blob 比会报**假不符**（一个会阻止你落刀的假红）。

## Anti-Patterns

| 反 pattern | 为什么错 | 修法 |
|---|---|---|
| 用 `write_text()` 改既有文件 | 默认转行尾，静默、无报错 | 两侧 `open(newline="")`，或用编辑器类工具 |
| 只给写侧加 `newline=""` | 方向反了：CRLF 会被转成 LF | 读侧也要 |
| 两侧都加了就以为完事 | 新插入的文本自带的行尾会混进去 | 先探出文件现有行尾，用它拼新文本 |
| 收尾做一次全局换行替换 | 会造出畸形换行、吞掉空行 | 别做全局转换；只拼新文本 |
| 拿 `git diff` 判「文件动没动」 | 行尾变化在它眼里不存在 | `git ls-files --eol` |
| 只查 `status`/`diff` 就说"git 看不见这个" | 那两个口径都在 filter 之后 | `--eol` 就是为这件事做的 |
| 改完不量落盘字节 | 前三种错法全部静默 | 改完立刻 `read_bytes().count(b"\r\n")` 对一眼 |

## 诚实边界

- **单项目、一天内四次独立命中**（四种错法各一次），机制在 Python 3.12.9 / Windows 上逐条实测。
- 属于「工具 gotcha」这一档，不走两击规则 —— 它是**标准库在某平台上的行为**，不是项目经验。
- 未在 macOS / Linux 上验（那边 `write_text` 不做翻译，本条多半不激发，但**未实测**）。

## 相关 Guidelines

- [`powershell-native-command-pitfalls.md`](powershell-native-command-pitfalls.md) Pitfall 4/5
  —— 同族的 PowerShell 轴（编码 / BOM / 行尾）
- [`posix-tools-on-windows.md`](posix-tools-on-windows.md) —— `sed -i` 是重写 + 顶替，同族
- [`../code/generating-code-through-shell.md`](../code/generating-code-through-shell.md)
  —— 转义层数那一轴；本条是**同一动作的另一种毁法**
- [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)
  —— 「改完立刻量落盘字节」是那条「量具先自证」的一个具体落点
