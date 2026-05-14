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
SPARKLINE_LEN = 24      # last 24 entries — przy cron co 1h to last 24h trendu
DCA_HISTORY_LEN = 30    # 30 dni (push_dca dedupluje po dacie)
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
    if len(prices) < days + 1:
        return 0.0
    return (prices[-1] - prices[-1 - days]) / prices[-1 - days] * 100


def cycle_score(now):
    """Halving = 30. Peak ~month 18 = 90. Decay after."""
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


def fmt_pct(p):
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:.1f}%".replace(".", ",")


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {"scores": {}, "btc_dca": [], "bnb_dca": []}


def push_score(history, key, score):
    arr = history["scores"].setdefault(key, [])
    arr.append(score)
    if len(arr) > SPARKLINE_LEN:
        del arr[: len(arr) - SPARKLINE_LEN]
    return list(arr)


def push_dca(history, key, decision):
    """One entry per calendar day. Same-day reruns update the latest entry
    (so the strip shows last 30 actual days, not last 30 refreshes)."""
    today = datetime.now().strftime("%Y-%m-%d")
    date_key = f"{key}_last_date"
    last_date = history.get(date_key)
    arr = history.setdefault(key, [])
    val = 1 if decision == "TAK" else 0
    if last_date == today and arr:
        arr[-1] = val
    else:
        arr.append(val)
        if len(arr) > DCA_HISTORY_LEN:
            del arr[: len(arr) - DCA_HISTORY_LEN]
    history[date_key] = today
    return list(arr)


def delta(arr):
    if len(arr) < 2:
        return 0
    return int(arr[-1] - arr[-2])


def months_pl(n):
    if n == 1:
        return "miesiąc"
    last_two = n % 100
    if 12 <= last_two <= 14:
        return "miesięcy"
    last_one = n % 10
    if 2 <= last_one <= 4:
        return "miesiące"
    return "miesięcy"


def forecast_volume(price_change_7d, vol_now, vol_30d_avg):
    direction = 1 if price_change_7d > 0.5 else -1 if price_change_7d < -0.5 else 0
    if direction == 0 or vol_30d_avg == 0:
        return (0, "Ruch w cenie zbyt mały by oceniać potwierdzenie wolumenem")
    ratio = vol_now / vol_30d_avg
    pct_str = f"{(ratio - 1) * 100:+.0f}%".replace("+", "+")
    if ratio > 1.2:
        delta_v = 5 * direction
        kierunek_s = "w górę" if direction > 0 else "w dół"
        return (delta_v, f"Ruch {kierunek_s} z wolumenem {pct_str} vs średnia 30d — potwierdzenie")
    elif ratio < 0.9:
        delta_v = -3 * direction
        kierunek_s = "w górę" if direction > 0 else "w dół"
        return (delta_v, f"Ruch {kierunek_s} bez wolumenu (wolumen {pct_str} vs 30d) — divergencja")
    else:
        delta_v = 2 * direction
        kierunek_s = "w górę" if direction > 0 else "w dół"
        return (delta_v, f"Ruch {kierunek_s} z umiarkowanym wolumenem ({pct_str} vs 30d)")


def forecast_mean_reversion(score_now, fng, prices):
    delta_v = 0
    notes = []
    if fng < 25:
        delta_v += 4
        notes.append(f"F&G {fng} (ekstremalny strach) — presja w górę")
    elif fng > 75:
        delta_v -= 4
        notes.append(f"F&G {fng} (ekstremalna chciwość) — presja w dół")

    if len(prices) >= 90:
        window = prices[-90:]
        lo, hi = min(window), max(window)
        if hi > lo:
            pos = (prices[-1] - lo) / (hi - lo)
            if pos > 0.9:
                delta_v -= 3
                notes.append(f"Cena w top decylu 90d range ({pos*100:.0f}%) — presja w dół")
            elif pos < 0.1:
                delta_v += 3
                notes.append(f"Cena w bottom decylu 90d range ({pos*100:.0f}%) — presja w górę")

    if not notes:
        return (0, f"F&G {fng} i pozycja w 90d range neutralne")
    return (delta_v, "; ".join(notes))


