# Adapting the Python baseline

Inspect the framework and process model first. `baseline/app.py` is a standard
WSGI service; it is not a replacement for a target framework. `baseline/metrics.py`
is the small reusable part: prometheus-client instruments an isolated registry
and exposes text. Integrate it into the target's registry instead if one exists.

For Flask, bind one Metrics object per app factory instance. Record monotonic
start time in before_request; in after_request use request.url_rule.rule and the
response status. Handled 500s still pass through after_request. Use the existing
500 handler; do not expose exception messages. Register /metrics without
instrumenting it. Use __unmatched__ when URL resolution fails. The reference
adaptation preserves a Blueprint, domain layer, factory and tests.

For an ASGI app use its native middleware and route resolution; a sync WSGI
wrapper is inappropriate. For streaming responses record completion/abortion
explicitly; this simple completed-response contract does not cover streams.
Gunicorn/multiple workers require prometheus-client multiprocess configuration
and cleanup, or an existing shared collection design. Do not ship per-worker
registries that silently omit other workers. This prototype supports one worker.

Reuse compose.yaml, scrape settings and Grafana provisioning only if the target
lacks equivalents. Update app build context, port, health path, scrape job,
datasource UID and dashboard queries as a coherent change. Preserve env config
and startup/shutdown entrypoints. `acceptance.json` is verifier input, not a new
skill format: it maps the fixture's success/error paths and resolved labels.

Future Go/Rust adapters can replace only instrumentation/lifecycle advice and
implementation; the Prometheus/Grafana HTTP contract remains the same. No adapter
interface, discovery mechanism or dependency resolver is needed.
