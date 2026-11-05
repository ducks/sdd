from flask import Flask,jsonify
from .routes import api

def create_app():
    app=Flask(__name__)
    app.register_blueprint(api)
    app.config['PROPAGATE_EXCEPTIONS']=False
    @app.get('/healthz')
    def health():return jsonify(status='healthy')
    @app.errorhandler(500)
    def internal_error(error):return jsonify(error='internal server error'),500
    from .monitoring import instrument
    instrument(app)
    return app
