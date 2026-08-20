# AI Mapper Agent v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy skill with a local, harness-native AI Mapper Agent for Codex and Claude Code, with a fixed 40-query Exa research workflow, mandatory Context Mode isolation, durable local artifacts, and deterministic offline validation.

**Architecture:** A dependency-free Python core owns run creation, manifest/state transitions, query-plan generation, response persistence, candidate normalization, evidence records, and Final Guard validation. Thin harness adapters describe how Codex and Claude Code invoke the core; Context Mode calls remain harness tool calls described by the Agent contract rather than hard-coded Python MCP names. Exa and web adapters are injectable so fixture-driven tests run without any live network request.

**Tech Stack:** Python 3.11+ standard library, `unittest`, shell installer, Markdown/YAML/JSONL artifacts.

**Implemented runtime amendment (2026-08-19):** The supported lifecycle interface is `python3 -m ai_mapper_agent <command>`. Exa execution accepts only a saved `query_id` and records request-hashed attempts separately from one final status. One structured Context Mode preflight receipt must precede research events. Successful fetches require a run-relative, hash-matching page file, and the 61st slot is rejected before network access. Finalization requires non-empty reports and updates latest pointers only after Guard passes. Codex and Claude installation now create discoverable harness entries without changing Context Mode or other global plugin settings.

---

## File Structure

- `ai_mapper_agent/contract.py`: version constants, statuses, lane allocation, artifact path rules, typed validation helpers.
- `ai_mapper_agent/plan.py`: exact 40-row query plan (A=10, B=8, C=14, D=8) and query terminal-state validation.
- `ai_mapper_agent/run.py`: create/resume runs, manifests, JSONL event logging, latest pointers, retention cleanup.
- `ai_mapper_agent/evidence.py`: candidate deduplication, evidence-ID creation, raw response and fetched-page persistence.
- `ai_mapper_agent/guard.py`: deterministic Final Guard and human-readable stop reasons.
- `ai_mapper_agent/cli.py`: local command-line entry points for offline operation and harness adapters.
- `scripts/install.sh`, `scripts/uninstall.sh`: local Codex/Claude setup without changing global configuration automatically.
- `SKILL.md`, `agents/openai.yaml`, `.claude/agents/ai-mapper.md`: harness-facing Agent contracts.
- `references/`: only v2 requirements and safety/reference documents; legacy Elsewhere/Obsidian references are removed.
- `tests/`: fixture-only unit and integration tests; no real Exa key or HTTP call.

### Task 1: Add a v2 contract and fixed query plan

**Files:**
- Create: `ai_mapper_agent/__init__.py`
- Create: `ai_mapper_agent/contract.py`
- Create: `ai_mapper_agent/plan.py`
- Create: `tests/test_contract_and_plan.py`

- [ ] **Step 1: Write failing tests for invariant constants and a 40-row plan**

```python
def test_fixed_query_plan_has_exact_lane_allocation():
    rows = build_query_plan(topic=None, run_date=date(2026, 8, 19))
    assert len(rows) == 40
    assert Counter(row["lane"] for row in rows) == {
        "A-dev": 10, "B-content": 8, "C-funding": 14, "D-academic": 8,
    }
    assert {row["query_id"] for row in rows} == {f"q{i:02d}" for i in range(1, 41)}
```

- [ ] **Step 2: Run the contract test to verify it fails because the package is absent**

Run: `python3 -m unittest tests.test_contract_and_plan -v`

Expected: import failure for `ai_mapper_agent`.

- [ ] **Step 3: Implement the smallest contract and deterministic plan**

```python
LANE_BUDGETS = {"A-dev": 10, "B-content": 8, "C-funding": 14, "D-academic": 8}

def build_query_plan(topic: str | None, run_date: date) -> list[dict[str, str]]:
    return [
        {"query_id": f"q{index:02d}", "lane": lane, "query": query, "type": "auto"}
        for index, (lane, query) in enumerate(_fixed_queries(topic, run_date), start=1)
    ]
```

- [ ] **Step 4: Run the contract test and whole suite**

Run: `python3 -m unittest tests.test_contract_and_plan -v && python3 -m unittest discover -s tests -v`

Expected: all tests pass.

### Task 2: Add run manifests, artifact creation, and resume boundaries

**Files:**
- Create: `ai_mapper_agent/run.py`
- Create: `tests/test_run_lifecycle.py`

- [ ] **Step 1: Write failing tests for a new run and same-day resume**

```python
def test_new_run_writes_required_empty_artifacts(tmp_path):
    run = create_run(tmp_path, topic=None, timezone_name="Asia/Shanghai", now=NOW)
    assert run.manifest["status"] == "in_progress"
    assert (run.path / "raw" / "exa-responses.jsonl").is_file()
    assert (run.path / "query-plan.jsonl").is_file()

def test_cross_day_resume_is_rejected(tmp_path):
    run = create_run(tmp_path, topic=None, timezone_name="Asia/Shanghai", now=NOW)
    with pytest.raises(ValueError, match="cross-day"):
        resume_run(tmp_path, run.run_id, now=NOW + timedelta(days=1))
```

