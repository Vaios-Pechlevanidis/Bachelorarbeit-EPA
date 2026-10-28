# Testergebnisse

> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt. Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume nach dem Annotationsprotokoll (Abschnitt 3.6.1)

Stand: 28.10.2026, 09:35 Uhr. Geprüft wurde der Code von Commit `bacca9a` (Branch `main`) mit zwei noch nicht committeten Änderungen: Aus dem Quellcode sind alle Kommentare und Docstrings entfernt, und Frontend, Tests, Auswertungsskripte und md-Dateien tragen einen Hinweis auf die Unterstützung durch Claude Code. Die Ergebnisse vor und nach diesen Änderungen sind gleich. Das Archiv der Referenzzeiträume liegt wieder unverändert in `docs/dz1-referenz/`.

## Überblick

| Prüfung | Werkzeug | Ergebnis |
|---|---|---|
| Backend-Tests | pytest 9.0.2, Python 3.13.3 | 1625 bestanden, 0 fehlgeschlagen, 50 Warnungen, 61,4 s |
| Frontend-Tests | Vitest 5.0.5, Node 24.13.0 | 35 bestanden, 0 fehlgeschlagen |
| Codeprüfung Frontend | ESLint 9.39.5 | 0 Fehler, 0 Warnungen |
| Produktions-Build Frontend | Vite 6.4.3 | erfolgreich, 1 Hinweis zur Dateigröße |

Alle Tests bestehen, im Backend und im Frontend.

## Ausführung

Backend, aus dem Ordner `backend/`:

```bash
.venv/bin/pytest -q
```

Frontend, aus dem Ordner `frontend/`:

```bash
npx vitest run
```

```bash
npx eslint .
```

```bash
npx vite build
```

## Backend nach Bereich

| Bereich | Ordner | Dateien | Tests | Bestanden | Geprüft wird |
|---|---|---:|---:|---:|---|
| Auffällige Veränderungen | `tests/anomaly/` | 7 | 189 | 189 | Erkennung der Niveauwechsel, auffällige Einzelmonate, Statusfilter, Stabilität der Ergebnisse, semi-synthetische Simulation, API-Route der Anomalien |
| Drill-down | `tests/drilldown/` | 8 | 219 | 219 | Dimension als Filter, Vergleich zweier Zeiträume, Themen je Bewertung, Schlagwort-Themen, Hervorhebung, Routen für Bewertungsliste und Erklärungen |
| Externe Belege | `tests/evidence/` | 14 | 191 | 191 | Belegspeicher, EQS-Mitteilungen, Texte der Belege, Ereignisfenster, allgemeine und gesamtwirtschaftliche Ereignisse, Abdeckung, Routen, Abrufskripte |
| Erklärungsansätze | `tests/explanations/` | 11 | 293 | 293 | Rangfolge, Ereigniskategorien, Bezeichnungen der Signale, strenge Artikelauswahl, Textabgleich, Begriffe aus Bewertungen, Auswertung der Gültigkeit, Bewertungsskript, festgeschriebene Regeln |
| Prognose | `tests/forecast/` | 8 | 87 | 87 | Prognoseverfahren, Rückrechnung (Backtest), Grenzfälle, Parameter, Datenbasis, Dienst und Zusammenspiel |
| Kursdaten | `tests/market/` | 4 | 72 | 72 | Route der Kursdaten, Aktien-Dashboard, Kontextdienst, Zusammenfassung |
| Stimmungsanalyse | `tests/sentiment_analysis/` | 3 | 23 | 23 | Transformer-Modell gegen Lexikon, Analysemodi, Genauigkeit |
| Statistik | `tests/statistical/` | 2 | 10 | 10 | Gewichtung nach Beschäftigtengruppe, statistische Berechnungen |
| Themenmodell | `tests/topic_modeling/` | 4 | 23 | 23 | LDA-Themenmodell, Themenübersicht, Themenqualität |
| Übrige Bereiche | `tests/` | 26 | 518 | 518 | Annotationen der Referenzzeiträume (Datei, Validator, blinde Zweitannotation, Abgleich), Archiv der Referenzzeiträume mit Prüfsummen, Bezugsgrößen und Auswertung der Erkennung, CSV- und Excel-Import, Unternehmensdaten, Bewertungszahlen, Scores mit Unsicherheit, gleitender Durchschnitt, Datenstand, eigene Ereignisse, Duplikate, Paginierung, paralleles Laden, Datenbank-Client, Prüfung der Evaluationsinstanz, Themenzitate |
| **Summe** | | **87** | **1625** | **1625** | |

