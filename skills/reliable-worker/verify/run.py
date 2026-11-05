#!/usr/bin/env python3
"""Independent local worker acceptance checks. Executes reviewed target code only with --allow-exec."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time

CHECKS = ('durable_enqueue','conflicting_key','duplicate_delivery','transient_retry',
          'permanent_failure','retry_exhaustion','bounded_timeout','concurrent_workers',
          'lease_fencing','crash_rolls_back_effect','expired_claim_recovers','graceful_shutdown',
          'existing_tests','cleanup')


class Verification:
    def __init__(self, project, output, allow_exec=False):
        self.project=Path(project).resolve();self.output=Path(output)
        self.allow_exec=allow_exec
        self.rows={k:{'status':'UNKNOWN','detail':'Not reached'} for k in CHECKS}
        self.processes=[]

    def result(self, name, status, detail):
        self.rows[name]={'status':status,'detail':detail}
        print(status+': '+name+': '+detail,flush=True)

    def command(self, *args, expected=0, timeout=8):
        p=subprocess.run([sys.executable,*args],cwd=self.project,capture_output=True,text=True,timeout=timeout,
                         env=dict(os.environ,SDD_TEST_DB=str(self.db)))
        if p.returncode!=expected:
            raise AssertionError(f'Command exit {p.returncode}, expected {expected}: '+p.stderr[-1200:])
        return p.stdout

    def code(self, source, expected=0):
        return self.command('-c','import os\nfrom reliable import Queue\nq=Queue(os.environ["SDD_TEST_DB"])\n'+source,expected=expected)

    def cli(self, *args, expected=0):
        return self.command('worker.py','--db',str(self.db),*args,expected=expected)

    def enqueue(self, key='task', simulation=None, attempts=3):
        payload=dict(self.contract['payload'])
        if simulation:payload['simulation']=simulation
        return int(self.cli('enqueue','--key',key,'--payload',json.dumps(payload),'--max-attempts',str(attempts)))

    def query(self, sql, params=()):
        with sqlite3.connect(self.db,timeout=2) as db:
            db.row_factory=sqlite3.Row
            return [dict(row) for row in db.execute(sql,params)]

    def job(self, key='task'):
        return self.query('SELECT * FROM jobs WHERE job_key=?',(key,))[0]

    def effects(self):
        return self.query('SELECT * FROM '+self.contract['result_table'])

    def worker(self, timeout=.4, lease=1, idle=.15):
        p=subprocess.Popen([sys.executable,'worker.py','--db',str(self.db),'work','--timeout',str(timeout),
            '--lease',str(lease),'--idle-exit',str(idle)],cwd=self.project,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            start_new_session=os.name=='posix')
        self.processes.append(p)
        return p

    def wait(self, process):
        if process.wait(timeout=8)!=0:raise AssertionError('Worker exited unsuccessfully')

    def eventually(self, fn, seconds=4):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            try:
                result=fn()
                if result:return result
            except (sqlite3.OperationalError,IndexError):pass
            time.sleep(.01)
        raise AssertionError('Condition not reached before timeout')

    def assert_done(self, attempts):
        job=self.job()
        assert job['state']=='done' and job['attempts']==attempts,job
        effects=self.effects()
        assert len(effects)==1,effects
        assert json.loads(effects[0]['value'])==self.contract['expected_result'],effects

    def durable_enqueue(self):
        job_id=self.enqueue()
        assert self.job()['id']==job_id
        assert self.job()['state']=='pending'
        # Enqueue and worker are different processes; state must survive process exit.
        self.wait(self.worker());self.assert_done(1)
        return 'Enqueue process exited; a separate worker completed the persisted task'

    def conflicting_key(self):
        self.enqueue()
        self.code('''try:
    q.enqueue('task',{'different':True})
except ValueError:
    pass
else:
    raise AssertionError('Conflicting key accepted')
''')
        assert len(self.query('SELECT * FROM jobs'))==1
        return 'Same idempotency key with different payload rejected'

    def duplicate_delivery(self):
        a=self.enqueue();b=self.enqueue();assert a==b
        self.wait(self.worker());self.enqueue();self.wait(self.worker());self.assert_done(1)
        return 'Duplicates before and after completion produced one job and one business effect'

    def transient_retry(self):
        self.enqueue(simulation={'fail_until':2});self.wait(self.worker());self.assert_done(3)
        return 'Two transient failures followed by success; exactly three attempts and one effect'

    def permanent_failure(self):
        self.enqueue(simulation={'permanent':True});self.wait(self.worker())
        job=self.job();assert job['state']=='dead' and job['attempts']==1 and job['error_code']=='permanent',job
        assert not self.effects()
        return 'Permanent error dead-lettered immediately without a business effect'

    def retry_exhaustion(self):
        self.enqueue(simulation={'fail_until':10});self.wait(self.worker())
        job=self.job();assert job['state']=='dead' and job['attempts']==3,job
        assert not self.effects()
        return 'Transient failure stopped at the configured three-attempt budget'

    def bounded_timeout(self):
        self.enqueue(simulation={'delay':1},attempts=2)
        start=time.monotonic();self.wait(self.worker(timeout=.15,lease=.6))
        job=self.job();assert job['state']=='dead' and job['attempts']==2 and job['error_code']=='timeout',job
        assert time.monotonic()-start<3
        assert not self.effects()
        # Supervised child must not publish a late effect after its timeout.
        time.sleep(.2);assert not self.effects()
        return 'Two timed-out child attempts were killed/reaped; no late business effect'

    def concurrent_workers(self):
        for n in range(6):self.enqueue(key='task-'+str(n))
        a=self.worker();b=self.worker();self.wait(a);self.wait(b)
        jobs=self.query('SELECT * FROM jobs')
        assert all(j['state']=='done' and j['attempts']==1 for j in jobs),jobs
        assert len(self.effects())==6
        return 'Two worker processes completed six jobs once each'

    def lease_fencing(self):
        self.enqueue()
        first=json.loads(self.code('import json\nprint(json.dumps(q.claim(.08)))'))
        time.sleep(.12)
        second=json.loads(self.code('import json\nprint(json.dumps(q.claim(2)))'))
        assert first['token']!=second['token']
        self.code('import handler\nassert not q.finish('+str(first['id'])+','+repr(first['token'])+',{},handler.apply)')
        assert not self.effects()
        self.cli('execute','--job-id',str(second['id']),'--token',second['token']);self.assert_done(2)
        return 'Expired owner rejected after reclaim; only the new token committed'

    def crash_rolls_back_effect(self):
        self.enqueue()
        # Write a business effect and exit before ack/commit inside the same transaction.
        self.code('''job=q.claim(2)
def crash(db,key,result):
    import handler
    handler.apply(db,key,result)
    os._exit(19)
q.finish(job['id'],job['token'],{},crash)
''',expected=19)
        assert not self.effects(),'Uncommitted effect survived process crash'
        assert self.job()['state']=='running'
        return 'Process exit between effect and ack rolled back the business write'

    def expired_claim_recovers(self):
        self.enqueue()
        self.code('q.claim(.08)\nos._exit(21)',expected=21)
        time.sleep(.12);self.wait(self.worker());self.assert_done(2)
        return 'A crashed claim owner was recovered after lease expiry, without dropping the job'

    def graceful_shutdown(self):
        if os.name!='posix':return None
        self.enqueue(simulation={'delay':.25});self.enqueue(key='next')
        process=self.worker(timeout=1,lease=2)
        self.eventually(lambda:self.job()['state']=='running')
        process.send_signal(signal.SIGTERM);self.wait(process)
        assert self.job()['state']=='done'
        assert self.job('next')['state']=='pending','Worker claimed another job after SIGTERM'
        assert len(self.effects())==1
        return 'SIGTERM finished current work and left the next task pending'

    def existing_tests(self):
        p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=self.project,capture_output=True,text=True,timeout=10)
        text=p.stdout+p.stderr
        assert p.returncode==0 and re.search(r'Ran [1-9]\d* tests?',text),text[-1500:]
        return re.search(r'Ran [1-9]\d* tests?[^\n]*',text).group(0)

    def run(self):
        if not self.allow_exec:
            for name in CHECKS:self.result(name,'SKIP','Review target code and supply --allow-exec')
            return self.save()
        try:
            self.contract=json.loads((self.project/'acceptance.json').read_text())
            if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',self.contract['result_table']):raise ValueError('Invalid SQL table identifier')
            with tempfile.TemporaryDirectory(prefix='sdd-worker-') as directory:
                for name in CHECKS[:-1]:
                    self.db=Path(directory)/(name+'.sqlite')
                    try:
                        self.cli('init')
                        detail=getattr(self,name)()
                        self.result(name,'SKIP' if detail is None else 'PASS',detail or 'POSIX signals unavailable')
                    except Exception as error:
                        self.result(name,'FAIL',type(error).__name__+': '+str(error))
                    finally:
                        for process in self.processes:
                            if process.poll() is None:
                                process.terminate()
                                try:process.wait(timeout=3)
                                except subprocess.TimeoutExpired:process.kill();process.wait()
                        self.processes=[]
            self.result('cleanup','PASS','Workers reaped and temporary SQLite databases/journals removed')
        except Exception as error:
            self.result('cleanup','FAIL',type(error).__name__+': '+str(error))
        return self.save()

    def save(self):
        self.output.parent.mkdir(parents=True,exist_ok=True)
        self.output.write_text(json.dumps({'schema_version':1,'created_at':datetime.now(timezone.utc).isoformat(),
            'project':str(self.project),'checks':self.rows},indent=2)+'\n')
        states={r['status'] for r in self.rows.values()}
        return 1 if 'FAIL' in states else 2 if states!={'PASS'} else 0


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--allow-exec',action='store_true')
    args=p.parse_args();sys.exit(Verification(args.project,args.output,args.allow_exec).run())
