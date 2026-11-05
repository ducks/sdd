"""Run the same trusted acceptance tests on a completed arm, independent of an agent."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def score(app,output):
    with tempfile.TemporaryDirectory(prefix='sdd-evaluation-') as directory:
        target=Path(directory)/'app';shutil.copytree(app,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git','.env'))
        # Keep the test oracle and fixture mapping outside either agent's control.
        shutil.rmtree(target/'tests',ignore_errors=True)
        shutil.copytree(ROOT/'examples/catalog-before/tests',target/'tests',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        shutil.copy2(ROOT/'examples/catalog-monitored/acceptance.json',target/'acceptance.json')
        return subprocess.run([sys.executable,str(ROOT/'skills/monitoring-stack/verify/run.py'),'--project',str(target),'--output',str(output.resolve()),'--allow-exec'],timeout=600).returncode

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--app',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--allow-exec',action='store_true');args=p.parse_args()
    if not args.allow_exec:p.error('review the completed app and pass --allow-exec before executing it')
    sys.exit(score(args.app,args.output))
