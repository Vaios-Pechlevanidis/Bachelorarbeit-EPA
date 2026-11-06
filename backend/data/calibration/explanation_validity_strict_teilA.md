# Bewertung der Erklärungsansätze: Passung und Unterschied

Permutationen 20000, Startwert 20261017.

## Teil A: Unterscheiden die Stufen Markierungs- von Vergleichsfenstern?

Grundlage: `data/calibration/explanation_validity_strict_2026-10-18.json` (100 Fenster, davon 100 vollständig im Speicher; 28 Markierungen in Clustern mit 72 Vergleichsfenstern).

Lesart der Spalten: Fisher behandelt die Fenster als unabhängig; der Permutationstest vergibt die Rolle „Markierung“ innerhalb jedes Clusters (Markierung und ihre verschobenen Fenster desselben Unternehmens) zufällig neu und ist deshalb der angemessene Test. „Nachweisbar wäre“ nennt den Anteil bei Markierungen, ab dem ein Unterschied zum Vergleichsanteil mit diesen Fallzahlen überhaupt mit 80 % Teststärke gefunden würde.

**Gesamt**

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall (Newcombe) | p Fisher | p Permutation (Cluster) | nachweisbar wäre (Anteil bei Markierungen) |
|---|---|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 14/28 (50 %) | 23/72 (32 %) | 18 pp | [-3; +38] pp | 0,110 | 0,058 | ≥ 62 % oder ≤ 10 % |
| oberste Stufe mindestens mittel | 14/28 (50 %) | 23/72 (32 %) | 18 pp | [-3; +38] pp | 0,110 | 0,058 | ≥ 62 % oder ≤ 10 % |
| mindestens ein Bündel der Stufe hoch | 2/28 (7 %) | 2/72 (3 %) | 4 pp | [-4; +20] pp | 0,312 | 0,502 | ≥ 27 % |
| Fenster mit kennzeichnenden Begriffen | 21/28 (75 %) | 54/72 (75 %) | 0 pp | [-20; +17] pp | 1,000 | 1,000 | ≥ 94 % oder ≤ 45 % |
| oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3) | Mittel 1,07 | Mittel 0,67 | 0,40 | – | – | 0,049 | – |

Gepaart je Cluster (oberste Stufe der Markierung minus Mittel ihrer Vergleichsfenster, 27 Paare): Markierung höher 11, gleich 11, niedriger 5; mittlere Differenz 0,38.

**Niveauwechsel** (19 Markierungen, 48 Vergleichsfenster)

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall (Newcombe) | p Fisher | p Permutation (Cluster) | nachweisbar wäre (Anteil bei Markierungen) |
|---|---|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 12/19 (63 %) | 15/48 (31 %) | 32 pp | [+6; +53] pp | 0,026 | 0,013 | ≥ 67 % oder ≤ 7 % |
| oberste Stufe mindestens mittel | 12/19 (63 %) | 15/48 (31 %) | 32 pp | [+6; +53] pp | 0,026 | 0,013 | ≥ 67 % oder ≤ 7 % |
| mindestens ein Bündel der Stufe hoch | 2/19 (11 %) | 2/48 (4 %) | 6 pp | [-6; +27] pp | 0,317 | 0,503 | ≥ 36 % |
| Fenster mit kennzeichnenden Begriffen | 19/19 (100 %) | 45/48 (94 %) | 6 pp | [-11; +17] pp | 0,553 | 0,505 | ≤ 61 % |
| oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3) | Mittel 1,37 | Mittel 0,67 | 0,70 | – | – | 0,007 | – |

**Einzelmonate** (9 Markierungen, 24 Vergleichsfenster)

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall (Newcombe) | p Fisher | p Permutation (Cluster) | nachweisbar wäre (Anteil bei Markierungen) |
|---|---|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 2/9 (22 %) | 8/24 (33 %) | -11 pp | [-37; +25] pp | 0,686 | 0,553 | ≥ 80 % oder ≤ 2 % |
| oberste Stufe mindestens mittel | 2/9 (22 %) | 8/24 (33 %) | -11 pp | [-37; +25] pp | 0,686 | 0,553 | ≥ 80 % oder ≤ 2 % |
| mindestens ein Bündel der Stufe hoch | 0/9 (0 %) | 0/24 (0 %) | 0 pp | [-14; +30] pp | 1,000 | 1,000 | ≥ 47 % |
| Fenster mit kennzeichnenden Begriffen | 2/9 (22 %) | 9/24 (38 %) | -15 pp | [-41; +21] pp | 0,681 | 0,654 | ≥ 83 % oder ≤ 4 % |
| oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3) | Mittel 0,44 | Mittel 0,67 | -0,22 | – | – | 0,553 | – |

**Markierungen mit gegen ohne Referenzzeitraum (E5)**

| Merkmal | mit Referenzzeitraum | ohne | Differenz | 95 %-Intervall | p Fisher |
|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 5/8 (62 %) | 9/20 (45 %) | 18 pp | [-21; +48] pp | 0,678 |
| oberste Stufe mindestens mittel | 5/8 (62 %) | 9/20 (45 %) | 18 pp | [-21; +48] pp | 0,678 |
| mindestens ein Bündel der Stufe hoch | 1/8 (12 %) | 1/20 (5 %) | 8 pp | [-14; +42] pp | 0,497 |
| Fenster mit kennzeichnenden Begriffen | 8/8 (100 %) | 13/20 (65 %) | 35 pp | [-2; +57] pp | 0,075 |

**Nullmodell: folgt die Stufe der Zahl der Belege?**

Spearman ρ Belege ↔ oberste Stufe: 0,32 (p 0,001, n 100); Belege ↔ mit Ansatz: 0,32 (p 0,001).

| Belege je Fenster (Drittel) | Spanne | Markierungen mit Ansatz | Vergleichsfenster mit Ansatz |
|---|---|---|---|
| wenige | 1–21 | 3/9 (33 %) | 2/23 (9 %) |
| mittel | 25–58 | 6/9 (67 %) | 8/24 (33 %) |
| viele | 61–510 | 5/10 (50 %) | 13/25 (52 %) |

Beschreibende Zahlen und Tests gegen die Nullhypothese 'kein Unterschied'. Ein Unterschied oder dessen Fehlen sagt nichts über Ursachen; ein Erklärungsansatz bleibt ein möglicher Zusammenhang. Die Passungsurteile stammen von einer bewertenden Instanz (Agent oder Person), die den Bogen blind gelesen hat; die Verblindung ist unvollständig, weil Unternehmen, Monate und Richtung sichtbar sind.

