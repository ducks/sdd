.PHONY: test verify-baseline verify-example controls

test:
	python3 -m unittest discover -s tests -p 'test_*.py' -v
	python3 -m compileall -q skills examples evaluation

verify-baseline:
	python3 skills/monitoring-stack/verify/run.py --project skills/monitoring-stack/baseline --output runs/baseline.json --allow-exec

verify-example:
	python3 skills/monitoring-stack/verify/run.py --project examples/catalog-monitored --output runs/catalog.json --allow-exec

controls:
	python3 tests/runtime_controls.py --allow-exec

.PHONY: verify-worker verify-worker-example worker-controls
verify-worker:
	python3 skills/reliable-worker/verify/run.py --project skills/reliable-worker/baseline --output runs/worker-baseline.json --allow-exec

verify-worker-example:
	python3 skills/reliable-worker/verify/run.py --project examples/invoices-worker --output runs/worker-invoices.json --allow-exec

worker-controls:
	python3 tests/worker_controls.py --allow-exec
