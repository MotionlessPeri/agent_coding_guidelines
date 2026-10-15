# kb：语料库维护工具

一个零依赖的 Python 脚本，三个子命令。在仓库根运行。

| 命令 | 做什么 | 什么时候用 |
|---|---|---|
| `python scripts/kb/kb.py lint` | 查全库断链；查有 `class` 的页面字段；查经验页与事故记录的双向引用；复测超过 180 天报警 | 改过 `evidence/` 或任何带 frontmatter 的页面之后，提交之前 |
| `python scripts/kb/kb.py index` | 生成 [`evidence/INDEX.md`](../../evidence/INDEX.md)（按页面分组的事故表和计数）和 [`guidelines/CATALOG.md`](../../guidelines/CATALOG.md)（按类别的页面目录） | 同上；两个生成文件不手改 |
| `python scripts/kb/kb.py query 零命中 没有` | 按章节检索：返回命中的章节正文而不是整份文件；命中页面 frontmatter `triggers` 的词会加权 | 知道症状、不知道文件名时 |

`lint` 有错误退出码为 1，只有警告为 0。它检查的是结构，不检查内容对不对。

## 页面 frontmatter

只有需要机器读的页面才加。当前只对 `class: experience` 做字段检查：

```yaml
---
class: experience          # knowledge | norm | experience | procedure
scope: universal
triggers: [报结论, 做不到, 零命中]
born: "2026-08，写下时的模型未记录"
retested: ["2026-10-15 claude-fable-5-1 子代理无指南：3 pass / 1 partial，见 docs/evaluations/xxx.md"]
incidents:
  - 2026-08-example-slug
---
```

`retested` 条目是自由文本，但要含一个 `YYYY-MM-DD` 日期，lint 按最后一条判过期。事故记录的字段见 [`evidence/README.md`](../../evidence/README.md)。

已判定为经验类、但还没改成「边界 + 事故」形状的页面，写 `class: experience` 加 `status: legacy`：lint 只提醒待改形，不要求字段；CATALOG 里能看到哪些还没改。其他类别（`knowledge` / `norm` / `procedure`）只需要 `class` 和 `scope` 两行，lint 不查别的字段。
