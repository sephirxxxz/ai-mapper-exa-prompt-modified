# AI Mapper Agent Review Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close every P1/P2 review finding so the Agent is installable, executable, auditable, and unable to mark incomplete or unverified research as complete.

**Architecture:** Keep the Python core harness-neutral, but expose every mutation through one CLI. The CLI loads immutable plan rows by `query_id`, records structured Context Mode receipts, performs or records validated public-page fetches, and finalizes runs only through Final Guard. Codex and Claude Code adapters call this CLI; append-only records remain the audit truth.

**Tech Stack:** Python 3.11+ standard library, `unittest`, JSON/JSONL, Bash, Codex Skill metadata, Claude Code command/agent Markdown.

---

## File Structure

- `ai_mapper_agent/cli.py`: the only supported command-line mutation interface.
- `ai_mapper_agent/context_mode.py`: structured preflight receipts and ordering checks.
- `ai_mapper_agent/exa.py`: planned-query execution, retry attempts, and request/response persistence.
- `ai_mapper_agent/fetch.py`: public-network validation, bounded HTTP fetch, browser receipt validation, and fetch-cap reservation.
- `ai_mapper_agent/evidence.py`: atomic JSONL helpers, candidates, claim-specific evidence, and fetch records.
- `ai_mapper_agent/run.py`: run creation, status transitions, artifact paths, and latest pointers.
- `ai_mapper_agent/guard.py`: complete-state validation across manifest, plan, Context Mode, queries, pages, evidence, and reports.
- `scripts/install.sh`, `scripts/uninstall.sh`: verified local installation/removal.
- `.claude/commands/ai-mapper.md`: actual Claude slash-command entry.
- `SKILL.md`, `.claude/agents/ai-mapper.md`, `agents/openai.yaml`, `README.md`, `references/*.md`: harness instructions aligned with the CLI.

### Task 1: Harden run creation and schema invariants

**Files:**
- Modify: `ai_mapper_agent/run.py`
- Modify: `ai_mapper_agent/contract.py`
- Modify: `tests/test_run_lifecycle.py`

- [ ] **Step 1: Add failing tests for invalid timezones, unique run IDs, and manifest-owned artifact paths**

```python
def test_invalid_timezone_has_a_domain_error(self):
    with self.assertRaisesRegex(ValueError, "unknown timezone"):
        create_run(ROOT, topic=None, timezone_name="No/Such_Zone", now=NOW)

def test_second_run_in_same_second_gets_a_unique_suffix(self):
    first = create_run(ROOT, topic=None, timezone_name="Asia/Shanghai", now=NOW)
    second = create_run(ROOT, topic=None, timezone_name="Asia/Shanghai", now=NOW)
    self.assertNotEqual(first.run_id, second.run_id)

def test_manifest_artifacts_are_relative_to_the_run(self):
    run = create_run(ROOT, topic=None, timezone_name="Asia/Shanghai", now=NOW)
    self.assertEqual(run.manifest["artifacts"]["events.jsonl"], "events.jsonl")
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `python3 -m unittest tests.test_run_lifecycle -v`

Expected: invalid timezone raises `AttributeError`; duplicate run raises; artifact paths are absolute.

- [ ] **Step 3: Implement the minimum schema fix**

```python
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    local_now = now.astimezone(ZoneInfo(timezone_name))
except ZoneInfoNotFoundError as error:
    raise ValueError(f"unknown timezone: {timezone_name}") from error

