# departures-api: live departures for a stop. Serves the departure boards in our stations and
# the public API (third-party apps). Platform info and stop details come from stops-api.
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import urllib3
from flask import abort, request

from common import create_app, log, serve
from network import STOPS, timetable

STOPS_API = os.environ.get("STOPS_API", "http://stops-api:8001")
# Connections to stops-api, shared by all requests. One quick call per request: 5 is plenty (2019).
POOL_SIZE = int(os.environ.get("STOPS_API_POOL_SIZE", "5"))
http = urllib3.PoolManager(maxsize=POOL_SIZE, block=True, timeout=urllib3.Timeout(connect=1, read=2), retries=1)
# A board must not show live data that is older than this: it shows the printed timetable instead.
LIVE_BUDGET_MS = int(os.environ.get("LIVE_BUDGET_MS", "500"))

app = create_app()


def stops_api(path):
    r = http.request("GET", f"{STOPS_API}{path}")
    return json.loads(r.data)


def stop_details(stop):
    return stops_api(f"/stops/{stop}")


def add_routes(departures):
    """include=route: the next stops of every departure, all looked up in parallel to be fast."""
    with ThreadPoolExecutor(max_workers=16) as pool:
        routes = [pool.map(stop_details, d["next_stops"]) for d in departures]
        for d, route in zip(departures, routes):
            d["route"] = list(route)


@app.get("/departures")
def departures():
    stop = request.args.get("stop", "")
    if stop not in STOPS:
        abort(404)
    t0 = time.perf_counter()
    platforms = stops_api(f"/stops/{stop}/platforms")["platforms"]
    stops_api_ms = (time.perf_counter() - t0) * 1000
    live = stops_api_ms <= LIVE_BUDGET_MS
    if not live:
        log.warning(f"event=served_from_timetable stop={stop} reason=live_data_late stops_api_ms={stops_api_ms:.0f}")
    result = timetable(stop)
    for d in result:
        d["platform"], d["live"] = platforms.get(d["line"]), live
    if "route" in request.args.get("include", "").split(","):
        add_routes(result)
    return {"stop": STOPS[stop], "source": "live" if live else "timetable", "departures": result}


if __name__ == "__main__":
    log.info(f"event=config stops_api_pool_size={POOL_SIZE} live_budget_ms={LIVE_BUDGET_MS}")
    serve(app, 8000)
