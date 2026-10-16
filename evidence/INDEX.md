# 事故索引（生成文件，勿手改）

由 `python scripts/kb/kb.py index` 从 `evidence/incidents/` 生成。按引用页面分组；统计只是计数，不是规则的权重。

## guidelines/code/diagnose-before-fixing.md

引用本页的事故 5 条。

| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |
|---|---|---|---|---|---|
| [2026-06-visualizer-fix-before-evidence](incidents/2026-06-visualizer-fix-before-evidence.md) | 2026-06 | 命中 | 用户 | 盲改, 取证 | 视口控制点手柄不显示。agent 第一反应是「八成是 `GUnrealEd` 在 `StartupModule` 时为 null 导致 c… |
| [2026-08-host-hang-blamed-on-user-file](incidents/2026-08-host-hang-blamed-on-user-file.md) | 2026-08 | 命中 | 用户 | rule-1, 用户产物, 加载器 | 宿主打不开用户交来的场景文件，报出去的话是「这份 fbx 打不开，可能是它坏了」。 |
| [2026-08-stream-died-after-unlogged-user-action](incidents/2026-08-stream-died-after-unlogged-user-action.md) | 2026-08 | 命中 | 用户 | 操作史, 日志 | 一个下游订阅方的数据流永久失效，日志只有一条格式错误，没有任何操作痕迹。 |
| [2026-08-validator-warning-pointed-at-local-code](incidents/2026-08-validator-warning-pointed-at-local-code.md) | 2026-08 | 命中 | 实验 | 校验器, 上游数据, 方向性oracle | 重定向框架报「髋部没朝向 +Z 轴 / 手臂不平行于 X 轴」，两条都指向「骨架是怎么建的」，差一步去改建骨代码的朝向。 |
| [2026-10-coordinator-deferred-diagnostic-evidence](incidents/2026-10-coordinator-deferred-diagnostic-evidence.md) | 2026-10 | 命中 | 用户 | coordination, diagnostic-priority, delivery | 基础流程反复阻塞，协调者已多次报告诊断信息不足，却继续优先安排旧状态追查、恢复和局部修补，直到交付截止后才完成请求关联日志的私有候选，仍未… |

- 类型：命中 5
- 发现方式：用户 4、实验 1
- 标签：coordination 1、delivery 1、diagnostic-priority 1、rule-1 1、上游数据 1、加载器 1、取证 1、操作史 1、方向性oracle 1、日志 1、校验器 1、用户产物 1、盲改 1

## guidelines/code/generating-code-through-shell.md

引用本页的事故 4 条。

| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |
|---|---|---|---|---|---|
| [2026-08-heredoc-ate-a-backslash](incidents/2026-08-heredoc-ate-a-backslash.md) | 2026-08 | 命中 | 自查 | shell生成代码, 转义, 静默失败 | 用「shell heredoc 到解释器再生成文件」这条链落盘一个 `.py`，源里写的 `"A\\nB"` 到了解释器变成 `A` 加真… |
| [2026-08-prose-four-tiers-script-two](incidents/2026-08-prose-four-tiers-script-two.md) | 2026-08 | 命中 | 第三方复核 | 交付文档代码块, 正文与工具漂移 | 文档正文讲了四档行为，文中附带的自检脚本只实现了两档。 |
| [2026-08-sed-choked-on-windows-path](incidents/2026-08-sed-choked-on-windows-path.md) | 2026-08 | 命中 | 自查 | shell生成代码, 转义, sed | 用 `sed` 改一段含 Windows 路径的内容，报 `unterminated 's' command`。 |
| [2026-08-two-people-each-did-half-the-compile-gate](incidents/2026-08-two-people-each-did-half-the-compile-gate.md) | 2026-08 | 命中 | 第三方复核 | 交付文档代码块, 先编译, 造红 | 一份十节文档里 8 个 ```python 代码块，交付前要「逐块 compile 一遍，且先造红」。两人各做了这条纪律的不同一半：一个编… |

- 类型：命中 4
- 发现方式：第三方复核 2、自查 2
- 标签：shell生成代码 2、交付文档代码块 2、转义 2、sed 1、先编译 1、正文与工具漂移 1、造红 1、静默失败 1

## guidelines/code/gui-visual-machine-gating.md

引用本页的事故 3 条。

| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |
|---|---|---|---|---|---|
| [2026-07-offscreen-gl-segfault-in-smoke](incidents/2026-07-offscreen-gl-segfault-in-smoke.md) | 2026-07 | 命中 | 实验 | GUI验证, 离屏渲染 | 想用 `QT_QPA_PLATFORM=offscreen` 无头渲染截图做冒烟，`pyqtgraph.opengl` 的 `GLView… |
| [2026-07-pure-function-gate-with-gl-smoke-only](incidents/2026-07-pure-function-gate-with-gl-smoke-only.md) | 2026-07 | 生效 | 自查 | GUI验证, 纯函数gate | 一个 PySide6 加 pyqtgraph.opengl 视口的 GUI 测试工具，消费一个 pybind 的 C++ 重定向库。每个功… |
| [2026-07-ui-framework-chosen-by-viewport-texture-path](incidents/2026-07-ui-framework-chosen-by-viewport-texture-path.md) | 2026-07 | 命中 | 事后复盘 | GUI验证, 框架选型, 渲染器视口 | 给一个主输出是实时 GPU 画面的工具选 UI 框架时，按控件多不多、好不好看比较。 |