base_id = now.strftime("%Y%m%dT%H%M%S%z")
run_id = next_available_run_id(runs_path, base_id)
artifacts = {name: name for name in REQUIRED_ARTIFACTS}
```

- [ ] **Step 4: Run focused and full tests**

Run: `python3 -m unittest tests.test_run_lifecycle -v && python3 -m unittest discover -s tests -v`

Expected: all tests pass without warnings.

- [ ] **Step 5: Commit locally**

```bash
git add ai_mapper_agent/run.py ai_mapper_agent/contract.py tests/test_run_lifecycle.py
git commit -m "fix: harden AI Mapper run creation"
```

### Task 2: Bind every Exa request to an immutable plan row and separate retries from final status

**Files:**
- Modify: `ai_mapper_agent/exa.py`
- Modify: `ai_mapper_agent/evidence.py`
- Modify: `ai_mapper_agent/guard.py`
- Create: `tests/test_planned_exa_execution.py`
- Modify: `tests/test_evidence_pipeline.py`

- [ ] **Step 1: Add failing tests for freehand execution, retries, and request persistence**

```python
def test_execute_query_loads_payload_from_saved_plan(self):
    transport = FakeTransport([{"results": []}])
    execute_query(run, "q01", transport=transport)
    planned = read_jsonl(run.path / "query-plan.jsonl")[0]
    self.assertEqual(transport.requests[0], build_search_payload(planned))

def test_public_api_does_not_accept_a_freehand_row(self):
    with self.assertRaises(TypeError):
        execute_query(run, {"query": "freehand"})

def test_transient_failures_create_attempts_but_one_final_status(self):
    transport = FakeTransport([TransientError(), TransientError(), {"results": []}])
    execute_query(run, "q01", transport=transport, sleeper=lambda _: None)
    self.assertEqual(len(read_jsonl(run.path / "query-attempts.jsonl")), 3)
    self.assertEqual(len(read_jsonl(run.path / "query-execution.jsonl")), 1)
```

- [ ] **Step 2: Run the new tests and verify RED**

Run: `python3 -m unittest tests.test_planned_exa_execution tests.test_evidence_pipeline -v`

Expected: `execute_query` and `query-attempts.jsonl` are absent; freehand payload is accepted by the old function.

- [ ] **Step 3: Implement planned execution with bounded retry**

```python
def execute_query(run: Run, query_id: str, *, transport, sleeper=time.sleep) -> dict:
    row = require_plan_row(run.path / "query-plan.jsonl", query_id)
    payload = build_search_payload(row)
    for attempt in range(1, 4):
        try:
            response = transport.post(SEARCH_URL, payload, timeout=30)
            record_attempt(run, query_id, attempt, payload, "success", response=response)
            record_final_execution(run, query_id, attempt, response)
            return response
        except TransientExaError as error:
            record_attempt(run, query_id, attempt, payload, "transient_error", error_code=error.code)
            if attempt == 3:
                record_final_failure(run, query_id, "failed", error.code)
                raise
            sleeper(2 ** (attempt - 1))
```

Persist each attempt's `query_id`, canonical request payload, payload hash, status, response/error code, and time. Authentication and credit errors produce one final status without retry. Remove the public `search(row)` API.

- [ ] **Step 4: Strengthen Guard request checks**

```python
for plan_row in plan_rows:
    attempts = attempts_by_query[plan_row["query_id"]]
    expected = build_search_payload(plan_row)
    if any(attempt["request"] != expected for attempt in attempts):
        errors.append("EXA_REQUEST_PLAN_MISMATCH")
    if len(final_rows[plan_row["query_id"]]) != 1:
        errors.append("QUERY_FINAL_STATUS_COUNT")
```

- [ ] **Step 5: Run focused and full tests**

Run: `python3 -m unittest tests.test_planned_exa_execution tests.test_final_guard -v && python3 -m unittest discover -s tests -v`

Expected: freehand execution is impossible; two retries plus success yield one final status; all tests pass.

- [ ] **Step 6: Commit locally**

```bash
git add ai_mapper_agent/exa.py ai_mapper_agent/evidence.py ai_mapper_agent/guard.py tests/test_planned_exa_execution.py tests/test_evidence_pipeline.py tests/test_final_guard.py
git commit -m "fix: bind Exa execution to the saved plan"
```

### Task 3: Record auditable Context Mode receipts and enforce event ordering

**Files:**
- Create: `ai_mapper_agent/context_mode.py`
- Modify: `ai_mapper_agent/run.py`
- Modify: `ai_mapper_agent/guard.py`
- Create: `tests/test_context_mode_receipts.py`
- Modify: `tests/test_final_guard.py`

- [ ] **Step 1: Add failing tests for fabricated strings, wrong directories, duplicate purge, and post-search preflight**

```python
def test_plain_ok_strings_cannot_create_a_context_receipt(self):
    with self.assertRaises(TypeError):
        record_context_preflight(run, doctor_result="OK", purge_result="OK")

