from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# Histograms
JOB_STAGE_DURATION = Histogram(
    "patchpilot_job_stage_duration_seconds",
    "Duration of pipeline stages in seconds",
    ["stage", "outcome"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

LLM_CALL_LATENCY = Histogram(
    "patchpilot_llm_latency_seconds",
    "LLM call response latency in seconds",
    ["provider", "model", "purpose"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 60.0],
)

# Counters
JOBS_TOTAL = Counter(
    "patchpilot_jobs_total",
    "Total number of repair/scan jobs processed",
    ["type", "status", "verdict"],
)

LLM_TOKENS_TOTAL = Counter(
    "patchpilot_llm_tokens_total",
    "Total input and output tokens consumed",
    ["model", "direction"],  # prompt / completion
)

GUARD_VIOLATIONS_TOTAL = Counter(
    "patchpilot_guard_violations_total",
    "Total static patch guard violations detected",
    ["code", "cwe"],
)

REVIEWS_TOTAL = Counter(
    "patchpilot_reviews_total",
    "Total human review decisions made",
    ["decision"],
)

# Gauges
ACTIVE_SANDBOXES = Gauge(
    "patchpilot_active_sandboxes",
    "Current number of concurrently active sandbox containers",
)

QUEUE_DEPTH = Gauge(
    "patchpilot_queue_depth",
    "Number of pending jobs in queue",
    ["queue_name"],
)