def forecast_momentum(prices):
    if len(prices) < 4:
        return (0, "Za mało historii do oceny streaku")
    threshold = 0.002  # 0.2%
    streak = 0
    direction = 0
    for i in range(len(prices) - 1, 0, -1):
        change = (prices[i] - prices[i - 1]) / prices[i - 1]
        if abs(change) < threshold:
            break
        sign = 1 if change > 0 else -1
        if direction == 0:
            direction = sign
            streak = 1
        elif sign == direction:
            streak += 1
        else:
            break

    if streak == 0 or direction == 0:
        return (0, "Brak wyraźnego streaku cenowego")

    kierunek_s = "w górę" if direction > 0 else "w dół"
    dni_word = "dzień" if streak == 1 else "dni"
    if streak <= 3:
        return (direction * 3, f"{streak} {dni_word} z rzędu {kierunek_s} — kontynuacja prawdopodobna")
    elif streak <= 5:
        return (direction * 1, f"{streak} {dni_word} z rzędu {kierunek_s} — ostygnięcie momentum")
    else:
        return (-direction * 3, f"{streak} {dni_word} z rzędu {kierunek_s} — wyczerpanie, reversal prawdopodobny")


def forecast_cycle(months):
    if months < 12:
        return (3, f"{months} mies. po halvingu — wczesna faza wzrostu (bullish bias)")
    elif months < 18:
        return (0, f"{months} mies. po halvingu — dojrzała faza wzrostu (neutralnie)")
    elif months < 24:
        return (-2, f"{months} mies. po halvingu — bliski szczyt cyklu (bearish bias)")
    else:
        return (-3, f"{months} mies. po halvingu — cykl po szczycie historycznym (bearish)")


