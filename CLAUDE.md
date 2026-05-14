# CryptoBeacon — kontekst projektu

> Ten plik czytany jest automatycznie przy starcie Claude Code w tym katalogu. Zawiera ustalenia i decyzje z rozmowy planistycznej, której nie ma już w pamięci konwersacji.

---

## Co to jest

**CryptoBeacon** to osobiste narzędzie do codziennej obserwacji „mgły" rynku krypto — pomoc w budowaniu intuicji o nastroju rynku, **nie** silnik predykcyjny. Generuje statyczny HTML dashboard aktualizowany 3× dziennie (rano / południe / wieczór).

Filozofia: rynek jest w dużej mierze efektywny i krótkoterminowo emocjonalny, więc nie próbujemy go „przewidywać". Zamiast tego pokazujemy **sentyment w warstwach czasowych**, żeby użytkownik mógł sam wyrobić sobie wyczucie.

## Użytkownik

- Średnio zaawansowany w krypto, **nie trader**
- Strategia: **DCA ~$100/miesiąc** w BTC i BNB
- Operuje na Binance (Binance jako benchmark cenowy — w pełni akceptowalne dla jego trybu)
- Teza w BNB: to asset oparty na **realnej działającej firmie**, więc jego fundamenty (wolumeny Binance, burny, regulacje) realnie wpływają na cenę. Daje więcej fundamentalnego oparcia niż większość altów, ale ma skoncentrowane ryzyko regulacyjne.

## Stan obecny — etap 1 ukończony (2026-05-11)

- `index.html` — statyczny HTML, **fetchuje `data.json`** przy ładowaniu i renderuje wszystko dynamicznie
- `fetch.py` — Python skrypt (stdlib only) który ściąga dane z CoinGecko + alternative.me, liczy score'y rules-based, generuje narrative-template, zapisuje `data.json` + dorzuca do `history.json`
- `data.json` — aktualny snapshot rynku (przepisywany przy każdym refreshu)
- `history.json` — historia score'ów dla sparklinów (rolling last 7) + 30-dniowy strip DCA
- `.github/workflows/refresh.yml` — GitHub Actions cron 3× dziennie (06:00/12:00/19:00 UTC = 8:00/14:00/21:00 PT letni). Cron uruchamia fetch.py → commit data.json+history.json → Vercel auto-deploy
- `colors.md` — pełna paleta kolorów + uzasadnienie + CSS variables

**Co dalej**: etap 2 (Claude API zamiast prostych reguł scoringu + bogatsza narracja). Patrz "Plan etapów".

## Decyzje produktowe — zatwierdzone

### Co pokazujemy
- **Sentyment w warstwach czasowych**: Dziś (24h) · Tydzień · Miesiąc · Kwartał · Cykl (od halvingu)
- **Aktywa**: BTC i BNB osobno, każde z 3 surowymi metrykami (cena, wolumen 24h, dominacja/BNB-BTC ratio)
- **Hero**: agregowany sentyment dnia + 2-zdaniowa narracja „co się dzieje"
- **DCA na dziś**: jednolinijkowa rekomendacja zakupowa
- **Wydarzenia z 24h**: top newsy z tagami (Binance / Regulacje / Makro / On-chain)
- **Panel szczegółów**: po kliknięciu komórki — rozbicie wyniku na wymiary (cena, wolumen) + krótki komentarz „dlaczego"

### Skala sentymentu
- **0–100**, jeden wynik per komórka (nie split na wymiary)
- Mood labele: Krew / Wyprzedaż / Słabość / Spokój / Wzmocnienie / Siła / Hossa / Mocna hossa / Mania
- **Delta** względem poprzedniego okresu (dla 24h vs wczoraj, dla 7d vs tydzień temu, itd.)
- Sparkline z ostatnich 7 odświeżeń w każdej komórce

