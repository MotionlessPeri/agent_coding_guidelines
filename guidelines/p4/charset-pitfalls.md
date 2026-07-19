# Perforce charset 自动 transcode 文本文件的坑

P4 server unicode-enabled 模式下，**`text` 和 `unicode` 类型的文件 sync 时会按
client `P4CHARSET` 自动 transcode**——同一个 file revision，不同 client 看到的
字节内容不一样。

对代码 / 数据库 / 二进制文件这种"字节必须保留"的场景**直接造成数据损坏**：
Python 源码 SyntaxError、SQLite 数据库读不开、xlsx 解析崩。

跟 git 默认行为完全不同（git 默认不动字节，只可能做 `core.autocrlf` 行尾转换）。
**P4 这个坑用 git 习惯做事的开发者最容易踩**。

---

## 现象（实际故障）

提交方机器（charset utf8）submit 一个 `.py` 文件（含中文注释，UTF-8 编码）到
unicode-enabled P4 server：

```python
# import_xlsx_to_json.py
"""xlsx 解析入口 dispatcher——"""
import openpyxl
```

接收方机器（charset cp936，中文 Windows 默认）`p4 sync` 下来这个文件，Python 3
执行：

```
SyntaxError: (unicode error) 'utf-8' codec can't decode byte 0xa1
in position 31: invalid start byte
```

`0xa1` 是 GBK 编码下 em-dash `—` 的首字节。源 UTF-8 文件里的 `——` (`E2 80 94 E2 80 94`)
在接收方机器变成了 `A1 AA A1 AA`（GBK）。

文件**在 P4 传输链路上被 transcode 了**。同一个 revision，提交方 sync 出 UTF-8 字节，接收方 sync 出 GBK 字节。

---

## Root cause

P4 server unicode-enabled 模式下，`text` / `unicode` 类型的文件：

1. submit 时：按提交方 client 的 `P4CHARSET` 把本地字节**解码**为 UTF-8 存到 server
2. sync 时：按接收方 client 的 `P4CHARSET` 把 server 存的 UTF-8 **编码**成接收方 charset 发到本地

这是 P4 的**设计 feature**——目的是让不同 locale 的 client 都能读到"本地编码的文本"。

但对**代码 / 数据**这种**字节必须保留**的场景，transcode 就是数据损坏：

| File type | server 存 | utf8 client sync | cp936 client sync | 结果 |
|---|---|---|---|---|
| `text` | 原字节（不解码）| 原字节 | 原字节 | OK（server 不做 transcode） |
| `unicode` | UTF-8 内部存储 | UTF-8 | GBK | **❌ transcode 损坏** |
| `binary` | 原字节（不动） | 原字节 | 原字节 | OK |

注意：

- `unicode` 类型**强制**按 utf8 内部存 + 按 client charset transcode
- `text` 类型在 server **non-unicode** 模式下不 transcode；但 server **unicode-enabled** 模式下 `text` 也会按 client charset 处理（看 P4 server 配置）
- **只有 `binary` 类型 100% 保证字节不变**

---

## 文件 type 怎么决定的

P4 client `p4 add file.py` 时由几个因素决定 type：

1. **P4 server 的 typemap**（admin 配的全局规则，如 `binary //....py`）
2. **client 端 `-t` 显式指定**（`p4 add -t binary file.py`）
3. **P4 自动检测**（基于文件内容前几 KB 扫描，多数情况猜对但 `.py` 容易猜成 `unicode` / `text`）

接收方踩坑的常见来源：

- 提交方用 IDE 直接 `p4 add` 没指定 type，P4 自动检测 `.py` → `unicode`
- 提交方 commit 时 charset utf8 → submit UTF-8 字节到 server 标为 unicode
- 接收方 client charset cp936 → sync 时被 transcode 成 GBK
- Python 3 默认按 UTF-8 解析源码 → 撞 GBK 字节 → SyntaxError

