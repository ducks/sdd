# Reliability contract

## General outcomes

Accepted jobs survive producer/worker process exit. Duplicate delivery with the
same identity/input does not repeat the intended business effect; conflicting
input under one identity is rejected. Transient failures retry within a finite
attempt budget; permanent/exhausted work enters an inspectable terminal state.
Timeouts bound execution, not merely how long a caller waits. Crashed ownership
can be reclaimed, while stale owners cannot acknowledge or publish effects.
Graceful shutdown stops new claims and preserves current/queued work safely.
Existing application behavior/tests remain intact.

## Tested reference profile

Python 3.12+, standard-library sqlite3, one SQLite database on a local filesystem,
multiple local worker processes, and process-isolated handlers. No server or
Python package dependency is needed. BEGIN IMMEDIATE transactions serialize
claim changes; busy_timeout bounds lock waiting. Default SQLite journal/synchronous
settings are retained. Database backups, migrations and power-loss durability
across filesystem/hardware configurations are not tested here.

Jobs carry a unique job_key, bounded JSON payload, pending/running/done/dead state,
attempt count/budget, available-at time, lease expiration and opaque ownership
token. Claiming consumes an attempt, including when a claimant crashes. Expired
final attempts become dead with lease_exhausted. Successful effect application
and done transition share one transaction. No automatic deletion/replay of dead
jobs is provided; inspect and make replay policy a deliberate application choice.

The effect guarantee is scoped to writes in that SQLite transaction, not remote
services. Preparation must perform pure computation or reads. It must not send
email, charge cards or mutate external systems. Apply must write only through
the supplied connection and remain short: SQLite permits one writer, and a slow
apply blocks the queue. Timeouts terminate the supervised child, rolling back
unfinished transactions. The token and lease are checked before apply while the
transaction owns the writer lock. A lease is not a real-time preemption mechanism
inside a transaction already in progress; keep that transaction bounded.

Retry backoff is deterministic exponential delay starting at 50ms, capped at one
second for fast local verification. This is not a recommended production retry
schedule. Real deployments should select appropriate backoff/jitter and visibility
renewal. The worker's task timeout is separate from a business deadline.

## Executable evidence

The verifier launches fresh processes, generates its own temporary databases,
and inspects jobs and business rows through sqlite3. It tests duplicates before
and after completion, three-attempt recovery/exhaustion, permanent failures,
killed timed-out children, two concurrent workers, expired-token rejection, a
process exiting after effect SQL but before acknowledgement commit, expired
claim recovery and SIGTERM between jobs. Reports use PASS/FAIL/SKIP/UNKNOWN;
exit 0 requires all checks PASS. POSIX shutdown is SKIP on other platforms.

Crash tests exercise process failure, not power loss. A worker parent killed by
SIGKILL cannot execute its cleanup; a separately sessioned child may survive
until its work ends. Local transactional fencing protects late commit, not
resource consumption. Production supervisors/cgroups and dependency deadlines
need separate verification. Multi-host queues, clock skew and arbitrary external
side effects are outside this reference profile.

## Sources used

- SQLite transaction semantics: https://www.sqlite.org/lang_transaction.html
- Busy handling: https://www.sqlite.org/rescode.html
- Python sqlite3 explicit transaction control: https://docs.python.org/3.12/library/sqlite3.html

The implementation uses isolation_level=None and explicit BEGIN/COMMIT/ROLLBACK;
it does not rely on context-manager implicit transaction defaults.
