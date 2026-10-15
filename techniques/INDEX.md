# 按操作查找流程

这些文件描述可复用的方法。只在需要该操作时读取，不因目录中存在某份流程就自动执行。

| 当前操作 | 资料 |
|---|---|
| 验证改动、识别不可靠的判据 | [对抗式验证](adversarial-verification.md) |
| 完整枚举后作出判断 | [先枚举再裁定](enumerate-then-adjudicate.md) |
| 协调子任务 | [协作方法](coordination-patterns.md)、[任务说明](worker-instructions.md) |
| 决定前取得事实证据 | [事实检查点](fact-forcing-gate.md) |
| 设计测量、报告读数 | [测量四问](measurement-four-questions.md) |
| 使用性能工具或调试器 | [性能分析](profiling-workflow.md)、[调试器脚本](debugger-scripting.md) |
| C++ 覆盖率与 CRAP 实测 | [覆盖率测量](cpp-coverage-and-crap-measurement.md) |
| 刻画闭源或无文档 API 参数 | [黑箱刻画](blackbox-api-characterization.md) |
| 在 DCC 宿主真界面里端到端验证插件 | [DCC 插件界面自动测试](dcc-plugin-gui-e2e-automation.md) |
| 安装、使用或排查 Model Worker MCP | [Model Worker MCP](model-worker-mcp.md) |
| 安装、使用或排查 Lane Router | [Lane Router](lane-router.md) |
| CI 向 P4 部署 | [P4 部署](ci-deploy-to-p4.md) |
| 配置 Claude Code 自主权限 | [Claude Code 权限](claude-code-autonomous-permissions.md) |

流程中的命令要按当前工具版本确认。文字检查点不会自行获得工具层的强制执行能力；授权来源仍以当前宿主、用户和项目约定为准。
