2026-08-14 20:50:54 - vnstock.core.utils.client - ERROR - API request failed: HTTPSConnectionPool(host='trading.vietcap.com.vn', port=443): Read timed out. (read timeout=30)
2026-08-14 20:51:27 - vnstock.core.utils.client - ERROR - API request failed: HTTPSConnectionPool(host='trading.vietcap.com.vn', port=443): Read timed out. (read timeout=30)
2026-08-14 20:51:59 - vnstock.core.utils.client - ERROR - API request failed: HTTPSConnectionPool(host='trading.vietcap.com.vn', port=443): Read timed out. (read timeout=30)
2026-08-14 20:52:31 - vnstock.core.utils.client - ERROR - API request failed: HTTPSConnectionPool(host='trading.vietcap.com.vn', port=443): Read timed out. (read timeout=30)
Traceback (most recent call last):
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py", line 534, in _make_request
    response = conn.getresponse()
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/urllib3/connection.py", line 571, in getresponse
    httplib_response = super().getresponse()
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/http/client.py", line 1430, in getresponse
    response.begin()
    ~~~~~~~~~~~~~~^^
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/http/client.py", line 331, in begin
    version, status, reason = self._read_status()
                              ~~~~~~~~~~~~~~~~~^^
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/http/client.py", line 292, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
               ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/socket.py", line 719, in readinto
    return self._sock.recv_into(b)
           ~~~~~~~~~~~~~~~~~~~~^^^
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/ssl.py", line 1304, in recv_into
    return self.read(nbytes, buffer)
           ~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/ssl.py", line 1138, in read
    return self._sslobj.read(len, buffer)
           ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
TimeoutError: The read operation timed out

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/requests/adapters.py", line 696, in send
    resp = conn.urlopen(
        method=request.method,
    ...<9 lines>...
        chunked=chunked,
    )
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py", line 842, in urlopen
    retries = retries.increment(
        method, url, error=new_e, _pool=self, _stacktrace=sys.exc_info()[2]
    )
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/urllib3/util/retry.py", line 498, in increment
    raise reraise(type(error), error, _stacktrace)
          ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/urllib3/util/util.py", line 39, in reraise
    raise value
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py", line 788, in urlopen
    response = self._make_request(
        conn,
    ...<10 lines>...
        **response_kw,
    )
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py", line 536, in _make_request
    self._raise_timeout(err=e, url=url, timeout_value=read_timeout)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py", line 367, in _raise_timeout
    raise ReadTimeoutError(
        self, url, f"Read timed out. (read timeout={timeout_value})"
    ) from err
urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='trading.vietcap.com.vn', port=443): Read timed out. (read timeout=30)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnstock/core/utils/client.py", line 269, in send_request_direct
    response = requests.post(
        url, headers=headers, data=data_arg, timeout=timeout, proxies=proxies
    )
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/requests/api.py", line 134, in post
    return request("post", url, data=data, json=json, **kwargs)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/requests/api.py", line 71, in request
    return session.request(method=method, url=url, **kwargs)
           ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/requests/sessions.py", line 651, in request
    resp = self.send(prep, **send_kwargs)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/requests/sessions.py", line 784, in send
    r = adapter.send(request, **kwargs)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/requests/adapters.py", line 742, in send
    raise ReadTimeout(e, request=request)
requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='trading.vietcap.com.vn', port=443): Read timed out. (read timeout=30)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/tenacity/__init__.py", line 473, in __call__
    result = fn(*args, **kwargs)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnstock/base.py", line 25, in wrapper
    result = func(self, *args, **kwargs)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnstock/api/trading.py", line 112, in price_board
    return self._delegate_to_provider(
           ~~~~~~~~~~~~~~~~~~~~~~~~~~^
        "price_board", symbols_list=symbols_list, **kwargs
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnstock/api/trading.py", line 220, in _delegate_to_provider
    return method(**kwargs)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnai/__init__.py", line 151, in wrapper
    return _optimized_func[0](*args, **kwargs)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnai/beam/quota.py", line 447, in wrapper
    result = func(*args, **kwargs)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnstock/explorer/vci/trading.py", line 81, in price_board
    data = client.send_request(
        url=url,
    ...<6 lines>...
        request_mode=self.proxy_config.request_mode,
    )
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnstock/core/utils/client.py", line 220, in send_request
    return send_request_direct(
        url, headers, method, params, payload, timeout, proxies=None
    )
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnstock/core/utils/client.py", line 280, in send_request_direct
    raise ConnectionError(error_msg) from e
ConnectionError: API request failed: HTTPSConnectionPool(host='trading.vietcap.com.vn', port=443): Read timed out. (read timeout=30)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/lucatxtruong/Documents/Github-test-model/scripts/probe_vnstock.py", line 51, in <module>
    probe()
    ~~~~~^^
  File "/Users/lucatxtruong/Documents/Github-test-model/scripts/probe_vnstock.py", line 30, in probe_price_board
    df = Trading(source="vci").price_board(symbols_list=[SYMBOL, "VNM"])
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnai/__init__.py", line 151, in wrapper
    return _optimized_func[0](*args, **kwargs)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/vnai/beam/quota.py", line 447, in wrapper
    result = func(*args, **kwargs)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/tenacity/__init__.py", line 331, in wrapped_f
    return copy(f, *args, **kw)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/tenacity/__init__.py", line 470, in __call__
    do = self.iter(retry_state=retry_state)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/tenacity/__init__.py", line 371, in iter
    result = action(retry_state)
  File "/Users/lucatxtruong/Documents/Github-test-model/.venv/lib/python3.13/site-packages/tenacity/__init__.py", line 414, in exc_check
    raise retry_exc from fut.exception()
tenacity.RetryError: RetryError[<Future at 0x1129cd480 state=finished raised ConnectionError>]
=== Quote.history(source='vci') ===
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                                 ┃
┃                                                                                 ┃
┃  🚀 VNSTOCK INSIDERS PROGRAM - NÂNG TẦM TRẢI NGHIỆM CỦA BẠN! 🚀                 ┃
┃                                                                                 ┃
┃  Nếu bạn cảm thấy khó chịu với các thông báo và quảng cáo:                      ┃
┃                                                                                 ┃
┃  ✨ Ẩn toàn bộ thông báo và quảng cáo phiền hà                                  ┃
┃  🔓 Mở rộng khả năng sử dụng API tối đa                                         ┃
┃  ⚡ Tăng tốc tải dữ liệu từ 5-8 lần                                              ┃
┃  📈 Tăng giới hạn truy cập API lên đến 5 lần                                    ┃
┃  🤖 Dùng AI Agent viết code hiệu quả với tài liệu Agent Guide                   ┃
┃                                                                                 ┃
┃  🔗 Tham gia ngay: https://vnstocks.com/insiders-program.                       ┃
┃                                                                                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
columns: ['time', 'open', 'high', 'low', 'close', 'volume']
dtypes:
 time      datetime64[ns]
open             float64
high             float64
low              float64
close            float64
volume             int64
dtype: object
rows: 146
tail:
           time  open  high   low  close   volume
143 2026-08-12  71.2  71.9  70.6   70.8  3685600
144 2026-08-13  71.0  71.3  69.2   69.2  7458000
145 2026-08-14  69.3  69.6  68.0   68.3  7123800

=== Trading.price_board(source='vci') ===

=== Trading.foreign_trade() (expected to FAIL) ===
failed as expected: RetryError: RetryError[<Future at 0x112a63570 state=finished raised NotImplementedError>]

================================================================================================
SUPPLEMENTARY INVESTIGATION — appended after the raw run above
================================================================================================

The raw output above is the literal, unedited result of running Step 6's exact command:

    .venv/bin/python scripts/probe_vnstock.py 2>&1 | tee docs/vnstock-probe-results.md

Two things are visible in it:

1. `Quote.history(source="vci")` **succeeded**, real columns and data (see above).
2. `Trading(source="vci").price_board(...)` **failed** with a network-level error before
   printing anything past its own header — no column data reached stdout.
3. `Trading(source="vci", symbol="FPT").foreign_trade()` **failed as expected**
   (`RetryError` wrapping `NotImplementedError`), consistent with the plan's expectation
   that this is a sponsor-only endpoint not implemented in the free `vci` explorer.

The script was run a **second, independent time**, unmodified, output captured separately
(not overwriting this file first, to avoid destroying the first real run). It reproduced the
identical failure mode for `price_board` — five read timeouts against
`trading.vietcap.com.vn`, ~32s apart, over roughly 2.5 minutes, then `tenacity.RetryError`
wrapping `ConnectionError`:

    2026-08-14 20:54:19 - vnstock.core.utils.client - ERROR - API request failed: HTTPSConnectionPool(host='trading.vietcap.com.vn', port=443): Read timed out. (read timeout=30)
    2026-08-14 20:54:51 - ... Read timed out. (read timeout=30)
    2026-08-14 20:55:25 - ... Read timed out. (read timeout=30)
    2026-08-14 20:55:57 - ... Read timed out. (read timeout=30)
    2026-08-14 20:56:29 - ... Read timed out. (read timeout=30)
    tenacity.RetryError: RetryError[<Future at 0x112ecdc70 state=finished raised ConnectionError>]

`Quote.history` and `foreign_trade()` behaved identically to the first run (success / expected
failure respectively). Only `price_board` was affected, both times, on the same host that
`Quote.history` was hitting successfully — so this is not "the network is unreachable."

## Root-cause diagnostic

To find out whether `price_board` was genuinely unreachable or just slow, I called the same
endpoint directly with a longer timeout (90s instead of the library's hardcoded 30s), bypassing
`Trading.price_board()`'s wrapper:

    url = "https://trading.vietcap.com.vn/api/price/symbols/getList"
    client.send_request(url=url, headers=get_headers(data_source="VCI", random_agent=False),
                         method="POST", payload={"symbols": ["FPT", "VNM"]}, timeout=90)

Real result:

    FAILED after 30.1s: ConnectionError: Failed to fetch data: 418 -

This is a genuine HTTP response (`vnstock/core/utils/client.py:273-274` only raises this from
an actual `response.status_code`), not a client-side timeout artifact — the Vietcap server (or a
WAF in front of it) is actively rejecting the request with **HTTP 418**, a status commonly used
by anti-bot/anti-scraping layers.

Reading `vnstock/core/utils/user_agent.py`: `Trading.__init__` and `Quote.__init__` both default
to `random_agent=False`, which makes `get_headers()` always emit the **same fixed**
`browser="chrome", platform="windows"` User-Agent/header set — identical across every vnstock
install that doesn't override it. That static, widely-shared fingerprint looks like a plausible
reason `price/symbols/getList` (a live price-board endpoint) specifically blocks it, while the
historical OHLC chart endpoint that `Quote.history` calls does not enforce the same rule.

**This is corroborated by a real, live, successful call** — same package, same `source="vci"`,
only difference is `random_agent=True` (a documented constructor kwarg on `Trading`/`Quote` that
just randomizes the simulated browser profile):

    Trading(source="vci", random_agent=True).price_board(symbols_list=["FPT", "VNM"])

This succeeded in 0.7s on the very first attempt (no retries needed). Real output:

    shape: (2, 82)
    columns (MultiIndex, top level = 'listing' | 'bid_ask' | 'match'):
    [('listing', 'symbol'), ('listing', 'ceiling'), ('listing', 'floor'), ('listing', 'ref_price'),
     ('listing', 'stock_type'), ('listing', 'exchange'), ('listing', 'trading_status'),
     ('listing', 'trading_status_code'), ('listing', 'trading_status_group'),
     ('listing', 'security_status'), ('listing', 'last_trading_date'), ('listing', 'issue_date'),
     ('listing', 'listed_share'), ('listing', 'coupon_rate'), ('listing', 'yield'),
     ('listing', 'sending_time'), ('listing', 'type'), ('listing', 'organ_name'),
     ('listing', 'mapping_symbol'), ('listing', 'product_grp_id'), ('listing', 'partition'),
     ('listing', 'index_type'), ('listing', 'trading_date'), ('listing', 'lst_trading_status'),
     ('listing', 'is_delisted'), ('listing', 'icb_code2'), ('listing', 'id'),
     ('bid_ask', 'transaction_time'), ('bid_ask', 'bid_count'), ('bid_ask', 'ask_count'),
     ('match', 'accumulated_value'), ('match', 'accumulated_volume'),
     ('match', 'accumulated_value_g1'), ('match', 'accumulated_volume_g1'),
     ('match', 'match_price_ato'), ('match', 'match_volume_ato'), ('match', 'match_price_atc'),
     ('match', 'match_volume_atc'), ('match', 'trading_session_id'), ('match', 'is_last_ato'),
     ('match', 'avg_match_price'), ('match', 'current_room'), ('match', 'foreign_buy_volume'),
     ('match', 'foreign_sell_volume'), ('match', 'foreign_buy_value'),
     ('match', 'foreign_sell_value'), ('match', 'highest'), ('match', 'lowest'),
     ('match', 'match_price'), ('match', 'open_price'), ('match', 'first_time_match_price'),
     ('match', 'match_type'), ('match', 'match_vol'), ('match', 'sending_time'),
     ('match', 'total_room'), ('match', 'total_buy_orders'), ('match', 'total_sell_orders'),
     ('match', 'bid_count'), ('match', 'ask_count'), ('match', 'underlying'),
     ('match', 'open_interest'), ('match', 'stock_type'), ('match', 'partition'),
     ('match', 'is_match_price'), ('match', 'ceiling_price'), ('match', 'floor_price'),
     ('match', 'reference_price'), ('match', 'icb_code2'), ('match', 'id'), ('match', 'last_ato'),
     ('bid_ask', 'bid_1_price'), ('bid_ask', 'bid_1_volume'), ('bid_ask', 'bid_2_price'),
     ('bid_ask', 'bid_2_volume'), ('bid_ask', 'bid_3_price'), ('bid_ask', 'bid_3_volume'),
     ('bid_ask', 'ask_1_price'), ('bid_ask', 'ask_1_volume'), ('bid_ask', 'ask_2_price'),
     ('bid_ask', 'ask_2_volume'), ('bid_ask', 'ask_3_price'), ('bid_ask', 'ask_3_volume')]

    FOREIGN COLUMNS FOUND (script's own `"foreign" in c.lower()` filter, applied to str(tuple)):
    ["('match', 'foreign_buy_volume')", "('match', 'foreign_sell_volume')",
     "('match', 'foreign_buy_value')", "('match', 'foreign_sell_value')"]

    dtypes + real sample values (FPT, VNM on 2026-08-14):
      ('match', 'foreign_buy_volume'):  int64  -> [1700217, 1199900]
      ('match', 'foreign_sell_volume'): int64  -> [2018643, 623736]
      ('match', 'foreign_buy_value'):   int64  -> [117148072400, 74126730000]
      ('match', 'foreign_sell_value'):  int64  -> [138932929900, 38534523600]

    Also present, semantically foreign-room-related but NOT matched by "foreign" in the name
    (worth flagging for Task 3 — these look like remaining/total foreign ownership room):
      ('match', 'current_room'): int64 -> [368745271, 1052456494]
      ('match', 'total_room'):   int64 -> [840019946, 2089955445]

    df.head() (truncated by pandas):
      listing                 ...      bid_ask
       symbol ceiling  floor  ... ask_2_volume ask_3_price ask_3_volume
    0     FPT   74000  64400  ...        68000       68600        22300
    1     VNM   65900  57300  ...        12300       61900         6900
    [2 rows x 82 columns]

## Important correction to the plan's assumption

`vnstock/explorer/vci/const.py` defines a `_PRICE_INFO_MAP` dict whose values include
`foreign_volume`, `foreign_room`, `foreign_holding_room` — the names the plan document assumed
`price_board` would return. **Grepping the entire installed `vnstock==4.0.5` package confirms
`_PRICE_INFO_MAP` is never imported or referenced anywhere outside `const.py` — it is dead
code.** `price_board()` does not apply it. The live response above confirms this directly: none
of `foreign_volume`, `foreign_room`, `foreign_holding_room`, `foreign_total_volume`,
`foreign_total_room` appear anywhere in the real 82-column response. The real names are
`foreign_buy_volume`, `foreign_sell_volume`, `foreign_buy_value`, `foreign_sell_value`,
`current_room`, `total_room`, all nested one level under `'match'` in a MultiIndex.

This is good news for `foreign_flow.yaml`, not bad: the real data is a **buy/sell split**
(not just a single net snapshot), so a net-foreign-flow computation (`foreign_buy_value -
foreign_sell_value`) is directly possible — richer than the plan's "point-in-time snapshot"
assumption.

## Operational note for Task 3 / the real fetcher

`Trading(source="vci")` and `Quote(source="vci")` both default to `random_agent=False`, which
sends a fixed, identical User-Agent/header fingerprint on every call. In this environment that
fingerprint was reliably rejected (HTTP 418) specifically on the `price_board` endpoint, twice,
while the identical fixed fingerprint worked fine for `Quote.history`. Passing
`random_agent=True` when constructing `Trading`/`Quote` made `price_board` succeed immediately,
with no code changes beyond that one kwarg. The data_provider fetcher built in a later task
should default to `random_agent=True` (or implement its own retry/backoff with header rotation)
for reliability. `scripts/probe_vnstock.py` itself was left exactly as specified in the task
brief (verbatim) and was NOT changed to add this kwarg — this note is for the real
implementation, not the throwaway probe.

## Exact column names for Task 3 (verified against a live response)

**OHLCV (`Quote(source="vci", symbol=...).history(...)`)** — flat columns, confirmed twice, live:
`time` (datetime64[ns]), `open` (float64), `high` (float64), `low` (float64), `close` (float64),
`volume` (int64).

**Foreign / price board (`Trading(source="vci", random_agent=True).price_board(symbols_list=[...])`)**
— MultiIndex columns `(group, field)`, confirmed live:
- `('match', 'foreign_buy_volume')` — int64
- `('match', 'foreign_sell_volume')` — int64
- `('match', 'foreign_buy_value')` — int64
- `('match', 'foreign_sell_value')` — int64
- `('match', 'current_room')` — int64 (likely remaining foreign room; name doesn't contain "foreign" — verify semantics before wiring into `foreign_flow.yaml`)
- `('match', 'total_room')` — int64 (likely total foreign room; same caveat)

**Reference price / ceiling / floor — UNRESOLVED, do not pick a column without further
verification.** The column list in "Root-cause diagnostic" above shows two name candidates in
different MultiIndex groups for each of three price-band fields:

- `('listing', 'ref_price')` vs `('match', 'reference_price')`
- `('listing', 'ceiling')` vs `('match', 'ceiling_price')`
- `('listing', 'floor')` vs `('match', 'floor_price')`

I re-checked this file (grepped every occurrence of `ref_price`, `reference_price`, `ceiling`,
`floor` — did not re-run the probe) to compare their actual values. The honest result: **the
comparison this would require isn't available in the recorded transcript.**

- `('listing', 'ceiling')` and `('listing', 'floor')` *do* have recorded values — from the
  `df.head()` print at the end of "Root-cause diagnostic": FPT ceiling=74000, floor=64400; VNM
  ceiling=65900, floor=57300.
- `('listing', 'ref_price')`, `('match', 'reference_price')`, `('match', 'ceiling_price')`, and
  `('match', 'floor_price')` have **no recorded value anywhere in this file** — only their
  *names* were captured, via the `columns:` list print. The `df.head()` call that ran right
  after was truncated by pandas' default column-display width before reaching any of them: the
  printed table shows only the first 3 columns (`symbol`, `ceiling`, `floor`) and the last 3
  (`ask_2_volume`, `ask_3_price`, `ask_3_volume`) of 82 total, with everything between collapsed
  to `...` — which swallowed `ref_price` (4th column) and all three `match`-group price fields
  (mid-list) without ever printing them.

So for every one of the three pairs, at least one side — and for `ref_price` /
`reference_price`, both sides — was never captured. That's a different finding from "identical,"
"differs," or "null for both": it's "not recorded." I'm not guessing which column is right from
this.

*Minor corroboration, not a substitute for the comparison above*: `listing.ceiling`=74000 and
`listing.floor`=64400 for FPT are arithmetically consistent with HOSE's ±7% band around a 69,200
reference price (69,200 × 1.07 = 74,044, rounds down to the 100-VND tick → 74,000; 69,200 × 0.93
= 64,356, rounds up to the 100-VND tick → 64,400) — and 69,200 is exactly FPT's prior-day close
already recorded in this file's `Quote.history` tail (`2026-08-13 ... close 69.2`). That confirms
the `listing` group's ceiling/floor are real, correctly-computed band values. It says nothing
about `listing.ref_price` itself (never printed), nor about whether the `match`-group namesakes
agree — that data point simply isn't in this file.

**Before wiring `price_band_risk`**, whoever implements it must run one targeted, offline-safe
check — not a full re-probe — printing exactly these six fields without truncation, e.g.:

    cols = [("listing", "ref_price"), ("match", "reference_price"),
            ("listing", "ceiling"), ("match", "ceiling_price"),
            ("listing", "floor"), ("match", "floor_price")]
    print(df[cols].to_string())

or `pd.set_option("display.max_columns", None)` before `.head()`. Until that runs, treat both
candidates in each pair as unverified.

The fetcher will need to flatten these MultiIndex columns (e.g. `flatten_columns=True`, a
documented `price_board()` kwarg that was not exercised in this probe) or index with the
2-tuples directly.

**`Trading(source="vci", symbol=...).foreign_trade()`** — confirmed twice, live: raises
(`tenacity.RetryError` wrapping `NotImplementedError`). Do not call this in the real fetcher.