- 类型：命中 2、生效 1
- 发现方式：事后复盘 1、实验 1、自查 1
- 标签：GUI验证 3、框架选型 1、渲染器视口 1、离屏渲染 1、纯函数gate 1

## guidelines/code/premises-not-in-the-text.md

引用本页的事故 8 条。

| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |
|---|---|---|---|---|---|
| [2026-08-autocrlf-was-system-level](incidents/2026-08-autocrlf-was-system-level.md) | 2026-08 | 命中 | 实验 | 前提, 机器, 内在前提 | 写下「本仓的 `core.autocrlf=true`」。 |
| [2026-08-commit-email-domain-as-outsider-test](incidents/2026-08-commit-email-domain-as-outsider-test.md) | 2026-08 | 命中 | 实验 | 前提, 人员构成, 谁的仓 | 用「commit email 不是我们的域 ⇒ 这是外部的改动」做判据。 |
| [2026-08-compression-dropped-two-qualifiers](incidents/2026-08-compression-dropped-two-qualifiers.md) | 2026-08 | 命中 | 第三方复核 | 前提, 改写压缩 | 把一份技术说明压成宣发版，两处作用域限定同时丢了：「仅旋转式导出成立」这个前提，和界面上的真实字样。 |
| [2026-08-line-numbers-broken-by-own-insertion](incidents/2026-08-line-numbers-broken-by-own-insertion.md) | 2026-08 | 命中 | 自查 | 前提, 移动引用, 行号 | 为消歧在文档里插入了一节 14 行，节内用行号引用文中别处。 |
| [2026-08-recipe-copied-missing-two-premises](incidents/2026-08-recipe-copied-missing-two-premises.md) | 2026-08 | 命中 | 事后复盘 | 前提, 配方 | 一条被标成「成本是一条命令」的验证配方发出后数分钟内被另一方原样照抄。 |
| [2026-08-recipe-pinned-to-head](incidents/2026-08-recipe-pinned-to-head.md) | 2026-08 | 命中 | 事后复盘 | 前提, 时刻, 移动引用 | 一条复现配方写 `git show HEAD:<path>` 来取「坏版本」。 |
| [2026-08-relative-time-quantifier-in-wrapup](incidents/2026-08-relative-time-quantifier-in-wrapup.md) | 2026-08 | 命中 | 事后复盘 | 前提, 相对时间量词, 收口 | 收口判断写成「最近三轮全是…」「至今没有新东西了」。 |
| [2026-08-scope-words-four-lanes-one-day](incidents/2026-08-scope-words-four-lanes-one-day.md) | 2026-08 | 命中 | 第三方复核 | 前提, 作用域, 归纳 | 同一天四方并行对话各犯一次作用域缺失：一个实例写成整层禁令；修法层面的约束写成「做不成」；手列出来的几个面写成「仅此一处」；朝一个方向失效… |

- 类型：命中 8
- 发现方式：事后复盘 3、实验 2、第三方复核 2、自查 1
- 标签：前提 8、移动引用 2、人员构成 1、作用域 1、内在前提 1、归纳 1、收口 1、改写压缩 1、时刻 1、机器 1、相对时间量词 1、行号 1、谁的仓 1、配方 1

## guidelines/code/reporting-limits-and-null-results.md

引用本页的事故 24 条。

| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |
|---|---|---|---|---|---|
| [2026-08-absent-for-a-guessed-class-name](incidents/2026-08-absent-for-a-guessed-class-name.md) | 2026-08 | 生效 | 自查 | rule-3, 猜的名字 | 探测一个类名返回 `ABSENT`，差一步报「框架没有这个工厂」。 |
| [2026-08-alpha-zero-called-a-property](incidents/2026-08-alpha-zero-called-a-property.md) | 2026-08 | 命中 | 外部追问 | rule-4, 数字的机制 | 一个参数 `alpha=0` 时「行为在两种坐标约定下相反」被写成该参数的性质。 |
| [2026-08-change-gate-blind-to-never-existed](incidents/2026-08-change-gate-blind-to-never-existed.md) | 2026-08 | 命中 | 事后复盘 | rule-3, 可达范围 | 一个只在数值变化时报警的 gate 一直绿，被读成「这个量没问题」。 |
| [2026-08-dedup-log-hid-1800-events](incidents/2026-08-dedup-log-hid-1800-events.md) | 2026-08 | 命中 | 自查 | rule-2, 事件聚合 | 30 fps 流送里每帧失败持续一整分钟，日志里只有一行，行内计数显示 01。差一步报成「只发生一次，偶发抖动，忽略即可」。 |
| [2026-08-directory-skeleton-mistaken-for-source](incidents/2026-08-directory-skeleton-mistaken-for-source.md) | 2026-08 | 命中 | 自查 | rule-3, 镜像形态 | 检查三个第三方依赖在不在，`ls -d` 三个目录全部存在，差一步报「依赖齐全，问题在别处」。 |
| [2026-08-evidence-in-unreachable-repo](incidents/2026-08-evidence-in-unreachable-repo.md) | 2026-08 | 命中 | 第三方复核 | rule-3, 可达范围 | 审计一份文档，判某条断言「无刻画记录 / 无依据」。 |
| [2026-08-filename-pattern-missed-the-asset](incidents/2026-08-filename-pattern-missed-the-asset.md) | 2026-08 | 命中 | 第三方复核 | rule-3, 可达范围 | 按 `*rig*` / `*ik_*` 文件名模式扫一个目录，报「这个资产没有配套的 X」。 |
| [2026-08-forked-bridge-mistaken-for-stock](incidents/2026-08-forked-bridge-mistaken-for-stock.md) | 2026-08 | 命中 | 第三方复核 | rule-1, 反方向 | 报「旧插件用自定义属性把时码流到下游，这个做法可用，记为 deferred 以后接」。 |
| [2026-08-grep-only-reached-vendored-subset](incidents/2026-08-grep-only-reached-vendored-subset.md) | 2026-08 | 命中 | 事后复盘 | rule-3, 可达范围 | 消费方查「库里有没有 X」，grep 零命中，报「没有」。 |
| [2026-08-host-hang-blamed-on-user-file](incidents/2026-08-host-hang-blamed-on-user-file.md) | 2026-08 | 命中 | 用户 | rule-1, 用户产物, 加载器 | 宿主打不开用户交来的场景文件，报出去的话是「这份 fbx 打不开，可能是它坏了」。 |
| [2026-08-lane-rejected-own-candidate](incidents/2026-08-lane-rejected-own-candidate.md) | 2026-08 | 生效 | 事后复盘 | rule-3, 规则生效统计 | 同一天六条 lane 的收尾复盘里，统计「报结论」这组规则有没有当场拦住过误判。 |
| [2026-08-log-file-as-observation-window](incidents/2026-08-log-file-as-observation-window.md) | 2026-08 | 命中 | 事后复盘 | rule-3, 观测窗口 | 报「日志里零命中，所以修复后没有复发」。 |
| [2026-08-mirror-declared-unsolvable-at-receiver](incidents/2026-08-mirror-declared-unsolvable-at-receiver.md) | 2026-08 | 命中 | 实验 | rule-1, 解法量词, 继承的规格 | 交接规格写「这个镜像藏在四元数里，接收端解不开」，并明确指示「别在接收端事后转一下」。下游 agent 忠实继承并再转发了一圈。 |
| [2026-08-offline-annotation-assumed-required](incidents/2026-08-offline-annotation-assumed-required.md) | 2026-08 | 命中 | 用户 | rule-1, 归错层 | 报「依赖离线人工标注，不适用」，整个能力被搁置。 |
| [2026-08-one-consumer-site-generalized](incidents/2026-08-one-consumer-site-generalized.md) | 2026-08 | 命中 | 第三方复核 | rule-4, 只取一个点 | 从一处消费点推出「这个参数在别处不被消费」。 |
| [2026-08-optional-dict-blamed-on-the-contract](incidents/2026-08-optional-dict-blamed-on-the-contract.md) | 2026-08 | 命中 | 用户 | rule-1, 归错层 | 报「契约表达不了挂两份算子，已请上游裁决」。 |
| [2026-08-ordering-constraint-under-another-name](incidents/2026-08-ordering-constraint-under-another-name.md) | 2026-08 | 命中 | 第三方复核 | rule-4, 按名字查 | 某顺序约束的逐对声明接口在三个算子里 grep 零命中，报成「框架不拦顺序」。 |
| [2026-08-p95-blind-to-threshold](incidents/2026-08-p95-blind-to-threshold.md) | 2026-08 | 命中 | 自查 | rule-2, 数值聚合 | 一个按速度阈值决定是否「锁住」的算子，阈值扫了 60 倍，p95 与最大值三档完全不动，初判「参数没接上，主导因素不是阈值」。 |
| [2026-08-port-covered-half-the-operator](incidents/2026-08-port-covered-half-the-operator.md) | 2026-08 | 命中 | 第三方复核 | rule-1, 归错层 | 报出去的话是「这个算子从不解决 A-vs-B 那类穿插，这是它的能力边界」。协调者把这句原样转给了第三方 lane。 |
| [2026-08-stash-control-group-never-ran](incidents/2026-08-stash-control-group-never-ran.md) | 2026-08 | 命中 | 自查 | rule-3, 对照组 | 用 `git stash` 前后各数一次测试数当对照组，两次数出同一个数，读成「改动没有影响」。 |
| [2026-08-symptom-hung-on-wrong-cause](incidents/2026-08-symptom-hung-on-wrong-cause.md) | 2026-08 | 命中 | 事后复盘 | rule-1, 文档写法 | 一份接入文档写「视口不实现某方法 ⇒ 拖拽后没有撤销」。 |
| [2026-08-toolset-scan-mistaken-for-framework](incidents/2026-08-toolset-scan-mistaken-for-framework.md) | 2026-08 | 命中 | 第三方复核 | rule-3, 可达范围 | 扫遍某个工具集找不到程序化入口，报「这个框架不支持程序化配置」。 |
| [2026-08-uncertainty-moved-to-mesh-consumer](incidents/2026-08-uncertainty-moved-to-mesh-consumer.md) | 2026-08 | 命中 | 外部追问 | rule-4, 数字的机制 | 「源侧推法的不确定度等于被消费量的 28% 到 67%」被外推到另一个消费方的对照上。 |
| [2026-10-compaction-hid-own-test-tool](incidents/2026-10-compaction-hid-own-test-tool.md) | 2026-10 | 命中 | 用户 | rule-3, 可达范围, 上下文压缩 | 上下文压缩之后报「插件只有界面按钮，这个我测不了」，把测试交给用户。 |

