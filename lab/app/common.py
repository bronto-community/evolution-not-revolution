# What every transit service already has: an access log in the central log bucket and a health
# endpoint. No OpenTelemetry in here.
import logging
import os
import socket
import time

from flask import Flask, g, request
from werkzeug.serving import WSGIRequestHandler

APP_NAME = os.environ["APP_NAME"]
APP_VERSION = os.environ["APP_VERSION"]
HOSTNAME = socket.gethostname()
LOG_DIR = os.environ.get("LOG_DIR", "/var/log/transit")
# The log format the team agreed on years ago. Can be overridden with LOG_FORMAT.
LOG_FORMAT = os.environ.get(
    "LOG_FORMAT", "%(asctime)s %(hostname)s %(app)s[%(version)s]: %(levelname)s %(message)s"
)


class Formatter(logging.Formatter):
    converter = time.gmtime

    def formatTime(self, record, datefmt=None):
        return time.strftime("%Y-%m-%dT%H:%M:%S", self.converter(record.created)) + f".{int(record.msecs):03d}Z"


def setup_logging():
    os.makedirs(f"{LOG_DIR}/{HOSTNAME}", exist_ok=True)
    handler = logging.FileHandler(f"{LOG_DIR}/{HOSTNAME}/{APP_NAME}.log")
    handler.setFormatter(Formatter(LOG_FORMAT))

    def add_context(record):
        record.hostname, record.app, record.version = HOSTNAME, APP_NAME, APP_VERSION
        return True

    handler.addFilter(add_context)
    log = logging.getLogger("transit")
    log.setLevel(logging.INFO)
    log.addHandler(handler)
    log.propagate = False
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    return log


log = setup_logging()


def create_app():
    app = Flask(APP_NAME)

    @app.before_request
    def start_timer():
        g.start = time.perf_counter()

    @app.after_request
    def access_log(response):
        if request.path != "/health":
            took_ms = (time.perf_counter() - g.start) * 1000
            log.info(f"method={request.method} path={request.path} status={response.status_code} duration_ms={took_ms:.0f}")
        return response

    @app.get("/health")
    def health():
        return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}

    return app


def serve(app, port):
    WSGIRequestHandler.protocol_version = "HTTP/1.1"   # keep-alive
    log.info(f"event=startup port={port}")
    app.run(host="0.0.0.0", port=port, threaded=True)