def compose_forecast(score_now, deltas_with_notes):
    """deltas_with_notes: list of dicts {name, delta, note}. Returns forecast dict."""
    deltas = [r["delta"] for r in deltas_with_notes]
    total = max(-30, min(30, sum(deltas)))
    expected = max(0, min(100, score_now + total))

    spread = max(deltas) - min(deltas)
    all_same_sign = all(d >= 0 for d in deltas) or all(d <= 0 for d in deltas)
    if all_same_sign and spread <= 5:
        width = 8
    elif spread <= 8:
        width = 12
    else:
        width = 20

    lo = max(0, expected - width // 2)
    hi = min(100, expected + width // 2)

    if width <= 8:
        confidence = "high"
    elif width <= 16:
        confidence = "medium"
    else:
        confidence = "low"

    if total > 1:
        direction_s = "up"
    elif total < -1:
        direction_s = "down"
    else:
        direction_s = "flat"

    mood_lo = mood_label(lo)
    mood_hi = mood_label(hi)
    mood_range = mood_lo if mood_lo == mood_hi else f"{mood_lo} → {mood_hi}"

    return {
        "horizon_days": 7,
        "score_now": score_now,
        "score_expected": expected,
        "score_range": [lo, hi],
        "mood_range": mood_range,
        "direction": direction_s,
        "confidence": confidence,
        "total_delta": total,
        "rules": deltas_with_notes,
    }


def build_forecast(score_now, prices, vol_now, vol_30d_avg, fng, months_since_halving):
    pct_7d = pct_change_from_prices(prices, 7) if len(prices) >= 8 else 0.0
    d_vol, n_vol = forecast_volume(pct_7d, vol_now, vol_30d_avg)
    d_mr, n_mr = forecast_mean_reversion(score_now, fng, prices)
    d_mom, n_mom = forecast_momentum(prices)
    d_cyc, n_cyc = forecast_cycle(months_since_halving)
    rules = [
        {"name": "Wolumen",        "delta": d_vol, "note": n_vol},
        {"name": "Mean reversion", "delta": d_mr,  "note": n_mr},
        {"name": "Momentum",       "delta": d_mom, "note": n_mom},
        {"name": "Cykl",           "delta": d_cyc, "note": n_cyc},
    ]
    return compose_forecast(score_now, rules)


def asset_time_block(asset_key, history, pct_24h, pct_7d, pct_30d, pct_90d, fng, cyc_score):
    """Build the time strip for a single asset."""
    s_24h = (fng + score_from_pct(pct_24h)) // 2
    s_7d = score_from_pct(pct_7d)
    s_30d = score_from_pct(pct_30d)
    s_90d = score_from_pct(pct_90d)

    h_24h = push_score(history, f"{asset_key}_dzis", s_24h)
    h_7d = push_score(history, f"{asset_key}_tydzien", s_7d)
    h_30d = push_score(history, f"{asset_key}_miesiac", s_30d)
    h_90d = push_score(history, f"{asset_key}_kwartal", s_90d)
    h_cyc = push_score(history, "cykl", cyc_score) if asset_key == "btc" else list(history["scores"].get("cykl", [cyc_score]))

    return [
        {"key": "dzis", "name": "Dziś", "sub": "24h", "score": s_24h,
         "delta": delta(h_24h), "mood": mood_label(s_24h), "history": h_24h},
        {"key": "tydzien", "name": "Tydzień", "sub": "7d", "score": s_7d,
         "delta": delta(h_7d), "mood": mood_label(s_7d), "history": h_7d},
        {"key": "miesiac", "name": "Miesiąc", "sub": "30d", "score": s_30d,
         "delta": delta(h_30d), "mood": mood_label(s_30d), "history": h_30d},
        {"key": "kwartal", "name": "Kwartał", "sub": "90d", "score": s_90d,
         "delta": delta(h_90d), "mood": mood_label(s_90d), "history": h_90d},
        {"key": "cykl", "name": "od halvingu", "sub": None, "score": cyc_score,
         "delta": delta(h_cyc), "mood": mood_label(cyc_score), "history": h_cyc},
    ]


def main():
    print("Fetching data...")

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

    btc_vol_7d_avg = sum(btc_vols[-8:-1]) / 7 if len(btc_vols) >= 8 else btc_vol
    bnb_vol_7d_avg = sum(bnb_vols[-8:-1]) / 7 if len(bnb_vols) >= 8 else bnb_vol
    btc_vol_vs_7d = (btc_vol / btc_vol_7d_avg - 1) * 100 if btc_vol_7d_avg else 0.0
    bnb_vol_vs_7d = (bnb_vol / bnb_vol_7d_avg - 1) * 100 if bnb_vol_7d_avg else 0.0

    if len(btc_prices) > 7 and len(bnb_prices) > 7:
        bnb_btc_now = bnb_prices[-1] / btc_prices[-1]
        bnb_btc_then = bnb_prices[-8] / btc_prices[-8]
        bnb_vs_btc_7d = (bnb_btc_now / bnb_btc_then - 1) * 100
    else:
        bnb_vs_btc_7d = 0.0

    cg = fetch_json("https://api.coingecko.com/api/v3/global")
    btc_dom = cg["data"]["market_cap_percentage"]["btc"]

    fng_resp = fetch_json("https://api.alternative.me/fng/?limit=1")
    fng = int(fng_resp["data"][0]["value"])
    fng_classification = fng_resp["data"][0]["value_classification"]

    print(f"  BTC: ${btc_price:.0f} ({btc_24h:+.1f}% 24h)")
    print(f"  BNB: ${bnb_price:.0f} ({bnb_24h:+.1f}% 24h)")
    print(f"  BTC dominance: {btc_dom:.1f}%   F&G: {fng}")

    cyc = cycle_score(datetime.now())
    btc_score = (fng + score_from_pct(btc_24h) * 2) // 3
    bnb_score = (fng + score_from_pct(bnb_24h) * 2) // 3

    btc_dca = "NIE" if btc_score >= 80 else "TAK"
    bnb_dca = "NIE" if bnb_score >= 80 else "TAK"

    fng_pl_map = {
        "Extreme Fear": "ekstremalny strach",
        "Fear": "strach",
        "Neutral": "rynek neutralny",
        "Greed": "chciwość",
        "Extreme Greed": "ekstremalna chciwość",
    }
    fng_pl = fng_pl_map.get(fng_classification, fng_classification.lower())
    months_since_halving = int((datetime.now() - HALVING_DATE).days / 30.4)
    if months_since_halving < 12:
        cycle_state = "cykl wciąż w fazie wzrostu"
    elif months_since_halving < 18:
        cycle_state = "cykl w dojrzałej fazie wzrostu"
    elif months_since_halving < 24:
        cycle_state = "cykl bliski historycznego szczytu"
    else:
        cycle_state = "cykl po szczycie historycznym"

    narrative = (
        f'<span class="coin-btc">BTC</span> <strong>{fmt_pct(btc_24h)}</strong>, '
        f'<span class="coin-bnb">BNB</span> <strong>{fmt_pct(bnb_24h)}</strong> w ostatnich 24h. '
        f'Fear &amp; Greed: <strong>{fng}</strong> ({fng_pl}). '
        f'{months_since_halving} {months_pl(months_since_halving)} po halvingu — {cycle_state}.'
    )

    btc_dom_pl = f"{btc_dom:.1f}".replace(".", ",")
    btc_narrative = (
        f'BTC <strong>{fmt_pct(btc_24h)}</strong> w 24h, <strong>{fmt_pct(btc_7d)}</strong> w 7d. '
        f'Wolumen <strong>{fmt_pct(btc_vol_vs_7d)}</strong> względem średniej z 7 dni. '
        f'Dominacja <strong>{btc_dom_pl}%</strong> rynku. '
        f'Fear &amp; Greed: <strong>{fng}</strong> ({fng_pl}).'
    )

    if bnb_vs_btc_7d > 1.5:
        ratio_phrase = "<strong>silniejszy od BTC</strong> w ostatnim tygodniu"
    elif bnb_vs_btc_7d < -1.5:
        ratio_phrase = "<strong>słabszy niż BTC</strong> w ostatnim tygodniu"
    else:
        ratio_phrase = "porusza się <strong>razem z BTC</strong> w ostatnim tygodniu"

    bnb_narrative = (
        f'BNB <strong>{fmt_pct(bnb_24h)}</strong> w 24h, <strong>{fmt_pct(bnb_7d)}</strong> w 7d. '
        f'Wolumen <strong>{fmt_pct(bnb_vol_vs_7d)}</strong> vs średnia tygodniowa. '
        f'BNB/BTC ratio <strong>{fmt_pct(bnb_vs_btc_7d)}</strong> w 7d — {ratio_phrase}.'
    )

    btc_vol_30d_avg = sum(btc_vols[-31:-1]) / 30 if len(btc_vols) >= 31 else btc_vol_7d_avg
    bnb_vol_30d_avg = sum(bnb_vols[-31:-1]) / 30 if len(bnb_vols) >= 31 else bnb_vol_7d_avg

    btc_forecast = build_forecast(btc_score, btc_prices, btc_vol, btc_vol_30d_avg, fng, months_since_halving)
    bnb_forecast = build_forecast(bnb_score, bnb_prices, bnb_vol, bnb_vol_30d_avg, fng, months_since_halving)

    history = load_history()
    btc_hist = push_score(history, "btc", btc_score)
    bnb_hist = push_score(history, "bnb", bnb_score)
    btc_dca_hist = push_dca(history, "btc_dca", btc_dca)
    bnb_dca_hist = push_dca(history, "bnb_dca", bnb_dca)

    btc_time = asset_time_block("btc", history, btc_24h, btc_7d, btc_30d, btc_90d, fng, cyc)
    bnb_time = asset_time_block("bnb", history, bnb_24h, bnb_7d, bnb_30d, bnb_90d, fng, cyc)

    now_local = datetime.now()
    header_label = f"{DAY_NAMES_PL[now_local.weekday()]}, {now_local.day} {MONTHS_PL[now_local.month - 1]}"

    data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "header_label": header_label,
        "narrative": narrative,
        "assets": [
            {
                "key": "btc",
                "name": "BTC",
                "sub": "Bitcoin",
                "score": btc_score,
                "delta": delta(btc_hist),
                "mood": mood_label(btc_score),
                "history": btc_hist,
                "price": fmt_price(btc_price),
                "price_change_24h": round(btc_24h, 1),
                "narrative": btc_narrative,
                "time": btc_time,
                "stats": [
                    {"label": "Cena", "value": fmt_price(btc_price),
                     "changes": [
                         {"tf": "24h", "val": round(btc_24h, 1)},
                         {"tf": "7d", "val": round(btc_7d, 1)},
                         {"tf": "30d", "val": round(btc_30d, 1)},
                     ]},
                    {"label": "Wolumen 24h", "value": fmt_volume(btc_vol), "change": round(btc_vol_vs_7d)},
                    {"label": "Dominacja", "value": f"{btc_dom:.1f}%".replace(".", ","), "change": None},
                ],
                "dca": {"decision": btc_dca, "history": btc_dca_hist},
                "forecast": btc_forecast,
            },
            {
                "key": "bnb",
                "name": "BNB",
                "sub": "Binance Coin",
                "score": bnb_score,
                "delta": delta(bnb_hist),
                "mood": mood_label(bnb_score),
                "history": bnb_hist,
                "price": fmt_price(bnb_price),
                "price_change_24h": round(bnb_24h, 1),
                "narrative": bnb_narrative,
                "time": bnb_time,
                "stats": [
                    {"label": "Cena", "value": fmt_price(bnb_price),
                     "changes": [
                         {"tf": "24h", "val": round(bnb_24h, 1)},
                         {"tf": "7d", "val": round(bnb_7d, 1)},
                         {"tf": "30d", "val": round(bnb_30d, 1)},
                     ]},
                    {"label": "Wolumen 24h", "value": fmt_volume(bnb_vol), "change": round(bnb_vol_vs_7d)},
                    {"label": "BNB / BTC",
                     "value": fmt_pct(bnb_vs_btc_7d),
                     "change": round(bnb_vs_btc_7d, 1), "changeUnit": "7d"},
                ],
                "dca": {"decision": bnb_dca, "history": bnb_dca_hist},
                "forecast": bnb_forecast,
            },
        ],
    }

    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2))

    print(f"BTC: {btc_score}/100 ({mood_label(btc_score)}), DCA: {btc_dca}")
    print(f"BNB: {bnb_score}/100 ({mood_label(bnb_score)}), DCA: {bnb_dca}")
    print(f"Wrote {DATA_FILE.name} and {HISTORY_FILE.name}")


if __name__ == "__main__":
    main()
