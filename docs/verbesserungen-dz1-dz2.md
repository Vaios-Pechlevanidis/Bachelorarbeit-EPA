# Verbesserungen für DZ1 und DZ2: Post-hoc-Prüfung

> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt. Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume nach dem Annotationsprotokoll (Abschnitt 3.6.1)

**Einordnung.** Alles hier ist **post hoc und explorativ**. Die DZ1-Auswertung vom 2026-10-10
(`backend/data/calibration/dz1_ergebnis.json`) und die DZ2-Bewertung vom 2026-10-17 bleiben die
Ergebnisse der Arbeit; keine bestehende Ergebnisdatei wurde geändert. Das Standardverhalten des
Dashboards ist unverändert (`weighting="none"`, Texte wie bisher).

## Kurzfassung

| Ziel | Befund | Hebel | Status |
|---|---|---|---|
| DZ1 Precision | Alle 9 Fehlalarme der Erkennung (annotierte Reihen) sind regelkonforme Kandidaten (6) oder Zweifelsfälle (3) des archivierten Regelprüfers; keiner ist ein Zeitraum ohne Kandidat. | Precision ist durch Regel 5 der Referenz (höchstens drei Zeiträume je Reihe) begrenzt, nicht durch die Erkennung. Gegen die Kandidatenmenge: Precision 72,7 %, F1 0,52 (statt 47,1 %, 0,43). | als Sensitivitätsanalyse berichtbar |
| DZ1 Recall | 12 verfehlte Zeiträume, fast alle einmonatig mit 5–12 Bewertungen mitten in der Reihe; keine Markierung in der Nähe. | Grenze der Daten und der Definition (Sprung eines Monats, Folgemonate nur zur Hälfte), nicht einfach durch das Verfahren zu heben. | erklärt |
| DZ1 Verfahren | Gewichtung der Monate nach Bewertungszahl (neu, Option) senkt semisynthetisch die Fehlalarme stark bei gleicher Trefferquote, verliert auf der Referenz aber Recall am Reihenanfang. | siehe Abschnitt DZ1 | Option, nicht Standard |
| DZ2 | Die strenge Artikelauswahl (nur Titel) unterscheidet Markierungs- von Vergleichsfenstern (50 % gegen 32 %, Cluster-Permutation p = 0,058; mittlere Stufe p = 0,049). Mit Artikeltexten (Standard seit 2026-10-25) verschwindet der Unterschied (57 % gegen 58 %, p = 1,0): Texte bringen 19 Vergleichs-, aber nur 2 Markierungsfenstern einen Ansatz. | Texte nicht für den Wortbezug nutzen (`EXPLANATION_TEXTS=0`), nur zur Anzeige; Bestätigung mit neuen blinden Urteilen. | Entscheidung des Autors |

## DZ1

### 1 Fehlalarme gegen die Kandidaten des Regelprüfers

`backend/scripts/dz1_posthoc.py` gleicht jede Markierung, die keinem Referenzzeitraum entspricht,
mit allen Zeiträumen ab, die der archivierte Regelprüfer (`docs/dz1-referenz/dz1_rechner.py`,
`scan`) als regelkonform oder Zweifelsfall ausgibt (gleiche Richtung, Fenster nach Regel 6).
Ergebnis (`backend/data/calibration/dz1_posthoc.md`):

| Bezug | TP | FP | davon regelkonformer Kandidat | davon Zweifelsfall | ohne Kandidat | Precision | Precision ohne Kandidaten-FP | F1 | F1 ohne Kandidaten-FP |
|---|---|---|---|---|---|---|---|---|---|
| annotierte Reihen | 8 | 9 | 6 | 3 | 0 | 47,1 % | 72,7 % | 0,432 | 0,516 |
| alle geeigneten Reihen | 8 | 11 | 6 | 4 | 1 | 42,1 % | 61,5 % | 0,410 | 0,485 |

Lesart: Die Erkennung markiert fast nur Stellen, die nach den Annotationsregeln selbst als
Niveauwechsel gelten würden. Dass sie als FP zählen, folgt aus der Auswahl der Referenz (Regel 5,
Setzung 4), nicht aus einem Fehlgriff der Erkennung. Für die Arbeit eignet sich das als
Sensitivitätsanalyse neben dem unveränderten Hauptwert (F1 0,43), ausdrücklich als nachträglich
gekennzeichnet.

### 2 Gewichtung nach Bewertungszahl (neue Option)

**Idee.** Bisher behandelt PELT jedes Monatsmittel gleich, obwohl ein Monat mit 5 Bewertungen
etwa dreimal so stark streut wie einer mit 50. Die neue Option `weighting="count"` gewichtet jeden
Monat mit `1/(τ² + s²/n)`:

- `s`: Streuung je Bewertung, gepoolt innerhalb der bewerteten Monate (`rating_series_service.review_sd`; in den 15 Reihen 0,69–1,19 Sterne);
- `τ`: echte Schwankung zwischen Monaten, robust aus den Monatsdifferenzen geschätzt (MAD; 0–0,45 Sterne);
- Kosten: gewichtete Quadratsumme, standardisiert; Strafterm `Faktor · ln(n)`, also dieselbe Form wie bisher (`2·σ²·ln(n)` in Einheiten der Varianz). Bei `τ` groß gegen `s²/n` geht das Verfahren in das bisherige über.

