"""Harness integration tests over the demo store. Offline (hashing embedder)."""

from api.generation import ExtractiveGenerator
from api.store import DemoStore
from evaluation import report as report_mod
from evaluation.dataset import demo_cases, load_cases
from evaluation.harness import evaluate

CASES = demo_cases()
STORE = DemoStore()
GEN = ExtractiveGenerator()


def _report():
    return evaluate(STORE, GEN, CASES)


def test_answerable_cases_answered_unanswerable_refused():
    rep = _report()
    by_q = {r.case.question: r for r in rep.results}
    for r in rep.results:
        if r.case.answerable:
            assert r.status == "answered", r.case.question
        else:
            assert r.status == "refused", r.case.question
    assert len(by_q) == len(CASES)


def test_retrieval_finds_gold_in_tiny_corpus():
    rep = _report()
    # The demo corpus is small enough that every gold source is retrieved.
    assert rep.recall_at_k == 1.0
    # First gold hit is rank 1 for 3 of 4 answerable cases, rank 2 for one.
    assert rep.mrr == (0.5 + 1.0 + 1.0 + 1.0) / 4


def test_refusal_is_perfect_on_demo_set():
    rep = _report()
    assert rep.refusal.refusal_recall == 1.0
    assert rep.refusal.answer_accuracy == 1.0


def test_extractive_has_no_inline_groundedness():
    # The extractive baseline emits no [markers]; groundedness is undefined and
    # the model is judged on citation precision/recall instead.
    rep = _report()
    assert rep.groundedness is None
    assert rep.citation_recall == 1.0


def test_report_to_dict_is_json_shaped():
    rep = _report()
    d = report_mod.to_dict(rep)
    assert d["backend"] == "demo"
    assert d["cases"] == len(CASES)
    assert set(d["aggregate"]) >= {"recall_at_k", "mrr", "answer_accuracy"}
    assert len(d["results"]) == len(CASES)


def test_jsonl_dataset_matches_builtin_demo_set():
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "evaluation" / "datasets" / "demo_eval.jsonl"
    loaded = load_cases(path)
    assert [c.question for c in loaded] == [c.question for c in CASES]
    assert [c.gold_source_ids for c in loaded] == [c.gold_source_ids for c in CASES]
