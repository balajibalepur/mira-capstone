# Q1 — Ideation (15 points)

**Where AI agents can increase PM/TPM productivity at Nexora Pvt. Ltd.**

Nexora is a 120-person software development and IT services company in London,
delivering to clients across Europe and Asia. Its PMs and TPMs run several
projects simultaneously with only a few people covering them, which is the
constraint every use case below attacks.

Three use cases are proposed. All three are grounded in the pain points named in
the Mira problem statement, and all three are implemented in the delivered
system rather than being aspirational.

---

## Use case 1 — Project plan generation

### Pain point

Creating a project plan from a high-level description takes **3–4 hours of manual
work per project**. With several projects running at once, this is the single
largest block of non-delivery time a Nexora PM spends. The output is also
inconsistent: there is no standard format, so plans from different PMs cannot be
compared, rolled up, or estimated against by engineering.

The hidden cost is worse than the hours. Because plans are expensive to produce,
they are produced once and rarely revised, so the plan drifts from reality and
stops being used.

### Agentic solution

A **Planner Agent** ingests the project description and any existing timeline and
returns a structured plan: phases, key activities, milestones and deliverables,
in a fixed schema. Because the schema is fixed, every plan across every Nexora
project becomes comparable.

The critical design constraint is that the agent must **refuse to plan from
nothing**. A generated plan carries an authority that a blank page does not — a
PM who receives a plausible-looking plan built from one sentence is worse off
than one who receives nothing, because they may act on invented phases. The agent
therefore returns an explicit list of what it needs when the input is
insufficient.

### Inputs and outputs

| | |
|---|---|
| **Inputs** | Project description (free text); existing timeline (CSV) if one exists |
| **Outputs** | JSON: `project_name`, `goals[]` with targets, `phases[]` with weeks, activities and milestones, `source_files[]`, `assumptions[]` |
| **On insufficient input** | `status: insufficient_information` plus a `missing[]` list — scope, timeline, team size, deliverables |

### Success metrics

| Metric | Definition | Target |
|---|---|---|
| **Plan groundedness** | % of milestones in a generated plan traceable to the source timeline | ≥ 98% |
| **Time to first draft** | Minutes from description to a reviewable plan | ≤ 5 min, from a 3–4 hour baseline |
| **Refusal correctness** | % of under-specified requests that return `insufficient_information` rather than a plan | 100% |

The third metric matters more than it looks. It is the one that keeps the first
two honest — a system that never refuses will score well on speed and badly on
trust.

### Knowledge base required

Project description text and the phase/milestone timeline. At Nexora's current
scale this is **direct context injection, not retrieval**: the full corpus for one
project is roughly 2,000 tokens. Retrieval becomes worth its complexity only once
plans must draw on a library of past projects.

---

## Use case 2 — Standardised risk assessment

### Pain point

Risk assessments are done **inconsistently — some projects have detailed risk
matrices, others have none.** The variance is the problem rather than the effort:
a portfolio where half the projects have risk registers cannot be governed,
because leadership cannot tell an unrisky project from an unassessed one.

Where risk registers do exist, they are often generic — the same six risks
restated per project, which is a form of documentation theatre that costs time
and surfaces nothing.

### Agentic solution

A **Risk Assessor Agent** produces a categorised risk matrix — risk, impact,
mitigation — grounded in the project's own risk data and description. Every risk
carries an identifier traceable to a source row, and each is tied to something
specific about the project.

A subtlety worth designing for: the supplied risk data has **no severity or
likelihood column**, so any ranking the agent produces is derived rather than
read. The agent must disclose the ranking rule it used. A ranking presented as if
the data supplied it is a quiet fabrication, and the kind a reviewer would not
catch.

### Inputs and outputs

| | |
|---|---|
| **Inputs** | Risk register (CSV); project description (free text) |
| **Outputs** | JSON: `risks[]` with `risk_id`, `category`, `risk`, `impact`, `mitigation`, `project_relevance`; plus `ranking_applied` and `ranking_rule` |
| **On insufficient input** | `status: insufficient_information` — project scope, domain, approach, timeline |

