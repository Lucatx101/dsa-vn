"""Vietnam market rules (HOSE / HNX / UPCOM).

Kept as pure functions with no I/O so they are cheap to test and safe to call
from prompt construction.

Step 0 verification (2026-08-15): price bands (HOSE ±7%, HNX ±10%,
UPCOM ±15%), the 100-share standard lot, the T+2 settlement cycle, and the
HOSE session times (ATO 9:00, continuous 9:00–11:30 and 13:00–14:30, ATC
14:30–14:45) were re-checked and found current — no change from the values
below. The ATC time was specifically re-confirmed as unchanged by the KRX
trading system that went live on HOSE 2025-05-05, and T+2 was specifically
re-confirmed as still the live settlement cycle (T+0 same-day settlement is a
publicly stated future roadmap item, not yet implemented as of this check).

Of the three primary sources named in the task brief, only hsx.vn responded,
and it returned a JS-rendered shell with no extractable rule text; hnx.vn
failed TLS certificate verification and ssc.gov.vn timed out — so none of
the three could be read directly. In their place, every value above was
cross-checked against several independent, mutually corroborating secondary
sources (thuvienphapluat.vn, vnexpress.net, dnse.com.vn, dsc.com.vn, TCBS's
official trading-regulations pages, and reporting on the 2025-05-05 KRX
go-live from cafef.vn / thitruongtaichinhtiente.vn / VnEconomy quoting the
State Securities Commission chairman on T+2 vs. T+0). One fetch
(fpts.com.vn) disagreed, claiming HOSE's afternoon session runs 13:00–15:00
with ATC at 15:00–15:15; that was outweighed by three independent sources
pinning ATC at 14:30–14:45 post-KRX and treated as stale or mismatched
content rather than as evidence of a real change.

Re-check if the regulator changes bands, lot size, or the settlement cycle.
"""

from enum import StrEnum

LOT_SIZE = 100
SETTLEMENT_CYCLE = "T+2"


class Exchange(StrEnum):
    HOSE = "HOSE"
    HNX = "HNX"
    UPCOM = "UPCOM"


PRICE_BAND: dict[Exchange, float] = {
    Exchange.HOSE: 0.07,
    Exchange.HNX: 0.10,
    Exchange.UPCOM: 0.15,
}


def price_band(exchange: Exchange) -> float:
    """Daily price band as a fraction of the reference price."""
    return PRICE_BAND[exchange]


def ceiling_price(reference_price: float, exchange: Exchange) -> float:
    """Giá trần — APPROXIMATE.

    The exchange rounds published bands to the tick size, so this can differ
    from the real ceiling by up to about half a tick (measured: FPT ref 69,200
    computes to 74,044, published 74,000). Prefer the board's own
    `listing_ceiling` when it is available; use this only as a fallback.
    """
    return reference_price * (1 + price_band(exchange))


def floor_price(reference_price: float, exchange: Exchange) -> float:
    """Giá sàn — APPROXIMATE. Same tick-rounding caveat as `ceiling_price`."""
    return reference_price * (1 - price_band(exchange))


def pct_from_reference(price: float, reference_price: float) -> float:
    """Percent move from the reference price, e.g. 107000 vs 100000 -> 7.0."""
    if reference_price == 0:
        raise ValueError("reference_price must be non-zero")
    return (price - reference_price) / reference_price * 100


def market_rules_text() -> str:
    """Vietnamese market-rules block injected into every LLM prompt."""
    return (
        "LUẬT THỊ TRƯỜNG CHỨNG KHOÁN VIỆT NAM (bắt buộc tuân thủ khi phân tích):\n"
        "- Biên độ dao động giá trong phiên, tính trên giá tham chiếu: "
        "HOSE ±7%, HNX ±10%, UPCOM ±15%.\n"
        "- Giá trần ≈ giá tham chiếu × (1 + biên độ); giá sàn ≈ giá tham chiếu × (1 − biên độ). "
        "Đây chỉ là ƯỚC LƯỢNG: sở giao dịch làm tròn theo bước giá, nên có thể lệch. "
        "Nếu phần dữ liệu có giá trần/giá sàn công bố, PHẢI dùng con số công bố đó, "
        "không dùng con số tự tính.\n"
        f"- Lô giao dịch chuẩn: {LOT_SIZE} cổ phiếu.\n"
        f"- Chu kỳ thanh toán: {SETTLEMENT_CYCLE}. Cổ phiếu mua hôm nay chưa thể bán ngay trong phiên.\n"
        "- Nhà đầu tư cá nhân thông thường KHÔNG được bán khống và KHÔNG được "
        "mua bán cùng một mã trong cùng một phiên.\n"
        "- Phiên giao dịch (HOSE): ATO 9:00, khớp lệnh liên tục 9:00–11:30 và "
        "13:00–14:30, ATC 14:30–14:45.\n"
        "- Chỉ số tham chiếu: VN-Index, VN30.\n"
        "TUYỆT ĐỐI KHÔNG áp dụng luật của thị trường nước khác (Mỹ, Trung Quốc, "
        "Hồng Kông…) vào phân tích này."
    )
