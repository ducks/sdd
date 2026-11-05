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
