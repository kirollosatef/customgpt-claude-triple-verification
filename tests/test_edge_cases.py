"""
Edge Case & Stress Tests for Quadruple Verification Plugin (Python port).
Python equivalent of test-edge-cases.mjs

Tests boundary conditions, unusual inputs, cross-cycle interactions,
and real-world scenarios that unit tests may miss.

Run: python3 -m unittest tests/test_edge_cases.py -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))
from quadruple_verification import (
    _get_file_ext,
    _is_research_file,
    _run_cycle1,
    _run_cycle2,
    _run_cycle4,
)


# ─── Vague language inside code blocks (false positives) ─────────────────────

class TestCodeBlockScanning(unittest.TestCase):
    def test_detects_vague_language_inside_markdown_code_blocks(self):
        # Current design scans full content including code blocks
        content = "# Report\n\n```\nStudies show that AI is transforming business.\n```\n"
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0, "Vague language in code blocks should be caught")
        self.assertEqual(v[0]["rule_id"], "no-vague-claims")

    def test_detects_vague_language_in_inline_code(self):
        content = "As `experts say`, this is important.\n"
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0)
        self.assertEqual(v[0]["rule_id"], "no-vague-claims")


# ─── Multiple vague phrases in one document ───────────────────────────────────

class TestMultipleVaguePhrases(unittest.TestCase):
    def test_blocks_on_first_match_returns_single_violation(self):
        content = (
            "Studies show that AI is growing. "
            "Research indicates the market is expanding. "
            "Experts say this is big."
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 1, "Should return exactly one violation (instant block)")
        self.assertEqual(v[0]["rule_id"], "no-vague-claims")


# ─── Vague phrase boundary detection ─────────────────────────────────────────

class TestVaguePhraseBoundaryDetection(unittest.TestCase):
    def test_blocks_studies_show_mid_sentence(self):
        content = "Many peer-reviewed studies show a clear trend in adoption rates."
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0)

    def test_blocks_case_variation_uppercase(self):
        content = "STUDIES SHOW THAT THIS IS THE CASE."
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0)

    def test_blocks_mixed_case(self):
        content = "Studies Show that things are changing rapidly."
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0)


# ─── Claims at document boundaries ───────────────────────────────────────────

class TestClaimsAtDocumentBoundaries(unittest.TestCase):
    def test_detects_claim_at_very_start_of_content(self):
        content = "45% of companies adopted AI. The end."
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0)
        self.assertEqual(v[0]["rule_id"], "no-unverified-claims")

    def test_detects_claim_at_very_end_of_content(self):
        content = "Here is the final note: revenue reached $5 billion"
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0)
        self.assertEqual(v[0]["rule_id"], "no-unverified-claims")

    def test_source_at_start_covers_claim_at_start(self):
        content = (
            "<!-- PERPLEXITY_VERIFIED -->\n"
            "[Source: Gartner 2024](https://gartner.com/report) 45% of companies adopted AI."
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)


# ─── Large content stress test ────────────────────────────────────────────────

class TestLargeContentStress(unittest.TestCase):
    def test_handles_1000_lines_without_error(self):
        lines = ["<!-- PERPLEXITY_VERIFIED -->"]
        for i in range(1000):
            lines.append(f"Line {i}: This is regular text without any claims or vague language.")
        content = "\n".join(lines)
        v = _run_cycle4(content, "research/big-report.md", set())
        self.assertEqual(len(v), 0)

    def test_handles_large_content_with_claims_and_sources(self):
        lines = ["<!-- PERPLEXITY_VERIFIED -->"]
        for i in range(100):
            lines.append(f"Revenue grew by {i * 10}% according to [Gartner](https://gartner.com/{i}).")
        content = "\n".join(lines)
        v = _run_cycle4(content, "research/big-report.md", set())
        self.assertEqual(len(v), 0, "All claims have nearby sources")

    def test_detects_unsourced_claims_in_large_content(self):
        lines = ["<!-- PERPLEXITY_VERIFIED -->"]
        for _ in range(200):
            lines.append("Regular text without claims.")
        lines.append("Revenue grew by 85% in the last quarter.")
        for _ in range(200):
            lines.append("More regular text without claims.")
        content = "\n".join(lines)
        v = _run_cycle4(content, "research/big-report.md", set())
        self.assertGreater(len(v), 0)
        self.assertEqual(v[0]["rule_id"], "no-unsourced-claims")


# ─── Special characters and Unicode ──────────────────────────────────────────

class TestSpecialCharactersAndUnicode(unittest.TestCase):
    def test_handles_emoji_in_content(self):
        content = "<!-- PERPLEXITY_VERIFIED -->\n🚀 Revenue grew by 45% [Source](https://example.com)"
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)

    def test_handles_non_latin_characters(self):
        content = "<!-- PERPLEXITY_VERIFIED -->\nこれはテストです。Revenue: $5 billion [Ref: Test](https://example.com)"
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)

    def test_handles_html_entities(self):
        content = "Studies&nbsp;show that this is important."
        v = _run_cycle4(content, "research/report.md", set())
        # "Studies&nbsp;show" shouldn't match "studies show" because of the entity
        self.assertEqual(len(v), 0, "HTML entity breaks the vague phrase")

    def test_handles_windows_line_endings_crlf(self):
        content = "<!-- PERPLEXITY_VERIFIED -->\r\nRevenue grew by 45%\r\n[Source](https://example.com)\r\n"
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)


# ─── False positive avoidance ─────────────────────────────────────────────────

class TestFalsePositiveAvoidance(unittest.TestCase):
    def test_does_not_trigger_on_css_like_values(self):
        # "45%" IS a claim; but "0.85" and "14px" don't match claim patterns
        content = "Set opacity to 0.85 and font-size to 14px."
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0, "CSS-like values should not trigger")

    def test_detects_year_references_as_claims(self):
        content = "In 2024, the market shifted significantly."
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0, "Year references are considered claims")

    def test_no_claims_in_purely_narrative_text(self):
        content = "The team discussed the project goals and decided on a new direction."
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)


# ─── Source pattern edge cases ────────────────────────────────────────────────

class TestSourcePatternEdgeCases(unittest.TestCase):
    def _verified(self, body: str) -> str:
        return f"<!-- PERPLEXITY_VERIFIED -->\n{body}"

    def test_accepts_url_with_query_parameters(self):
        content = self._verified(
            "Revenue grew by 45% https://example.com/report?year=2024&type=annual"
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)

    def test_accepts_url_with_fragment(self):
        content = self._verified(
            "Revenue grew by 45% https://example.com/report#section-3"
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)

    def test_accepts_markdown_link_with_complex_url(self):
        content = self._verified(
            "Revenue grew by 45% [Annual Report 2024](https://example.com/reports/2024/annual-revenue.pdf)"
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)

    def test_rejects_source_marker_without_brackets(self):
        content = self._verified("Revenue grew by 45%. Source: McKinsey Report")
        v = _run_cycle4(content, "research/report.md", set())
        # "Source:" without brackets is NOT a valid marker
        self.assertGreater(len(v), 0)

    def test_accepts_source_with_various_content_inside_brackets(self):
        content = self._verified(
            "Revenue grew by 45% [Source: McKinsey Global Institute, 2024 Annual Review, pp. 45-67]"
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)


# ─── PERPLEXITY_VERIFIED tag placement ───────────────────────────────────────

class TestVerificationTagPlacement(unittest.TestCase):
    def test_accepts_tag_at_end_of_document(self):
        content = "Revenue grew by 45% [Source](https://example.com)\n\n<!-- PERPLEXITY_VERIFIED -->"
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)

    def test_accepts_tag_in_middle_of_document(self):
        content = "# Report\n\n<!-- PERPLEXITY_VERIFIED -->\n\nRevenue grew by 45% [Source](https://example.com)"
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0)

    def test_rejects_similar_but_incorrect_tag_missing_underscore(self):
        content = "<!-- PERPLEXITY VERIFIED -->\nRevenue grew by 45%."
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0)
        self.assertEqual(v[0]["rule_id"], "no-unverified-claims")

    def test_rejects_lowercase_tag(self):
        content = "<!-- perplexity_verified -->\nRevenue grew by 45%."
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0)
        self.assertEqual(v[0]["rule_id"], "no-unverified-claims")


# ─── isResearchFile extended path patterns ────────────────────────────────────

class TestIsResearchFileExtendedPaths(unittest.TestCase):
    def test_detects_deeply_nested_research_paths(self):
        self.assertTrue(_is_research_file("a/b/c/research/d/report.md"))

    def test_detects_research_with_windows_path(self):
        self.assertTrue(_is_research_file("C:\\Users\\dev\\project\\research\\report.md"))

    def test_detects_relative_research_prefix(self):
        self.assertTrue(_is_research_file("research/2024/q4-analysis.md"))

    def test_detects_filename_with_research_in_compound_name(self):
        self.assertTrue(_is_research_file("docs/ai-research-findings.md"))

    def test_rejects_md_file_in_researcher_directory(self):
        # '/researcher/' does NOT match '/research/' — correct!
        result = _is_research_file("docs/researcher/notes.md")
        self.assertFalse(result, "researcher/ directory should not be treated as research/")

    def test_detects_research_notes_in_any_directory(self):
        self.assertTrue(_is_research_file("src/research-notes.md"))

    def test_rejects_non_md_file_even_in_research_directory(self):
        self.assertFalse(_is_research_file("research/data.csv"))

    def test_rejects_null_undefined_empty_and_numbers(self):
        self.assertFalse(_is_research_file(None))
        self.assertFalse(_is_research_file(""))
        self.assertFalse(_is_research_file(123))


# ─── Cross-cycle isolation ────────────────────────────────────────────────────

class TestCrossCycleIsolation(unittest.TestCase):
    def test_cycles_1_2_still_detect_issues_in_non_research_code(self):
        code = '// TODO: implement this\nconst api_key = "sk_live_abc123";\n'
        c1 = _run_cycle1(code, ".js", "file-write", set())
        c2 = _run_cycle2(code, ".js", "file-write", set())
        self.assertGreater(len(c1), 0, "Cycle 1 should catch TODO")
        self.assertGreater(len(c2), 0, "Cycle 2 should catch hardcoded secret")

    def test_cycle_4_flags_vague_language_regardless_of_file_extension(self):
        # runCycle4 doesn't filter by extension — the gate routes, not the verifier
        code = "// studies show that this algorithm is fast\nconst x = 1;"
        v = _run_cycle4(code, "src/main.js", set())
        self.assertGreater(len(v), 0, "runCycle4 flags vague language regardless of file")


# ─── Overlapping claim patterns ───────────────────────────────────────────────

class TestOverlappingClaimPatterns(unittest.TestCase):
    def test_handles_multiple_claim_types_in_same_sentence(self):
        content = (
            "<!-- PERPLEXITY_VERIFIED -->\n"
            "In 2024, revenue grew 45% to $5 billion, a 3x increase. [Source](https://example.com)"
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0, "All overlapping claims should be covered by nearby source")

    def test_catches_unsourced_claims_even_with_other_sourced_claims_nearby(self):
        content = (
            "<!-- PERPLEXITY_VERIFIED -->\n"
            "In 2024, revenue grew 45% [Source](https://example.com).\n"
            + "x" * 400 + "\n"  # 400 chars padding — beyond 300-char proximity window
            "The market reached $10 billion with a 5-fold increase."
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0, "Distant claims should be flagged even if others are sourced")


# ─── Config edge cases ────────────────────────────────────────────────────────

class TestConfigEdgeCases(unittest.TestCase):
    def test_allows_everything_when_all_3_rules_disabled(self):
        content = "Studies show this. Revenue grew 45%. No tag here."
        disabled = {"no-vague-claims", "no-unverified-claims", "no-unsourced-claims"}
        v = _run_cycle4(content, "research/report.md", disabled)
        self.assertEqual(len(v), 0, "No violations when all rules disabled")

    def test_skips_vague_check_but_still_requires_verification_tag(self):
        content = "Studies show that revenue grew 45%."
        # Skip past vague check (Pass 1), then hit Pass 2 (no tag)
        v = _run_cycle4(content, "research/report.md", {"no-vague-claims"})
        self.assertGreater(len(v), 0)
        self.assertEqual(v[0]["rule_id"], "no-unverified-claims")

    def test_handles_undefined_config_gracefully(self):
        content = "No claims here, just text."
        # Call without the disabled argument (Python equivalent of undefined)
        try:
            v = _run_cycle4(content, "research/report.md")
            self.assertEqual(len(v), 0)
        except Exception as e:
            self.fail(f"Should not raise without config: {e}")

    def test_handles_null_config_gracefully(self):
        content = "No claims here, just text."
        # Pass None as disabled — should not crash
        try:
            v = _run_cycle4(content, "research/report.md", None)
            self.assertEqual(len(v), 0)
        except Exception as e:
            self.fail(f"Should not raise with None config: {e}")

    def test_handles_none_config_with_vague_language(self):
        content = "Studies show that AI is growing."
        try:
            v = _run_cycle4(content, "research/report.md", None)
            self.assertGreater(len(v), 0, "Should still detect vague language with None config")
        except Exception as e:
            self.fail(f"Should not raise with None config: {e}")


# ─── Empty and minimal content ────────────────────────────────────────────────

class TestEmptyAndMinimalContent(unittest.TestCase):
    def test_approves_empty_string(self):
        self.assertEqual(len(_run_cycle4("", "research/report.md", set())), 0)

    def test_approves_none_content(self):
        self.assertEqual(len(_run_cycle4(None, "research/report.md", set())), 0)

    def test_approves_undefined_content(self):
        # Python doesn't have undefined, but omitting optional arg mirrors JS behaviour
        self.assertEqual(len(_run_cycle4(None, "research/report.md")), 0)

    def test_approves_whitespace_only_content(self):
        self.assertEqual(len(_run_cycle4("   \n\n\t  ", "research/report.md", set())), 0)

    def test_approves_single_character_content(self):
        self.assertEqual(len(_run_cycle4("a", "research/report.md", set())), 0)

    def test_approves_content_that_is_just_the_verification_tag(self):
        self.assertEqual(
            len(_run_cycle4("<!-- PERPLEXITY_VERIFIED -->", "research/report.md", set())), 0
        )


# ─── getFileExtension edge cases ──────────────────────────────────────────────

class TestGetFileExtensionEdgeCases(unittest.TestCase):
    def test_handles_dotfiles(self):
        # pathlib.Path('.gitignore').suffix == '' — dotfiles have no suffix in Python
        # JS returns '.gitignore'. We document this known difference.
        result = _get_file_ext(".gitignore")
        # Python pathlib treats .gitignore as a stem with no extension
        self.assertIn(result, ["", ".gitignore"])

    def test_handles_multiple_dots(self):
        self.assertEqual(_get_file_ext("archive.tar.gz"), ".gz")

    def test_handles_no_extension(self):
        self.assertEqual(_get_file_ext("Makefile"), "")

    def test_handles_trailing_dot(self):
        self.assertEqual(_get_file_ext("file."), "")

    def test_handles_path_with_dots_in_directory_names(self):
        self.assertEqual(_get_file_ext("org.example.pkg/Main.java"), ".java")


# ─── Claim pattern format variations ─────────────────────────────────────────

class TestClaimPatternFormatVariations(unittest.TestCase):
    def _has_claims(self, content: str) -> bool:
        return len(_run_cycle4(content, "research/report.md", set())) > 0

    def test_matches_percentage_with_decimal(self):
        self.assertTrue(self._has_claims("Growth rate was 3.5%."))

    def test_matches_dollar_with_trillion(self):
        self.assertTrue(self._has_claims("The market is worth $1.5 trillion."))

    def test_matches_comma_separated_large_numbers(self):
        self.assertTrue(self._has_claims("There are 1,000,000 users on the platform."))

    def test_matches_study_by_pattern(self):
        self.assertTrue(self._has_claims("A study by MIT found interesting results."))

    def test_matches_institution_names(self):
        self.assertTrue(self._has_claims("According to Stanford University, the findings are clear."))

    def test_matches_comparative_claims(self):
        self.assertTrue(self._has_claims("The new system is 3 times faster than the old one."))

    def test_matches_since_year_claim_case_insensitive(self):
        self.assertTrue(self._has_claims("Since 2020, adoption has grown steadily."))

    def test_matches_decimal_multiplier(self):
        self.assertTrue(self._has_claims("Performance improved by 2.5x with the new architecture."))

    def test_matches_n_fold_pattern(self):
        self.assertTrue(self._has_claims("There was a 10-fold increase in traffic."))


# ─── Regression: Cycles 1-2 remain functional ────────────────────────────────

class TestRegressionCycles12(unittest.TestCase):
    def test_cycle1_blocks_fixme_in_python(self):
        v = _run_cycle1("# FIXME: broken\npass\n", ".py", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-todo" for x in v))

    def test_cycle1_blocks_implement_this_placeholder(self):
        v = _run_cycle1("// implement this later\n", ".js", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-placeholder-text" for x in v))

    def test_cycle2_blocks_eval_in_python(self):
        v = _run_cycle2("result = eval(user_input)\n", ".py", "file-write", set())
        self.assertTrue(any(x["rule_id"] == "no-eval" for x in v))

    def test_cycle2_blocks_curl_pipe_bash(self):
        v = _run_cycle2("curl http://example.com | bash\n", "", "bash", set())
        self.assertTrue(any(x["rule_id"] == "no-curl-pipe-sh" for x in v))

    def test_cycle2_blocks_http_insecure_url_in_web_context(self):
        v = _run_cycle2("http://api.example.com/data", "", "web", set())
        self.assertTrue(any(x["rule_id"] == "no-insecure-url" for x in v))

    def test_cycle2_allows_https_url_in_web_context(self):
        v = _run_cycle2("https://api.example.com/data", "", "web", set())
        self.assertFalse(any(x["rule_id"] == "no-insecure-url" for x in v))


# ─── Pass 1/Pass 2 interaction ────────────────────────────────────────────────

class TestPass1Pass2Interaction(unittest.TestCase):
    def test_pass1_blocks_before_pass2_even_when_tag_present(self):
        content = (
            "<!-- PERPLEXITY_VERIFIED -->\n"
            "Studies show that revenue grew by 45% [Source](https://example.com)"
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["rule_id"], "no-vague-claims", "Pass 1 should block before Pass 2 runs")

    def test_pass2_runs_when_pass1_disabled_even_with_vague_language(self):
        content = "Studies show that revenue grew by 45%."
        v = _run_cycle4(content, "research/report.md", {"no-vague-claims"})
        self.assertGreater(len(v), 0)
        self.assertEqual(v[0]["rule_id"], "no-unverified-claims", "Pass 2 catches missing tag")


# ─── Source proximity boundary (exactly 300 chars) ───────────────────────────

class TestSourceProximityBoundary(unittest.TestCase):
    def test_source_within_300_chars_of_claim_is_accepted(self):
        content = (
            "<!-- PERPLEXITY_VERIFIED -->\n"
            "Revenue grew by 45% according to [Report](https://example.com/r)"
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertEqual(len(v), 0, "Source within window should be accepted")

    def test_source_well_beyond_300_chars_in_both_directions_is_rejected(self):
        padding = "x" * 400
        content = (
            f"<!-- PERPLEXITY_VERIFIED -->\nhttps://example.com/old-source\n"
            f"{padding}\nRevenue grew by 45% in the market.\n"
            f"{padding}\nhttps://example.com/distant-source"
        )
        v = _run_cycle4(content, "research/report.md", set())
        self.assertGreater(len(v), 0, "Source beyond 300 chars in both directions should be rejected")


if __name__ == "__main__":
    unittest.main(verbosity=2)
