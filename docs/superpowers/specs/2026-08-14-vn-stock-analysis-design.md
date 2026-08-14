# DSA-VN: Vietnam Stock Analysis Pipeline — Design

**Date:** 2026-08-14
**Status:** Approved (conversational), pending written-spec review

## 1. Context & motivation

The user wants to apply the architecture of [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) (DSA) — an LLM-driven, multi-strategy stock analysis system currently covering China A-shares, Hong Kong, US, Japan, Korea, and Taiwan — to the Vietnamese stock market (HOSE/HNX/UPCOM), which DSA does not support today.

DSA's distinguishing architectural idea is not "an LLM writes a stock report." It is: multiple independent strategy agents each produce a standardized opinion (`AgentOpinion`), those opinions are mathematically aggregated with explicit rules for conflict/insufficient-data cases (the "multi-strategy contract"), and only then does a final LLM pass synthesize the aggregated evidence into a human-readable decision dashboard. This design ports that specific pattern, not DSA's full product surface (web UI, desktop app, screening engine, backtesting, multi-channel bots, adaptive weight feedback loops), which are explicitly out of scope for this MVP.

## 2. Goals

- Reproduce DSA's core pipeline pattern — data ingestion → per-strategy LLM agents → standardized-opinion aggregation/synthesis → final LLM decision synthesis → rendered dashboard → notification — for a configurable watchlist of Vietnamese tickers.
- Encode Vietnam-specific market rules (price bands, lot size, settlement cycle, trading sessions, foreign ownership room) so the LLM reasons with correct local rules instead of rules inherited from another market.
- Run as a personal-use tool: manually or via cron, output delivered to a single Telegram chat.

## 3. Non-goals (explicitly deferred)