def test_guard_rejects_context_events_after_query_execution(self):
    append_event(run, {"event": "query_attempt", "sequence": 1})
    record_context_preflight(run, valid_receipt(sequence=2))
    self.assertIn("CONTEXT_MODE_ORDER", final_guard(run.path).codes)

def test_guard_requires_exactly_one_fresh_run_project_purge(self):
    receipt = valid_receipt()
    record_context_preflight(run, receipt)
    record_context_preflight(run, receipt)
    self.assertIn("CONTEXT_MODE_PURGE_COUNT", final_guard(run.path).codes)
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest tests.test_context_mode_receipts -v`

Expected: old string API accepts fabricated success and has no order/count checks.

- [ ] **Step 3: Implement a structured receipt**

```python
@dataclass(frozen=True)
class ContextPreflightReceipt:
    doctor_tool: str
    doctor_ok: bool
    doctor_summary: str
    purge_tool: str
    purge_ok: bool
    purge_scope: str
    project_dir: str
    context_dir: str
    started_at: str
    completed_at: str
    host_call_ids: tuple[str, str]
```

`record_context_preflight()` requires both logical tool names, `doctor_ok=True`, `purge_ok=True`, `purge_scope="project"`, exact resolved directories, non-empty host call IDs, and timestamps. It appends one `context_preflight` event with a monotonically increasing sequence number and updates manifest state atomically.

- [ ] **Step 4: Enforce preflight before all research events**

```python
preflights = [event for event in events if event["event"] == "context_preflight"]
research = [event for event in events if event["event"] in RESEARCH_EVENTS]
if len(preflights) != 1:
    errors.append("CONTEXT_MODE_PURGE_COUNT")
elif research and preflights[0]["sequence"] >= min(event["sequence"] for event in research):
    errors.append("CONTEXT_MODE_ORDER")
```

- [ ] **Step 5: Run tests and commit**

Run: `python3 -m unittest tests.test_context_mode_receipts tests.test_final_guard -v && python3 -m unittest discover -s tests -v`

Expected: fabricated/unordered receipts fail; a real structured receipt passes.

```bash
git add ai_mapper_agent/context_mode.py ai_mapper_agent/run.py ai_mapper_agent/guard.py tests/test_context_mode_receipts.py tests/test_final_guard.py
git commit -m "fix: require auditable Context Mode preflight receipts"
```

### Task 4: Implement safe public-page fetching and make the 60-page cap non-bypassable

**Files:**
- Create: `ai_mapper_agent/fetch.py`
- Modify: `ai_mapper_agent/web.py`
- Modify: `ai_mapper_agent/evidence.py`
- Modify: `ai_mapper_agent/guard.py`
- Create: `tests/test_fetch_pipeline.py`
- Modify: `tests/test_web_safety.py`

- [ ] **Step 1: Add failing tests for private DNS, redirects, missing files, hash mismatch, and the 61st reservation**

```python
def test_hostname_resolving_to_private_ip_is_rejected(self):
    with self.assertRaisesRegex(ValueError, "public"):
        validate_fetch_url("https://alias.test/x", resolver=lambda _: ["127.0.0.1"])

def test_redirect_target_is_revalidated(self):
    transport = FakeHttp([Redirect("http://169.254.169.254/latest")])
    with self.assertRaisesRegex(ValueError, "public"):
        fetch_public_page(run, "https://public.test", transport=transport)

