"""Load vignettes and expand them into (case x framing x model x repeat) jobs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator

DEFAULT_CASES = Path(__file__).resolve().parents[2] / "data" / "cases.json"


@dataclass(frozen=True)
class Case:
    id: str
    domain: str
    expected_urgency: int
    facts: str
    pair: str | None = None
    crisis_relevant: bool = False


@dataclass(frozen=True)
class Framing:
    id: str
    template: str

    def render(self, facts: str) -> str:
        return self.template.format(facts=facts)


@dataclass(frozen=True)
class Job:
    key: str
    case_id: str
    framing: str
    model: str
    repeat: int
    prompt: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Dataset:
    cases: list[Case]
    framings: list[Framing]
    urgency_scale: dict[str, str]

    def case(self, case_id: str) -> Case:
        return next(c for c in self.cases if c.id == case_id)


def load_dataset(path: Path = DEFAULT_CASES) -> Dataset:
    raw = json.loads(Path(path).read_text())
    cases = [Case(**c) for c in raw["cases"]]
    framings = [Framing(**f) for f in raw["framings"]]
    ids = [c.id for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case ids in dataset")
    if framings[0].id != "neutral":
        raise ValueError("The first framing must be 'neutral' (used as the baseline)")
    for c in cases:
        if str(c.expected_urgency) not in raw["urgency_scale"]:
            raise ValueError(f"{c.id}: expected_urgency not on the scale")
    return Dataset(cases, framings, raw["urgency_scale"])


def build_jobs(
    ds: Dataset,
    models: Iterable[str],
    repeats: int,
    case_ids: Iterable[str] | None = None,
) -> Iterator[Job]:
    wanted = set(case_ids) if case_ids else None
    for model in models:
        for case in ds.cases:
            if wanted and case.id not in wanted:
                continue
            for framing in ds.framings:
                for r in range(repeats):
                    yield Job(
                        key=f"{model}|{case.id}|{framing.id}|{r}",
                        case_id=case.id,
                        framing=framing.id,
                        model=model,
                        repeat=r,
                        prompt=framing.render(case.facts),
                    )


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
