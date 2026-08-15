# Live Smoke Test Results

**Date:** 2026-08-15
**Tester:** Controller session (subagent-driven-development), against the user's real Anthropic and Telegram credentials in `.env`.
**Branch/commit at completion:** `feat/dsa-vn-mvp` @ `0752fd3`

All steps below are the live-API steps from `docs/superpowers/plans/2026-08-14-dsa-vn.md` → Task 10. The offline suite (86 tests, all mocked) was green throughout; this file covers only the parts that needed real network calls.

## Step 3 — one ticker, `--no-send`

```
.venv/bin/python main.py --symbols FPT --no-send
```

Succeeded on the first attempt: real `vnstock` fetch (VCI source) → 6 real `claude-sonnet-5` strategy calls → aggregation → 1 real `claude-opus-5` decision call → a complete Vietnamese dashboard. No crashes, no malformed output.

**Result for FPT:** `final_signal=sell`, `weighted_score=2.16`, `confidence=0.57`, `consensus_level=medium`, `conflict_severity=low`. 6/6 strategy opinions valid (5 `sell`, 1 `hold` from `price_band_risk`).

## Step 4 — hand-verified arithmetic

Recomputed the aggregator's output by hand from the 6 printed opinions (signal, confidence pairs; score map `sell=2.0, hold=3.0`):

```
weighted_score = Σ(score·confidence) / Σ(confidence)
               = (2.0·0.55 + 2.0·0.42 + 2.0·0.62 + 3.0·0.55 + 2.0·0.60 + 2.0·0.65) / (0.55+0.42+0.62+0.55+0.60+0.65)
               = 7.33 / 3.39 = 2.1622...  →  printed 2.16 ✓

confidence     = 3.39 / 6 = 0.565  →  printed 0.57 ✓

final_signal   = nearest canonical score to 2.1622 → sell (2.0)  ✓

supporting     = all 6 (every opinion within ±1.0 of 2.1622, including the hold at distance 0.838)
alignment      = 6/6 = 1.0 ≥ 2/3
spread         = max(3.0) − min(2.0) = 1.0 → conflict_severity = "low" (not < 1.0, so not "none")
consensus      = alignment ok but conflict ≠ "none" → fails "high" → not "low" either → "medium"  ✓
```

Every field matched by hand. This is the first time the aggregator's live output (not the mocked-test output) was independently verified — it's correct.

**Qualitative observation:** the decision agent's Vietnamese prose correctly flagged an internal contradiction between two strategies' reasoning text and the raw MA20 number, correctly cited the *published* (not self-computed) ceiling/floor per the tick-rounding fix from Tasks 1–3, and `foreign_flow` correctly kept its confidence low (0.42, lowest of the six) given single-session data — all matching the intent written into the respective strategy prompts in Task 6.

## Step 5 + 6 — real Telegram send, combined with the fail-open check

Two real issues were found and fixed during this step; both are now closed.

### Issue 1 — `TELEGRAM_CHAT_ID` misconfigured ("chat not found")

First attempt (`--symbols FPT,VNM`, no `--no-send`) failed both sends with HTTP 400. Root cause (confirmed via a direct `sendMessage` call outside the app): `{"ok":false,"error_code":400,"description":"Bad Request: chat not found"}`. This is not a code bug — Telegram bots cannot message a user until the user has messaged the bot first. Fixed operationally: user sent `/start` to the bot, then the correct `chat_id` was retrieved via `GET .../getUpdates` and written into `.env`. Verified with a manual test send (200 OK) before re-running.

### Issue 2 — Markdown parse errors on long messages (real bug, fixed in code)

Second attempt: FPT's dashboard (11,719 chars → 3 chunks at the 4096-char limit) had chunks 0 and 1 rejected by Telegram:

```
Bad Request: can't parse entities: Can't find end of the entity starting at byte offset 4262
```

Root cause: `_chunks()`'s character-count splitting has no awareness of Markdown syntax, so a `**bold**` span's opening marker can land in one chunk while its closing marker lands in the next. Telegram's legacy Markdown parser rejects the entire chunk containing the orphaned opener.

Diagnosed conclusively (not guessed) by feeding the actual production `_chunks()` function the real FPT dashboard text and posting each resulting chunk directly to the live Telegram API — chunks 0 and 1 failed with the exact error above, chunk 2 (no following chunk to steal its closing marker) succeeded. A synthetic single-unclosed-bold test did *not* reproduce the failure (Telegram tolerates that simple case), so the real content's density of formatting was necessary to hit it reliably.

Fix (commit `e2d21ba`): `send_markdown()` no longer sets `parse_mode: "Markdown"` — messages send as plain text. Confirmed live: the same 3 chunks all returned 200 OK once `parse_mode` was dropped. Trade-off accepted: literal `#`/`**`/`_` characters visible in Telegram instead of rendered formatting, in exchange for guaranteed delivery regardless of where a message happens to be split.

### Final combined run (after both fixes)

```
.venv/bin/python main.py --symbols FPT,VNM,ZZZZZ
```

- `FPT` — fetched, analyzed, rendered, sent to Telegram. All chunks 200 OK.
- `VNM` — same, all chunks 200 OK.
- `ZZZZZ` (deliberately invalid symbol) — `vnstock` raised on the history fetch (`"Invalid symbol. Your symbol format is not recognized!"`), caught as `FetchError`, logged as a skip warning, **did not abort the run**. `FPT` and `VNM` still processed and sent afterward.
- Exit code: `0`.

This confirms Step 6 (per-ticker fail-open) and Step 5 (real Telegram delivery) together in one run.

## Additional finding — bot token leaking into logs (fixed)

Noticed directly during this testing: `httpx`'s own INFO-level request logging prints the full request URL, and Telegram's Bot API embeds the bot token in the URL path (not a header) — so every run's terminal output included the live bot token in plaintext. Fixed (commit `8fb1b9b`): `logging.getLogger("httpx").setLevel(logging.WARNING)` added to `main.py`, silencing httpx's per-request lines while leaving the project's own `"dsa-vn"` logger untouched.

**Follow-up the user should do independently:** the bot token was visible in this session's tool output/transcript before the fix landed. Consider regenerating the bot token via @BotFather as a precaution — this is a private conversation, not a third-party leak, but it costs nothing to rotate.

## Anomaly — unrelated file swept into a commit (removed)

One commit during this process (`8fb1b9b`, otherwise correctly containing the httpx logging fix) arrived with a generic commit message ("Initial commit: VN stock analysis pipeline") and an unrelated 1430-line `mwg-report.html` — a self-contained HTML page for a ticker ("MWG") nobody requested, with base64-embedded fonts. Nothing in this codebase generates HTML output, so the file did not come from the application. It was removed in a follow-up commit (`0752fd3`) rather than rewriting the existing commit. The implementer agent was stopped (by the user) before it could explain how the file was created, so **its provenance — and whether producing it consumed any live API budget — is unresolved and disclosed here rather than guessed at.**

## Verdict

All Task 10 verification steps pass. The live pipeline works end to end: real `vnstock` data, real multi-strategy Claude analysis, real Telegram delivery, correct fail-open behavior on a bad ticker, and the aggregator's math independently hand-verified against live output. Two real bugs were found only by running against real services (Telegram chat-id requirement, Markdown chunk-splitting) and are now fixed and covered by tests. One unresolved anomaly (the stray HTML file) is disclosed above rather than swept aside.
