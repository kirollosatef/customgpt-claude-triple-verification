/**
 * Edge Case & Stress Tests for Triple Verification Plugin.
 * Tests boundary conditions, unusual inputs, cross-cycle interactions,
 * and real-world scenarios that unit tests may miss.
 */

import { describe, it } from 'node:test';
import { strict as assert } from 'node:assert';
import { runCycle4 } from '../scripts/lib/research-verifier.mjs';
import { runCycle1, runCycle2 } from '../scripts/lib/rules-engine.mjs';
import { isResearchFile, getFileExtension } from '../scripts/lib/utils.mjs';

// ─── Edge Case: Vague language inside code blocks (false positives) ─────────

describe('Cycle 4 — Code blocks should still trigger (content-based scan)', () => {
  it('detects vague language even inside markdown code blocks', () => {
    const content = '# Report\n\n```\nStudies show that AI is transforming business.\n```\n';
    const violations = runCycle4(content, 'research/report.md');
    // The current design scans full content including code blocks
    assert.ok(violations.length > 0, 'Vague language in code blocks should be caught');
    assert.equal(violations[0].ruleId, 'no-vague-claims');
  });

  it('detects vague language in inline code', () => {
    const content = 'As `experts say`, this is important.\n';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
    assert.equal(violations[0].ruleId, 'no-vague-claims');
  });
});

// ─── Edge Case: Multiple vague phrases in one document ──────────────────────

describe('Cycle 4 — Multiple vague phrases', () => {
  it('blocks on first match (returns single violation, not multiple)', () => {
    const content = 'Studies show that AI is growing. Research indicates the market is expanding. Experts say this is big.';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 1, 'Should return exactly one violation (instant block)');
    assert.equal(violations[0].ruleId, 'no-vague-claims');
  });
});

// ─── Edge Case: Vague phrase as substring of a larger word ──────────────────

