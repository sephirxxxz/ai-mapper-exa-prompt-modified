# AI Mapper Run Modes

Use this before Exa recall. `references/run-modes.json` is the machine-readable source of truth for validator gate minimums; keep the Markdown explanation and JSON config in sync. The default mode is `adaptive standard scan`: it has a minimum acceptable line, a target range, and a cap. Do not mechanically chase the cap when marginal yield is low.

## Mode Selection

| Mode | Trigger | Completion label |
|---|---|---|
| `adaptive standard scan` | Default for normal `/ai-mapper` and `TOPIC=通用扫描` runs | `complete` when all standard minimum gates pass and Elsewhere is available; `degraded / Exa-only` when Elsewhere is unavailable but Exa/public-source gates pass |
| `deep map` | Only when the user explicitly asks for `深度扫`, `全量市场地图`, `重扫一遍`, `尽可能不要漏`, or equivalent high-recall language | `complete` only when deep minimum gates pass and Elsewhere is available; `degraded / Exa-only` when Elsewhere is unavailable but deep Exa/public-source gates pass |
| `blocked` | Exa unavailable, no public-source path for verification, or workspace cannot be written | `blocked` |

Do not ask the user to choose a mode during a normal run. Use `adaptive standard scan` unless the user's wording clearly requests deep coverage.

## Gate Budgets

### Adaptive Standard Scan

| Metric | Minimum | Target | Cap |
|---|---:|---:|---:|
| Total Exa query/source paths | 36 | 40-70 | 80 |
| Total Exa candidate URLs | 160 | 180-320 | 350 |
| Total opened/fetched original pages | 50 | 60-100 | 120 |
| Total raw P0/P1 leads | 30 | 35-70 | 80 |
| Source families | 10 | 12-16 | 18 |
| C-funding source families | 6 | 6-8 | 10 |
| Elsewhere financing/startup candidate facts | 5 | 8-15 | 20 |

### Deep Map

| Metric | Minimum | Target | Cap |
|---|---:|---:|---:|
| Total Exa query/source paths | 100 | 100-120 | 140 |
| Total Exa candidate URLs | 500 | 500-600 | 700 |
| Total opened/fetched original pages | 150 | 150-180 | 220 |
| Total raw P0/P1 leads | 100 | 100-120 | 150 |
| Source families | 18 | 18-24 | 28 |
| C-funding source families | 10 | 10-14 | 16 |
| Elsewhere financing/startup candidate facts | 20 | 20-30 | 40 |

## Lane Allocation

### Adaptive Standard Scan

| Lane | Query target | Candidate URL target | Opened pages target | Raw leads target |
|---|---:|---:|---:|---:|
| A-dev | 10-14 | 40-70 | 12-22 | 8-15 |
| B-content | 8-12 | 35-60 | 10-18 | 6-12 |
| C-funding | 14-22 | 70-140 | 24-42 | 12-25 |
| D-academic | 8-12 | 35-60 | 10-18 | 6-12 |

Standard scan minimum lane gates for `run-report.md`:

| Gate | Minimum |
|---|---:|
| C-funding query/source paths | 12 |
| C-funding candidate URLs | 70 |
| C-funding opened/fetched pages | 18 |
| C-funding raw financing/startup leads | 10 |

### Deep Map

| Lane | Query target | Candidate URL target | Opened pages target | Raw leads target |
|---|---:|---:|---:|---:|
| A-dev | 25-35 | 100-140 | 35-50 | 25-35 |
| B-content | 20-30 | 90-130 | 30-45 | 20-30 |
| C-funding | 50-60 | 300-330 | 80-95 | 50-70 |
| D-academic | 20-30 | 90-130 | 30-45 | 20-30 |

Deep map minimum lane gates for `run-report.md`:

| Gate | Minimum |
|---|---:|
| C-funding query/source paths | 50 |
| C-funding candidate URLs | 300 |
| C-funding opened/fetched pages | 80 |
| C-funding raw financing/startup leads | 50 |

## Early Stop Rule

After the selected mode's minimum gates pass, Main Codex may stop before the target/cap only when marginal yield is low.

Record the marginal-yield check in `run-report.md`. The check passes when the latest review batch of 25-30 new candidate URLs produces fewer than 3 new plausible P0/P1 leads, or the new pages are mostly duplicates, mature companies, stale items, closed-source-only items, or out-of-scope pages, and all four lanes have usable coverage.

Do not use early stop before the minimum gates pass. Do not use context pressure as an early-stop reason; use context-mode and compact artifacts instead.

## Run Report Fields

Every run report must state:

- `run_mode`: `adaptive standard scan` / `deep map` / `blocked`
- selected budget table: minimum, target, cap
- lane allocation actuals
- marginal-yield check: batch size, new P0/P1 leads, duplicate/stale/out-of-scope rate, stop/continue decision
- whether every minimum gate for the selected mode passed

