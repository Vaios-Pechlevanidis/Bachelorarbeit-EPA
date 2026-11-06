> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.

# Gewichtung nach Bewertungszahl: semisynthetischer Vergleich (DZ1)

15 Reihen × 100 Wiederholungen, Startwert 20261013; Strafterm-Faktor gewichtet 1, ungewichtet 2. Gepaart: beide Varianten auf denselben Reihen, Wechseln und Richtungen.

| Bedingung | Lage | Δ | Maß | ungewichtet | gewichtet | Differenz (pp) | 95 %-Intervall (Cluster-Bootstrap) | nur ungew. / nur gew. | p (Vorzeichen) | weitere Markierungen je Reihe ungew. / gew. |
|---|---|---|---|---|---|---|---|---|---|---|
| bewertungen | mitte | 0 | Anteil Reihen mit Fehlalarm | 18,3 % | 33,3 % | +15,1 | [+7,3; +21,5] | 81 / 307 | < 0,001 | 0,34 / 0,66 |
| bewertungen | mitte | 0,3 | Trefferquote | 22,9 % | 30,0 % | +7,1 | [+5,1; +9,3] | 61 / 168 | < 0,001 | 0,58 / 0,94 |
| bewertungen | mitte | 0,5 | Trefferquote | 58,8 % | 63,9 % | +5,1 | [+2,9; +7,4] | 60 / 137 | < 0,001 | 0,59 / 0,87 |
| bewertungen | mitte | 0,75 | Trefferquote | 80,5 % | 83,1 % | +2,5 | [+1,1; +4,1] | 28 / 66 | < 0,001 | 0,47 / 0,77 |
| bewertungen | mitte | 1 | Trefferquote | 91,5 % | 92,1 % | +0,7 | [-0,1; +1,5] | 23 / 33 | 0,229 | 0,38 / 0,70 |
| bewertungen | ende | 0 | Anteil Reihen mit Fehlalarm | 18,3 % | 33,3 % | +15,1 | [+7,4; +21,5] | 81 / 307 | < 0,001 | 0,33 / 0,66 |
| bewertungen | ende | 0,3 | Trefferquote | 14,9 % | 27,1 % | +12,1 | [+8,2; +16,3] | 28 / 210 | < 0,001 | 0,36 / 0,71 |
| bewertungen | ende | 0,5 | Trefferquote | 42,1 % | 58,5 % | +16,4 | [+12,2; +21,1] | 21 / 267 | < 0,001 | 0,40 / 0,74 |
| bewertungen | ende | 0,75 | Trefferquote | 74,1 % | 82,6 % | +8,5 | [+5,9; +11,1] | 17 / 145 | < 0,001 | 0,38 / 0,70 |
| bewertungen | ende | 1 | Trefferquote | 89,3 % | 92,3 % | +3,1 | [+1,3; +4,9] | 11 / 57 | < 0,001 | 0,34 / 0,65 |
| monate | mitte | 0 | Anteil Reihen mit Fehlalarm | 14,5 % | 49,2 % | +34,7 | [+26,7; +42,0] | 15 / 535 | < 0,001 | 0,24 / 1,29 |
| monate | mitte | 0,3 | Trefferquote | 15,2 % | 24,3 % | +9,1 | [+7,4; +11,1] | 35 / 172 | < 0,001 | 0,48 / 1,59 |
| monate | mitte | 0,5 | Trefferquote | 42,0 % | 51,0 % | +9,0 | [+6,1; +12,1] | 48 / 183 | < 0,001 | 0,55 / 1,59 |
| monate | mitte | 0,75 | Trefferquote | 71,6 % | 75,8 % | +4,2 | [+2,1; +6,5] | 38 / 101 | < 0,001 | 0,43 / 1,43 |
| monate | mitte | 1 | Trefferquote | 87,1 % | 86,9 % | -0,2 | [-1,1; +0,7] | 32 / 29 | 0,798 | 0,32 / 1,33 |

**Trefferquote nach Belegung des Wechselmonats**

| Bedingung | Lage | Δ | Wechselmonat | Wiederholungen | ungewichtet | gewichtet |
|---|---|---|---|---|---|---|
| bewertungen | mitte | 0.3 | n<10 | 920 | 22,6 % | 27,3 % |
| bewertungen | mitte | 0.3 | n>=10 | 580 | 23,3 % | 34,3 % |
| bewertungen | mitte | 0.5 | n<10 | 920 | 54,7 % | 58,5 % |
| bewertungen | mitte | 0.5 | n>=10 | 580 | 65,3 % | 72,6 % |
| bewertungen | mitte | 0.75 | n<10 | 920 | 76,5 % | 78,8 % |
| bewertungen | mitte | 0.75 | n>=10 | 580 | 86,9 % | 89,8 % |
| bewertungen | mitte | 1 | n<10 | 920 | 88,8 % | 89,5 % |
| bewertungen | mitte | 1 | n>=10 | 580 | 95,7 % | 96,4 % |
| bewertungen | ende | 0.3 | n<10 | 735 | 15,0 % | 21,8 % |
| bewertungen | ende | 0.3 | n>=10 | 765 | 14,9 % | 32,2 % |
| bewertungen | ende | 0.5 | n<10 | 735 | 37,7 % | 50,3 % |
| bewertungen | ende | 0.5 | n>=10 | 765 | 46,3 % | 66,3 % |
| bewertungen | ende | 0.75 | n<10 | 735 | 68,0 % | 76,2 % |
| bewertungen | ende | 0.75 | n>=10 | 765 | 79,9 % | 88,8 % |
| bewertungen | ende | 1 | n<10 | 735 | 85,9 % | 89,7 % |
| bewertungen | ende | 1 | n>=10 | 765 | 92,5 % | 94,9 % |
| monate | mitte | 0.3 | n<10 | 902 | 15,0 % | 23,7 % |
| monate | mitte | 0.3 | n>=10 | 598 | 15,6 % | 25,2 % |
| monate | mitte | 0.5 | n<10 | 902 | 41,6 % | 49,0 % |
| monate | mitte | 0.5 | n>=10 | 598 | 42,6 % | 54,0 % |
| monate | mitte | 0.75 | n<10 | 902 | 69,8 % | 73,7 % |
| monate | mitte | 0.75 | n>=10 | 598 | 74,2 % | 78,9 % |
| monate | mitte | 1 | n<10 | 902 | 85,7 % | 85,6 % |
| monate | mitte | 1 | n>=10 | 598 | 89,1 % | 88,8 % |

Lesart: Δ 0 = Reihe ohne eingesetzten Wechsel; jede Markierung ist dort ein Fehlalarm. „bewertungen“ mischt die Einzelnoten über die Monate (nur Stichprobenrauschen), „monate“ mischt ganze Monate (echte Schwankung zwischen Monaten bleibt). Gewichtet: Kosten je Monat mit 1/(τ² + s²/n), s = Streuung innerhalb der Monate, τ robust aus den Monatsdifferenzen; Strafterm 2·ln(n) wie bisher in Einheiten der Varianz.
