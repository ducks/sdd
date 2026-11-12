.DEFAULT_GOAL := help
.PHONY: help setup format lint check build clean release-check release test verify-baseline verify-example controls

test: ## Run all capability unit and contract tests
	python3 -m unittest discover -s tests -p 'test_*.py' -v
	python3 -m compileall -q skills examples evaluation

verify-baseline: ## Run live monitoring baseline checks (Docker)
	python3 skills/monitoring-stack/verify/run.py --project skills/monitoring-stack/baseline --output runs/baseline.json --allow-exec

verify-example: ## Run live adapted monitoring checks (Docker)
	python3 skills/monitoring-stack/verify/run.py --project examples/catalog-monitored --output runs/catalog.json --allow-exec

controls: ## Reject broken monitoring integrations (Docker)
	python3 tests/runtime_controls.py --allow-exec

.PHONY: verify-worker verify-worker-example worker-controls
verify-worker: ## Run durable worker baseline checks
	python3 skills/reliable-worker/verify/run.py --project skills/reliable-worker/baseline --output runs/worker-baseline.json --allow-exec

verify-worker-example: ## Verify the adapted invoice worker
	python3 skills/reliable-worker/verify/run.py --project examples/invoices-worker --output runs/worker-invoices.json --allow-exec

worker-controls: ## Reject broken worker integrations
	python3 tests/worker_controls.py --allow-exec

help: ## List available commands
	@python3 scripts/foundation.py help
setup: ## Validate Python, Rust, Ruff, Make and Git; use nix-shell for tools
	@python3 scripts/foundation.py setup
format: ## Format foundation Python and Rust reference source
	ruff format skills/codebase-foundation scripts tests/test_foundation.py
	cargo fmt --manifest-path skills/codebase-foundation/baseline/Cargo.toml
lint: ## Check Python syntax, foundation style and Rust formatting
	python3 scripts/foundation.py lint
check: lint test verify-worker verify-worker-example worker-controls ## Complete non-Docker local verification
build: ## Build and inspect the portable source bundle
	python3 scripts/foundation.py source-build
clean: ## Remove only the owned source distribution directory
	python3 scripts/foundation.py clean
release-check: check build verify-baseline verify-example controls ## Validate all capabilities and release metadata
	python3 scripts/foundation.py check
release: release-check ## Prepare local artifacts; no publication or tags
	python3 scripts/foundation.py prepare

.PHONY: verify-foundation foundation-controls
verify-foundation: ## Exercise the Rust foundation in a disposable copy
	python3 skills/codebase-foundation/verify/run.py --project skills/codebase-foundation/baseline --output runs/foundation.json --allow-exec
foundation-controls: ## Run adversarial controls and mode demonstrations
	python3 -m unittest discover -s tests -p 'test_foundation.py' -v
