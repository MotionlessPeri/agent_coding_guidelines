export const meta = {
  name: 'radar-lite',
  description: 'Lightweight radar scan — fan-out web searches + fetch/extract claims, NO adversarial verify, NO synthesize. Produces unverified candidates for manual triage. ~1/4 the token cost of full deep-research.',
  whenToUse: 'Invoked by the research-radar skill for routine external-knowledge scanning. The radar is an inbox, not a corpus — adversarial verification is deferred to the manual promotion step (see _radar/README.md), so this workflow deliberately skips it. Pass the niche query as args.',
  phases: [
    { title: 'Scope', detail: 'Decompose query (from args) into 5 search angles' },
    { title: 'Search', detail: '5 parallel WebSearch agents, one per angle' },
    { title: 'Fetch', detail: 'URL-dedup, fetch top 15 sources, extract falsifiable claims' },
  ],
}

// radar-lite: Scope → pipeline(Search → URL-dedup → Fetch+Extract). STOP.
// Trimmed from the deep-research workflow: the 3-vote Verify phase (25 claims × 3 = 75 agents,
// the token bulk) and the Synthesize phase are removed. Candidates come back UNVERIFIED by design —
// the radar is an inbox; adversarial verification is deferred to the manual promotion step.
// Query is passed via Workflow({scriptPath: '.../radar-lite.js', args: '<query>'}).

const MAX_FETCH = 15
const MAX_CANDIDATES = 40

// ─── Schemas ───
const SCOPE_SCHEMA = {
  type: "object", required: ["question", "angles", "summary"],
  properties: {
    question: { type: "string" },
    summary: { type: "string" },
    angles: { type: "array", minItems: 3, maxItems: 6, items: {
      type: "object", required: ["label", "query"],
      properties: {
        label: { type: "string" },
        query: { type: "string" },
        rationale: { type: "string" },
      },
    }},
  },
}
const SEARCH_SCHEMA = {
  type: "object", required: ["results"],
  properties: {
    results: { type: "array", maxItems: 6, items: {
      type: "object", required: ["url", "title", "relevance"],
      properties: {
        url: { type: "string" },
        title: { type: "string" },
        snippet: { type: "string" },
        relevance: { enum: ["high", "medium", "low"] },
      },
    }},
  },
}
const EXTRACT_SCHEMA = {
  type: "object", required: ["claims", "sourceQuality"],
  properties: {
    sourceQuality: { enum: ["primary", "secondary", "blog", "forum", "unreliable"] },
    publishDate: { type: "string" },
    claims: { type: "array", maxItems: 5, items: {
      type: "object", required: ["claim", "quote", "importance"],
      properties: {
        claim: { type: "string" },
        quote: { type: "string" },
        importance: { enum: ["central", "supporting", "tangential"] },
      },
    }},
  },
}

// ─── Phase 0: Scope — decompose query into search angles ───
phase("Scope")
const QUESTION = (typeof args === "string" && args.trim()) || ""
if (!QUESTION) {
  return { error: "No query provided. Pass it as args: Workflow({scriptPath: '.../radar-lite.js', args: '<query>'})." }
}
const scope = await agent(
  "Decompose this research query into complementary search angles.\n\n" +
  "## Query\n" + QUESTION + "\n\n" +
  "## Task\n" +
  "Generate 5 distinct web search queries that together cover the query from different angles. Pick angles that suit the domain. Examples:\n" +
  "- broad/primary  · academic/technical  · recent news  · contrarian/skeptical  · practitioner/implementation\n" +
  "- For tech: state-of-art · benchmarks · limitations · industry adoption · cost/tradeoffs\n\n" +
  "Make queries specific enough to surface high-signal results. Avoid redundancy.\n" +
  "Return: the query (verbatim or lightly normalized), a 1-2 sentence decomposition strategy, and the angles.\n\nStructured output only.",
  { label: "scope", schema: SCOPE_SCHEMA }
)
if (!scope) {
  return { error: "Scope agent returned no result — cannot decompose the query." }
}
log("Q: " + QUESTION.slice(0, 80) + (QUESTION.length > 80 ? "…" : ""))
log("Decomposed into " + scope.angles.length + " angles: " + scope.angles.map(a => a.label).join(", "))

// ─── Dedup state — accumulates across searchers as they complete ───
const normURL = u => {
  try {
    const p = new URL(u)
    return (p.hostname.replace(/^www\./, "") + p.pathname.replace(/\/$/, "")).toLowerCase()
  } catch { return u.toLowerCase() }
}
const seen = new Map()
const dupes = []
const budgetDropped = []
const relRank = { high: 0, medium: 1, low: 2 }
let fetchSlots = MAX_FETCH

// ─── Prompts ───
const SEARCH_PROMPT = (angle) =>
  "## Web Searcher: " + angle.label + "\n\n" +
  "Research query: \"" + QUESTION + "\"\n\n" +
  "Your angle: **" + angle.label + "** — " + (angle.rationale || "") + "\n" +
  "Search query: `" + angle.query + "`\n\n" +
  "## Task\nUse WebSearch with the query above (or a refined version). Return the top 4-6 most relevant results.\n" +
  "Rank by relevance to the ORIGINAL query, not just the search query. Skip obvious SEO spam/content farms.\n" +
  "Include a short snippet capturing why each result is relevant.\n\nStructured output only."

