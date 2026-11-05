# Reliable worker: invoice adaptation and evidence

The second skill tests whether the same packaging approach can cover stateful
failure handling rather than monitoring configuration. It is still an ordinary
Agent Skill; no dependency on monitoring-stack is introduced.

## Different starting application

`examples/invoices-before` is a synchronous package with integer-cents invoice
validation, a public render_invoice function, a stdin/stdout CLI and three tests.
It has no queue or worker. `examples/invoices-worker` keeps all four original
source/test files byte-identical and adds asynchronous execution alongside them.

Reused: the baseline's reliable.py transactional queue and worker.py supervisor.
Customized: handler.prepare calls the existing domain function, invalid domain
input is a permanent error, and handler.apply persists into invoice_reports.
The acceptance fixture maps an invoice payload and exact expected total. The
baseline's message fixture and result table are unchanged.

No framework/domain rewrite, broker, production migration or external API was
needed. The handler's simulation controls exist solely to exercise failure paths
in this local fixture; they are not a proposed production job interface.

## Commands executed

```sh
python3 skills/reliable-worker/verify/run.py --project skills/reliable-worker/baseline --output runs/worker-baseline.json --allow-exec
python3 skills/reliable-worker/verify/run.py --project examples/invoices-worker --output runs/worker-invoices.json --allow-exec
python3 tests/worker_controls.py --allow-exec
python3 -m unittest discover -s tests -p test_worker.py -v
make test
```

The baseline and adaptation were also run in the existing digest-pinned Python
3.12 container with networking disabled, no added packages, all capabilities
dropped and the source mounted read-only. Native development used Python 3.14.
The skill frontmatter validator and local documentation links were checked.

## Acceptance results

| Fixture/run | Outcome | Evidence |
| --- | --- | --- |
| Worker baseline, native | 14/14 PASS | [JSON](evidence/worker-baseline.json) |
| Invoice adaptation, native | 14/14 PASS; original three tests preserved | [JSON](evidence/worker-invoices.json) |
| Worker baseline, Python 3.12 | 14/14 PASS | [JSON](evidence/worker-baseline-python312.json) |
| Invoice adaptation, Python 3.12 | 14/14 PASS | [JSON](evidence/worker-invoices-python312.json) |
| Fencing deliberately removed | lease_fencing failed as expected; cleanup passed | [JSON](evidence/worker-missing-fence.json) |
| Timeout deliberately removed | bounded_timeout failed as expected; cleanup passed | [JSON](evidence/worker-missing-timeout.json) |

The process-level checks cover durable enqueue, conflicting/duplicate identities,
transient and permanent failures, retry exhaustion, killed timeouts, concurrent
workers, stale leases, process death inside the business-write transaction,
expired ownership recovery, SIGTERM drain, existing tests and cleanup. There were
no failed/skipped/unknown checks in the four positive runs. The two negative
control failures are intentional evidence of rejection, not passing integrations.
Temporary databases, journals and worker processes are removed by the harness.

## Decisions and limitations

Using sqlite3 avoids infrastructure dependencies in this reference. It also
means a local single-writer database, short transactional effects and local
clocks. This is not a replacement for a production distributed queue. Existing
Celery/RQ/native workers should retain their backend and receive adapted checks.

Only effects in the same SQLite transaction as acknowledgement get the tested
idempotency guarantee. Pure preparation followed by a short transactional apply
makes that boundary visible. External effects need their own idempotency/outbox
contract. Process crash tests are not power-loss durability tests. A parent
killed by SIGKILL cannot guarantee child cleanup; production supervisors and
long-running task renewal remain unverified.

The authoring agent implemented both versions using the skill/resources. No
user intervention was required. This is another feasibility demonstration, not
a blind A/B study or a measured agent-performance improvement. The existing A/B
preparer/scorer remains specific to monitoring-stack.