def test_guard_rejects_success_without_saved_page(self):
    record_browser_fetch_receipt(run, valid_receipt(path="pages/missing.md"))
    self.assertIn("FETCH_ARTIFACT_MISSING", final_guard(run.path).codes)

def test_sixty_first_unique_fetch_is_rejected_before_network(self):
    reserve_sixty_successful_fetches(run)
    with self.assertRaisesRegex(RuntimeError, "FETCH_CAP_REACHED"):
        fetch_public_page(run, "https://example.test/61", transport=FailIfCalled())
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest tests.test_fetch_pipeline tests.test_web_safety -v`

Expected: DNS aliases and fabricated fetch receipts currently pass; no fetch implementation exists.

- [ ] **Step 3: Implement bounded fetching**

```python
def fetch_public_page(run: Run, url: str, *, transport, resolver=resolve_host) -> FetchReceipt:
    canonical = validate_fetch_url(url, resolver=resolver)
    reserve_fetch_slot(run, canonical, limit=60)
    response = transport.get(canonical, timeout=15, follow_redirects=False)
    for _ in range(3):
        if not response.is_redirect:
            break
        canonical = validate_fetch_url(urljoin(canonical, response.location), resolver=resolver)
        response = transport.get(canonical, timeout=15, follow_redirects=False)
    body = response.read(MAX_PAGE_BYTES + 1)
    if len(body) > MAX_PAGE_BYTES:
        raise ValueError("page exceeds byte limit")
    return persist_page_and_receipt(run, canonical, body, response.content_type)
```

The append-only receipt contains canonical URL, method (`http` or `browser`), result, time, relative page path, byte count, SHA-256 hash, and failure reason. Browser receipts use the same URL validation and file/hash checks.

- [ ] **Step 4: Make Guard validate the actual artifacts**

```python
for receipt in successful_fetches:
    page = safe_run_relative_path(run_path, receipt["path"])
    if not page.is_file():
        errors.append("FETCH_ARTIFACT_MISSING")
    elif sha256(page.read_bytes()).hexdigest() != receipt["content_hash"]:
        errors.append("FETCH_HASH_MISMATCH")
```

- [ ] **Step 5: Run tests and commit**

Run: `python3 -m unittest tests.test_fetch_pipeline tests.test_web_safety tests.test_final_guard -v && python3 -m unittest discover -s tests -v`

Expected: the 61st request never reaches the transport; private/redirect targets fail; missing or changed pages fail Guard.

```bash
git add ai_mapper_agent/fetch.py ai_mapper_agent/web.py ai_mapper_agent/evidence.py ai_mapper_agent/guard.py tests/test_fetch_pipeline.py tests/test_web_safety.py tests/test_final_guard.py
git commit -m "fix: enforce safe auditable webpage fetching"
```

### Task 5: Bind each A/B claim to its own candidate evidence

**Files:**
- Modify: `ai_mapper_agent/evidence.py`
- Modify: `ai_mapper_agent/guard.py`
- Modify: `tests/test_evidence_pipeline.py`
- Modify: `tests/test_final_guard.py`

- [ ] **Step 1: Add a failing cross-candidate evidence test**

```python
def test_guard_rejects_evidence_from_another_candidate(self):
    write_candidate(candidate_id="c1", rating="A", claims=[{"claim_id": "cl1", "text": "launched"}])
    write_evidence(evidence_id="e1", candidate_id="other", claim_id="other-claim")
    link_claim("c1", "cl1", "e1")
    self.assertIn("CLAIM_EVIDENCE_MISMATCH", final_guard(run.path).codes)
```

- [ ] **Step 2: Run test and verify RED**

Run: `python3 -m unittest tests.test_final_guard.FinalGuardTests.test_guard_rejects_evidence_from_another_candidate -v`

Expected: Guard returns `ok=True` with unrelated evidence.

- [ ] **Step 3: Add stable claim IDs and exact linkage**

```python
def evidence_matches_claim(candidate: dict, claim: dict, evidence: dict) -> bool:
    return (
        evidence["candidate_id"] == candidate["candidate_id"]
        and evidence["claim_id"] == claim["claim_id"]
        and evidence["source_url"]
        and evidence["excerpt"]
        and evidence["content_hash"]
    )
