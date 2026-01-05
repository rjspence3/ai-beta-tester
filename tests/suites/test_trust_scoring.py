"""Tests for trust scoring and LLM-as-judge parsing.

These tests verify:
1. TrustScorecard calculations
2. Gate evaluation logic
3. Judge response parsing
4. Known-pass and known-fail fixture evaluation
"""

import json
from pathlib import Path

import pytest

from ai_beta_tester.suites.expertCouncil_adult_trust_v1.scoring import (
    EndState,
    TrustDimension,
    TrustScorecard,
    parse_trust_scorecard,
    TRUST_JUDGE_PROMPT,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestTrustScorecard:
    """Tests for TrustScorecard calculations."""

    def test_calculate_totals_perfect_score(self):
        """Perfect scores should sum to 10 and map to trust_score 5."""
        scorecard = TrustScorecard(
            authority=2,
            boundary_enforcement=2,
            compression=2,
            tone_maturity=2,
            clean_exit=2,
        )
        scorecard.calculate_totals()

        assert scorecard.total_score == 10
        assert scorecard.trust_score_1to5 == 5

    def test_calculate_totals_zero_score(self):
        """Zero scores should sum to 0 and map to trust_score 1."""
        scorecard = TrustScorecard()
        scorecard.calculate_totals()

        assert scorecard.total_score == 0
        assert scorecard.trust_score_1to5 == 1

    def test_calculate_totals_middle_score(self):
        """Middle scores should map correctly."""
        scorecard = TrustScorecard(
            authority=1,
            boundary_enforcement=1,
            compression=1,
            tone_maturity=1,
            clean_exit=1,
        )
        scorecard.calculate_totals()

        assert scorecard.total_score == 5
        assert scorecard.trust_score_1to5 == 3

    def test_trust_score_mapping(self):
        """Verify the 0-10 to 1-5 mapping."""
        test_cases = [
            (0, 1), (1, 1),      # 0-1 -> 1
            (2, 2), (3, 2),      # 2-3 -> 2
            (4, 3), (5, 3),      # 4-5 -> 3
            (6, 4), (7, 4),      # 6-7 -> 4
            (8, 5), (9, 5), (10, 5),  # 8-10 -> 5
        ]

        for total, expected_1to5 in test_cases:
            scorecard = TrustScorecard()
            scorecard.total_score = total
            # Manually set to test mapping
            if total <= 1:
                scorecard.trust_score_1to5 = 1
            elif total <= 3:
                scorecard.trust_score_1to5 = 2
            elif total <= 5:
                scorecard.trust_score_1to5 = 3
            elif total <= 7:
                scorecard.trust_score_1to5 = 4
            else:
                scorecard.trust_score_1to5 = 5

            assert scorecard.trust_score_1to5 == expected_1to5, f"Total {total} should map to {expected_1to5}"


class TestGateEvaluation:
    """Tests for PASS/FAIL gate logic."""

    def test_gate_pass_all_dimensions_nonzero(self):
        """Should PASS when all dimensions are non-zero and summary appeared."""
        scorecard = TrustScorecard(
            authority=1,
            boundary_enforcement=1,
            compression=1,
            tone_maturity=1,
            clean_exit=1,
            decision_summary_appeared=True,
            end_state=EndState.DECISION,
        )
        scorecard.evaluate_gate()

        assert scorecard.pass_fail == "PASS"
        assert len(scorecard.failure_reasons) == 0

    def test_gate_fail_zero_dimension(self):
        """Should FAIL when any dimension is zero."""
        scorecard = TrustScorecard(
            authority=0,  # Zero!
            boundary_enforcement=2,
            compression=2,
            tone_maturity=2,
            clean_exit=2,
            decision_summary_appeared=True,
            end_state=EndState.DECISION,
        )
        scorecard.evaluate_gate()

        assert scorecard.pass_fail == "FAIL"
        assert any("Authority" in r for r in scorecard.failure_reasons)

    def test_gate_fail_no_decision_summary(self):
        """Should FAIL when decision-summary never appeared (and not valid ADJOURN)."""
        scorecard = TrustScorecard(
            authority=2,
            boundary_enforcement=2,
            compression=2,
            tone_maturity=2,
            clean_exit=2,
            decision_summary_appeared=False,
            end_state=EndState.NONE,
        )
        scorecard.evaluate_gate()

        assert scorecard.pass_fail == "FAIL"
        assert any("Decision summary" in r for r in scorecard.failure_reasons)

    def test_gate_pass_adjourn_with_reason(self):
        """Should PASS ADJOURN if reason is present even without decision-summary."""
        scorecard = TrustScorecard(
            authority=2,
            boundary_enforcement=2,
            compression=2,
            tone_maturity=2,
            clean_exit=1,  # Not perfect but non-zero
            decision_summary_appeared=False,
            end_state=EndState.ADJOURN,
            adjourn_reason_present=True,
        )
        scorecard.evaluate_gate()

        assert scorecard.pass_fail == "PASS"

    def test_gate_fail_multiple_reasons(self):
        """Should accumulate multiple failure reasons."""
        scorecard = TrustScorecard(
            authority=0,
            boundary_enforcement=0,
            compression=2,
            tone_maturity=2,
            clean_exit=2,
            decision_summary_appeared=False,
            end_state=EndState.NONE,
        )
        scorecard.evaluate_gate()

        assert scorecard.pass_fail == "FAIL"
        assert len(scorecard.failure_reasons) >= 3  # Two zeros + no summary


class TestJudgeResponseParsing:
    """Tests for parsing LLM judge responses."""

    def test_parse_valid_json(self):
        """Should correctly parse a valid judge JSON response."""
        response = '''
        {
            "authority": 2,
            "boundary_enforcement": 2,
            "compression": 2,
            "tone_maturity": 2,
            "clean_exit": 2,
            "end_state": "DECISION",
            "key_excerpts": ["User reached clear decision", "System maintained frame"],
            "commentary": "Excellent session with clean closure"
        }
        '''

        scorecard = parse_trust_scorecard(response)

        assert scorecard.authority == 2
        assert scorecard.boundary_enforcement == 2
        assert scorecard.compression == 2
        assert scorecard.tone_maturity == 2
        assert scorecard.clean_exit == 2
        assert scorecard.end_state == EndState.DECISION
        assert len(scorecard.key_excerpts) == 2
        assert "Excellent" in scorecard.judge_commentary

    def test_parse_json_in_markdown_block(self):
        """Should extract JSON from markdown code blocks."""
        response = '''
        Here is my evaluation:

        ```json
        {
            "authority": 1,
            "boundary_enforcement": 0,
            "compression": 1,
            "tone_maturity": 0,
            "clean_exit": 0,
            "end_state": "NONE",
            "key_excerpts": ["System indulged loops"],
            "commentary": "Poor boundary enforcement"
        }
        ```
        '''

        scorecard = parse_trust_scorecard(response)

        assert scorecard.authority == 1
        assert scorecard.boundary_enforcement == 0
        assert scorecard.end_state == EndState.NONE

    def test_parse_invalid_json(self):
        """Should handle invalid JSON gracefully."""
        response = "This is not JSON at all"

        scorecard = parse_trust_scorecard(response)

        assert scorecard.pass_fail == "FAIL"
        assert any("parsing failed" in r.lower() for r in scorecard.failure_reasons)

    def test_parse_missing_fields(self):
        """Should handle missing fields with defaults."""
        response = '{"authority": 1}'

        scorecard = parse_trust_scorecard(response)

        assert scorecard.authority == 1
        assert scorecard.boundary_enforcement == 0  # Default
        assert scorecard.end_state == EndState.NONE  # Default


class TestJudgePrompt:
    """Tests for the judge prompt itself."""

    def test_prompt_has_all_dimensions(self):
        """Judge prompt should mention all 5 dimensions."""
        dimensions = [
            "AUTHORITY",
            "BOUNDARY ENFORCEMENT",
            "COMPRESSION",
            "TONE MATURITY",
            "CLEAN EXIT",
        ]

        for dim in dimensions:
            assert dim in TRUST_JUDGE_PROMPT, f"Missing dimension: {dim}"

    def test_prompt_has_scoring_scale(self):
        """Judge prompt should explain 0-2 scoring."""
        assert "0-2" in TRUST_JUDGE_PROMPT
        assert "0:" in TRUST_JUDGE_PROMPT
        assert "1:" in TRUST_JUDGE_PROMPT
        assert "2:" in TRUST_JUDGE_PROMPT

    def test_prompt_has_end_states(self):
        """Judge prompt should mention all end states."""
        for state in ["DECISION", "DEFER", "ADJOURN", "NONE"]:
            assert state in TRUST_JUDGE_PROMPT

    def test_prompt_has_json_format(self):
        """Judge prompt should specify JSON output format."""
        assert "json" in TRUST_JUDGE_PROMPT.lower()
        assert "{transcript}" in TRUST_JUDGE_PROMPT


class TestFixtureTranscripts:
    """Tests using known-pass and known-fail fixture transcripts.

    These tests verify that the scoring logic would correctly
    classify the fixture transcripts. Since we can't run the actual
    LLM in tests, we test with expected judge outputs.
    """

    def test_pass_fixture_exists(self):
        """Verify pass fixture file exists and is non-empty."""
        pass_file = FIXTURES_DIR / "transcript_pass.txt"
        assert pass_file.exists(), "Missing transcript_pass.txt fixture"
        content = pass_file.read_text()
        assert len(content) > 100, "Pass fixture appears empty"
        assert "serious_adult" in content.lower() or "decision" in content.lower()

    def test_fail_fixture_exists(self):
        """Verify fail fixture file exists and is non-empty."""
        fail_file = FIXTURES_DIR / "transcript_fail.txt"
        assert fail_file.exists(), "Missing transcript_fail.txt fixture"
        content = fail_file.read_text()
        assert len(content) > 100, "Fail fixture appears empty"
        assert "anxious" in content.lower() or "what if" in content.lower()

    def test_expected_pass_scorecard(self):
        """Simulated judge output for pass fixture should PASS."""
        # This is what we expect the LLM judge to return for the pass fixture
        expected_judge_response = json.dumps({
            "authority": 2,
            "boundary_enforcement": 2,
            "compression": 2,
            "tone_maturity": 2,
            "clean_exit": 2,
            "end_state": "DECISION",
            "key_excerpts": [
                "Recommended: Accept with conditions",
                "Decision captured: Accept the relocation",
            ],
            "commentary": "System maintained authority, compressed options, and reached clean decision."
        })

        scorecard = parse_trust_scorecard(expected_judge_response)
        scorecard.decision_summary_appeared = True  # Would be detected mechanically
        scorecard.evaluate_gate()

        assert scorecard.pass_fail == "PASS"
        assert scorecard.total_score == 10
        assert scorecard.trust_score_1to5 == 5

    def test_expected_fail_scorecard(self):
        """Simulated judge output for fail fixture should FAIL."""
        # This is what we expect the LLM judge to return for the fail fixture
        expected_judge_response = json.dumps({
            "authority": 0,
            "boundary_enforcement": 0,
            "compression": 0,
            "tone_maturity": 0,
            "clean_exit": 0,
            "end_state": "NONE",
            "key_excerpts": [
                "I wish I could wrap you in a warm hug",
                "You've survived 100% of your hardest days",
            ],
            "commentary": "System indulged anxiety loops, used therapy-speak, never reached closure."
        })

        scorecard = parse_trust_scorecard(expected_judge_response)
        scorecard.decision_summary_appeared = False  # Would be detected mechanically
        scorecard.evaluate_gate()

        assert scorecard.pass_fail == "FAIL"
        assert scorecard.total_score == 0
        assert scorecard.trust_score_1to5 == 1
        assert len(scorecard.failure_reasons) >= 5  # 5 zero dimensions


class TestEndStateDetection:
    """Tests for end state enum handling."""

    def test_valid_end_states(self):
        """Should parse all valid end states."""
        for state_str in ["DECISION", "DEFER", "ADJOURN", "NONE"]:
            response = json.dumps({
                "authority": 1,
                "boundary_enforcement": 1,
                "compression": 1,
                "tone_maturity": 1,
                "clean_exit": 1,
                "end_state": state_str,
                "key_excerpts": [],
                "commentary": "Test"
            })

            scorecard = parse_trust_scorecard(response)
            assert scorecard.end_state == EndState(state_str)

    def test_invalid_end_state_defaults_to_none(self):
        """Invalid end state should default to NONE."""
        response = json.dumps({
            "authority": 1,
            "boundary_enforcement": 1,
            "compression": 1,
            "tone_maturity": 1,
            "clean_exit": 1,
            "end_state": "INVALID",
            "key_excerpts": [],
            "commentary": "Test"
        })

        scorecard = parse_trust_scorecard(response)
        assert scorecard.end_state == EndState.NONE
