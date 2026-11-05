"""Queue adapter retains the existing invoice domain API and synchronous CLI."""
import json
import time
from invoices import render_invoice
from reliable import PermanentError,TransientError

def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS invoice_reports(job_key TEXT PRIMARY KEY,value TEXT NOT NULL)')

def prepare(payload,attempt):
    simulation=payload.get('simulation',{})
    delay=float(simulation.get('delay',0))
    if not 0<=delay<=5:raise PermanentError('invalid delay')
    time.sleep(delay)
    if simulation.get('permanent'):raise PermanentError('synthetic invalid invoice')
    if attempt<=simulation.get('fail_until',0):raise TransientError('synthetic temporary failure')
    try:return render_invoice(payload['invoice'])
    except (KeyError,TypeError,ValueError) as error:raise PermanentError('invalid invoice') from error

def apply(db,key,result):
    db.execute('INSERT INTO invoice_reports(job_key,value) VALUES(?,?)',(key,json.dumps(result,sort_keys=True)))