Drei Testdateien bauen eine Verbindung zur gehosteten Supabase-Datenbank auf und brauchen deshalb `backend/.env` und eine Netzverbindung: `forecast/test_forecast_databasis.py`, `sentiment_analysis/test_sentiment_accuracy.py` und `topic_modeling/test_improved_topics.py`.

`test_dz1_referenz_archiv.py` vergleicht die Dateien in `docs/dz1-referenz/` mit den SHA-256-Prüfsummen aus deren README. Diese Dateien müssen deshalb byte-genau bleiben. Darum enthalten `dz1_rechner.py` und `pruefe_bereinigung.py` noch ihre ursprünglichen Kommentare, und die Agentendatei trägt keinen Hinweis auf Claude Code; dieser steht in der README des Archivs.

## Backend je Testdatei

| Testdatei | Tests | Bestanden | Fehlgeschlagen | Laufzeit (s) |
|---|---:|---:|---:|---:|
| `anomaly/test_anomalies_route.py` | 18 | 18 | 0 | 0,60 |
| `anomaly/test_anomaly_service.py` | 23 | 23 | 0 | 3,27 |
| `anomaly/test_changepoint_detector.py` | 41 | 41 | 0 | 3,27 |
| `anomaly/test_outlier_months.py` | 11 | 11 | 0 | 0,16 |
| `anomaly/test_simulate_detection.py` | 41 | 41 | 0 | 3,60 |
| `anomaly/test_stability.py` | 4 | 4 | 0 | 0,20 |
| `anomaly/test_status_filter.py` | 51 | 51 | 0 | 0,93 |
| `drilldown/test_dimension_scope.py` | 26 | 26 | 0 | 0,37 |
| `drilldown/test_explanation_service.py` | 24 | 24 | 0 | 0,06 |
| `drilldown/test_explanations_route.py` | 16 | 16 | 0 | 2,29 |
| `drilldown/test_keyword_topic_service.py` | 54 | 54 | 0 | 4,13 |
| `drilldown/test_period_comparison.py` | 17 | 17 | 0 | 0,42 |
| `drilldown/test_review_topics.py` | 23 | 23 | 0 | 3,67 |
| `drilldown/test_reviews_route.py` | 38 | 38 | 0 | 1,47 |
| `drilldown/test_topic_highlight.py` | 21 | 21 | 0 | 0,53 |
| `evidence/test_context_coverage.py` | 11 | 11 | 0 | 0,02 |
| `evidence/test_context_decisions.py` | 6 | 6 | 0 | 0,01 |
| `evidence/test_context_dimension.py` | 10 | 10 | 0 | 0,49 |
| `evidence/test_context_routes.py` | 13 | 13 | 0 | 1,03 |
| `evidence/test_evidence_contracts.py` | 10 | 10 | 0 | 0,01 |
| `evidence/test_evidence_eqs.py` | 13 | 13 | 0 | 0,18 |
| `evidence/test_evidence_language.py` | 8 | 8 | 0 | 0,01 |
| `evidence/test_evidence_store.py` | 22 | 22 | 0 | 0,06 |
| `evidence/test_evidence_text.py` | 20 | 20 | 0 | 0,14 |
| `evidence/test_evidence_window.py` | 32 | 32 | 0 | 0,03 |
| `evidence/test_fetch_context_script.py` | 14 | 14 | 0 | 0,05 |
| `evidence/test_fetch_evidence_text_script.py` | 11 | 11 | 0 | 0,14 |
| `evidence/test_global_events.py` | 8 | 8 | 0 | 0,12 |
| `evidence/test_macro_events.py` | 13 | 13 | 0 | 0,03 |
| `explanations/test_corrections_2026_10_13.py` | 19 | 19 | 0 | 0,02 |
| `explanations/test_event_categories.py` | 27 | 27 | 0 | 0,04 |
| `explanations/test_explanation_ranking.py` | 94 | 94 | 0 | 0,11 |
| `explanations/test_explanation_validity.py` | 14 | 14 | 0 | 1,01 |
| `explanations/test_explanations_in_responses.py` | 8 | 8 | 0 | 1,49 |
| `explanations/test_frozen_rules.py` | 5 | 5 | 0 | 0,01 |
| `explanations/test_rate_explanations.py` | 31 | 31 | 0 | 0,94 |
| `explanations/test_review_terms.py` | 26 | 26 | 0 | 0,05 |
| `explanations/test_signal_labels.py` | 31 | 31 | 0 | 0,07 |
| `explanations/test_strict_selection.py` | 22 | 22 | 0 | 0,05 |
| `explanations/test_text_match.py` | 16 | 16 | 0 | 0,03 |
| `forecast/test_forecast_backtest.py` | 11 | 11 | 0 | 0,21 |
| `forecast/test_forecast_databasis.py` | 15 | 15 | 0 | 0,53 |
| `forecast/test_forecast_details.py` | 6 | 6 | 0 | 0,03 |
| `forecast/test_forecast_edgecases.py` | 16 | 16 | 0 | 0,11 |
| `forecast/test_forecast_engine.py` | 21 | 21 | 0 | 0,08 |
| `forecast/test_forecast_hyperparams.py` | 8 | 8 | 0 | 0,35 |
| `forecast/test_forecast_integration.py` | 2 | 2 | 0 | 0,12 |
| `forecast/test_forecast_service.py` | 8 | 8 | 0 | 0,12 |
| `market/test_context_service.py` | 28 | 28 | 0 | 0,07 |
| `market/test_finance_dashboard.py` | 23 | 23 | 0 | 0,09 |
| `market/test_market_route.py` | 17 | 17 | 0 | 0,10 |
| `market/test_market_summary.py` | 4 | 4 | 0 | 0,02 |
| `sentiment_analysis/test_sentiment_accuracy.py` | 1 | 1 | 0 | 6,10 |
| `sentiment_analysis/test_sentiment_modes.py` | 1 | 1 | 0 | 1,30 |
| `sentiment_analysis/test_transformer_primacy.py` | 21 | 21 | 0 | 2,31 |
| `statistical/test_employee_weighting.py` | 3 | 3 | 0 | 0,20 |
| `statistical/test_statistical_implementation.py` | 7 | 7 | 0 | 0,01 |
| `test_analyze_topic_rating.py` | 15 | 15 | 0 | 0,03 |
| `test_annotations_file.py` | 3 | 3 | 0 | 0,06 |
| `test_annotations_validator.py` | 66 | 66 | 0 | 0,13 |
| `test_blind_annotations.py` | 21 | 21 | 0 | 0,17 |
| `test_check_evaluation_instance.py` | 8 | 8 | 0 | 0,02 |
| `test_companies_review_counts.py` | 4 | 4 | 0 | 0,01 |
| `test_company_metadata.py` | 38 | 38 | 0 | 0,08 |
| `test_compare_annotations.py` | 32 | 32 | 0 | 0,12 |
| `test_csv_service.py` | 33 | 33 | 0 | 0,11 |
| `test_data_status.py` | 19 | 19 | 0 | 0,07 |
| `test_dz1_baselines.py` | 49 | 49 | 0 | 0,50 |
| `test_dz1_referenz_archiv.py` | 16 | 16 | 0 | 1,10 |
| `test_evaluate_detection.py` | 33 | 33 | 0 | 0,08 |
| `test_excel_service.py` | 19 | 19 | 0 | 0,05 |
| `test_fetch_all_rows_parallel.py` | 9 | 9 | 0 | 0,04 |
| `test_make_annotation_sheet.py` | 33 | 33 | 0 | 0,17 |
| `test_rating_series_service.py` | 17 | 17 | 0 | 0,04 |
| `test_ratings_pagination.py` | 10 | 10 | 0 | 0,06 |
| `test_remove_duplicates.py` | 5 | 5 | 0 | 0,01 |
| `test_rolling_average_service.py` | 19 | 19 | 0 | 0,05 |
| `test_score_service.py` | 15 | 15 | 0 | 0,05 |
| `test_score_uncertainty.py` | 8 | 8 | 0 | 0,02 |
| `test_seed_company_metadata.py` | 10 | 10 | 0 | 0,05 |
| `test_supabase_client_concurrency.py` | 3 | 3 | 0 | 0,01 |
| `test_topic_quotes_nfa07.py` | 4 | 4 | 0 | 0,01 |
| `test_user_events.py` | 29 | 29 | 0 | 0,10 |
| `topic_modeling/test_improved_topics.py` | 3 | 3 | 0 | 0,32 |
| `topic_modeling/test_lda_topic_modeling.py` | 15 | 15 | 0 | 0,88 |
| `topic_modeling/test_topic_modeling.py` | 3 | 3 | 0 | 0,13 |
| `topic_modeling/test_topic_overview.py` | 2 | 2 | 0 | 0,65 |

