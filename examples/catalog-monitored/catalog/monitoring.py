"""Adapt metric recording to Flask's resolved routes and request lifecycle."""
import time
from flask import g,request,Response
from .metrics import Metrics

def instrument(app):
    metrics=Metrics()
    app.extensions['sdd_metrics']=metrics
    @app.get('/metrics')
    def scrape():
        data,content_type=metrics.render();return Response(data,content_type=content_type)
    @app.before_request
    def began():g.monitoring_start=time.monotonic()
    @app.after_request
    def completed(response):
        if request.path not in ('/metrics','/healthz'):
            route=request.url_rule.rule if request.url_rule else '__unmatched__'
            metrics.observe(request.method,route,response.status_code,time.monotonic()-g.monitoring_start)
        return response
