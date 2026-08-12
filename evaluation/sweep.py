"""Score several generators on the same store + cases, side by side.

This is what drives the VLM comparison: retrieval is identical across
generators (same store, same cases), so it's reported once; what differs is how
each model grounds and when it refuses. Adding a new candidate VLM is a one-line
`GeneratorSpec` once its `Generator` subclass is registered in
`api.generation.build_generator`.
"""

from __future__ import annotations

from dataclasses import dataclass

from api.generation import build_generator
from api.store import Store

from .dataset import EvalCase
from .harness import EvalReport, evaluate
from .report import _pct, summary_row


@dataclass
class GeneratorSpec:
    label: str  # display name in the comparison table
    kind: str  # a kind understood by api.generation.build_generator
    model_name: str = ""  # HF id for vision kinds; unused for extractive


def default_specs() -> list[GeneratorSpec]:
    """The candidate line-up. Only the baseline runs without a GPU + ML deps;
    the vision rows are built lazily and skipped if their deps/models are absent.
    """
    return [
        GeneratorSpec(label="extractive (baseline)", kind="extractive"),
        GeneratorSpec(label="qwen2.5-vl-3b", kind="qwen-vision", model_name="Qwen/Qwen2.5-VL-3B-Instruct"),
        GeneratorSpec(label="qwen2.5-vl-7b", kind="qwen-vision", model_name="Qwen/Qwen2.5-VL-7B-Instruct"),
    ]


def run_sweep(
    store: Store,
    specs: list[GeneratorSpec],
    cases: list[EvalCase],
    *,
    k_text: int = 4,
    k_figures: int = 2,
) -> list[EvalReport]:
    """Evaluate each spec. A spec whose generator can't be built (missing deps
    or model) is skipped with a note rather than aborting the whole sweep.
    """
    reports: list[EvalReport] = []
    for spec in specs:
        try:
            generator = build_generator(spec.kind, spec.model_name)
        except Exception as exc:  # noqa: BLE001 — surface why a candidate was skipped
            print(f"  skipped {spec.label}: {type(exc).__name__}: {exc}")
            continue
        report = evaluate(store, generator, cases, k_text=k_text, k_figures=k_figures)
        report.generator = spec.label  # display the friendly label, not the class name
        reports.append(report)
    return reports


def comparison_markdown(reports: list[EvalReport], *, title: str = "VLM comparison") -> str:
    """Retrieval reported once, then a generation/refusal row per generator."""
    if not reports:
        return f"# {title}\n\n(no generators ran)"

    first = reports[0]
    lines = [
        f"# {title} — {first.backend}, {len(first.results)} cases, k = {first.k}",
        "",
        "Retrieval is generator-independent (same store + cases):",
        f"**recall@{first.k} = {_pct(first.recall_at_k).strip()}**, "
        f"**MRR = {_pct(first.mrr).strip()}** (percentages).",
        "",
        "| generator | citation P | citation R | groundedness | refusal recall | answer acc |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in reports:
        row = summary_row(r)
        lines.append(
            f"| {r.generator} | {row['cite_p'].strip()} | {row['cite_r'].strip()} "
            f"| {row['grounded'].strip()} | {row['refuse_r'].strip()} | {row['answer_acc'].strip()} |"
        )
    return "\n".join(lines)
