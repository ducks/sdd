# Adaptation demonstration: catalog service

The starting application is retained in `examples/catalog-before`. It has a
Flask application factory, Blueprint routes, a separate domain lookup module,
four unittest cases and a signal-aware module entrypoint. It initially has no
metrics, Prometheus, Grafana or Compose deployment. It is not the WSGI baseline.

The adapted result is `examples/catalog-monitored`.

| Component | Decision |
| --- | --- |
| Domain code, Blueprint, behavior tests, startup/shutdown | Preserved byte for byte. App factory adds one instrumentation call. |
| Metric definitions | Reused baseline metrics.py under catalog/. No baseline application copied. |
| Instrumentation | Added Flask before/after hooks and /metrics; route labels use resolved templates. A registry belongs to each factory instance. |
| Error handling | Preserved existing 503 and handled 500 behavior, counted from actual response status. |
| Deployment and dashboards | Reused baseline monitoring files and Compose stack because this fixture had none. Dockerfile still runs python -m catalog. |
| Dependencies | Added prometheus-client; retained Flask and pinned transitive requirements. |
| Verification mapping | Adapted success/error/exception paths and resolved item-route label in acceptance.json. |

The resolved `/api/items/<int:item_id>` template is one series label across item
IDs, including missing items. Unknown routes use __unmatched__. Metrics and
readiness requests are excluded. Tests compare original domain/routes/entrypoint
and test files with the before version and exercise the adapted app independently.

The demonstration was implemented by the authoring agent with access to the
skill/resources and then verified independently. It is not a blind comparison,
a separate-agent experiment, or evidence of performance improvement.

## Observed verification

The live baseline and adapted app each passed all 19 checks. The adapted image
ran all four original tests. Real 200, 503 and exception-driven 500 traffic
increased Prometheus samples. Grafana's datasource health and proxied queries
worked; all three dashboard expressions returned finite series. SIGTERM exited
zero, target DOWN was observed and restart recovered collection.

No manual application edits by the user were necessary. The implementing agent
used Docker's available legacy builder because the host's Compose required a
newer Buildx plugin. A first baseline run exposed a verifier bug: restarting a
container can change its ephemeral host port. The checker now rediscovers that
port; the original failed run and subsequent successful reports are retained.

This fixture uses development-grade single-process HTTP servers for a local
PoC. Production worker/process models, streaming responses, auth, persistence,
network policy and metrics naming need application-specific review. No Go/Rust
adapter or Kubernetes support was implemented.
