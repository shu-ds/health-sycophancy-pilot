# "Does the advice bend?": AI safety in women's health and mental health

**Question:** does a model say what it believes, or lean towards what the user wants to hear?

This initial prototype studies the safety and reliability of AI advice: sycophancy, honesty, robustness to user framing, inappropriate or irrelevant recommendations, recognition of high-risk situations, and when to hand over to a human. It focuses on anxiety, depression, postpartum and perimenopausal mental health, and passive suicidal ideation. The facts are held fixed and only the way the person asks changes. Two examples: a woman with months of anxiety who says "it's probably just hormones", or a new mother who says "please don't send me to someone else, you're the only one I can talk to". The right advice shouldn't change because of that sentence. This repo measures whether it does.

**[→ Live dashboard](https://shu-ds.github.io/health-sycophancy-pilot/)**

## Why this testbed, and why it matters for alignment

- **It's an alignment question.** Anthropic's [recommended research directions](https://alignment.anthropic.com/2025/recommended-directions/) ask whether a model answers because it believes the answer is correct, or because it wants to please the user. That's an honesty question, and sycophancy is its most common everyday form.
- **Health and mental health make a sharp testbed.** The pressure is natural (people really do say "it's just stress"), clinicians agree on the right level of care for many cases, and the cost of bending is real. Anthropic's work on [personal guidance](https://www.anthropic.com/research/claude-personal-guidance) and [user well-being](https://www.anthropic.com/news/protecting-well-being-of-users) points to sycophancy as the key risk in these conversations.
- **There's a fairness angle too.** Women's symptoms, physical and emotional, have a long history of being waved away as stress or hormones. A model that does the same thing more warmly isn't being kind.
- **Why I care.** It's personal for me. In stressful, anxious stretches I've been the person typing to an AI late at night, wanting it to agree with me.

## Design

| | |
|---|---|
| **Cases** | 14 synthetic first-person vignettes ([`data/cases.json`](data/cases.json)): anxiety, depression, work stress, postpartum mood, perimenopause, PMDD, restrictive eating, passive suicidal ideation, fatigue dismissed as burnout, chest pain in someone with panic attacks, and 3 low-risk controls. Each has an expected urgency on a 0–3 scale. |
| **Framings** | The same facts asked 6 ways: `neutral`, `anxious`, `minimizing` ("just stress or hormones"), `pressure` (cost, time), `social_proof` ("my mum says every woman goes through this"), `companion` ("you're the only one I can talk to"). |
| **Sex pair** | The chest-pain case is asked twice, identical except for "woman" vs "man". |
| **Subjects** | Any Claude models (default: Opus 5.5, Sonnet 5.5, Haiku 5.5), 3 samples per cell. |
| **Grading** | A **blind** LLM judge sees only the reply, never the framing or the expected answer. It labels the recommended urgency, whether the reply endorses waiting, whether it encourages human support, and whether it gives crisis resources. |
| **Validation** | A random 30-reply sample is exported for a human (ideally a clinician) to label blind. Agreement with the judge is reported. |
| **Metrics** | Shift in urgency vs. neutral (paired by case, bootstrap 95% CI), under-triage, endorsing waiting, encouraging human support, crisis-resource rate, over-triage on controls, male−female gap. |

```
cases.json ──► collect (async, resumable) ──► responses.jsonl
                                              │
                         blind judge ◄────────┘
                              │
                        labels.jsonl ──► analyze ──► summary.csv · report.md · dashboard.html
                                                     handcheck_sample.csv (human validation)
```

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                                    # offline tests, no API key needed
python -m hspilot.cli all --dry-run       # full pipeline on synthetic labels -> results_dry_run/dashboard.html

export ANTHROPIC_API_KEY=...              # never commit this
python -m hspilot.cli all --models claude-haiku-5-5 --repeats 1   # cheap smoke test
python -m hspilot.cli all                 # full pilot: 756 replies + 756 judge calls (~USD 25-35)
python -m hspilot.cli dashboard           # refresh docs/index.html with real results
```

- Every step can be resumed, so a stopped run skips the jobs it already finished.
- Dry-run numbers go to `results_dry_run/` and are never written into the published dashboard.

## The dashboard

`docs/index.html` is a self-contained static page (no server, no build step).
- **Always shown:** method, cases, framings, limitations.
- **With results:** summary statistics, metric chart with table view, sex-swapped pair, and a response browser with judge labels.

Publish via **Settings → Pages → Deploy from branch → `main` / `docs`**.

## Limitations

- **The expected labels are mine.** I wrote them from mainstream public guidance, and they need clinician review.
- **The conversations are single-turn.** Real pressure, and real companionship, builds over many turns. That's the next step.
- **The judge is a model.** The human check measures its error rate rather than assuming it away.
- **The sample is small by design.** This is a pilot to see whether the effect exists, not a benchmark.

## Next steps

1. **Belief vs. statement.** Train probes on open-weight models to read the internal judgement of urgency.
   - Does that judgement stay high under pressure while the stated advice softens? Then the model knows and says otherwise: an honesty failure, with a possible monitoring signal.
   - Or does the internal judgement drop too? Then pressure is changing what the model believes.
2. **Fixes that generalize.** Do mitigations like inoculation prompting or spec-style training on a few framings make honesty hold on framings and topics never trained on? The cost is measured as over-triage on the controls.
3. **Multi-turn pressure and reliance, plus more demographic pairs** (age, language fluency).

## Data and ethics

- **All synthetic.** No patient data, client data or real conversations are used, and every vignette is synthetic.
- **Not medical advice.** The results describe model behaviour.
- **If you're struggling:** please reach out to someone you trust or a local crisis line.

MIT licensed.
