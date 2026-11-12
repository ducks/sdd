.DEFAULT_GOAL := help
.PHONY: help setup format lint test check build clean release-check release

help: ## List the stable developer interface
	@python3 scripts/release.py help
setup: ## Validate installed native tools; enter nix-shell to obtain them
	@python3 scripts/release.py setup
format: ## Format Rust source with rustfmt
	cargo fmt
lint: ## Check formatting and Clippy warnings
	cargo fmt -- --check
	cargo clippy --locked --offline --all-targets -- -D warnings
test: ## Run unit, integration and documentation tests
	cargo test --locked --offline
check: lint test ## Complete local quality gate
build: ## Build the release binary without changing the lockfile
	cargo build --release --locked --offline
clean: ## Remove only the owned Cargo target directory
	@python3 scripts/release.py clean
release-check: check build ## Validate metadata, tree, tags, docs and the built binary
	@python3 scripts/release.py check
release: release-check ## Prepare and validate a local archive; never publish or tag
	@python3 scripts/release.py prepare
