# SDD engineering workflow

skills/ contains ordinary portable Agent Skills. Each capability keeps its
baseline, references and independent verifier together. examples/ demonstrates
adaptation; tests/ owns regression and negative controls; docs/evidence/ records
actual execution. No agent runtime or model-provider integration belongs here.

Use nix-shell, make setup, make check and make build. make check includes the
Python tests and durable worker runtime/negative controls; Docker-backed monitoring
checks are separate: make verify-baseline verify-example controls. New foundation
checks run through make verify-foundation and make foundation-controls. Inspect
runs/*.json for per-check evidence; expected failures inside negative controls are
not suite failures. Use make format for new foundation code only; preserve older
skills' behavior and avoid unrelated formatting rewrites.

Audit mode never runs target code and writes reports outside evaluated projects.
--allow-exec authorizes reviewed code in disposable copies, not a hostile-code
sandbox. Do not expose secrets to fixtures. Keep cleanup confined to owned paths.

VERSION owns the source release number. Read RELEASE.md. make release-check
requires a clean committed tree unless an explicitly reviewed dirty preview is
requested; make release prepares local artifacts only. Commits, tags, pushes,
publication and deployments require explicit user authorization. Do not claim
SKIP/UNKNOWN as successful verification or publish unreviewed run logs.
