# Crypto Beacon — paleta kolorów

Pełna paleta używana w mockupie dashboardu. Podzielona na warstwy: brand, UI/tło, skala sentymentu, wskaźniki zmian.

---

## Brand & akcent

| Rola | Hex | Opis |
|---|---|---|
| **Accent / Brand** | `#c4a878` | Złoto-piaskowy — tytuł "CRYPTO BEACON", etykieta DCA, tag Binance. Charakter: latarnia, ciepło, dyskretny luksus |

## Tło i karty (dark mode)

| Rola | Hex | Opis |
|---|---|---|
| Background page | `#0d1117` | Tło strony |
| Background soft | `#11161f` | Lekkie wyróżnienie (panel detali) |
| Panel | `#161c27` | Tło kart i komórek |
| Panel deeper | `#1c2330` | Wewnętrzne karty (np. dla `dim`) |
| Border | `#232b3a` | Obramowania, linie podziału |

## Typografia

| Rola | Hex | Opis |
|---|---|---|
| Tekst główny | `#e6e9ef` | Domyślny kolor tekstu |
| Tekst osłabiony | `#8a93a6` | Etykiety sekcji, drugi plan |
| Tekst najsłabszy | `#6b7385` | Referencje, najmniej ważne metadane |

---

## Skala sentymentu (0–100)

Od paniki (czerwień) przez spokój (szary) do euforii (zieleń). Szary w środku to **świadoma decyzja** — neutralność nie powinna być żółta/oliwkowa, bo to sugeruje ostrzeżenie. Pomarańcz i limonka jako „przedmuchy" wokół neutrum.

| Score | Hex | Znaczenie | Mood label |
|---|---|---|---|
| 0   | `#dc2626` | Najniższy — głęboka panika | Krew / kapitulacja |
| 15  | `#ef4444` | Mocny strach | Wyprzedaż |
| 30  | `#f97316` | Negatyw, ostrzeżenie | Słabość / niepokój |
| 45  | `#9ca3af` | **Neutrum** | Spokój |
| 55  | `#84cc16` | Wczesny pozytyw | Wzmocnienie |
| 65  | `#4ade80` | Pozytyw | Siła |
| 75  | `#22c55e` | Mocny pozytyw | Hossa |
| 85  | `#16a34a` | Bardzo silny pozytyw | Mocna hossa |
| 100 | `#15803d` | Najwyższy — euforia | Mania |

## Wskaźniki zmian (delta — strzałki, % zmian)

| Rola | Hex |
|---|---|
| Pozytywna zmiana | `#22c55e` (lub `#4ade80` w pillach) |
| Negatywna zmiana | `#ef4444` (lub `#f87171` w pillach) |
| Bez zmian | `#6b7385` (szary) |

---

## Charakter / mood-board

- **Dominacja**: ciemne, przygaszone tła (`#0d1117` → `#161c27`)
- **Akcent**: ciepły, dyskretny złoto-piaskowy (`#c4a878`) — pojawia się rzadko, podkreśla istotne elementy
- **Skala**: pełny gradient czerwień → szary → zieleń, bez „kwaśnych" oliwek w środku
- **Niska saturacja** w warstwie UI/tła; **wysoka i bezpośrednia** w wskaźnikach i wynikach
- **Inspiracja**: latarnia morska, mgła, terminale finansowe (Bloomberg, Linear, Vercel)

---

## CSS variables (do skopiowania)

```css
:root {
  /* Brand */
  --accent: #c4a878;

  /* Surfaces */
  --bg: #0d1117;
  --bg-soft: #11161f;
  --panel: #161c27;
  --panel-2: #1c2330;
  --border: #232b3a;

  /* Text */
  --text: #e6e9ef;
  --muted: #8a93a6;
  --muted-2: #6b7385;

  /* Sentiment scale 0–100 */
  --c-0:   #dc2626;
  --c-15:  #ef4444;
  --c-30:  #f97316;
  --c-45:  #9ca3af;
  --c-55:  #84cc16;
  --c-65:  #4ade80;
  --c-75:  #22c55e;
  --c-85:  #16a34a;
  --c-100: #15803d;

  /* Change indicators */
  --pos: #22c55e;
  --neg: #ef4444;
}
```
