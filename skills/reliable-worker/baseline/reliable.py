"""Durable local queue. Business effects must share finish()'s SQLite transaction."""
from contextlib import contextmanager
import json
import math
from pathlib import Path
import sqlite3
import time
import uuid


class PermanentError(Exception):
    pass


class TransientError(Exception):
    pass


class Queue:
    def __init__(self, path):
        self.path = str(Path(path))

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA busy_timeout=5000')
        return db

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:
                db.execute('ROLLBACK')
            raise
        finally:
            db.close()

    def initialize(self):
        with self.transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY,
                job_key TEXT NOT NULL UNIQUE,
                payload TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL,
                available_at REAL NOT NULL,
                lease_until REAL,
                token TEXT,
                error_code TEXT
            )''')
            db.execute('CREATE INDEX IF NOT EXISTS jobs_ready ON jobs(state,available_at)')

    def enqueue(self, key, payload, max_attempts=3):
        if not isinstance(key, str) or not 1 <= len(key) <= 200:
            raise ValueError('job key must be 1..200 characters')
        if type(max_attempts) is not int or not 1 <= max_attempts <= 10:
            raise ValueError('max_attempts must be 1..10')
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False, separators=(',', ':'))
        if len(encoded.encode()) > 65536:
            raise ValueError('payload exceeds 64 KiB')
        with self.transaction() as db:
            row = db.execute('SELECT * FROM jobs WHERE job_key=?', (key,)).fetchone()
            if row:
                if row['payload'] != encoded or row['max_attempts'] != max_attempts:
                    raise ValueError('idempotency key reused with different input')
                return row['id']
            return db.execute('INSERT INTO jobs(job_key,payload,max_attempts,available_at) VALUES(?,?,?,?)',
                              (key, encoded, max_attempts, time.time())).lastrowid

    def claim(self, lease_seconds=2, now=None):
        if not math.isfinite(lease_seconds) or not .05 <= lease_seconds <= 3600:
            raise ValueError('lease_seconds must be .05..3600')
        now = time.time() if now is None else now
        with self.transaction() as db:
            db.execute("""UPDATE jobs SET state='dead',error_code='lease_exhausted',token=NULL,lease_until=NULL
                WHERE state='running' AND lease_until<=? AND attempts>=max_attempts""", (now,))
            row = db.execute("""SELECT * FROM jobs WHERE attempts<max_attempts AND
                ((state='pending' AND available_at<=?) OR (state='running' AND lease_until<=?))
                ORDER BY id LIMIT 1""", (now, now)).fetchone()
            if row is None:
                return None
            token = uuid.uuid4().hex
            db.execute("""UPDATE jobs SET state='running',attempts=attempts+1,token=?,lease_until=?
                WHERE id=?""", (token, now + lease_seconds, row['id']))
            result = dict(db.execute('SELECT * FROM jobs WHERE id=?', (row['id'],)).fetchone())
            result['payload'] = json.loads(result['payload'])
            return result

    def finish(self, job_id, token, result, apply):
        with self.transaction() as db:
            job = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
            if not job or job['state'] != 'running' or job['token'] != token or job['lease_until'] <= time.time():
                return False
            apply(db, job['job_key'], result)
            db.execute("UPDATE jobs SET state='done',token=NULL,lease_until=NULL,error_code=NULL WHERE id=?", (job_id,))
            return True

    def fail(self, job_id, token, code, permanent=False, base_delay=.05):
        if code not in ('transient', 'permanent', 'timeout', 'exception', 'child_exit'):
            raise ValueError('unbounded error classification')
        with self.transaction() as db:
            job = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
            if not job or job['state'] != 'running' or job['token'] != token or job['lease_until'] <= time.time():
                return False
            dead = permanent or job['attempts'] >= job['max_attempts']
            delay = min(1.0, base_delay * 2 ** (job['attempts'] - 1))
            db.execute('''UPDATE jobs SET state=?,error_code=?,available_at=?,token=NULL,lease_until=NULL
                WHERE id=?''', ('dead' if dead else 'pending', code, time.time() + delay, job_id))
            return True

    def get(self, job_id):
        db = self.connect()
        try:
            row = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
            return dict(row) if row else None
        finally:
            db.close()

    def unfinished(self):
        db = self.connect()
        try:
            return db.execute("SELECT count(*) FROM jobs WHERE state IN ('pending','running')").fetchone()[0]
        finally:
            db.close()
