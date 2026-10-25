# SNOWY

**S.N.O.W.Y.** — *Simulacrum Noematum Operandi Vindex Ypothesis*

> Open-core multi-agent assistant: FastAPI gateway, 7-step pipeline, flat tool registry, React/Vite UI, serverless on AWS for near-zero cost. A hosted, paid edition is developed separately.

> **Coordinated Autonomous Background Learning Execution System — Multi Agent Network**
> *v1 · CABLES MAN Architecture*

SNOWY is a multi-agent AI assistant framework built on top of free-tier infrastructure. It combines adaptive identity modeling, emotional intelligence, semantic memory, a 7-stage execution pipeline, and a flat tool registry into a single coherent system — designed to run in production on close to zero budget, on AWS. See **[docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md)** for the full deployment guide and cost breakdown.

The design combines prompt-cache management, sub-agent delegation, gated tool execution, the Nature Scientific Reports 2026 ensemble emotional intelligence research, and Big Five personality psychology (OCEAN model). Every design decision prioritizes permanent memory, zero deletion, and a system that learns specifically who *you* are. SNOWY runs entirely on open-weight models (Qwen, GPT-OSS) via Groq — it never claims to be Claude, GPT, or any other vendor's model.


> **Power switch:** set the GitHub variable `SNOWY_ENABLED` to `false` and run the deploy to stop everything: chat and all tabs return 503 and the 15-minute tick is disabled (unset or `true` = on). There is also a header toggle for a softer off (`GET/PUT /power`); it cannot override the GitHub variable. History, login and /health keep working while off.

---

## Architecture Overview

```
INTERFACE (React UI + Voice)
        ↓
   FastAPI GATEWAY
        ↓
 ┌──────────────────────────────────────────────────┐
 │              7-STEP PIPELINE                     │
 │  Bootstrap → CTX Assembly → Memory Load →        │
 │  Query Engine → Tool Exec → CTX Pressure →       │
 │  Sub-Agent Delegation                            │
 └──────────────────────────────────────────────────┘
        ↓
 ┌────────────────────────────────────────────┐
 │           CACHE LAYER                      │
 │  SYS CACHE · CONV CACHE · CACHE CTRL       │
 └────────────────────────────────────────────┘
        ↓
 ┌────────────────────────────────────────────┐
 │         CABLES MAN CORE                    │
 │        TAU · NATURE SCI · PACIFIC          │
 └────────────────────────────────────────────┘
        ↓
 ┌────────────────────────────────────────────────────────────────┐
 │                        AGENTS                                  │
 │  PULSE · DEEPPLAN · ORCHESTRATOR · CONSOLIDATOR · OUTREACH ...   │
 └────────────────────────────────────────────────────────────────┘
        ↓
 ┌──────────────────────────────────────────────────────────────────┐
 │                     TOOLS REGISTRY (flat)                        │
 │  MCP · AgentTool · BashTool · ArtifactTool                       │
 │  Web: SerpAPI · WebFetch · NewsTool                              │
 │  Misc: Calendar · WhatsApp                                       │
 └──────────────────────────────────────────────────────────────────┘
        ↓
 ┌──────────────────────────────────┐
 │        STORAGE LAYER             │
 │  Neon Postgres + pgvector        │
 └──────────────────────────────────┘
```

---

## Research Foundations

### NATURE SCI — emotion

Each message is read by an open-source emotion classifier (DistilRoBERTa,
`j-hartmann/emotion-english-distilroberta-base`: anger, disgust, fear, joy,
neutral, sadness, surprise) running on the same Modal app as the embeddings.
A confident, non-neutral reading adds one tone line to that turn's context
("the user sounds frustrated — get straight to a fix"). Without Modal, a small
word list stands in. CONSOLIDATOR uses emotional intensity when scoring memories.
The design draws on the 2026 Nature Scientific Reports ensemble work; the
multimodal parts (facial expression, generation) aren't built.

### Big Five OCEAN Model — PACIFIC

