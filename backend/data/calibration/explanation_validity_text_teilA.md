# Bewertung der Erklärungsansätze: Passung und Unterschied

Permutationen 20000, Startwert 20261017.

## Teil A: Unterscheiden die Stufen Markierungs- von Vergleichsfenstern?

Grundlage: `data/calibration/explanation_validity_text_2026-10-25.json` (100 Fenster, davon 100 vollständig im Speicher; 28 Markierungen in Clustern mit 72 Vergleichsfenstern).

Lesart der Spalten: Fisher behandelt die Fenster als unabhängig; der Permutationstest vergibt die Rolle „Markierung“ innerhalb jedes Clusters (Markierung und ihre verschobenen Fenster desselben Unternehmens) zufällig neu und ist deshalb der angemessene Test. „Nachweisbar wäre“ nennt den Anteil bei Markierungen, ab dem ein Unterschied zum Vergleichsanteil mit diesen Fallzahlen überhaupt mit 80 % Teststärke gefunden würde.

**Gesamt**

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall (Newcombe) | p Fisher | p Permutation (Cluster) | nachweisbar wäre (Anteil bei Markierungen) |
|---|---|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 16/28 (57 %) | 42/72 (58 %) | -1 pp | [-22; +19] pp | 1,000 | 1,000 | ≥ 84 % oder ≤ 29 % |
| oberste Stufe mindestens mittel | 16/28 (57 %) | 42/72 (58 %) | -1 pp | [-22; +19] pp | 1,000 | 1,000 | ≥ 84 % oder ≤ 29 % |
| mindestens ein Bündel der Stufe hoch | 5/28 (18 %) | 15/72 (21 %) | -3 pp | [-18; +16] pp | 1,000 | 0,756 | ≥ 51 % oder ≤ 4 % |
| Fenster mit kennzeichnenden Begriffen | 21/28 (75 %) | 54/72 (75 %) | 0 pp | [-20; +17] pp | 1,000 | 1,000 | ≥ 94 % oder ≤ 45 % |
| oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3) | Mittel 1,32 | Mittel 1,38 | -0,05 | – | – | 0,837 | – |

Gepaart je Cluster (oberste Stufe der Markierung minus Mittel ihrer Vergleichsfenster, 27 Paare): Markierung höher 10, gleich 8, niedriger 9; mittlere Differenz -0,05.

**Niveauwechsel** (19 Markierungen, 48 Vergleichsfenster)

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall (Newcombe) | p Fisher | p Permutation (Cluster) | nachweisbar wäre (Anteil bei Markierungen) |
|---|---|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 14/19 (74 %) | 32/48 (67 %) | 7 pp | [-18; +27] pp | 0,771 | 0,754 | ≥ 92 % oder ≤ 31 % |
| oberste Stufe mindestens mittel | 14/19 (74 %) | 32/48 (67 %) | 7 pp | [-18; +27] pp | 0,771 | 0,754 | ≥ 92 % oder ≤ 31 % |
| mindestens ein Bündel der Stufe hoch | 4/19 (21 %) | 12/48 (25 %) | -4 pp | [-23; +21] pp | 1,000 | 0,724 | ≥ 61 % oder ≤ 4 % |
| Fenster mit kennzeichnenden Begriffen | 19/19 (100 %) | 45/48 (94 %) | 6 pp | [-11; +17] pp | 0,553 | 0,505 | ≤ 61 % |
| oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3) | Mittel 1,68 | Mittel 1,58 | 0,10 | – | – | 0,801 | – |

**Einzelmonate** (9 Markierungen, 24 Vergleichsfenster)

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall (Newcombe) | p Fisher | p Permutation (Cluster) | nachweisbar wäre (Anteil bei Markierungen) |
|---|---|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 2/9 (22 %) | 10/24 (42 %) | -19 pp | [-45; +17] pp | 0,429 | 0,336 | ≥ 85 % oder ≤ 6 % |
| oberste Stufe mindestens mittel | 2/9 (22 %) | 10/24 (42 %) | -19 pp | [-45; +17] pp | 0,429 | 0,336 | ≥ 85 % oder ≤ 6 % |
| mindestens ein Bündel der Stufe hoch | 1/9 (11 %) | 3/24 (12 %) | -1 pp | [-22; +32] pp | 1,000 | 1,000 | ≥ 62 % |
| Fenster mit kennzeichnenden Begriffen | 2/9 (22 %) | 9/24 (38 %) | -15 pp | [-41; +21] pp | 0,681 | 0,654 | ≥ 83 % oder ≤ 4 % |
| oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3) | Mittel 0,56 | Mittel 0,96 | -0,40 | – | – | 0,354 | – |

**Markierungen mit gegen ohne Referenzzeitraum (E5)**

| Merkmal | mit Referenzzeitraum | ohne | Differenz | 95 %-Intervall | p Fisher |
|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 6/8 (75 %) | 10/20 (50 %) | 25 pp | [-15; +52] pp | 0,401 |
| oberste Stufe mindestens mittel | 6/8 (75 %) | 10/20 (50 %) | 25 pp | [-15; +52] pp | 0,401 |
| mindestens ein Bündel der Stufe hoch | 1/8 (12 %) | 4/20 (20 %) | -8 pp | [-31; +29] pp | 1,000 |
| Fenster mit kennzeichnenden Begriffen | 8/8 (100 %) | 13/20 (65 %) | 35 pp | [-2; +57] pp | 0,075 |

**Nullmodell: folgt die Stufe der Zahl der Belege?**

Spearman ρ Belege ↔ oberste Stufe: 0,21 (p 0,033, n 100); Belege ↔ mit Ansatz: 0,17 (p 0,091).

| Belege je Fenster (Drittel) | Spanne | Markierungen mit Ansatz | Vergleichsfenster mit Ansatz |
|---|---|---|---|
| wenige | 1–21 | 4/9 (44 %) | 9/23 (39 %) |
| mittel | 25–58 | 7/9 (78 %) | 17/24 (71 %) |
| viele | 61–510 | 5/10 (50 %) | 16/25 (64 %) |

Beschreibende Zahlen und Tests gegen die Nullhypothese 'kein Unterschied'. Ein Unterschied oder dessen Fehlen sagt nichts über Ursachen; ein Erklärungsansatz bleibt ein möglicher Zusammenhang. Die Passungsurteile stammen von einer bewertenden Instanz (Agent oder Person), die den Bogen blind gelesen hat; die Verblindung ist unvollständig, weil Unternehmen, Monate und Richtung sichtbar sind.

