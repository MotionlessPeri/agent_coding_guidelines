export const meta = {
  name: 'schema-probe',
  description: 'Probe whether StructuredOutput fails by payload size under a worker capability profile',
  phases: [
    { title: 'Small', detail: 'one schema agent, tiny payload' },
    { title: 'Large', detail: 'one schema agent, ~3KB payload (same shape as deep-research SCOPE_SCHEMA)' },
  ],
}

// 一次性诊断脚本。问题：worker 里 deep-research 的 Scope agent 五次 StructuredOutput 全被权限层拒
// （载荷完整、三个必填字段齐全、各 3157 字节）。而 main lane 的最小 schema agent 测试是通过的。
// 差别只剩 profile 档位与载荷大小。本探针在同一 profile 下先小后大，单变量分离这两者。
// 小的过、大的不过 → 大小阈值；两个都不过 → 跟大小无关，是 profile / is_subagent 那条线。

const SMALL_SCHEMA = {
  type: 'object', required: ['ok'], additionalProperties: false,
  properties: { ok: { type: 'string' } },
}

const LARGE_SCHEMA = {
  type: 'object', required: ['question', 'angles', 'summary'], additionalProperties: false,
  properties: {
    question: { type: 'string' },
    summary: { type: 'string' },
    angles: {
      type: 'array', minItems: 5, maxItems: 5,
      items: {
        type: 'object', required: ['label', 'query', 'rationale'], additionalProperties: false,
        properties: {
          label: { type: 'string' },
          query: { type: 'string' },
          rationale: { type: 'string' },
        },
      },
    },
  },
}

phase('Small')
let smallOk = false
try {
  const small = await agent('Return exactly ok="yes". Structured output only.', {
    label: 'small', schema: SMALL_SCHEMA,
  })
  smallOk = !!small
  log('SMALL result: ' + JSON.stringify(small))
} catch (e) {
  log('SMALL threw: ' + (e && e.message ? e.message : String(e)))
}

phase('Large')
let largeOk = false
try {
  const large = await agent(
    'Decompose this into exactly 5 search angles: "agent best practices radar for a cross-project agent guidelines corpus". ' +
    'Each angle needs label, query, and a rationale of at least 200 characters. Also return the question verbatim and a 2-sentence summary. ' +
    'Structured output only.',
    { label: 'large', schema: LARGE_SCHEMA },
  )
  largeOk = !!large
  log('LARGE ok: ' + largeOk + ' | angles: ' + (large && large.angles ? large.angles.length : 'n/a'))
} catch (e) {
  log('LARGE threw: ' + (e && e.message ? e.message : String(e)))
}

return { smallOk, largeOk, verdict: smallOk && !largeOk ? 'size-dependent' : (!smallOk ? 'schema-agents-fail-outright' : 'both-passed') }
