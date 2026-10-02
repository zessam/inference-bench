# inference-bench

LLM inference performance benchmarking for OpenAI-compatible endpoints, such
as vLLM on RunPod. Everything runs in Docker.

| Folder | What it does |
|---|---|
| [`guidellm/`](guidellm/README.md) | Load tests with [GuideLLM](https://github.com/vllm-project/guidellm): latency, throughput and concurrency under several traffic patterns (synchronous, throughput, concurrent, poisson, sweep, replay). Writes JSON, CSV and HTML reports. |
| [`monitoring/`](monitoring/README.md) | Prometheus and Grafana for watching the vLLM server's own metrics while a benchmark runs. |

The two are independent: use either or both.

> **Cost warning:** benchmarks send real load to your endpoint and can incur
> GPU costs.

## Quick start

Requires Docker (Docker Desktop on Windows/macOS; on WSL, turn on its WSL
integration).

```bash
git clone https://github.com/zessam/inference-bench.git
cd inference-bench

# 1. Monitoring (optional), in one terminal
cd monitoring               # set your server in prometheus.yaml
docker compose up -d        # Grafana on http://localhost:3000 (admin/admin), import grafana.json

# 2. Benchmark
cd ../guidellm
cp .env.example .env        # set VLLM_BASE_URL, VLLM_API_KEY, VLLM_MODEL
docker compose run --rm guidellm synchronous   # short warm-up run
docker compose run --rm guidellm sweep
```

Reports appear in `./<run id>/<profile>/`.

## Layout

```
guidellm/
  compose.yaml      GuideLLM official image + settings from .env
  bench.py          runs the chosen profiles in order
  configs/          one GuideLLM scenario per profile
  traces/           trace files for the replay profile
monitoring/
  docker-compose.yaml, prometheus.yaml, grafana.json
```
