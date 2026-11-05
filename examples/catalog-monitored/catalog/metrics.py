"""Small shared metric vocabulary; route/method values are bounded by the caller."""
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

BUCKETS=(.005,.01,.025,.05,.1,.25,.5,1,2.5,5)
METHODS={'GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS'}

class Metrics:
    def __init__(self):
        self.registry=CollectorRegistry()
        self.requests=Counter('http_requests_total','Completed application requests',
            ['method','route','status_class'],registry=self.registry)
        self.duration=Histogram('http_request_duration_seconds','Application request duration in seconds',
            ['method','route'],buckets=BUCKETS,registry=self.registry)
        self.errors=Counter('http_errors_total','Completed HTTP error responses',
            ['route','error_class'],registry=self.registry)

    def observe(self,method,route,status,elapsed):
        method=method if method in METHODS else 'OTHER'
        status_class=str(status//100)+'xx' if 100<=status<=599 else 'other'
        self.requests.labels(method,route,status_class).inc()
        self.duration.labels(method,route).observe(elapsed)
        if status>=400:
            self.errors.labels(route,'server_error' if status>=500 else 'client_error').inc()

    def render(self):
        return generate_latest(self.registry),CONTENT_TYPE_LATEST