- 类型：命中 22、生效 2
- 发现方式：第三方复核 7、事后复盘 5、自查 5、用户 4、外部追问 2、实验 1
- 标签：rule-3 11、rule-1 7、可达范围 6、rule-4 4、归错层 3、rule-2 2、数字的机制 2、上下文压缩 1、事件聚合 1、加载器 1、反方向 1、只取一个点 1、对照组 1、按名字查 1、数值聚合 1、文档写法 1、猜的名字 1、用户产物 1、继承的规格 1、观测窗口 1、规则生效统计 1、解法量词 1、镜像形态 1

## guidelines/code/reuse-before-implementing.md

引用本页的事故 5 条。

| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |
|---|---|---|---|---|---|
| [2026-05-subprocess-helper-extracted-late](incidents/2026-05-subprocess-helper-extracted-late.md) | 2026-05 | 命中 | 用户 | 复用, 重复堆叠 | 660 行的 subprocess 逻辑（路径校验、CreateProc、30 s 超时、exit code、MessageLog）在 `… |
| [2026-08-lock-scope-outgrown-by-function-body](incidents/2026-08-lock-scope-outgrown-by-function-body.md) | 2026-08 | 命中 | 自查 | 复用, 隐含假设随演化失效 | 一个只做数据搬运时合理的「整函数加锁，在实时回调里调用」，后来被塞进了重计算。 |
| [2026-08-mobu-samples-had-the-exact-device-example](incidents/2026-08-mobu-samples-had-the-exact-device-example.md) | 2026-08 | 命中 | 自查 | 复用, 框架侧reference-impl, 随装samples | 一个「设备插件怎么写、跨版本有无差异」的问题，本来要靠旧版本经验加网络搜索推测。 |
| [2026-08-rotation-order-declared-never-read](incidents/2026-08-rotation-order-declared-never-read.md) | 2026-08 | 命中 | 自查 | 复用, 错误实现无害潜伏, 全链一致地错 | 配置文件声明了旋转序，解析进字段后再无任何读取点，全链走框架默认序。 |
| [2026-08-wrong-matrix-overwritten-each-frame](incidents/2026-08-wrong-matrix-overwritten-each-frame.md) | 2026-08 | 命中 | 自查 | 复用, 错误实现无害潜伏, 输出被覆盖 | 一个「局部转全局」的矩阵函数把入参在函数内覆盖后自乘，算出的是父变换的平方，骨骼自身的成员从未参与。它有注释、命名合理、被真实调用，功能也… |

- 类型：命中 5
- 发现方式：自查 4、用户 1
- 标签：复用 5、错误实现无害潜伏 2、全链一致地错 1、框架侧reference-impl 1、输出被覆盖 1、重复堆叠 1、随装samples 1、隐含假设随演化失效 1

## guidelines/collaboration/lane-topology-design.md

引用本页的事故 10 条。

| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |
|---|---|---|---|---|---|
| [2026-08-archived-address-semantics-changed-thrice](incidents/2026-08-archived-address-semantics-changed-thrice.md) | 2026-08 | 命中 | 事后复盘 | lane拓扑, 重划执行, 平台语义 | 「归档后的 lane 地址能否复用」在一周内收到三封互相推翻的更正。 |
| [2026-08-four-cross-lane-errors-all-on-seams](incidents/2026-08-four-cross-lane-errors-all-on-seams.md) | 2026-08 | 命中 | 事后复盘 | lane拓扑, 接缝 | 一周内四次 lane 互抓错，全部发生在两条 lane 都会碰的契约面上：共享容器、双向信号、同名异义函数。`set_undo_stack… |
| [2026-08-hotfix-lane-premise-silently-gone](incidents/2026-08-hotfix-lane-premise-silently-gone.md) | 2026-08 | 命中 | 事后复盘 | lane拓扑, 存在前提 | hotfix 独立 lane 一直在，值守流量很低。 |
| [2026-08-lane-boundaries-crossed-repo-boundaries](incidents/2026-08-lane-boundaries-crossed-repo-boundaries.md) | 2026-08 | 命中 | 事后复盘 | lane拓扑, 按仓切 | 8 条 lane 按「技术子域 + 职能」混切（render、ui 按子域，arch、review、hotfix 按职能）。代码持续下沉进… |
| [2026-08-lane-ran-in-removed-worktree-dir](incidents/2026-08-lane-ran-in-removed-worktree-dir.md) | 2026-08 | 命中 | 第三方复核 | lane拓扑, 重划执行, cwd | 一条 lane 长期跑在一个已拆掉的 worktree 残留目录里。 |
| [2026-08-pin-advance-checks-missed-17-modules](incidents/2026-08-pin-advance-checks-missed-17-modules.md) | 2026-08 | 命中 | 事后复盘 | lane拓扑, 事件触发 | 版本钉定前进、目录搬迁之后的连带检查靠人记得，层表的登记欠账攒到 17 个模块才被撞见。 |
| [2026-08-review-lane-idle-between-campaigns](incidents/2026-08-review-lane-idle-between-campaigns.md) | 2026-08 | 命中 | 事后复盘 | lane拓扑, 审查campaign制 | 一条常驻的 review lane，一场审计满负荷，平时零负载。 |
| [2026-08-seam-count-inflated-by-test-references](incidents/2026-08-seam-count-inflated-by-test-references.md) | 2026-08 | 命中 | 第三方复核 | lane拓扑, 接缝计数 | 接缝表给一条缝的 breaking change 预告等级定高了一档。 |
| [2026-08-seam-numbers-in-brief-anchored-all-lanes](incidents/2026-08-seam-numbers-in-brief-anchored-all-lanes.md) | 2026-08 | 命中 | 事后复盘 | lane拓扑, brief锚定, 独立复核 | 接缝表里的数字进了派单 brief，所有 lane 都读到了同一个数。 |
| [2026-08-shared-tree-write-conflicts](incidents/2026-08-shared-tree-write-conflicts.md) | 2026-08 | 命中 | 事后复盘 | lane拓扑, 共享树, 实现权分散 | 多条 lane 同时写一个仓。三起事故：共享 git 索引互吞，索引差 3 秒吞掉 4 个文件；一条「只改 docstring」的 com… |