PACIFIC (Preference Alignment Choices Inference for Five-factor Identity
Characterization) infers Big Five traits from implicit signals rather than a
questionnaire. Once a day the scheduled tick has a free model read recent
messages across every conversation and saves OCEAN scores plus an observed
answer style ("short answers, code first") to the owner's profile; every chat
reads that saved profile. A keyword estimate covers the time before the first
daily read.

---

## Layer Breakdown

### Interface
| Component | Description |
|-----------|-------------|
| **SNOWY UI** | React frontend. Chat, voice, status, real-time agent activity feed. |
| **VOICE INPUT** | Microphone + screen awareness. Sensory layer bridging physical world into Snowy. |

### Gateway
| Component | Description |
|-----------|-------------|
| **FastAPI GATEWAY** | Single HTTP entry point. Auth, task queuing. Deployed on AWS Lambda behind a Function URL. |

### TAU Layer — Adaptive Identity Engine
TAU is a completely separate autonomous layer that runs in parallel to the main pipeline. Its sole purpose is to observe, learn, and build a model of *you specifically* — not a generic user profile.

| Component | Description |
|-----------|-------------|
| **TAU** | Orchestrates the identity engine. Feeds context into CABLES MAN every turn. |
| **USER MODEL** | Structured profile: habits, preferences, schedule, goals. Refined by CONSOLIDATOR. |
| **MEMORY** | Long-term memory across all sessions. Stored in Neon Postgres. Never deleted. |
| **IDENTITY** | Consistent personality and self-model. Stable across sessions. |
| **PACIFIC** | Big Five OCEAN engine. Infers personality from implicit signals. |
| **TAU CACHE** | 1hr profile TTL + rolling EMU cache. Prevents re-inference every turn. |

### 7-Step Pipeline
Every request passes through these 7 stages in order:

**Step 1 — BOOTSTRAP**
7-stage initialization: Prefetch → Safety → CLI parse + trust gate → Tool loading → Deferred init → Mode routing → Query engine handoff.

**Step 2 — CTX ASSEMBLY**
Loads `SNOWY.md` configuration hierarchy: `global → user → project → local`. Applied every turn. 40k character limit enforced.

**Step 3 — MEMORY LOAD**
Delegates semantic lookup to SEM RETRIEVAL (pgvector cosine search). Raw record fetch via Neon Postgres. Topic index kept as fallback. Transcripts are grepped rather than fully loaded. Retrieval scope is infinite — everything ever stored is retained.

**Step 3b — SEM RETRIEVAL**
Semantic Memory Retrieval engine. Queries pgvector by cosine similarity. Returns top-K memories ranked by semantic closeness to the current query. Replaces legacy topic-pointer lookup entirely.

**Step 4 — QUERY ENGINE**
All LLM calls, streaming, and caching. Tracks cache-break events (tool changes, model switches, image additions, system prompt edits). `REASONING_BUFFER` holds reasoning between tool calls and returns a compact summary. Feeds Cache Layer before every API call.

**Step 5 — TOOL EXECUTION**
3 trust levels (per tool, with a global override):
- **Trusted** — no confirmation; set for calls carrying the owner's API key
- **Confirm Writes** — write operations return a confirmation request first
- **Open** — read-only or low-risk tools run immediately

**Step 6 — CTX PRESSURE**
5 compaction strategies applied in escalating severity:
1. Budgeting
2. Microcompact
3. Collapse
4. Autocompact
5. Prune + Index

13k buffer, 20k summary target, 3-failure circuit breaker.

**Step 7 — SUB-AGENT DELEGATION**
3 execution models:
- **Fork** — cache-optimized parallel execution
- **Teammate** — file mailbox coordination
- **Worktree** — isolated git branch execution

### Cache Layer
All LLM API calls are intercepted by the Cache Layer before hitting the external API.

