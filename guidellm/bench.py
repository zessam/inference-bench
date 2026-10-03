"""Run GuideLLM profiles one after another inside the GuideLLM container.

    docker compose run --rm guidellm                  # PROFILES from .env (default: all)
    docker compose run --rm guidellm poisson          # one
    docker compose run --rm guidellm sweep poisson    # several, in this order
    docker compose run --rm guidellm all              # every config in configs/
    docker compose run --rm guidellm --list           # show available profiles
    docker compose run --rm guidellm sweep --run-id baseline

Each profile is configs/<name>.json. Reports go to
<results>/<run id>/<profile>/benchmarks.{json,csv,html}.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path(os.getenv("CONFIG_DIR", "/configs"))
RESULTS_DIR = Path(os.getenv("RESULTS_DIR_IN_CONTAINER", "/results"))
FORMATS = ("json", "csv", "html")


def available():
    return sorted(p.stem for p in CONFIG_DIR.glob("*.json"))


def endpoint_env():
    """GuideLLM backend settings from the VLLM_* values in .env."""
    base_url = os.getenv("VLLM_BASE_URL", "").strip().rstrip("/")
    model = os.getenv("VLLM_MODEL", "").strip()
    api_key = os.getenv("VLLM_API_KEY", "").strip()

    problems = []
    if not base_url or "YOUR-SERVER" in base_url:
        problems.append("VLLM_BASE_URL is not set")
    if not model or model == "YOUR-MODEL-ID":
        problems.append("VLLM_MODEL is not set")
    if problems:
        sys.exit("Set these in .env: " + "; ".join(problems))

    if base_url.endswith("/v1"):
        base_url = base_url[:-3]

    env = os.environ.copy()
    env["GUIDELLM__SPEC__BACKEND__TARGET"] = base_url
    env["GUIDELLM__SPEC__BACKEND__MODEL"] = model
    if api_key and api_key != "your_vllm_api_key":
        env["GUIDELLM__SPEC__BACKEND__API_KEY"] = api_key
    return env, base_url, model


def missing_trace(config_path):
    """Path of a replay trace that does not exist, else None."""
    spec = json.loads(config_path.read_text()).get("spec", {})
    for data in spec.get("data", []):
        path = (data.get("source") or {}).get("path")
        if path and not Path(path).exists():
            return path
    return None


def main():
    names = available()
    parser = argparse.ArgumentParser(
        prog="docker compose run --rm guidellm",
        description="Run GuideLLM profiles in order.",
    )
    parser.add_argument(
        "profiles", nargs="*",
        help=f"any of: {', '.join(names)}, or 'all' "
             "(default: PROFILES from .env)",
    )
    parser.add_argument(
        "--run-id",
        default=os.getenv("RUN_ID") or datetime.now().strftime("%Y%m%d-%H%M%S"),
        help="results folder name (default: RUN_ID from .env, else a timestamp)",
    )
    parser.add_argument("--list", action="store_true",
                        help="list available profiles and exit")
    args = parser.parse_args()

    if args.list:
        print("\n".join(names))
        return 0

    requested = args.profiles or [os.getenv("PROFILES") or "all"]
    # Accept "a,b" as well as "a b".
    requested = [p.strip() for item in requested for p in item.split(",") if p.strip()]
    profiles = names if "all" in requested else requested

    unknown = [p for p in profiles if p not in names]
    if unknown:
        parser.error(
            f"unknown profile(s): {', '.join(unknown)}. "
            f"Available: {', '.join(names)}, all"
        )

    env, base_url, model = endpoint_env()
    run_dir = RESULTS_DIR / args.run_id
    print(f"Endpoint: {base_url}  model: {model}", flush=True)
    print(f"Running {', '.join(profiles)} -> {args.run_id}/", flush=True)

    results = []
    for profile in profiles:
        config = CONFIG_DIR / f"{profile}.json"
        out = run_dir / profile
        trace = missing_trace(config)
        if trace:
            print(f"\n=== {profile}: skipped, trace file not found: {trace}",
                  flush=True)
            results.append((profile, "skipped (no trace)", None))
            continue

        print(f"\n=== {profile} ===", flush=True)
        cmd = [
            sys.executable, "-m", "guidellm", "run",
            f"--scenario={config}",
            f"--label=run={args.run_id}",
            f"--label=profile={profile}",
            *[f"--output=kind={f},path={out}/benchmarks.{f}" for f in FORMATS],
            "--disable-console-interactive",
        ]
        start = time.monotonic()
        code = subprocess.run(cmd, env=env).returncode
        minutes = (time.monotonic() - start) / 60
        status = "ok" if code == 0 else f"failed (exit {code})"
        results.append((profile, f"{status}, {minutes:.1f} min", out))

    print(f"\nSummary for run {args.run_id}:")
    for profile, status, out in results:
        where = f"  {args.run_id}/{profile}/" if out else ""
        print(f"  {profile:12} {status}{where}")

    # Skipped profiles (e.g. replay without a trace) don't fail the run.
    return 1 if any(s.startswith("failed") for _, s, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
