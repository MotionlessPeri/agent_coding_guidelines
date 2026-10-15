---
class: experience
scope: gui-or-rendering-tools
triggers: [GUI, 视口, 画面, 截图, 离屏, offscreen, 像素, 冒烟, 渲染层, Qt, pyqtgraph, ImGui, 画面对不对]
born: "2026-07，写下时的模型未记录"
retested:
  - "2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：V1 pass、V2 pass；见 docs/evaluations/experience-retest-2026-10-15.md"
incidents:
  - 2026-07-offscreen-gl-segfault-in-smoke
  - 2026-07-pure-function-gate-with-gl-smoke-only
  - 2026-07-ui-framework-chosen-by-viewport-texture-path
---

# GUI 与可视代码：机器 gate 压在渲染无关的纯逻辑，画面交人工

做带 GUI、3D 视口、图表这类「输出是画面」的工具时，机器测试很难覆盖「画面对不对」。做法是：把渲染无关的逻辑抽成纯函数，机器 gate 压在纯函数上并用独立 oracle；渲染层只做「能构建加渲一帧非空」的冒烟；画面正确性交人工。框架无关。

## 四条规则

1. **切开渲染无关逻辑与渲染本身。** 数据变换（pose 到绘制数组）、状态机（播放、帧游标、开关）、UI 配置到底层调用的格式转换、几何计算，抽成不碰 widget 和 GL 的纯函数或纯类，用独立 oracle 机器 gate：跨实现交叉校验、round-trip、不变量、mutation 变红。oracle 阶梯见 [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)。
2. **渲染层只做冒烟。** 能构建 widget、渲一帧、像素非空（标准差大于阈值）、不崩、不挂（硬超时）。不把「画面视觉正确」塞进机器 gate，像素比对和截图 diff 脆、跨机不稳、误报。
3. **画面视觉正确等于人工。** 每个里程碑列启动命令加观察点；agent 可以读一张渲出的 PNG 自检一次作 sanity，但不替代用户交互式眼校（动画跟随、手感、颜色、比例）。
4. **纯函数层要能在无 GUI 环境跑。** 无 QApplication、无 display，CI 和 headless 也能 gate 逻辑。渲染冒烟可能只在有桌面会话的开发机跑得了，那就让它当 best-effort，真牙在纯函数。

## 离屏渲染常常不可靠

「设 offscreen 平台就能无头截图」经常翻车：Qt 的 `QT_QPA_PLATFORM=offscreen` 没有 GL context，`pyqtgraph.opengl` 的 `GLViewWidget` 一构建就段错误，`renderToArray` 同样，软件 GL 也救不了；而有桌面会话时走默认平台、不 `show()`、直接 `grabFramebuffer()` 能出非空帧。先 spike 探测目标环境到底能不能渲、怎么截图，再决定冒烟怎么写；不同栈（EGL、OSMesa、headless Chromium、引擎 nullrhi）各有各的坑。

## 实时 GPU 画面工具的 UI 框架选型

主输出是实时 GPU 画面的工具，选 UI 框架的决定性因素是视口怎么拿到渲染结果：选能跟渲染器共享同一 GPU 设备的（如 Dear ImGui 的 `ImTextureID` 直接是渲染器的纹理句柄），免掉每帧跨设备、跨上下文拷贝。集成接缝用 RHI 中立类型，契约面写 `TextureHandle` 不写具体框架类型，换框架时契约不必重谈。

## 反模式

| 反模式 | 修法 |
|---|---|
| 逻辑和 widget 或 GL 缠在一起，只能肉眼验 | 抽渲染无关纯函数，gate 它 |
| 把「画面对」写进机器断言（像素比对、截图 diff） | 纯函数 gate 加人工看画面 |
| 冒烟只断言「没崩」 | 断言像素非空，加独立 oracle |
| 假设 offscreen 平台能渲 GL | spike 探测；默认平台不 show 直接 grabFramebuffer；牙留纯函数 |
| agent 渲图不看就说「做好了」 | 读渲出的 PNG 自检一次，仍需人工交互验 |
| 纯函数测试里建了 QApplication 或 GL | 纯函数不依赖 Qt 和 GL，延迟 import widget |

## 证据

事故记录见本页 frontmatter 的 `incidents`，统计由 `kb.py index` 生成。切法在一个 PySide6 加 pyqtgraph.opengl 的重定向 GUI 工具里完整跑通，80 多个 pytest 全绿加人工眼校；离屏段错误是同项目的一次实测；框架选型那条来自另一个渲染器项目的收尾 harvest。单项目各一次，apply-and-refine。

## 相关

- [`validation.md`](validation.md)：看代码不等于验证；可信 check 只能建在渲染无关层。
- [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)：四要素与 oracle 阶梯。
- [`function-clarity.md`](function-clarity.md)：抽纯函数同时改善可读性与可测性。
