# Task options

Options are ordinary task inputs interpreted by the agent. They are not new
SKILL.md frontmatter, a scripting language, an installer or a runtime API.
Supply them in prose, a mapping in the prompt, or a reviewed data file explicitly
named by the user. Loading a file never authorizes scripts or side effects.

| Option | Default | Meaning |
| --- | --- | --- |
| `language` | `auto` | Detect the target's language/framework. A preference does not authorize rewriting the app in another language. |
| `metrics` | `auto` | Retain an existing collection backend; if absent, propose the bundled Prometheus reference. An explicit backend is a constraint. |
| `dashboards` | `auto` | Reuse existing visualization; if absent, propose Grafana for a full integration. `none` explicitly omits dashboards. |
| `deployment` | `auto` | Extend the existing deployment. With none present, use the local Compose reference if appropriate. Never migrate the app merely to fit a baseline. |
| `scope` | `full` | `full`, `instrumentation`, or `dashboards`. Scope controls components to change and acceptance obligations; it does not weaken the selected checks. |

For `scope: instrumentation`, auto backend/dashboard choices do not authorize
installing servers. For `scope: dashboards`, retain the existing collection and
instrumentation; establish that it provides the required signals before adding
panels. Explicit incompatible choices require resolution, not silent fallback.

Reuse existing infrastructure by default. Replacements require explicit task
scope. `auto` is a discovery instruction, not a request to choose a new stack.
Endpoints, ports, metric prefixes, buckets, registries and datasource IDs should
normally come from project inspection; callers may constrain these in prose
without a growing universal options schema.

## Examples

With this SKILL.md loaded, the request can include:

```yaml
language: auto
metrics: prometheus
dashboards: grafana
deployment: compose
scope: full
```

Or: “Use monitoring-stack to add request/error/latency metrics to this Go service.
Keep our existing Prometheus and deployment. Instrumentation only; no Grafana.”
This is valid input, but the Go implementation and matching tests must be supplied
and run during adaptation. There is no bundled Go baseline or tested Go adapter.

Or: “Use monitoring-stack with our existing OpenTelemetry collector and existing
visualization. Preserve the current deployment.” This selects general guidance;
it does not make the Prometheus-specific verifier applicable to OTLP ingestion.

## Resolve and report

Record a short resolved plan, for example:

```text
Language: Python / Flask (detected)
Metrics: Prometheus (requested; existing service retained)
Dashboards: none (requested)
Deployment: existing Compose (detected)
Scope: instrumentation
Resources: Python adapter + metric helper; no server/provisioning files copied
Verification: original app tests + exposition/traffic checks; existing collector
checked if authorized/reachable; bundled full-stack verifier not applicable
```

The full-stack verifier always requires the complete bundled profile. It must
not report full success when Grafana is omitted or a different backend is selected.
Scoped verification needs an explicit executable check set; record missing checks
as SKIP/UNKNOWN and do not claim a full-stack integration passed. Include the
resolved options and applicable contract in the final report.

## Current evidence boundary

| Configuration | Status |
| --- | --- |
| Python WSGI + Prometheus + Grafana + Compose, full scope | Working baseline; live acceptance tested |
| Python Flask + Prometheus + Grafana + Compose, full scope | Adaptation example; live acceptance tested |
| Other languages, collectors, visualization or deployment | General guidance only; implementation/checks must be adapted |
| Instrumentation-only / dashboards-only verification | Scoped guidance; no dedicated bundled verification mode yet |

No custom parser, backend plugin registry or dependency resolution is introduced.
