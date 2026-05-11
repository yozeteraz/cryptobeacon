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

## Stan obecny

- `mockup.html` — statyczny HTML z dummy data, demonstrujący docelowy UI
- `colors.md` — pełna paleta kolorów + uzasadnienie + CSS variables
- **Implementacja jeszcze nie rozpoczęta** — to ostatni krok przed etapem 1 (zbudowanie skryptu Python który zasili HTML prawdziwymi danymi)

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
- Predykcji cenowych — **nigdy**
- Sygnałów typu „buy/sell" intraday

## Konwencje UI/UX — z uzasadnieniem

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

## Źródła danych — zatwierdzone, wszystkie darmowe

| Źródło | Co | Notes |
|---|---|---|
| Binance API (spot + futures) | Ceny BTC/BNB, wolumeny, funding rates, open interest | Główne źródło, bez rejestracji do public endpoints |
| CoinGecko API | Dominacja BTC, kapitalizacja rynku, Fear & Greed | Free tier wystarczy |
| mempool.space | BTC on-chain, transakcje, mempool | Dla BTC napływów na giełdy |
| BscScan API | BNB Chain — transakcje, gas, aktywność | Dla BNB on-chain |
| Whale Alert | Duże transakcje BTC/BNB | Free tier (Twitter/RSS feed) |
| Arkham Intelligence | Etykiety portfeli (które należą do Binance) | Free konto |
| RSS: Binance Announcements + CoinDesk + CoinTelegraph | Newsy, listings, regulacje | Standardowe RSS |

**Pominięte świadomie:**
- Glassnode / CryptoQuant (płatne, niepotrzebne dla naszej skali)
- Płatne API sentymentu z Twittera (szumne, mało wartościowe)

## Plan etapów

1. **MVP** — minimalne: ceny + wolumeny z Binance API → proste reguły scoring → statyczny HTML. Bez Claude API jeszcze. Daje wizualnie prawdziwy dashboard z prawdziwymi liczbami.
2. **Sentyment z Claude API** — call do API z surowymi danymi, otrzymujemy score + label + komentarz + narrację. *Wymaga klucza API z console.anthropic.com.*
3. **On-chain BTC/BNB** — net flows do Binance, funding rates, Coinbase Premium, aktywność BSC. Wszystko w detalach komórek aktywów.
4. **Newsy i wydarzenia** — RSS + LLM streszcza top 4–6 z 24h.
5. **Automatyzacja** — `launchd` plist, odpalanie 3× dziennie, ikona w doku (opcjonalnie macOS notification po każdym odświeżeniu).
6. **Alerty zdarzeniowe** (opcjonalne) — Telegram push przy progowych zmianach (funding, MVRV, duży news regulacyjny).

## Otwarte — do potwierdzenia z użytkownikiem przed startem etapu 1

- Klucz API Claude (`console.anthropic.com` → załóż konto, dodaj $5 → starczy na 3+ miesiące). Potrzebny dopiero w etapie 2.
- Python 3.10+ na Macu — sprawdzić przy starcie, jeśli brak → instalacja przez `uv`.
- Konkretne godziny odświeżeń — domyślnie proponowane 8:00 / 14:00 / 21:00.

## Nazwa, branding

- Nazwa: **CryptoBeacon** (wybrana ze ścieżki Foglight → Mgielnik → Beacon → CryptoBeacon)
- Brand color: `#c4a878` (złoto-piaskowy, motyw latarni)
- Paleta: patrz `colors.md` (kompletna z uzasadnieniem)

---

**Kiedy ktokolwiek startuje Claude Code w tym katalogu:** przeczytaj ten plik + `colors.md` + `mockup.html` i wskocz w rozmowę zakładając, że plan jest zatwierdzony, czekamy na zielone światło użytkownika do startu etapu 1.
