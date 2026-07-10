from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
VALIDATE_RUN = SKILL_DIR / "scripts" / "validate_run.py"
PREFLIGHT = SKILL_DIR / "scripts" / "preflight.py"


def load_validate_run():
    spec = importlib.util.spec_from_file_location("validate_run", VALIDATE_RUN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PROJECT_HEADER = (
    "| 项目名 | 一句话描述 | AI 软件细分方向 | 产品形态 | 项目背景与证据 | 融资状态 | "
    "关联人才与背景 | 下一步补全项 | 评级 | 来源链接 | 采集日期 | 最近有效动态日期 |"
)
TALENT_HEADER = "| 姓名/昵称 | 关联公司/项目 | 最近动作 | 身份 | 背景 | 评级 |"
RAW_HEADER = (
    "| 名称 | 入口类型 | 类型 | 一句话描述 | 赛道 | 找谁 | 为什么找 | 怎么找 | 找了之后问什么 | "
    "最近动态 | 主证据链接 | 补充证据链接 | 联系入口 | 证据等级 | 备注 |"
)
QUEUE_HEADER = "| Exa query | Candidate URL | Why it might matter | Opened/fetched? | Keep/drop reason |"


def write_bad_workspace(workspace: Path) -> None:
    (workspace / "results").mkdir(parents=True)
    for lane in ("A-dev", "B-content", "C-funding", "D-academic"):
        (workspace / "results" / f"{lane}.md").write_text(
            f"""# {lane}

## Exa Candidate Queue
{QUEUE_HEADER}
| q | https://example.com/{lane} | fake | no | not_selected |

{RAW_HEADER}
| 假项目 | project | AI | fake | fake | 未知 | because | nowhere | nothing | source_page_date none; true_event_date none | https://example.com | | | S | 搜索次数: 1 |

搜索次数: 1
""",
            encoding="utf-8",
        )

    (workspace / "topic.md").write_text("# topic\nTOPIC=通用扫描\n", encoding="utf-8")
    (workspace / "topics.md").write_text("# topics\n## Elsewhere Keyword Intelligence\nnone\n", encoding="utf-8")
    research_axes = {
        "schema_version": "1.0",
        "topic": "通用扫描",
        "objective": "发现中国相关早期 AI 软件项目与人才",
        "collection_date": "2026-07-07",
        "priority_window": {"start": "2026-06-07", "end": "2026-07-07"},
        "axes": [
            {
                "axis_id": "developer-product",
                "axis_type": "base",
                "base_role": "developer-product",
                "label": "开发者与产品发布",
                "ranking_question": "Find early China-relevant AI software releases with original evidence.",
                "search_seed": "中国 AI 软件 产品 发布",
                "candidate_types": ["project", "repo"],
                "evidence_targets": ["true event date", "repo"],
                "lane_affinity": ["A-dev"],
                "weight": 1.0,
                "exclusions": ["招聘信息"],
            },
            {
                "axis_id": "product-market",
                "axis_type": "base",
                "base_role": "product-market",
                "label": "产品与市场验证",
                "ranking_question": "Find early China-relevant AI software with customer or deployment proof.",
                "search_seed": "中国 AI 软件 客户 部署",
                "candidate_types": ["project", "company"],
                "evidence_targets": ["customer proof", "deployment"],
                "lane_affinity": ["B-content"],
                "weight": 0.9,
                "exclusions": ["招聘信息"],
            },
            {
                "axis_id": "funding-company",
                "axis_type": "base",
                "base_role": "funding-company",
                "label": "早期融资与公司事件",
                "ranking_question": "Find early China-relevant AI software funding events with original evidence.",
                "search_seed": "中国 AI 软件 融资 天使轮 种子轮",
                "candidate_types": ["company", "founder"],
                "evidence_targets": ["funding round", "investor"],
                "lane_affinity": ["C-funding"],
                "weight": 1.0,
                "exclusions": ["招聘信息"],
            },
            {
                "axis_id": "academic-productization",
                "axis_type": "base",
                "base_role": "academic-productization",
                "label": "学术产品化与人才",
                "ranking_question": "Find China-relevant AI papers converted into repos, demos, or products.",
                "search_seed": "中国 AI 论文 系统 repo demo 产品化",
                "candidate_types": ["paper", "repo", "project"],
                "evidence_targets": ["paper date", "repo or demo"],
                "lane_affinity": ["D-academic"],
                "weight": 0.8,
                "exclusions": ["招聘信息"],
            },
        ],
    }
    (workspace / "research-axes.json").write_text(
        json.dumps(research_axes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    query_plan = {
        "schema_version": "1.0",
        "plan_id": "exa-plan-2026-07-07-adaptive-standard-scan",
        "query_id": "q-0001",
        "axis_id": "developer-product",
        "lane": "A-dev",
        "source_family": "GitHub",
        "exa_query": "site:github.com 中国 AI 软件 发布 2026 07",
        "ranking_question": "Find early China-relevant AI software releases with original evidence.",
        "candidate_types": ["project", "repo"],
        "evidence_targets": ["true event date", "repo"],
        "priority": 1.0,
        "run_mode": "adaptive standard scan",
        "collection_date": "2026-07-07",
        "priority_window_start": "2026-06-07",
        "priority_window_end": "2026-07-07",
        "execution_status": "planned",
    }
    (workspace / "exa-query-plan.jsonl").write_text(
        json.dumps(query_plan, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    query_execution = {
        "schema_version": "1.0",
        "plan_id": query_plan["plan_id"],
        "query_id": "q-0001",
        "axis_id": "developer-product",
        "lane": "A-dev",
        "source_family": "GitHub",
        "exa_query": query_plan["exa_query"],
        "status": "completed",
        "result_count": 160,
        "collection_date": "2026-07-07",
    }
    (workspace / "exa-query-execution.jsonl").write_text(
        json.dumps(query_execution, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (workspace / "validated.md").write_text(
        "# validated\nElsewhere API discovery/supplement\nsource_origin=Elsewhere API\n人才类线索: x\n",
        encoding="utf-8",
    )
    (workspace / "rated.md").write_text(
        f"""# rated
{PROJECT_HEADER}
| 假项目 | 假 | Agent | 网站 | 没有证据但格式齐 | 未公开披露 | 未知 | 待补 | A / 重点关注 | https://example.com | 2026-07-07 | 2026-07-07 |

{TALENT_HEADER}
| 张三 | 假项目 | 不存在 | 创始人 | 无 | A / 重点关注 |
""",
        encoding="utf-8",
    )
    (workspace / "AI项目与人才Mapping.md").write_text(
        f"""## 运行状态
- run_mode: adaptive standard scan
- 完整性状态: complete
- Elsewhere 状态: available
- Exa 状态: available
- 停止原因: reached_target

{PROJECT_HEADER}
| 假项目 | 假 | Agent | 网站 | 没有证据但格式齐 | 未公开披露 | 未知 | 待补 | A / 重点关注 | https://example.com | 2026-07-07 | 2026-07-07 |

{TALENT_HEADER}
| 张三 | 假项目 | 不存在 | 创始人 | 无 | A / 重点关注 |

## 来源质量复盘
""",
        encoding="utf-8",
    )

    exa_rows = []
    for i in range(160):
        exa_rows.append(
            {
                "record_id": f"r{i}",
                "plan_id": query_plan["plan_id"],
                "query_id": "q-0001",
                "axis_id": "developer-product",
                "lane": "A-dev",
                "exa_query": "q",
                "query_batch_id": "b",
                "source_family_planned": "GitHub",
                "returned_rank": i,
                "url": "https://example.com/duplicate",
                "normalized_url": "https://example.com/duplicate",
                "domain": "example.com",
                "title": "same",
                "source_type_hint": "unknown",
                "source_family_hint": "garbage-family",
                "entry_type_hint": "project",
                "possible_signal": "fake",
                "risk_reason": "none",
                "entity_cluster_id": "same-cluster",
                "must_open_reason": "none",
                "review_decision": "not_selected",
                "exa_returned_date": "not-a-date",
                "exa_published_date": "not-a-date",
                "exa_crawl_date": "not-a-date",
                "highlight_or_snippet": "exa snippet treated as truth",
                "why_it_might_matter": "because",
                "collection_date": "not-a-date",
                "run_mode": "adaptive standard scan",
                "selected_for_review": False,
                "fetch_status": "banana",
                "keep_drop_status": "kept",
                "keep_drop_reason": "",
                "candidate_id": "c1",
            }
        )
    (workspace / "exa-candidates.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in exa_rows) + "\n",
        encoding="utf-8",
    )
    (workspace / "candidates.jsonl").write_text(
        json.dumps(
            {
                "candidate_id": "c1",
                "name": "假项目",
                "entry_type": "project",
                "lane": "A-dev",
                "source_origin": "Exa",
                "run_mode": "adaptive standard scan",
                "status": "rated",
                "rating": "A / 重点关注",
                "gap_type": "",
                "evidence_ids": ["missing-evidence-id"],
                "notes": "fake",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace / "evidence.jsonl").write_text(
        json.dumps(
            {
                "evidence_id": "e1",
                "candidate_id": "someone-else",
                "url": "https://example.com",
                "source_family": "forbidden-garbage",
                "source_type": "exa_snippet",
                "evidence_level": "S",
                "claim_supported": "everything",
                "source_page_date": "bad",
                "true_event_date": "bad",
                "exa_returned_date": "bad",
                "collection_date": "bad",
                "date_decision": "use exa date",
                "openable_status": "opened",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    gates = [
        ("Total Exa query/source paths", 36),
        ("Total Exa candidate URLs", 160),
        ("Total opened/fetched original pages", 50),
        ("Total raw P0/P1 leads", 30),
        ("C-funding query/source paths", 12),
        ("C-funding candidate URLs", 70),
        ("C-funding opened/fetched pages", 18),
        ("C-funding raw financing/startup leads", 10),
        ("Source families", 10),
        ("C-funding source families", 6),
        ("Elsewhere financing/startup candidate facts", 5),
    ]
    gate_table = "| Gate | Required | Actual | Pass? | Notes |\n|---|---:|---:|---|---|\n"
    gate_table += "\n".join(f"| {gate} | {minimum} | {minimum} | PASS | fabricated |" for gate, minimum in gates)
    (workspace / "run-report.md").write_text(
        """# run report
run_mode: adaptive standard scan
Elsewhere API 使用质量
Exa 召回质量
A 类项目审计
真实日期审计
Recall Volume Gate
Exa Search Quantity Gate
Source Coverage Gate
Elsewhere Financing Pass
Exa candidate audit
Exa triage/open audit
marginal-yield

"""
        + gate_table
        + "\n",
        encoding="utf-8",
    )


class ValidateRunTests(unittest.TestCase):
    def test_validate_workspace_rejects_fabricated_audit_trail(self) -> None:
        module = load_validate_run()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "bad-workspace"
            write_bad_workspace(workspace)

            errors = module.validate_workspace(workspace, SKILL_DIR)

        joined = "\n".join(errors)
        self.assertIn("duplicate normalized_url", joined)
        self.assertIn("fetch_status", joined)
        self.assertIn("invalid date", joined)
        self.assertIn("missing evidence ids", joined)
        self.assertIn("evidence candidate_id", joined)
        self.assertIn("source_type", joined)

    def test_preflight_skip_network_is_not_complete_candidate(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(PREFLIGHT),
                "--skip-network",
                "--exa-status",
                "available",
                "--context-mode-status",
                "available",
            ],
            check=True,
            text=True,
            capture_output=True,
            env={**os.environ, "ELSEWHERE_KEY": "els_live_test_key"},
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["elsewhere"]["status"], "key_present_not_checked")
        self.assertEqual(payload["completeness_preflight"], "preflight_pending")

    def test_validate_query_artifacts_rejects_unknown_axis_and_missing_execution(self) -> None:
        module = load_validate_run()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "bad-query-links"
            write_bad_workspace(workspace)
            plan = json.loads(
                (workspace / "exa-query-plan.jsonl").read_text(encoding="utf-8")
            )
            plan["axis_id"] = "unknown-axis"
            (workspace / "exa-query-plan.jsonl").write_text(
                json.dumps(plan, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            (workspace / "exa-query-execution.jsonl").write_text(
                "",
                encoding="utf-8",
            )

            errors = module.validate_workspace(workspace, SKILL_DIR)

        joined = "\n".join(errors)
        self.assertIn("references unknown axis", joined)
        self.assertIn("planned queries not executed", joined)

    def test_validate_query_artifacts_rejects_freehand_candidate(self) -> None:
        module = load_validate_run()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "freehand-query"
            write_bad_workspace(workspace)
            rows = [
                json.loads(line)
                for line in (workspace / "exa-candidates.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            rows[0]["query_id"] = ""
            (workspace / "exa-candidates.jsonl").write_text(
                "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
                + "\n",
                encoding="utf-8",
            )

            errors = module.validate_workspace(workspace, SKILL_DIR)

        self.assertIn(
            "exa-candidates.jsonl: unknown query_id <empty>",
            "\n".join(errors),
        )

    def test_validate_query_artifacts_accepts_blocked_status_records(self) -> None:
        module = load_validate_run()
        status = {
            "record_type": "status",
            "status": "blocked",
            "run_mode": "blocked",
            "blocker_reason": "Exa unavailable",
            "collection_date": "2026-07-09",
            "notes": "Planning and recall did not run.",
        }
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "research-axes.json").write_text(
                json.dumps(status, ensure_ascii=False),
                encoding="utf-8",
            )
            for name in ("exa-query-plan.jsonl", "exa-query-execution.jsonl"):
                (workspace / name).write_text(
                    json.dumps(status, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
            errors: list[str] = []

            module.validate_query_artifacts(workspace, [], errors)

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
