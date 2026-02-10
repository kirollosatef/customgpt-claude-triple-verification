/**
 * Research Verifier — Cycle 4 (Research Claim Verification).
 *
 * Blocks research .md files containing vague claims, unverified statistics,
 * or missing source URLs. Requires a <!-- PERPLEXITY_VERIFIED --> tag proving
 * claims were actually checked via Perplexity MCP tools.
 *
 * Two-pass verification:
 *   Pass 1 — Vague language detection (instant block)
 *   Pass 2 — Claim extraction + URL proximity check
 *
 * Zero dependencies — Node.js built-ins only.
 */

// ─── Pass 1: Vague Language Phrases ──────────────────────────────────────────

const VAGUE_PHRASES = [
  'studies show',
  'research indicates',
  'experts say',
  'according to research',
  'data suggests',
  'it is known that',
  'generally accepted',
  'industry reports',
  'recent surveys',
  'analysts estimate',
  'sources suggest',
  'widely reported',
  'it has been shown',
  'evidence suggests'
];

const VAGUE_PATTERN = new RegExp(
  VAGUE_PHRASES.map(p => p.replace(/\s+/g, '\\s+')).join('|'),
  'i'
);

// ─── Pass 2: Claim Patterns ─────────────────────────────────────────────────

const CLAIM_PATTERNS = [
  /\d+(\.\d+)?\s*%/,                              // percentages: "45%", "3.5%"
  /\d+(\.\d+)?x\b/,                               // multipliers: "10x", "2.5x"
  /\d+-fold\b/i,                                   // n-fold: "3-fold"
  /\b\d{1,3}(,\d{3})+\b/,                         // quantities: "1,000,000"
  /\$\s*\d+(\.\d+)?\s*(million|billion|trillion|[MBTmbt])\b/i,  // dollar amounts
  /\b(study|survey|report)\s+(by|from|at)\b/i,    // study references
  /\b[A-Z][a-z]+\s+(University|Institute|Lab)\b/, // named studies/institutions
  /\b\d+(\.\d+)?\s*times\s+(more|less|faster|slower|higher|lower|greater|better|worse)\b/i, // comparative claims
  /\b(in|since|by|from)\s+\d{4}\b/i              // year-specific claims
];

// ─── Source Proximity Check ─────────────────────────────────────────────────

const SOURCE_PATTERNS = [
  /\[.*?\]\(https?:\/\/[^\s)]+\)/,    // markdown link [text](url)
  /https?:\/\/[^\s)>\]]+/,            // bare URL
  /\[(Source|Ref|Verified):?[^\]]*\]/i  // [Source: ...], [Ref: ...], [Verified: ...] marker
];

const VERIFICATION_TAG = '<!-- PERPLEXITY_VERIFIED -->';
const SOURCE_PROXIMITY = 300; // characters

// ─── Rule Definitions ───────────────────────────────────────────────────────

const CYCLE4_RULES = [
  {
    id: 'no-vague-claims',
    description: 'Block vague unsourced language like "studies show", "experts say"',
    appliesTo: 'research-md',
    message: 'Research file contains vague language (e.g. "studies show", "experts say"). Replace with specific, sourced claims: name the study, author, institution, and year, then link the source.'
  },
  {
    id: 'no-unverified-claims',
    description: 'Block statistical/factual claims without PERPLEXITY_VERIFIED tag',
    appliesTo: 'research-md',
    message: 'Research file contains statistical or factual claims but is missing the <!-- PERPLEXITY_VERIFIED --> tag. Verify all claims using Perplexity MCP tools and add the tag to confirm verification.'
  },
  {
    id: 'no-unsourced-claims',
    description: 'Block claims that lack a nearby source URL (within 300 chars)',
    appliesTo: 'research-md',
    message: 'Research file has the PERPLEXITY_VERIFIED tag but some claims lack a source URL within 300 characters. Add a markdown link, bare URL, or [Source:]/[Ref:]/[Verified:] marker near each claim.'
  }
];

// ─── Public API ─────────────────────────────────────────────────────────────

/**
 * Run Cycle 4 (Research Claim Verification) against content.
 *
 * @param {string} content - The markdown content to verify
 * @param {string} filePath - The file path (for context in messages)
 * @param {object} config - Configuration with disabledRules array
 * @returns {Array<{ruleId: string, cycle: number, message: string}>}
 */
export function runCycle4(content, filePath = '', config = {}) {
  const disabledRules = (config && config.disabledRules) || [];
  const violations = [];

  if (!content || typeof content !== 'string') return violations;

  // Pass 1 — Vague Language Detection
  if (!disabledRules.includes('no-vague-claims')) {
    const match = VAGUE_PATTERN.exec(content);
    if (match) {
      violations.push({
        ruleId: 'no-vague-claims',
        cycle: 4,
        message: `${CYCLE4_RULES[0].message}\n\nFound: "${match[0]}"`
      });
      // Instant block — skip Pass 2
      return violations;
    }
  }

  // Pass 2 — Claim Extraction + URL Proximity
  const claims = extractClaims(content);
  if (claims.length === 0) return violations;

  // Check for PERPLEXITY_VERIFIED tag
  const hasVerificationTag = content.includes(VERIFICATION_TAG);

  if (!hasVerificationTag && !disabledRules.includes('no-unverified-claims')) {
    violations.push({
      ruleId: 'no-unverified-claims',
      cycle: 4,
      message: `${CYCLE4_RULES[1].message}\n\nFound ${claims.length} claim(s) without verification tag.`
    });
    return violations;
  }

  // Tag present — check source proximity for each claim
  if (hasVerificationTag && !disabledRules.includes('no-unsourced-claims')) {
    const unsourced = claims.filter(claim => !hasNearbySource(content, claim.index));
    if (unsourced.length > 0) {
      violations.push({
        ruleId: 'no-unsourced-claims',
        cycle: 4,
        message: `${CYCLE4_RULES[2].message}\n\nFound ${unsourced.length} unsourced claim(s).`
      });
    }
  }

  return violations;
}

/**
 * Get all Cycle 4 rule definitions for documentation/testing.
 */
export function getAllCycle4Rules() {
  return CYCLE4_RULES.map(r => ({ ...r }));
}

// ─── Internal Helpers ───────────────────────────────────────────────────────

/**
 * Extract all statistical/factual claims from content with their positions.
 */
function extractClaims(content) {
  const claims = [];
  const seen = new Set();

  for (const pattern of CLAIM_PATTERNS) {
    const globalPattern = new RegExp(pattern.source, pattern.flags.includes('i') ? 'gi' : 'g');
    let match;
    while ((match = globalPattern.exec(content)) !== null) {
      // Deduplicate overlapping matches
      const key = `${match.index}:${match[0]}`;
      if (!seen.has(key)) {
        seen.add(key);
        claims.push({
          text: match[0],
          index: match.index
        });
      }
    }
  }

  return claims;
}

/**
 * Check if there's a source (URL, markdown link, or marker) within SOURCE_PROXIMITY chars of a claim.
 */
function hasNearbySource(content, claimIndex) {
  // Check a window around the claim position
  const start = Math.max(0, claimIndex - SOURCE_PROXIMITY);
  const end = Math.min(content.length, claimIndex + SOURCE_PROXIMITY);
  const window = content.slice(start, end);

  return SOURCE_PATTERNS.some(p => p.test(window));
}
