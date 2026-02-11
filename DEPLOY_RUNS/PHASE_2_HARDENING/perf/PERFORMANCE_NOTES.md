# Performance Notes (Phase 2D)

## Dataset/Scenario
- Seed target: 150 patients with orders.
- Concurrent probe: 5 workers issuing worklist/results reads (10 total API calls).
- Probe script output: `performance_probe.txt`.

## Observed Latency (avg / max)
- `/api/v1/patients/`: 88.12 ms / 379.11 ms
- `/api/v1/worklist/patients/`: 25.89 ms / 33.96 ms
- `/api/v1/samples/pending_collections/`: 6.56 ms / 16.37 ms
- `/api/v1/results/worklist/`: 13.97 ms / 33.13 ms

## Concurrency Batch
- 5-worker batch wall time: 134.21 ms
- Calls executed: 10

## Limitations
- Probe executed in containerized local environment, not production hardware.
- This is a synthetic stress approximation; full browser E2E concurrency still pending.