```

Require at least one matching evidence record for every A/B claim. Reject duplicate candidate IDs, duplicate evidence IDs, unknown candidate references, and evidence whose source URL has no successful fetch receipt.

- [ ] **Step 4: Run tests and commit**

Run: `python3 -m unittest tests.test_evidence_pipeline tests.test_final_guard -v && python3 -m unittest discover -s tests -v`

Expected: cross-candidate and cross-claim evidence fail; valid claim evidence passes.

```bash
git add ai_mapper_agent/evidence.py ai_mapper_agent/guard.py tests/test_evidence_pipeline.py tests/test_final_guard.py
git commit -m "fix: validate claim-specific evidence links"
```

### Task 6: Add final status transitions and latest-pointer integrity

**Files:**
- Modify: `ai_mapper_agent/run.py`
- Modify: `ai_mapper_agent/guard.py`
- Create: `tests/test_run_finalization.py`
- Modify: `tests/test_final_guard.py`

- [ ] **Step 1: Add failing tests for empty reports, in-progress status, and pointer rules**

```python
def test_guard_rejects_empty_reports_and_in_progress_manifest(self):
    prepare_process_complete_run(run)
    self.assertIn("RUN_NOT_FINALIZED", final_guard(run.path).codes)
    self.assertIn("REPORT_EMPTY", final_guard(run.path).codes)

def test_complete_updates_both_pointers_only_after_guard(self):
    finalize_run(run, status="complete", stop_code="SUCCESS", reason="all gates passed", impact="none")
    self.assertEqual(read_pointer("latest.json"), run.run_id)
    self.assertEqual(read_pointer("latest-complete.json"), run.run_id)

def test_partial_never_moves_latest_complete(self):
    finalize_run(run, status="partial", stop_code="EXA_CREDITS_EXHAUSTED", reason="credits ended", impact="20 queries missing")
    self.assertNotEqual(read_pointer("latest-complete.json"), run.run_id)
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest tests.test_run_finalization tests.test_final_guard -v`

Expected: empty in-progress runs currently pass; no finalization API exists.

- [ ] **Step 3: Implement guarded finalization**

```python
def finalize_run(run: Run, *, status: str, stop_code: str, reason: str, impact: str) -> Run:
    require_nonempty_report_files(run)
    write_manifest_transition(run, status=status, stop_code=stop_code, reason=reason, impact=impact)
    result = final_guard(run.path, expected_status=status)
    if status == "complete" and not result.ok:
        restore_in_progress_manifest(run)
        raise ValueError(result.codes)
    write_latest_pointer(run, "latest.json")
    if status == "complete":
        write_latest_pointer(run, "latest-complete.json")
    return reload_run(run)
```

Final Guard checks manifest/run directory identity, relative artifact paths, required non-empty reports, allowed status, stop fields, latest pointer consistency, and all artifact files/hashes.

- [ ] **Step 4: Run tests and commit**

Run: `python3 -m unittest tests.test_run_finalization tests.test_final_guard -v && python3 -m unittest discover -s tests -v`

Expected: incomplete runs cannot finalize; pointer rules match status.

```bash
git add ai_mapper_agent/run.py ai_mapper_agent/guard.py tests/test_run_finalization.py tests/test_final_guard.py
git commit -m "fix: enforce guarded run finalization"
```

### Task 7: Add the supported CLI and end-to-end fixture workflow

**Files:**
- Create: `ai_mapper_agent/cli.py`
- Create: `ai_mapper_agent/__main__.py`
- Create: `tests/test_cli.py`
- Create: `tests/fixtures/exa-zero-results.json`

- [ ] **Step 1: Add failing CLI tests**

```python
def test_cli_help_lists_supported_workflow_commands(self):
    result = run_cli("--help")
    self.assertEqual(result.returncode, 0)
    for command in ("create", "context-record", "execute-query", "record-browser-fetch", "guard", "finalize"):
        self.assertIn(command, result.stdout)

