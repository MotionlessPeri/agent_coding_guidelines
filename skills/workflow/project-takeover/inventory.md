# 第 1 步：盘点现状

三个工具都只描述代码现在的样子，不读 git 历史、不收 TODO、也不知道哪条分支没合。这一步由你用 git 和检索自己做，产出一页「现状盘点」。

## 先找已有的交接材料

上一个人常常留了东西，先找再查：

```
rg -il "handoff|交接|实施计划|implementation plan|roadmap|TODO\.md|CHANGELOG" --glob "*.md"
ls docs docs/archive docs/plans 2>/dev/null
```

找到的文档按日期排，最近的先读；它说的「做到哪」要拿下面的 git 事实核一遍，文档可能比代码旧。

## git 六项

```
git status --short                       # 未提交、未跟踪
git stash list                           # 藏起来的半成品
git branch -a --no-merged <主分支>        # 没合的分支
git for-each-ref --sort=-committerdate --format="%(committerdate:short) %(refname:short) %(subject)" refs/heads refs/remotes | head -30
git log --oneline -50                    # 最近在改什么
git log --stat -20 | rg "^ \S+ \|" | awk "{print $1}" | xargs -n1 dirname | sort | uniq -c | sort -rn | head   # 最近改动落在哪些目录
rg -n "TODO|FIXME|HACK|XXX" --stats      # 末尾的 stats 告诉你集中在哪些文件
```

主分支名用 `git symbolic-ref refs/remotes/origin/HEAD` 查，查不到看 `git branch -a`。没合的分支逐条看最后一次提交的日期和作者：三个月没动的多半是弃掉的，但要写明「未确认」。

## 构建与测试

找构建入口（`package.json` 的 `scripts`、`pyproject.toml`、`CMakeLists.txt`、`Makefile`、`*.sln`），按仓库文档写的命令跑一次构建和测试。记下实际命令和结果；跑不起来也记，写明卡在哪一步，不猜原因。

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
