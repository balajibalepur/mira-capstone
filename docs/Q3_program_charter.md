# Q3 — Program Charter: Mira (25 points)

**Nexora Pvt. Ltd. · Project Intelligence Assistant**
Sponsor: CTO · Owner: AI PM/TPM · Status: Pilot design

---

## 1. Vision

**Every Nexora project has a current plan, a current risk register and a current
status report — because producing them costs minutes rather than hours.**

Nexora's constraint is not that its PMs lack judgement. It is that judgement is
crowded out by document production. A PM running three projects spends the
majority of their planning capacity transcribing information they already have
into formats other people can read.

Mira does the transcription. The PM keeps the judgement, and reviews rather than
authors. The measure of success is not that Mira writes well — it is that a
Nexora PM never again skips a risk assessment because there was no time.

### What Mira is not

Stating this explicitly, because the failure mode of a tool like this is scope
drift into decision-making:

- **Not a decision-maker.** Mira reports that a task is blocked. It does not
  decide what to do about it.
- **Not a source of truth.** The task board and timeline remain authoritative.
  Mira reads them and never writes to them.
- **Not an estimator.** Mira reports what the data says. It does not predict
  completion dates or infer progress from tone.

---

## 2. Scope

### In scope

| Capability | Description |
|---|---|
| Project plan generation | Structured plans with phases, activities, milestones, deliverables, grounded in the project description and timeline |
| Risk assessment | Categorised risk matrix with impact, mitigation and project-specific relevance; derived rankings disclosed as derived |
| Weekly status reporting | Counts by status, blockers, rule-based health rating; stakeholder update emails |
| Milestone alerting | Timeline versus board comparison; at-risk milestones with reason and suggested action |
| Observability | Per-agent tracing: routing decisions, inputs, outputs, tokens, latency, cost |

### Out of scope for the pilot

| Excluded | Why |
|---|---|
| Writing to task boards or timelines | Read-only removes an entire class of harm. A wrong report is corrected; a wrong write corrupts the source. |
| Live board API integration (Trello, Jira) | Adds an authentication dependency and a failure mode without changing what the agents can conclude. CSV export is sufficient to prove the value. |
| Client-facing outputs | Every output is reviewed by a PM before leaving Nexora. Revisit only once accuracy is measured over a full cycle. |
| Multi-project portfolio rollup | Requires a cross-project data model that does not exist yet. Natural phase two. |
| Fine-tuning | Prompt guardrails are the cheaper and more inspectable intervention at this scale. |

### Assumptions

- Project data is available as text and CSV exports in a consistent format.
- One PM reviews every Mira output before it is acted on, throughout the pilot.
- The 10 pilot PMs/TPMs are willing to log corrections — without that, there is
  no accuracy measurement.

---

## 3. Success criteria

Grouped by what they protect. A system can be fast and useless, or accurate and
unused, so all three groups must hold.

### Accuracy — is it right?

| Criterion | Measure | Target |
|---|---|---|
| Plan groundedness | Milestones traceable to the source timeline | ≥ 98% |
| Risk relevance | Risks carrying a valid source identifier | 100% |
| Status accuracy | Task counts matching the board exactly | 100% |

### Trustworthiness — does it know what it doesn't know?

| Criterion | Measure | Target |
|---|---|---|
| Refusal correctness | Under-specified requests that refuse rather than generate | 100% |
| Hallucination rate | Outputs containing an item not traceable to a source file | 0% for identifiers; < 2% overall |
| Disclosure compliance | Derived values (rankings, health) accompanied by the rule used | 100% |

### Adoption — is it used?

| Criterion | Measure | Target |
|---|---|---|
| Coverage | Active projects holding a current risk matrix | ≥ 95% |
| Time saved | Hours returned per PM per project cycle | ≥ 15 h |
| Voluntary usage | Pilot PMs using Mira unprompted in week 4 | ≥ 8 of 10 |

The last one is the honest one. If PMs stop using it once nobody is watching, the
other numbers do not matter.

### Gate to proceed beyond pilot

All accuracy and trustworthiness targets met, **and** at least 8 of 10 pilot PMs
using Mira voluntarily in week 4. Failing either, the pilot extends rather than
scaling.

---

## 4. Timeline

Pilot phase, from build to go/no-go decision.

| Phase | Duration | Activities | Exit criteria |
|---|---|---|---|
| **1. Design and grounding** | Week 1 | Data contract, output schemas, agent prompts, architecture, derived time anchors | Grounding facts computed and committed; prompts written |
| **2. Core build** | Week 1–2 | Status Reporter first (most testable), then Planner and Risk Assessor, each tested standalone | Three capabilities working end to end |
| **3. Orchestration** | Week 2 | Router over proven agents; Milestone Tracker | All 12 baseline inputs routing correctly |
| **4. Evaluation** | Week 2 | Full baseline suite; trace analysis; at least one documented prompt fix with before/after evidence | 12/12 documented; every failure either fixed or recorded |
| **5. Pilot with 10 PMs/TPMs** | Week 3–6 | Onboarding, supervised use, correction logging, weekly review | Adoption and accuracy measured over four weeks |
| **6. Go/no-go** | Week 7 | Evaluate against §3 gate; decide scale, extend or stop | Documented decision |

Phases 1–4 are the capstone submission. Phases 5–6 are the operational plan.

---

## 5. Risks

Risks to the **Mira programme** — distinct from the risks Mira assesses in client
projects.

| # | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| M1 | **Fabricated content reaches a stakeholder.** An invented milestone or risk in a document sent to a client. | Critical — a single incident destroys trust in the whole system | Medium without controls | Explicit refusal rules in every agent prompt; `source_files` on every output; mandatory PM review before anything leaves Nexora; four of twelve tests grade refusal specifically |
| M2 | **Silent arithmetic error.** Status counts that look plausible but are wrong. | High — status reports drive decisions | Medium | Counting instruction with recount check; automated verification against the source; status accuracy tracked at 100% target, not "high" |
| M3 | **Over-trust.** PMs stop reviewing because Mira is usually right. | High — the review step is the safety net | High over time | Health ratings state the rule that fired, so review is cheap; correction logging keeps PMs engaged; periodic seeded-error audits |
| M4 | **Source data is inconsistent or wrong.** Mira faithfully reports bad input. | Medium | High — already observed; the supplied brief's own task counts contradict its CSV | Validation script recomputes grounding facts from source; discrepancies disclosed rather than reconciled |
| M5 | **Adoption failure.** Built, correct, unused. | High — no return on the investment | Medium | Pilot with 10 PMs rather than a full rollout; voluntary-usage gate; onboarding tied to a real project rather than a demo |
| M6 | **Cost drift at scale.** Token spend grows faster than expected. | Low at current volume | Low | Per-agent cost tracing from day one; small model by default; corpus small enough to inject directly |
| M7 | **Model or platform change breaks outputs.** A provider update alters formatting or behaviour. | Medium | Medium | Structured output schemas fail loudly rather than silently; baseline suite re-runnable in minutes as a regression test |

The most dangerous is **M3**, because it grows precisely as the system succeeds.

---

## 6. Stakeholders

| Stakeholder | Interest | Involvement | Decision rights |
|---|---|---|---|
| **CTO** | Sponsor; delivery capacity and technology positioning | Milestone reviews; go/no-go | Funding; approves scaling |
| **AI PM/TPM (owner)** | Design, build, evaluation | Daily | Architecture, tooling, prompts |
| **Pilot PMs/TPMs (10)** | Primary users; time recovered | Weekly review; correction logging | Veto on usability — if they will not use it, it does not ship |
| **Delivery leads** | Consistency of plans and reports across projects | Format review | Approve output formats |
| **Client stakeholders (e.g. ABCDE Ltd.)** | Recipients of PM-reviewed outputs | Indirect | None — they see PM-reviewed documents, never raw output |
| **Legal / Data protection** | Client project data in a third-party LLM | Review before pilot | **Blocking** approval on data handling |
| **Finance** | Per-user running cost | Cost review at go/no-go | Approves ongoing spend |

Legal review is a **blocking dependency, not a parallel task**. Client project
data leaves Nexora's boundary when it reaches an LLM provider, and that must be
settled before the pilot rather than during it. The same lesson is visible in the
client project Mira reads: T024, the security review, has been Blocked waiting on
availability.

---

## 7. Decision-making

| Decision | Owner | Consulted | Escalation |
|---|---|---|---|
| Architecture, agent design, prompts | AI PM/TPM | Delivery leads | CTO |
| Model and platform selection | AI PM/TPM | Finance on cost | CTO |
| Output format and schema changes | AI PM/TPM | Delivery leads, pilot PMs | CTO |
| Adding a capability to scope | CTO | AI PM/TPM, delivery leads | — |
| Data handling and retention | Legal | AI PM/TPM, CTO | CTO |
| Go / no-go to scale | CTO | All | — |
| **Halting the pilot on an accuracy incident** | **Any pilot PM** | AI PM/TPM | CTO within 24 h |

The last row is deliberate. A PM who spots fabricated content should be able to
stop the pilot immediately without seeking permission. Making that expensive is
how incidents go unreported.

### Change control

Prompt changes are version-controlled and require a full baseline re-run before
merge. The suite takes minutes and costs pennies; there is no justification for
shipping a prompt change unevaluated.

---

## 8. Rollout plan

### Stage 1 — Pilot (weeks 3–6, 10 PMs/TPMs)

**Selection.** Ten volunteers spanning project types and seniority, deliberately
including two sceptics. A pilot of enthusiasts measures enthusiasm.

**Onboarding.** A 45-minute session per PM covering what Mira does, what it
refuses to do, and — most importantly — **what its failure modes look like**. PMs
are taught to spot a fabricated milestone, not merely told that fabrication is
possible.

**Operating rules during pilot:**

1. Every output is PM-reviewed before use. No exceptions.
2. Every correction is logged — what was wrong, which agent, what the source said.
3. Nothing goes to a client without a named PM's sign-off.
4. Weekly 30-minute review of the correction log with the owner.

**Instrumentation.** Every run traced. Weekly: accuracy against §3, refusal
correctness, cost per user per day, and usage frequency per PM.

### Stage 2 — Go/no-go (week 7)

Evaluated against the §3 gate. Three outcomes: **scale**, **extend** (a specific
metric missed, with a named fix), or **stop** (a trustworthiness target missed —
an accurate-but-unused system can be fixed; an unreliable one cannot be trusted
while it is repaired).

### Stage 3 — Departmental rollout (weeks 8–12)

All Nexora PMs/TPMs. Pilot PMs become local champions — peer onboarding beats
central training at this size. Mira output becomes the expected format for plans,
risk matrices and status reports, but **manual production remains permitted**;
mandating a tool is how shadow processes start.

### Stage 4 — Steady state (from week 13)

Monthly accuracy audit on a sample of outputs. Quarterly review of the baseline
suite against new project types. Correction log remains open permanently — it is
the early warning system for M3 and M7.

### Rollback

If accuracy or trustworthiness targets fail at any stage, Mira reverts to
advisory-only: outputs are drafts, and the standard is a manually-authored
document. The read-only design means rollback costs nothing — there is no
corrupted state to unwind, because Mira never wrote to the source systems.
