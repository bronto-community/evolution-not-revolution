#!/usr/bin/env python3
"""Checks on the data itself (run during an incident):  verify.py incident | classic
classic:  no trace_id in the classic log files or in classic-logs; no user agent / query string in classic-logs;
          departures-api says the stops-api call took ~1 s while stops-api says it answered in a few ms.
incident: + enriched: a slow board trace in Jaeger (client span ~1 s, its stops-api server span < 60 ms);
          5.0 traces with ~25 stops-api calls; user_agent.original / url.query are fields of the index pattern;
          one traceId filter on enriched-* returns that request's log lines and spans."""
import glob
import json
import os
import sys
import urllib.request

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL = 0


def get(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"}, method="POST" if body else "GET")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def search(index, body):
    return get(f"http://localhost:9200/{index}/_search", body)


def check(name, ok, detail=""):
    global FAIL
    print(f"  {'PASS' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail else ""), flush=True)
    FAIL += 0 if ok else 1


def classic():
    print("classic lab:")
    files = glob.glob(f"{LAB}/logs/classic/*/*.log")
    n = sum(open(f, errors="replace").read().count("trace_id") for f in files)
    check("no 'trace_id' in the classic log files", n == 0, f"{len(files)} files, {n} matches")
    hits = search("classic-logs-*", {"size": 0, "track_total_hits": True,
                                     "query": {"query_string": {"query": "*trace_id* OR trace_id:* OR traceId:*"}}})["hits"]["total"]["value"]
    check("no trace id in classic-logs", hits == 0, f"{hits} docs")
    m = get("http://localhost:9200/classic-logs-*/_mapping")
    fields = set()
    for idx in m.values():
        fields |= set(idx["mappings"].get("properties", {}))
    bad = [f for f in fields if any(k in f.lower() for k in ("agent", "query", "trace", "span"))]
    check("no user agent / query string / trace fields in classic-logs", not bad, f"fields: {sorted(fields)}")
    rng = {"range": {"@timestamp": {"gte": "now-2m"}}}
    w = search("classic-logs-*", {"size": 0, "query": {"bool": {"filter": [rng, {"term": {"event": "served_from_timetable"}}]}},
                                  "aggs": {"p": {"percentiles": {"field": "stops_api_ms", "percents": [50, 95]}}}})
    s = search("classic-logs-*", {"size": 0, "query": {"bool": {"filter": [rng, {"term": {"app": "stops-api"}},
                                                                           {"prefix": {"path": "/stops/"}}]}},
                                  "aggs": {"p": {"percentiles": {"field": "duration_ms", "percents": [50, 95]}},
                                           "plat": {"filter": {"wildcard": {"path": "*/platforms"}},
                                                    "aggs": {"p": {"percentiles": {"field": "duration_ms", "percents": [50, 95]}}}}}})
    wp, sp = w["aggregations"]["p"]["values"], s["aggregations"]["plat"]["p"]["values"]
    print(f"  departures-api timetable warnings (2 min): {w['hits']['total']['value']}, stops_api_ms p50 {wp['50.0']} p95 {wp['95.0']}")
    print(f"  stops-api log, /stops/<id>/platforms duration_ms p50 {sp['50.0']} p95 {sp['95.0']}; all /stops p95 {s['aggregations']['p']['values']['95.0']}")
    return wp, sp


def enriched():
    print("enriched lab:")
    r = search("enriched-spans-*", {"size": 20, "sort": [{"@timestamp": "desc"}], "query": {"bool": {"filter": [
        {"prefix": {"attributes.user_agent.original": "departure-board"}}, {"term": {"kind": "Server"}},
        {"range": {"attributes.duration_ms": {"gte": 700}}}, {"range": {"@timestamp": {"gte": "now-5m", "lte": "now-20s"}}}]}}})
    hits = r["hits"]["hits"]
    check("slow board requests (server span >= 700 ms) in the last 5 min", bool(hits), f"{len(hits)} found")
    shown = 0
    for h in hits[:5]:
        tid = h["_source"]["traceId"]
        try:
            d = get(f"http://localhost:16686/api/traces/{tid}")["data"][0]
        except Exception as e:
            print(f"  trace {tid}: not in Jaeger ({e})")
            continue
        procs = {k: v["serviceName"] for k, v in d["processes"].items()}
        spans = {s["spanID"]: s for s in d["spans"]}
        client = [s for s in d["spans"] if procs[s["processID"]] == "departures-api"
                  and any(t["key"] == "span.kind" and t["value"] == "client" for t in s["tags"])]
        if not client:
            continue
        c = client[0]
        child = [s for s in d["spans"] if any(ref["spanID"] == c["spanID"] for ref in s["references"])]
        cms, sms = c["duration"] / 1000, (child[0]["duration"] / 1000 if child else None)
        ok = cms >= 500 and sms is not None and sms < 60
        check(f"Jaeger trace {tid}: departures-api client span {cms:.0f} ms, stops-api server span {sms if sms is None else round(sms)} ms", ok)
        shown += 1
        if shown == 2:
            break
    r = search("enriched-spans-*", {"size": 5, "sort": [{"@timestamp": "desc"}], "query": {"bool": {"filter": [
        {"prefix": {"attributes.user_agent.original": "JourneyApp/5.0"}}, {"term": {"kind": "Server"}},
        {"range": {"@timestamp": {"gte": "now-5m", "lte": "now-30s"}}}]}}})
    for h in r["hits"]["hits"][:3]:
        src = h["_source"]
        n = search("enriched-spans-*", {"size": 0, "track_total_hits": True, "query": {"bool": {"filter": [
            {"term": {"traceId": src["traceId"]}}, {"term": {"resource.service.name": "stops-api"}}]}}})["hits"]["total"]["value"]
        check(f"5.0 trace {src['traceId']}: {n} stops-api calls (url.query={src['attributes'].get('url.query')})", 20 <= n <= 30)
        tid = src["traceId"]
    agg = search("enriched-*", {"size": 0, "query": {"term": {"traceId": tid}}, "aggs": {"i": {"terms": {"field": "_index"}}}})
    by = {b["key"].split("-")[1]: b["doc_count"] for b in agg["aggregations"]["i"]["buckets"]}
    check(f"traceId:{tid} on enriched-* returns logs and spans", by.get("logs", 0) > 0 and by.get("spans", 0) > 0, str(by))
    ip = get("http://localhost:5601/api/saved_objects/index-pattern/enriched")
    names = {f["name"] for f in json.loads(ip["attributes"]["fields"])}
    for f in ("attributes.user_agent.original", "attributes.url.query", "resource.service.name", "traceId"):
        check(f"index pattern enriched-* has field {f}", f in names)
    fmt = json.loads(ip["attributes"]["fieldFormatMap"]).get("traceId", {})
    check("traceId is a link to Jaeger", "16686/trace/" in fmt.get("params", {}).get("urlTemplate", ""))


if __name__ == "__main__":
    wp, sp = classic()
    if sys.argv[1:] == ["incident"]:
        check("departures-api log: stops_api_ms p50 >= 500 on timetable lines", (wp["50.0"] or 0) >= 500, f"p50 {wp['50.0']}")
        check("stops-api log: platform lookups p95 < 60 ms", (sp["95.0"] or 999) < 60, f"p95 {sp['95.0']}")
        enriched()
    print(f"verify: {FAIL} failure(s)")
    sys.exit(FAIL)