describe('Cycle 4 — Vague phrase boundary detection', () => {
  it('blocks "studies show" even mid-sentence', () => {
    const content = 'Many peer-reviewed studies show a clear trend in adoption rates.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });

  it('blocks case variations like "STUDIES SHOW"', () => {
    const content = 'STUDIES SHOW THAT THIS IS THE CASE.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });

  it('blocks mixed case "Studies Show"', () => {
    const content = 'Studies Show that things are changing rapidly.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });
});

// ─── Edge Case: Claims at document boundaries ───────────────────────────────

describe('Cycle 4 — Claims at document boundaries', () => {
  it('detects claim at the very start of content', () => {
    const content = '45% of companies adopted AI. The end.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
    assert.equal(violations[0].ruleId, 'no-unverified-claims');
  });

  it('detects claim at the very end of content', () => {
    const content = 'Here is the final note: revenue reached $5 billion';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
    assert.equal(violations[0].ruleId, 'no-unverified-claims');
  });

  it('source at start covers claim at start', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\n[Source: Gartner 2024](https://gartner.com/report) 45% of companies adopted AI.';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });
});

// ─── Edge Case: Very large content ──────────────────────────────────────────

describe('Cycle 4 — Large content stress test', () => {
  it('handles content with 1000+ lines without error', () => {
    const lines = [];
    lines.push('<!-- PERPLEXITY_VERIFIED -->');
    for (let i = 0; i < 1000; i++) {
      lines.push(`Line ${i}: This is regular text without any claims or vague language.`);
    }
    const content = lines.join('\n');
    const violations = runCycle4(content, 'research/big-report.md');
    assert.equal(violations.length, 0);
  });

  it('handles large content with claims and sources', () => {
    const lines = [];
    lines.push('<!-- PERPLEXITY_VERIFIED -->');
    for (let i = 0; i < 100; i++) {
      lines.push(`Revenue grew by ${i * 10}% according to [Gartner](https://gartner.com/${i}).`);
    }
    const content = lines.join('\n');
    const violations = runCycle4(content, 'research/big-report.md');
    assert.equal(violations.length, 0, 'All claims have nearby sources');
  });

  it('detects unsourced claims in large content', () => {
    const lines = [];
    lines.push('<!-- PERPLEXITY_VERIFIED -->');
    // 200 lines of clean text
    for (let i = 0; i < 200; i++) {
      lines.push('Regular text without claims.');
    }
    // Then a claim with no source nearby
    lines.push('Revenue grew by 85% in the last quarter.');
    for (let i = 0; i < 200; i++) {
      lines.push('More regular text without claims.');
    }
    const content = lines.join('\n');
    const violations = runCycle4(content, 'research/big-report.md');
    assert.ok(violations.length > 0);
    assert.equal(violations[0].ruleId, 'no-unsourced-claims');
  });
});

// ─── Edge Case: Special characters and Unicode ──────────────────────────────

describe('Cycle 4 — Special characters and Unicode', () => {
  it('handles emoji in content', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\n🚀 Revenue grew by 45% [Source](https://example.com)';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });

  it('handles non-Latin characters', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\nこれはテストです。Revenue: $5 billion [Ref: Test](https://example.com)';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });

  it('handles HTML entities', () => {
    const content = 'Studies&nbsp;show that this is important.';
    const violations = runCycle4(content, 'research/report.md');
    // "Studies&nbsp;show" shouldn't match "studies show" because of the entity
    assert.equal(violations.length, 0, 'HTML entity breaks the vague phrase');
  });

  it('handles Windows line endings (CRLF)', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\r\nRevenue grew by 45%\r\n[Source](https://example.com)\r\n';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });
});

// ─── Edge Case: Content that looks like claims but isn't ────────────────────

describe('Cycle 4 — False positive avoidance', () => {
  it('does not trigger on small percentages in non-claim context', () => {
    // "45%" IS a claim regardless of context, so this WILL trigger
    const content = 'Set opacity to 0.85 and font-size to 14px.';
    const violations = runCycle4(content, 'research/report.md');
    // No percentage pattern matches "0.85" or "14px"
    assert.equal(violations.length, 0, 'CSS-like values should not trigger');
  });

  it('detects year references as claims', () => {
    const content = 'In 2024, the market shifted significantly.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0, 'Year references are considered claims');
  });

  it('no claims in purely narrative text', () => {
    const content = 'The team discussed the project goals and decided on a new direction.';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });
});

// ─── Edge Case: Source patterns ─────────────────────────────────────────────

describe('Cycle 4 — Source pattern edge cases', () => {
  it('accepts URL with query parameters', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\nRevenue grew by 45% https://example.com/report?year=2024&type=annual';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });

  it('accepts URL with fragment', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\nRevenue grew by 45% https://example.com/report#section-3';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });

  it('accepts markdown link with complex URL', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\nRevenue grew by 45% [Annual Report 2024](https://example.com/reports/2024/annual-revenue.pdf)';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });

  it('rejects source marker without brackets', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\nRevenue grew by 45%. Source: McKinsey Report';
    const violations = runCycle4(content, 'research/report.md');
    // "Source:" without brackets is NOT a valid marker
    assert.ok(violations.length > 0);
  });

  it('accepts [Source] with various content inside brackets', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\nRevenue grew by 45% [Source: McKinsey Global Institute, 2024 Annual Review, pp. 45-67]';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });
});

// ─── Edge Case: PERPLEXITY_VERIFIED tag placement ───────────────────────────

describe('Cycle 4 — Verification tag placement', () => {
  it('accepts tag at the end of document', () => {
    const content = 'Revenue grew by 45% [Source](https://example.com)\n\n<!-- PERPLEXITY_VERIFIED -->';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });

  it('accepts tag in the middle of document', () => {
    const content = '# Report\n\n<!-- PERPLEXITY_VERIFIED -->\n\nRevenue grew by 45% [Source](https://example.com)';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0);
  });

  it('rejects similar but incorrect tags', () => {
    const content = '<!-- PERPLEXITY VERIFIED -->\nRevenue grew by 45%.';
    const violations = runCycle4(content, 'research/report.md');
    // Missing underscore — should NOT match
    assert.ok(violations.length > 0);
    assert.equal(violations[0].ruleId, 'no-unverified-claims');
  });

  it('rejects lowercase tag', () => {
    const content = '<!-- perplexity_verified -->\nRevenue grew by 45%.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
    assert.equal(violations[0].ruleId, 'no-unverified-claims');
  });
});

// ─── Edge Case: isResearchFile path patterns ────────────────────────────────

describe('isResearchFile — Extended path patterns', () => {
  it('detects deeply nested research paths', () => {
    assert.ok(isResearchFile('a/b/c/research/d/report.md'));
  });

  it('detects research at root with Windows path', () => {
    assert.ok(isResearchFile('C:\\Users\\dev\\project\\research\\report.md'));
  });

  it('detects relative research/ prefix', () => {
    assert.ok(isResearchFile('research/2024/q4-analysis.md'));
  });

  it('detects filename with "research" in compound name', () => {
    assert.ok(isResearchFile('docs/ai-research-findings.md'));
  });

  it('rejects .md file in "researcher" directory', () => {
    // "researcher" contains "research" as substring in the filename split check
    // The path doesn't contain /research/ but the directory name contains "research"
    // Actually the normalized path "docs/researcher/notes.md" — the filename is "notes.md"
    // which does NOT contain "research". Let's check if includes('/research/') catches "researcher"
    const result = isResearchFile('docs/researcher/notes.md');
    // '/researcher/' does NOT match '/research/' — correct!
    assert.ok(!result, 'researcher/ directory should not be treated as research/');
  });

  it('detects file named "research-notes.md" in any directory', () => {
    assert.ok(isResearchFile('src/research-notes.md'));
  });

  it('rejects non-.md file even in research directory', () => {
    assert.ok(!isResearchFile('research/data.csv'));
  });

  it('rejects null, undefined, empty, and numbers', () => {
    assert.ok(!isResearchFile(null));
    assert.ok(!isResearchFile(undefined));
    assert.ok(!isResearchFile(''));
    assert.ok(!isResearchFile(123));
  });
});

// ─── Cross-cycle: Research file should NOT trigger Cycles 1-2 ───────────────

describe('Cross-cycle isolation', () => {
  it('Cycles 1-2 still detect issues in non-research code', () => {
    const code = '// TODO: implement this\nconst api_key = "sk_live_abc123";\n';
    const c1 = runCycle1(code, '.js', 'file-write', {});
    const c2 = runCycle2(code, '.js', 'file-write', {});
    assert.ok(c1.length > 0, 'Cycle 1 should catch TODO');
    assert.ok(c2.length > 0, 'Cycle 2 should catch hardcoded secret');
  });

  it('Cycle 4 does not run on code files (no false positives)', () => {
    // A code file containing "studies show" should NOT be caught by Cycle 4
    // because the pre-tool-gate routes code files to Cycles 1-2 only
    // Here we test the verifier directly — it WILL flag it if called
    const code = '// studies show that this algorithm is fast\nconst x = 1;';
    const violations = runCycle4(code, 'src/main.js');
    // runCycle4 doesn't care about file extension — it's the gate that routes
    assert.ok(violations.length > 0, 'runCycle4 flags vague language regardless of file');
  });
});

// ─── Edge Case: Overlapping claim patterns ──────────────────────────────────

describe('Cycle 4 — Overlapping claim patterns', () => {
  it('handles text with multiple claim types in same sentence', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\nIn 2024, revenue grew 45% to $5 billion, a 3x increase. [Source](https://example.com)';
    const violations = runCycle4(content, 'research/report.md');
    // All claims should have a nearby source
    assert.equal(violations.length, 0, 'All overlapping claims should be covered by nearby source');
  });

  it('catches unsourced claims even with other sourced claims nearby', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\n' +
      'In 2024, revenue grew 45% [Source](https://example.com).\n' +
      'x'.repeat(400) + '\n' + // 400 chars padding — beyond 300-char proximity window
      'The market reached $10 billion with a 5-fold increase.'; // far from any source
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0, 'Distant claims should be flagged even if others are sourced');
  });
});

// ─── Edge Case: Config-based disabling ──────────────────────────────────────

describe('Cycle 4 — Config edge cases', () => {
  it('allows everything when all 3 rules disabled', () => {
    const content = 'Studies show this. Revenue grew 45%. No tag here.';
    const config = {
      disabledRules: ['no-vague-claims', 'no-unverified-claims', 'no-unsourced-claims']
    };
    const violations = runCycle4(content, 'research/report.md', config);
    assert.equal(violations.length, 0, 'No violations when all rules disabled');
  });

  it('skips vague check but still requires verification tag', () => {
    const content = 'Studies show that revenue grew 45%.';
    const config = { disabledRules: ['no-vague-claims'] };
    const violations = runCycle4(content, 'research/report.md', config);
    // Should skip past vague check (Pass 1), then hit Pass 2 (no tag)
    assert.ok(violations.length > 0);
    assert.equal(violations[0].ruleId, 'no-unverified-claims');
  });

  it('handles undefined config gracefully', () => {
    const content = 'No claims here, just text.';
    assert.doesNotThrow(() => runCycle4(content, 'research/report.md', undefined));
    assert.equal(runCycle4(content, 'research/report.md', undefined).length, 0);
  });

  it('handles null config gracefully (no crash)', () => {
    const content = 'No claims here, just text.';
    assert.doesNotThrow(() => runCycle4(content, 'research/report.md', null));
    assert.equal(runCycle4(content, 'research/report.md', null).length, 0);
  });

  it('handles null config with vague language', () => {
    const content = 'Studies show that AI is growing.';
    assert.doesNotThrow(() => runCycle4(content, 'research/report.md', null));
    const v = runCycle4(content, 'research/report.md', null);
    assert.ok(v.length > 0, 'Should still detect vague language with null config');
  });
});

// ─── Edge Case: Empty and minimal content ───────────────────────────────────

describe('Cycle 4 — Empty and minimal content', () => {
  it('approves empty string', () => {
    assert.equal(runCycle4('', 'research/report.md').length, 0);
  });

  it('approves null content', () => {
    assert.equal(runCycle4(null, 'research/report.md').length, 0);
  });

  it('approves undefined content', () => {
    assert.equal(runCycle4(undefined, 'research/report.md').length, 0);
  });

  it('approves whitespace-only content', () => {
    assert.equal(runCycle4('   \n\n\t  ', 'research/report.md').length, 0);
  });

  it('approves single character content', () => {
    assert.equal(runCycle4('a', 'research/report.md').length, 0);
  });

  it('approves content that is just the verification tag', () => {
    assert.equal(runCycle4('<!-- PERPLEXITY_VERIFIED -->', 'research/report.md').length, 0);
  });
});

// ─── Edge Case: getFileExtension ────────────────────────────────────────────

describe('getFileExtension — Edge cases', () => {
  it('handles dotfiles', () => {
    assert.equal(getFileExtension('.gitignore'), '.gitignore');
  });

  it('handles multiple dots', () => {
    assert.equal(getFileExtension('archive.tar.gz'), '.gz');
  });

  it('handles no extension', () => {
    assert.equal(getFileExtension('Makefile'), '');
  });

  it('handles trailing dot', () => {
    assert.equal(getFileExtension('file.'), '');
  });

  it('handles path with dots in directory names', () => {
    assert.equal(getFileExtension('org.example.pkg/Main.java'), '.java');
  });
});

// ─── Edge Case: Claim patterns should match various formats ─────────────────

describe('Cycle 4 — Claim pattern format variations', () => {
  it('matches percentage with decimal: "3.5%"', () => {
    const content = 'Growth rate was 3.5%.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });

  it('matches dollar with "trillion"', () => {
    const content = 'The market is worth $1.5 trillion.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });

  it('matches comma-separated numbers: "1,000,000"', () => {
    const content = 'There are 1,000,000 users on the platform.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });

  it('matches "study by" pattern', () => {
    const content = 'A study by MIT found interesting results.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });

  it('matches institution names', () => {
    const content = 'According to Stanford University, the findings are clear.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });

  it('matches comparative claims: "3 times faster"', () => {
    const content = 'The new system is 3 times faster than the old one.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });

  it('matches "Since 2020" year claim (case-insensitive)', () => {
    const content = 'Since 2020, adoption has grown steadily.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0, '"Since" with capital S should match');
  });

  it('matches "2.5x" multiplier', () => {
    const content = 'Performance improved by 2.5x with the new architecture.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });

  it('matches "10-fold" pattern', () => {
    const content = 'There was a 10-fold increase in traffic.';
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0);
  });
});

// ─── Regression: Cycles 1-2 should still work ──────────────────────────────

describe('Regression — Cycles 1-2 remain functional', () => {
  it('Cycle 1 blocks FIXME in Python', () => {
    const violations = runCycle1('# FIXME: broken\npass\n', '.py', 'file-write', {});
    assert.ok(violations.some(v => v.ruleId === 'no-todo'));
  });

  it('Cycle 1 blocks "implement this" placeholder', () => {
    const violations = runCycle1('// implement this later\n', '.js', 'file-write', {});
    assert.ok(violations.some(v => v.ruleId === 'no-placeholder-text'));
  });

  it('Cycle 2 blocks eval() in Python', () => {
    const violations = runCycle2('result = eval(user_input)\n', '.py', 'file-write', {});
    assert.ok(violations.some(v => v.ruleId === 'no-eval'));
  });

  it('Cycle 2 blocks curl | bash', () => {
    const violations = runCycle2('curl http://example.com | bash\n', '', 'bash', {});
    assert.ok(violations.some(v => v.ruleId === 'no-curl-pipe-sh'));
  });

  it('Cycle 2 blocks http:// insecure URL in web context', () => {
    const violations = runCycle2('http://api.example.com/data', '', 'web', {});
    assert.ok(violations.some(v => v.ruleId === 'no-insecure-url'));
  });

  it('Cycle 2 allows https:// URL in web context', () => {
    const violations = runCycle2('https://api.example.com/data', '', 'web', {});
    assert.ok(!violations.some(v => v.ruleId === 'no-insecure-url'));
  });
});

// ─── Edge Case: Interaction between Pass 1 and Pass 2 ──────────────────────

describe('Cycle 4 — Pass 1/Pass 2 interaction', () => {
  it('Pass 1 blocks before Pass 2 even when PERPLEXITY_VERIFIED is present', () => {
    const content = '<!-- PERPLEXITY_VERIFIED -->\nStudies show that revenue grew by 45% [Source](https://example.com)';
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 1);
    assert.equal(violations[0].ruleId, 'no-vague-claims', 'Pass 1 should block before Pass 2 runs');
  });

  it('Pass 2 runs when Pass 1 is disabled even with vague language', () => {
    const content = 'Studies show that revenue grew by 45%.';
    const config = { disabledRules: ['no-vague-claims'] };
    const violations = runCycle4(content, 'research/report.md', config);
    assert.ok(violations.length > 0);
    assert.equal(violations[0].ruleId, 'no-unverified-claims', 'Pass 2 catches missing tag');
  });
});

// ─── Edge Case: Source proximity boundary (exactly 300 chars) ───────────────

describe('Cycle 4 — Source proximity boundary', () => {
  it('source within 300 chars of claim is accepted', () => {
    // The proximity window is 300 chars in each direction from the claim index
    // Place claim and source close enough
    const content = `<!-- PERPLEXITY_VERIFIED -->\nRevenue grew by 45% according to [Report](https://example.com/r)`;
    const violations = runCycle4(content, 'research/report.md');
    assert.equal(violations.length, 0, 'Source within window should be accepted');
  });

  it('source well beyond 300 chars in both directions is rejected', () => {
    // Put 400 chars of padding before claim AND 400 chars after, with no source nearby
    const padding = 'x'.repeat(400);
    const content = `<!-- PERPLEXITY_VERIFIED -->\nhttps://example.com/old-source\n${padding}\nRevenue grew by 45% in the market.\n${padding}\nhttps://example.com/distant-source`;
    const violations = runCycle4(content, 'research/report.md');
    assert.ok(violations.length > 0, 'Source beyond 300 chars in both directions should be rejected');
  });
});