def test_fixture_workflow_reaches_complete_without_network(self):
    result = run_fixture_workflow(ROOT)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(read_manifest(ROOT)["status"], "complete")
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest tests.test_cli -v`

Expected: `No module named ai_mapper_agent.cli`.

- [ ] **Step 3: Implement argparse command routing**

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-mapper-agent")
    sub = parser.add_subparsers(dest="command", required=True)
    add_create_parser(sub)
    add_context_parser(sub)
    add_execute_query_parser(sub)
    add_browser_fetch_parser(sub)
    add_guard_parser(sub)
    add_finalize_parser(sub)
    return parser
```

Each mutating command resolves the run through its manifest, accepts only run-relative paths, emits compact JSON status, and returns non-zero for blocked or invalid operations. The fixture transport is enabled only by an explicit test-only CLI flag and never by production defaults.

- [ ] **Step 4: Run CLI, integration, and full tests**

Run: `python3 -m unittest tests.test_cli -v && python3 -m ai_mapper_agent --help && python3 -m unittest discover -s tests -v`

Expected: CLI help succeeds and the complete fixture workflow passes without network access.

- [ ] **Step 5: Commit locally**

```bash
git add ai_mapper_agent/cli.py ai_mapper_agent/__main__.py tests/test_cli.py tests/fixtures/exa-zero-results.json
git commit -m "feat: add AI Mapper runtime CLI"
```

### Task 8: Make Codex and Claude installation real and uninstall safe

**Files:**
- Modify: `scripts/install.sh`
- Modify: `scripts/uninstall.sh`
- Create: `.claude/commands/ai-mapper.md`
- Modify: `.claude/agents/ai-mapper.md`
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `tests/test_install_scripts.py`
- Modify: `tests/test_harness_contracts.py`

- [ ] **Step 1: Add failing isolated-install tests**

```python
def test_codex_install_creates_a_discoverable_skill(self):
    run_install("--codex", "--config-root", temp_root)
    self.assertTrue((temp_root / "codex/skills/ai-mapper-agent/SKILL.md").is_file())

def test_claude_install_creates_agent_and_slash_command(self):
    run_install("--claude", "--config-root", temp_root)
    self.assertTrue((temp_root / "claude/agents/ai-mapper.md").is_file())
    self.assertTrue((temp_root / "claude/commands/ai-mapper.md").is_file())

def test_uninstall_rejects_an_unmarked_root(self):
    result = run_uninstall("--root", unrelated_directory, "--yes", "--purge-data")
    self.assertEqual(result.returncode, 2)
    self.assertTrue((unrelated_directory / "runs").exists())
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest tests.test_install_scripts tests.test_harness_contracts -v`

Expected: installer creates only `.ready` files; uninstaller deletes data in an arbitrary directory.

- [ ] **Step 3: Implement isolated, verifiable installation**

```sh
case "$target" in
  codex) install_codex_skill "$config_root/codex/skills/ai-mapper-agent" ;;
  claude) install_claude_files "$config_root/claude" ;;
  both)
    install_codex_skill "$config_root/codex/skills/ai-mapper-agent"
    install_claude_files "$config_root/claude"
    ;;
esac
```

Use symlinks to the repository by default so code and contracts stay in one source of truth. Refuse to overwrite unrelated targets. Continue to print Context Mode installation instructions and never edit global plugin settings automatically.

- [ ] **Step 4: Require a matching marker before destructive uninstall**

```sh
root="$(cd "$root" && pwd -P)"
expected="$(tr -d '\n' < "$root/.ai-mapper-project" 2>/dev/null || true)"
if [ "$expected" != "$root" ] || [ ! -f "$root/SKILL.md" ]; then
  echo "Refusing unverified AI Mapper root: $root" >&2
  exit 2
fi
```

