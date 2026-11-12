# Make interface

Use help as the default goal and document all ten required targets. Phony targets
avoid collisions with files named test/build. Keep recipes thin: the native tool
or a reviewed helper is the implementation, Make is the stable public interface.

- setup validates/provisions the declared local environment; no implicit global
  installation. Nix users enter the reviewed shell first.
- format modifies source; lint checks without rewriting it.
- test discovers and executes assertions; reject empty suites.
- check combines formatting, lint, tests and applicable integration gates.
- build produces inspectable artifacts, using locked dependencies where possible.
- clean operates on owned generated directories, never `git clean -fdx` or broad
  home/tmp wildcards. Reject symlinks and uncontrolled path overrides.
- release-check runs check/build and release metadata/artifact prerequisites.
- release prepares locally, calling release-check. Publication is separate.

Use ordinary prerequisites and sequential recipes; don't swallow errors with
`|| true`, ignored exit codes or last-command success. Make's parallel execution
must not allow a release side effect to race its prerequisite. Platform-specific
shell commands should be disclosed. Rust uses cargo fmt, cargo clippy, cargo test
and cargo build, normally --locked; offline is appropriate for the dependency-free
baseline, not a universal requirement for uncached applications. Python and JS
should delegate to their existing tools. Preserve subproject target interfaces
in polyglot repositories instead of flattening their build systems.
