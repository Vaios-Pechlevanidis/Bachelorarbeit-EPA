> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.

# Gewichtung nach Bewertungszahl: semisynthetischer Vergleich (DZ1)

15 Reihen × 100 Wiederholungen, Startwert 20261013; Strafterm-Faktor gewichtet 1.25, ungewichtet 2. Gepaart: beide Varianten auf denselben Reihen, Wechseln und Richtungen.

| Bedingung | Lage | Δ | Maß | ungewichtet | gewichtet | Differenz (pp) | 95 %-Intervall (Cluster-Bootstrap) | nur ungew. / nur gew. | p (Vorzeichen) | weitere Markierungen je Reihe ungew. / gew. |
|---|---|---|---|---|---|---|---|---|---|---|
| bewertungen | mitte | 0 | Anteil Reihen mit Fehlalarm | 18,3 % | 19,0 % | +0,7 | [-6,3; +6,2] | 122 / 133 | 0,531 | 0,34 / 0,31 |
| bewertungen | mitte | 0,3 | Trefferquote | 22,9 % | 27,5 % | +4,7 | [+2,8; +6,7] | 62 / 132 | < 0,001 | 0,58 / 0,62 |
| bewertungen | mitte | 0,5 | Trefferquote | 58,8 % | 64,1 % | +5,3 | [+3,4; +7,2] | 48 / 127 | < 0,001 | 0,59 / 0,57 |
| bewertungen | mitte | 0,75 | Trefferquote | 80,5 % | 82,5 % | +2,0 | [+0,9; +3,2] | 24 / 54 | < 0,001 | 0,47 / 0,46 |
| bewertungen | mitte | 1 | Trefferquote | 91,5 % | 92,2 % | +0,7 | [-0,2; +1,7] | 19 / 30 | 0,152 | 0,38 / 0,38 |
| bewertungen | ende | 0 | Anteil Reihen mit Fehlalarm | 18,3 % | 19,0 % | +0,7 | [-6,3; +5,9] | 122 / 133 | 0,531 | 0,33 / 0,31 |
| bewertungen | ende | 0,3 | Trefferquote | 14,9 % | 21,6 % | +6,7 | [+2,9; +10,5] | 35 / 135 | < 0,001 | 0,36 / 0,35 |
| bewertungen | ende | 0,5 | Trefferquote | 42,1 % | 52,3 % | +10,2 | [+6,0; +14,5] | 35 / 188 | < 0,001 | 0,40 / 0,40 |
| bewertungen | ende | 0,75 | Trefferquote | 74,1 % | 80,9 % | +6,9 | [+4,9; +9,0] | 19 / 122 | < 0,001 | 0,38 / 0,37 |
| bewertungen | ende | 1 | Trefferquote | 89,3 % | 91,6 % | +2,3 | [+0,6; +4,1] | 13 / 48 | < 0,001 | 0,34 / 0,34 |
| monate | mitte | 0 | Anteil Reihen mit Fehlalarm | 14,5 % | 34,9 % | +20,3 | [+13,9; +26,5] | 22 / 327 | < 0,001 | 0,24 / 0,78 |
| monate | mitte | 0,3 | Trefferquote | 15,2 % | 21,8 % | +6,6 | [+5,1; +8,3] | 30 / 129 | < 0,001 | 0,48 / 1,06 |
| monate | mitte | 0,5 | Trefferquote | 42,0 % | 49,1 % | +7,1 | [+4,9; +9,2] | 45 / 151 | < 0,001 | 0,55 / 1,08 |
| monate | mitte | 0,75 | Trefferquote | 71,6 % | 74,1 % | +2,5 | [+1,0; +4,1] | 43 / 80 | 0,001 | 0,43 / 0,93 |
| monate | mitte | 1 | Trefferquote | 87,1 % | 87,1 % | +0,0 | [-0,9; +0,8] | 27 / 27 | 1,000 | 0,32 / 0,82 |

**Trefferquote nach Belegung des Wechselmonats**

| Bedingung | Lage | Δ | Wechselmonat | Wiederholungen | ungewichtet | gewichtet |
|---|---|---|---|---|---|---|
| bewertungen | mitte | 0.3 | n<10 | 920 | 22,6 % | 24,6 % |
| bewertungen | mitte | 0.3 | n>=10 | 580 | 23,3 % | 32,2 % |
| bewertungen | mitte | 0.5 | n<10 | 920 | 54,7 % | 58,1 % |
| bewertungen | mitte | 0.5 | n>=10 | 580 | 65,3 % | 73,5 % |
| bewertungen | mitte | 0.75 | n<10 | 920 | 76,5 % | 77,6 % |
| bewertungen | mitte | 0.75 | n>=10 | 580 | 86,9 % | 90,3 % |
| bewertungen | mitte | 1 | n<10 | 920 | 88,8 % | 89,2 % |
| bewertungen | mitte | 1 | n>=10 | 580 | 95,7 % | 96,9 % |
| bewertungen | ende | 0.3 | n<10 | 735 | 15,0 % | 15,9 % |
| bewertungen | ende | 0.3 | n>=10 | 765 | 14,9 % | 27,1 % |
| bewertungen | ende | 0.5 | n<10 | 735 | 37,7 % | 42,9 % |
| bewertungen | ende | 0.5 | n>=10 | 765 | 46,3 % | 61,3 % |
| bewertungen | ende | 0.75 | n<10 | 735 | 68,0 % | 74,3 % |
| bewertungen | ende | 0.75 | n>=10 | 765 | 79,9 % | 87,3 % |
| bewertungen | ende | 1 | n<10 | 735 | 85,9 % | 88,6 % |
| bewertungen | ende | 1 | n>=10 | 765 | 92,5 % | 94,5 % |
| monate | mitte | 0.3 | n<10 | 902 | 15,0 % | 21,1 % |
| monate | mitte | 0.3 | n>=10 | 598 | 15,6 % | 22,9 % |
| monate | mitte | 0.5 | n<10 | 902 | 41,6 % | 46,8 % |
| monate | mitte | 0.5 | n>=10 | 598 | 42,6 % | 52,5 % |
| monate | mitte | 0.75 | n<10 | 902 | 69,8 % | 71,8 % |
| monate | mitte | 0.75 | n>=10 | 598 | 74,2 % | 77,4 % |
| monate | mitte | 1 | n<10 | 902 | 85,7 % | 85,1 % |
| monate | mitte | 1 | n>=10 | 598 | 89,1 % | 90,0 % |

Lesart: Δ 0 = Reihe ohne eingesetzten Wechsel; jede Markierung ist dort ein Fehlalarm. „bewertungen“ mischt die Einzelnoten über die Monate (nur Stichprobenrauschen), „monate“ mischt ganze Monate (echte Schwankung zwischen Monaten bleibt). Gewichtet: Kosten je Monat mit 1/(τ² + s²/n), s = Streuung innerhalb der Monate, τ robust aus den Monatsdifferenzen; Strafterm 2·ln(n) wie bisher in Einheiten der Varianz.
