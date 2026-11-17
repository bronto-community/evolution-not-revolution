# Two labs side by side, same apps, same traffic, one OpenSearch:
#   transit-classic   departures-api + stops-api, log files shipped by Fluent Bit (what we have)
#   transit-enriched  the same + injector (traces, trace_id in the log line) + OpenTelemetry Collector
#   transit-shared    OpenSearch, OpenSearch Dashboards, Jaeger, the load generator (and the rollout schedule)
# `make help` lists the targets.
SHELL := /bin/bash
DC    := scripts/lab.sh
export BUILDX_BUILDER := desktop-linux

.PHONY: help build up down status schedule fix reset screens walk record
help:
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

build: ## build the images, fetch the injector + Python agent (needs network once)
	docker build --load -q -t transit-lab/departures-api:3.1.0 --build-arg APP_NAME=departures-api --build-arg APP_VERSION=3.1.0 app
	docker build --load -q -t transit-lab/stops-api:1.8.2 --build-arg APP_NAME=stops-api --build-arg APP_VERSION=1.8.2 app
	docker build --load -q -t transit-lab/loadgen:1 --build-arg APP_NAME=loadgen --build-arg APP_VERSION=1 app
	[ -d injector/root/usr ] || injector/install.sh

up: ## start everything, wait until healthy, set up OpenSearch + Dashboards (about 2 min)
	@docker image inspect transit-lab/loadgen:1 >/dev/null 2>&1 && [ -d injector/root/usr ] || $(MAKE) build
	@mkdir -p logs/classic logs/enriched state
	$(DC) shared up -d --wait opensearch jaeger dashboards
	@scripts/setup.py --no-dashboards
	$(DC) classic  up -d --wait --remove-orphans
	$(DC) enriched up -d --wait --remove-orphans
	$(DC) shared --profile load up -d loadgen
	@scripts/setup.py
	@scripts/status.py

down: ## stop everything, keep the data
	-$(DC) shared --profile load stop loadgen
	-$(DC) enriched down --remove-orphans
	-$(DC) classic  down --remove-orphans
	-$(DC) shared --profile load down

status: ## schedule, 5.0 share, boards served from timetable per lab, stops-api, alerts, clock drift
	@scripts/status.py

# make schedule                          show the plan
# make schedule ROLLOUT_AT=14:25         JourneyApp 5.0 rollout starts at 14:25 (local time)
# make schedule ROLLOUT_IN=10m           ... in 10 minutes
#   RAMP=5m (default)  SHARE=15 (default, % of phones on 5.0 at the end of the ramp)
# make schedule OFF=1                    no rollout (all phones on 4.0)
schedule: ## show or set the JourneyApp 5.0 rollout (ROLLOUT_AT=HH:MM | ROLLOUT_IN=10m, RAMP=5m, SHARE=15, OFF=1)
	@scripts/schedule.py ROLLOUT_AT="$(ROLLOUT_AT)" ROLLOUT_IN="$(ROLLOUT_IN)" RAMP="$(RAMP)" SHARE="$(SHARE)" OFF="$(OFF)"

fix: ## mitigation: stops-api connection pool 5 -> 50 in departures-api, restart it in both labs
	@echo 50 > state/pool-size
	@$(DC) classic up -d --no-deps departures-api & $(DC) enriched up -d --no-deps departures-api & wait
	@echo "departures-api restarted with STOPS_API_POOL_SIZE=50 in both labs"

reset: ## back to normal for the next run: no rollout, pool size 5 (WIPE=1: also delete all data)
	@rm -f state/pool-size; scripts/schedule.py OFF=1 >/dev/null
	@if [ -n "$(WIPE)" ]; then \
	  $(DC) shared --profile load stop loadgen; \
	  $(DC) enriched down -v --remove-orphans; $(DC) classic down -v --remove-orphans; \
	  $(DC) shared --profile load down -v; rm -rf logs/classic logs/enriched; \
	  $(MAKE) up; \
	else \
	  ($(DC) classic up -d --no-deps departures-api & $(DC) enriched up -d --no-deps departures-api & wait); \
	  echo "rollout off, departures-api back to STOPS_API_POOL_SIZE=5 in both labs"; fi

screens: ## screenshots of the before/after click paths into screens/ (while the incident is on)
	node scripts/ui/screens.js

walk: ## stills of both click paths for the deck (slides/public/walk, slides/components/walk.json), while the incident is on
	node scripts/ui/walk.js

record: ## record before.mp4 and after.mp4 into recordings/ (while the incident is on)
	scripts/record/record.sh
