> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt. Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume nach dem Annotationsprotokoll (Abschnitt 3.6.1)

**Markierungsfenster**

| Unternehmen | Fenster (vollständig) | mit Ansatz | mit hoch | mit mittel | mit niedrig | Belege / Bündel je Fenster (Median) |
|---|---|---|---|---|---|---|
| E.ON | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | 373 / 30 |
| RWE | 2 (2) | 1/2 (50 %) | 0/2 (0 %) | 1/2 (50 %) | 0/2 (0 %) | 304.5 / 6.5 |
| SAP SE | 2 (2) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 0/2 (0 %) | 345.5 / 78 |
| NTT DATA SE | 4 (4) | 2/4 (50 %) | 1/4 (25 %) | 2/4 (50 %) | 0/4 (0 %) | 2 / 0.5 |
| 1&1 AG | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 0/1 (0 %) | 25 / 2 |
| Bechtle | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 0/1 (0 %) | 6 / 2 |
| Cancom | 2 (2) | 0/2 (0 %) | 0/2 (0 %) | 0/2 (0 %) | 0/2 (0 %) | 7 / 0 |
| Carl Zeiss | 2 (2) | 0/2 (0 %) | 0/2 (0 %) | 0/2 (0 %) | 0/2 (0 %) | 59.5 / 0 |
| Compugroup Medical Deutschland | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 0/1 (0 %) | 38 / 2 |
| Telekom | 7 (7) | 3/7 (43 %) | 0/7 (0 %) | 3/7 (43 %) | 0/7 (0 %) | 61 / 0 |
| Freenet | 5 (5) | 4/5 (80 %) | 1/5 (20 %) | 3/5 (60 %) | 0/5 (0 %) | 31 / 1 |
| **Gesamt** | 28 (28) | 16/28 (57 %) | 5/28 (18 %) | 15/28 (54 %) | 0/28 (0 %) | 45 / 1 |

**Vergleichsfenster**

| Unternehmen | Fenster (vollständig) | mit Ansatz | mit hoch | mit mittel | mit niedrig | Belege / Bündel je Fenster (Median) |
|---|---|---|---|---|---|---|
| E.ON | 3 (3) | 3/3 (100 %) | 2/3 (67 %) | 3/3 (100 %) | 0/3 (0 %) | 335 / 18 |
| RWE | 6 (6) | 1/6 (17 %) | 1/6 (17 %) | 1/6 (17 %) | 0/6 (0 %) | 171 / 0 |
| SAP SE | 3 (3) | 2/3 (67 %) | 2/3 (67 %) | 2/3 (67 %) | 0/3 (0 %) | 460 / 53 |
| NTT DATA SE | 9 (9) | 5/9 (56 %) | 3/9 (33 %) | 4/9 (44 %) | 0/9 (0 %) | 5 / 1 |
| 1&1 AG | 3 (3) | 2/3 (67 %) | 0/3 (0 %) | 2/3 (67 %) | 0/3 (0 %) | 30 / 1 |
| Bechtle | 3 (3) | 3/3 (100 %) | 0/3 (0 %) | 3/3 (100 %) | 0/3 (0 %) | 7 / 1 |
| Cancom | 6 (6) | 1/6 (17 %) | 1/6 (17 %) | 1/6 (17 %) | 0/6 (0 %) | 4 / 0 |
| Carl Zeiss | 5 (5) | 1/5 (20 %) | 0/5 (0 %) | 1/5 (20 %) | 0/5 (0 %) | 34 / 0 |
| Compugroup Medical Deutschland | 3 (3) | 3/3 (100 %) | 1/3 (33 %) | 3/3 (100 %) | 0/3 (0 %) | 25 / 2 |
| Telekom | 16 (16) | 12/16 (75 %) | 5/16 (31 %) | 11/16 (69 %) | 0/16 (0 %) | 60 / 3 |
| Freenet | 15 (15) | 9/15 (60 %) | 0/15 (0 %) | 9/15 (60 %) | 0/15 (0 %) | 41 / 1 |
| **Gesamt** | 72 (72) | 42/72 (58 %) | 15/72 (21 %) | 40/72 (56 %) | 0/72 (0 %) | 44 / 1 |

„mit Ansatz“ = mindestens ein Bündel der Stufe niedrig oder höher; „mit hoch/mittel/niedrig“ = mindestens ein Bündel dieser Stufe. Anteile beziehen sich auf die vollständig im Speicher liegenden Fenster (in Klammern).

