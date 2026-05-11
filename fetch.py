#!/usr/bin/env python3
"""CryptoBeacon — fetch market data, compute scores, write data.json.

Runs 3x/day via GitHub Actions. No external deps (stdlib only).

Note: Binance API jest zablokowane dla US data centerów (HTTP 451),
więc na GitHub Actions używamy CoinGecko (działa globalnie).
"""

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data.json"
HISTORY_FILE = ROOT / "history.json"
SPARKLINE_LEN = 7
DCA_HISTORY_LEN = 30
HALVING_DATE = datetime(2024, 4, 19)  # Bitcoin 4th halving

DAY_NAMES_PL = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
MONTHS_PL = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
             "lipca", "sierpnia", "września", "października", "listopada", "grudnia"]


def fetch_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "cryptobeacon/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def mood_label(score):
    if score < 15: return "Krew"
    if score < 30: return "Wyprzedaż"
    if score < 45: return "Słabość"
    if score < 55: return "Spokój"
    if score < 65: return "Wzmocnienie"
    if score < 75: return "Siła"
    if score < 85: return "Hossa"
    if score < 95: return "Mocna hossa"
    return "Mania"


def score_from_pct(pct):
    """Map a % price change to 0-100 score. -20% = 0, 0% = 50, +20% = 100."""
    return int(max(0, min(100, round(50 + pct * 2.5))))


def pct_change_from_prices(prices, days):
    """% change over the last N days from a daily prices array."""
    if len(prices) < days + 1:
        return 0.0
    close_now = prices[-1]
    close_then = prices[-1 - days]
    return (close_now - close_then) / close_then * 100


def cycle_score(now):
    """Score the BTC cycle position. Halving = 30. Peak ~month 18 = 90. Decay after."""
    months = (now - HALVING_DATE).days / 30.4
    if months < 18:
        s = 30 + (months / 18) * 60
    else:
        s = 90 - (months - 18) * 5
    return int(max(0, min(100, round(s))))


def fmt_price(p):
    if p >= 10000:
        return ("$" + f"{int(p):,}").replace(",", " ")
    if p >= 100:
        return f"${p:,.0f}".replace(",", " ")
    return f"${p:,.2f}".replace(",", " ").replace(".", ",")


def fmt_volume(v):
    if v >= 1e9:
        return f"${v / 1e9:.1f}B".replace(".", ",")
    if v >= 1e6:
        return f"${v / 1e6:.0f}M"
    return f"${v / 1e3:.0f}K"


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {"scores": {}, "dca": []}


def push_score(history, key, score):
    arr = history["scores"].setdefault(key, [])
    arr.append(score)
    if len(arr) > SPARKLINE_LEN:
        del arr[: len(arr) - SPARKLINE_LEN]
    return list(arr)


def push_dca(history, decision):
    arr = history.setdefault("dca", [])
    arr.append(1 if decision == "TAK" else 0)
    if len(arr) > DCA_HISTORY_LEN:
        del arr[: len(arr) - DCA_HISTORY_LEN]
    return list(arr)


def delta(arr):
    if len(arr) < 2:
        return 0
    return int(arr[-1] - arr[-2])


