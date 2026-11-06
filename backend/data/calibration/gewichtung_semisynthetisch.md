> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.

# Gewichtung nach Bewertungszahl: semisynthetischer Vergleich (DZ1)

15 Reihen × 200 Wiederholungen, Startwert 20261013; Strafterm-Faktor gewichtet 2, ungewichtet 2. Gepaart: beide Varianten auf denselben Reihen, Wechseln und Richtungen.

| Bedingung | Lage | Δ | Maß | ungewichtet | gewichtet | Differenz (pp) | 95 %-Intervall (Cluster-Bootstrap) | nur ungew. / nur gew. | p (Vorzeichen) | weitere Markierungen je Reihe ungew. / gew. |
|---|---|---|---|---|---|---|---|---|---|---|
| bewertungen | mitte | 0 | Anteil Reihen mit Fehlalarm | 19,2 % | 3,7 % | -15,5 | [-21,3; -11,6] | 476 / 11 | < 0,001 | 0,35 / 0,04 |
| bewertungen | mitte | 0,3 | Trefferquote | 23,5 % | 22,3 % | -1,2 | [-3,1; +0,5] | 182 / 146 | 0,053 | 0,58 / 0,29 |
| bewertungen | mitte | 0,5 | Trefferquote | 58,1 % | 60,4 % | +2,4 | [+0,3; +4,3] | 117 / 188 | < 0,001 | 0,59 / 0,32 |
| bewertungen | mitte | 0,75 | Trefferquote | 81,1 % | 82,9 % | +1,8 | [+0,9; +2,8] | 49 / 103 | < 0,001 | 0,47 / 0,20 |
| bewertungen | mitte | 1 | Trefferquote | 91,6 % | 92,4 % | +0,8 | [+0,5; +1,2] | 26 / 50 | 0,008 | 0,38 / 0,12 |
| bewertungen | ende | 0 | Anteil Reihen mit Fehlalarm | 19,2 % | 3,7 % | -15,5 | [-21,2; -11,6] | 476 / 11 | < 0,001 | 0,34 / 0,04 |
| bewertungen | ende | 0,3 | Trefferquote | 15,5 % | 12,8 % | -2,7 | [-5,3; +0,1] | 162 / 82 | < 0,001 | 0,38 / 0,08 |
| bewertungen | ende | 0,5 | Trefferquote | 42,3 % | 38,9 % | -3,4 | [-7,2; +0,6] | 227 / 125 | < 0,001 | 0,41 / 0,13 |
| bewertungen | ende | 0,75 | Trefferquote | 74,0 % | 72,8 % | -1,2 | [-3,8; +1,4] | 122 / 87 | 0,018 | 0,39 / 0,13 |
| bewertungen | ende | 1 | Trefferquote | 89,6 % | 89,2 % | -0,4 | [-1,6; +0,7] | 50 / 37 | 0,198 | 0,35 / 0,09 |
| monate | mitte | 0 | Anteil Reihen mit Fehlalarm | 14,1 % | 11,2 % | -2,9 | [-6,2; +0,2] | 153 / 66 | < 0,001 | 0,23 / 0,19 |
| monate | mitte | 0,3 | Trefferquote | 14,7 % | 14,4 % | -0,3 | [-1,6; +0,9] | 84 / 75 | 0,526 | 0,47 / 0,42 |
| monate | mitte | 0,5 | Trefferquote | 40,5 % | 42,1 % | +1,5 | [-0,1; +3,4] | 114 / 160 | 0,006 | 0,57 / 0,50 |
| monate | mitte | 0,75 | Trefferquote | 70,8 % | 71,3 % | +0,5 | [-0,6; +1,7] | 77 / 93 | 0,250 | 0,44 / 0,39 |
| monate | mitte | 1 | Trefferquote | 86,8 % | 86,8 % | -0,0 | [-0,8; +0,6] | 48 / 47 | 1,000 | 0,32 / 0,28 |

**Trefferquote nach Belegung des Wechselmonats**

| Bedingung | Lage | Δ | Wechselmonat | Wiederholungen | ungewichtet | gewichtet |
|---|---|---|---|---|---|---|
| bewertungen | mitte | 0.3 | n<10 | 1814 | 22,8 % | 19,5 % |
| bewertungen | mitte | 0.3 | n>=10 | 1186 | 24,6 % | 26,6 % |
| bewertungen | mitte | 0.5 | n<10 | 1814 | 53,2 % | 53,2 % |
| bewertungen | mitte | 0.5 | n>=10 | 1186 | 65,4 % | 71,5 % |
| bewertungen | mitte | 0.75 | n<10 | 1814 | 77,1 % | 77,8 % |
| bewertungen | mitte | 0.75 | n>=10 | 1186 | 87,2 % | 90,6 % |
| bewertungen | mitte | 1 | n<10 | 1814 | 88,9 % | 89,1 % |
| bewertungen | mitte | 1 | n>=10 | 1186 | 95,6 % | 97,3 % |
| bewertungen | ende | 0.3 | n<10 | 1459 | 14,9 % | 8,4 % |
| bewertungen | ende | 0.3 | n>=10 | 1541 | 16,0 % | 16,9 % |
| bewertungen | ende | 0.5 | n<10 | 1459 | 37,7 % | 28,2 % |
| bewertungen | ende | 0.5 | n>=10 | 1541 | 46,7 % | 49,1 % |
| bewertungen | ende | 0.75 | n<10 | 1459 | 67,8 % | 63,5 % |
| bewertungen | ende | 0.75 | n>=10 | 1541 | 79,8 % | 81,6 % |
| bewertungen | ende | 1 | n<10 | 1459 | 86,4 % | 84,6 % |
| bewertungen | ende | 1 | n>=10 | 1541 | 92,7 % | 93,6 % |
| monate | mitte | 0.3 | n<10 | 1782 | 14,6 % | 13,4 % |
| monate | mitte | 0.3 | n>=10 | 1218 | 14,9 % | 15,8 % |
| monate | mitte | 0.5 | n<10 | 1782 | 40,2 % | 40,0 % |
| monate | mitte | 0.5 | n>=10 | 1218 | 41,0 % | 45,2 % |
| monate | mitte | 0.75 | n<10 | 1782 | 70,3 % | 70,0 % |
| monate | mitte | 0.75 | n>=10 | 1218 | 71,5 % | 73,2 % |
| monate | mitte | 1 | n<10 | 1782 | 86,4 % | 85,4 % |
| monate | mitte | 1 | n>=10 | 1218 | 87,4 % | 88,8 % |

Lesart: Δ 0 = Reihe ohne eingesetzten Wechsel; jede Markierung ist dort ein Fehlalarm. „bewertungen“ mischt die Einzelnoten über die Monate (nur Stichprobenrauschen), „monate“ mischt ganze Monate (echte Schwankung zwischen Monaten bleibt). Gewichtet: Kosten je Monat mit 1/(τ² + s²/n), s = Streuung innerhalb der Monate, τ robust aus den Monatsdifferenzen; Strafterm 2·ln(n) wie bisher in Einheiten der Varianz.
