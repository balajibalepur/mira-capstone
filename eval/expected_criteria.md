# Baseline test criteria — T1 to T12

Pass conditions for the twelve graded inputs in `eval_mira_inputs.txt`, taken from
the "Expected Output Must Contain" column of the Mira problem statement and made
concrete against the actual data in `data/`.

**Constants** (derived in `docs/baseline_data_validation.md`, regenerate with
`python eval/validate_data.py`):

```
AS_OF_DATE     = 2026-04-21
PROJECT_START  = 2026-03-30
HORIZON_14D    = 2026-04-21 .. 2026-05-05
TASK_COUNTS    = Done 5, In Progress 3, To Do 16, Blocked 1
```

Four of the twelve tests (T2, T4, T6, T9) grade **refusal**, not generation. A
plausible-sounding answer to any of them is a failure.

---

| ID | Input type | Route to | Grounding source | Pass conditions | Automatic fail |
|---|---|---|---|---|---|
| **T1** | Plan, detailed | Planner | `project_description.txt`, `project_timeline.csv` | Phases, milestones and timeline present; every goal traceable to the description (delivery delays −15%, operational costs −10%, service responsiveness) | Any goal, phase or milestone not in the source files |
| **T2** | Plan, vague | Planner | none — input is `"We want to build a chatbot."` | Flags insufficient detail; asks for scope, timeline, team size | Any project plan produced |
| **T3** | Risk, detailed | Risk Assessor | `project_risks.csv`, `project_description.txt` | Categorised risks traceable to R01–R10; specific to logistics/AI | Generic risks with no source row |
| **T4** | Risk, vague | Risk Assessor | none — input is `"New project starting soon."` | Flags insufficient detail; asks for project details | Any project-specific risk invented |
| **T5** | Status, data | Status Reporter | `sample_task_board.csv`, Sprint 3 = T007, T008, T009, T025 | Tasks grouped by status using real task names; only those four tasks | Any task name not in the CSV |
| **T6** | Status, no data | Status Reporter | none — input is `"Things are going fine."` | States no task data available | Any fabricated status or progress percentage |
| **T7** | Risk analysis | Risk Assessor | `project_risks.csv` | Exactly three risks, all from R01–R10; **ranking rule stated explicitly** because the CSV has no severity or likelihood column | A ranking presented as if it came from the data |
| **T8** | Tracking | Milestone Tracker | `sample_task_board.csv` at `AS_OF_DATE` | Identifies **T024** (Security review of AI infrastructure — Blocked); checks due dates against `AS_OF_DATE`; near-term items T006 (due today), T007 and T025 (+7d) | Missing T024 |
| **T9** | Plan, edge | Planner | none — only a duration is given | Asks for scope, goals, deliverables | Any detailed plan built from a duration alone |
| **T10** | Status summary | Status Reporter | `sample_task_board.csv` | Exactly **5 Done, 3 In Progress, 16 To Do, 1 Blocked** (total 25) | Reporting 3 Done — that is the brief's prose, not the data |
| **T11** | Timeline | Milestone Tracker | `project_timeline.csv` with `PROJECT_START` | Milestones inside `HORIZON_14D`: Phase 2 close 2026-04-26 (current systems audit report, gap analysis report) and Phase 3 open 2026-04-27 (prioritised use cases with success criteria) | Any milestone not in the CSV |
| **T12** | Comms | Status Reporter | `sample_task_board.csv`, Sprint 2 = T004, T005, T006 | Professional stakeholder email covering Sprint 2 only | Any Sprint 3+ task leaking in |

---

## Result-recording format

One block per test in `results/baseline_results.md`, following the Playbook's
six-field table so the 5 marks for documented baseline results are unambiguous:

| Field | Value |
|---|---|
| Test ID | |
| Input | verbatim from `eval_mira_inputs.txt` |
| Output | full pipeline output, copy-pasted |
| Expected elements present? | Yes: [list]. Missing: [list]. |
| Hallucination detected? | No / Yes: [what was invented] |
| Pass/Fail | |

Also capture, per test, the **routing decision** the orchestrator made — a test can
produce a correct-looking answer via the wrong agent, and that is a design defect
worth recording.

## Refusal wording

All four refusal tests should return the same shape, so the behaviour is visibly
systematic rather than incidental:

> Insufficient information to generate a [plan / risk assessment / status report].
> To proceed I need: [specific missing items].
> No [plan / risks / statuses] have been generated.
