"""Offline end-to-end test: no API key needed."""

import csv
import json

from hspilot.cli import main
from hspilot.data import build_jobs, load_dataset


def test_dataset_is_valid():
    ds = load_dataset()
    assert ds.framings[0].id == "neutral"
    assert all("{facts}" in f.template for f in ds.framings)
    assert {c.domain for c in ds.cases} >= {"control", "mental_health", "womens_health"}
    assert any(c.crisis_relevant for c in ds.cases)
    assert {f.id for f in ds.framings} >= {"companion", "pressure"}


def test_jobs_cover_full_grid():
    ds = load_dataset()
    jobs = list(build_jobs(ds, ["m1", "m2"], repeats=2))
    assert len(jobs) == 2 * len(ds.cases) * len(ds.framings) * 2
    assert len({j.key for j in jobs}) == len(jobs)


def test_dry_run_end_to_end_and_resume(tmp_path):
    out = tmp_path / "res"
    args = ["all", "--dry-run", "--results", str(out), "--models", "a", "b", "--repeats", "2"]
    main(args)
    n_resp = sum(1 for _ in (out / "responses.jsonl").open())
    n_lab = sum(1 for _ in (out / "labels.jsonl").open())
    assert n_resp == n_lab > 0

    main(args)  # resuming must not duplicate work
    assert sum(1 for _ in (out / "responses.jsonl").open()) == n_resp

    with (out / "summary.csv").open() as f:
        rows = list(csv.DictReader(f))
    neutral = [r for r in rows if r["framing"] == "neutral"]
    assert all(float(r["mean_shift_vs_neutral"]) == 0 for r in neutral)
    assert "DRY RUN" in (out / "report.md").read_text()
    assert (out / "handcheck_sample.csv").exists()


def test_dashboards(tmp_path):
    out = tmp_path / "res"
    main(["all", "--dry-run", "--results", str(out), "--models", "a", "b", "--repeats", "1"])
    dry = (out / "dashboard.html").read_text()
    assert "Dry run" in dry and "__DATA__" not in dry

    page = tmp_path / "docs" / "index.html"
    main(["dashboard", "--dry-run", "--results", str(out), "--out", str(page)])
    html = page.read_text()
    assert "Initial prototype · results pending" in html  # dry-run numbers are never published
    assert '"rows": []' in html


def test_judge_never_sees_framing_or_label(tmp_path):
    out = tmp_path / "res"
    main(["all", "--dry-run", "--results", str(out), "--models", "a", "--repeats", "1"])
    label = json.loads((out / "labels.jsonl").open().readline())
    assert "prompt" not in label and "expected_urgency" not in label
