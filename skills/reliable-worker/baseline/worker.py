"""Fixed local worker entrypoint. Handlers are reviewed application code, not job input."""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import handler
from reliable import Queue, PermanentError, TransientError


def initialize(queue):
    queue.initialize()
    with queue.transaction() as db:
        handler.initialize(db)


def execute(queue, job_id, token):
    job = queue.get(job_id)
    if not job or job['state'] != 'running' or job['token'] != token:
        return 3
    try:
        result = handler.prepare(json.loads(job['payload']), job['attempts'])
        return 0 if queue.finish(job_id, token, result, handler.apply) else 3
    except PermanentError:
        queue.fail(job_id, token, 'permanent', permanent=True)
    except TransientError:
        queue.fail(job_id, token, 'transient')
    except Exception:
        queue.fail(job_id, token, 'exception')
    return 1


def kill_child(child):
    if child.poll() is None:
        if os.name == 'posix':
            os.killpg(child.pid, signal.SIGKILL)
        else:
            child.kill()
    child.wait()


def work(queue, timeout=.5, lease=2, idle_exit=0):
    if not all(math.isfinite(v) for v in (timeout, lease, idle_exit)):
        raise ValueError('worker durations must be finite')
    if not .02 <= timeout <= 300 or not timeout + .1 < lease <= 3600 or not 0 <= idle_exit <= 60:
        raise ValueError('invalid timeout, lease, or idle-exit settings')
    stopping = False
    def stop(*_):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    idle_since = time.monotonic()
    while not stopping:
        job = queue.claim(lease)
        if job is None:
            if idle_exit and time.monotonic() - idle_since >= idle_exit and not queue.unfinished():
                break
            time.sleep(.02)
            continue
        idle_since = time.monotonic()
        command = [sys.executable, str(Path(__file__).resolve()), '--db', queue.path,
                   'execute', '--job-id', str(job['id']), '--token', job['token']]
        child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=os.name == 'posix')
        try:
            child.wait(timeout=timeout)
            row = queue.get(job['id'])
            if row['state'] == 'running':
                queue.fail(job['id'], job['token'], 'child_exit')
        except subprocess.TimeoutExpired:
            kill_child(child)
            queue.fail(job['id'], job['token'], 'timeout')
        finally:
            kill_child(child)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default=os.environ.get('WORKER_DB', 'worker.sqlite'))
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('init')
    enqueue = commands.add_parser('enqueue')
    enqueue.add_argument('--key', required=True)
    enqueue.add_argument('--payload', required=True)
    enqueue.add_argument('--max-attempts', type=int, default=3)
    worker = commands.add_parser('work')
    worker.add_argument('--timeout', type=float, default=.5)
    worker.add_argument('--lease', type=float, default=2)
    worker.add_argument('--idle-exit', type=float, default=0, help='Exit after idle seconds with no unfinished jobs; 0 keeps polling')
    execution = commands.add_parser('execute')
    execution.add_argument('--job-id', type=int, required=True)
    execution.add_argument('--token', required=True)
    args = parser.parse_args()
    queue = Queue(args.db)
    initialize(queue)
    if args.command == 'enqueue':
        print(queue.enqueue(args.key, json.loads(args.payload), args.max_attempts))
    elif args.command == 'work':
        return work(queue, args.timeout, args.lease, args.idle_exit)
    elif args.command == 'execute':
        return execute(queue, args.job_id, args.token)
    return 0


if __name__ == '__main__':
    sys.exit(main())