| Component | Details |
|-----------|---------|
| **SYS CACHE** | Caches `SNOWY.md` system prompt + TOOLS registry. Write = 1.25× cost (5-min TTL) or 2× (1-hr TTL). Read = 0.10× cost. KV in-memory only. |
| **CONV CACHE** | Rolling conversation cache. Auto-advances breakpoint as conversation grows. Up to 4 breakpoints per request, 20-block lookback. |
| **CACHE CTRL** | Cryptographic prefix hash as cache key. Tracks cache-break events. Manages TTL refresh. Cache miss triggers fresh write at 1.25× cost. |
| **TAU CACHE** | Dedicated identity cache. Stores PACIFIC OCEAN traits, EMUs, personality snapshots, CONSOLIDATOR results. |

### CABLES MAN Core — Multi-Agent Orchestration
CABLES MAN is pure orchestration — zero direct API calls. All external access goes through TOOLS.

| Component | Description |
|-----------|-------------|
| **CABLES MAN** | Coordinated Autonomous Background Learning Execution System. Routes tasks to agents. |
| **NATURE SCI** | Open-source emotion classifier on each message; steers the reply's tone. |
| **SALIENCE ENGINE** | Scores every memory candidate before persistence. Combines EMU weights + surprise delta from Query Engine. High salience = encoded to Neon (row + embedding) first. Nothing deleted — salience controls priority only. |
| **WORKING MEM** | Cross-turn scratchpad. Persists active reasoning across multiple turns on the same problem. Cleared only when the problem is resolved. |

### Agents
All agents are spawned by CABLES MAN and interact exclusively through the TOOLS registry.

| Agent | Description |
|-------|-------------|
| **PULSE** | Scheduled tick (every 15 minutes via EventBridge, or a loop on an always-on box). Delivers due reminders and the daily morning brief, then runs automations. Audit-logged. |
| **DEEPPLAN** | Deep-planning agent: one long, bounded call on GPT-OSS-120B (Groq) for goals that need more reasoning than the quick PLAN agent. |
| **ORCHESTRATOR** | Fans a list of subtasks out to parallel workers and merges their results. Shared scratchpad. |
| **CONSOLIDATOR** | Memory maintenance. Runs once 24 hours and 5 new sessions have passed. Survey → Load → Score → Reindex: scores every memory via SALIENCE ENGINE and refreshes embeddings in Neon (pgvector). Nothing pruned. |
| **OUTREACH** | Stores reminders and sends messages for PULSE to deliver: alerts, suggestions, reminders without being asked. |
| **EXPLORE** | Fast knowledge/codebase search subagent. Spawned via AgentTool. |
| **PLAN AGENT** | Designs strategy before any action. Prevents sloppy execution. |
| **GENERAL AGENT** | Handles complex multi-step tasks end-to-end. Workhorse of CABLES MAN. |
| **GUIDE AGENT** | Self-knowledge agent. Answers questions about Snowy's own capabilities and current state. |
| **WORKER_POOL** | Parallel workers with per-task context isolation (contextvars), so concurrent tasks don't bleed into each other. |
| **AGENT INBOX** | Agent-to-agent messaging. Planned, not built. |
| **BRIDGE** | Remote commands from a phone or another app (OpenClaw, MCP): run a query or call a tool. |
| **COMPANION** | Optional virtual pet: species, rarity tiers, stats, mood. A light personality layer. |

### Tools Registry (Flat)
Every tool defines its own input schema, permission level, and execution logic independently. Zero shared mutable state between tools. CABLES MAN has zero direct API access — everything routes through this registry.

| Tool | Description |
|------|-------------|
| **MCP TOOL** | Model Context Protocol bridge. Gmail, Google Calendar, Slack, Asana, custom servers. Tool definitions loaded dynamically at runtime. |
| **AGENT TOOL** | Spawns sub-agents as standard tool calls. Flat and predictable. |
| **BASH TOOL** | Every shell command gated through 23 security checks before execution. |
| **ARTIFACT TOOL** | Structured renderer. `<artifact type='jsx\|html\|mermaid\|svg\|md'>`. JSX via `@babel/standalone`. HTML in sandboxed iframe. |

