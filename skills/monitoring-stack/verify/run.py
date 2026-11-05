#!/usr/bin/env python3
"""Independently validate a reviewed Compose monitoring integration.

Execution requires --allow-exec: Compose builds and application tests execute code.
Exit 0 means every check passed, 1 means failure, 2 means incomplete evidence.
"""
import argparse
import base64
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CHECKS=('compose_config','prometheus_config','application_tests','application_starts',
        'metrics_endpoint','prometheus_target_up','prometheus_queries','request_counter',
        'error_counter','exception_counter','latency_histogram','bounded_routes',
        'grafana_datasource','grafana_queries_prometheus','dashboard','graceful_shutdown',
        'target_down_detected','restart_recovers','cleanup')

class Verification:
    def __init__(self,project,output,allow_exec=False,wait_seconds=18):
        self.project=Path(project).resolve();self.output=Path(output)
        self.identity='sdd-'+secrets.token_hex(6)
        self.env=dict(os.environ,APP_PORT='0',PROMETHEUS_PORT='0',GRAFANA_PORT='0',
            GRAFANA_PASSWORD=secrets.token_urlsafe(24))
        self.results={name:{'status':'UNKNOWN','detail':'Not reached'} for name in CHECKS}
        self.allow_exec=allow_exec;self.started=False;self.wait_seconds=wait_seconds

    def result(self,name,status,detail):
        self.results[name]={'status':status,'detail':detail}
        print(f'{status}: {name}: {detail}',flush=True)

    def command(self,*args,input=None,timeout=180):
        return subprocess.run(['docker','compose','--project-name',self.identity,'--file',str(self.project/'compose.yaml'),*args],
            cwd=self.project,env=self.env,input=input,text=True,capture_output=True,timeout=timeout)

    def checked(self,*args,input=None,timeout=180):
        p=self.command(*args,input=input,timeout=timeout)
        if p.returncode:raise RuntimeError('Command failed: '+' '.join(args[:4])+'\n'+(p.stderr+p.stdout)[-2500:])
        return p.stdout

    def check(self,name,fn):
        try:
            detail=fn();self.result(name,'PASS',str(detail or 'Executed successfully'));return detail
        except Exception as error:
            # The randomly generated Grafana password is never a report field.
            detail=(type(error).__name__+': '+str(error)).replace(self.env['GRAFANA_PASSWORD'],'[REDACTED]')
            self.result(name,'FAIL',detail);return None

    def url(self,service,port):
        published=self.checked('port',service,str(port)).strip().splitlines()[0]
        if not re.fullmatch(r'127\.0\.0\.1:\d+',published):raise RuntimeError('Expected loopback-only published port')
        return 'http://'+published

    def request(self,url,expected=200,auth=False):
        headers={}
        if auth:headers['Authorization']='Basic '+base64.b64encode(('admin:'+self.env['GRAFANA_PASSWORD']).encode()).decode()
        req=urllib.request.Request(url,headers=headers)
        try:
            with urllib.request.urlopen(req,timeout=4) as r:status=r.status;body=r.read(2*1024*1024+1);kind=r.headers.get('Content-Type','')
        except urllib.error.HTTPError as e:
            status=e.code;body=e.read(2*1024*1024+1);kind=e.headers.get('Content-Type','');e.close()
        if len(body)>2*1024*1024:raise RuntimeError('Response too large')
        if status!=expected:raise AssertionError(f'Expected HTTP {expected}, got {status}')
        return body.decode(),kind

    def get_json(self,url,auth=False):return json.loads(self.request(url,auth=auth)[0])

    def eventually(self,fn,seconds=None):
        deadline=time.monotonic()+(self.wait_seconds if seconds is None else seconds);error=None
        while time.monotonic()<deadline:
            try:return fn()
            except Exception as e:error=e;time.sleep(.5)
        raise AssertionError('Condition not satisfied before timeout: '+str(error))

    def query(self,expression,grafana=False):
        root=self.grafana+'/api/datasources/proxy/uid/sdd-prometheus' if grafana else self.prom
        data=self.get_json(root+'/api/v1/query?'+urllib.parse.urlencode({'query':expression}),auth=grafana)
        if data.get('status')!='success':raise AssertionError('Prometheus query failed')
        return data['data']['result']

    def value(self,expression,grafana=False):
        rows=self.query(expression,grafana)
        if len(rows)!=1:raise AssertionError('Expected one numeric series; found '+str(len(rows)))
        value=float(rows[0]['value'][1])
        if not math.isfinite(value):raise AssertionError('Non-finite sample')
        return value

    def expect_value(self,expression,predicate):
        def check():
            value=self.value(expression)
            if not predicate(value):raise AssertionError(f'Unexpected sample {value}')
            return value
        return self.eventually(check)

    def config(self):
        config=json.loads(self.checked('config','--format','json'))
        for name,service in config['services'].items():
            for port in service.get('ports',[]):
                if port.get('host_ip')!='127.0.0.1':raise AssertionError('Public service binding: '+name)
        return 'Compose parsed; all published ports use loopback'

    def tests(self):
        p=self.command('run','--rm','--no-deps','app','python','-m','unittest','discover','-s','tests','-v')
        text=p.stdout+p.stderr
        if p.returncode or not re.search(r'Ran [1-9]\d* tests?',text):raise AssertionError('Application tests failed or zero tests ran: '+text[-2000:])
        return re.search(r'Ran [1-9]\d* tests?[^\n]*',text).group(0)

    def target(self,state):
        data=self.get_json(self.prom+'/api/v1/targets')['data']['activeTargets']
        targets=[t for t in data if t.get('labels',{}).get('job')==self.contract['job']]
        if len(targets)!=1 or targets[0]['health']!=state:raise AssertionError('Expected one '+state+' application target')
        return 'Target '+state+': '+targets[0]['scrapeUrl']

    def metrics(self):
        for path,status in ((self.contract['success_path'],200),(self.contract['error_path'],503),(self.contract['exception_path'],500)):
            self.request(self.app+path,status)
        text,content_type=self.request(self.app+'/metrics')
        if not ('text/plain' in content_type or 'openmetrics-text' in content_type):raise AssertionError('Unexpected metrics content type')
        for family,kind in (('http_requests_total','counter'),('http_errors_total','counter'),('http_request_duration_seconds','histogram')):
            if '# TYPE '+family+' '+kind not in text:raise AssertionError('Missing or wrong metric type '+family)
        self.checked('exec','-T','prometheus','promtool','check','metrics',input=text)
        return 'HTTP exposition parsed by promtool; required counter/histogram families present'

    def change(self,metric,path,route,status):
        match='{job='+json.dumps(self.contract['job'])+',route='+json.dumps(route)+'}'
        expr='sum('+metric+match+')'
        before=self.eventually(lambda:self.value(expr))
        for _ in range(3):self.request(self.app+path,status)
        after=self.expect_value(expr,lambda v:v>=before+3)
        return f'{before} -> {after} after 3 HTTP {status} requests'

    def histogram(self):
        expr='sum(http_request_duration_seconds_count{job='+json.dumps(self.contract['job'])+'})'
        before=self.eventually(lambda:self.value(expr));self.request(self.app+self.contract['success_path'])
        self.expect_value(expr,lambda v:v>=before+1)
        buckets=self.query('http_request_duration_seconds_bucket{job='+json.dumps(self.contract['job'])+'}')
        if len(buckets)<3:raise AssertionError('Missing histogram buckets')
        return 'Histogram count increased and bucket series are queryable'

    def cardinality(self):
        for i in range(10):self.request(self.app+'/unrecognized-'+str(i),404)
        def check():
            rows=self.query('http_requests_total{job='+json.dumps(self.contract['job'])+'}')
            routes={r['metric'].get('route') for r in rows}
            if '__unmatched__' not in routes:raise AssertionError('Unmatched route not scraped yet')
            if any('/unrecognized-' in (r or '') for r in routes):raise AssertionError('Raw path in route label')
            return 'Unknown paths collapse to __unmatched__'
        return self.eventually(check)

    def datasource(self):
        data=self.get_json(self.grafana+'/api/datasources/uid/sdd-prometheus',auth=True)
        if data.get('type')!='prometheus' or data.get('url')!='http://prometheus:9090':raise AssertionError('Unexpected datasource configuration')
        health=self.get_json(self.grafana+'/api/datasources/uid/sdd-prometheus/health',auth=True)
        if health.get('status')!='OK':raise AssertionError('Datasource health failed')
        return 'Provisioned Prometheus datasource health OK'

    def grafana_up(self):
        value=self.value('up{job='+json.dumps(self.contract['job'])+'}',grafana=True)
        if value!=1:raise AssertionError('Target not up through Grafana')
        return 'Prometheus UP series returned through Grafana datasource proxy'

    def dashboard(self):
        data=self.get_json(self.grafana+'/api/dashboards/uid/sdd-application',auth=True)['dashboard']
        panels=data.get('panels') or []
        if len(panels)<3:raise AssertionError('Expected request, error and latency panels')
        for panel in panels:
            for target in panel.get('targets',[]):
                rows=self.query(target['expr'],grafana=True)
                if not rows:raise AssertionError('Dashboard expression has no series: '+target['expr'])
                if any(not math.isfinite(float(r['value'][1])) for r in rows):raise AssertionError('Dashboard query has non-finite values')
        return 'Dashboard provisioned; all panel expressions return finite series via Grafana'

    def shutdown(self):
        cid=self.checked('ps','-q','app').strip();self.checked('stop','--timeout','10','app')
        p=subprocess.run(['docker','inspect','--format','{{.State.ExitCode}}',cid],text=True,capture_output=True,timeout=10)
        if p.returncode or p.stdout.strip()!='0':raise AssertionError('Application did not exit cleanly on SIGTERM')
        return 'SIGTERM exited 0 within 10 seconds'

    def recover(self):
        self.checked('up','-d','--wait','--wait-timeout','45','app')
        self.app=self.url('app',8000)
        self.eventually(lambda:self.request(self.app+'/healthz'))
        self.eventually(lambda:self.target('up'))
        self.request(self.app+self.contract['success_path'])
        self.expect_value('sum(http_requests_total{job='+json.dumps(self.contract['job'])+'})',lambda v:v>=1)
        return 'App and scraping recovered after restart'

    def run(self):
        if not self.allow_exec:
            for name in CHECKS:self.result(name,'SKIP','Execution not authorized: review the project, then pass --allow-exec')
            return self.save()
        if not shutil.which('docker'):
            for name in CHECKS:self.result(name,'SKIP','Docker executable not available')
            return self.save()
        daemon=subprocess.run(['docker','info'],capture_output=True,timeout=15)
        if daemon.returncode:
            for name in CHECKS:self.result(name,'SKIP','Docker daemon unavailable or permission denied')
            return self.save()
        try:
            self.contract=json.loads((self.project/'acceptance.json').read_text())
            for key in ('success_path','error_path','exception_path'):
                if not self.contract[key].startswith('/') or self.contract[key].startswith('//'):raise ValueError('Paths must be local absolute HTTP paths')
            if self.check('compose_config',self.config) is None:raise RuntimeError('Compose validation failed')
            self.started=True
            self.checked('build','app',timeout=300)
            self.check('prometheus_config',lambda:self.checked('run','--rm','--no-deps','--entrypoint','promtool','prometheus','check','config','/etc/prometheus/prometheus.yml'))
            self.check('application_tests',self.tests)
            self.checked('up','-d','--wait','--wait-timeout','90',timeout=120)
            self.app=self.url('app',8000);self.prom=self.url('prometheus',9090);self.grafana=self.url('grafana',3000)
            self.check('application_starts',lambda:self.request(self.app+'/healthz')[0])
            self.check('metrics_endpoint',self.metrics)
            self.check('prometheus_target_up',lambda:self.eventually(lambda:self.target('up')))
            job=json.dumps(self.contract['job'])
            self.check('prometheus_queries',lambda:self.expect_value('up{job='+job+'}',lambda v:v==1))
            self.check('request_counter',lambda:self.change('http_requests_total',self.contract['success_path'],self.contract['success_route'],200))
            self.check('error_counter',lambda:self.change('http_errors_total',self.contract['error_path'],self.contract['error_route'],503))
            # Query exception route by bounded server-error label; verify both request and error instrumentation.
            self.check('exception_counter',lambda:self.exception_change())
            self.check('latency_histogram',self.histogram)
            self.check('bounded_routes',self.cardinality)
            self.check('grafana_datasource',self.datasource)
            self.check('grafana_queries_prometheus',self.grafana_up)
            self.check('dashboard',lambda:self.eventually(self.dashboard))
            if self.check('graceful_shutdown',self.shutdown) is not None:
                self.check('target_down_detected',lambda:self.eventually(lambda:self.target('down')))
                self.check('restart_recovers',self.recover)
        except Exception as error:
            if self.results['application_starts']['status']=='UNKNOWN':
                self.result('application_starts','FAIL','Startup/build failed: '+str(error).replace(self.env['GRAFANA_PASSWORD'],'[REDACTED]'))
            for name,row in self.results.items():
                if row['status']=='UNKNOWN':row['detail']='Blocked by '+type(error).__name__+': '+str(error).replace(self.env['GRAFANA_PASSWORD'],'[REDACTED]')
        finally:
            if self.started:
                self.check('cleanup',lambda:self.checked('down','--volumes','--remove-orphans','--rmi','local',timeout=90) or 'Owned containers, volumes, network and build image removed')
            elif self.results['cleanup']['status']=='UNKNOWN':self.result('cleanup','SKIP','No resources were created')
        return self.save()

    def exception_change(self):
        expr='sum(http_errors_total{job='+json.dumps(self.contract['job'])+',error_class="server_error"})'
        before=self.eventually(lambda:self.value(expr));self.request(self.app+self.contract['exception_path'],500)
        after=self.expect_value(expr,lambda v:v>=before+1)
        return f'{before} -> {after} after synthetic exception'

    def save(self):
        report={'schema_version':1,'created_at':datetime.now(timezone.utc).isoformat(),'project':str(self.project),'compose_project':self.identity,'checks':self.results}
        self.output.parent.mkdir(parents=True,exist_ok=True);self.output.write_text(json.dumps(report,indent=2)+'\n')
        states={row['status'] for row in self.results.values()}
        return 1 if 'FAIL' in states else 2 if states!={'PASS'} else 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--allow-exec',action='store_true',help='Authorize this reviewed Compose project, build and tests to execute')
    parser.add_argument('--wait-seconds',type=int,default=18,choices=range(1,61),metavar='1..60')
    args=parser.parse_args();return Verification(args.project,args.output,args.allow_exec,args.wait_seconds).run()

if __name__=='__main__':sys.exit(main())
