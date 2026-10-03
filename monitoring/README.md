# vLLM monitoring

Prometheus and Grafana for watching the vLLM server's own metrics (queue
length, KV-cache usage, token throughput, latency) while benchmarks run. This
complements GuideLLM's client-side reports in `../guidellm`.

```
docker-compose.yaml     Prometheus (port 9090) and Grafana (port 3000)
.env                    which vLLM to scrape, Grafana login (copy .env.example)
prometheus.yaml         what Prometheus scrapes, filled in from .env
grafana.json            vLLM's Grafana dashboard
grafana-provisioning/   loads the data source and grafana.json on start
```

## Point it at your vLLM server

vLLM serves Prometheus metrics at `/metrics` on its API port; this needs no
API key. Copy `.env.example` to `.env` (in this folder) and set the target.

A remote vLLM server (use `https` and no port when it is behind HTTPS):

```
VLLM_METRICS_TARGET=<host>:8000
VLLM_METRICS_SCHEME=http
```

vLLM on this machine:

```
VLLM_METRICS_TARGET=host.docker.internal:8000
VLLM_METRICS_SCHEME=http
```

`.env` also sets the Grafana login (`GF_SECURITY_ADMIN_USER`,
`GF_SECURITY_ADMIN_PASSWORD`, default `admin` / `admin`).

## Run

From this folder:

```bash
docker compose up -d
```

- Grafana: http://localhost:3000, log in with the user and password from
  `.env`. Open **Dashboards → vLLM** and choose your model in the `model_name`
  drop-down. The Prometheus data source and the dashboard are set up
  automatically.
- Prometheus: http://localhost:9090. Under **Status → Targets**, `vllm` should
  be **UP**.

After changing `.env`, `prometheus.yaml` or `grafana.json`, restart:

```bash
docker compose up -d --force-recreate
```

## Stop

```bash
docker compose down
```
