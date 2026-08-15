# DSA-VN

Phân tích cổ phiếu Việt Nam bằng kiến trúc multi-agent, port từ
[ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis).

Công cụ nghiên cứu cá nhân. **Không phải khuyến nghị đầu tư.**

## Cách hoạt động

Với mỗi mã cổ phiếu: lấy dữ liệu từ vnstock (nguồn VCI) → 6 strategy agent chạy song song
(mỗi agent là một lệnh gọi Claude riêng — `claude-sonnet-5` — trả về `AgentOpinion` chuẩn hóa) →
tổng hợp đa chiến lược bằng logic Python thuần (không LLM) → 1 lệnh gọi Claude cuối
(`claude-opus-5`) viết dashboard tiếng Việt, không được sửa kết quả tổng hợp → gửi Telegram.

Chi phí: khoảng 7 lệnh gọi Claude mỗi mã mỗi lần chạy.

## Cài đặt

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env
```

Điền vào `.env`:
- `ANTHROPIC_API_KEY` — API key Anthropic.
- `TELEGRAM_BOT_TOKEN` — tạo qua [@BotFather](https://t.me/BotFather): `/newbot`, làm theo hướng dẫn, lấy token.
- `TELEGRAM_CHAT_ID` — **bot không thể chủ động nhắn cho bạn cho đến khi bạn nhắn cho nó trước.**
  Mở chat với bot vừa tạo, gửi `/start`, rồi lấy `chat_id` bằng lệnh:
  ```bash
  curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
  ```
  Tìm `"chat":{"id": ...}` trong kết quả trả về.
- `STOCK_LIST` — danh sách mã theo dõi, cách nhau bằng dấu phẩy.

## Sử dụng

```bash
.venv/bin/python main.py                              # dùng STOCK_LIST trong .env
.venv/bin/python main.py --symbols FPT,VNM            # chỉ định mã
.venv/bin/python main.py --symbols FPT --no-send      # in ra màn hình, không gửi Telegram
.venv/bin/python main.py --exchange HNX --symbols SHS # sàn khác (mặc định HOSE)
```

## Kiểm thử

```bash
.venv/bin/pytest
```

86 test, toàn bộ mock hóa lệnh gọi Claude/vnstock/Telegram — không tốn API khi chạy `pytest`.
Kết quả kiểm thử thật với API thật: xem `docs/smoke-test-results.md`.

## Giới hạn đã biết

- Nguồn dữ liệu cố định là `vci` — sàn duy nhất trong bản vnstock miễn phí có cột dữ liệu
  mua/bán ròng khối ngoại.
- Chiến lược `foreign_flow` chỉ đọc được dữ liệu **một phiên gần nhất**, không có chuỗi
  mua/bán ròng nhiều phiên (đó là tính năng của gói `vnstock_data` có trả phí).
- Giá trần/sàn tự tính trong `core/market_profile.py` chỉ là ước lượng (sở giao dịch làm tròn
  theo bước giá) — pipeline luôn ưu tiên dùng số liệu sở công bố khi có.
- Tin nhắn Telegram gửi dạng **văn bản thuần**, không render `**đậm**`/`_nghiêng_` — chế độ
  Markdown cũ của Telegram dễ từ chối tin nhắn dài bị cắt đoạn giữa một cặp ký hiệu định dạng.
- Chưa có: tin tức/sentiment, Web UI, backtest, engine sàng lọc cổ phiếu, đa kênh thông báo.
- `import vnstock` (không qua `data_provider`) sẽ âm thầm ghi file vào thư mục home của bạn —
  xem `docs/vnstock-probe-results.md`. Guard chặn việc này nằm trong `data_provider/__init__.py`;
  không import `vnstock` trực tiếp từ module khác.

## Cấu trúc dự án

```
core/market_profile.py           luật thị trường VN (biên độ giá, lô, T+2, phiên)
data_provider/vnstock_fetcher.py lấy dữ liệu vnstock (nguồn vci)
agent/schemas.py                 AgentOpinion, StrategySynthesis
agent/aggregator.py              tổng hợp đa chiến lược (logic thuần)
agent/synthesis.py               mức đồng thuận / mâu thuẫn
agent/strategy_agent.py          chạy 1 strategy agent (1 lệnh gọi Claude)
agent/decision_agent.py          agent quyết định cuối (1 lệnh gọi Claude)
strategies/*.yaml                6 định nghĩa chiến lược (persona + prompt)
formatters.py                    render dashboard Markdown
notification_sender/telegram_sender.py  gửi Telegram
pipeline.py                      điều phối theo từng mã
main.py                          CLI
```