**Web Tools (subsection)**
- `SERP API` — Google search + news via SerpAPI
- `WEB FETCH` — Full page content from URLs
- `NEWS TOOL` — Real-time news. Used by PULSE for monitoring.

**Misc Tools (subsection)**
- `CALENDAR` — Google Calendar read/write for time-aware outreach
- `WHATSAPP` — WhatsApp Business API outbound channel for alerts and lead capture

### External APIs
| API | Role |
|-----|------|
| **GROQ** (Qwen3.8-27B) | Primary free LLM backend, open-weight. All calls intercepted by Cache Layer. |
| **GPT-OSS-120B-Distill-70B** (via Groq) | Powers DEEPPLAN. 30-minute deep reasoning sessions. Free, open-weight. |

### Storage Layer
| Store | Description |
|-------|-------------|
| **Neon Postgres + pgvector** | One database holds both raw text and its embedding side by side — a `memories` row and its vector live together. CONSOLIDATOR writes/refreshes embeddings at consolidation time. SEM RETRIEVAL queries by cosine similarity every turn. Free tier, autosuspends when idle. |

Every memory row carries both its raw text and its semantic embedding together, so every memory is findable by association — not just by topic or date.

---

## Memory Philosophy

SNOWY never forgets. This is not a design constraint — it's a deliberate principle with three pillars:

1. **No deletion** — Neon never removes a record. Every conversation, decision, and learned fact is permanent.

2. **Salience, not pruning** — when storage grows large, the SALIENCE ENGINE determines what gets encoded first and ranked highest during retrieval. Low-salience memories remain in the store; they just surface less frequently.

3. **Semantic retrieval** — SEM RETRIEVAL means an old memory from months ago can surface today if it's semantically close to the current query. Recency is irrelevant; meaning is everything.

CONSOLIDATOR consolidates memories once 24 hours and 5 new sessions have passed, scores them via salience, writes embeddings, and updates a ranked index (`MEMORY.md`). The index is a pointer map — the actual memories live permanently in Neon (Postgres + pgvector).

---

## Infrastructure (near-zero budget, on AWS)

| Component | Service | Tier |
|-----------|---------|------|
| Chat API | AWS Lambda + Function URL, streaming (FastAPI via Lambda Web Adapter) | Free (1M req/mo forever) |
| Scheduled PULSE tick | AWS Lambda + EventBridge (rate: 15 min) | Free |
| LLM Backend | Groq (Qwen3.8-27B) | Free |
| Planning LLM | Groq (GPT-OSS-120B) | Free |
| Backup LLM (optional) | Modal (Ternary Bonsai 2 27B, scales to zero) | $30/mo Modal credit |
| Model picker | Free: Bonsai, Gemini, Groq · Paid: Claude, GPT, Qwen, DeepSeek, Kimi, Hugging Face | Free by default |
| Images / voice | Gemini (Nano Banana, TTS) | Free tier |
| Video ads (optional) | Modal (Wan 2.1, monthly cap) | Capped spend |
| Persistent Storage + Vector Store | Neon Postgres + pgvector | Free |
| Cache | DynamoDB (pay-per-request, TTL) | ~$0 |
| Embeddings | Modal (sentence-transformers) | Free ($30/mo credit) |
| Frontend | React + Vite (Cloudflare Pages) | Free |

The entire system is designed to run in production for a few cents a month —
see **[docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md)** for the full cost
breakdown and setup. LLM cost reduction is achieved through the Cache Layer —
system prompt reads cost 0.10× base cost after the first write.

---

## Configuration

Snowy uses a hierarchical `SNOWY.md` config system loaded every turn:

```
global/SNOWY.md      ← base defaults
user/SNOWY.md        ← per-user overrides
project/SNOWY.md     ← per-project context
local/SNOWY.md       ← local machine overrides
```

