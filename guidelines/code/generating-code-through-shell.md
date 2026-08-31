# 别用嵌套 shell 生成代码：转义被吃掉一层，而失败可以是静默的

## 核心规则

**要落盘会被解释器读的东西（`.py` / patch / `.mel` / JSON / 正则），用写文件工具，
不要用「shell heredoc → 解释器 → 生成文件」这条链。**

理由不是"不优雅"，是**转义要穿过比你以为更多的层，而少一层的表现可能是静默失败**。

跟 [`../ci-windows/powershell-native-command-pitfalls.md`](../ci-windows/powershell-native-command-pitfalls.md)
的 Pitfall 4 是同族**不同轴**：那条讲 PowerShell 落盘毁在**编码 / BOM / 行尾**三轴上；
本条讲**转义层数**，且**跟平台无关**（实测发生在 Git Bash 的 heredoc 里）。

## 实测：heredoc 吃掉一层反斜杠，而 `<<'EOF'` 挡不住

判定用**字节和长度**，不要用 `repr()` —— `repr` 把真换行也印成 `\n`，两种情况长得一样：

| 通道 | 我写的 | 解释器实际收到 | 结论 |
|---|---|---|---|
| heredoc（**含 `<<'EOF'`**）| `"A\\nB"` | `[65, 10, 66]` = `A` + **真换行** + `B` | **被吃掉一层** |
| heredoc | `"A\\\\nB"` | `[65, 92, 110, 66]` = `A` `\` `n` `B` | 四个反斜杠才得到字面 `\n` |
| argv（单引号传参）| `'A\nB'` | `[65, 92, 110, 66]` | **完整，不吃** |

⚠️ **`<<'EOF'` 引号 heredoc 本该是完全字面的** —— 它挡不住，说明吃转义的那一层
**在 shell 之上**（工具把命令字符串交给 shell 之前）。⇒ 「我用了引号 heredoc 所以安全」
是个错的心智模型。

## 为什么它比编码那一类更贵：失败形态可以是静默的

链条是：**生成的文件里出现真换行 → 字符串字面量未闭合 → SyntaxError → 整份文件编译失败。**

而如果那份文件是被 `exec()` / `import` / `-script` 加载的：

> **什么都不跑、什么都不报、表现跟卡死一模一样。**

实测代价：两轮各约 7 分钟的宿主启动等待，两次都先怀疑「环境慢 / 宿主卡了」，
而真因是生成的那个文件第 66 行有个未闭合的字符串。

⇒ 这跟 [`reporting-limits-and-null-results.md`](reporting-limits-and-null-results.md) 规则 3
是同一个病：**「没有输出」有两种成因**（还没跑完 / 压根没开始跑），而它们产生同一个观测。

## 三条修法，按优先级

1. **用写文件工具**（编辑器 / Write / Edit）。零转义层，也不吃行尾。
2. **非要走 shell：用 argv**，别用 heredoc。实测 argv 通道不吃反斜杠。
3. **干脆不产生反斜杠**：`chr(10)` / `splitlines()` / `" | ".join(...)` / `os.linesep`。
   ⇒ 这条最稳 —— 它让「有几层在吃」这个问题失去意义。

## 一道便宜的门：生成完先编译，再交给下游

```bash
python -m py_compile gen.py   || exit 2     # .py
python -c "import json,sys;json.load(open('a.json'))" || exit 2
git apply --check a.patch     || exit 2     # patch
```

它把「7 分钟静默卡死」换成「1 秒报错」，而且**报错指向生成的文件**而不是宿主。

⚠️ **这道门自己要先验能红** —— 注入一个语法错，看它拦不拦。一道只会绿的门比没有门更坏
（见 [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)
「先证明那道门能红」）。

## 同族新场景：交付文档里的代码块，交付前 exec / 编译一次

「生成完先编译」同样适用于**写进交付文档的代码块**——没有任何机制会检查它能不能跑（没有编译器、没有测试，审稿人读的是逻辑），而读者第一件事就是复制粘贴运行；一个少括号的 snippet 让他撞 SyntaxError，毁的是对整份文档的第一印象。实测配套三条：

- 逐块抽出 ```python 块 `compile()` 一遍（一份十节文档 8 块，一条命令的事）；
- **这道门自己先造红**（注入 `def f(:` 看它拦不拦）。实测两人各做了这条纪律的**不同一半**（一个编了全部块没造红、一个造了红但只编过两块）——「补做别人提的纪律」时，人补的是自己没做的那半，而不是那条纪律的全部，因为读到它时自己做过的那半已经产生「这条我做了」的感觉；
- **正文与文中工具会漂移**：正文讲了四档行为而自检脚本只实现两档 ⇒ 工具报假绿，而读者信工具多过正文（工具给结论，正文要读）。⇒ 改正文时问一句：**下面那个脚本实现了吗**。

（单项目一场，其中「正文对了、工具没跟上」两击。）

## Anti-Patterns

| 反 pattern | 为什么错 | 修法 |
|---|---|---|
| heredoc 里写 `\\n` 期望得到字面 `\n` | 被吃掉一层，得到真换行 | 写四个，或改用 `chr(10)` |
| 「我用了 `<<'EOF'` 所以是字面的」 | 吃转义的层在 shell 之上，引号挡不住 | 别把生成代码交给这条链 |
| 拿 `repr()` 判断转义对不对 | `repr` 把真换行也印成 `\n`，两种一样 | 看 `len()` / `list(s.encode())` |
| 生成完直接交给宿主跑 | 语法错 ⇒ 静默失败 ⇒ 误判成环境慢 | 先 `py_compile` / `json.load` / `--check` |
| 用 `sed` 改带 Windows 路径的内容 | 路径里的 `\` 和 `/` 会毁掉 sed 表达式（实测 `unterminated 's' command`）| 用写文件工具，或 Python 做替换 |

## 诚实边界

- **单项目、同一次会话内 2 次独立命中**（一次 `sed` 的路径转义、一次 heredoc 的 `\\n`），
  外加用户自述「遇到很多次了」。
- 「吃掉一层」这个数是**在这个 harness（Claude Code 的 Bash 工具 → Windows 上的 Git Bash）
  实测的**。别的 harness / shell 吃几层**未测** —— 但纪律不依赖那个数：
  修法 1 和 3 对任何层数都成立。

## 相关 Guidelines / Techniques

- [`../ci-windows/powershell-native-command-pitfalls.md`](../ci-windows/powershell-native-command-pitfalls.md)
  Pitfall 4 —— 同族的另一轴（编码 / BOM / 行尾），PowerShell 专属
- [`../ci-windows/posix-tools-on-windows.md`](../ci-windows/posix-tools-on-windows.md)
  —— `sed -i` 是重写 + 顶替；本条 Anti-Pattern 最后一行是它的转义面
- [`reporting-limits-and-null-results.md`](reporting-limits-and-null-results.md) 规则 3
  —— 「没有输出」的两种成因
- [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)
  —— 那道预编译门自己要能红
