---
name: frame-system-design
description: "Prepare, rehearse or review a system-design interview using FRAME: frame the problem, resolve requirements, choose a simple architecture, examine failure modes and evolve under new constraints. Use for interview practice or a requested FRAME design discussion."
license: MIT
---

# FRAME — system design

Use the user's FRAME framework to structure a 60-minute design discussion.
This is an interview practice aid, not an official ICEYE assessment rubric.
Accept a shorter time budget, a supplied problem and an explicit coaching or
candidate role. In rehearsal, ask focused questions and let the candidate answer;
do not deliver a complete polished solution before they have tried.

## Work the loop

**F — Frame.** Identify the user, desired outcome, primary workflow and boundary.
Restate the problem before drawing components. Surface consequential unknowns;
state assumptions rather than inventing requirements or company infrastructure.

**R — Requirements.** Separate essential behavior from optional features.
Resolve requests/data volume/concurrency/growth, latency/availability/durability/
consistency, existing systems, team size, cost and deployment constraints. Identify
the constraint that most changes the design. Use rough calculations where they
inform a decision, stating inputs and units rather than manufacturing precision.

**A — Architecture.** Start with the simplest viable design and draw its data
flow. Identify interfaces, persistent state and source of truth. Map every added
component to a requirement and compare an alternative before adding complexity.
Explain the principal trade-off aloud; don't substitute a list of technologies
for a working workflow. Use a small diagram if it makes the flow clearer.

**M — Modes of failure.** Follow requests and in-flight work through failures.
Discuss applicable timeouts, bounded retries, idempotency, backpressure, recovery
and user-visible behavior. Explain how logs, metrics or traces distinguish a
failure from normal operation. Choose signals and validation tied to this design;
do not add every observability tool by default.

**E — Evolve.** When a requirement changes, name the invalidated assumption,
affected component and bottleneck. Compare options, make the smallest justified
change, and state what test or measurement would validate it. Revisit earlier
choices instead of defending them after their assumptions have changed.

For each important decision record **assumption → choice → trade-off → validation**.
Keep this visible in the discussion; a design is conditional on its assumptions.

## Pace and conclude

Use [the playbook](references/playbook.md) for timing, a decision worksheet,
rehearsal prompts and a closing checklist. Default pacing: 0–10 clarify,
10–20 baseline architecture, 20–40 trade-offs/failure/observability,
40–55 evolving requirements, 55–60 summary. Adjust to the interviewer rather
than mechanically restarting phases or rushing into optional components.

Close with the end-to-end workflow, key decisions, unresolved risks and a concrete
validation plan. In a review, distinguish observed reasoning from unanswered
questions; do not invent interview scores, test results or performance evidence.
This skill requires no code execution, model provider or agent runtime.
