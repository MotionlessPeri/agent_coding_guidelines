---
class: experience
scope: universal
triggers: [maya.exe, GUI 测试, loadPlugin, Untrusted Plugin Loading, 信任中心, Trust Center, MAYA_APP_DIR, 每次都要同意, Security Warning]
born: "2026-10-21 claude-opus-5-5，Maya 2024 实测"
retested: []
incidents:
  - 2026-10-maya-gui-test-trust-prompt-every-run
---

# Maya GUI 测试：插件放固定目录，只让用户信任一次

agent 在交互 `maya.exe` 里加载自己编的插件做测试时，Maya 的信任中心会对「不在允许列表里的目录」弹安全确认，
要人点。安排不当会每轮都弹，用户每轮被打断一次。下面的规则让同一个项目的同一个 Maya 版本**一辈子只问一次**。

适用：Maya 2024 实测（2026-10-21）；别的版本有没有同样的信任中心、选项名是否相同未核。
`mayapy` / `mayabatch` 等无头运行没有测过。

## 规则

1. **每个项目 × Maya 版本固定一个测试插件目录。** 每次测试前把新编的 `.mll` 和它要的同目录依赖
   （DLL、shader 等）覆盖拷进去，再从这里 `loadPlugin`。不要直接从各个编译目录加载，那样每个目录都要信任一次。
2. **不同项目不共用一个插件目录。** 同名依赖 DLL 会互相覆盖。
3. **`MAYA_APP_DIR` 用一份固定的 agent 专用偏好目录**，和插件目录放在一起。不要每轮新建：允许列表存在这份偏好里，
   新建等于清空。也不要用用户自己平时的偏好目录：测试会改它的窗口布局和各种 optionVar。
4. **第一次加载由用户确认。** 弹出「Untrusted Plugin Loading - Security Warning」时，请用户先勾
   「Apply to all plugins in this location」再点 Allow。之后在这个目录里覆盖成新文件也不再问。
5. **测试结束要正常退出 Maya。** 偏好在退出时写盘；超时被 kill 的那一轮不会保存这次的同意。
   看门狗的时限要把「等用户点确认」的时间算进去。
6. **脚本不替人处理安全确认。** 不点 Allow；不用 `optionVar -sva SafeModeAllowedlistPaths` 自己加目录
   （Maya 会另弹「Security Preferences Changing」要人确认）；不直接改 `userPrefs.mel` 绕过确认。
   自动化遇到安全框就停下等人，或者按失败报告。
7. **`loadPlugin` 没报错不等于插件加载成功。** 安全框被关掉（等于 Deny）时，`loadPlugin` 也不抛异常。
   要看插件自己的初始化痕迹（日志、注册的命令或节点）。

推荐的目录形状（Windows）：

```text
%USERPROFILE%\agent_maya_test\<项目>\Maya<版本>\plug-ins\   ← 每次覆盖拷入的插件
%USERPROFILE%\agent_maya_test\<项目>\maya_app_dir\           ← MAYA_APP_DIR，跨轮保留
```

## 机制

依据：Maya 2024 自带脚本 `scripts/startup/createPrefWndUI.mel`（`onTrustCenterPathAddButton`）与
`createPreferencesOptVars.mel`，以及 2026-10-21 的实测。

- 允许列表是 optionVar `SafeModeAllowedlistPaths`，字符串数组，元素是目录，用正斜杠。总开关是
  `TrustCenterPathOption`（默认 1 = 开）。两者都存在 `<MAYA_APP_DIR>/<版本>/prefs/userPrefs.mel`。
- 从不在列表里的目录加载插件时，`loadPlugin` 期间弹出模态框「Untrusted Plugin Loading - Security Warning」，
  有 Allow / Deny 两个按钮和「Apply to all plugins in this location」勾选框。勾选后点 Allow，这个目录会被追加进列表。
- 关掉这个框等于 Deny：`loadPlugin` 正常返回，但插件的 `initializePlugin` 没有跑（实测插件日志一行都没有）。
- 脚本执行 `optionVar -sva SafeModeAllowedlistPaths <目录>` 时，Maya 弹「Security Preferences Changing」
  要人确认；不确认，列表就不变。

## 验证状态

2026-10-21，Maya 2024，同一台 Windows 机器上实测：

- 每轮新建 `MAYA_APP_DIR`、插件从编译目录加载：每轮都弹。
- 关掉安全框：插件没有初始化，`loadPlugin` 也没报错。
- 脚本追加允许列表：弹「Security Preferences Changing」。
- 用户在固定目录勾选后点 Allow 一次，正常退出；下一轮把不同哈希的 `.mll` 覆盖进同一目录再加载，没有任何弹窗，插件正常初始化。

未核：允许列表是否覆盖子目录、其他 Maya 版本，以及 macOS / Linux。