const FETCH_PROMPT = (source, angle) =>
  "## Source Extractor\n\n" +
  "Research query: \"" + QUESTION + "\"\n\n" +
  "Fetch and extract key claims from this source:\n" +
  "**URL:** " + source.url + "\n**Title:** " + source.title + "\n**Found via:** " + angle + " search\n\n" +
  "## Task\n1. Use WebFetch to retrieve the page content.\n" +
  "2. Assess source quality: primary research/institution? secondary reporting? blog/opinion? forum? unreliable?\n" +
  "3. Extract 2-5 FALSIFIABLE claims that bear on the query. Each claim must:\n" +
  "   - be a concrete, checkable statement (not vague generalities)\n" +
  "   - include a direct quote from the source as support\n" +
  "   - be rated central/supporting/tangential to the query\n" +
  "4. Note publish date if available.\n\n" +
  "If the fetch fails or the page is irrelevant/paywalled, return claims: [] and sourceQuality: \"unreliable\".\n\nStructured output only."

// ─── Pipeline: search → dedup → fetch+extract (no barrier) ───
const searchResults = await pipeline(
  scope.angles,

  angle => agent(SEARCH_PROMPT(angle), {
    label: "search:" + angle.label, phase: "Search", schema: SEARCH_SCHEMA
  }).then(r => {
    if (!r) return null
    log(angle.label + ": " + r.results.length + " results")
    return { angle: angle.label, results: r.results }
  }),

  searchResult => {
    const sorted = [...searchResult.results].sort((a, b) => relRank[a.relevance] - relRank[b.relevance])
    const novel = sorted.filter(r => {
      const key = normURL(r.url)
      if (seen.has(key)) {
        dupes.push({ ...r, angle: searchResult.angle, dupOf: seen.get(key) })
        return false
      }
      if (fetchSlots <= 0 && relRank[r.relevance] >= 1) {
        budgetDropped.push({ ...r, angle: searchResult.angle })
        return false
      }
      seen.set(key, { angle: searchResult.angle, title: r.title })
      fetchSlots--
      return true
    })
    if (novel.length < searchResult.results.length) {
      log(searchResult.angle + ": " + novel.length + " novel (" + (searchResult.results.length - novel.length) + " filtered)")
    }
    return parallel(
      novel.map(source => () => {
        let host = "unknown"
        try { host = new URL(source.url).hostname.replace(/^www\./, "") } catch {}
        return agent(FETCH_PROMPT(source, searchResult.angle), {
          label: "fetch:" + host,
          phase: "Fetch",
          schema: EXTRACT_SCHEMA,
        }).then(ext => {
          if (!ext) return null
          return {
            url: source.url, title: source.title, angle: searchResult.angle,
            sourceQuality: ext.sourceQuality, publishDate: ext.publishDate,
            claims: ext.claims.map(c => ({ ...c, sourceUrl: source.url, sourceQuality: ext.sourceQuality, publishDate: ext.publishDate, angle: searchResult.angle })),
          }
        }).catch(e => {
          log("fetch failed: " + source.url + " — " + (e.message || e))
          return { url: source.url, title: source.title, angle: searchResult.angle, sourceQuality: "unreliable", claims: [] }
        })
      })
    )
  }
)

const allSources = searchResults.flat().filter(Boolean)
const allClaims = allSources.flatMap(s => s.claims)
const impRank = { central: 0, supporting: 1, tangential: 2 }
const qualRank = { primary: 0, secondary: 1, blog: 2, forum: 3, unreliable: 4 }

const candidates = [...allClaims]
  .sort((a, b) => (impRank[a.importance] - impRank[b.importance]) || (qualRank[a.sourceQuality] - qualRank[b.sourceQuality]))
  .slice(0, MAX_CANDIDATES)

log("Fetched " + allSources.length + " sources → " + allClaims.length + " claims (returning top " + candidates.length + " UNVERIFIED candidates; verify deferred to promotion)")

// ─── Return raw candidates. NO verify, NO synthesize — that's the point. ───
return {
  question: QUESTION,
  mode: "radar-lite (unverified — no adversarial verify, no synthesize by design)",
  summary: "Lightweight scan: " + allSources.length + " sources fetched, " + allClaims.length + " claims extracted, top " + candidates.length + " returned. Candidates are UNVERIFIED — vet sources manually before promoting anything into guidelines/ (see _radar/README.md).",
  candidates: candidates.map(c => ({
    claim: c.claim,
    quote: c.quote,
    importance: c.importance,
    sourceUrl: c.sourceUrl,
    sourceQuality: c.sourceQuality,
    publishDate: c.publishDate,
    angle: c.angle,
  })),
  sources: allSources.map(s => ({ url: s.url, title: s.title, quality: s.sourceQuality, angle: s.angle, claimCount: s.claims.length })),
  dropped: {
    urlDupes: dupes.length,
    budgetDropped: budgetDropped.map(d => ({ url: d.url, title: d.title, angle: d.angle })),
  },
  stats: {
    angles: scope.angles.length,
    sources: allSources.length,
    claims: allClaims.length,
    candidates: candidates.length,
    agentCalls: 1 + scope.angles.length + allSources.length,
  },
}