- News, sentiment, and fundamentals data sources (DSA's Anspire/SerpAPI/Tavily-equivalent integrations).
- Web UI, desktop app, FastAPI backend, multi-turn chat interface.
- Multi-channel notification beyond Telegram (Discord/Slack/email/WeChat/Feishu).
- Stock screening engine and backtesting engine.
- Outcome tracking / adaptive strategy-weight feedback loop (DSA's Phase 4).
- The 9 DSA strategies not listed in §6 below (`chan_theory`, `dragon_head`, `wave_theory`, `bottom_volume`, `emotion_cycle`, `event_driven`, `expectation_repricing`, `growth_quality`, `hot_theme`, `one_yang_three_yin`) — several are tied closely to Chinese-market terminology/culture and are left for a later phase if still wanted after the MVP proves out.
- Public/multi-user deployment and any related regulatory considerations (personal use only, per user decision).

## 4. Architecture overview

```
Watchlist (config: comma-separated VN tickers)
   │
   ▼
[vnstock fetcher] ── OHLCV history, latest quote, foreign buy/sell room, index membership
   │
   ▼ (per ticker, strategies run in parallel via asyncio)
[6 Strategy Agents] ── each is a separate Claude call with its own persona/prompt
   │   (strategies/*.yaml) → returns a standardized AgentOpinion
   ▼
[Aggregator + Synthesizer] ── ported logic from DSA's multi-strategy-contract
   │   (partition valid/invalid, weighted score, consensus level, conflict severity)
   ▼
[Decision Agent] ── one final Claude call: strategy_synthesis + market context
   │   → Vietnamese-language dashboard. Must not modify strategy_synthesis.
   ▼
[Renderer] → Markdown dashboard (Vietnamese)
   │
   ▼
[Telegram sender] → pushed to configured chat
```

Cost/latency note: each ticker run costs **7 Claude calls** (6 strategy agents + 1 decision agent). Total cost per run scales as `len(watchlist) × 7`. This was an explicit trade-off the user chose (fidelity to DSA's per-strategy-agent architecture over the cheaper hybrid deterministic-scoring approach). To keep this affordable, the 6 strategy agents should default to a smaller/cheaper Claude model and only the single decision agent uses a stronger model — a tiered setup, not a scope change, since the aggregation contract in §5.5 already treats every strategy opinion uniformly regardless of which model produced it.

**Tech stack:** Python 3.11+, `asyncio` for bounded-concurrency strategy calls, the Anthropic Python SDK, `vnstock` (class-based API), and direct Telegram Bot API HTTP calls (no heavier framework needed for a single-chat MVP).

## 5. Components

### 5.1 Data layer — `data_provider/vnstock_fetcher.py`

Wraps vnstock's class-based API (post-migration; the legacy `Vnstock` class reaches EOL 2026-08-31) to fetch, per ticker:
- OHLCV history (sufficient window for moving averages / breakout detection, e.g. 120 trading days)
- Latest quote (price, reference price, ceiling/floor price, volume)
- Foreign buy/sell room and net foreign trading value, if exposed by the underlying vnstock data source (TCBS/VCI) — **to verify during implementation**; if unavailable, `foreign_flow` strategy degrades gracefully (marks its own opinion invalid rather than fabricating data)
- Index membership (VN30 constituency) for context

Failure handling: any fetch error for a ticker (symbol not found, rate limit, network) is caught, logged, and that ticker is skipped for the run — the rest of the watchlist proceeds (fail-open per ticker).

### 5.2 Market profile — `core/market_profile.py`

Encodes Vietnam-specific facts, verified against current regulatory sources rather than assumed from general LLM knowledge:
- Price band (biên độ dao động) by exchange, relative to reference price: HOSE ±7%, HNX ±10%, UPCOM ±15%
- Ceiling/floor price = reference price × (1 ± band)
- Standard round lot: 100 shares
- Settlement cycle: T+2
- No same-day round-trip selling and no general short-selling for retail
- Trading sessions: ATO 9:00, continuous 9:00–11:30 & 13:00–14:30, ATC 14:30–14:45 (HOSE)
- Reference indices: VN-Index, VN30

This module is consumed by every strategy-agent prompt and the decision-agent prompt so the LLM never applies rules from another market (e.g. it must not reason about limit-up/down using non-VN thresholds, and must not suggest same-day flips).

**Implementation note:** the exact session times and any recent regulatory changes (e.g. settlement-cycle shortening proposals) should be re-verified at implementation time against HOSE/HNX/UPCOM or SSC primary sources, since these can change.

### 5.3 Strategy agents — `strategies/*.yaml` + `agent/strategy_agent.py`

Each strategy is a YAML file defining a persona and prompt template (mirrors DSA's `strategies/*.yaml` + `SkillAgent`), executed as one Claude call. Starting set:

| File | Origin | What it evaluates |
|---|---|---|
| `ma_trend.yaml` | Direct port of `ma_golden_cross.yaml` | Moving-average trend / golden-cross-death-cross |
| `volume_breakout.yaml` | Direct port | Price breakout confirmed by volume |
| `box_oscillation.yaml` | Direct port | Range-bound accumulation |
| `shrink_pullback.yaml` | Direct port | Pullback on shrinking volume (healthy-consolidation signal) |
| `foreign_flow.yaml` | **New — VN-specific** | Net foreign buy/sell flow and remaining foreign room; no equivalent in DSA's original strategy set, but this is one of the most closely watched signals by VN retail investors |
| `price_band_risk.yaml` | **Adapted** from DSA's China limit-up/down handling | Flags abnormal liquidity or price action near the ceiling/floor band |

Each agent call returns a JSON object matching the standardized schema (§5.4). Malformed or missing fields → the opinion is marked invalid (see §5.5), never silently coerced into a valid signal.

### 5.4 `AgentOpinion` schema (ported verbatim from DSA)

```
agent_name:  string
signal:      one of "strong_buy" | "buy" | "hold" | "sell" | "strong_sell"  (lowercase, canonical)
confidence:  float, 0.0–1.0
reasoning:   string (Vietnamese)
key_levels:  object (e.g. support/resistance/ceiling/floor prices referenced)
raw_data:    object (the inputs the agent was given, for traceability/debugging)
```

### 5.5 Aggregator + Synthesizer — `agent/aggregator.py`, `agent/synthesis.py`

Ports DSA's multi-strategy-contract rules:

1. **Partition**: an opinion is *valid* iff `signal` is one of the five canonical values and the opinion has no `invalid_signal=True` flag. Invalid opinions are collected into diagnostics (`meta["invalid_opinions"]`), never mixed into the evidence chain and never silently converted to `hold`.
2. **Insufficient-consensus branches** (checked in order):
   - Zero valid opinions → `final_signal="hold"`, `confidence=0.0`, `consensus_level="insufficient"`
   - Exactly one valid opinion → `consensus_level="insufficient"` regardless of that opinion's signal
   - Two or more valid opinions but `sum(confidence) == 0` → forced `hold`, `confidence=0.0`
3. **Weighted score**: canonical signal mapped to a numeric score, weighted by confidence. Proposed symmetric mapping (not verbatim confirmed from DSA source, but consistent with its described `buy→4.0` / `hold→3.0` pattern): `strong_sell=1.0, sell=2.0, hold=3.0, buy=4.0, strong_buy=5.0`.
4. **Consensus level**: `high` (≥2/3 alignment, zero conflicts) / `medium` (partial alignment or medium conflict) / `low` (high conflict or significant misalignment) / `insufficient` (per branch 2 above).
5. **Supporting/opposing grouping**: opinions within ±1.0 score of the weighted score are `supporting_skills`; all other valid opinions are `opposing_skills`.
6. **Output payload** (`strategy_synthesis`): `final_signal`, `weighted_score`, `confidence`, `consensus_level`, `conflict_severity`, `supporting_skills[]`, `opposing_skills[]`, `summary_params {opinion_count, invalid_opinion_count, total_opinion_count}`.

**Invariant carried over from DSA:** `strategy_synthesis` is immutable once produced. The Decision Agent (§5.6) may explain it, but must never overwrite or "fix" it.

### 5.6 Decision agent — `agent/decision_agent.py`

One final Claude call per ticker. Input: `strategy_synthesis` + market-profile context + the raw latest quote. Output: the Vietnamese-language dashboard content — core conclusion, score, trend, entry/exit levels, risk warnings, catalysts, action checklist. Must not alter `strategy_synthesis` fields (only read/explain them).

### 5.7 Renderer — `formatters.py`

Combines `strategy_synthesis` + decision-agent output into a single Markdown dashboard (Vietnamese), one section per ticker.

### 5.8 Notification — `notification_sender/telegram_sender.py`

Sends the rendered Markdown to a configured Telegram chat via the Bot API. Send failures are logged and do not abort the rest of the run.

### 5.9 Orchestration — `pipeline.py` / `main.py`

CLI entry point. For each ticker in the watchlist: fetch data → run the 6 strategy agents concurrently (bounded concurrency to respect API rate limits) → aggregate/synthesize → run decision agent → render → send. Designed to be invoked manually or from cron; no scheduler service in this MVP.

## 6. Configuration

`.env` (pattern matches DSA's `.env.example`):
- `ANTHROPIC_API_KEY`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `STOCK_LIST` — comma-separated VN tickers, e.g. `FPT,VNM,HPG,VCB`

## 7. Error handling summary

| Failure | Behavior |
|---|---|
| vnstock fetch fails for a ticker | Skip ticker, log, continue with the rest of the watchlist |
| A strategy agent returns malformed/invalid JSON | That opinion is marked invalid → diagnostics, not coerced to `hold`; aggregation proceeds with remaining valid opinions |
| Zero valid opinions for a ticker | Dashboard shows "insufficient data" for that ticker; no Telegram send for it (avoid noise) |
| Telegram send fails | Log error, continue to next ticker; run does not crash |

## 8. Testing strategy

- **Unit tests, aggregator/synthesizer** (highest priority — this is pure logic and the most likely place for subtle bugs): the three insufficient-consensus branches, weighted-score math, consensus-level thresholds, supporting/opposing grouping.
- **Unit tests, market_profile**: ceiling/floor price computation per exchange.
- **Pipeline integration test**: full run with mocked vnstock responses and mocked Claude responses — no real network/API calls in CI.
- **Manual smoke test**: one real run against 1–2 real tickers with real API keys before declaring the MVP done.

## 9. Open items to verify during implementation

- Exact vnstock class-based API surface post-migration (the legacy `Vnstock` class EOLs 2026-08-31, so implementation must use the current class-based interface from the start).
- Whether vnstock exposes foreign room / net foreign trading data directly, or whether `foreign_flow.yaml` needs a different data path.
- Current exact trading-session times and any settlement-cycle changes, re-verified against HOSE/HNX/UPCOM/SSC primary sources at implementation time.
- Telegram bot creation steps (BotFather token, obtaining the target chat ID) — operational setup, not architectural.

## 10. Project layout

Repository root is the current directory (`Github-test-model`, freshly `git init`-ed). Proposed layout, naming aligned with DSA for easy cross-reference:

```
data_provider/vnstock_fetcher.py
core/market_profile.py
strategies/*.yaml
agent/strategy_agent.py
agent/aggregator.py
agent/synthesis.py
agent/decision_agent.py
notification_sender/telegram_sender.py
formatters.py
pipeline.py
main.py
.env.example
```
