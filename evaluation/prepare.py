"""Prepare clean paired workspaces. This never runs an agent or downloads code."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
PROMPT='''Add a Prometheus and Grafana monitoring stack to this application. Preserve its architecture and existing behavior. Instrument request latency and failures and verify that Prometheus collects the metrics.

Use Docker Compose for the local deployment. Keep published ports on loopback. The independent acceptance harness expects app/prometheus/grafana services on internal ports 8000/9090/3000, /metrics and /healthz, a Prometheus job named application, Grafana datasource UID sdd-prometheus and dashboard UID sdd-application. Use http_requests_total{method,route,status_class}, http_errors_total{route,error_class} and http_request_duration_seconds{method,route}. Use route templates, __unmatched__ for unmatched routes and client_error/server_error classes. Exclude health and metrics endpoints. Preserve SIGTERM shutdown. Add no public credentials. The fixture's /api/unavailable and /api/crash exercise errors. Existing tests must pass.

Report commands, verification evidence, limitations and manual interventions. You have 30 minutes, the same available tools and model as the other arm, and a clean Docker environment with cached images. Do not modify the independent harness or the original test oracle.
'''

def prepare(destination):
    destination=Path(destination).resolve();destination.mkdir(exist_ok=False,parents=True)
    for arm in ('A','B'):
        target=destination/arm;target.mkdir()
        shutil.copytree(ROOT/'examples/catalog-before',target/'app',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (target/'requirement.txt').write_text(PROMPT)
    shutil.copytree(ROOT/'skills/monitoring-stack',destination/'B/skills/monitoring-stack',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (destination/'B/skill-availability.txt').write_text('An ordinary Agent Skill is available at skills/monitoring-stack/SKILL.md. Use it for this task.\n')
    manifest={'schema_version':1,'state':'prepared_not_run','prompt_sha256':hashlib.sha256(PROMPT.encode()).hexdigest(),
        'arms':{'A':'Conventional implementation, no skill access','B':'Same requirement with monitoring-stack available'},
        'metrics':{'model':None,'time_limit_seconds':1800,'time_to_completion_seconds':None,'tool_calls':None,'input_tokens':None,'output_tokens':None,'manual_interventions':None},
        'note':'Choose the same agent/model/settings/tools for both arms. No agent has been invoked by this script.'}
    (destination/'experiment.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return destination

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);print(prepare(p.parse_args().destination))
