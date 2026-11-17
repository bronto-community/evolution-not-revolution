# Evolution, not revolution

Growing observability on top of the monitoring you already have. A talk by Severin Neumann
([Bronto](https://bronto.io)) at [OSMC 2026](https://osmc.de), Nuremberg, 18 November 2026.

**Slides:** https://evolution-not-revolution-talk.vercel.app (presenter view with speaker notes: `/presenter`)

> Evolution, Not Revolution: Growing Observability on Top of the Monitoring You Already Have
>
> It’s 2 a.m. Your monitoring is doing exactly what you built it to do: a check has gone red, the alert fired, you know something is wrong. So you start digging, and that’s where it gets slow. Which request? Which dependency? Why this time and not the last thousand? Your checks and dashboards told you that there’s a problem. Answering why is a different job, and it’s the job traces and logs are built for. You’ve spent years building your monitoring, Icinga, Nagios, Checkmk, dashboards, a log pipeline, and it works. Now everyone’s talking about “observability” and OpenTelemetry, and the unspoken question is: do I throw this away and start over?
>
> You don’t. This talk argues the move is evolution, not revolution. The real shift isn’t a new tool that replaces your monitoring, it’s getting the signals you already collect to work as one story instead of three. Most of you already have metrics, checks, and logs. The signal that completes the picture is tracing — the end-to-end view of a request, valuable even in a monolith and it’s easy to add with zero-code auto-instrumentation.
>
> But adding a signal isn’t the point; connecting them is. In a live demo we’ll take a metric spike, a trace, and a log line and watch them come together into a single investigation, linked by shared context, feeding an open-source backend that runs alongside the tools you already operate.
>
> You’ll leave with a concrete, low-risk path to make the monitoring you already trust answer “why,” not just “what.”

## The incident

A city transit operator runs `departures-api`, which serves live departures to the boards in the stations and
calls the shared `stops-api`. One evening the boards start showing the printed timetable. Nobody deployed
anything, there are no errors, and `stops-api` is fast by its own logs. The cause is another company's app:
JourneyApp 5.0 adds `&include=route`, so each request makes 26 parallel calls to `stops-api` through
`departures-api`'s pool of 5 connections, and the boards wait for a connection.

With the logs we have today the trail ends there. With the same logs plus context (semantic-convention names,
the `trace_id` in the log line, zero-code traces) you can follow the data from the alert to the cause.

## What's in here

| | |
|---|---|
| [`slides/`](slides) | the deck ([Slidev](https://sli.dev)), with speaker notes |
| [`lab/`](lab) | the incident in two labs side by side, same apps and traffic: **classic** (log files shipped by Fluent Bit) and **enriched** (the same log files plus the OpenTelemetry Injector, the `trace_id` in the log line, and an OpenTelemetry Collector). OpenSearch, OpenSearch Dashboards and Jaeger, all open source, all on your laptop |
| [`agent-demo/`](agent-demo) | the same question asked of a coding agent, without and with context (Claude Code against a scripted model, with tool results from the lab) |

## Run it

The deck:

```bash
cd slides && npm install && npm run dev
```

The lab (Docker Desktop, about 2 CPU cores; see [`lab/README.md`](lab/README.md)):

```bash
cd lab
make up                          # first time about 5 minutes
make schedule ROLLOUT_IN=10m     # JourneyApp 5.0 starts rolling out in 10 minutes
make status                      # what the boards see, per lab
```

Then follow the alert in OpenSearch Dashboards (http://localhost:5601) and Jaeger (http://localhost:16686).
`make fix` is the mitigation, `make reset` gets the lab ready for the next run.

## License

[Apache-2.0](LICENSE), for the code and for the deck. The Bronto name, logo and dinosaur illustrations are
trademarks of Bronto and not covered by the license.