Code: `backend/models/changepoint_detector.py` (`between_month_sd`, `month_weights`,
`weighted_l2_cost`, `PeltDetector(weighting=...)`), Durchreichung in
`backend/services/anomaly_service.py` (`detect_anomalies`, `company_anomalies`, Stabilität).
Tests: `backend/tests/anomaly/test_weighted_detection.py`.

**Semisynthetisch** (`backend/scripts/compare_weighting.py`, gepaart auf denselben Ziehungen wie
`simulate_detection.py`; 15 Reihen × 200 Wiederholungen;
`backend/data/calibration/gewichtung_semisynthetisch.md`). Die ungewichtete Variante
reproduziert die Simulation vom 2026-10-13 bis auf die Dublettenbereinigung der Datenbank.

| Bedingung | Maß | ungewichtet | gewichtet (Faktor 2) |
|---|---|---|---|
| Bewertungen gemischt, ohne Wechsel | Reihen mit Fehlalarm | 19,2 % | 3,7 % |
| Monate gemischt, ohne Wechsel | Reihen mit Fehlalarm | 14,1 % | 11,2 % |
| Bewertungen gemischt, Δ 0,5, Mitte | Trefferquote | 58,1 % | 60,4 % |
| Bewertungen gemischt, Δ 0,5, Ende | Trefferquote | 42,3 % | 38,9 % |
| Monate gemischt, Δ 0,5, Mitte | Trefferquote | 40,5 % | 42,1 % |
| alle Bedingungen | weitere Markierungen je Reihe | 0,23–0,59 | 0,04–0,50 |

**An der Referenz (post hoc, nichts eingestellt):** F1 0,30 statt 0,43 (TP 5 statt 8). Verloren
gehen Telekom 2009-12 und 2010-07 sowie 1&1 2016-10: Wechsel am Reihenanfang in dünn belegten
Monaten, wo auch die Simulation einen Verlust zeigt (Lage Ende, Wechselmonat n < 10: 37,7 % →
28,2 % bei Δ 0,5). Die Fehlalarme, die die Gewichtung einspart, sind auf der Referenz fast alle
Kandidaten (siehe 1); ihr Vorteil zeigt sich dort deshalb nicht.

**Kalibrierung des Strafterms** (nur semisynthetisch, damit beide Varianten bei gleicher
Fehlalarmrate verglichen werden; ungewichtet immer Faktor 2; je 100 Wiederholungen,
`backend/data/calibration/gewichtung_kalibrierung/`):

| Faktor gewichtet | Fehlalarm Bewertungen gemischt (ungew. 18,3 %) | Treffer Δ 0,5 Mitte / Ende (ungew. 58,8 / 42,1 %) | Fehlalarm Monate gemischt (ungew. 14,5 %) | Treffer Δ 0,5 Monate (ungew. 42,0 %) |
|---|---|---|---|---|
| 1,0 | 33,3 % | 63,9 / 58,5 % | 49,2 % | 51,0 % |
| 1,25 | 19,0 % | 64,1 / 52,3 % | 34,9 % | 49,1 % |
| 1,5 | 11,1 % | 62,9 / 47,3 % | 23,9 % | 47,7 % |
| 2,0 (200 Wdh.) | 3,7 % | 60,4 / 38,9 % | 11,2 % | 42,1 % |

Bei reinem Stichprobenrauschen ist die Gewichtung bei gleicher Fehlalarmrate (Faktor 1,25) klar
besser (+5 bzw. +10 pp Trefferquote). Bleibt die echte Schwankung zwischen Monaten erhalten
(„Monate gemischt“, näher an den echten Reihen), steigen die Fehlalarme mit kleinerem Faktor steil
an, und der Gewinn an Treffern ist klein. Faktor 2 ist dort die einzige Einstellung ohne mehr
Fehlalarme.

**Bewertung.** Die Gewichtung macht die Erkennung robuster gegen dünn belegte Monate (weniger
Fehlalarme und Zusatzmarkierungen), hebt aber F1 gegen diese Referenz nicht, weil die Referenz
selbst auf ungewichteten Monatsmitteln definiert ist und viele Zeiträume in dünnen Monaten liegen.
Sie bleibt deshalb eine Option (`weighting="count"`), nicht der Standard. Für die Arbeit taugt sie
als Robustheitsprüfung: Welche Markierungen bleiben, wenn man die Bewertungszahl berücksichtigt?

### 3 Weitere Hebel für DZ1 (nicht umgesetzt)

- **Zweite Annotation:** Der Agent kennt den Modus `zweitperson`, `compare_annotations.py` und
  `blind_annotations.py` liegen bereit. Eine unabhängige zweite Referenz mit Übereinstimmungsmaß
  stärkt die Gültigkeit von DZ1 mehr als jede Änderung am Verfahren.