- 类型：命中 10
- 发现方式：事后复盘 8、第三方复核 2
- 标签：lane拓扑 10、重划执行 2、brief锚定 1、cwd 1、事件触发 1、共享树 1、存在前提 1、实现权分散 1、审查campaign制 1、平台语义 1、按仓切 1、接缝 1、接缝计数 1、独立复核 1

## techniques/adversarial-verification.md

引用本页的事故 1 条。

| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |
|---|---|---|---|---|---|
| [2026-10-retest-probe-inherited-the-rules](incidents/2026-10-retest-probe-inherited-the-rules.md) | 2026-10 | 命中 | 自查 | 探针不干净, 对照组, 量具先自证 | 给两份经验页做「干净模型还犯不犯」的复测，用本会话派生的子代理逐题作答，8 题全部通过，答案逐字复述规则原文，连「真名少一个 -er」「计… |

- 类型：命中 1
- 发现方式：自查 1
- 标签：对照组 1、探针不干净 1、量具先自证 1

## techniques/measurement-four-questions.md

引用本页的事故 9 条。

| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |
|---|---|---|---|---|---|
| [2026-08-biased-ground-truth-produced-fake-failures](incidents/2026-08-biased-ground-truth-produced-fake-failures.md) | 2026-08 | 命中 | 第三方复核 | 测量四问, 真值有偏 | 用有缺陷的真值去评一个判别器，得到一批失败点；下游据此建了「有一部分不受该缺陷影响」的结论。 |
| [2026-08-commit-diff-rule-called-a-hole](incidents/2026-08-commit-diff-rule-called-a-hole.md) | 2026-08 | 命中 | 第三方复核 | 测量四问, 判据, 覆盖不了的两种意思 | 某类损坏没被「提交前读全 diff」拦住，被说成那条纪律有洞。 |
| [2026-08-control-files-were-the-minority](incidents/2026-08-control-files-were-the-minority.md) | 2026-08 | 命中 | 实验 | 测量四问, 总体, 报分母 | 拿 3 个「没碰过的」文件当对照组判行尾口径，结论反了。 |
| [2026-08-count-grew-with-observation](incidents/2026-08-count-grew-with-observation.md) | 2026-08 | 命中 | 自查 | 测量四问, 总体, 随观测增长 | 一个计数 4 变 5 变 6，涨的全是观测行为本身产生的。 |
| [2026-08-filter-clause-judged-dead-by-constructed-sample](incidents/2026-08-filter-clause-judged-dead-by-constructed-sample.md) | 2026-08 | 命中 | 实验 | 测量四问, 样本, A/B | 判一条过滤子句是不是死代码，用构造样本推理，结论「死代码」。 |
| [2026-08-four-probe-failures-one-day](incidents/2026-08-four-probe-failures-one-day.md) | 2026-08 | 命中 | 第三方复核 | 测量四问, 量具 | 同一天四条并行对话里，临时写的探针各坏了一次：grep 模式写错报 0 而内容在；用行号定位内容，文件被追加过，行号早漂了；求差指纹在混合… |
| [2026-08-scanner-counted-itself](incidents/2026-08-scanner-counted-itself.md) | 2026-08 | 命中 | 自查 | 测量四问, 总体, 量具在总体里 | 一个扫描器把自己的脚本算成了「写过那个文件」的进程。 |
| [2026-08-stub-gave-both-methods](incidents/2026-08-stub-gave-both-methods.md) | 2026-08 | 命中 | 第三方复核 | 测量四问, 样本, 构造样本盲区 | 做降级实验的 stub 把一组两个方法都给全了，于是「只给一半会怎样」这一格从未进样本。 |
| [2026-08-wcag-threshold-answered-another-question](incidents/2026-08-wcag-threshold-answered-another-question.md) | 2026-08 | 命中 | 第三方复核 | 测量四问, 判据, 证据升级时判据要重选 | 「浅底上 32% 白字看不见」从目测推断升级成 WCAG 对比率，顺手用了 4.5:1 这条无障碍标准线。 |

- 类型：命中 9
- 发现方式：第三方复核 5、实验 2、自查 2
- 标签：测量四问 9、总体 3、判据 2、样本 2、A/B 1、报分母 1、构造样本盲区 1、真值有偏 1、覆盖不了的两种意思 1、证据升级时判据要重选 1、量具 1、量具在总体里 1、随观测增长 1
