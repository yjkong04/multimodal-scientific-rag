"""Render an `EvalReport` as text, a Markdown table, or JSON.

Kept separate from scoring so the harness never has to know how results are
shown, and so the sweep can drop several reports into one comparison table.
"""

from __future__ import annotations

from .harness import EvalReport


def _pct(value: float | None) -> str:
    return "  n/a" if value is None else f"{value * 100:5.1f}"


def summary_row(report: EvalReport) -> dict[str, str]:
    """The one-line aggregate metrics for a report, as display strings."""
    ref = report.refusal
    return {
        "backend": report.backend,
        "generator": report.generator,
        f"recall@{report.k}": _pct(report.recall_at_k),
        "mrr": _pct(report.mrr),
        "cite_p": _pct(report.citation_precision),
        "cite_r": _pct(report.citation_recall),
        "grounded": _pct(report.groundedness),
        "refuse_r": _pct(ref.refusal_recall),
        "answer_acc": _pct(ref.answer_accuracy),
    }


def to_markdown(report: EvalReport, *, per_case: bool = True) -> str:
    """Full report: aggregate table + optional per-case breakdown."""
    row = summary_row(report)
    lines = [
        f"# Evaluation — {report.backend} / {report.generator}",
        "",
        f"Cases: {len(report.results)}  ·  k = {report.k}  (percentages)",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| recall@{report.k} | {row[f'recall@{report.k}'].strip()} |",
        f"| MRR | {row['mrr'].strip()} |",
        f"| citation precision | {row['cite_p'].strip()} |",
        f"| citation recall | {row['cite_r'].strip()} |",
        f"| groundedness | {row['grounded'].strip()} |",
        f"| refusal recall | {row['refuse_r'].strip()} |",
        f"| answer accuracy | {row['answer_acc'].strip()} |",
    ]

    if per_case:
        lines += [
            "",
            "| question | ans? | status | recall | rr | cite_p | grounded |",
            "| --- | :-: | :-: | ---: | ---: | ---: | ---: |",
        ]
        for r in report.results:
            q = r.case.question if len(r.case.question) <= 48 else r.case.question[:45] + "..."
            lines.append(
                f"| {q} | {'Y' if r.case.answerable else 'N'} | {r.status} "
                f"| {_pct(r.recall_at_k).strip()} | {r.reciprocal_rank:.2f} "
                f"| {_pct(r.citation_precision).strip()} | {_pct(r.groundedness).strip()} |"
            )
    return "\n".join(lines)


def to_text(report: EvalReport) -> str:
    """Compact console summary."""
    row = summary_row(report)
    ordered = [
        f"recall@{report.k}",
        "mrr",
        "cite_p",
        "cite_r",
        "grounded",
        "refuse_r",
        "answer_acc",
    ]
    head = f"{report.backend}/{report.generator}  ({len(report.results)} cases)"
    body = "  ".join(f"{key}={row[key].strip()}" for key in ordered)
    return f"{head}\n  {body}"


def to_dict(report: EvalReport) -> dict:
    """JSON-serializable view: aggregates + per-case rows."""
    ref = report.refusal
    return {
        "backend": report.backend,
        "generator": report.generator,
        "k": report.k,
        "cases": len(report.results),
        "aggregate": {
            "recall_at_k": report.recall_at_k,
            "mrr": report.mrr,
            "citation_precision": report.citation_precision,
            "citation_recall": report.citation_recall,
            "groundedness": report.groundedness,
            "refusal_recall": ref.refusal_recall,
            "refusal_precision": ref.refusal_precision,
            "answer_accuracy": ref.answer_accuracy,
        },
        "refusal_tally": {
            "answered_when_answerable": ref.answered_when_answerable,
            "refused_when_answerable": ref.refused_when_answerable,
            "refused_when_unanswerable": ref.refused_when_unanswerable,
            "answered_when_unanswerable": ref.answered_when_unanswerable,
        },
        "results": [
            {
                "question": r.case.question,
                "answerable": r.case.answerable,
                "status": r.status,
                "gold_source_ids": list(r.case.gold_source_ids),
                "retrieved_ids": r.retrieved_ids,
                "cited_ids": r.cited_ids,
                "recall_at_k": r.recall_at_k,
                "reciprocal_rank": r.reciprocal_rank,
                "citation_precision": r.citation_precision,
                "citation_recall": r.citation_recall,
                "groundedness": r.groundedness,
            }
            for r in report.results
        ],
    }
