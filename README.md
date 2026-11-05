# Skill-Driven Development (SDD)

A small experiment in packaging an engineering capability as an ordinary
[Agent Skill](https://agentskills.io/specification): knowledge, a working
baseline, adaptation guidance and independent executable acceptance checks.

The first capability is **monitoring-stack**: Prometheus, Grafana, a Python HTTP
service and real checks that traffic produces queryable metrics. No agent
runtime, model API or hosted service is required to use or verify it.

This is a packaging practice, not a new skill specification. Ordinary skills
already support scripts and assets. Scaffolding already produces working code.
The question here is whether keeping a tested baseline and runtime verifier
with adaptation guidance helps agents integrate capabilities into existing apps.
The same acronym also means Spec-Driven Development elsewhere; this project
does not replace that methodology. See [research and architecture](docs/research.md).

## Try the capability

Requirements: Python 3.12+, Docker Engine, Docker Compose v2+, and authorized
container execution. First image/package downloads need network access; deployed
services and checks run locally. `nix-shell` supplies Python dependencies and
Docker clients without installing tools globally; a Docker daemon is still needed.

```sh
nix-shell                         # optional, or use your Python environment
make test                         # Python unit/integration tests, no Docker
make verify-baseline              # builds, runs all checks, removes owned resources
make verify-example               # same checks against the adapted Flask service
make controls                     # deliberately broken fixtures must be detected
```

The baseline's only application dependency is prometheus-client. The Flask
example adds Flask and its pinned dependencies. Container images are digest
pinned and Python requirements have hashes. No code is downloaded and executed
by skill discovery. Review skill resources, target code and Compose volumes
before authorizing builds or tests. Skill instructions cannot grant permissions.

`runs/*.json` records PASS/FAIL/SKIP/UNKNOWN per check. Exit zero requires all
checks PASS. Missing Docker, skipped execution or blocked checks never imply
success. [Verification details](skills/monitoring-stack/verify/README.md).

To inspect the disposable demo manually:

```sh
cd skills/monitoring-stack/baseline
export GRAFANA_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
docker compose up --build -d --wait
# App: http://127.0.0.1:18000    Prometheus: http://127.0.0.1:19090
# Grafana: http://127.0.0.1:13000 (admin / your generated password)
docker compose down --volumes --rmi local
```

The demo publishes only loopback ports. Do not expose it publicly without the
application's appropriate authentication/network design. It uses ephemeral
monitoring data; production storage and retention are separate decisions.

## Load the skill

The portable unit is the complete `skills/monitoring-stack` directory, beginning
with SKILL.md. Copy or symlink that directory into your compatible agent's
configured skill search path; installation paths differ between clients. No
repository-specific agent config is necessary. An agent that can read files can
also load SKILL.md explicitly from this checkout and follow its relative links.
No plugin manifest or provider integration is required. Normal agentskills
installers can distribute this layout when the repository is published.

> Add a Prometheus and Grafana monitoring stack to this application using the
> `monitoring-stack` skill. Preserve the existing architecture, instrument
> request latency and failures, and verify that Prometheus collects the metrics.

The skill accepts ordinary task options; omitted values are resolved by inspecting
the application. For example, include this in the request:

```yaml
language: auto
metrics: prometheus
dashboards: grafana
deployment: compose
scope: full
```

You can also request “instrumentation only, keep our existing collector, no
Grafana.” This changes the adaptation scope; it does not install another stack.
[Options and coverage](skills/monitoring-stack/references/options.md) explain
resolution and tested configurations. Other backends/languages require suitable
implementations and executable checks; selecting them does not make the supplied
Prometheus/Grafana verifier generic.

Load SKILL.md first, then only the applicable adapter/contract/implementation
resources. Do not dump the whole baseline into context. Inspect existing
monitoring first and extend it; do not duplicate a registry or stack. Adapt the
reference to the application, not the application to the reference.

The [before/after Flask example](docs/adaptation.md) preserves a factory,
Blueprint and domain layer while reusing the metric helper and provisioning.
[The contract](skills/monitoring-stack/references/contract.md) defines observable
success. The baseline and demo passed real Prometheus/Grafana checks; see the
[implementation report](docs/implementation-report.md) for evidence and limits.

## Evaluate the idea

[Evaluation protocol](evaluation/README.md) prepares clean A/B workspaces and
scores completed implementations with the same external verifier and original
tests. It does not invoke agents or integrate any provider. Agent time, tokens
and tool calls remain unmeasured until actual paired runs are performed.
Feasibility is demonstrated; a performance improvement is not established.

## Add another capability

Create an ordinary skill directory with name/description frontmatter. Include
only guidance that changes engineering decisions. Supply the smallest working
reference, explicit observable contract, selective adaptation guidance and an
independent checker that can reject broken implementations. Test it in a
structurally different application and retain honest evidence. Optional resource
directory names are not a new schema; use what the capability actually needs.

## Scope

This prototype supports disposable local Compose deployments and single-process
Python HTTP services. It has no package registry, dependency resolver, agent
orchestration, proprietary integration, Kubernetes, tracing, alert manager or
production deployment controller. Go/Rust adapters, production worker models,
streaming request semantics and broad framework support remain future work.
