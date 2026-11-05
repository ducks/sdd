from flask import Blueprint,jsonify
from .domain import lookup

api=Blueprint('catalog',__name__,url_prefix='/api')

@api.get('/items/<int:item_id>')
def item(item_id):
    value=lookup(item_id)
    return (jsonify(value),200) if value else (jsonify(error='not found'),404)

@api.get('/unavailable')
def unavailable():return jsonify(error='catalog unavailable'),503

@api.get('/crash')
def crash():raise RuntimeError('synthetic catalog failure')
