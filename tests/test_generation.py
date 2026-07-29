"""Generator tests. Pure/offline — the extractive path and the pipeline wiring.

The qwen-vision path needs a downloaded model, so it isn't unit-tested here;
these lock in the interface, the extractive fallback, and the refusal contract.
"""

import pytest

from api.generation import ExtractiveGenerator, build_generator
from api.pipeline import answer_question
from api.schemas import AskRequest, Citation, Modality
from api.store import DemoStore


def _cite(modality, snippet, label=None):
    return Citation(
        modality=modality, paper_id="P", source_id="s", snippet=snippet, score=1.0, figure_label=label
    )


def test_extractive_uses_text_and_figure():
    out = ExtractiveGenerator().generate(
        "q", [_cite(Modality.TEXT, "dose rises"), _cite(Modality.FIGURE, "a curve", "Figure 3")]
    )
    assert "dose rises" in out and "Figure 3" in out


def test_extractive_empty_citations_returns_empty():
    assert ExtractiveGenerator().generate("q", []) == ""


def test_build_generator_extractive():
    assert isinstance(build_generator("extractive", "m"), ExtractiveGenerator)


def test_build_generator_unknown_raises():
    with pytest.raises(ValueError):
        build_generator("nope", "m")


class _Refusing:
    def generate(self, q, citations):
        return ""


class _Answering:
    def generate(self, q, citations):
        return "grounded answer"


def test_pipeline_refuses_when_generator_cant_ground():
    # Citations exist, but the generator returns empty -> refuse, drop citations.
    req = AskRequest(question="What does the figure show about dose and response?")
    resp = answer_question(req, DemoStore(), _Refusing())
    assert resp.status == "refused"
    assert resp.citations == []


def test_pipeline_answers_and_attaches_citations():
    req = AskRequest(question="What does the figure show about dose and response?")
    resp = answer_question(req, DemoStore(), _Answering())
    assert resp.status == "answered"
    assert resp.answer == "grounded answer"
    assert resp.citations
