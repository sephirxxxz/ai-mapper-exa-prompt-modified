# Must-Fix Runtime Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the AI Mapper Agent safe to use for a real candidate-bearing run by closing evidence, rating, interface, date-window, recovery, and Context Mode preflight gaps.

**Architecture:** Keep the fixed 40-row Exa plan and append-only run artifacts. Add typed lifecycle commands for the operations currently requiring manual JSONL edits; make Guard validate claim text and rating schema; make malformed responses terminate cleanly; and require the launcher/CLI to carry the isolated Context Mode environment contract.

**Tech Stack:** Python 3 standard library, unittest, Bash launchers, Markdown Agent instructions.

---

### Task 1: Bind evidence to the exact candidate claim

**Files:** `tests/test_final_guard.py`, `ai_mapper_agent/guard.py`

- [ ] Add a failing test where an A candidate claim text differs from the linked evidence `claim` text and assert `CLAIM_TEXT_MISMATCH`.
- [ ] Run the focused test and confirm it fails because Guard currently checks only IDs.
- [ ] Add claim-text equality validation for every linked evidence row; retain candidate and claim ID checks.
- [ ] Run the focused test and the existing final-guard tests.

### Task 2: Restore a post-Elsewhere rating contract

**Files:** `references/rating-rubric.md`, `SKILL.md`, `README.md`, `tests/test_final_guard.py`, `ai_mapper_agent/guard.py`

- [ ] Add a failing test for an unknown rating on a reviewed unique candidate and assert `RATING_INVALID`.
- [ ] Define the allowed ratings `A`, `B`, `C`, and `暂不跟进`; document project-first scope, early-stage/freshness/evidence/why-now gates, and the allowed gap enum without Elsewhere.
- [ ] Reject unknown ratings in Guard and document the exact candidate JSONL fields required for review.
- [ ] Run all Guard and documentation-contract tests.

### Task 3: Expose the real fetch, review, and evidence operations through the launcher

**Files:** `tests/test_cli.py`, `ai_mapper_agent/cli.py`, `ai_mapper_agent/evidence.py`, `ai_mapper_agent/fetch.py`, `SKILL.md`, `README.md`

- [ ] Add failing CLI tests for `fetch`, `review-candidate`, and `record-evidence`.
- [ ] Add `fetch` with the existing safe HTTP pipeline, `review-candidate` with atomic candidate-row replacement and a `candidate_review` event, and `record-evidence` that reads a run-local page and calls `record_evidence`.
- [ ] Keep report writing as a normal run-local file operation but document the exact report names and required sections.
- [ ] Run CLI tests and a positive candidate-bearing offline workflow.

### Task 4: Make the fixed publication window include the run date and preserve timezone semantics

**Files:** `tests/test_contract_and_plan.py`, `ai_mapper_agent/plan.py`, `ai_mapper_agent/run.py`, `ai_mapper_agent/guard.py`, `references/run-schema-v2.md`

- [ ] Change the plan test to require an explicit local-time start boundary and the next-day exclusive end boundary.
- [ ] Pass the manifest timezone into plan construction and Guard reconstruction.
- [ ] Update the payload and schema documentation; verify all 40 rows remain `auto` with 10 results.

### Task 5: Recover cleanly from malformed successful Exa responses

**Files:** `tests/test_planned_exa_execution.py`, `ai_mapper_agent/exa.py`, `ai_mapper_agent/evidence.py`, `ai_mapper_agent/guard.py`

- [ ] Add a failing test for a successful transport response whose `results` is not a list; require one terminal `failed` row and no partial raw/candidate record.
- [ ] Validate the response before persisting a success attempt; record a terminal `failed` attempt with `INVALID_RESPONSE` and allow the run to continue as partial.
- [ ] Verify no retry lock or persisted attempt prevents a deliberate new run from handling the query.

### Task 6: Enforce the Context Mode environment contract and document the 40-query retry semantics

**Files:** `tests/test_context_mode_receipts.py`, `ai_mapper_agent/context_mode.py`, `ai_mapper_agent/cli.py`, `scripts/install.sh`, `SKILL.md`, `README.md`, `references/context-mode-contract.md`

- [ ] Add a failing test that successful `context-record` is rejected when `CONTEXT_MODE_PROJECT_DIR` and `CONTEXT_MODE_DIR` do not match the run root and isolated directory.
- [ ] Require those exact environment values for successful preflight and export them from the installed launcher for the lifecycle subprocess; retain the host-level requirement that the Harness/MCP server must be started with the same values.
- [ ] State that 40 is the logical query count and retries can create additional API requests; stop with an explicit status when the user wants a hard request cap.
- [ ] Run the complete suite, shell checks, hygiene scans, and a positive candidate-bearing workflow.
