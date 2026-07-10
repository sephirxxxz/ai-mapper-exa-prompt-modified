# AI Mapper Source Families

Use this when counting Source Coverage Gate and writing 来源质量复盘. A source family is a distinct origin class, not a single URL count.

## Allowed Source Families

| Family | Count when | Notes |
|---|---|---|
| Elsewhere API | Elsewhere keyword/discovery/financing/enrichment returns usable chunks/entities/content | Mandatory for complete runs; unavailable runs mark degraded |
| GitHub | Repo, release, issue, discussion, maintainer profile, or trending page is openable | Radar must be backtraced to repo/release evidence |
| Product Hunt | Launch page is openable | Radar only unless backtraced to product/source evidence |
| Hugging Face | Model/space/dataset page is openable | Radar/model evidence when tied to project |
| arXiv/OpenReview/Semantic Scholar/OpenAlex | Paper/profile/proceedings page is openable | Academic leads must be projectized |
| Papers With Code / ACL / CVF / NeurIPS / ICLR / ICML | Benchmark/paper/project page is openable | Count separately from generic academic search when used |
| Product/company site | Product docs, pricing, customer, demo, about/team, changelog, or blog page is openable | Static homepage alone is weak |
| 36氪 | Funding/startup article is openable | Funding/media family |
| 投资界 | Funding/startup article is openable | Funding/media family |
| 创业邦 | Funding/startup article is openable | Funding/media family |
| 猎云网 | Funding/startup article is openable | Funding/media family |
| 亿欧 | Funding/startup article is openable | Funding/media family |
| 雷峰网 | Product/funding/technical article is openable | Media family |
| 新智元 | Product/research/company article is openable | Media family |
| 量子位 | Product/research/company article is openable | Media family |
| 机器之心 | Product/research/company article is openable | Media family |
| InfoQ | Technical/company article is openable | Media family |
| DoNews | Company/product/funding article is openable | Media family |
| TechNode / KrASIA | Company/product/funding article is openable | Media family |
| Investor/VC newsroom or portfolio | Investor page verifies financing/portfolio/company relation | Count by investor/VC source family class unless many distinct VC pages are material |
| Accelerator/demo-day/event pages | Public event/demo/roadshow page verifies participant/current action | Event family |

## Banned Or Non-Counting Families

Do not count closed/account-only/paywall/CAPTCHA sources, recruitment/job-board pages, broad ranking databases, generic AI tool directories, generic community feeds outside the allowlist, Exa snippets, context-mode snippets, or private browser/app state.

If queried but no usable openable candidate appears, record `queried/no usable result` in run-report instead of counting it as usable coverage.
