import json
import sys
from .domain import render_invoice

if __name__ == '__main__':
    print(json.dumps(render_invoice(json.load(sys.stdin)), sort_keys=True))
