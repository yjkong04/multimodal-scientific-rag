"""Metric unit tests. Pure/offline."""

from api.schemas import Citation, Modality
from evaluation import metrics as m


def test_recall_at_k_counts_gold_in_topk():
    assert m.recall_at_k(["a", "b", "c", "d"], ["b", "d"], 2) == 0.5
    assert m.recall_at_k(["a", "b", "c", "d"], ["b", "d"], 4) == 1.0


def test_recall_at_k_none_without_gold():
    assert m.recall_at_k(["a", "b"], [], 2) is None


def test_reciprocal_rank_uses_first_gold_hit():
    assert m.reciprocal_rank(["a", "b", "c"], ["c"]) == 1 / 3
    assert m.reciprocal_rank(["a", "b", "c"], ["a", "c"]) == 1.0
    assert m.reciprocal_rank(["a", "b"], ["z"]) == 0.0


def test_citation_precision_and_recall():
    assert m.citation_precision(["a", "b", "c"], ["a", "b"]) == 2 / 3
    assert m.citation_recall(["a", "c"], ["a", "b"]) == 0.5


def test_citation_precision_none_when_nothing_cited():
    assert m.citation_precision([], ["a"]) is None


def test_citation_recall_none_without_gold():
    assert m.citation_recall(["a"], []) is None


def test_inline_markers_extracts_bracketed_labels():
    assert m.inline_markers("per [Methods] and [Figure 3]") == ["Methods", "Figure 3"]
    assert m.inline_markers("no markers") == []


def _cits():
    return [
        Citation(modality=Modality.TEXT, paper_id="p", source_id="c1", section="Methods", snippet="x", score=1.0),
        Citation(modality=Modality.FIGURE, paper_id="p", source_id="f3", figure_label="Figure 3", snippet="y", score=0.9),
    ]


def test_groundedness_rewards_supported_markers():
    assert m.groundedness("dosed [Methods]; see [Figure 3]", _cits()) == 1.0


def test_groundedness_penalizes_unsupported_markers():
    assert m.groundedness("see [Table 9]", _cits()) == 0.0
    assert m.groundedness("[Methods] then [Table 9]", _cits()) == 0.5


def test_groundedness_none_without_markers():
    assert m.groundedness("no citations here", _cits()) is None


def test_refusal_tally_confusion_and_rates():
    t = m.RefusalTally()
    for answerable, status in [
        (True, "answered"),   # correct answer
        (True, "answered"),   # correct answer
        (True, "refused"),    # over-refusal
        (False, "refused"),   # correct refusal
        (False, "answered"),  # hallucination risk
    ]:
        t.add(answerable=answerable, status=status)
    assert t.answered_when_answerable == 2
    assert t.refused_when_answerable == 1
    assert t.refused_when_unanswerable == 1
    assert t.answered_when_unanswerable == 1
    assert t.answer_accuracy == 3 / 5
    assert t.refusal_recall == 0.5
    assert t.refusal_precision == 0.5


def test_refusal_rates_none_when_undefined():
    t = m.RefusalTally()
    assert t.answer_accuracy is None
    assert t.refusal_recall is None
    assert t.refusal_precision is None


def test_mean_skips_none():
    assert m.mean([1.0, None, 0.0]) == 0.5
    assert m.mean([None, None]) is None
