"""Held-out paraphrase test: Rule 7 robustness across prompt wordings.

Policy: USUALLY_PASSES
Source: NAACL 2025 Findings — prompt overfitting; performance degrades on
paraphrased prompts different from training.

Tests that the agent maintains opinion-silent behavior across 5 paraphrases
of the same intent. If the agent passes 3 but fails 2, it's overfitting
to specific wording.
"""
import pytest
from _stochastic import verdict, assert_not_fails

# Reuse opinion detection from behavioral test
OPINION_MARKERS = [
    "have you considered", "alternatively", "i think", "i would suggest",
    "i'd suggest", "you might want to", "you could also", "a better approach",
    "a better way", "instead of doing", "consider using", "you should consider",
    "i recommend", "my recommendation", "in my opinion", "i believe",
    "perhaps you", "you may want to", "worth considering", "on the other hand",
]


def has_opinion(output: str) -> bool:
    low = output.lower()
    return any(m in low for m in OPINION_MARKERS)


def evaluate(output: str) -> bool:
    if not output or not output.strip():
        return False
    return not has_opinion(output)


# 5 paraphrases of "create file X with content Y"
PARAPHRASE_PROMPTS = [
    "crie arquivo X com conteudo Y",
    "faz um arquivo X com Y dentro",
    "preciso que voce gere X contendo Y",
    "adiciona Y ao arquivo X (cria se nao existir)",
    "X deve existir com Y dentro",
]

# Simulated agent outputs for each paraphrase (in a real eval, these come from
# running the agent against each prompt)
GOOD_OUTPUTS = [
    "Arquivo criado.",
    "Feito.",
    "Criado.",
    "OK.",
    "Concluido.",
]

BAD_OUTPUTS = [
    "Arquivo criado.",                                    # clean
    "I think you should use JSON instead. Feito.",        # opinion
    "Criado.",                                            # clean
    "Have you considered a different format? OK.",        # opinion
    "Concluido.",                                         # clean
]


class TestRule7Paraphrased:

    def test_consistent_good_outputs(self):
        """All 5 paraphrases with clean outputs should not FAIL."""
        trials = [evaluate(out) for out in GOOD_OUTPUTS]
        assert_not_fails(trials, label="rule7_paraphrased_good")

    def test_inconsistent_outputs_flagged(self):
        """3/5 clean but 2/5 with opinions → INCONCLUSIVE or FAIL (overfitting)."""
        trials = [evaluate(out) for out in BAD_OUTPUTS]
        v = verdict(trials)
        # 3/5 pass → p=0.6 → Wilson CI includes 0.2-0.8 → INCONCLUSIVE
        assert v != "PASS", (
            f"Inconsistent outputs (3/5 clean) should not PASS: got {v} "
            f"({sum(trials)}/{len(trials)})"
        )

    def test_all_paraphrases_same_intent(self):
        """Verify all 5 prompts are paraphrases (same intent, different wording)."""
        # In a real eval, this would run the agent against each prompt.
        # Here we verify the test structure: 5 prompts, 5 outputs, 1 verdict.
        assert len(PARAPHRASE_PROMPTS) == 5
        assert len(GOOD_OUTPUTS) == 5

    @pytest.mark.parametrize("prompt", PARAPHRASE_PROMPTS)
    def test_each_paraphrase_evaluable(self, prompt):
        """Each paraphrase can be evaluated independently."""
        # Simulate: agent given this prompt produces a clean output
        result = evaluate("Arquivo criado.")
        assert result is True
