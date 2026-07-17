# GUI / 可视代码:机器 gate 压在「渲染无关的纯逻辑」,画面交人工

做带 GUI / 3D 视口 / 图表 / 任何「输出是画面」的工具时,机器测试很难覆盖「画面对不对」。
本条给一套 discipline:**把渲染无关的逻辑抽成纯函数、机器 gate 压在纯函数上(独立 oracle),
渲染层只做『能构建 + 渲一帧非空』冒烟,画面正确性交人工**。另附一条常踩的框架 hidden contract
(离屏 GL 段错误)。框架无关(Qt/pyqtgraph、matplotlib、web canvas、游戏引擎视口皆适用)。

## 核心规则

1. **切开「渲染无关逻辑」与「渲染本身」**。渲染无关的部分——数据变换(pose → 绘制数组)、状态机
   (播放/帧游标、开关)、marshalling(UI 配置 → 底层调用)、几何计算——**抽成纯函数/纯类,不碰 widget/GL**,
   用**独立 oracle** 机器 gate:
   - 跨实现交叉校验(新绘制数组 reshape 后 == 旧实现的几何)、
   - round-trip(存/载、编码/解码逆运算)、
   - 不变量(计数、拓扑、bit-identical 确定性)、
   - mutation(扰动必让测试变红,证明 gate 有牙)。
2. **渲染层只做冒烟**:「能构建 widget + 渲一帧、像素非空(std > 阈值)、不崩、不挂(硬超时)」。**不**把
   「画面视觉正确」塞进机器 gate。
3. **画面视觉正确 = 人工**:每个里程碑列**启动命令 + 观察点(TC)**;agent 可以**读一张渲出的 PNG 自检**
   (Read 图片)一次作 sanity,但**不替代**用户交互式眼校(动画跟随 / 手感 / 颜色 / 比例)。
4. **纯函数层要能在无 GUI 环境跑**(无 QApplication / 无 display):这样 CI / headless 也能 gate 逻辑。渲染冒烟
   可能只在有桌面会话的开发机跑得了(见下),那就让它当**best-effort 冒烟**,真牙在纯函数。

## Hidden contract:离屏渲染常常不可靠(以 Qt/pyqtgraph GL 为例)

想当然地「设 offscreen 平台就能无头渲染截图」经常翻车:

- **Qt `QT_QPA_PLATFORM=offscreen` 无 GL context** → `pyqtgraph.opengl` 的 `GLViewWidget` 一构建/渲染就
  **段错误(exit 139)**;`renderToArray` 同样段错误。软件 GL(`QT_OPENGL=software`)也救不了。
- **默认平台(开发机有桌面会话)下,`grabFramebuffer()` 不 `show()` 也能出非空帧**(拿到真 GL context)。
  → GL 冒烟**走默认平台、不设 offscreen、不 show、grabFramebuffer 断言像素非空**;这在有桌面的机器可跑,
  真 headless(无桌面会话)会失败 —— 所以**别把它当硬 gate**,机器 gate 的牙留在纯函数。
- 通用教训:**先 spike 探测「目标环境到底能不能渲/怎么截图」**,再决定冒烟怎么写;别假设离屏可用。不同栈
  (EGL/OSMesa、headless Chromium、引擎 nullrhi)各有各的坑。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 逻辑和 widget/GL 缠在一起,只能靠肉眼验 | 无机器 gate,回归靠人 | 抽渲染无关纯函数,gate 它 |
| 把「画面对」写进机器断言(像素比对/截图 diff) | 脆、跨机不稳、误报 | 纯函数 gate + 人工看画面 |
| 冒烟只断言「没崩」 | 空白画面也过(no teeth) | 断言像素 std > 阈值(非空)+ 独立 oracle |
| 假设 offscreen 平台能渲 GL | 段错误 exit 139,CI 神秘挂 | spike 探测;默认平台 + 不 show grabFramebuffer;牙留纯函数 |
| agent 渲图不看就说「做好了」 | 画面其实错也不知道 | Read 渲出的 PNG 自检一次(仍需人工交互验) |
| 纯函数测试里建了 QApplication/GL | headless/CI 跑不了、变慢 | 纯函数不依赖 Qt/GL,延迟 import widget |

## 跟其它条目的关系

- [`guidelines/code/validation.md`](validation.md) —— 「看代码 ≠ 验证」「对抗式:选可信 check」。本条是其在
  **GUI/可视**场景的落地:可信 check 只能建在渲染无关层。
- [`techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md) —— 「选可信 check:四要素 +
  oracle 判据」。本条抽的纯函数正是为了能上 round-trip / 交叉实现 / 不变量这类独立 oracle。
- [`guidelines/code/function-clarity.md`](function-clarity.md) —— 抽纯函数同时改善可读性/可测性。

## 项目实例参考

RetargetStudy 的 GUI 测试工具(PySide6 + pyqtgraph.opengl 视口,消费一个 pybind 的 C++ retarget 库):
- 每个功能都切成**纯函数 + 渲染层**:`pose → GL 绘制数组` / 播放状态机 / 骨骼树模型 / characterize·映射
  marshalling / rig 配置存载 —— 全部**无 QApplication 可单测**;跟另一份(旧 matplotlib)几何**交叉校验**、
  存载 round-trip、真实数据 bit-identical 确定性、mutation 变红。GLViewWidget 只「构建 + grabFramebuffer 非空」冒烟。
- **离屏 GL 段错误**:初版想 `QT_QPA_PLATFORM=offscreen` 截图 → GLViewWidget 段错误(exit 139);spike 逐步定位到
  `renderToArray` 也崩、而**默认平台下不 show 的 `grabFramebuffer()` 出非空帧**。据此定：冒烟走默认平台、
  牙压纯函数。全程 80+ pytest 全绿 + 人工 `--view` 眼校 + agent 读渲出 PNG 自检。
