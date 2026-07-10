# AI Mapper Run States

Use this with `references/run-modes.md` before writing final, latest pointer, or run-report artifacts.

## State Table

| State | Trigger | Standard outputs | Required wording | Forbidden |
|---|---|---|---|---|
| `complete` | Elsewhere is available, Exa is available, selected run-mode gates pass, public-source evidence supports A/B rows | All standard paths, including final, raw, latest pointer, validated/rated, `candidates.jsonl`, `evidence.jsonl`, and run-report | `完整性状态: complete` | Cannot mark Elsewhere as unavailable; cannot use search snippets as evidence |
| `degraded / Exa-only` | Elsewhere key is missing or API returns quota/rate exhaustion, Exa is available, selected Exa/public-source gates pass | Same standard paths as complete; no alternate `*-exa-only` files | `完整性状态: degraded / Exa-only`; Elsewhere source layer may use `待补 Elsewhere`; team/person/background/contact gaps must use public-web/Codex search wording | Cannot call the run complete; cannot silently omit Elsewhere status; cannot use Elsewhere as team/person/background follow-up wording |
| `blocked` | Exa unavailable, Exa response persistence fails, workspace cannot be written, or public-source evidence cannot verify candidates after required recall/open work has been attempted | Standard run-report path and blocker final/latest when possible | `完整性状态: blocked`; exact blocker reason | Cannot produce decision-ready A/B tables; cannot use under-minimum recall/open counts as the blocker when Exa and workspace are available |

## State Transition Rules

1. Start every run in `preflight`.
2. If Exa is unavailable, transition to `blocked`.
3. If Exa is available and Elsewhere is available, continue toward `complete`.
4. If Exa is available but Elsewhere is missing, quota-exhausted, or rate-limited, continue toward `degraded / Exa-only`.
5. A run can move from `complete` candidate to `degraded / Exa-only` only when Elsewhere fails during the run and the failure is recorded.
6. A run cannot move from `degraded / Exa-only` to `complete` unless Elsewhere keyword intelligence, discovery, financing pass, and enrichment are actually completed and recorded.
7. A run cannot move to `blocked` merely because selected-mode Exa query/source paths, candidate URLs, opened/fetched pages, source-family coverage, or C-funding lane gates are below minimum. While Exa is available and the workspace is writable, under-minimum counts mean continue recall/opening; they are not a deliverable state.

## Required Status Block

Every final report starts with:

```markdown
## 运行状态

- run_mode: adaptive standard scan / deep map / blocked
- 完整性状态: `complete` / `degraded / Exa-only` / `blocked` (do not write bare `degraded`)
- Elsewhere 状态: available / missing_key / quota_exhausted / rate_limited / error / not_run
- Exa 状态: available / unavailable
- 停止原因: reached_minimum_and_low_marginal_yield / reached_target / reached_cap / blocked
- 影响: {what is missing or trustworthy about this run}
```

Latest pointer must repeat run mode, completeness, Elsewhere status, Exa status, stop reason, final path, raw path, and run-report path.
