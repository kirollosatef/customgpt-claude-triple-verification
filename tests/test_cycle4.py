"""
Cycle 4 — Research Claim Verification
Python equivalent of test-cycle4.mjs
Run: python3 -m unittest tests/test_cycle4.py -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))
from quadruple_verification import _run_cycle4, _is_research_file, get_all_cycle4_rules

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# ─── Pass 1: Vague Language Detection ────────────────────────────────────────

class TestCycle4Pass1VagueLanguage(unittest.TestCase):
    def _assert_vague(self, text: str):
        v = _run_cycle4(text, "docs/research/report.md", set())
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["rule_id"], "no-vague-claims")
        self.assertEqual(v[0]["cycle"], 4)

    def test_blocks_studies_show(self):
        self._assert_vague("Studies show that AI is transforming business.")

    def test_blocks_research_indicates(self):
        self._assert_vague("Research indicates a growing trend in cloud adoption.")

    def test_blocks_experts_say(self):
        self._assert_vague("Experts say this is the future of computing.")

    def test_blocks_according_to_research(self):
        self._assert_vague("According to research, the market is expanding.")

    def test_blocks_data_suggests(self):
        self._assert_vague("Data suggests that revenue will double.")

    def test_blocks_it_is_known_that(self):
        self._assert_vague("It is known that open source dominates.")

    def test_blocks_generally_accepted(self):
        self._assert_vague("This approach is generally accepted in the industry.")

    def test_blocks_industry_reports_confirm(self):
        self._assert_vague("Industry reports confirm the trend.")

    def test_blocks_recent_surveys_found(self):
        self._assert_vague("Recent surveys found high satisfaction rates.")

    def test_blocks_analysts_estimate(self):
        self._assert_vague("Analysts estimate the market will reach $1 trillion.")

    def test_blocks_sources_suggest(self):
        self._assert_vague("Sources suggest a shift toward remote work.")

    def test_blocks_widely_reported(self):
        self._assert_vague("The trend has been widely reported across media.")

    def test_blocks_it_has_been_shown(self):
        self._assert_vague("It has been shown that automation reduces costs.")

    def test_blocks_evidence_suggests(self):
        self._assert_vague("Evidence suggests a correlation between AI use and profit.")

    def test_allows_specific_sourced_text_without_vague_language(self):
        content = "According to the McKinsey 2023 report, AI adoption grew by 25%."
        v = _run_cycle4(content, "docs/research/report.md", set())
        # No vague phrase → passes Pass 1.
        # Pass 2 triggers because there is no PERPLEXITY_VERIFIED tag.
        self.assertFalse(any(x["rule_id"] == "no-vague-claims" for x in v))


# ─── Pass 2: Verification Tag Requirement ────────────────────────────────────

class TestCycle4Pass2VerificationTag(unittest.TestCase):
    def test_blocks_claims_without_perplexity_verified_tag(self):
        content = "The AI market grew by 35% in 2023 and reached $150 billion."
        v = _run_cycle4(content, "research/market.md", set())
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["rule_id"], "no-unverified-claims")
        self.assertEqual(v[0]["cycle"], 4)

    def test_allows_claims_with_tag_and_nearby_sources(self):
        content = (
            "<!-- PERPLEXITY_VERIFIED -->\n\n"
            "The AI market grew by 35% in 2023 [Source: https://example.com/report]."
        )
        v = _run_cycle4(content, "research/market.md", set())
        self.assertEqual(len(v), 0)

    def test_blocks_when_tag_present_but_sources_too_far_from_claim(self):
        padding = "Lorem ipsum dolor sit amet. " * 15  # ~420 chars
        content = (
            "<!-- PERPLEXITY_VERIFIED -->\n\n"
            "The market grew by 45% in 2023.\n\n"
            f"{padding}\n\n"
            "[Source: https://example.com/report]"
        )
        v = _run_cycle4(content, "research/market.md", set())
        self.assertTrue(any(x["rule_id"] == "no-unsourced-claims" for x in v))


# ─── Pass 2: Source Proximity Check ──────────────────────────────────────────

class TestCycle4Pass2SourceProximity(unittest.TestCase):
    def _verified(self, body: str) -> str:
        return f"<!-- PERPLEXITY_VERIFIED -->\n\n{body}"

    def test_accepts_markdown_links_as_valid_sources(self):
        content = self._verified(
            "Revenue grew 45% according to [McKinsey Report](https://mckinsey.com/report)."
        )
        v = _run_cycle4(content, "research/revenue.md", set())
        self.assertEqual(len(v), 0)

    def test_accepts_bare_urls_as_valid_sources(self):
        content = self._verified(
            "Revenue grew 45% in 2023. See https://example.com/data for details."
        )
        v = _run_cycle4(content, "research/revenue.md", set())
        self.assertEqual(len(v), 0)

    def test_accepts_ref_markers_as_valid_sources(self):
        content = self._verified(
            "Revenue grew 45% in 2023. [Ref: McKinsey 2023 Annual Report]"
        )
        v = _run_cycle4(content, "research/revenue.md", set())
        self.assertEqual(len(v), 0)

    def test_accepts_verified_markers_as_valid_sources(self):
        content = self._verified(
            "The market hit $500 billion. [Verified: Grand View Research 2023]"
        )
        v = _run_cycle4(content, "research/revenue.md", set())
        self.assertEqual(len(v), 0)


# ─── Claim Pattern Detection ─────────────────────────────────────────────────

class TestCycle4ClaimPatternDetection(unittest.TestCase):
    def test_detects_percentage_claims(self):
        v = _run_cycle4("Growth was 45% year-over-year.", "research/report.md", set())
        self.assertGreater(len(v), 0)

    def test_detects_dollar_amount_claims(self):
        v = _run_cycle4("The market was valued at $150 billion.", "research/report.md", set())
        self.assertGreater(len(v), 0)

    def test_detects_multiplier_claims(self):
        v = _run_cycle4("Performance improved by 10x after optimization.", "research/report.md", set())
        self.assertGreater(len(v), 0)

    def test_detects_n_fold_claims(self):
        v = _run_cycle4("There was a 3-fold increase in adoption.", "research/report.md", set())
        self.assertGreater(len(v), 0)

    def test_detects_large_number_quantities(self):
        v = _run_cycle4("The platform serves 1,000,000 users.", "research/report.md", set())
        self.assertGreater(len(v), 0)

    def test_detects_comparative_claims(self):
        v = _run_cycle4("AI is 5 times faster than manual processing.", "research/report.md", set())
        self.assertGreater(len(v), 0)

    def test_does_not_trigger_on_content_without_claims(self):
        v = _run_cycle4(
            "This document describes the architecture of our system.",
            "research/report.md",
            set(),
        )
        self.assertEqual(len(v), 0)


# ─── Disabled Rules Config ───────────────────────────────────────────────────

class TestCycle4DisabledRules(unittest.TestCase):
    def test_skips_vague_language_check_when_no_vague_claims_is_disabled(self):
        content = "Studies show that AI is transforming business."
        v = _run_cycle4(content, "research/report.md", {"no-vague-claims"})
        self.assertFalse(any(x["rule_id"] == "no-vague-claims" for x in v))

    def test_skips_verification_tag_check_when_no_unverified_claims_is_disabled(self):
        content = "The AI market grew by 35% in 2023."
        v = _run_cycle4(content, "research/report.md", {"no-unverified-claims"})
        self.assertFalse(any(x["rule_id"] == "no-unverified-claims" for x in v))

    def test_skips_source_proximity_check_when_no_unsourced_claims_is_disabled(self):
        padding = "Lorem ipsum dolor sit amet. " * 15
        content = (
            f"<!-- PERPLEXITY_VERIFIED -->\n\nGrew by 45%.\n\n{padding}\n\n"
            "[Source: https://example.com]"
        )
        v = _run_cycle4(content, "research/report.md", {"no-unsourced-claims"})
        self.assertFalse(any(x["rule_id"] == "no-unsourced-claims" for x in v))


# ─── Fixture Files ───────────────────────────────────────────────────────────

class TestCycle4FixtureFiles(unittest.TestCase):
    def test_blocks_blocked_research_md(self):
        content = (FIXTURES_DIR / "blocked-research.md").read_text(encoding="utf-8")
        v = _run_cycle4(content, "docs/research/blocked-research.md", set())
        self.assertGreater(len(v), 0, "Should block research file with vague claims")

    def test_approves_clean_research_md(self):
        content = (FIXTURES_DIR / "clean-research.md").read_text(encoding="utf-8")
        v = _run_cycle4(content, "docs/research/clean-research.md", set())
        rule_ids = [x["rule_id"] for x in v]
        self.assertEqual(len(v), 0, f"Expected no violations, got: {rule_ids}")


# ─── isResearchFile utility ──────────────────────────────────────────────────

class TestIsResearchFile(unittest.TestCase):
    def test_detects_files_in_research_directory(self):
        self.assertTrue(_is_research_file("docs/research/report.md"))
        self.assertTrue(_is_research_file("docs/research/findings.md"))

    def test_detects_files_with_research_in_filename(self):
        self.assertTrue(_is_research_file("docs/market-research.md"))
        self.assertTrue(_is_research_file("research-notes.md"))

    def test_handles_windows_backslash_paths(self):
        self.assertTrue(_is_research_file("docs\\research\\report.md"))

    def test_rejects_non_md_files(self):
        self.assertFalse(_is_research_file("docs/research/report.py"))
        self.assertFalse(_is_research_file("research.js"))

    def test_rejects_non_research_md_files(self):
        self.assertFalse(_is_research_file("docs/README.md"))
        self.assertFalse(_is_research_file("CHANGELOG.md"))

    def test_handles_null_undefined_empty(self):
        self.assertFalse(_is_research_file(None))
        self.assertFalse(_is_research_file(""))


# ─── getAllCycle4Rules ────────────────────────────────────────────────────────

class TestGetAllCycle4Rules(unittest.TestCase):
    def test_returns_all_3_cycle4_rules(self):
        rules = get_all_cycle4_rules()
        self.assertEqual(len(rules), 3)
        rule_ids = {r["id"] for r in rules}
        self.assertIn("no-vague-claims", rule_ids)
        self.assertIn("no-unverified-claims", rule_ids)
        self.assertIn("no-unsourced-claims", rule_ids)


if __name__ == "__main__":
    unittest.main(verbosity=2)