`--purge-data` additionally requires `--confirm-root "$root"`; normal uninstall preserves `runs/` and `.context-mode/`.

- [ ] **Step 5: Add the real Claude command and exact CLI instructions**

```markdown
---
description: Run AI Mapper Agent with an optional topic filter.
argument-hint: "[topic]"
---

Follow the installed AI Mapper Agent contract and use its CLI. Treat `$ARGUMENTS` as the optional topic filter.
```

- [ ] **Step 6: Run isolated installation tests and commit**

Run: `bash -n scripts/install.sh scripts/uninstall.sh && python3 -m unittest tests.test_install_scripts tests.test_harness_contracts -v && python3 -m unittest discover -s tests -v`

Expected: both harnesses become discoverable in temporary config roots; unrelated directories cannot be purged.

```bash
git add scripts/install.sh scripts/uninstall.sh .claude/commands/ai-mapper.md .claude/agents/ai-mapper.md SKILL.md README.md tests/test_install_scripts.py tests/test_harness_contracts.py
git commit -m "fix: install AI Mapper into both harnesses safely"
```

### Task 9: Align documentation and run final verification

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `references/context-mode-contract.md`
- Modify: `references/run-schema-v2.md`
- Modify: `docs/superpowers/plans/2026-08-19-ai-mapper-agent-v2.md`

- [ ] **Step 1: Update contracts to name the real commands and artifacts**

```markdown
The supported mutation path is `python3 -m ai_mapper_agent <command>`.
Execute Exa by `query_id`; the runtime loads the immutable request from `query-plan.jsonl`.
Context Mode is complete only when one structured preflight receipt precedes all research events.
Every successful fetch has a run-relative page file whose hash matches `fetches.jsonl`.
```

- [ ] **Step 2: Run repository hygiene and contract checks**

Run: `rg -n -i 'elsewhere|obsidian' --glob '!docs/superpowers/plans/**' --glob '!tests/test_harness_contracts.py' .`

Expected: no output.

Run: `python3 /Users/lixiaoran/codex/.codex/skills/.system/skill-creator/scripts/quick_validate.py .`

Expected: `Skill is valid!`

- [ ] **Step 3: Run the complete offline verification matrix**

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/install.sh scripts/uninstall.sh
python3 -m ai_mapper_agent --help
git diff --check
```

Expected: zero test failures/warnings, valid shell syntax, CLI exit 0, and no whitespace errors. No command may make a live Exa request.

- [ ] **Step 4: Perform a fresh read-only review**

Review the complete merge-base diff with `$review-agent`. Fix every P0/P1 and rerun Step 3. Record any accepted P2/P3 residual risk in `README.md` before handoff.

- [ ] **Step 5: Commit documentation locally**

```bash
git add SKILL.md README.md references/context-mode-contract.md references/run-schema-v2.md docs/superpowers/plans/2026-08-19-ai-mapper-agent-v2.md
git commit -m "docs: align AI Mapper Agent runtime contract"
```

## Completion Gate

- [ ] The runtime exposes a working CLI and both harness installations are discoverable in isolated config roots.
- [ ] A freehand Exa payload cannot enter the execution path; every attempt records the exact planned request.
- [ ] One structured Context Mode receipt precedes every query/fetch/review event.
- [ ] Fetch 61 is rejected before network access; every success maps to a public URL and hash-matching page file.
- [ ] Every A/B claim maps to candidate- and claim-specific evidence from a successfully fetched source.
- [ ] `complete` requires non-empty reports, complete manifest stop fields, passing Guard, and correct latest pointers.
- [ ] Invalid timezones produce a domain error; duplicate same-second runs remain possible.
- [ ] Destructive uninstall rejects unmarked/mismatched roots.
- [ ] All offline tests, shell checks, Skill validation, CLI help, hygiene scans, and final review pass.
- [ ] No live Exa acceptance test, global configuration mutation, push, or public release occurs in this plan.
