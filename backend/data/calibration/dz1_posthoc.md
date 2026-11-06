> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.

# DZ1 post hoc: Gewichtung nach Bewertungszahl und Fehlalarme gegen Regelkandidaten

Post hoc und explorativ: Die DZ1-Auswertung vom 2026-10-10 (dz1_ergebnis.json) bleibt das Ergebnis der Arbeit. Die gewichtete Variante wurde vor diesem Abgleich festgelegt (Strafterm-Faktor, min_size, min_delta unverändert) und zuerst semisynthetisch geprüft; hier wird nichts an der Referenz eingestellt. Die Kandidaten stammen aus dem archivierten Regelprüfer (scan) und sind regelkonforme Zeiträume, die nicht in der Referenz stehen, z. B. wegen Regel 5 (höchstens drei je Reihe).

Prüfung: ungewichtete Variante aus den Serien-CSVs gleich dz1_ergebnis.json (TP/FP/FN je annotierter Reihe): ja.

**Annotierte Reihen (wie DZ1-Hauptwert)**

| Variante | TP | FP | FN | Precision | Recall | F1 | FP = regelkonformer Kandidat | FP = Zweifelsfall | FP ohne Kandidat | Precision ohne Kandidaten-FP | F1 ohne Kandidaten-FP |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ungewichtet (DZ1) | 8 | 9 | 12 | 47,1 % | 40,0 % | 0,432 | 6 | 3 | 0 | 72,7 % | 0,516 |
| gewichtet | 5 | 8 | 15 | 38,5 % | 25,0 % | 0,303 | 6 | 2 | 0 | 71,4 % | 0,370 |

**Alle geeigneten Reihen (Markierungen in Reihen ohne Eintrag zählen als FP)**

| Variante | TP | FP | FN | Precision | Recall | F1 | FP = regelkonformer Kandidat | FP = Zweifelsfall | FP ohne Kandidat | Precision ohne Kandidaten-FP | F1 ohne Kandidaten-FP |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ungewichtet (DZ1) | 8 | 11 | 12 | 42,1 % | 40,0 % | 0,410 | 6 | 4 | 1 | 61,5 % | 0,485 |
| gewichtet | 5 | 10 | 15 | 33,3 % | 25,0 % | 0,286 | 6 | 2 | 2 | 55,6 % | 0,345 |

Gepaart je Referenzzeitraum (20): beide finden 5, nur ungewichtet 3, nur gewichtet 0, keine 12.

**Je Reihe**

| Reihe | Einträge | s je Bewertung | ungewichtet TP/FP/FN | gewichtet TP/FP/FN | gewichtet: Markierungen |
|---|---|---|---|---|---|
| Thyssenkrupp | 0 | 1,021 | 0/0/0 | 0/0/0 | – |
| Open Grid Europe | 0 | 0,689 | 0/0/0 | 0/0/0 | – |
| E.ON | 0 | 0,914 | 0/1/0 | 0/1/0 | 2024-03 rise (kein_kandidat) |
| RWE | 0 | 0,910 | 0/1/0 | 0/1/0 | 2018-08 rise (kein_kandidat) |
| Karlsruher Institut für Technologie | 0 | 0,884 | 0/0/0 | 0/0/0 | – |
| Technische Universität München | 0 | 0,864 | 0/0/0 | 0/0/0 | – |
| SAP SE | 1 | 0,892 | 1/0/0 | 1/0/0 | 2024-08 rise (TP) |
| NTT DATA SE | 1 | 1,188 | 1/3/0 | 1/1/0 | 2019-07 fall (regelkonformer_kandidat), 2020-06 rise (TP) |
| 1&1 AG | 3 | 1,089 | 1/0/2 | 0/2/3 | 2019-12 fall (regelkonformer_kandidat), 2023-10 rise (zweifelsfall) |
| Bechtle | 3 | 1,146 | 0/1/3 | 0/1/3 | 2016-02 rise (regelkonformer_kandidat) |
| Cancom | 3 | 1,140 | 0/0/3 | 0/0/3 | – |
| Carl Zeiss | 0 | 0,872 | 0/0/0 | 0/0/0 | – |
| Compugroup Medical Deutschland | 3 | 1,105 | 1/0/2 | 1/0/2 | 2022-08 fall (TP) |
| Telekom | 3 | 0,950 | 2/2/1 | 0/1/3 | 2019-04 rise (regelkonformer_kandidat) |
| Freenet | 3 | 0,990 | 2/3/1 | 2/3/1 | 2015-10 fall (regelkonformer_kandidat), 2016-04 rise (TP), 2019-10 rise (regelkonformer_kandidat), 2021-09 fall (TP), 2022-02 rise (zweifelsfall) |