## Frontend je Testdatei

| Testdatei | Tests | Bestanden | Geprüft wird |
|---|---:|---:|---|
| `src/lib/__tests__/companies.test.js` | 4 | 4 | Branche eines Unternehmens und Vorschlag von Firmen derselben Branche im Vergleich |
| `src/lib/__tests__/comparisonText.test.js` | 3 | 3 | Hinweis auf Bewertungen ohne Freitext im Vergleich |
| `src/lib/__tests__/dimensionScope.test.js` | 10 | 10 | Dimension als globaler Filter |
| `src/lib/__tests__/reportSummary.test.js` | 12 | 12 | Regelbasierter Kurzbericht im PDF-Export |
| `src/lib/__tests__/userEvents.test.js` | 6 | 6 | Eigene Ereignisse |
| **Summe** | **35** | **35** | |

## Dateien ohne Tests

Vier Dateien heißen zwar `test_*.py`, sind aber eigenständige Auswertungsskripte. pytest sammelt aus ihnen keine Tests:

- `tests/sentiment_analysis/test_sentiment_comparison.py`
- `tests/topic_modeling/test_aggressive_topic_merging.py`
- `tests/topic_modeling/test_topic_accuracy.py`
- `tests/topic_modeling/test_topic_merging.py`

## Warnungen im Backend

