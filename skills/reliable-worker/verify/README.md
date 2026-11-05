# Worker verification

Python 3.12+ standard library; no Docker, model, network or broker required.
Review the target handler, worker and tests before authorizing their execution.

```sh
python3 skills/reliable-worker/verify/run.py \
  --project skills/reliable-worker/baseline --output runs/worker-baseline.json --allow-exec
python3 skills/reliable-worker/verify/run.py \
  --project examples/invoices-worker --output runs/worker-invoices.json --allow-exec
python3 tests/worker_controls.py --allow-exec
```

The independent checker launches actual target CLI processes and reads persisted
SQLite state, rather than trusting target-written explanations. It expects the
reference CLI/API/job schema; acceptance.json maps a fixture payload, expected
result and result table. That file is ordinary test data, not a skill format.
The controller accepts only a plain SQL identifier for the table. For another
backend, adapt and review the checks rather than claiming these results cover it.

All 14 checks must PASS for exit 0; failures exit 1; SKIP/UNKNOWN exits 2. Without
--allow-exec every check is SKIP and no target code runs. Existing tests must be
nonempty and successful. Each behavioral check gets a fresh temporary database;
processes and database/journal files are cleaned afterward. POSIX SIGTERM is not
claimed on other systems. SQLite/network filesystems and Windows process-tree
behavior have not been tested.

The harness itself is not a hostile-code sandbox. Application tests execute code,
and fixtures must be reviewed. Synthetic crash subprocesses exit deliberately;
their expected nonzero exit is part of the assertion, not an ignored failure.
Negative controls remove ownership fencing or execution timeout and must be
rejected by the corresponding acceptance checks. Reports retain no job output,
raw exception payloads or secrets. Test databases are disposable.
