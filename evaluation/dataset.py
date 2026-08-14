"""The held-out evaluation set: questions with gold source ids.

An `EvalCase` pairs a question with the source ids that *should* ground its
answer (`gold_source_ids`) and whether the corpus can answer it at all
(`answerable`). Unanswerable cases have no gold ids and exist to test the
refusal path — the system should decline, not hallucinate.

Two ways to get cases:

- `load_cases(path)` reads a JSONL file (one case per line). This is how the
  real, corpus-specific sets are stored (see `datasets/`).
- `demo_cases()` returns a built-in set over the `DEMO-0001` demo corpus so the
  harness runs end to end with no database. The unanswerable questions are
  deliberately worded to share no term with the demo corpus, so the demo run is
  an honest showcase of the refusal path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvalCase:
    question: str
    # Source ids (chunk id / figure id) that should ground the answer. Empty for
    # unanswerable cases.
    gold_source_ids: tuple[str, ...] = ()
    # False = the corpus cannot support an answer; the system should refuse.
    answerable: bool = True
    notes: str = ""

    def __post_init__(self) -> None:
        # An answerable case needs at least one gold source to score retrieval
        # against; an unanswerable one must have none, or the metrics lie.
        if self.answerable and not self.gold_source_ids:
            raise ValueError(f"answerable case has no gold source ids: {self.question!r}")
        if not self.answerable and self.gold_source_ids:
            raise ValueError(f"unanswerable case has gold source ids: {self.question!r}")


def _case_from_dict(d: dict) -> EvalCase:
    return EvalCase(
        question=d["question"],
        gold_source_ids=tuple(d.get("gold_source_ids", ())),
        answerable=d.get("answerable", bool(d.get("gold_source_ids"))),
        notes=d.get("notes", ""),
    )


def load_cases(path: str | Path) -> list[EvalCase]:
    """Load eval cases from a JSONL file (one JSON object per non-blank line)."""
    cases: list[EvalCase] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cases.append(_case_from_dict(json.loads(line)))
    return cases


def demo_cases() -> list[EvalCase]:
    """Built-in cases over the `DEMO-0001` corpus in `api/store.py`.

    Ids must match `_demo_records()`: c1 (Methods), c2 (Results),
    c3 (Discussion), fig3 (Figure 3, Results).
    """
    pid = "DEMO-0001"
    return [
        EvalCase(
            question="How was response measured across the dose series?",
            gold_source_ids=(f"{pid}:c1",),
            notes="Methods passage describes the assay + triplicate design.",
        ),
        EvalCase(
            question="What happens to the response as the dose increases?",
            gold_source_ids=(f"{pid}:c2", f"{pid}:fig3"),
            notes="Rises then plateaus; supported by Results text and Figure 3.",
        ),
        EvalCase(
            question="Is the plateau at higher doses due to toxicity or target saturation?",
            gold_source_ids=(f"{pid}:c3",),
            notes="Discussion attributes the plateau to saturation, not toxicity.",
        ),
        EvalCase(
            question="What does Figure 3 show about dose and response?",
            gold_source_ids=(f"{pid}:fig3",),
            notes="Direct figure question.",
        ),
        EvalCase(
            question="Which antibiotic prevents neonatal infection?",
            answerable=False,
            notes="Off-corpus; zero term overlap so the demo store retrieves nothing.",
        ),
        EvalCase(
            question="Do older adults report improved sleep quality?",
            answerable=False,
            notes="Off-corpus; should refuse rather than guess.",
        ),
    ]
