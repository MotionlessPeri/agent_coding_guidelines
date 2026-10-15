---
class: experience
scope: universal
triggers: [heredoc, 反斜杠, 转义, sed, 生成代码, 生成文件, 落盘, py_compile, 代码块, 静默失败, 卡死]
born: "2026-08，写下时的模型未记录"
retested: []
incidents:
  - 2026-08-heredoc-ate-a-backslash
  - 2026-08-sed-choked-on-windows-path
  - 2026-08-two-people-each-did-half-the-compile-gate
  - 2026-08-prose-four-tiers-script-two
---

# 别用嵌套 shell 生成代码

**要落盘会被解释器读的东西（`.py`、patch、`.mel`、JSON、正则），用写文件工具，不要走「shell heredoc 到解释器再生成文件」这条链。** 理由不是不优雅，是转义要穿过比你以为更多的层，而少一层的表现可能是静默失败。

跟 [`../ci-windows/powershell-native-command-pitfalls.md`](../ci-windows/powershell-native-command-pitfalls.md) 的 Pitfall 4 是同族不同轴：那条讲 PowerShell 落盘毁在编码、BOM、行尾三轴上，本条讲转义层数，且跟平台无关。

## 实测：heredoc 吃掉一层反斜杠，`<<'EOF'` 挡不住

判定用字节和长度，不要用 `repr()`，它把真换行也印成 `\n`，两种情况长得一样。

| 通道 | 写的 | 解释器收到 |
|---|---|---|
| heredoc，含 `<<'EOF'` | `"A\\nB"` | `A` 加真换行加 `B`，被吃掉一层 |
| heredoc | `"A\\\\nB"` | 字面 `\n`，四个反斜杠才得到两个 |
| argv，单引号传参 | `'A\nB'` | 完整，不吃 |

引号 heredoc 本该完全字面，它挡不住，说明吃转义的那层在 shell 之上，是工具把命令交给 shell 之前。「我用了引号 heredoc 所以安全」是错的心智模型。

## 为什么它比编码那类更贵

生成的文件里出现真换行，字符串字面量未闭合，SyntaxError，整份文件编译失败。文件若被 `exec`、`import`、`-script` 加载，就什么都不跑、什么都不报，表现跟卡死一模一样。「没有输出」有两种成因（还没跑完 / 压根没开始），而它们产生同一个观测。

## 三条修法，按优先级

1. 用写文件工具（编辑器、Write、Edit），零转义层，也不吃行尾。
2. 非要走 shell，用 argv，别用 heredoc。
3. 干脆不产生反斜杠：`chr(10)`、`splitlines()`、`" | ".join(...)`、`os.linesep`。这条最稳，它让「有几层在吃」失去意义。

`sed` 同理：带 Windows 路径的内容会毁掉表达式，用写文件工具或 Python 做替换。

## 一道便宜的门：生成完先编译，再交给下游

```bash
python -m py_compile gen.py   || exit 2
python -c "import json,sys;json.load(open('a.json'))" || exit 2
git apply --check a.patch     || exit 2
```

它把「7 分钟静默卡死」换成「1 秒报错」，且报错指向生成的文件而不是宿主。**这道门自己要先验能红**：注入一个语法错，看它拦不拦；一道只会绿的门比没有门更坏。

同样适用于交付文档里的代码块：没有任何机制检查它能不能跑，而读者第一件事就是复制粘贴运行。逐块抽出 ```python 块 `compile()` 一遍，并先造红。两条陪跑的教训：补做别人提的纪律时，人补的是自己没做的那半，不是那条纪律的全部；正文与文中工具会漂移，改正文时问一句「下面那个脚本实现了吗」。

## 反模式

| 反模式 | 修法 |
|---|---|
| heredoc 里写 `\\n` 期望得到字面 `\n` | 写四个，或改用 `chr(10)` |
| 「我用了 `<<'EOF'` 所以是字面的」 | 别把生成代码交给这条链 |
| 拿 `repr()` 判断转义对不对 | 看 `len()`、`list(s.encode())` |
| 生成完直接交给宿主跑 | 先 `py_compile` / `json.load` / `--check` |
| 用 `sed` 改带 Windows 路径的内容 | 写文件工具，或 Python 替换 |

## 证据

事故记录见本页 frontmatter 的 `incidents`，统计由 `kb.py index` 生成。单项目、同一次会话内两次独立命中（sed 路径转义、heredoc 反斜杠），用户自述「遇到很多次了」；交付文档代码块那两条各一次。「吃掉一层」这个数是在这个 harness（Claude Code 的 Bash 工具到 Windows 上的 Git Bash）实测的，别的 harness 吃几层未测，但修法 1 和 3 对任何层数都成立。

## 相关

- [`../ci-windows/powershell-native-command-pitfalls.md`](../ci-windows/powershell-native-command-pitfalls.md)：同族的另一轴（编码、BOM、行尾）。
- [`../ci-windows/posix-tools-on-windows.md`](../ci-windows/posix-tools-on-windows.md)：`sed -i` 是重写加顶替。
- [`reporting-limits-and-null-results.md`](reporting-limits-and-null-results.md) 规则 3：「没有输出」的两种成因。
- [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)：那道预编译门自己要能红。
