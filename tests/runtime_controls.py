"""Real negative controls in disposable copies. Requires reviewed Docker execution."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def run(output):
    output.mkdir(parents=True,exist_ok=True)
    results=[]
    for fault,expected in [('broken-scrape','prometheus_target_up'),('frozen-counters','request_counter'),('broken-datasource','grafana_datasource')]:
        with tempfile.TemporaryDirectory(prefix='sdd-control-') as directory:
            project=Path(directory)/'baseline';shutil.copytree(ROOT/'skills/monitoring-stack/baseline',project)
            if fault=='broken-scrape':
                p=project/'monitoring/prometheus.yml';p.write_text(p.read_text().replace('app:8000','app:9'))
            elif fault=='frozen-counters':
                p=project/'metrics.py';p.write_text(p.read_text().replace('.inc()','.inc(0)'))
            else:
                p=project/'monitoring/grafana/provisioning/datasources/prometheus.yaml';p.write_text(p.read_text().replace('prometheus:9090','prometheus:9'))
            report=output/(fault+'.json')
            process=subprocess.run([sys.executable,str(ROOT/'skills/monitoring-stack/verify/run.py'),'--project',str(project),'--output',str(report),'--allow-exec','--wait-seconds','3'],timeout=240)
            data=json.loads(report.read_text())
            detected=process.returncode==1 and data['checks'][expected]['status']=='FAIL' and data['checks']['cleanup']['status']=='PASS'
            results.append({'fault':fault,'expected_failed_check':expected,'detected':detected,'report':report.name})
            print(f'CONTROL {fault}: '+('PASS' if detected else 'FAIL'),flush=True)
    (output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    return 0 if all(r['detected'] for r in results) else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--allow-exec',action='store_true');parser.add_argument('--output',type=Path,default=ROOT/'runs/controls')
    args=parser.parse_args()
    if not args.allow_exec:parser.error('review the fixtures and pass --allow-exec to authorize their execution')
    sys.exit(run(args.output))
