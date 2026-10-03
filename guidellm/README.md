# GuideLLM benchmarks

Load-tests an OpenAI-compatible endpoint (for example vLLM) with
[GuideLLM](https://github.com/vllm-project/guidellm) running in its official
Docker image (`ghcr.io/vllm-project/guidellm:v0.8.0`). Nothing to install
besides Docker.

> **Cost warning:** benchmarks send real load to your endpoint and can incur
> GPU costs.

## Setup

1. Install Docker Desktop. On Windows, turn on **Settings → Resources → WSL
   Integration** for your WSL distro.
2. Copy `.env.example` to `.env` (in this folder) and fill in:
   ```
   VLLM_BASE_URL=<server URL, e.g. http://<host>:8000>   # without /v1
   VLLM_API_KEY=<the key vLLM was started with>
   VLLM_MODEL=<model id served by the endpoint>
   ```
   These are read from `.env` only. Variables set in your shell do not override
   them. The run stops with a message if they are missing.

   Check the URL, key and model before a run:
   ```bash
   source .env
   curl -s -H "Authorization: Bearer $VLLM_API_KEY" "$VLLM_BASE_URL/v1/models"
   ```
   `VLLM_MODEL` must match the `id` it returns. GuideLLM also downloads that
   model's tokenizer from Hugging Face to size the prompts.

## Running

From this folder:

```bash
docker compose run --rm guidellm                    # PROFILES from .env (default: all)
docker compose run --rm guidellm poisson            # one profile
docker compose run --rm guidellm sweep poisson      # several, in this order
docker compose run --rm guidellm all                # every config in configs/
docker compose run --rm guidellm --list             # available profiles
docker compose run --rm guidellm sweep --run-id baseline
```

Profiles always run one after another, never in parallel, so they don't skew
each other's results. A summary at the end shows each profile as ok, failed
or skipped.

## Profiles

| Profile | What it measures | Default settings |
|---|---|---|
| `synchronous` | One request at a time: baseline latency | 60 s |
| `throughput` | Everything at once: maximum throughput | up to 256 in flight, 60 s |
| `concurrent` | Fixed number of parallel streams | 1, 4, 16, 32 streams, 60 s each |
| `poisson` | Random (Poisson) arrivals at set rates | 1, 2, 4, 8 req/s, 60 s each |
| `sweep` | Synchronous, throughput, then rates in between | 10 steps, 30 s each |
| `replay` | Timing and sizes from a trace file | needs a trace, see below |

Synthetic profiles send 256-token prompts and ask for 128 output tokens. Each
step stops at its time limit or at a 10% error rate.

Each profile is a GuideLLM scenario file, `configs/<profile>.json`. Edit it to
change settings:

- profile options: `streams`, `rate`, `sweep_size`, `max_concurrency`, `time_scale`
- data: `prompt_tokens`, `output_tokens`
- limits: `max_duration` (`seconds`), `max_requests` (`count`), `max_error_rate` (`rate`)

A new `.json` file in `configs/` becomes a new profile name automatically.

### Replay traces

`replay` sends synthetic prompts sized and timed from a trace file. Put the
trace in `traces/sample.jsonl`, one JSON object per line:

```json
{"timestamp": 0.0, "input_length": 256, "output_length": 128}
{"timestamp": 0.4, "input_length": 512, "output_length": 64}
```

`timestamp` is in seconds and the lengths are in tokens. To use another file
name or a CSV, change `data[0].source` in `configs/replay.json` (path
`/traces/<file>`, `"kind": "csv_file"` for CSV). With no trace, `replay` is
skipped and the other profiles still run.

## Results

Reports are written to the folder you run the command from:

```
./<run id>/<profile>/
  benchmarks.json   full report (source of truth)
  benchmarks.csv    one row per sub-benchmark
  benchmarks.html   interactive report, open in a browser
```

The run id is a timestamp unless you pass `--run-id` or set `RUN_ID` in
`.env`. To write somewhere else, set `RESULTS_DIR` in `.env`. To run from
another folder, point at this compose file:

```bash
cd ~/my-reports
docker compose -f /path/to/inference-bench/guidellm/compose.yaml run --rm guidellm all
```

Tokenizer downloads are cached in `.hf-cache/` in this folder.

## How it works

```
compose.yaml   the GuideLLM image, .env, and folder mounts
bench.py       picks profiles, runs `guidellm run` for each, prints a summary
configs/       one GuideLLM scenario per profile
traces/        trace files for replay
```

`bench.py` runs inside the container. For each profile it calls:

```bash
guidellm run --scenario=/configs/<profile>.json \
  --output=kind=json,path=/results/<run id>/<profile>/benchmarks.json  # also csv, html
```

It passes the endpoint, model and key from `.env` to GuideLLM as environment
variables, so the key is never written to `configs/` or to the reports.

`configs/` uses GuideLLM 0.8's format. Change `GUIDELLM_VERSION` only
together with the configs.
