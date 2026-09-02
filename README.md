# Mira — AI-Powered Project Intelligence Assistant

Capstone submission for **Applied Agentic AI for PMs/TPMs**.

Mira is a router-orchestrated multi-agent assistant for Nexora Pvt. Ltd. It takes
raw project data for the ABCDE Ltd. AI Adoption Project and returns a structured
project plan, a categorised risk matrix, or a weekly status report — depending on
what was asked. Every output is grounded in the files in [`data/`](data/); when the
input is too vague to ground, Mira refuses rather than inventing.

> **Status: in progress.** Sections marked _TBD_ are filled in as the build
> proceeds. See [Build status](#build-status).

---

## Contents

| Path | What it holds |
|---|---|
| [`data/`](data/) | The supplied project files, verbatim and never edited |
| [`eval/eval_mira_inputs.txt`](eval/eval_mira_inputs.txt) | The 12 graded baseline test inputs |
| [`eval/expected_criteria.md`](eval/expected_criteria.md) | Concrete pass conditions for T1–T12 |
| [`eval/validate_data.py`](eval/validate_data.py) | Recomputes every grounding fact from source |
| [`eval/results/`](eval/results/) | Baseline test results and before/after evidence |
| [`docs/baseline_data_validation.md`](docs/baseline_data_validation.md) | Generated validation report |
| [`docs/`](docs/) | Q1, architecture, charter, reflection, cost analysis |
| [`workflow/`](workflow/) | Exported workflow JSON and the agent system prompts |

---

## The system

**Orchestration pattern: router / dispatcher.** Requests to Mira fall into distinct
types that need different handling — "generate a plan", "what are the risks",
"status report for Sprint 3", "which milestones are coming up". A sequential
pipeline would run every agent on every request, wasting tokens and inviting
fabrication when an agent is handed input it has no business processing. A router
classifies intent once and delegates to a single specialist.

| Agent | Responsibility | Reads |
|---|---|---|
| Orchestrator | Classifies intent, routes to one specialist, refuses to route when intent is unclear | — |
| Planner | Structured project plan: phases, activities, milestones, deliverables | `project_description.txt`, `project_timeline.csv` |
| Risk Assessor | Categorised risk matrix with impact and mitigation | `project_risks.csv`, `project_description.txt` |
| Status Reporter | Weekly status: counts by status, blockers, health rating | `sample_task_board.csv` |
| Milestone Tracker | At-risk milestones and upcoming deliverables | `project_timeline.csv`, `sample_task_board.csv` |

Full rationale, diagram and tool-selection table: [`docs/architecture.md`](docs/architecture.md).
Agent system prompts: [`workflow/prompts/`](workflow/prompts/).

![Mira architecture](docs/diagrams/mira_architecture.svg)

## Data grounding

Two time anchors are **derived from the supplied data**, not from the real-world
date. This matters: the sample task board is historical, so using the actual
current date would make every task overdue and every milestone past.

| Constant | Value | How it is derived |
|---|---|---|
| `AS_OF_DATE` | 2026-04-21 | Earliest due date among not-Done tasks — the only date at which the board is self-consistent |
| `PROJECT_START` | 2026-03-30 | The unique Monday where Sprint 1 falls inside timeline Phase 1 **and** Sprint 2 falls inside Phase 2 |

Regenerate the full derivation at any time:

```bash
python eval/validate_data.py --write
```

### Known discrepancy in the source material

The Mira problem statement describes the task board as "3 Done, 3 In Progress, 1
Blocked, and the rest To Do". **The CSV contains 5 Done** (T001–T005), 3 In
Progress, 1 Blocked and 16 To Do. Test T10 requires counts to match actual data,
so Mira is grounded in the CSV. This is disclosed rather than silently reconciled.

Two further gaps are handled explicitly rather than papered over:

- `project_risks.csv` has **no severity or likelihood column**, so the "top 3
  risks" ranking asked for by T7 is derived by a stated rule, and Mira says so.
- Timeline Phase 8 (Monitoring & Review) has **no tasks on the board**, so the
  Milestone Tracker reports "no tasks mapped" rather than inferring progress.

## Guardrails

Every agent prompt carries an explicit insufficient-input rule. Four of the twelve
graded tests (T2, T4, T6, T9) exist to check that Mira refuses; a plausible answer
to any of them is a failure, not a partial credit.

---

## Setup

```bash
git clone https://github.com/<user>/mira-capstone.git
cd mira-capstone
cp .env.example .env      # then fill in your keys
```

### LangFlow + Langfuse

1. Install LangFlow and start it: `pip install langflow && langflow run`
2. Set the Langfuse variables **before** starting LangFlow, so tracing is active from the first run:

   ```bash
   export LANGFUSE_PUBLIC_KEY=pk-lf-...
   export LANGFUSE_SECRET_KEY=sk-lf-...
   export LANGFUSE_HOST=https://cloud.langfuse.com
   ```

3. Import [`workflow/mira_workflow.json`](workflow/) _(TBD)_ into LangFlow.
4. Point the four File components at the files in [`data/`](data/).
5. Paste each system prompt from [`workflow/prompts/`](workflow/prompts/) into its Prompt component.
6. Confirm a trace appears in Langfuse before building further.

## Reproducing the evaluation

```bash
python eval/validate_data.py          # verify the grounding facts
```

Then run each input in `eval/eval_mira_inputs.txt` through the pipeline and record
results per [`eval/expected_criteria.md`](eval/expected_criteria.md). Outputs land
in [`eval/results/baseline_results.md`](eval/results/).

---

## Build status

| Phase | Work | Status |
|---|---|---|
| P0 | Repository, platform and tracing setup | 🟡 In progress |
| P1 | Data contract, schemas, grounding rules | 🟢 Complete |
| P2 | Status Reporter agent | 🟡 Prompt written, awaiting LangFlow build |
| P3 | Planner and Risk Assessor agents | 🟡 Prompts written, awaiting LangFlow build |
| P4 | Router orchestrator and Milestone Tracker | 🟡 Prompts written, awaiting LangFlow build |
| P5 | Full evaluation run and documented fix | ⚪ Not started |
| P6 | Q1, Q3, Q4, architecture writeup, deck | 🟡 Q1 + Q3 drafted; Q4 and deck need build evidence |
| P7 | Rubric audit | ⚪ Not started |

## Deliverables index

| Assignment | Points | Document |
|---|---|---|
| Q1 — Ideation | 15 | [`docs/Q1_ideation.md`](docs/Q1_ideation.md) ✅ draft |
| Q2 — Build Mira | 45 | [`docs/architecture.md`](docs/architecture.md) ✅, [`workflow/prompts/`](workflow/prompts/) ✅, [`workflow/mira_workflow.json`](workflow/) _(TBD)_, [`eval/results/`](eval/results/) _(TBD)_ |
| Q3 — Program Charter | 25 | [`docs/Q3_program_charter.md`](docs/Q3_program_charter.md) ✅ draft |
| Q4 — Reflection | 15 | [`docs/Q4_reflection.md`](docs/) _(TBD)_ |

---

## Source data

All files in `data/` are supplied course material for the fictional ABCDE Ltd. AI
Adoption Project and are reproduced unmodified. Nexora Pvt. Ltd. and ABCDE Ltd.
are fictional companies used by the course.
