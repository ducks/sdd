"""Single-process reference HTTP service using the standard WSGI server."""
import json
import os
import signal
import threading
import time
from wsgiref.simple_server import make_server,WSGIRequestHandler
from metrics import Metrics

class Application:
    def __init__(self):
        self.metrics=Metrics()

    def __call__(self,environ,start_response):
        path=environ.get('PATH_INFO','/')
        if path=='/metrics':
            data,content_type=self.metrics.render()
            start_response('200 OK',[('Content-Type',content_type)])
            return [data]
        if path=='/healthz':
            start_response('200 OK',[('Content-Type','text/plain')]);return [b'healthy']
        began=time.monotonic();route=path if path in ('/','/fail','/boom') else '__unmatched__'
        status=200
        try:
            if path=='/boom':raise RuntimeError('Synthetic test failure')
            if path=='/fail':status=503;payload={'error':'temporarily unavailable'}
            elif path=='/':payload={'message':'hello'}
            else:status=404;payload={'error':'not found'}
        except Exception:
            status=500;payload={'error':'internal server error'}
        data=json.dumps(payload).encode()
        self.metrics.observe(environ.get('REQUEST_METHOD','GET'),route,status,time.monotonic()-began)
        reasons={200:'OK',404:'Not Found',500:'Internal Server Error',503:'Service Unavailable'}
        start_response(str(status)+' '+reasons[status],[('Content-Type','application/json'),('Content-Length',str(len(data)))])
        return [data]

app=Application()

class QuietHandler(WSGIRequestHandler):
    def log_message(self,*args):pass

def serve():
    server=make_server(os.environ.get('BIND_HOST','0.0.0.0'),int(os.environ.get('PORT','8000')),app,handler_class=QuietHandler)
    # shutdown() must run outside serve_forever's thread.
    def stop(*_):threading.Thread(target=server.shutdown,daemon=True).start()
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:server.serve_forever(poll_interval=.1)
    finally:server.server_close()

if __name__=='__main__':serve()
