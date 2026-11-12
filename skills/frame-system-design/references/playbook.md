# FRAME playbook

## 60-minute guide

| Time | Focus | Useful output |
|---|---|---|
| 0–10 | Users, workflow, boundary, constraints | Restated problem and important assumptions |
| 10–20 | Simplest viable architecture | Data-flow sketch, interfaces, persistent state and source of truth |
| 20–40 | Trade-offs, failures and observability | Failure behavior, bounded recovery and diagnostic signals |
| 40–55 | New requirements | Changed assumption, minimal revision and validation |
| 55–60 | Walkthrough and summary | Decisions, risks, unanswered questions, next measurements |

These are conversational time boxes, not a requirement to leave important questions
unanswered. Revisit requirements when new information changes them.

## Decision worksheet

```text
User / outcome:
Primary workflow:
System boundary:
Essential behavior / optional behavior:
Scale and units:
Latency / availability / durability / consistency:
Existing systems / team / cost / deployment:
Most influential constraint:

Decision:
  Assumption:
  Choice:
  Alternative considered:
  Trade-off:
  Validation or measurement:

Failure:
  Affected request or in-flight work:
  Detection:
  User-visible effect:
  Recovery / retry bound / idempotency boundary:

New requirement:
  Assumption that changed:
  Bottleneck / affected component:
  Smallest justified change:
  How to validate:
```

## Rehearse an evolving problem

Use a supplied interview prompt first. If none is provided, this is a synthetic
practice case, not a claim about ICEYE's interview:

“Design a service that accepts image-processing jobs and lets a customer retrieve
the result. Start by asking what matters to the customer.”

Reveal one change after the candidate explains a baseline: bursts in arrivals,
duplicate job submissions, a worker dying mid-job, a customer cancellation, or
a tighter completion deadline. Ask which assumption changed and what evidence
would justify a more complex design. Do not quietly add all changes at once.
In review mode, ask why a component exists and what simpler alternative was
rejected. A verbal design is not proof of load, durability or recovery behavior.

## Useful phrasing

- “I'm assuming eventual consistency is acceptable here; is that right?”
- “At this scale, I'd start with the simpler option because…”
- “The trade-off is less operational complexity versus…”
- “I'd validate that assumption with a load test or production metric.”

## Closing check

Can another engineer follow one successful request through the sketch? Is the
source of truth clear? Does every component serve a stated requirement? What
happens to in-flight work on failure? Which assumption is most uncertain? What
changes first under growth? Which measurement or test would settle that question?

Give specific feedback on those points. Avoid grading diagram polish or the
number of named technologies as a substitute for engineering judgment.