### Success metrics

| Metric | Definition | Target |
|---|---|---|
| **Risk relevance** | % of returned risks carrying a valid identifier from the source register | 100% |
| **Project specificity** | % of risks whose relevance line references something stated in the project description | ≥ 80% |
| **Coverage consistency** | % of active Nexora projects holding a current risk matrix | ≥ 95%, from a mixed baseline |

The third metric is the business case. The first two are how you keep it from
being met with worthless documents.

### Knowledge base required

The project's risk register and description. A shared cross-project risk taxonomy
would be the natural second phase — it would let Nexora see which risks recur
across its portfolio, which no single project's register can show.

---

## Use case 3 — Weekly status reporting and milestone alerting

### Pain point

Two connected problems. Weekly status reports take **1–2 hours to compile
manually** from task boards and meeting notes. And separately, **milestones are
missed because there are no proactive alerts — issues are discovered only in
retrospectives**, which is the most expensive moment to discover them.

These belong together because they draw on the same data and are both symptoms of
the board being read by a human only once a week.

### Agentic solution

A **Status Reporter Agent** reads the task board and returns counts by status,
blockers, and an overall health rating — and can render the same facts as a
stakeholder update email, since the reporting burden is partly about audience
translation rather than analysis.

A **Milestone Tracker Agent** compares the timeline against the board and flags
milestones at risk, with the reason and a suggested action. This is what turns a
weekly retrospective finding into a same-week alert.

Two rules keep this trustworthy. Counts must be produced by **counting rows**, not
estimating — this is the one place where a plausible answer is most likely to be
quietly wrong. And **health must be assigned by an explicit rule**, not by
impression, with the rule that fired stated in the output:

| Health | Rule |
|---|---|
| RED | A blocked task is due within 14 days, or more than 20% of open tasks are past due |
| AMBER | Any blocked task exists, or any open task is past due |
| GREEN | Neither |

### Inputs and outputs

| | |
|---|---|
| **Inputs** | Task board export (CSV); project timeline (CSV); a reference date |
| **Outputs** | JSON: `counts`, `tasks[]`, `blockers[]` with days-to-due, `health` with `health_reason`, optional `email_body`; and separately `at_risk[]` and `upcoming_milestones[]` |
| **On insufficient input** | `status: insufficient_information` — no task data means no report, never an estimated one |

### Success metrics

| Metric | Definition | Target |
|---|---|---|
| **Status accuracy** | % of runs whose task counts match the board exactly | 100% |
| **Blocker detection latency** | Days between a task becoming blocked and it appearing in an alert | ≤ 1 day, from up to 14 |
| **Report preparation time** | Minutes from board export to a sendable stakeholder update | ≤ 10 min, from 60–120 |

### Knowledge base required

Task board export with identifiers, statuses, assignees, sprints and due dates,
plus the project timeline with phase milestones. Optionally a live board API
(Trello, Jira) to remove the export step — deliberately out of scope for this
build, since it adds an authentication dependency without changing what the
agents can conclude.

---

## Why these three, and why one system

All three read from the same small corpus and serve the same person, so building
them as one router-orchestrated assistant rather than three tools means a PM asks
in one place and the grounding rules are written once.

Estimated recovery per PM per project cycle:

| Activity | Manual | With Mira | Saved |
|---|---|---|---|
| Project plan | 3–4 h once | ~0.5 h review | ~3 h |
| Risk assessment | 2–3 h, when done at all | ~0.5 h review | ~2 h |
| Weekly status × 12 weeks | 12–24 h | ~2 h review | ~15 h |
| **Per project** | | | **~20 h** |

Across a PM running three concurrent projects, that is roughly **60 hours per
cycle returned to delivery work** — and, more importantly, risk registers and
status reports that exist for every project rather than the ones someone found
time for.

> These figures are derived from the baselines stated in the Mira problem
> statement (3–4 h per plan, 1–2 h per status report) and from observed review
> times, not from measured production use. They are an estimate to be validated
> during the pilot described in the Program Charter, not a result.
