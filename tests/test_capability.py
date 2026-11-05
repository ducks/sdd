import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

metrics=load('reference_metrics',ROOT/'skills/monitoring-stack/baseline/metrics.py')
verifier=load('verification',ROOT/'skills/monitoring-stack/verify/run.py')

class ContractTests(unittest.TestCase):
    def test_metric_types_classification_and_method_bounds(self):
        m=metrics.Metrics()
        m.observe('UNBOUNDED_METHOD','/',503,.2)
        m.observe('GET','__unmatched__',404,.01)
        text=m.render()[0].decode()
        self.assertIn('# TYPE http_requests_total counter',text)
        self.assertIn('# TYPE http_request_duration_seconds histogram',text)
        self.assertIn('error_class="server_error"',text)
        self.assertIn('error_class="client_error"',text)
        self.assertIn('method="OTHER"',text)
        self.assertNotIn('UNBOUNDED_METHOD',text)

    def test_registries_are_independent(self):
        a=metrics.Metrics();b=metrics.Metrics();a.observe('GET','/',200,.1)
        self.assertIn(b'http_requests_total{',a.render()[0])
        self.assertNotIn(b'http_requests_total{',b.render()[0])

    def test_existing_application_files_preserved(self):
        before=ROOT/'examples/catalog-before';after=ROOT/'examples/catalog-monitored'
        for file in ('catalog/domain.py','catalog/routes.py','catalog/__main__.py','tests/test_catalog.py'):
            self.assertEqual((before/file).read_bytes(),(after/file).read_bytes(),file)
        self.assertNotIn('monitoring',(before/'catalog/__init__.py').read_text())

    def test_applications_tests_execute(self):
        for project,count in [('skills/monitoring-stack/baseline',1),('examples/catalog-before',4),('examples/catalog-monitored',4)]:
            result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT/project,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn(f'Ran {count} test',result.stderr)

    def test_flask_bounded_routes_and_exception_recording(self):
        code='''from catalog import create_app
app=create_app();client=app.test_client()
for n in (42,7,99999):client.get('/api/items/'+str(n))
client.get('/api/crash')
text=client.get('/metrics').data.decode()
assert 'route="/api/items/<int:item_id>"' in text
assert '/api/items/99999' not in text
assert 'error_class="server_error"' in text
'''
        p=subprocess.run([sys.executable,'-c',code],cwd=ROOT/'examples/catalog-monitored',text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_execution_requires_authorization_and_incomplete_is_not_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'report.json'
            v=verifier.Verification(ROOT/'skills/monitoring-stack/baseline',output)
            with patch.object(subprocess,'run',side_effect=AssertionError('must not execute')):
                self.assertEqual(v.run(),2)
            self.assertEqual({r['status'] for r in json.loads(output.read_text())['checks'].values()},{'SKIP'})

    def test_failed_check_and_unknown_checks_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            v=verifier.Verification(ROOT,Path(directory)/'report.json')
            self.assertEqual(v.save(),2)
            def failure():raise AssertionError('broken scrape')
            v.check('prometheus_target_up',failure)
            self.assertEqual(v.save(),1)

    def test_target_health_requires_matching_job_and_state(self):
        v=verifier.Verification(ROOT,Path('/tmp/unused-sdd-test.json'));v.prom='http://example.invalid';v.contract={'job':'application'}
        v.get_json=lambda _: {'data':{'activeTargets':[{'labels':{'job':'application'},'health':'down','scrapeUrl':'http://app:8000/metrics'}]}}
        with self.assertRaises(AssertionError):v.target('up')
        self.assertIn('Target down',v.target('down'))

if __name__=='__main__':unittest.main()