### Czego świadomie nie pokazujemy
- Dominacji BTC jako głównego wymiaru (zrzucone do detali, drugorzędny sygnał dla DCA)
- Funding rates / MVRV / Pi Cycle na pierwszym widoku (advanced, w detalach po kliknięciu)
- **Predykcji cenowych — nigdy**. Nie liczymy, nie pokazujemy, nie sugerujemy konkretnych target-prices.
- Sygnałów typu „buy/sell" intraday

### Co pokazujemy z przyszłości (od 2026-05-13)
- **Forecast pasma sentymentu w 7d** — rules-based, transparentny, z explicit konwikcją (low/medium/high). To NIE predykcja ceny, tylko probabilistyczna ekstrapolacja widocznego setupu (volume confirmation, mean reversion, momentum streak, cykl).
- Zasady: zawsze pasmo (nie pojedynczy punkt), zawsze z konwikcją, zawsze z rozbiciem regła-po-regle na detalu, zawsze z disclaimerem.
- Szczegóły implementacji w `design.md` → sekcja "Rules-based forecast".

## Konwencje UI/UX — z uzasadnieniem

> **Naczelna zasada estetyki: iOS.** Pełna specyfikacja w `design.md` (cards, hairlines vs gap, typografia, animacje). Każda zmiana UI musi być z tym zgodna.
>
> **Why:** te zasady wynikają z konkretnych iteracji w rozmowie. Nie zmieniaj ich bez ponownego pytania.
> **How to apply:** każde nowe miejsce/element musi się tych zasad trzymać.

