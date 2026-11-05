"""Synthetic local task fixture. Simulation options are for verification only."""
import json
import time
from reliable import PermanentError, TransientError


def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS results(job_key TEXT PRIMARY KEY,value TEXT NOT NULL)')


def prepare(payload, attempt):
    simulation = payload.get('simulation', {})
    delay = float(simulation.get('delay', 0))
    if not 0 <= delay <= 5:
        raise PermanentError('invalid delay')
    time.sleep(delay)
    if simulation.get('permanent'):
        raise PermanentError('synthetic invalid task')
    if attempt <= simulation.get('fail_until', 0):
        raise TransientError('synthetic temporary failure')
    return {'message': payload['message']}


def apply(db, key, result):
    db.execute('INSERT INTO results(job_key,value) VALUES(?,?)', (key, json.dumps(result, sort_keys=True)))
