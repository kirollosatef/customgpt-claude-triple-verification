# Cycle 4 — Research Claim Verification

<span class="badge badge-cycle4">PreToolUse + Stop</span> <span class="badge badge-block">Blocks on violation</span>

Cycle 4 runs on **Write** and **Edit** of research `.md` files, and also scans research directories at session end via the **Stop** hook. It ensures all research claims are verified and properly sourced.

## Why This Matters

AI can confidently generate statistics, citations, and claims that sound authoritative but are fabricated. Cycle 4 enforces a verification workflow: every claim must be checked via Perplexity MCP tools and include a source URL.

## What Counts as a Research File

A file is treated as "research" if it meets **both** criteria:
- Has a `.md` extension
- Either lives in a `/research/` directory OR has "research" in its filename

Examples of research files:
- `docs/research/market-analysis.md`
- `research/competitor-review.md`
- `ai-research-report.md`

## Rules

### `no-vague-claims` — Block vague unsourced language

Scans for 14 vague phrases that indicate unsourced claims:

> "studies show", "research indicates", "experts say", "according to research", "data suggests", "it is known that", "generally accepted", "industry reports", "recent surveys", "analysts estimate", "sources suggest", "widely reported", "it has been shown", "evidence suggests"

**Blocked:**
```markdown
Studies show that AI adoption is accelerating across industries.
Experts say that most enterprises will deploy AI by 2025.
```

**Allowed:**
```markdown
According to the McKinsey 2023 Annual Report, AI adoption grew by 25% year-over-year.
The Stanford HAI 2023 Index measured a 35% increase in enterprise AI deployments.
```

---

### `no-unverified-claims` — Block claims without verification tag

Any research file containing statistical or factual claims must include a `<!-- PERPLEXITY_VERIFIED -->` HTML comment tag. This tag proves all claims were checked using Perplexity MCP tools.

**Blocked:**
```markdown
# Market Report
The AI market grew by 35% in 2023 and reached $150 billion.
```

**Allowed:**
```markdown
<!-- PERPLEXITY_VERIFIED -->

# Market Report
The AI market grew by 35% in 2023 according to [IDC](https://www.idc.com/report).
```

---

### `no-unsourced-claims` — Block claims lacking a source URL

Even with the `<!-- PERPLEXITY_VERIFIED -->` tag, each claim must have a source URL within 300 characters. Valid sources include:
- Markdown links: `[text](url)`
- Bare URLs: `https://...`
- Source markers: `[Source:]`, `[Ref:]`, `[Verified:]`

**Blocked:**
```markdown
<!-- PERPLEXITY_VERIFIED -->

The AI market grew by 35% in 2023.

(... 300+ characters of text without any source link ...)
```

**Allowed:**
```markdown
<!-- PERPLEXITY_VERIFIED -->

The AI market grew by 35% in 2023 [Source: https://www.idc.com/ai-spending-guide].
Revenue reached $150.2 billion per the [IDC Worldwide AI Spending Guide](https://www.idc.com/promo/ai-spending-guide).
```

## Verification Workflow

The recommended workflow for writing research documents:

1. **Draft your claims** — Write the content with placeholder claims
2. **Verify with Perplexity** — Use `mcp__perplexity__perplexity_search` or `mcp__perplexity__perplexity_research` to verify each claim
3. **Add source URLs** — Include links from the verification results near each claim
4. **Add the verification tag** — Place `<!-- PERPLEXITY_VERIFIED -->` at the top of the file
5. **Write the file** — The plugin will verify that all claims have nearby sources

## Stop Gate (Session End Scan)

In addition to checking individual Write/Edit operations, Cycle 4 runs a **session-end scan** via the Stop hook. This scan looks for research `.md` files in:
- `docs/research/`
- `research/`
- `docs/`

Any files found that contain unverified claims will trigger a block, giving Claude a chance to fix them before the session ends.
