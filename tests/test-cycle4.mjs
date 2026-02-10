import { describe, it } from 'node:test';
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { runCycle4, getAllCycle4Rules } from '../scripts/lib/research-verifier.mjs';
import { isResearchFile } from '../scripts/lib/utils.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const fixturesDir = resolve(__dirname, 'fixtures');

// ─── Pass 1: Vague Language Detection ────────────────────────────────────────

describe('Cycle 4 — Pass 1: Vague Language', () => {
  const vagueExamples = [
    'Studies show that AI is transforming business.',
    'Research indicates a growing trend in cloud adoption.',
    'Experts say this is the future of computing.',
    'According to research, the market is expanding.',
    'Data suggests that revenue will double.',
    'It is known that open source dominates.',
    'This approach is generally accepted in the industry.',
    'Industry reports confirm the trend.',
    'Recent surveys found high satisfaction rates.',
    'Analysts estimate the market will reach $1 trillion.',
    'Sources suggest a shift toward remote work.',
    'The trend has been widely reported across media.',
    'It has been shown that automation reduces costs.',
    'Evidence suggests a correlation between AI use and profit.'
  ];

  for (const text of vagueExamples) {
    it(`blocks: "${text.slice(0, 50)}..."`, () => {
      const violations = runCycle4(text, 'docs/research/report.md');
      assert.equal(violations.length, 1);
      assert.equal(violations[0].ruleId, 'no-vague-claims');
      assert.equal(violations[0].cycle, 4);
    });
  }

  it('allows specific sourced text without vague language', () => {
    const content = 'According to the McKinsey 2023 report, AI adoption grew by 25%.';
    const violations = runCycle4(content, 'docs/research/report.md');
    // This has a claim (25%) but no vague phrase, so pass 1 passes.
    // Pass 2 will trigger because there is no PERPLEXITY_VERIFIED tag.
    assert.ok(!violations.some(v => v.ruleId === 'no-vague-claims'));
  });
});

// ─── Pass 2: Verification Tag Requirement ────────────────────────────────────

describe('Cycle 4 — Pass 2: Verification Tag', () => {
  it('blocks claims without PERPLEXITY_VERIFIED tag', () => {
    const content = 'The AI market grew by 35% in 2023 and reached $150 billion.';
    const violations = runCycle4(content, 'research/market.md');
    assert.equal(violations.length, 1);
    assert.equal(violations[0].ruleId, 'no-unverified-claims');
    assert.equal(violations[0].cycle, 4);
  });

  it('allows claims with PERPLEXITY_VERIFIED tag and nearby sources', () => {
    const content = `<!-- PERPLEXITY_VERIFIED -->

The AI market grew by 35% in 2023 [Source: https://example.com/report].`;
    const violations = runCycle4(content, 'research/market.md');
    assert.equal(violations.length, 0);
  });

  it('blocks when tag present but sources too far from claim', () => {
    // Create content where the source is >300 chars away from the claim
    const padding = 'Lorem ipsum dolor sit amet. '.repeat(15); // ~420 chars
    const content = `<!-- PERPLEXITY_VERIFIED -->

The market grew by 45% in 2023.

${padding}

[Source: https://example.com/report]`;
    const violations = runCycle4(content, 'research/market.md');
    assert.ok(violations.some(v => v.ruleId === 'no-unsourced-claims'));
  });
});

// ─── Pass 2: Source Proximity Check ──────────────────────────────────────────

describe('Cycle 4 — Pass 2: Source Proximity', () => {
  it('accepts markdown links as valid sources', () => {
    const content = `<!-- PERPLEXITY_VERIFIED -->

Revenue grew 45% according to [McKinsey Report](https://mckinsey.com/report).`;
    const violations = runCycle4(content, 'research/revenue.md');
    assert.equal(violations.length, 0);
  });

  it('accepts bare URLs as valid sources', () => {
    const content = `<!-- PERPLEXITY_VERIFIED -->

Revenue grew 45% in 2023. See https://example.com/data for details.`;
    const violations = runCycle4(content, 'research/revenue.md');
    assert.equal(violations.length, 0);
  });

  it('accepts [Ref:] markers as valid sources', () => {
    const content = `<!-- PERPLEXITY_VERIFIED -->

Revenue grew 45% in 2023. [Ref: McKinsey 2023 Annual Report]`;
    const violations = runCycle4(content, 'research/revenue.md');
    assert.equal(violations.length, 0);
  });

  it('accepts [Verified:] markers as valid sources', () => {
    const content = `<!-- PERPLEXITY_VERIFIED -->

The market hit $500 billion. [Verified: Grand View Research 2023]`;
    const violations = runCycle4(content, 'research/revenue.md');
    assert.equal(violations.length, 0);
  });
});

// ─── Claim Pattern Detection ─────────────────────────────────────────────────

