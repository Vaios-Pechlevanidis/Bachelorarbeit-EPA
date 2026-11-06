> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.

# Gewichtung nach Bewertungszahl: semisynthetischer Vergleich (DZ1)

15 Reihen × 100 Wiederholungen, Startwert 20261013; Strafterm-Faktor gewichtet 1.5, ungewichtet 2. Gepaart: beide Varianten auf denselben Reihen, Wechseln und Richtungen.

| Bedingung | Lage | Δ | Maß | ungewichtet | gewichtet | Differenz (pp) | 95 %-Intervall (Cluster-Bootstrap) | nur ungew. / nur gew. | p (Vorzeichen) | weitere Markierungen je Reihe ungew. / gew. |
|---|---|---|---|---|---|---|---|---|---|---|
| bewertungen | mitte | 0 | Anteil Reihen mit Fehlalarm | 18,3 % | 11,1 % | -7,1 | [-13,4; -2,8] | 163 / 56 | < 0,001 | 0,34 / 0,16 |
| bewertungen | mitte | 0,3 | Trefferquote | 22,9 % | 25,7 % | +2,9 | [+1,2; +4,4] | 62 / 105 | 0,001 | 0,58 / 0,45 |
| bewertungen | mitte | 0,5 | Trefferquote | 58,8 % | 62,9 % | +4,1 | [+2,3; +6,1] | 53 / 115 | < 0,001 | 0,59 / 0,44 |
| bewertungen | mitte | 0,75 | Trefferquote | 80,5 % | 82,3 % | +1,7 | [+0,8; +2,7] | 24 / 50 | 0,003 | 0,47 / 0,32 |
| bewertungen | mitte | 1 | Trefferquote | 91,5 % | 92,2 % | +0,7 | [-0,3; +1,7] | 17 / 28 | 0,135 | 0,38 / 0,23 |
| bewertungen | ende | 0 | Anteil Reihen mit Fehlalarm | 18,3 % | 11,1 % | -7,1 | [-13,2; -2,8] | 163 / 56 | < 0,001 | 0,33 / 0,15 |
| bewertungen | ende | 0,3 | Trefferquote | 14,9 % | 19,0 % | +4,1 | [+0,5; +7,7] | 45 / 106 | < 0,001 | 0,36 / 0,20 |
| bewertungen | ende | 0,5 | Trefferquote | 42,1 % | 47,3 % | +5,2 | [+1,2; +9,5] | 54 / 132 | < 0,001 | 0,40 / 0,25 |
| bewertungen | ende | 0,75 | Trefferquote | 74,1 % | 78,7 % | +4,7 | [+2,8; +6,8] | 24 / 94 | < 0,001 | 0,38 / 0,24 |
| bewertungen | ende | 1 | Trefferquote | 89,3 % | 91,0 % | +1,7 | [+0,3; +3,1] | 12 / 38 | < 0,001 | 0,34 / 0,19 |
| monate | mitte | 0 | Anteil Reihen mit Fehlalarm | 14,5 % | 23,9 % | +9,3 | [+3,8; +14,7] | 36 / 176 | < 0,001 | 0,24 / 0,47 |
| monate | mitte | 0,3 | Trefferquote | 15,2 % | 19,3 % | +4,1 | [+2,4; +5,7] | 34 / 95 | < 0,001 | 0,48 / 0,75 |
| monate | mitte | 0,5 | Trefferquote | 42,0 % | 47,7 % | +5,7 | [+3,9; +7,5] | 39 / 125 | < 0,001 | 0,55 / 0,79 |
| monate | mitte | 0,75 | Trefferquote | 71,6 % | 72,8 % | +1,2 | [+0,2; +2,2] | 42 / 60 | 0,092 | 0,43 / 0,64 |
| monate | mitte | 1 | Trefferquote | 87,1 % | 87,2 % | +0,1 | [-0,7; +0,9] | 22 / 24 | 0,883 | 0,32 / 0,53 |

**Trefferquote nach Belegung des Wechselmonats**

| Bedingung | Lage | Δ | Wechselmonat | Wiederholungen | ungewichtet | gewichtet |
|---|---|---|---|---|---|---|
| bewertungen | mitte | 0.3 | n<10 | 920 | 22,6 % | 23,0 % |
| bewertungen | mitte | 0.3 | n>=10 | 580 | 23,3 % | 30,0 % |
| bewertungen | mitte | 0.5 | n<10 | 920 | 54,7 % | 56,5 % |
| bewertungen | mitte | 0.5 | n>=10 | 580 | 65,3 % | 73,1 % |
| bewertungen | mitte | 0.75 | n<10 | 920 | 76,5 % | 77,0 % |
| bewertungen | mitte | 0.75 | n>=10 | 580 | 86,9 % | 90,7 % |
| bewertungen | mitte | 1 | n<10 | 920 | 88,8 % | 89,0 % |
| bewertungen | mitte | 1 | n>=10 | 580 | 95,7 % | 97,2 % |
| bewertungen | ende | 0.3 | n<10 | 735 | 15,0 % | 13,9 % |
| bewertungen | ende | 0.3 | n>=10 | 765 | 14,9 % | 23,9 % |
| bewertungen | ende | 0.5 | n<10 | 735 | 37,7 % | 37,5 % |
| bewertungen | ende | 0.5 | n>=10 | 765 | 46,3 % | 56,6 % |
| bewertungen | ende | 0.75 | n<10 | 735 | 68,0 % | 71,3 % |
| bewertungen | ende | 0.75 | n>=10 | 765 | 79,9 % | 85,9 % |
| bewertungen | ende | 1 | n<10 | 735 | 85,9 % | 87,6 % |
| bewertungen | ende | 1 | n>=10 | 765 | 92,5 % | 94,2 % |
| monate | mitte | 0.3 | n<10 | 902 | 15,0 % | 18,3 % |
| monate | mitte | 0.3 | n>=10 | 598 | 15,6 % | 20,7 % |
| monate | mitte | 0.5 | n<10 | 902 | 41,6 % | 45,3 % |
| monate | mitte | 0.5 | n>=10 | 598 | 42,6 % | 51,3 % |
| monate | mitte | 0.75 | n<10 | 902 | 69,8 % | 70,6 % |
| monate | mitte | 0.75 | n>=10 | 598 | 74,2 % | 76,1 % |
| monate | mitte | 1 | n<10 | 902 | 85,7 % | 85,4 % |
| monate | mitte | 1 | n>=10 | 598 | 89,1 % | 90,0 % |

Lesart: Δ 0 = Reihe ohne eingesetzten Wechsel; jede Markierung ist dort ein Fehlalarm. „bewertungen“ mischt die Einzelnoten über die Monate (nur Stichprobenrauschen), „monate“ mischt ganze Monate (echte Schwankung zwischen Monaten bleibt). Gewichtet: Kosten je Monat mit 1/(τ² + s²/n), s = Streuung innerhalb der Monate, τ robust aus den Monatsdifferenzen; Strafterm 2·ln(n) wie bisher in Einheiten der Varianz.
