"""Command line entry point.

    python -m hspilot.cli all --dry-run                 # offline test, no API calls
    python -m hspilot.cli all --repeats 3               # full pilot
    python -m hspilot.cli collect --cases passive_ideation --models claude-haiku-5-5
    python -m hspilot.cli dashboard                     # publish docs/index.html for GitHub Pages
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .analyze import judge_agreement, run_analysis, sex_pair_gap, summarize
from .dashboard import write_dashboard
from .data import DEFAULT_CASES, build_jobs, load_dataset, read_jsonl
from .pipeline import collect, grade

DEFAULT_MODELS = ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="hspilot", description="Health-advice sycophancy pilot")
    p.add_argument("step", choices=["collect", "grade", "analyze", "all", "dashboard"])
    p.add_argument("--out", type=Path, default=Path("docs/index.html"), help="dashboard step: output file")
    p.add_argument("--cases-file", type=Path, default=DEFAULT_CASES)
    p.add_argument("--results", type=Path, default=Path("results"))
    p.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    p.add_argument("--judge", default="claude-opus-5-5")
    p.add_argument("--repeats", type=int, default=3, help="samples per (model, case, framing)")
    p.add_argument("--cases", nargs="*", help="only run these case ids")
    p.add_argument("--effort", default="medium", choices=["low", "medium", "high"])
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--dry-run", action="store_true", help="fake replies and labels; no API calls")
    a = p.parse_args(argv)

    if a.dry_run and a.results == Path("results"):
        a.results = Path("results_dry_run")  # never mix synthetic and real data
    ds = load_dataset(a.cases_file)
    responses, labels = a.results / "responses.jsonl", a.results / "labels.jsonl"

    if a.step in ("collect", "all"):
        jobs = list(build_jobs(ds, a.models, a.repeats, a.cases))
        n = asyncio.run(collect(jobs, responses, effort=a.effort, concurrency=a.concurrency, dry_run=a.dry_run))
        print(f"collect: {n} new replies ({len(jobs)} jobs total) -> {responses}")
    if a.step in ("grade", "all"):
        n = asyncio.run(grade(responses, labels, ds, judge_model=a.judge, concurrency=a.concurrency, dry_run=a.dry_run))
        print(f"grade: {n} new labels -> {labels}")
    if a.step in ("analyze", "all"):
        print(f"analyze: report -> {run_analysis(ds, a.results, dry_run=a.dry_run)}")
        print(f"analyze: dashboard -> {a.results / 'dashboard.html'}")
    if a.step == "dashboard":
        # Publishable page: real results if they exist, otherwise the study design only.
        # Dry-run numbers are never published here.
        labels = [] if a.dry_run else read_jsonl(labels)
        resp = read_jsonl(responses) if labels else []
        rows = summarize(ds, labels) if labels else []
        gaps = sex_pair_gap(ds, labels) if labels else []
        agreement = judge_agreement(labels, a.results / "handcheck_labeled.csv") if labels else None
        out = write_dashboard(a.out, ds, rows, gaps, resp, labels, agreement, dry_run=False)
        print(f"dashboard: {'results' if rows else 'design only'} -> {out}")


if __name__ == "__main__":
    main()
