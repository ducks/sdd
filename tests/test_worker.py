import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

engine=load('reliable_reference',ROOT/'skills/reliable-worker/baseline/reliable.py')
checker=load('worker_checker',ROOT/'skills/reliable-worker/verify/run.py')


class WorkerContractTests(unittest.TestCase):
    def test_retry_is_not_available_before_backoff(self):
        with tempfile.TemporaryDirectory() as directory:
            q=engine.Queue(Path(directory)/'jobs.sqlite');q.initialize();q.enqueue('key',{'message':'hello'})
            job=q.claim()
            self.assertTrue(q.fail(job['id'],job['token'],'transient'))
            next_at=q.get(job['id'])['available_at']
            self.assertIsNone(q.claim(now=next_at-.001))
            self.assertEqual(q.claim(now=next_at+.001)['attempts'],2)

    def test_expired_last_attempt_becomes_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            q=engine.Queue(Path(directory)/'jobs.sqlite');q.initialize();job_id=q.enqueue('key',{},1)
            job=q.claim(.1)
            self.assertIsNone(q.claim(now=job['lease_until']+.01))
            self.assertEqual(q.get(job_id)['state'],'dead')
            self.assertEqual(q.get(job_id)['error_code'],'lease_exhausted')

    def test_failed_business_write_rolls_back_and_does_not_ack(self):
        with tempfile.TemporaryDirectory() as directory:
            q=engine.Queue(Path(directory)/'jobs.sqlite');q.initialize();job_id=q.enqueue('key',{})
            with q.transaction() as db:db.execute('CREATE TABLE effects(value TEXT)')
            job=q.claim()
            def broken(db,key,result):
                db.execute("INSERT INTO effects(value) VALUES('partial')")
                raise RuntimeError('failed business operation')
            with self.assertRaises(RuntimeError):q.finish(job_id,job['token'],{},broken)
            with sqlite3.connect(q.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM effects').fetchone()[0],0)
            self.assertEqual(q.get(job_id)['state'],'running')

    def test_worker_requires_execution_authorization(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'results.json'
            v=checker.Verification(ROOT/'skills/reliable-worker/baseline',output)
            self.assertEqual(v.run(),2)
            self.assertEqual({r['status'] for r in json.loads(output.read_text())['checks'].values()},{'SKIP'})

    def test_invoice_domain_cli_and_original_tests_preserved(self):
        before=ROOT/'examples/invoices-before';after=ROOT/'examples/invoices-worker'
        for filename in ('invoices/__init__.py','invoices/__main__.py','invoices/domain.py','tests/test_invoices.py'):
            self.assertEqual((before/filename).read_bytes(),(after/filename).read_bytes())
        for project in (before,after):
            test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=project,text=True,capture_output=True)
            self.assertEqual(test.returncode,0,test.stderr)
            self.assertIn('Ran 3 tests',test.stderr)
            invoice={'id':'INV-1','currency':'EUR','lines':[{'cents':125}]}
            cli=subprocess.run([sys.executable,'-m','invoices'],cwd=project,input=json.dumps(invoice),text=True,capture_output=True)
            self.assertEqual(cli.returncode,0,cli.stderr)
            self.assertEqual(json.loads(cli.stdout),{'invoice':'INV-1','currency':'EUR','total_cents':125})
