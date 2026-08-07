export const meta = {
  name: 'radar-textmode',
  description: 'Full-scope radar (Scope/Search/Fetch/Verify/Synthesize) with NO agent schemas — every agent returns plain text JSON, parsed in JS. Works around runtimes whose tool-call parameter path cannot carry a large StructuredOutput payload.',
  whenToUse: 'When the runtime cannot run schema-bound workflow agents (large StructuredOutput payloads get cancelled) but you still want the full fan-out with adversarial verification.',
  phases: [
    { title: 'Scope', detail: '拆 5 个搜索角度' },
    { title: 'Search', detail: '5 路并行搜索' },
    { title: 'Fetch', detail: 'URL 去重后抓源、提取可证伪 claim' },
    { title: 'Verify', detail: '每条 claim 3 票对抗核验' },
    { title: 'Synthesize', detail: '合并去重、按置信度排序、附引用' },
  ],
}

// 为什么不用 schema：这个 worker 运行时的工具调用参数通道扛不住大载荷——12 字节的
// StructuredOutput 能过，5~6 KB 的被取消（两次实测，见 _radar 记录）。而 agent 的
// **最终文本**不走那条通道，所以改成「让 agent 返回 JSON 文本，在 JS 里解析」。
// 换焦点改 QUESTION 常量即可（本运行时也传不了字符串 args，所以不走 args）。

const QUESTION = 'Agent 最佳实践雷达（2026-02 至 2026-08，越近越优先）：Claude Code 生态的成型方法论——hooks / skills / subagents / plugins / MCP / settings / permission modes 的 hidden contract 与可操作规则；AGENTS.md 与 context engineering 的具体做法；multi-agent 编排（coordinator-worker、agent 间通信、失败处理、成本质量权衡）；agent 输出的评测与验证 discipline。只要能落成可操作规则或工具的东西，不要鸡汤、不要 listicle、不要 thought leadership。'

const ALREADY_COVERED = 'commit 规范、TDD 红绿、单一职责、AGENTS.md 基本用法、先读文档再改代码、spec-driven development、context rot、UI 截图验证、Lilian Weng context 综述、subagent contracts、negation blindness、tool design principles、context budget、de-anchored judge'
const ALREADY_CAPTURED = 'Stop hook 连续阻断 8 次后被 override、claude.com/blog 的动态 workflow 命名模式、Agent Teams、auto mode classifier 对 subagent 的三阶段检查、plugin 系统打包与分发'

const MAX_FETCH = 15
const MAX_VERIFY = 10
const VOTES = 3

