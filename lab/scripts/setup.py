#!/usr/bin/env python3
"""Set up OpenSearch and OpenSearch Dashboards for both labs (idempotent, run by `make up`).
OpenSearch: index templates (keyword strings, 5 s refresh, no replicas), an ingest pipeline for the enriched
indices, a retention policy (2 days), one alert monitor per lab.
Dashboards: index patterns with fixed IDs, the trace id as a link to Jaeger, light theme, two saved searches
that only set columns (named after the data, not after the answer)."""
import json
import sys
import time
import urllib.error
import urllib.request

OS, OSD = "http://localhost:9200", "http://localhost:5601"
JAEGER_UI = "http://localhost:16686"


def call(method, url, body=None, ok=(200, 201), headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Content-Type": "application/json", "osd-xsrf": "true", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        payload = e.read()
        if e.code in ok:
            return e.code, json.loads(payload or b"{}")
        raise SystemExit(f"{method} {url}: {e.code} {payload[:500]!r}")


def wait(url, what):
    for _ in range(180):
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(2)
    raise SystemExit(f"{what} not ready: {url}")


STRINGS_AS_KEYWORDS = [{"strings": {"match_mapping_type": "string", "mapping": {"type": "keyword", "ignore_above": 1024}}}]
KW = {"type": "keyword", "ignore_above": 1024}
# Every field of the log line is mapped up front, so Discover knows it before its first occurrence
# (event, stop, reason, stops_api_ms only appear with the first timetable fallback).
CLASSIC_FIELDS = {"@timestamp": {"type": "date"}, "message": {"type": "text"},
                  **{f: KW for f in ("host", "app", "version", "level", "method", "path", "event", "stop", "reason")},
                  "status": {"type": "integer"}, "duration_ms": {"type": "long"}, "stops_api_ms": {"type": "long"}}
ENRICHED_FIELDS = {
    "@timestamp": {"type": "date_nanos"}, "startTime": {"type": "date_nanos"}, "endTime": {"type": "date_nanos"},
    "observedTimestamp": {"type": "date_nanos"}, "body": {"type": "text"},
    **{f: KW for f in ("traceId", "spanId", "parentSpanId", "name", "kind")},
    "severity": {"properties": {"text": KW, "number": {"type": "long"}}},
    "resource": {"properties": {f: KW for f in ("service.name", "service.version", "host.name", "deployment.environment.name")}},
    "attributes": {"properties": {
        **{f: KW for f in ("event.name", "stop", "reason", "http.request.method", "url.path", "url.query",
                           "user_agent.original", "http.route", "url.full")},
        "duration_ms": {"type": "long"}, "stops_api_ms": {"type": "long"}, "http.response.status_code": {"type": "integer"}}}}
SETTINGS = {"number_of_shards": 1, "number_of_replicas": 0, "refresh_interval": "5s", "translog.durability": "async"}


def opensearch():
    wait(f"{OS}/_cluster/health?wait_for_status=yellow&timeout=5s", "OpenSearch")
    # enriched: spans get @timestamp = startTime (the exporter leaves it at year 1); drop the exporter's data_stream labels
    call("PUT", f"{OS}/_ingest/pipeline/enriched", {
        "description": "enriched lab: one time field for logs and spans",
        "processors": [{"script": {"source": """
            if (ctx.attributes instanceof Map) { ctx.attributes.remove('data_stream'); }
            if (ctx.startTime != null) { ctx['@timestamp'] = ctx.startTime; }"""}}]})
    call("PUT", f"{OS}/_index_template/classic-logs", {
        "index_patterns": ["classic-logs-*"], "priority": 100,
        "template": {"settings": SETTINGS, "mappings": {
            "dynamic_templates": STRINGS_AS_KEYWORDS,
            "properties": CLASSIC_FIELDS}}})
    call("PUT", f"{OS}/_index_template/enriched", {
        "index_patterns": ["enriched-*"], "priority": 100,
        "template": {"settings": {**SETTINGS, "default_pipeline": "enriched"}, "mappings": {
            "dynamic_templates": STRINGS_AS_KEYWORDS,
            "properties": ENRICHED_FIELDS}}})
    # existing indices (e.g. today's, created before a template change): add the known fields too
    call("PUT", f"{OS}/classic-logs-*/_mapping", {"properties": CLASSIC_FIELDS}, ok=(200, 404))
    call("PUT", f"{OS}/enriched-*/_mapping", {"properties": ENRICHED_FIELDS}, ok=(200, 404))
    # retention: the labs write ~1-2 GB a day; keep 2 days
    status, _ = call("GET", f"{OS}/_plugins/_ism/policies/lab-retention", ok=(200, 404))
    if status == 404:
        call("PUT", f"{OS}/_plugins/_ism/policies/lab-retention", {"policy": {
            "description": "delete lab indices after 2 days", "default_state": "hot",
            "states": [{"name": "hot", "actions": [], "transitions": [{"state_name": "delete", "conditions": {"min_index_age": "2d"}}]},
                       {"name": "delete", "actions": [{"delete": {}}], "transitions": []}],
            "ism_template": [{"index_patterns": ["classic-logs-*", "enriched-*"], "priority": 100}]}})
    monitors()


def monitor(lab, index, path_field, event_field):
    """The same alert in both labs: more than 5 % of /departures requests served from the timetable in the last minute."""
    return {
        "type": "monitor", "monitor_type": "query_level_monitor", "enabled": True,
        "name": f"{lab}: departures served from timetable",
        "schedule": {"period": {"interval": 1, "unit": "MINUTES"}},
        "inputs": [{"search": {"indices": [index], "query": {
            "size": 0,
            "query": {"bool": {"filter": [{"range": {"@timestamp": {
                "gte": "{{period_end}}||-1m", "lte": "{{period_end}}", "format": "epoch_millis"}}}]}},
            "aggs": {"departures": {"filter": {"term": {path_field: "/departures"}}},
                     "timetable": {"filter": {"term": {event_field: "served_from_timetable"}}}}}}}],
        "triggers": [{"query_level_trigger": {
            "name": "more than 5% from timetable", "severity": "1",
            "condition": {"script": {"lang": "painless", "source":
                "def d = ctx.results[0].aggregations.departures.doc_count; "
                "return d > 0 && ctx.results[0].aggregations.timetable.doc_count * 100.0 / d > 5"}},
            "actions": []}}]}


def monitors():
    wanted = [monitor("classic", "classic-logs-*", "path", "event"),
              monitor("enriched", "enriched-logs-*", "attributes.url.path", "attributes.event.name")]
    _, found = call("POST", f"{OS}/_plugins/_alerting/monitors/_search",
                    {"size": 50, "query": {"match_all": {}}}, ok=(200, 404))
    existing = {h["_source"]["name"]: h["_id"] for h in found.get("hits", {}).get("hits", []) if "name" in h.get("_source", {})}
    for m in wanted:
        if m["name"] in existing:
            call("PUT", f"{OS}/_plugins/_alerting/monitors/{existing[m['name']]}", m)
        else:
            call("POST", f"{OS}/_plugins/_alerting/monitors", m)


def fields(pattern):
    """The field list Discover needs (what 'refresh field list' does)."""
    _, r = call("GET", f"{OSD}/api/index_patterns/_fields_for_wildcard?pattern={pattern}"
                       "&meta_fields=_source&meta_fields=_id&meta_fields=_type&meta_fields=_index&meta_fields=_score")
    return json.dumps(r["fields"])


def saved_object(kind, oid, attributes):
    call("POST", f"{OSD}/api/saved_objects/{kind}/{oid}?overwrite=true", {"attributes": attributes})


def dashboards():
    wait(f"{OSD}/api/status", "OpenSearch Dashboards")
    trace_link = {"id": "url", "params": {"urlTemplate": f"{JAEGER_UI}/trace/{{{{value}}}}", "labelTemplate": "{{value}}"}}
    patterns = {
        "classic-logs": ("classic-logs-*", {}),
        "enriched": ("enriched-*", {"traceId": trace_link}),              # logs + spans: one search for a trace id
        "enriched-logs": ("enriched-logs-*", {"traceId": trace_link}),
        "enriched-spans": ("enriched-spans-*", {"traceId": trace_link}),
    }
    for oid, (title, formats) in patterns.items():
        saved_object("index-pattern", oid, {"title": title, "timeFieldName": "@timestamp",
                                             "fieldFormatMap": json.dumps(formats), "fields": fields(title)})
    columns = {"classic-logs": ["app", "level", "message"],
               "enriched": ["resource.service.name", "name", "attributes.duration_ms", "body", "traceId"]}
    titles = {"classic-logs": "classic logs", "enriched": "enriched logs and spans"}
    for oid, cols in columns.items():
        call("POST", f"{OSD}/api/saved_objects/search/{oid}?overwrite=true", {
            "attributes": {"title": titles[oid], "columns": cols, "sort": [["@timestamp", "desc"]],
                           "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps({
                               "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
                               "query": {"query": "", "language": "kuery"}, "filter": []})}},
            "references": [{"name": "kibanaSavedObjectMeta.searchSourceJSON.index", "type": "index-pattern", "id": oid}]})
    call("POST", f"{OSD}/api/opensearch-dashboards/settings", {"changes": {
        "defaultIndex": "classic-logs", "dateFormat:tz": "Europe/Berlin",
        "dateFormat": "HH:mm:ss.SSS", "dateNanosFormat": "HH:mm:ss.SSS", "discover:sampleSize": 500, "timepicker:timeDefaults":
            json.dumps({"from": "now-30m", "to": "now"}),
        "home:useNewHomePage": False}})


if __name__ == "__main__":
    opensearch()
    if "--no-dashboards" not in sys.argv:
        dashboards()
    print("OpenSearch + Dashboards set up: index patterns classic-logs, enriched (logs+spans), enriched-logs, enriched-spans; 2 monitors")
