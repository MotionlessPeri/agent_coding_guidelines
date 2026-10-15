# 事故索引（生成文件，勿手改）

由 `python scripts/kb/kb.py index` 从 `evidence/incidents/` 生成。按引用页面分组；统计只是计数，不是规则的权重。

## guidelines/code/diagnose-before-fixing.md

引用本页的事故 4 条。

| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |
|---|---|---|---|---|---|
| [2026-06-visualizer-fix-before-evidence](incidents/2026-06-visualizer-fix-before-evidence.md) | 2026-06 | 命中 | 用户 | 盲改, 取证 | 视口控制点手柄不显示。agent 第一反应是「八成是 `GUnrealEd` 在 `StartupModule` 时为 null 导致 c… |
| [2026-08-host-hang-blamed-on-user-file](incidents/2026-08-host-hang-blamed-on-user-file.md) | 2026-08 | 命中 | 用户 | rule-1, 用户产物, 加载器 | 宿主打不开用户交来的场景文件，报出去的话是「这份 fbx 打不开，可能是它坏了」。 |
| [2026-08-stream-died-after-unlogged-user-action](incidents/2026-08-stream-died-after-unlogged-user-action.md) | 2026-08 | 命中 | 用户 | 操作史, 日志 | 一个下游订阅方的数据流永久失效，日志只有一条格式错误，没有任何操作痕迹。 |
| [2026-08-validator-warning-pointed-at-local-code](incidents/2026-08-validator-warning-pointed-at-local-code.md) | 2026-08 | 命中 | 实验 | 校验器, 上游数据, 方向性oracle | 重定向框架报「髋部没朝向 +Z 轴 / 手臂不平行于 X 轴」，两条都指向「骨架是怎么建的」，差一步去改建骨代码的朝向。 |

- 类型：命中 4
- 发现方式：用户 3、实验 1
- 标签：rule-1 1、上游数据 1、加载器 1、取证 1、操作史 1、方向性oracle 1、日志 1、校验器 1、用户产物 1、盲改 1

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
