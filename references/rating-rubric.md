# AI Mapper Candidate Rating Rubric

Use this rubric before writing `candidates.jsonl`, `candidate-cards.md`, or the final report. It is the single source of truth for review decisions.

## Project-first review

Rate the project first. A missing person, background, or contact field is a follow-up gap, not an automatic rejection. Every A/B row must still state which public source families were checked and what remains unresolved.

## Required A/B gates

An A or B project must be China-relevant or explicitly relevant to the requested topic, be an AI software project or a projectized paper/repo/demo/model, and have a concrete source-backed recent action. The action should fall inside the run's 30-day window unless the row explains a specific reason to retain an older signal.

A project also needs a concrete product, repository, company, paper-system, demo, model, dataset, funding, customer, or deployment signal. A generic directory listing, ranking page, or unattributed social mention is not sufficient on its own.

## Ratings

| Rating | Meaning |
|---|---|
| `A` | Immediate attention: scope, early-stage relevance, recent action, strong original evidence, and a concrete reason to care now are all supported. |
| `B` | Relevant lead for follow-up: one or more of background, contact, freshness, funding, evidence, why-now, project signal, customer proof, or person-project relation needs a concrete next check. |
| `C` | Useful context but mature, stale, broad, weakly aligned, or not strong enough for immediate follow-up. |
| `暂不跟进` | Public evidence is insufficient, inaccessible, unverifiable, out of scope, or only a generic directory/community signal. |

## A-class evidence floor

If an A row relies on one media or report page, public enrichment must verify at least one stronger original source: product or company site, GitHub or release, model/demo page, investor announcement, team profile, customer/deployment proof, or equivalent first-party artifact. Otherwise cap the row at B.

## Allowed gap values

Use one or more of these exact values in `gap_type` and follow-up notes: `Background`, `Contact`, `Freshness`, `Funding`, `Evidence`, `Why now`, `Project signal`, `Customer/user proof`, `Person-project relation`, `Date verification`, `Public evidence`.

## Candidate JSONL review shape

Every unique candidate must be rewritten with `review_status: "reviewed"` and one allowed `rating`. A/B rows must include non-empty `claims`; each claim must contain `claim_id`, `text`, and one or more `evidence_ids`. Each linked evidence record must repeat the exact claim text and point to a successful run-local page.

## Academic projects

Do not create a separate academic-only talent table. Include an academic result only when it has a projectized artifact or a credible path to AI software use; record paper, venue, repository/demo/model, author or lab relation, and productization context in the same project workflow.