// ── 纯文本 JSON：剥围栏 / 取第一个完整 JSON 值 ──
function parseLoose(text) {
  if (typeof text !== 'string') return null
  let s = text.trim()
  const fence = s.match(/```(?:json)?\s*([\s\S]*?)```/)
  if (fence) s = fence[1].trim()
  const start = s.search(/[[{]/)
  if (start < 0) return null
  const open = s[start]
  const close = open === '{' ? '}' : ']'
  let depth = 0, inStr = false, esc = false
  for (let i = start; i < s.length; i++) {
    const c = s[i]
    if (esc) { esc = false; continue }
    if (c === '\\') { esc = true; continue }
    if (c === '"') { inStr = !inStr; continue }
    if (inStr) continue
    if (c === open) depth++
    else if (c === close) { depth--; if (depth === 0) { try { return JSON.parse(s.slice(start, i + 1)) } catch { return null } } }
  }
  return null
}

// 一次重试：第一次没给出可解析的 JSON 就把原样回显给它、要求只输出 JSON
async function jsonAgent(prompt, opts) {
  const first = await agent(prompt + '\n\n只输出 JSON，不要任何前后说明、不要 markdown 围栏。', opts)
  const parsed = parseLoose(first)
  if (parsed) return parsed
  const retry = await agent(
    '你上一次的回复无法被解析成 JSON。原样重发一次，这次**只输出 JSON 本体**，第一个字符必须是 { 或 [。\n\n' +
    '原任务：\n' + prompt + '\n\n你上次的回复（截断）：\n' + String(first || '').slice(0, 800),
    { ...opts, label: (opts.label || 'agent') + ':retry' },
  )
  return parseLoose(retry)
}

// ── Scope ──
phase('Scope')
const scope = await jsonAgent(
  '把下面这个调研问题拆成 5 个互补的搜索角度。\n\n## 问题\n' + QUESTION +
  '\n\n## 已充分覆盖（搜索时主动排除）\n' + ALREADY_COVERED +
  '\n\n## 今天已捕获（不要重复）\n' + ALREADY_CAPTURED +
  '\n\n返回形如：{"angles":[{"label":"...","query":"...","rationale":"..."}]}，恰好 5 个。' +
  'query 要具体到能搜出高信号结果，别互相重复。',
  { label: 'scope', phase: 'Scope' },
)
if (!scope || !Array.isArray(scope.angles) || !scope.angles.length) {
  return { error: 'Scope 阶段没拿到可解析的角度列表', raw: scope }
}
log('拆出 ' + scope.angles.length + ' 个角度：' + scope.angles.map(a => a.label).join(' / '))

// ── URL 去重状态 ──
const normURL = u => { try { const p = new URL(u); return (p.hostname.replace(/^www\./, '') + p.pathname.replace(/\/$/, '')).toLowerCase() } catch { return String(u).toLowerCase() } }
const seen = new Map()
let slots = MAX_FETCH
let dropped = 0

// ── Search → Fetch（pipeline，无 barrier）──
const fetched = await pipeline(
  scope.angles,

  angle => jsonAgent(
    '## 搜索角度：' + angle.label + '\n\n调研问题：' + QUESTION + '\n\n' +
    '用 WebSearch 搜 `' + (angle.query || angle.label) + '`（可自行优化措辞）。返回最相关的 4-6 条。\n' +
    '按对**原问题**的相关度排序，不是对搜索词。跳过 SEO 垃圾和内容农场。\n\n' +
    '返回形如：{"results":[{"url":"...","title":"...","snippet":"为什么相关","relevance":"high|medium|low"}]}',
    { label: 'search:' + angle.label, phase: 'Search' },
  ).then(r => (r && Array.isArray(r.results)) ? { angle: angle.label, results: r.results } : null),

  sr => {
    if (!sr) return []
    const rank = { high: 0, medium: 1, low: 2 }
    const novel = [...sr.results].sort((a, b) => (rank[a.relevance] ?? 1) - (rank[b.relevance] ?? 1)).filter(r => {
      const k = normURL(r.url)
      if (seen.has(k)) { dropped++; return false }
      if (slots <= 0) { dropped++; return false }
      seen.set(k, true); slots--; return true
    })
    return parallel(novel.map(src => () => jsonAgent(
      '## 抓源提取\n\n调研问题：' + QUESTION + '\n\n' +
      '用 WebFetch 抓 ' + src.url + '（标题：' + src.title + '），然后：\n' +
      '1. 判断源质量：primary（一手/官方）/ secondary / blog / forum / unreliable\n' +
      '2. 提取 2-5 条**可证伪**的 claim，每条必须配来自该页的**逐字**引语\n' +
      '3. 标注 central / supporting / tangential\n' +
      '抓取失败或页面无关就返回 {"claims":[],"sourceQuality":"unreliable"}。**绝不编造引语或 URL。**\n\n' +
      '返回形如：{"sourceQuality":"...","publishDate":"...","claims":[{"claim":"...","quote":"...","importance":"central"}]}',
      { label: 'fetch:' + (() => { try { return new URL(src.url).hostname.replace(/^www\./, '') } catch { return 'src' } })(), phase: 'Fetch' },
    ).then(ext => (ext && Array.isArray(ext.claims)) ? {
      url: src.url, title: src.title, angle: sr.angle, sourceQuality: ext.sourceQuality, publishDate: ext.publishDate,
      claims: ext.claims.map(c => ({ ...c, sourceUrl: src.url, sourceQuality: ext.sourceQuality, publishDate: ext.publishDate })),
    } : null)))
  },
)

const sources = fetched.flat().filter(Boolean)
const claims = sources.flatMap(s => s.claims || [])
log('抓了 ' + sources.length + ' 个源，提取 ' + claims.length + ' 条 claim（去重/超额丢弃 ' + dropped + '）')
if (!claims.length) return { error: '没有提取到任何 claim', sources: sources.length, dropped }

// ── Verify：每条 claim 3 票对抗核验 ──
const impRank = { central: 0, supporting: 1, tangential: 2 }
const toVerify = [...claims].sort((a, b) => (impRank[a.importance] ?? 1) - (impRank[b.importance] ?? 1)).slice(0, MAX_VERIFY)
log('送 ' + toVerify.length + ' 条 claim 进对抗核验（每条 ' + VOTES + ' 票）')

phase('Verify')
const verdicts = await parallel(toVerify.map((c, i) => () =>
  parallel(Array.from({ length: VOTES }, (_, v) => () => jsonAgent(
    '## 对抗核验（第 ' + (v + 1) + ' 票）\n\n**尽力驳倒**下面这条 claim。拿不准就判 refuted=true。\n\n' +
    'claim：' + c.claim + '\n引语：' + c.quote + '\n来源：' + c.sourceUrl + '\n\n' +
    '用 WebFetch 打开来源核对：这条引语是否**逐字**出现在该页？claim 是否被它支持？页面是否真实存在？\n' +
    '重点抓：编造的引语、URL 打不开、claim 超出引语能支撑的范围、把博客观点说成官方规格。\n\n' +
    '返回形如：{"refuted":true|false,"reason":"一句话","quoteVerbatim":true|false}',
    { label: 'verify:' + i + ':' + v, phase: 'Verify' },
  ))).then(vs => {
    const ok = vs.filter(Boolean)
    const refutes = ok.filter(v => v.refuted).length
    return { ...c, votes: ok.length, refutes, survived: ok.length > 0 && refutes < Math.ceil(ok.length / 2) }
  })))

const survived = verdicts.filter(Boolean).filter(v => v.survived)
const killed = verdicts.filter(Boolean).filter(v => !v.survived)
log('核验：' + survived.length + ' 条存活 / ' + killed.length + ' 条被驳倒')

// ── Synthesize ──
phase('Synthesize')
const synth = await jsonAgent(
  '## 综合成雷达候选\n\n调研问题：' + QUESTION + '\n\n' +
  '## 已充分覆盖（必须排除）\n' + ALREADY_COVERED + '\n\n## 今天已捕获（不要重复推）\n' + ALREADY_CAPTURED + '\n\n' +
  '## 通过对抗核验的 claim\n' + JSON.stringify(survived.map(s => ({ claim: s.claim, quote: s.quote, url: s.sourceUrl, quality: s.sourceQuality, refutes: s.refutes + '/' + s.votes })), null, 1).slice(0, 20000) + '\n\n' +
  '把它们合并成 3-6 条雷达候选。语义重复的合并。三问任一为否就砍：是新的吗？能落成可操作规则或工具吗？跟这个 corpus 的 niche 沾边吗？\n' +
  '宁缺毋滥——一条都不合格就返回空数组，别为凑数放水。\n\n' +
  '返回形如：{"candidates":[{"name":"...","what":"一两句","why_relevant":"对到具体 guideline 槽位，不要空话","promotion_bar":"采纳前要先验证什么","novelty":"为什么不属于已覆盖","sources":[{"url":"...","quote":"逐字引语"}],"confidence":"high|medium|low"}],"judgment":"一句话总评"}',
  { label: 'synthesize', phase: 'Synthesize' },
)

return {
  mode: 'radar-textmode（无 agent schema，全部走纯文本 JSON）',
  question: QUESTION,
  candidates: (synth && synth.candidates) || [],
  judgment: (synth && synth.judgment) || '综合阶段没拿到可解析结果',
  verified: survived.map(s => ({ claim: s.claim, url: s.sourceUrl, refutes: s.refutes + '/' + s.votes })),
  killed: killed.map(s => ({ claim: s.claim, url: s.sourceUrl, refutes: s.refutes + '/' + s.votes })),
  stats: {
    angles: scope.angles.length,
    sources_fetched: sources.length,
    claims_extracted: claims.length,
    claims_verified: toVerify.length,
    survived: survived.length,
    killed: killed.length,
    dropped_dupe_or_budget: dropped,
  },
}
