# AI Mapper Evals

Use this to check whether the `ai-mapper` skill should load and whether its output stays within contract.

## Positive Examples (Skill SHOULD Load)

### 1. Direct slash command
**Input**: "/ai-mapper"
**Expected**: Load. User explicitly invokes the skill.

### 2. AI mapping request
**Input**: "帮我扫一下最近中文 AI 创业项目"
**Expected**: Load. User asks for AI mapping of Chinese projects.

### 3. Talent lead mapping
**Input**: "map AI talent leads in China this week"
**Expected**: Load. User asks for AI talent mapping.

### 4. Obsidian artifact request
**Input**: "把最近看到的 AI Agent 和 MCP 项目整理成 Obsidian 报告"
**Expected**: Load. User wants an Obsidian research artifact for AI projects.

### 5. Founder/startup discovery
**Input**: "有哪些早期中国 AI 开源项目的创始人值得关注"
**Expected**: Load. User asks for early Chinese AI open-source founders.

### 6. Funding scan
**Input**: "最近 30 天国内 AI 融资项目"
**Expected**: Load. User asks for recent China AI funding projects.

## Negative Examples (Skill Should NOT Load)

### 7. General AI question
**Input**: "什么是 MCP？"
**Expected**: Skip. Conceptual question, no mapping or artifact intent.

### 8. Specific company research
**Input**: "帮我查一下 OpenAI 最新动态"
**Expected**: Skip. User wants research on one known entity, not a market map.

### 9. Code review
**Input**: "review 这段 Python 代码"
**Expected**: Skip. General coding task, no AI mapping intent.

### 10. Request to read existing artifact
**Input**: "打开我的 AI-Mapping Obsidian vault"
**Expected**: Skip. User wants file navigation, not a new mapping run.

### 11. Non-Chinese market request
**Input**: "map all US AI startups"
**Expected**: Skip. Out of scope for China-relevant AI mapping.

### 12. Recruitment task
**Input**: "帮我找 10 个 AI 工程师简历"
**Expected**: Skip. Recruitment/job-board paths are banned; not the skill's purpose.

## Known Failure Cases

### F1. "AI 项目" without mapping intent
**Input**: "推荐几个好用的 AI 项目"
**Expected**: May load if "项目" + "AI" is interpreted as mapping; should only load if user wants source-backed market mapping into Obsidian.
**Risk**: False positive on generic product recommendations.

### F2. Directional hint narrows scan
**Input**: "/ai-mapper 重点看 AI 客服"
**Expected**: Should load but keep `TOPIC=通用扫描`; treat AI 客服 as an emphasis inside the generic scan, not a narrowed topic.
**Risk**: Agent may incorrectly narrow the scan and skip other lanes.

### F3. Subagent asked for recall
**Input**: "用四个子代理并行跑 A/B/C/D 车道"
**Expected**: Should load but refuse to use subagents for front-stage recall. Subagents are allowed only after Exa Candidate Queue exists and only if user explicitly asks for parallel lane processing.
**Risk**: Agent may spawn subagents too early, violating the forced no-subagent pipeline.

### F4. Elsewhere unavailable
**Input**: "/ai-mapper" (no Elsewhere key configured)
**Expected**: Should load, run Exa + public sources as `degraded / Exa-only`, write standard paths, and not mark run `complete`.
**Risk**: Agent may either skip Elsewhere entirely without recording degradation or halt the run.

### F5. Under-minimum counts
**Input**: "/ai-mapper" (guard-final reports gates below minimum while Exa is available)
**Expected**: Should continue recall/opening, not write final/latest or call run `blocked`.
**Risk**: Agent may treat under-minimum as a stopping state and deliver incomplete artifacts.
