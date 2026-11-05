"""Prove the independent worker verifier detects missing fencing and missing timeouts."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def run(output):
    output.mkdir(parents=True,exist_ok=True)
    summary=[]
    for fault,expected in [('missing-fence','lease_fencing'),('missing-timeout','bounded_timeout')]:
        with tempfile.TemporaryDirectory(prefix='sdd-worker-control-') as directory:
            target=Path(directory)/'worker'
            shutil.copytree(ROOT/'skills/reliable-worker/baseline',target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            if fault=='missing-fence':
                path=target/'reliable.py'
                path.write_text(path.read_text().replace(" or job['token'] != token",''))
            else:
                path=target/'worker.py'
                path.write_text(path.read_text().replace('child.wait(timeout=timeout)','child.wait()'))
            report=output/(fault+'.json')
            p=subprocess.run([sys.executable,str(ROOT/'skills/reliable-worker/verify/run.py'),
                '--project',str(target),'--output',str(report),'--allow-exec'],timeout=60)
            data=json.loads(report.read_text())
            detected=p.returncode==1 and data['checks'][expected]['status']=='FAIL' and data['checks']['cleanup']['status']=='PASS'
            summary.append({'fault':fault,'expected_failed_check':expected,'detected':detected,'report':report.name})
            print('CONTROL '+fault+': '+('PASS' if detected else 'FAIL'),flush=True)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return 0 if all(row['detected'] for row in summary) else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--allow-exec',action='store_true');p.add_argument('--output',type=Path,default=ROOT/'runs/worker-controls');args=p.parse_args()
    if not args.allow_exec:p.error('Review the fixtures and supply --allow-exec')
    sys.exit(run(args.output))