- **„Spokój" = szary, nie żółty/amber.** Konwencja Fear & Greed Index jest semantycznie błędna — żółty komunikuje „ostrzeżenie", nie „brak emocji". Środek skali (45–55) to neutralny slate gray.
- **Brak kolorowych pasków po lewej** w komórkach i blokach detali. Wynik liczbowy jest pofarbowany sam — to wystarczy.
- **Strzałka delty obok wielkiej liczby** (nie przy etykiecie). Wcześniej próbowaliśmy umieszczać ją przy labelu — testowo wróciliśmy, ale po stronie użytkownika lepiej się czyta gdy jest tuż obok wyniku. Strzałka w kolorze wyniku (`--cell-color`), nie w klasycznym czerwono-zielonym — kierunek niesie sam symbol ↑↓.
- **Hero w tym samym stylu co komórki**, tylko większy. Bez okrągłych dialów / wskazówek — to nie jest gauge. Spójność wizualna z resztą. Hero też ma własny sparkline (większy, ~44px wysokości).
- **Sparkline w każdej komórce** — ostatnie 7 odświeżeń, cienka linia w kolorze sentymentu, z kropką na ostatnim punkcie. Daje kontekst „trendu" bez konieczności klikania.
- **Nagłówek strony minimalistyczny**: brand „CRYPTO BEACON" po lewej, **tylko data** po prawej. Bez „ostatnia aktualizacja / kolejna", bez info o cyklu (cykl ma własną komórkę w siatce czasu).
- **Sekcje mają jednozdaniowy podtytuł** wyjaśniający kontekst. Użytkownik nie jest tradera, każdy techniczny termin (np. „Aktywa") wymaga krótkiego doprecyzowania.
- **Sekcja Aktywa to wiersz: kafelek wyniku + 3 stat blocki** (Cena, Wolumen, vs rynek). Nie szerokie 2 komórki obok siebie — to wyglądało niezbalansowane vs siatka czasu.
- **Pomost decyzyjny „DCA na dziś"** pod hero — 1-zdaniowa synteza danych → rekomendacja. Bez tego użytkownik czyta liczby, ale nie wie *co z tego*. Skrót DCA = Dollar-Cost Averaging (stała kwota w regularnych odstępach).
- **Hero narracja** ma nagłówek „Co się dzieje", **nie** powtórzony mood label — żeby uniknąć redundancji „Lekkie osłabienie" pojawiające się dwa razy.
- **Brak emoji** w UI (z wyjątkiem strzałek ↑ ↓ →). Jednoznaczne, profesjonalne.
- **Font: Helvetica Neue** (fallback: Helvetica, Arial, system fonts). Daje neutralny, klasyczny charakter zamiast „bardzo nowoczesnego" SF Pro.

## Architektura techniczna

**Stack:**
- Python 3.10+ (instalacja przez `uv` jeśli brakuje)
- SQLite (przechowywanie historii odświeżeń + cache surowych danych)
- Claude API (`claude-opus-4-7` lub `claude-sonnet-4-6` — sonnet wystarczy do tego zadania, taniej)
- Statyczny HTML generowany ze skryptu (jeden plik, otwierasz lokalnie z zakładki)
- `launchd` na Macu — odpalanie 3× dziennie

**Workflow każdego odświeżenia:**
1. Skrypt Python ściąga surowe dane z darmowych API (cena, wolumen, on-chain, RSS)
2. Liczy podstawowe metryki regułami (delty, średnie, ratio)
3. Wysyła do Claude API: surowe dane + ich kontekst historyczny → otrzymuje (a) score 0–100 per komórka, (b) mood label, (c) krótki komentarz, (d) syntezę „co się dzieje" dla hero, (e) DCA bridge
4. Renderuje HTML z szablonu (Jinja2 albo proste f-stringi)
5. Zapisuje aktualny stan + dodaje wpis do historii (sparkline = ostatnie 7 odświeżeń)

**Koszt:** ~$1–2/miesiąc API (3× dziennie × ~3k tokens/refresh).

## Źródła danych — zweryfikowane 2026-05-11

> Status każdego źródła sprawdzony bezpośrednim HTTP probe. Dostępność i pricing API się zmieniają — przy starcie etapu 1 zrobić quick re-check.

### Działa darmowo, bez klucza

| Źródło | Endpoint | Co | Notes |
|---|---|---|---|
| **Binance Spot** | `api.binance.com/api/v3/ticker/24hr` | Ceny BTC/BNB, wolumeny 24h | Public, bez rejestracji |
| **Binance Futures** | `fapi.binance.com/fapi/v1/premiumIndex` | Funding rates, premium index | Public, bez rejestracji |
| **CoinGecko global** | `api.coingecko.com/api/v3/global` | Dominacja BTC (`market_cap_percentage.btc`), total market cap | Bez klucza. Rate limit OK do naszego use case (3×/dzień) |
| **alternative.me** | `api.alternative.me/fng/?limit=1` | Fear & Greed Index | Bez klucza. **NIE z CoinGecko** (poprzedni plan się mylił) |
| **mempool.space** | `mempool.space/api/...` | BTC on-chain: bloki, mempool, address stats | Bez klucza. Dla "wpłat na Binance" potrzebujemy własnej listy adresów (patrz "Co zamiast Arkham") |
| **CoinDesk RSS** | `coindesk.com/arc/outboundfeeds/rss?outputType=xml` | Newsy, regulacje | Bez slash przed `?` (poprzedni URL → 308 redirect) |
| **CoinTelegraph RSS** | `cointelegraph.com/rss` | Newsy, listings | Standardowy RSS |
| **Binance Announcements** | `binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=10` | Listings, burns, regulacje | **Nie RSS** — JSON od wewnętrznego CMS Binance (nieoficjalne, stabilne; jeśli zmienią CMS, padnie) |

### Wymagało zmiany strategii (poprzedni plan był nierealny)

| Co chcieliśmy | Czemu nie działa | Co zamiast |
|---|---|---|
| **BscScan API** dla BNB on-chain | V1 deprecated; Etherscan V2 multichain dla BSC wymaga paid plan (`"Free API access is not supported for this chain"`) | **BSC RPC** bezpośrednio: `bsc-dataseed.binance.org` (darmowe, JSON-RPC, bez klucza). Wymaga pracy nad `eth_call`/`getLogs`. Albo MVP-cięcie: BNB on-chain ograniczony do tego co da się wyciągnąć z Binance API |
| **Whale Alert** dla dużych transakcji | Free tier wymaga klucza + 10 req/min + ostatnia 1h + min $500k. Twitter feed za paywallem od 2023 | Dla BTC: własna logika nad mempool.space — filtr transakcji na/z hardcoded listy adresów Binance, próg np. >100 BTC. Dla BNB: w MVP pomijamy |
| **Arkham Intelligence** dla etykiet portfeli | Web UI nie ma stabilnego endpointu; API wymaga paid plan | **Hardcoded lista** znanych Binance hot/cold wallets (~15–20 publicznie udokumentowanych adresów, np. `34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo`) |

### Świadomie pominięte

- **Glassnode / CryptoQuant** — płatne, niepotrzebne dla naszej skali
- **Płatne API sentymentu z Twittera** — szumne, mało wartościowe
- **Whale Alert paid (~$50/mc)** — sztywne limity, niewart kosztu vs własna logika na mempool.space
- **Arkham paid** — jw., własna lista wystarczy

## Plan etapów

> **Zasada projektu (decyzja 2026-05-14):** zero płatnych API. Trzymamy się darmowych źródeł i rules-based logiki. Etap 2 (LLM) został odrzucony.

1. ✅ **MVP** — ceny + wolumeny z CoinGecko → reguły scoring → dynamiczne dane w HTML. **Ukończone 2026-05-11.** Binance API porzucone (HTTP 451 z GitHub Actions); CoinGecko działa globalnie. GitHub Actions cron — od 2026-05-14 lecimy co 1h zamiast 3×/dzień.
2. ⚙️ **Etap 1.5 — wzmocnienie MVP** (ukończone 2026-05-14):
   - Restruktura UI: 2 widgety BTC/BNB hairline-połączone, detail pages jako iOS modal sheet (drag handle, blur Material, slide-up), forecast 7d rules-based z 4 regułami (volume/mean-reversion/momentum/cykl), DCA per-asset (Dziś / Za 7 dni), header z czasem ostatniej aktualizacji.
3. ❌ **Sentyment z Claude API** — **ODRZUCONE 2026-05-14**. Zostajemy na rules-based scoring + template narrative. Powód: użytkownik nie chce płacić za API. Patrz [[feedback_no_paid_apis]].
4. ⬜ **On-chain BTC/BNB** — net flows do Binance (mempool.space + hardcoded lista wallet'ów Binance), aktywność BSC przez BSC RPC. Darmowe źródła. Mini-placeholder „Niebawem: on-chain" już teaserowany na detalach.
5. ⬜ **Newsy i wydarzenia** — RSS (CoinDesk + CoinTelegraph) + Binance announcements JSON. **Bez LLM streszczeń** — tylko surowe nagłówki + link out, albo template-based brief. Mini-placeholder „Niebawem: newsy" już teaserowany.
6. ⬜ **Alerty zdarzeniowe** (opcjonalne) — Telegram bot (darmowy) push przy progowych zmianach.

## Otwarte — do potwierdzenia z użytkownikiem przed startem etapu 1

- Klucz API Claude (`console.anthropic.com` → załóż konto, dodaj $5 → starczy na 3+ miesiące). Potrzebny dopiero w etapie 2.
- Python 3.10+ na Macu — sprawdzić przy starcie, jeśli brak → instalacja przez `uv`.
- Konkretne godziny odświeżeń — domyślnie proponowane 8:00 / 14:00 / 21:00.

## Nazwa, branding

- Nazwa: **CryptoBeacon** (wybrana ze ścieżki Foglight → Mgielnik → Beacon → CryptoBeacon)
- Brand color: `#c4a878` (złoto-piaskowy, motyw latarni)
- Paleta: patrz `colors.md` (kompletna z uzasadnieniem)

---

**Kiedy ktokolwiek startuje Claude Code w tym katalogu:** przeczytaj ten plik + `colors.md` + `index.html` i wskocz w rozmowę zakładając, że plan jest zatwierdzony, czekamy na zielone światło użytkownika do startu etapu 1.