整条链上**每一步都"按设计工作"**，但组合起来就是坑。

---

## 修法：典型 file type 一律 binary

**唯一可靠的方法**：所有"字节必须保留"的文件类型强制 `binary`。

### 哪些必须 binary

| 类型 | 理由 |
|---|---|
| `.py` / `.pyd` | Python 源码 + C 扩展，UTF-8 编码 |
| `.db` / `.sqlite` | 二进制数据库文件，transcode 直接损坏 |
| `.xlsx` / `.xls` | Excel zip 容器，transcode 损坏 |
| `.uasset` / `.umap` | UE 资产二进制 |
| `.png` / `.tga` / `.jpg` / 任何图片 | 图片二进制 |
| `.fbx` / `.obj` | 3D 模型 |
| `.wav` / `.mp3` / `.ogg` | 音频 |
| `.exe` / `.dll` / `.pdb` | 可执行 / 库 / 调试符号 |

### 边界 case（可以 binary 也可以 text）

| 类型 | 取舍 |
|---|---|
| `.ini` / `.cfg` | 含中文注释或 key 时建议 binary；纯 ASCII 用 text 没事 |
| `.json` | 含中文 string 时建议 binary |
| `.md` | 含中文 + 多人 sync 时建议 binary |
| `.txt` | 同 .md |
| `.csv` | 含中文列 / 值时建议 binary |

**保守策略**：跨多 charset client 的项目里，**所有文本文件都 binary**，让 P4 完全不碰字节。代价是 P4 server 上不能 diff 这些文件（diff 工具不识别 binary）—— 但这些文件通常用 git 之类 VCS 做 review，不依赖 P4 diff。

---

## 实施方法（按权限层级排序）

### 最一劳永逸（需要 P4 admin）：server 端 typemap

`p4 typemap` 全局配置规则，所有 `p4 add` 自动应用：

```
binary //....py
binary //....pyd
binary //....db
binary //....sqlite
binary //....xlsx
binary //....xls
binary //....uasset
binary //....umap
binary //....png
binary //....tga
binary //....fbx
```

加完之后：

- **未来**所有 `p4 add` 这些扩展名的文件自动 binary
- **已经在 depot 里的**这些扩展名文件**不会自动改 type**——需要逐个 `p4 edit -t binary` + submit 一次

历史文件批量改 type：

```cmd
:: 列所有 type 不是 binary 的 .py 文件
p4 files "//depot/...py" | findstr /v "binary"

:: 改 type（不改内容）
p4 edit -t binary "//depot/...py"
p4 submit -d "Migrate .py to binary type"
```

### 客户端（不需要 admin）：add / reopen 时显式 `-t binary`

每次 `p4 add` 加 `-t binary`：

```cmd
p4 add -t binary file.py
```

或者**对已存在的**文件改 type（不改内容）：

```cmd
p4 edit -t binary "//depot/path/file.py"
p4 submit -d "Convert .py to binary"
```

P4V GUI 步骤：

1. Workspace tab 选文件 → 右键 `Check Out`（mark for edit）
2. 选中保持不变 → 右键 **`Change Filetype...`**
3. `Base Filetype` 下拉选 `binary` → OK（其他选项保持默认）
4. Pending tab 找 default changelist → 右键 → Submit

或者用 P4V 一次性批量：选多个文件 → 右键 → Change Filetype → 选 binary。

⚠️ 改 type 之前**确认本地字节是你想要的**：如果 client 之前是 cp936，本地 sync 出来已经是 GBK 编码；改 binary 后 submit 上去的就是 GBK 字节，**所有人**都拿到 GBK。要先在 utf8 charset 下 force re-sync 拿到原 UTF-8 字节，再改 type。

### 临时 workaround（不解决根因）：接收方设 `P4CHARSET=utf8`

```cmd
p4 set P4CHARSET=utf8
p4 sync -f //...                  :: force re-sync 拿原 UTF-8 字节
```