Der Standardlauf meldet 50 Warnungen. Keine davon lässt einen Test fehlschlagen.

| Anzahl | Art | Herkunft | Bedeutung |
|---:|---|---|---|
| 16 | RuntimeWarning | statsmodels, ausgelöst in `forecast/test_forecast_edgecases.py` und `forecast/test_forecast_engine.py` | Division durch null im Logarithmus bei konstanten Reihen, unter anderem in `test_constant_values`, `test_constant_maximum` und `test_constant_minimum` |
| 12 | DeprecationWarning | Bibliothek pyiceberg | veraltete Pydantic- und pyparsing-Aufrufe in der Bibliothek |
| 6 | DeprecationWarning | supabase | die Parameter `timeout` und `verify` beim Anlegen des Clients sind veraltet |
| 6 | PytestReturnNotNoneWarning | Projekt-Tests | sechs Testfunktionen geben einen Wert zurück statt `None`: drei in `topic_modeling/test_topic_modeling.py`, zwei in `statistical/test_employee_weighting.py`, eine in `sentiment_analysis/test_sentiment_accuracy.py` |
| 5 | DeprecationWarning | transformers | veraltete Erzeugung des WordPiece-Tokenizers |
| 5 | RuntimeWarning | gensim, ausgelöst in `topic_modeling/test_lda_topic_modeling.py` und `topic_modeling/test_topic_modeling.py` | ungültiger Wert bei einer Division im LDA-Modell von gensim |

## Hinweis aus dem Build

`vite build` läuft durch und meldet, dass die Haupt-JavaScript-Datei größer als 500 kB ist:

| Datei | Größe | komprimiert (gzip) |
|---|---:|---:|
| `index-*.js` | 2.013,97 kB | 590,26 kB |
| `index.es-*.js` | 159,72 kB | 53,54 kB |
| `purify.es-*.js` | 29,40 kB | 11,31 kB |
| `index-*.css` | 100,07 kB | 18,74 kB |

Das ist ein Hinweis zur Ladezeit, kein Fehler. Vite schlägt vor, die Datei mit dynamischen `import()`-Aufrufen aufzuteilen.