Each level overrides the previous. Total limit: 40,000 characters.

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Bash security checks | 23 |
| CTX compaction strategies | 5 |
| Cache breakpoints per request | up to 4 |
| Cache lookback window | 20 blocks |
| CTX buffer | 13k chars |
| CTX summary target | 20k chars |
| Circuit breaker threshold | 3 failures |
| PULSE tick interval | 15 minutes |
| PULSE tick budget | 120 seconds |
| CONSOLIDATOR trigger | 24 hours + 5 new sessions |
| Cache write cost (5-min TTL) | 1.25× base |
| Cache write cost (1-hr TTL) | 2.0× base |
| Cache read cost | 0.10× base |
| CTX assembly char limit | 40,000 |

---

## Project Structure (Proposed)

```
snowy/
├── main.py                 ← FastAPI app (local dev entrypoint)
├── run.sh                   ← Light tier — starts uvicorn under Lambda Web Adapter
├── tick_handler.py          ← Medium tier — scheduled PULSE tick (EventBridge)
├── template.yaml             ← AWS SAM stack (Lambda, DynamoDB, EventBridge)
├── modal_app/
│   └── embeddings.py         ← Modal function: sentence-transformers over HTTP
├── gateway/
│   ├── router.py             ← /chat, /status, /health
│   └── webhooks.py           ← optional OpenClaw bridge (WhatsApp/Telegram)
├── pipeline/                ← 7-step pipeline
│   ├── bootstrap.py
│   ├── ctx_assembly.py
│   ├── memory_load.py
│   ├── query_engine.py
│   ├── tool_execution.py
│   ├── ctx_pressure.py
│   └── sub_agent_deleg.py
├── tau/                     ← Adaptive identity engine
│   ├── tau_engine.py
│   ├── pacific.py
│   ├── emotion_engine.py
│   └── consolidator.py
├── core/                    ← CABLES MAN + support re-exports
│   ├── cables_man.py
│   ├── nature_sci.py
│   ├── salience.py
│   └── working_mem.py
├── agents/                  ← All agent implementations
│   ├── pulse.py             (run_once() for Medium tier, start() for Heavy)
│   ├── deepplan.py
│   ├── orchestrator.py
│   ├── consolidator_agent.py
│   ├── proactive.py
│   ├── explore.py
│   ├── plan_agent.py
│   ├── general_agent.py
│   ├── guide_agent.py
│   ├── worker_pool.py
│   ├── agent_inbox.py
│   ├── bridge.py
│   └── companion.py
├── tools/                   ← Flat tool registry
│   ├── registry.py
│   ├── mcp_tool.py
│   ├── agent_tool.py
│   ├── bash_tool.py
│   ├── artifact_tool.py
│   ├── openclaw_bridge.py
│   ├── web/
│   └── misc/
├── cache/                   ← DynamoDB-backed cache, in-memory L1
│   ├── ddb_backend.py
│   ├── sys_cache.py
│   ├── conv_cache.py
│   ├── cache_ctrl.py
│   └── tau_cache.py
├── storage/                 ← Neon Postgres + pgvector
│   ├── neon_store.py
│   └── embeddings.py         ← calls Modal, falls back to a local vector
├── memory/
│   ├── sem_retrieval.py      ← pgvector semantic search
│   ├── salience_engine.py
│   └── working_mem.py
├── tests/                   ← pytest + moto (DynamoDB) + respx (Groq)
├── frontend/                 ← React + Vite UI, deploys to Cloudflare Pages
├── SNOWY.md              ← Global config
├── docs/AWS_DEPLOYMENT.md    ← deployment guide + cost breakdown
└── README.md
```

---

## Name

**SNOWY** — the system presents itself as you expect, responds as you need, and learns who you are without you having to explain it again. The name reflects the core premise: an AI that develops a genuine model of its user rather than treating every session as the first.

**CABLES MAN** — Coordinated Autonomous Background Learning Execution System — Multi Agent Network. The orchestration core that makes parallelism invisible to the user.

**TAU** — the identity layer. Named for the constant — something fixed that defines proportion and character.

**PACIFIC** — Preference Alignment Choices Inference for Five-factor Identity Characterization. Also: deep, vast, and slow to change — like personality itself.
