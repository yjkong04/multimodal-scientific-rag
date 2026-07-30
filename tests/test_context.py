"""Context assembler tests. Pure/offline."""

from api.context import assemble_context, sections_covered
from api.schemas import Citation, Modality


def _t(sid, section, snippet, score, paper="P1"):
    return Citation(
        modality=Modality.TEXT, paper_id=paper, source_id=sid, section=section, snippet=snippet, score=score
    )


def _f(sid, snippet, score, label="Figure 1", paper="P1"):
    return Citation(
        modality=Modality.FIGURE, paper_id=paper, source_id=sid, section=None,
        figure_label=label, snippet=snippet, score=score,
    )


def test_dedupe_by_source_id():
    out = assemble_context([_t("c1", "M", "x", 0.9), _t("c1", "M", "x", 0.9)], per_section_cap=5)
    assert len([c for c in out if c.modality == Modality.TEXT]) == 1


def test_section_diversity_cap():
    cites = [_t(f"m{i}", "Methods", f"text{i}", 0.9 - i * 0.01) for i in range(4)]
    cites.append(_t("r0", "Results", "res", 0.5))
    out = assemble_context(cites, per_section_cap=2, char_budget=100000)
    assert len([c for c in out if c.section == "Methods"]) == 2
    assert len([c for c in out if c.section == "Results"]) == 1


def test_char_budget_truncates_but_keeps_one():
    cites = [_t(f"c{i}", f"S{i}", "x" * 100, 0.9 - i * 0.01) for i in range(10)]
    out = assemble_context(cites, char_budget=250, per_section_cap=5)
    text = [c for c in out if c.modality == Modality.TEXT]
    assert 1 <= len(text) <= 3


def test_figures_capped():
    out = assemble_context([_f(f"f{i}", "cap", 0.8 - i * 0.01) for i in range(5)], max_figures=3)
    assert len([c for c in out if c.modality == Modality.FIGURE]) == 3


def test_result_is_score_sorted():
    out = assemble_context([_t("c1", "A", "x", 0.3), _t("c2", "B", "y", 0.9)], per_section_cap=5)
    assert [c.score for c in out] == sorted([c.score for c in out], reverse=True)


def test_sections_covered_counts_distinct():
    cites = [_t("c1", "Methods", "x", 0.9), _t("c2", "Results", "y", 0.8), _t("c3", "Methods", "z", 0.7)]
    assert sections_covered(cites) == 2