describe('Cycle 4 — Claim Pattern Detection', () => {
  it('detects percentage claims', () => {
    const content = 'Growth was 45% year-over-year.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0, 'Should detect percentage claim');
  });

  it('detects dollar amount claims', () => {
    const content = 'The market was valued at $150 billion.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0, 'Should detect dollar claim');
  });

  it('detects multiplier claims', () => {
    const content = 'Performance improved by 10x after optimization.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0, 'Should detect multiplier claim');
  });

  it('detects n-fold claims', () => {
    const content = 'There was a 3-fold increase in adoption.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0, 'Should detect n-fold claim');
  });

  it('detects large number quantities', () => {
    const content = 'The platform serves 1,000,000 users.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0, 'Should detect large number claim');
  });

  it('detects comparative claims', () => {
    const content = 'AI is 5 times faster than manual processing.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0, 'Should detect comparative claim');
  });

  it('does not trigger on content without claims', () => {
    const content = 'This document describes the architecture of our system.';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0, 'Should have no violations for claim-free content');
  });
});

// ─── Disabled Rules Config ───────────────────────────────────────────────────

describe('Cycle 4 — Disabled Rules', () => {
  it('skips vague language check when no-vague-claims is disabled', () => {
    const content = 'Studies show that AI is transforming business.';
    const config = { disabledRules: ['no-vague-claims'] };
    const violations = runCycle4(content, 'research/report.md', config);
    assert.ok(!violations.some(v => v.ruleId === 'no-vague-claims'));
  });

  it('skips verification tag check when no-unverified-claims is disabled', () => {
    const content = 'The AI market grew by 35% in 2023.';
    const config = { disabledRules: ['no-unverified-claims'] };
    const violations = runCycle4(content, 'research/report.md', config);
    assert.ok(!violations.some(v => v.ruleId === 'no-unverified-claims'));
  });

  it('skips source proximity check when no-unsourced-claims is disabled', () => {
    const padding = 'Lorem ipsum dolor sit amet. '.repeat(15);
    const content = `<!-- PERPLEXITY_VERIFIED -->\n\nGrew by 45%.\n\n${padding}\n\n[Source: https://example.com]`;
    const config = { disabledRules: ['no-unsourced-claims'] };
    const violations = runCycle4(content, 'research/report.md', config);
    assert.ok(!violations.some(v => v.ruleId === 'no-unsourced-claims'));
  });
});

// ─── Fixture Files ───────────────────────────────────────────────────────────

describe('Cycle 4 — Fixture Files', () => {
  it('blocks blocked-research.md', () => {
    const content = readFileSync(resolve(fixturesDir, 'blocked-research.md'), 'utf-8');
    const violations = runCycle4(content, 'docs/research/blocked-research.md');
    assert.ok(violations.length > 0, 'Should block research file with vague claims');
  });

  it('approves clean-research.md', () => {
    const content = readFileSync(resolve(fixturesDir, 'clean-research.md'), 'utf-8');
    const violations = runCycle4(content, 'docs/research/clean-research.md');
    assert.equal(violations.length, 0, `Expected no violations, got: ${violations.map(v => v.ruleId).join(', ')}`);
  });
});

// ─── isResearchFile utility ──────────────────────────────────────────────────

describe('isResearchFile()', () => {
  it('detects files in /research/ directory', () => {
    assert.equal(isResearchFile('docs/research/report.md'), true);
    assert.equal(isResearchFile('docs/research/findings.md'), true);
  });

  it('detects files with "research" in filename', () => {
    assert.equal(isResearchFile('docs/market-research.md'), true);
    assert.equal(isResearchFile('research-notes.md'), true);
  });

  it('handles Windows backslash paths', () => {
    assert.equal(isResearchFile('docs\\research\\report.md'), true);
  });

  it('rejects non-.md files', () => {
    assert.equal(isResearchFile('docs/research/report.py'), false);
    assert.equal(isResearchFile('research.js'), false);
  });

  it('rejects non-research .md files', () => {
    assert.equal(isResearchFile('docs/README.md'), false);
    assert.equal(isResearchFile('CHANGELOG.md'), false);
  });

  it('handles null/undefined/empty', () => {
    assert.equal(isResearchFile(null), false);
    assert.equal(isResearchFile(undefined), false);
    assert.equal(isResearchFile(''), false);
  });
});

// ─── getAllCycle4Rules ────────────────────────────────────────────────────────

describe('getAllCycle4Rules()', () => {
  it('returns all 3 Cycle 4 rules', () => {
    const rules = getAllCycle4Rules();
    assert.equal(rules.length, 3);
    assert.ok(rules.some(r => r.id === 'no-vague-claims'));
    assert.ok(rules.some(r => r.id === 'no-unverified-claims'));
    assert.ok(rules.some(r => r.id === 'no-unsourced-claims'));
  });
});