- [ ] **Step 2: Run lifecycle tests and verify they fail because the API is absent**

Run: `python3 -m unittest tests.test_run_lifecycle -v`

Expected: import failure for `create_run`.

- [ ] **Step 3: Implement explicit directories, JSONL files, manifest and latest-pointer rules**

```python
REQUIRED_FILES = ("events.jsonl", "query-plan.jsonl", "query-execution.jsonl", "candidates.jsonl", "evidence.jsonl")

def create_run(root: Path, *, topic: str | None, timezone_name: str, now: datetime) -> Run:
    run_path = root / "runs" / run_id_from(now)
    (run_path / "raw").mkdir(parents=True)
    (run_path / "pages").mkdir()
    for relative in REQUIRED_FILES:
        (run_path / relative).touch()
    return _write_manifest(run_path, status="in_progress", topic=topic, timezone_name=timezone_name, now=now)
```

- [ ] **Step 4: Run lifecycle tests and complete suite**

Run: `python3 -m unittest tests.test_run_lifecycle -v && python3 -m unittest discover -s tests -v`

Expected: all tests pass.

### Task 3: Add raw Exa persistence, candidates, evidence, and fetch safety

**Files:**
- Create: `ai_mapper_agent/evidence.py`
- Create: `ai_mapper_agent/web.py`
- Create: `tests/test_evidence_pipeline.py`
- Create: `tests/test_web_safety.py`

- [ ] **Step 1: Write failing tests for response preservation, canonical URL deduplication, evidence linkage, and private-host rejection**

```python
def test_every_exa_result_is_retained_and_duplicate_is_linked(run):
    record_exa_response(run, "q01", {"results": [RESULT, {**RESULT, "url": "https://x.test/a/"}]})
    candidates = read_jsonl(run.path / "candidates.jsonl")
    assert len(candidates) == 2
    assert candidates[1]["duplicate_of"] == candidates[0]["candidate_id"]

def test_fetch_target_rejects_private_networks():
    with self.assertRaisesRegex(ValueError, "private"):
        validate_fetch_url("http://127.0.0.1/admin")
```

- [ ] **Step 2: Run the new tests to verify missing behavior fails**

Run: `python3 -m unittest tests.test_evidence_pipeline tests.test_web_safety -v`

Expected: import failures for persistence and fetch helpers.

- [ ] **Step 3: Implement JSONL audit truth and bounded public-page validation**

```python
def validate_fetch_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only public http(s) URLs are allowed")
    if parsed.hostname in {"localhost", "metadata.google.internal"} or ipaddress.ip_address(parsed.hostname).is_private:
        raise ValueError("private or metadata address is blocked")
    return value
```

- [ ] **Step 4: Run focused and full offline tests**

Run: `python3 -m unittest tests.test_evidence_pipeline tests.test_web_safety -v && python3 -m unittest discover -s tests -v`

Expected: all tests pass without network access.

### Task 4: Add Final Guard and status reporting

**Files:**
- Create: `ai_mapper_agent/guard.py`
- Create: `tests/test_final_guard.py`

- [ ] **Step 1: Write failing tests that reject incomplete query terminals, more than 60 pages, and unlinked A/B claims**

```python
def test_guard_rejects_nonterminal_query(run):
    result = final_guard(run.path)
    assert result.ok is False
    assert "QUERY_NOT_TERMINAL" in result.codes

def test_guard_accepts_zero_candidates_when_process_gates_pass(run):
    complete_all_queries_with_zero_results(run)
    assert final_guard(run.path).ok is True
```

- [ ] **Step 2: Run guard tests to verify they fail because Final Guard is absent**

Run: `python3 -m unittest tests.test_final_guard -v`

Expected: import failure for `final_guard`.

- [ ] **Step 3: Implement deterministic checks and status/stop-reason writes**

```python
def final_guard(run_path: Path) -> GuardResult:
    errors = [*check_plan(run_path), *check_query_terminals(run_path), *check_pages(run_path), *check_evidence(run_path)]
    return GuardResult(ok=not errors, codes=tuple(errors))
```

- [ ] **Step 4: Run guard and full test suites**

Run: `python3 -m unittest tests.test_final_guard -v && python3 -m unittest discover -s tests -v`

Expected: all tests pass.

### Task 5: Replace legacy documentation and add harness adapters

**Files:**
- Modify: `SKILL.md`
- Modify: `agents/openai.yaml`
- Create: `.claude/agents/ai-mapper.md`
- Create: `references/context-mode-contract.md`
- Create: `references/run-schema-v2.md`
- Modify: `README.md`
- Delete: `references/elsewhere-policy.md`
- Delete: `references/run-modes.md`
- Delete: `references/run-modes.json`
- Delete: `assets/screenshots/ai-mapper-output-example.png`
- Delete: `assets/screenshots/ai-mapper-research-workflow.png`
- Delete: `assets/screenshots/ai-mapper-workflow-overview.png`

