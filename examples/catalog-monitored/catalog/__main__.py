import os
import signal
import threading
from werkzeug.serving import make_server
from . import create_app

def main():
    server=make_server('0.0.0.0',int(os.environ.get('PORT','8000')),create_app())
    def stop(*_):threading.Thread(target=server.shutdown,daemon=True).start()
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:server.serve_forever(poll_interval=.1)
    finally:server.server_close()

if __name__=='__main__':main()
