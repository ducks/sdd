# Optional example verifier

This supports the Rust example and limited static inventory. It is not the main
entry point or a required gate for codebase-foundation. The skill's playbook
applies to Go, Python and other projects without this checker. Use their native
tests, startup/build checks, screenshot review and CI/release evidence. This tool
does not verify a complete environment, screenshot workflow or CI/CD system.

Python 3.12+ standard library. From any directory:

```sh
python3 SKILL/verify/run.py --project TARGET --output /tmp/foundation.json
python3 SKILL/verify/run.py --project REVIEWED_TARGET --output /tmp/verified.json --allow-exec
```

Audit reads only, including Make text (never make -n), native metadata, changelog,
documentation, Nix and GitHub workflow commands. It reports direct Make targets;
included/computed rules and dynamic/workspace versions need manual review.
It does not validate arbitrary shell/YAML semantics. Presence checks state what
was detected, not that the environment or release process works.

Execution is opt-in. The checker copies a reviewed project to a temporary tree,
excluding Git, environment files and generated directories, rejects symlinks,
uses a credential-stripped environment, bounds per-command time/output/file
sizes, terminates process groups and removes its copy. It is NOT a security
sandbox: authorized code still has the operator's filesystem/network permissions.
Use an OS/container sandbox for untrusted code. No network or hostile project
execution is authorized by this skill. Never put secret fixtures in the source.

Behavioral checks run make help/setup/lint/test/check/build, require a nonzero
native test count, inject a failing test into the COPY for Rust/Python, confirm
failure propagation and mutate Rust metadata to check release rejection. Test
locations vary: UNKNOWN means adapt the probe, not proof the suite is broken.
The exact reviewed baseline release helper permits additional local release and
symlink-cleanup probes, independent archive/version/binary/checksum validation.
Alternative release/cleanup helpers remain UNKNOWN until reviewed with equivalent
checks. Matching the helper is not a requirement for a valid engineering solution.
The verifier never runs make format on the original and never publishes anything.

Exit 1: at least one FAIL. Exit 2: no FAIL but SKIP/UNKNOWN remains. Exit 0: all
reported checks executed or are NOT APPLICABLE. The Rust baseline should reach
zero with authorization. NOT APPLICABLE is a scope conclusion, not execution.
Reports include executed command, exit code, timeout and bounded logs. Static
audits generally return 1 for gaps or 2 for incomplete runtime evidence.

`make foundation-controls` runs isolated defective fixtures: missing check,
no-op test, swallowed check failure, unchecked release version, publishing
without approval, incompatible changelog, nonexistent CI/docs targets, escaping
cleanup and undeclared tool. It also tests a working baseline, readonly audit,
execution authorization, timeout, alternate Make implementation and release
failure paths. See docs/codebase-foundation-report.md for actual results.
