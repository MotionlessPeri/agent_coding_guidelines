# 第 1 步：盘点现状

三个工具都只描述代码现在的样子，不读 git 历史、不收 TODO、也不知道哪条分支没合。这一步由你用 git 和检索自己做，产出一页「现状盘点」。

## 先找已有的交接材料

上一个人常常留了东西，先找再查。下面的命令只用 git 自带的子命令和各 shell 自带的管道，不依赖 `rg`、`head`、`awk`、`xargs`（Windows 上常常没有）。

bash / zsh：

```bash
git grep -il -E "handoff|交接|实施计划|implementation plan|roadmap" -- "*.md"
git ls-files docs | head -50
```

PowerShell 5.1：

```powershell
git ls-files -- "*.md" | Where-Object { Select-String -Path $_ -Pattern "handoff|交接|实施计划|implementation plan|roadmap" -Quiet -Encoding utf8 }
git ls-files docs | Select-Object -First 50
```

找到的文档按日期排，最近的先读；它说的「做到哪」要拿下面的 git 事实核一遍，文档可能比代码旧。

## git 六项

两个 shell 通用的四条：

```
git status --short                       # 未提交、未跟踪
git stash list                           # 藏起来的半成品
git branch -a --no-merged <主分支>        # 没合的分支
git log --oneline -50                    # 最近在改什么
```

带管道的三条，bash / zsh：

```bash
git for-each-ref --sort=-committerdate --format="%(committerdate:short) %(refname:short) %(subject)" refs/heads refs/remotes | head -30
git log -20 --name-only --format="" | grep . | xargs -n1 dirname | sort | uniq -c | sort -rn | head        # 最近改动落在哪些目录
git grep -n -E "TODO|FIXME|HACK|XXX" | cut -d: -f1 | sort | uniq -c | sort -rn | head                     # TODO 集中在哪些文件
```

同样三条，PowerShell 5.1：

```powershell
git for-each-ref --sort=-committerdate --format="%(committerdate:short) %(refname:short) %(subject)" refs/heads refs/remotes | Select-Object -First 30
git log -20 --name-only --format="" | Where-Object { $_ } | ForEach-Object { Split-Path $_ -Parent } | Group-Object | Sort-Object Count -Descending | Select-Object -First 10 Count, Name
git grep -n -E "TODO|FIXME|HACK|XXX" | ForEach-Object { ($_ -split ":")[0] } | Group-Object | Sort-Object Count -Descending | Select-Object -First 10 Count, Name
```

主分支名用 `git symbolic-ref refs/remotes/origin/HEAD` 查，查不到看 `git branch -a`。没合的分支逐条看最后一次提交的日期和作者：三个月没动的多半是弃掉的，但要写明「未确认」。

## 构建与测试

找构建入口（`package.json` 的 `scripts`、`pyproject.toml`、`CMakeLists.txt`、`Makefile`、`*.sln`），按仓库文档写的命令跑一次构建和测试。记下实际命令和结果；跑不起来也记，写明卡在哪一步，不猜原因。测试结果连机器状态一起记：忙机器上的超时类失败不算回归，没复跑就写「未判明」。

## 现状盘点一页的格式

```
# <仓库名> 现状盘点（<YYYY-MM-DD>，提交 <短 sha>，分支 <名>）

## 已有交接材料
- <路径>：<一句话它说做到哪>（<文档日期>）

## 分支
- 主分支 <名>，最新提交 <日期>
- 没合的：<分支> <最后提交日期> <作者> <一句话在做什么>

## 未提交 / stash
- <有或无；有则列文件和看起来在做什么>

## 最近 50 个提交在改什么
- <目录或模块>：<几个提交，做了什么>

## TODO / FIXME
- <文件或目录>：<条数，主要是什么>

## 构建与测试
- 构建：<命令> → <通过 / 失败在哪>
- 测试：<命令> → <通过数 / 失败数 / 跑不起来的原因>

## 疑点
- <代码和文档对不上的地方、看不懂的决定>
```

写完检查：六项每项都有结论或「没查到」；每条结论能指到命令输出或文件。这一页是第 5 步总览的主要材料。
