# vLLM monitoring

Prometheus and Grafana for watching the vLLM server's own metrics (queue
length, KV-cache usage, token throughput, latency) while benchmarks run. This
complements GuideLLM's client-side reports in `../guidellm`.

```
docker-compose.yaml   Prometheus (port 9090) and Grafana (port 3000)
prometheus.yaml       what Prometheus scrapes
grafana.json          vLLM's Grafana dashboard
```

## Point it at your vLLM server

vLLM serves Prometheus metrics at `/metrics` on its API port. Set the target
in `prometheus.yaml`.

vLLM on this machine:

```yaml
scrape_configs:
  - job_name: vllm
    static_configs:
      - targets:
          - 'host.docker.internal:8000'
```

vLLM on RunPod, through its HTTPS proxy (the default):

```yaml
scrape_configs:
  - job_name: vllm
    scheme: https
    static_configs:
      - targets:
          - '<your-pod-id>-8000.proxy.runpod.net'
```

## Run

From this folder:

```bash
docker compose up -d
```

- Prometheus: http://localhost:9090. Under **Status → Targets**, `vllm` should
  be **UP**.
- Grafana: http://localhost:3000, user `admin`, password `admin` (you'll be
  asked to change it).

## Set up Grafana (first time)

1. **Connections → Data sources → Add data source → Prometheus**, URL
   `http://prometheus:9090`, then **Save & test**.
2. **Dashboards → New → Import**, upload `grafana.json`, and pick the
   Prometheus data source you just added.
3. Choose your model in the `model_name` drop-down at the top of the dashboard.

Grafana keeps this setup only while its container exists. `docker compose
down` removes it, and you'll need to repeat these steps.

## Stop

```bash
docker compose down
```