或 P4V Connection → 改 Character Set 为 `Unicode (UTF-8)` + 右键 workspace → `Get Revision` → 勾 `Force Operation`。

这只是**临时**——对当前 client 当前机器有效。新 client / 新机器 / 新策划接入又会踩。**最终一定要走 typemap binary**。

---

## 怎么诊断这个坑

接收方报"Python SyntaxError 0xa1" / "SQLite database is locked" / "xlsx file is not a zip"，**先怀疑 P4 transcode**：

```cmd
:: 1. 看文件实际 type
p4 fstat //depot/path/file.py
:: 看 ... headType: 字段，是 binary 还是 unicode/text

:: 2. dump 文件前 50 字节
:: PowerShell
$bytes = [System.IO.File]::ReadAllBytes("D:\workspace\path\file.py")
$bytes[0..49] | ForEach-Object { '{0:X2}' -f $_ }

:: 3. 跟提交方机器的同一文件对比字节
:: 如果接收方 0xa1 而提交方 0xe2 0x80 0x94 → transcode 损坏
```

也看 `p4 info` 输出：

```
Server services: commit-server          ← unicode-enabled server 通常有这个
Unicode-enabled: enabled                ← 直接标记（某些 P4 版本不显示这行）
Case Handling: sensitive
```

如果 server unicode-enabled + 接收方 `p4 set P4CHARSET` 不是 utf8，就是这个坑。

---

## 防御性约定（适合写进新项目 AGENTS.md）

P4 项目跨多 charset client 时遵守：

1. **接入 P4 server 第一步：跟 admin 确认 typemap 规则**——常用扩展名是否都标 binary
2. **加新 file type 提交之前：明确决定 type**（admin 配 typemap 或 client `-t binary` 都行，但不能依赖 P4 auto-detect）
3. **新 client / 新策划接入时：第一件事是 `p4 set P4CHARSET=utf8`** + force resync——做防御性配置，不依赖 admin
4. **CI 自动 submit 流程：每次 submit 前对关键扩展名 `p4 reopen -t binary`**，不依赖 server typemap 已配（部分项目 admin 不一定配过来）

第 4 条的实施详 `techniques/ci-deploy-to-p4.md`。

---

## 跟 `unicode` 类型对照

P4 client spec / changelist spec 这种 P4 server 内部 metadata 默认是 `unicode` 类型——这是**预期**的，因为 P4 工具自己用 client charset 跟你交互。

**用户文件不要用 `unicode` 类型**。即使是中文文档 / 配置，也走 `binary`（多 charset 安全）或 `text`（单 charset 团队足够）。

`unicode` 仅在所有 client charset 一致 + 真的需要 P4 帮你跨编码翻译时才有意义——
实际项目几乎不需要。

---

## 项目实例参考

UE 5.5 dialogue plugin 部署到策划方 P4 server (commit-server, unicode-enabled)
踩穿过：

- 内部 dev 用 utf8 charset submit `.py` 到 P4 server（type 被 auto detect 成 `unicode`）
- 策划 client 默认 cp936 charset，sync 下来 .py 是 GBK
- Python 3 报 `SyntaxError: (unicode error) 'utf-8' codec can't decode byte 0xa1 in position 31`

修法走客户端批量 reopen：

```cmd
p4 edit -t binary "//depot/path/DialogueSystem_*/Plugins/.../*.py"
p4 submit -d "Convert .py unicode → binary (fix charset transcoding)"
```

之后 CI 也加了 `p4 reopen -t binary //...EXT` 兜底，每次 submit 强制 binary
type（即使 admin 没配 typemap）。

## 相关 Guidelines / Techniques

- `techniques/ci-deploy-to-p4.md` —— CI 自动 submit 时的完整 reopen -t binary 流程
- `guidelines/code/validation.md` —— "接收方视角验证"原则（多 charset client 是典型接收方场景）
