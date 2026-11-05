# Python adaptation

Keep the existing job framework when one exists: Celery/RQ/framework-native
retries, acknowledgements and visibility settings have different contracts. Read
and test those semantics instead of wrapping this local queue around them.

For a new local worker, the reusable baseline is reliable.py plus worker.py.
The small handler module has three explicit application functions:

- initialize(connection): ensure the domain result table exists (demo setup;
  use normal migrations in an existing application).
- prepare(payload, attempt): pure computation/reads returning a result, with no
  externally visible writes. Raise PermanentError for invalid input and
  TransientError for a recoverable dependency failure.
- apply(connection, job_key, result): short business write using that connection;
  finish commits it with the acknowledgement. Never commit independently.

This is an ordinary function boundary, not a dynamic plugin system. Worker
payloads cannot name functions, import modules or select commands. The reference
CLI always imports its application-owned handler.py.

The invoice example preserves its synchronous package API/CLI and domain module,
and adds a queue-facing handler. Its existing integer-money validation becomes
a permanent failure; a successful result is written to invoice_reports. No email,
HTTP call or file write is presented as transactionally protected by SQLite.

Adapt timeout/lease bounds, payload validation, key scope, attempt budgets,
shutdown and retry schedule to the actual task. The child is supervised with a
real process timeout; do not replace it with a Future timeout that leaves work
running. SIGTERM drains the current task within the configured work bound and
then stops claiming. Default idle-exit=0 means keep polling; a positive idle-exit
is useful for tests and exits only when no unfinished jobs remain.

Keep SQLite on a suitable local filesystem, not an assumed cross-host queue.
No heartbeat or multi-host clock protocol is implemented. If jobs outlive the
lease, add/test renewal or select a longer lease; do not simply accept expired
owners. External effects require a separately reviewed idempotency/outbox design.
