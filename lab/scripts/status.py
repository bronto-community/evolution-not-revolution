#!/usr/bin/env python3
"""Both labs side by side: rollout, what the departure boards saw (loadgen), stops-api as seen in its own
logs (OpenSearch), alerts, clock drift.   status.py [--json]"""
import json
import os
import subprocess
import sys
import time
import urllib.request

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OS = "http://localhost:9200"


def q(path, body=None):
    req = urllib.request.Request(OS + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"}, method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return None


def stops_api(index, service_field, path_field, dur_field, window="1m"):
    """stops-api requests/s and p95 handling time from its access log lines (the last minute, 15 s ingest lag)."""
    body = {"size": 0, "track_total_hits": True,
            "query": {"bool": {"filter": [
                {"range": {"@timestamp": {"gte": f"now-{window}-15s", "lt": "now-15s"}}},
                {"term": {service_field: "stops-api"}}, {"exists": {"field": path_field}}]}},
            "aggs": {"p95": {"percentiles": {"field": dur_field, "percents": [50, 95]}}}}
    r = q(f"/{index}/_search", body)
    if not r:
        return None
    secs = {"1m": 60, "5m": 300}[window]
    p = r["aggregations"]["p95"]["values"]
    return {"rps": round(r["hits"]["total"]["value"] / secs, 1), "p50_ms": p.get("50.0"), "p95_ms": p.get("95.0")}


def alerts():
    r = q("/_plugins/_alerting/monitors/alerts?size=50&sortString=start_time&sortOrder=desc")
    out = {}
    for a in (r or {}).get("alerts", []):
        lab = a.get("monitor_name", "").split(":")[0]
        if a["state"] in ("ACTIVE", "ACKNOWLEDGED", "ERROR") and lab not in out:
            out[lab] = {"state": a["state"], "since": a.get("start_time")}
    return out


def main():
    st = {}
    try:
        st = json.load(open(f"{LAB}/state/loadgen.json"))
    except Exception:
        pass
    age = time.time() - st.get("host_time", 0)
    pool = open(f"{LAB}/state/pool-size").read().strip() if os.path.exists(f"{LAB}/state/pool-size") else "5"
    res = {"loadgen_age_s": round(age, 1), "drift_s": st.get("drift_s"), "share_pct": st.get("share_pct"),
           "phones_on_5_0": st.get("phones_on_5_0"), "pool_size": pool, "labs": {}}
    al = alerts()
    for lab, idx, sf, pf, df in (("classic", "classic-logs-*", "app", "path", "duration_ms"),
                                 ("enriched", "enriched-logs-*", "resource.service.name", "attributes.url.path", "attributes.duration_ms")):
        seen = st.get("labs", {}).get(lab, {})
        res["labs"][lab] = {"riders": seen, "stops_api": stops_api(idx, sf, pf, df), "alert": al.get(lab)}
    if "--json" in sys.argv:
        print(json.dumps(res, indent=1))
        return
    if "--line" in sys.argv:   # one line, for logs of test runs (scripts/watch.sh)
        out = [time.strftime("%H:%M:%S"), f"5.0={res['share_pct']}%", f"pool={pool}"]
        for lab, v in res["labs"].items():
            b, a5, s = v["riders"].get("board", {}), v["riders"].get("app5", {}), v["stops_api"] or {}
            out.append(f"| {lab}: boards timetable {b.get('timetable_pct')}% p95 {b.get('p95_ms')}ms, "
                       f"5.0 n={a5.get('requests')} p50 {a5.get('p50_ms')}ms, stops-api {s.get('rps')}/s "
                       f"p95 {round(s['p95_ms']) if s.get('p95_ms') else '-'}ms, alert {(v['alert'] or {}).get('state', 'ok')}")
        print(" ".join(out), flush=True)
        return
    subprocess.run([f"{LAB}/scripts/schedule.py"])
    if age > 15:
        print(f"WARNING: loadgen state is {age:.0f} s old (loadgen not running?)")
    print(f"JourneyApp 5.0: {res['share_pct']}% of {st.get('phones')} phones ({res['phones_on_5_0']})   "
          f"departures-api stops-api pool size: {pool}")
    print(f"{'last 60 s':<28}{'classic':>22}{'enriched':>22}")

    def row(label, f):
        print(f"{label:<28}" + "".join(f"{f(res['labs'][lab]):>22}" for lab in ("classic", "enriched")))

    def fmt_kind(kind):
        def f(l):
            k = l["riders"].get(kind)
            if not k or not k["requests"]:
                return "-"
            return f"{k['timetable_pct']:.0f}% of {k['requests']}" + (f" ({k['errors']} err)" if k["errors"] else "")
        return f

    def fmt_p95(kind):
        def f(l):
            k = l["riders"].get(kind)
            return f"p50 {k['p50_ms']} / p95 {k['p95_ms']} ms" if k and k.get("p95_ms") is not None else "-"
        return f

    row("boards from timetable", fmt_kind("board"))
    row("boards latency", fmt_p95("board"))
    row("app 4.0 from timetable", fmt_kind("app4"))
    row("app 5.0 requests", lambda l: str(l["riders"].get("app5", {}).get("requests", "-")))
    row("stops-api req/s (its logs)", lambda l: str(l["stops_api"]["rps"]) if l["stops_api"] else "-")
    row("stops-api handling", lambda l: f"p50 {l['stops_api']['p50_ms'] or 0:.0f} / p95 {l['stops_api']['p95_ms'] or 0:.0f} ms" if l["stops_api"] else "-")
    row("alert", lambda l: "FIRING since " + time.strftime("%H:%M:%S", time.localtime(l["alert"]["since"] / 1000)) if l["alert"] else "ok")
    d = res["drift_s"]
    if d is None:
        print("clock: unknown (no loadgen state)")
    elif abs(d) > 5:
        print(f"WARNING: the Docker VM clock is {d:+.0f} s off the host clock. Timestamps in OpenSearch/Jaeger are off by that much. "
              "Stop other heavy containers; if it stays, restart Docker Desktop.")
    else:
        print(f"clock: Docker VM vs host {d:+.1f} s (ok)")


if __name__ == "__main__":
    main()