- **Neuer, vorab festgelegter Lauf:** Wer ein geändertes Verfahren als Ergebnis berichten will,
  legt es vorher fest (Parameter, Teilmengen) und wertet einmal gegen eine neue oder zweite
  Referenz aus; ein erneuter Abgleich mit denselben 20 Zeiträumen ist sonst Anpassung an die
  Referenz.

## DZ2

### 1 Teil A für die strenge Auswahl und für die Textfassung

`rate_explanations.py auswerten --validity …` (Cluster-Permutation, 20 000 Permutationen) auf die
vorhandenen Validitätsberichte; Ergebnisse in
`backend/data/calibration/explanation_validity_strict_teilA.md` und
`…_text_teilA.md`:

| Fassung | Markierungen mit Ansatz | Vergleichsfenster mit Ansatz | Differenz | p (Cluster-Permutation) | mittlere oberste Stufe M / V | p |
|---|---|---|---|---|---|---|
| bisher (2026-10-13, E23) | 23/28 (82 %) | 57/72 (79 %) | +3 pp | 0,755 | 1,46 / 1,31 | 0,389 |
| streng, nur Titel (2026-10-18, E33) | 14/28 (50 %) | 23/72 (32 %) | +18 pp | 0,058 | 1,07 / 0,67 | 0,049 |
| streng mit Texten (2026-10-25, Standard) | 16/28 (57 %) | 42/72 (58 %) | −1 pp | 1,000 | 1,32 / 1,38 | 0,837 |
| Kontrolle ohne Texte (2026-10-25) | 14/28 (50 %) | 23/72 (32 %) | +18 pp | 0,058 | 1,07 / 0,67 | 0,049 |

Fensterweise gegen die Kontrolle ohne Texte: Die Texte geben 19 Vergleichsfenstern und 2
Markierungsfenstern einen Ansatz, den sie ohne Texte nicht hätten. Lange Texte enthalten
kennzeichnende Begriffe der Bewertungen offenbar oft zufällig.

### 2 Passung der strengen Auswahl nach den vorhandenen Urteilen (zirkulär)

Wendet man `exclusion_reason` auf die 184 blinden Urteile vom 2026-10-17 an (oberster
verbleibender Ansatz je Fenster; kein Fenster unbestimmt):

| | Markierungen | Vergleichsfenster |
|---|---|---|
| bisher: oberster Ansatz passend (≥ 2), je Fenster mit Ansatz | 6/23 (26 %) | 17/57 (30 %) |
| streng: oberster Ansatz passend, je Fenster mit Ansatz | 7/14 (50 %) | 8/20 (40 %) |
| bisher: passender oberster Ansatz, alle Fenster | 6/28 (21 %) | 17/72 (24 %) |
| streng: passender oberster Ansatz, alle Fenster | 7/28 (25 %) | 8/72 (11 %) |

**Vorsicht:** Die Regeln der strengen Auswahl (Unternehmen im Titel, Themenbezug statt
Ereignisart allein) wurden am 2026-10-18 aus genau diesen Urteilen abgeleitet. Die Zahlen sind
deshalb optimistisch und nur ein Hinweis. Bestätigen lässt sich das nur mit neuen blinden Urteilen
(`rate_explanations.py bogen` auf der strengen Fassung, neuer Bewerter oder neue Fenster).

### 3 Empfehlung DZ2

1. Wortbezug wieder nur aus Titeln (`EXPLANATION_TEXTS=0` oder Standard in
   `services/evidence_text.texts_enabled` umstellen); Texte nur zur Anzeige. Das ist die vorab
   gerechnete Kontrollfassung vom 2026-10-25, also keine neue Anpassung.
2. Danach einmal neue blinde Urteile für die strenge Fassung erheben (Teil B) und mit
   2026-10-17 vergleichen.
3. Stufe und Belegmenge entkoppeln: Die Stufe folgt bisher der Zahl der Belege (Spearman 0,40).
   Ein Ansatz sollte im Verhältnis zur üblichen Meldungslage des Unternehmens bewertet werden
   (Häufung im Fenster gegen die Vergleichsfenster), nicht absolut. Nicht umgesetzt.

## Nachvollziehen

```bash
cd backend
.venv/bin/python -m pytest -q tests/anomaly/test_weighted_detection.py
.venv/bin/python scripts/compare_weighting.py --reps 200 --workers 8 --json data/calibration/gewichtung_semisynthetisch.json --md data/calibration/gewichtung_semisynthetisch.md
.venv/bin/python scripts/compare_weighting.py --reps 100 --workers 8 --weighted-factor 1.25
.venv/bin/python scripts/dz1_posthoc.py --json data/calibration/dz1_posthoc.json --md data/calibration/dz1_posthoc.md
.venv/bin/python scripts/rate_explanations.py auswerten --validity data/calibration/explanation_validity_strict_2026-10-18.json
```

`compare_weighting.py` und `dz1_posthoc.py` lesen Bewertungen aus der Datenbank (nur SELECT);
mit `--rows <cache.json>` aus einem lokalen Zwischenspeicher. Die abgelegten Läufe nutzten
einen solchen Zwischenspeicher derselben Datenbank (nicht versioniert).