def main():
    print("Fetching data...")

    # CoinGecko simple prices (current price, 24h change, 24h volume)
    prices_resp = fetch_json(
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,binancecoin&vs_currencies=usd"
        "&include_24hr_change=true&include_24hr_vol=true"
    )
    btc_p = prices_resp["bitcoin"]
    bnb_p = prices_resp["binancecoin"]

    btc_price = btc_p["usd"]
    bnb_price = bnb_p["usd"]
    btc_24h = btc_p["usd_24h_change"]
    bnb_24h = bnb_p["usd_24h_change"]
    btc_vol = btc_p["usd_24h_vol"]
    bnb_vol = bnb_p["usd_24h_vol"]

    # CoinGecko market chart (daily prices + volumes, last 95 days)
    btc_chart = fetch_json(
        "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        "?vs_currency=usd&days=95&interval=daily"
    )
    bnb_chart = fetch_json(
        "https://api.coingecko.com/api/v3/coins/binancecoin/market_chart"
        "?vs_currency=usd&days=95&interval=daily"
    )
    btc_prices = [p[1] for p in btc_chart["prices"]]
    bnb_prices = [p[1] for p in bnb_chart["prices"]]
    btc_vols = [v[1] for v in btc_chart["total_volumes"]]
    bnb_vols = [v[1] for v in bnb_chart["total_volumes"]]

    btc_7d = pct_change_from_prices(btc_prices, 7)
    btc_30d = pct_change_from_prices(btc_prices, 30)
    btc_90d = pct_change_from_prices(btc_prices, 90)
    bnb_7d = pct_change_from_prices(bnb_prices, 7)
    bnb_30d = pct_change_from_prices(bnb_prices, 30)
    bnb_90d = pct_change_from_prices(bnb_prices, 90)

    # Volume vs 7d average
    btc_vol_7d_avg = sum(btc_vols[-8:-1]) / 7 if len(btc_vols) >= 8 else btc_vol
    bnb_vol_7d_avg = sum(bnb_vols[-8:-1]) / 7 if len(bnb_vols) >= 8 else bnb_vol
    btc_vol_vs_7d = (btc_vol / btc_vol_7d_avg - 1) * 100 if btc_vol_7d_avg else 0.0
    bnb_vol_vs_7d = (bnb_vol / bnb_vol_7d_avg - 1) * 100 if bnb_vol_7d_avg else 0.0

    # BNB/BTC ratio change 7d
    if len(btc_prices) > 7 and len(bnb_prices) > 7:
        bnb_btc_now = bnb_prices[-1] / btc_prices[-1]
        bnb_btc_then = bnb_prices[-8] / btc_prices[-8]
        bnb_vs_btc_7d = (bnb_btc_now / bnb_btc_then - 1) * 100
    else:
        bnb_vs_btc_7d = 0.0

    # CoinGecko global (BTC dominance)
    cg = fetch_json("https://api.coingecko.com/api/v3/global")
    btc_dom = cg["data"]["market_cap_percentage"]["btc"]

    # alternative.me Fear & Greed
    fng_resp = fetch_json("https://api.alternative.me/fng/?limit=1")
    fng = int(fng_resp["data"][0]["value"])

    print(f"  BTC: ${btc_price:.0f} ({btc_24h:+.1f}% 24h)")
    print(f"  BNB: ${bnb_price:.0f} ({bnb_24h:+.1f}% 24h)")
    print(f"  BTC dominance: {btc_dom:.1f}%   F&G: {fng}")

    # Timeframe scores
    score_24h = (fng + score_from_pct(btc_24h) + score_from_pct(bnb_24h)) // 3
    score_7d = (score_from_pct(btc_7d) + score_from_pct(bnb_7d)) // 2
    score_30d = (score_from_pct(btc_30d) + score_from_pct(bnb_30d)) // 2
    score_90d = (score_from_pct(btc_90d) + score_from_pct(bnb_90d)) // 2
    score_cycle = cycle_score(datetime.now())

    btc_score = (fng + score_from_pct(btc_24h) * 2) // 3
    bnb_score = (fng + score_from_pct(bnb_24h) * 2) // 3

    dca = "TAK" if score_24h < 80 else "NIE"

    history = load_history()
    hero_hist = push_score(history, "hero", score_24h)
    dzis_hist = push_score(history, "dzis", score_24h)
    tydzien_hist = push_score(history, "tydzien", score_7d)
    miesiac_hist = push_score(history, "miesiac", score_30d)
    kwartal_hist = push_score(history, "kwartal", score_90d)
    cykl_hist = push_score(history, "cykl", score_cycle)
    btc_hist = push_score(history, "btc", btc_score)
    bnb_hist = push_score(history, "bnb", bnb_score)
    dca_hist = push_dca(history, dca)

    now_local = datetime.now()
    header_label = f"{DAY_NAMES_PL[now_local.weekday()]}, {now_local.day} {MONTHS_PL[now_local.month - 1]}"

    data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "header_label": header_label,
        "hero": {
            "score": score_24h,
            "delta": delta(hero_hist),
            "mood": mood_label(score_24h),
            "history": hero_hist,
        },
        "dca": {
            "decision": dca,
            "history": dca_hist,
        },
        "time": [
            {"key": "dzis", "name": "Dziś", "sub": "24h", "score": score_24h,
             "delta": delta(dzis_hist), "mood": mood_label(score_24h), "history": dzis_hist},
            {"key": "tydzien", "name": "Tydzień", "sub": "7d", "score": score_7d,
             "delta": delta(tydzien_hist), "mood": mood_label(score_7d), "history": tydzien_hist},
            {"key": "miesiac", "name": "Miesiąc", "sub": "30d", "score": score_30d,
             "delta": delta(miesiac_hist), "mood": mood_label(score_30d), "history": miesiac_hist},
            {"key": "kwartal", "name": "Kwartał", "sub": "90d", "score": score_90d,
             "delta": delta(kwartal_hist), "mood": mood_label(score_90d), "history": kwartal_hist},
            {"key": "cykl", "name": "od halvingu", "sub": None, "score": score_cycle,
             "delta": delta(cykl_hist), "mood": mood_label(score_cycle), "history": cykl_hist},
        ],
        "assets": [
            {"key": "btc", "name": "BTC", "sub": "Bitcoin", "score": btc_score,
             "delta": delta(btc_hist), "mood": mood_label(btc_score), "history": btc_hist,
             "stats": [
                 {"label": "Cena", "value": fmt_price(btc_price),
                  "changes": [
                      {"tf": "24h", "val": round(btc_24h, 1)},
                      {"tf": "7d", "val": round(btc_7d, 1)},
                      {"tf": "30d", "val": round(btc_30d, 1)},
                  ]},
                 {"label": "Wolumen 24h", "value": fmt_volume(btc_vol), "change": round(btc_vol_vs_7d)},
                 {"label": "Dominacja", "value": f"{btc_dom:.1f}%".replace(".", ","),
                  "change": None},
             ]},
            {"key": "bnb", "name": "BNB", "sub": "Binance Coin", "score": bnb_score,
             "delta": delta(bnb_hist), "mood": mood_label(bnb_score), "history": bnb_hist,
             "stats": [
                 {"label": "Cena", "value": fmt_price(bnb_price),
                  "changes": [
                      {"tf": "24h", "val": round(bnb_24h, 1)},
                      {"tf": "7d", "val": round(bnb_7d, 1)},
                      {"tf": "30d", "val": round(bnb_30d, 1)},
                  ]},
                 {"label": "Wolumen 24h", "value": fmt_volume(bnb_vol), "change": round(bnb_vol_vs_7d)},
                 {"label": "BNB / BTC", "value": ("+" if bnb_vs_btc_7d >= 0 else "") + f"{bnb_vs_btc_7d:.1f}%".replace(".", ","),
                  "change": round(bnb_vs_btc_7d, 1), "changeUnit": "7d"},
             ]},
        ],
    }

    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2))

    print(f"Hero: {score_24h}/100 ({mood_label(score_24h)}), DCA: {dca}")
    print(f"Wrote {DATA_FILE.name} and {HISTORY_FILE.name}")


if __name__ == "__main__":
    main()