| Unternehmen | Abdeckungsquote NFA-05 (Markierungen mit Ansatz) | Niveauwechsel | Einzelmonate | Vergleichsfenster mit Ansatz |
|---|---|---|---|---|
| E.ON | 1/1 (100 %) | 1/1 (100 %) | – | 3/3 (100 %) |
| RWE | 1/2 (50 %) | 1/1 (100 %) | 0/1 (0 %) | 1/6 (17 %) |
| SAP SE | 2/2 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 2/3 (67 %) |
| NTT DATA SE | 2/4 (50 %) | 2/4 (50 %) | – | 5/9 (56 %) |
| 1&1 AG | 1/1 (100 %) | 1/1 (100 %) | – | 2/3 (67 %) |
| Bechtle | 1/1 (100 %) | 1/1 (100 %) | – | 3/3 (100 %) |
| Cancom | 0/2 (0 %) | – | 0/2 (0 %) | 1/6 (17 %) |
| Carl Zeiss | 0/2 (0 %) | – | 0/2 (0 %) | 1/5 (20 %) |
| Compugroup Medical Deutschland | 1/1 (100 %) | 1/1 (100 %) | – | 3/3 (100 %) |
| Telekom | 3/7 (43 %) | 2/4 (50 %) | 1/3 (33 %) | 12/16 (75 %) |
| Freenet | 4/5 (80 %) | 4/5 (80 %) | – | 9/15 (60 %) |
| **Gesamt** | 16/28 (57 %) | 14/19 (74 %) | 2/9 (22 %) | 42/72 (58 %) |

**Nach Referenzzeiträumen (E5)**

*Markierungsfenster mit Referenzzeitraum*

| Unternehmen | Fenster (vollständig) | mit Ansatz | mit hoch | mit mittel | mit niedrig | Belege / Bündel je Fenster (Median) |
|---|---|---|---|---|---|---|
| E.ON | 0 (0) | – | – | – | – | – / – |
| RWE | 0 (0) | – | – | – | – | – / – |
| SAP SE | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | 362 / 83 |
| NTT DATA SE | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 0/1 (0 %) | 2 / 1 |
| 1&1 AG | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 0/1 (0 %) | 25 / 2 |
| Bechtle | 0 (0) | – | – | – | – | – / – |
| Cancom | 0 (0) | – | – | – | – | – / – |
| Carl Zeiss | 0 (0) | – | – | – | – | – / – |
| Compugroup Medical Deutschland | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 0/1 (0 %) | 38 / 2 |
| Telekom | 2 (2) | 0/2 (0 %) | 0/2 (0 %) | 0/2 (0 %) | 0/2 (0 %) | 70 / 0 |
| Freenet | 2 (2) | 2/2 (100 %) | 0/2 (0 %) | 2/2 (100 %) | 0/2 (0 %) | 39 / 1.5 |
| **Gesamt** | 8 (8) | 6/8 (75 %) | 1/8 (12 %) | 6/8 (75 %) | 0/8 (0 %) | 46.5 / 1.5 |

*Markierungsfenster ohne Referenzzeitraum*

| Unternehmen | Fenster (vollständig) | mit Ansatz | mit hoch | mit mittel | mit niedrig | Belege / Bündel je Fenster (Median) |
|---|---|---|---|---|---|---|
| E.ON | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | 373 / 30 |
| RWE | 2 (2) | 1/2 (50 %) | 0/2 (0 %) | 1/2 (50 %) | 0/2 (0 %) | 304.5 / 6.5 |
| SAP SE | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | 329 / 73 |
| NTT DATA SE | 3 (3) | 1/3 (33 %) | 1/3 (33 %) | 1/3 (33 %) | 0/3 (0 %) | 2 / 0 |
| 1&1 AG | 0 (0) | – | – | – | – | – / – |
| Bechtle | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 0/1 (0 %) | 6 / 2 |
| Cancom | 2 (2) | 0/2 (0 %) | 0/2 (0 %) | 0/2 (0 %) | 0/2 (0 %) | 7 / 0 |
| Carl Zeiss | 2 (2) | 0/2 (0 %) | 0/2 (0 %) | 0/2 (0 %) | 0/2 (0 %) | 59.5 / 0 |
| Compugroup Medical Deutschland | 0 (0) | – | – | – | – | – / – |
| Telekom | 5 (5) | 3/5 (60 %) | 0/5 (0 %) | 3/5 (60 %) | 0/5 (0 %) | 61 / 2 |
| Freenet | 3 (3) | 2/3 (67 %) | 1/3 (33 %) | 1/3 (33 %) | 0/3 (0 %) | 31 / 1 |
| **Gesamt** | 20 (20) | 10/20 (50 %) | 4/20 (20 %) | 9/20 (45 %) | 0/20 (0 %) | 45 / 0.5 |

Markierung trifft einen Referenzzeitraum der Annotationsdatei (E5, Regel 6): Markierungsmonat im Fenster ±1 Monat um den Zeitraum, bei nicht bewertetem Nachbarmonat bis zu 3 Monate, gleiche Richtung; jede Markierung für sich geprüft, Vergleichsfenster außen vor. Annotationsdatei: data/annotations.json (version 3, 20 Einträge).

| Oberste Stufe je Fenster (gesamt) | hoch | mittel | niedrig | offen |
|---|---|---|---|---|
| Markierungsfenster | 5 | 11 | 0 | 12 |
| Vergleichsfenster | 15 | 27 | 0 | 30 |

Beschreibende Zahlen ohne Signifikanzaussage. Ein Erklärungsansatz ist ein möglicher Zusammenhang, keine Ursache; die Einstufung beruht auf Titeln und Wortbezügen. Fenster mit fehlenden Monaten im Speicher zählen nicht als 'ohne Ansatz'. Die Stimmung der Titel wurde nicht berechnet (ohne Einfluss auf die Stufe).
