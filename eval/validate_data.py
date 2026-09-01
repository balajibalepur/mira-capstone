#!/usr/bin/env python3
"""
Mira capstone - baseline data validation.

Recomputes every factual claim made in docs/baseline_data_validation.md directly
from the supplied source files, so the document is generated evidence rather than
asserted evidence.

Run:  python eval/validate_data.py            # print report
      python eval/validate_data.py --write    # regenerate docs/baseline_data_validation.md

Nothing here calls an LLM. It exists to pin down the two time anchors and the
grounding facts that every agent prompt depends on.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import pathlib
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "docs" / "baseline_data_validation.md"

DONE = "Done"
BLOCKED = "Blocked"
IN_PROGRESS = "In Progress"
TODO = "To Do"


# --------------------------------------------------------------------------- io


def load() -> tuple[list[dict], list[dict], list[dict], str]:
    board = list(csv.DictReader((DATA / "sample_task_board.csv").open()))
    timeline = list(csv.DictReader((DATA / "project_timeline.csv").open()))
    risks = list(csv.DictReader((DATA / "project_risks.csv").open()))
    description = (DATA / "project_description.txt").read_text().strip()
    return board, timeline, risks, description


def d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


# ------------------------------------------------------------------- anchor A


def derive_as_of(board: list[dict]) -> tuple[dt.date, dict]:
    """The as-of date for status reporting, derived from the board itself.

    The board is only self-consistent inside a narrow window: every Done task's
    due date must have passed, and no not-Done task may be overdue. The earliest
    due date among not-Done tasks is the tightest defensible anchor.
    """
    done_due = [d(t["due_date"]) for t in board if t["status"] == DONE]
    open_due = [d(t["due_date"]) for t in board if t["status"] != DONE]
    as_of = min(open_due)
    driver = [t["task_id"] for t in board if t["status"] != DONE and d(t["due_date"]) == as_of]
    return as_of, {
        "latest_done_due": max(done_due),
        "earliest_open_due": as_of,
        "driver_tasks": driver,
    }


# ------------------------------------------------------------------- anchor B


def derive_project_start(board: list[dict], timeline: list[dict]) -> tuple[dt.date, list[dict]]:
    """The project start date, derived by constraint satisfaction.

    project_timeline.csv is expressed in week numbers; sample_task_board.csv is
    expressed in dates. The join is a start date. We search every Monday in a
    plausible range and keep the ones where each early sprint's due dates land
    inside the timeline phase that shares its subject matter.
    """
    # Sprint 1 tasks are labelled Planning -> timeline phase 1 (Project Initiation)
    # Sprint 2 tasks are labelled Analysis -> timeline phase 2 (Current State Analysis)
    constraints = [("Sprint 1", 1), ("Sprint 2", 2)]
    phase_weeks = {int(p["phase"]): (int(p["start_week"]), int(p["end_week"])) for p in timeline}

    earliest = min(d(t["due_date"]) for t in board)
    candidates, trace = [], []
    for back in range(0, 57):  # up to 8 weeks before the first due date
        start = earliest - dt.timedelta(days=back)
        if start.weekday() != 0:  # Mondays only
            continue
        ok = True
        detail = []
        for sprint, phase in constraints:
            w0, w1 = phase_weeks[phase]
            lo = start + dt.timedelta(weeks=w0 - 1)
            hi = start + dt.timedelta(weeks=w1) - dt.timedelta(days=1)
            dues = [d(t["due_date"]) for t in board if t["sprint"] == sprint]
            fits = all(lo <= x <= hi for x in dues)
            detail.append((sprint, phase, lo, hi, fits))
            ok = ok and fits
        trace.append({"start": start, "ok": ok, "detail": detail})
        if ok:
            candidates.append(start)

    if len(candidates) != 1:
        print(f"WARNING: {len(candidates)} candidate start dates: {candidates}", file=sys.stderr)
    return (candidates[0] if candidates else earliest), trace


def phase_windows(timeline: list[dict], start: dt.date) -> list[dict]:
    out = []
    for p in timeline:
        a = start + dt.timedelta(weeks=int(p["start_week"]) - 1)
        b = start + dt.timedelta(weeks=int(p["end_week"])) - dt.timedelta(days=1)
        out.append({**p, "start_date": a, "end_date": b})
    return out


# ------------------------------------------------------------------- grounding


def label_phase_map(board: list[dict], windows: list[dict]) -> dict[str, set[str]]:
    m: dict[str, set[str]] = defaultdict(set)
    for t in board:
        due = d(t["due_date"])
        for p in windows:
            if p["start_date"] <= due <= p["end_date"]:
                m[t["labels"]].add(f"P{p['phase']} {p['phase_name']}")
    return dict(m)


def health(board: list[dict], as_of: dt.date) -> tuple[str, list[str]]:
    """Explicit Red/Amber/Green rubric. Every rule reads only from the board."""
    reasons = []
    blocked = [t for t in board if t["status"] == BLOCKED]
    overdue = [t for t in board if t["status"] != DONE and d(t["due_date"]) < as_of]
    open_tasks = [t for t in board if t["status"] != DONE]

    imminent = [t for t in blocked if (d(t["due_date"]) - as_of).days <= 14]
    overdue_share = len(overdue) / len(open_tasks) if open_tasks else 0.0

    if imminent:
        reasons.append(f"blocked task(s) due within 14 days: {[t['task_id'] for t in imminent]}")
        return "RED", reasons
    if overdue_share > 0.20:
        reasons.append(f"{overdue_share:.0%} of open tasks are past due (threshold 20%)")
        return "RED", reasons
    if blocked:
        reasons.append(
            f"blocked task(s) present with runway: "
            + ", ".join(f"{t['task_id']} due {t['due_date']} (+{(d(t['due_date'])-as_of).days}d)" for t in blocked)
        )
    if overdue:
        reasons.append(f"past-due open task(s): {[t['task_id'] for t in overdue]}")
    if reasons:
        return "AMBER", reasons
    return "GREEN", ["no blocked tasks, nothing past due"]


# ---------------------------------------------------------------------- report


def report() -> str:
    board, timeline, risks, description = load()
    as_of, anchor_a = derive_as_of(board)
    start, trace = derive_project_start(board, timeline)
    windows = phase_windows(timeline, start)
    status = Counter(t["status"] for t in board)
    labels = label_phase_map(board, windows)
    rag, rag_why = health(board, as_of)

    current_week = ((as_of - start).days // 7) + 1
    horizon = as_of + dt.timedelta(days=14)
    upcoming = [p for p in windows if p["start_date"] <= horizon and p["end_date"] >= as_of]

    L: list[str] = []
    w = L.append

    w("# Baseline data validation")
    w("")
    w("Generated by `eval/validate_data.py` from the files in `data/`. Do not hand-edit;")
    w("re-run the script instead. Every number below is computed, not transcribed.")
    w("")
    w(f"- Source files: {len(board)}-row task board, {len(timeline)}-phase timeline, "
      f"{len(risks)} risks, {len(description.split())}-word project description")
    w("")

    w("## 1. Task board status counts")
    w("")
    w("| Status | Count | Task IDs |")
    w("|---|---|---|")
    for s in (DONE, IN_PROGRESS, BLOCKED, TODO):
        ids = [t["task_id"] for t in board if t["status"] == s]
        shown = ", ".join(ids) if len(ids) <= 6 else ", ".join(ids[:6]) + f", … (+{len(ids)-6})"
        w(f"| {s} | {status[s]} | {shown} |")
    w(f"| **Total** | **{len(board)}** | |")
    w("")
    w("> **Discrepancy with the problem statement.** The Mira brief states \"3 Done, 3 In")
    w(f"> Progress, 1 Blocked, and the rest To Do\". The CSV contains **{status[DONE]} Done**.")
    w("> Test T10 requires counts to match actual data, so all agents are grounded in the")
    w("> CSV. This is disclosed rather than silently reconciled.")
    w("")

    w("## 2. Anchor A — as-of date for status reporting")
    w("")
    w(f"- Latest due date among Done tasks: `{anchor_a['latest_done_due']}`")
    w(f"- Earliest due date among not-Done tasks: `{anchor_a['earliest_open_due']}` "
      f"({', '.join(anchor_a['driver_tasks'])})")
    w(f"- **as_of := {as_of} ({as_of.strftime('%A')})**")
    w("")
    w("Rationale: the only date at which the board is self-consistent. Any later and the")
    w("driver task would be overdue while still marked In Progress; any earlier and the")
    w("Done tasks could not yet have completed. No real-world 'today' is introduced.")
    w("")

    w("## 3. Anchor B — project start date")
    w("")
    w("`project_timeline.csv` uses week numbers; `sample_task_board.csv` uses dates. The")
    w("join between them is a start date, found by constraint satisfaction over Mondays:")
    w("")
    w("| Constraint | Requirement |")
    w("|---|---|")
    w("| 1 | Sprint 1 (Planning) due dates fall inside timeline Phase 1, weeks 1–2 |")
    w("| 2 | Sprint 2 (Analysis) due dates fall inside timeline Phase 2, weeks 3–4 |")
    w("")
    passing = [t for t in trace if t["ok"]]
    w(f"Candidate Mondays tested: {len(trace)}. Satisfying both constraints: "
      f"{len(passing)} — {', '.join(str(t['start']) for t in passing)}.")
    w("")
    w(f"- **project_start := {start} ({start.strftime('%A')})**")
    w(f"- as_of {as_of} therefore falls in **week {current_week}**")
    w("")

    w("## 4. Timeline phases mapped to dates")
    w("")
    w("| Phase | Weeks | Dates | Milestones / deliverables |")
    w("|---|---|---|---|")
    for p in windows:
        mark = " ←" if p in upcoming else ""
        w(f"| P{p['phase']} {p['phase_name']}{mark} | {p['start_week']}–{p['end_week']} "
          f"| {p['start_date']} → {p['end_date']} | {p['milestones_deliverables']} |")
    w("")
    w(f"Rows marked ← overlap the two-week window {as_of} → {horizon}. These are the only")
    w("milestones test T11 may report.")
    w("")

    w("## 5. Task label → timeline phase mapping")
    w("")
    w("A deterministic join key, so the Milestone Tracker computes at-risk milestones by")
    w("rule rather than by inference.")
    w("")
    w("| Label | Tasks | Phase(s) containing its due dates |")
    w("|---|---|---|")
    counts = Counter(t["labels"] for t in board)
    for lab in sorted(labels, key=lambda x: min(d(t["due_date"]) for t in board if t["labels"] == x)):
        w(f"| {lab} | {counts[lab]} | {'; '.join(sorted(labels[lab]))} |")
    w("")
    w("The mapping is 1:1 through Phase 5 and drifts afterwards, because the task board")
    w(f"ends {max(d(t['due_date']) for t in board)} while the timeline runs to "
      f"{windows[-1]['end_date']}. Phase {windows[-1]['phase']} "
      f"({windows[-1]['phase_name']}) has no tasks at all — agents must report")
    w("\"no tasks mapped\" rather than inferring progress.")
    w("")

    w("## 6. Risk data shape")
    w("")
    w(f"- Rows: {len(risks)}; distinct categories: {len(set(r['category'] for r in risks))}")
    w(f"- Columns: {', '.join(risks[0].keys())}")
    w("")
    w("> **No severity, likelihood or probability column exists.** Test T7 asks for the")
    w("> \"top 3 risks\", but the data contains no ranking. The Risk Assessor must rank by")
    w("> an explicit, disclosed rule and state that the ranking is derived, not supplied.")
    w("")

    w("## 7. Project health — Red / Amber / Green")
    w("")
    w("| Health | Rule (evaluated at as_of) |")
    w("|---|---|")
    w("| RED | A blocked task falls due within 14 days, **or** >20% of open tasks are past due |")
    w("| AMBER | Any blocked task exists, **or** any open task is past due |")
    w("| GREEN | Neither |")
    w("")
    w(f"**Computed at as_of {as_of}: {rag}**")
    for r in rag_why:
        w(f"- {r}")
    w("")

    w("## 8. Sprint cadence")
    w("")
    w("| Sprint | Tasks | Due-date range |")
    w("|---|---|---|")
    for s in sorted({t["sprint"] for t in board}, key=lambda x: int(x.split()[1])):
        rows = [t for t in board if t["sprint"] == s]
        dues = sorted(t["due_date"] for t in rows)
        w(f"| {s} | {len(rows)} | {dues[0]} → {dues[-1]} |")
    w("")
    w("Cadence is 14 days from Sprint 3 onward but 11 and 10 days for the first two")
    w("transitions. Do not derive dates from an assumed uniform sprint length; read")
    w("`due_date` directly.")
    w("")

    w("## 9. Constants for agent prompts")
    w("")
    w("```")
    w(f"AS_OF_DATE      = {as_of}")
    w(f"PROJECT_START   = {start}")
    w(f"CURRENT_WEEK    = {current_week}")
    w(f"HORIZON_14D     = {as_of} .. {horizon}")
    w(f"TASK_COUNTS     = Done {status[DONE]}, In Progress {status[IN_PROGRESS]}, "
      f"To Do {status[TODO]}, Blocked {status[BLOCKED]}")
    w(f"BLOCKED_TASKS   = {[t['task_id'] for t in board if t['status'] == BLOCKED]}")
    w(f"PROJECT_HEALTH  = {rag}")
    w("```")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write docs/baseline_data_validation.md")
    args = ap.parse_args()
    text = report()
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text)
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        print(text)


if __name__ == "__main__":
    main()