- [ ] **Step 1: Write static-contract tests for the two harness entries**

```python
def test_harness_contracts_require_context_mode_and_use_same_core_rules():
    for path in (ROOT / "SKILL.md", ROOT / ".claude/agents/ai-mapper.md"):
        text = path.read_text(encoding="utf-8")
        self.assertIn("ctx_doctor", text)
        self.assertIn("40", text)
        self.assertNotIn("Elsewhere", text)
        self.assertNotIn("Obsidian", text)
```

- [ ] **Step 2: Run static-contract tests to verify the legacy skill fails them**

Run: `python3 -m unittest tests.test_harness_contracts -v`

Expected: failure because legacy references remain.

- [ ] **Step 3: Write the harness-neutral contract and thin host adapters**

```markdown
Before any search or fetch, invoke Context Mode's logical `ctx_doctor` tool.
If it is missing, errors, times out, or reports FAIL: write a `blocked` manifest with `CONTEXT_MODE_UNAVAILABLE` and stop.
For a fresh run, set dedicated Context Mode paths, verify the project marker, then invoke `ctx_purge(confirm:true, scope:"project")`.
```

- [ ] **Step 4: Run static-contract and complete offline tests**

Run: `python3 -m unittest tests.test_harness_contracts -v && python3 -m unittest discover -s tests -v`

Expected: all tests pass.

### Task 6: Add installer, uninstaller, and isolated installation verification

**Files:**
- Create: `scripts/install.sh`
- Create: `scripts/uninstall.sh`
- Create: `tests/test_install_scripts.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write failing tests for usage validation, no-global default behavior, and data-preserving uninstall**

```python
def test_uninstall_preserves_runs_without_explicit_purge(tmp_path):
    runs = tmp_path / "runs" / "sample"
    runs.mkdir(parents=True)
    result = run_script("scripts/uninstall.sh", "--root", str(tmp_path), "--yes")
    self.assertEqual(result.returncode, 0)
    self.assertTrue(runs.exists())
```

- [ ] **Step 2: Run installer tests to verify missing scripts fail**

Run: `python3 -m unittest tests.test_install_scripts -v`

Expected: failure because scripts do not exist.

- [ ] **Step 3: Implement safe local installation and explicit destructive-data confirmation**

```sh
case "$target" in codex|claude|both) ;; *) usage; exit 2 ;; esac
if ! command -v python3 >/dev/null; then echo "Python 3 is required" >&2; exit 1; fi
echo "Install Context Mode separately; AI Mapper refuses to run without ctx_doctor."
```

- [ ] **Step 4: Run script tests, shell syntax checks, and full suite**

Run: `bash -n scripts/install.sh scripts/uninstall.sh && python3 -m unittest tests.test_install_scripts -v && python3 -m unittest discover -s tests -v`

Expected: all tests pass.

### Task 7: Remove legacy implementation and run release-quality checks

**Files:**
- Delete: `scripts/build_exa_query_plan.py`
- Delete: `scripts/forced_pipeline.py`
- Delete: `scripts/preflight.py`
- Delete: `scripts/validate_run.py`
- Delete: `tests/test_forced_pipeline.py`
- Delete: `tests/test_query_plan.py`
- Delete: `tests/test_validate_run.py`
- Modify: `.gitignore`

- [ ] **Step 1: Replace legacy tests with the v2 test suite before deletion**

```python
def test_repository_has_no_elsewhere_or_obsidian_runtime_reference():
    matches = search_repository_for(("Elsewhere", "Obsidian"))
    self.assertEqual(matches, [])
```

- [ ] **Step 2: Run the test and verify legacy source causes the intended failure**

Run: `python3 -m unittest tests.test_harness_contracts.HygieneTests.test_repository_has_no_elsewhere_or_obsidian_runtime_reference -v`

Expected: failure listing legacy files.

- [ ] **Step 3: Delete legacy runtime/source artifacts and keep only v2 paths**

```text
Retain raw Git history; remove legacy working-tree source, policy, tests, and screenshots.
Never delete `runs/` as part of an upgrade.
```

- [ ] **Step 4: Verify the finished repository offline**

Run: `python3 -m unittest discover -s tests -v && rg -n -i 'elsewhere|obsidian' --glob '!docs/superpowers/plans/**' . && git status --short`

Expected: all tests pass; the source tree contains no legacy runtime reference; planned historic wording is exempt.

## Final Verification

- [ ] Run all offline tests: `python3 -m unittest discover -s tests -v`.
- [ ] Run shell validation: `bash -n scripts/install.sh scripts/uninstall.sh`.
- [ ] Run static hygiene: `rg -n -i 'elsewhere|obsidian' --glob '!docs/superpowers/plans/**' .`.
- [ ] Verify no secret file is tracked: `git ls-files | rg '(^|/)\\.env($|\\.)|context-mode|runs/'`.
- [ ] Verify no live Exa call was made during tests by using only fixture payloads.
- [ ] Do not publish or push: the upstream repository has no redistribution license/authorization.
