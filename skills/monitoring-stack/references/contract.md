# Monitoring acceptance contract

## Stack-independent outcomes

Use the resolved options to scope the integration. Preserve existing application
behavior and tests. Request volume, failure classification and latency must be
observable with bounded dimensions. Demonstrate that controlled traffic reaches
the chosen collection backend and produces queryable changes. If dashboards
are selected, verify their actual datasource and queries. Verify configuration,
application health and appropriate failure/recovery behavior using executable
checks. Never substitute configuration presence for runtime evidence.

For instrumentation-only work, prove the application's output and original tests;
collection/dashboard requirements remain outside that task's scope, not verified.
For a dashboards-only task, query the existing backend and validate the dashboard;
do not add instrumentation automatically. State the scoped contract explicitly.

Changing a backend requires adapting the implementation and verifier. This is
engineering work guided by a skill, not a promise of automatic backend support.

## Bundled tested profile: Python / Prometheus / Grafana / Compose

The reference vocabulary is deliberately small; existing integrations can retain
their established names if the corresponding verifier queries are reviewed.

- `http_requests_total{method,route,status_class}`: counter incremented once for
  each completed application response, including errors; status class is 1xx–5xx.
- `http_request_duration_seconds{method,route}`: histogram covering the same
  requests, measured through response construction with a monotonic clock; buckets 5ms through 5s plus +Inf.
  Tune buckets to actual latency/SLO needs when adapting; never label by duration.
- `http_errors_total{route,error_class}`: counter for completed 4xx (`client_error`)
  and 5xx (`server_error`) responses, including handled application exceptions.
  HTTP errors do not imply process crashes. Transport disconnects and aborted
  streaming requests are outside this baseline's completed-response definition.
- Only a fixed set of methods and resolved route templates may be labels.
  Unknown routes map to `__unmatched__`; never include raw paths or identifiers.
- `/metrics` responds with valid Prometheus exposition. `/healthz` reports process
  readiness. Neither endpoint contributes to request metrics.

Success requires real application HTTP traffic, valid Prometheus config and
exposition, one UP scrape target, increasing request/error/histogram samples
queryable in Prometheus, a working provisioned Grafana datasource and dashboard,
and the original application's nonempty test suite passing. Runtime checks also
exercise synthetic exceptions, bounded unmatched labels, SIGTERM, target DOWN
and recovery. Counters reset on process restart; consumers should use `rate` or
`increase`, not treat a decrease as negative traffic.

Dashboards use rates over one minute (the demo scrapes every second), calculate
histogram quantiles after preserving the `le` label, and use seconds for latency.
For a slower production scrape interval increase the rate window to at least
four scrape intervals. A health response does not prove healthy scraping.

The Compose demo publishes all ports on 127.0.0.1, generates a Grafana password
in the verifier, uses private service DNS for scraping, caps retention, and
persists no named volumes. These defaults are for disposable local validation,
not a production persistence, TLS, authentication or backup design.

Verification states:

| State | Meaning |
| --- | --- |
| PASS | The check executed and the observed result satisfied the assertion. |
| FAIL | The check executed and an assertion or command failed. |
| SKIP | A known prerequisite/authorization was absent; the check did not run. |
| UNKNOWN | A preceding failure or unavailable evidence prevented a conclusion. |

Exit 0 requires every check PASS; FAIL exits 1; otherwise incomplete evidence
exits 2. Cleanup is itself a check. Read the JSON results, not just an exit code.

Latency excludes transfer of the response body to the client. The baseline and
Flask hooks measure response construction, not end-to-end network time.
