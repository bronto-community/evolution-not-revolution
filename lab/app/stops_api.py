# stops-api: master data for every stop (run by the network data team). Used by departures-api,
# the website and the ticket machines.
import random
import time

from flask import abort

from common import create_app, serve
from network import LINES, STOPS

app = create_app()


def find(stop_id):
    if stop_id not in STOPS:
        abort(404)
    return stop_id


@app.get("/stops/<stop_id>")
def stop(stop_id):
    find(stop_id)
    time.sleep(random.lognormvariate(-3.1, 0.1))   # the master data query: ~45 ms
    return {
        "id": stop_id, "name": STOPS[stop_id],
        "lines": [line for line, stops in LINES.items() if stop_id in stops],
        "step_free": len(stop_id) % 3 != 0, "lifts_ok": random.random() > 0.05,
    }


@app.get("/stops/<stop_id>/platforms")
def platforms(stop_id):
    find(stop_id)
    time.sleep(random.lognormvariate(-5.2, 0.25))   # from the cache: ~6 ms
    return {
        "id": stop_id,
        "platforms": {line: 1 + i % 2 for i, line in enumerate(LINES) if stop_id in LINES[line]},
        "notice": None,
    }


if __name__ == "__main__":
    serve(app, 8001)
