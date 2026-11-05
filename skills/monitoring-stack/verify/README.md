# Independent verification

Python 3.12+ standard library, Docker Engine and Compose v2+ are required. No
model or agent is used. Review the target code, Dockerfile, Compose config,
volume mounts and tests first: building containers and running tests executes
code, and Docker daemon access is privileged. No target hooks are auto-discovered.
The explicit `--allow-exec` flag confirms execution within the environment's
existing authorization; it does not bypass the environment's permission checks.

From the SDD repository:

```sh
python3 skills/monitoring-stack/verify/run.py \
  --project skills/monitoring-stack/baseline \
  --output runs/baseline.json --allow-exec
python3 skills/monitoring-stack/verify/run.py \
  --project examples/catalog-monitored \
  --output runs/catalog.json --allow-exec
```

Without --allow-exec all checks are SKIP, with exit 2. Docker unavailable also
produces SKIP. A blocked check is UNKNOWN, not PASS. Failures exit 1; every check
must pass to exit zero. Run `--help` for arguments. On hosts with Compose but no
compatible Buildx, prefix the command with `DOCKER_BUILDKIT=0` if the Docker
legacy builder is available; no builder is installed or changed by the script.

The verifier uses an unpredictable project name, ephemeral loopback ports and a
random Grafana password. It runs a nonempty unittest suite inside the app image,
validates Compose/promtool configs, checks real traffic and API results, and
removes its project's containers, volumes, networks and locally built image in
finally. Pulled images and Docker build cache remain reusable; no global prune.
SIGKILL/host failure cannot execute cleanup: the JSON contains the project name
for `docker compose -p NAME -f /path/to/compose.yaml down --volumes --rmi local`.
Run only against a reviewed disposable fixture; restart/error probes are invasive.

The initial contract expects app/prometheus/grafana services, internal ports
8000/9090/3000, healthz/metrics endpoints, sdd-prometheus datasource UID and
sdd-application dashboard UID. `acceptance.json` maps fixture paths and routes.
It is not a general deployment checker. Adapt the checker transparently for an
existing deployment rather than modifying live infrastructure to match it.

Tests execute the fixed command `python -m unittest discover -s tests -v` in the
app container. Projects with other test runners should change this explicitly
and preserve evidence that tests ran. No arbitrary command is read from JSON.
