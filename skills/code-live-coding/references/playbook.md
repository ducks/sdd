# CODE playbook

| Time | Focus | Evidence to retain |
|---|---|---|
| 0–10 | Extract safely, inspect, run baseline | Architecture sketch, test commands and initial behavior |
| 10–15 | Scope implementation and signals | Acceptance criteria, affected files and failure cases |
| 15–40 | Small reviewed changes | Diffs and incremental test results |
| 40–50 | Tests and live behavior | Exercised feature, changing metrics, useful logs |
| 50–60 | Final walkthrough | Behavior, trade-offs, limitations and next improvements |

## Initial exploration prompt

```text
Inspect this repository without modifying files.

Identify:
- Application entry points and components
- Existing tests and how to run them
- Relevant Docker Compose services
- Current observability instrumentation
- Likely areas affected by the requested change

Summarize the architecture and potential risks.
Do not implement anything yet.
```

The instruction is read-only: running project commands needs separate review and
authorization. Follow exploration with your own inspection of the cited files.
Do not accept the model's architecture summary without checking it.

## Small development prompt

```text
Implement only [one behavior] in [reviewed files/components].
Preserve [existing interface and invariants].
Reuse [existing library/instrumentation] rather than adding a framework.
Cover [success case] and [failure case] with the project's existing tests.
Do not change unrelated files. Explain the diff and report the tests actually run.
```

Review before the next prompt. If a test fails, understand whether it exposed a
regression, pre-existing behavior or an environment problem. Don't weaken the
assertion simply to finish within the interview window.

## Observability selection

| Signal | Appropriate examples | Verification |
|---|---|---|
| Counter | Completed jobs, failures, retries | Compare before/after samples for controlled operations |
| Histogram | Processing/request duration in seconds | Observe count and bucket changes; choose useful buckets |
| Gauge | Active jobs, queue depth, resources | Observe increases and decreases, including failure cleanup |
| Structured logs | Context and classified errors | Exercise the path and inspect relevant records |

Do not label metrics with job/user IDs, raw URLs or exception messages. Use bounded
operation/outcome/error-class labels. Do not count a retry as another successful
business operation. Preserve existing metric registry and deployment ownership.
Avoid double instrumentation. Do not log secrets. Choose signals appropriate to
the actual task; not every exercise needs every metric type.

Where Prometheus exists, generate controlled traffic, confirm the target is up,
query the relevant samples and demonstrate changes. Container status or the mere
presence of /metrics is insufficient. Existing SDD monitoring/worker skills can
help with deeper work, but are not required dependencies of this interview guide.

## Final walkthrough

Explain what changed, trace the primary data flow, show tests and actual service
behavior, and discuss failure handling. Name remaining risks and checks that could
not run. Finish with the smallest next improvement you would make if more time
were available. Review git diff for accidental files and unintended edits.
