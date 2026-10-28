# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import json
import os
import re
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import validate_annotations as va  # noqa: E402

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(BACKEND_DIR, "data", "annotations.json")
DENSITY = os.path.join(BACKEND_DIR, "data", "data_density.json")
SERIES_DIR = os.path.join(BACKEND_DIR, "data", "series")

FROZEN_F50B727 = [
    ("SAP SE", "employee", "durchschnittsbewertung", "2024-07", "2024-08", "rise"),
    ("NTT DATA SE", "employee", "durchschnittsbewertung", "2020-06", "2020-06", "rise"),
    ("1&1 AG", "employee", "durchschnittsbewertung", "2016-10", "2016-10", "fall"),
    ("1&1 AG", "employee", "durchschnittsbewertung", "2018-04", "2018-04", "rise"),
    ("1&1 AG", "employee", "durchschnittsbewertung", "2018-09", "2018-09", "fall"),
    ("Bechtle", "employee", "durchschnittsbewertung", "2021-02", "2021-02", "rise"),
    ("Bechtle", "employee", "durchschnittsbewertung", "2021-08", "2021-09", "fall"),
    ("Bechtle", "employee", "durchschnittsbewertung", "2023-01", "2023-01", "rise"),
    ("Cancom", "employee", "durchschnittsbewertung", "2016-08", "2016-08", "rise"),
    ("Cancom", "employee", "durchschnittsbewertung", "2021-07", "2021-07", "fall"),
    ("Cancom", "employee", "durchschnittsbewertung", "2023-12", "2023-12", "rise"),
    ("Compugroup Medical Deutschland", "employee", "durchschnittsbewertung", "2019-06", "2019-08", "fall"),
    ("Compugroup Medical Deutschland", "employee", "durchschnittsbewertung", "2021-04", "2021-05", "rise"),
    ("Compugroup Medical Deutschland", "employee", "durchschnittsbewertung", "2022-08", "2022-11", "fall"),
    ("Telekom", "employee", "durchschnittsbewertung", "2009-12", "2009-12", "rise"),
    ("Telekom", "employee", "durchschnittsbewertung", "2010-07", "2010-07", "fall"),
    ("Telekom", "employee", "durchschnittsbewertung", "2013-05", "2013-05", "rise"),
    ("Freenet", "employee", "durchschnittsbewertung", "2016-04", "2016-04", "rise"),
    ("Freenet", "employee", "durchschnittsbewertung", "2020-02", "2020-02", "rise"),
    ("Freenet", "employee", "durchschnittsbewertung", "2021-09", "2021-09", "fall"),
]
KEYS = ("company", "source", "dimension", "period_from", "period_to", "direction")


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def test_real_file_validates_offline_without_errors():
    companies = va.companies_from_density(_load(DENSITY))
    warnings = []
    assert va.attach_series_counts(companies, SERIES_DIR, warnings) > 0
    result = va.validate(_load(ANNOTATIONS), companies)
    assert result.ok, result.errors


def test_real_file_content_frozen_at_f50b727():
    doc = _load(ANNOTATIONS)
    assert [tuple(a[k] for k in KEYS) for a in doc["annotations"]] == FROZEN_F50B727
    assert all(set(a) == set(KEYS) | {"note"} for a in doc["annotations"])
    assert isinstance(doc["version"], int) and doc["version"] >= 1


_FORBIDDEN = [
    re.compile(r"ed\.DEFAULT_FILE"),
    re.compile(r"DEFAULT_ANNOTATIONS"),
    re.compile(r"""["']data/annotations(_zweitperson)?\.json["']"""),
    re.compile(r"""["']data["']\s*,\s*["']annotations(_zweitperson)?\.json["']"""),
]


def test_no_test_applies_scripts_to_real_file():
    own = os.path.abspath(__file__)
    offenders = []
    for root, _dirs, files in os.walk(TESTS_DIR):
        for name in files:
            path = os.path.abspath(os.path.join(root, name))
            if not name.endswith(".py") or path == own:
                continue
            text = open(path, encoding="utf-8").read()
            offenders += [f"{name}: {p.pattern}" for p in _FORBIDDEN if p.search(text)]
            if "import report_explanation_validity" in text:
                for call in re.findall(r"\b(?:script|sc)\.main\(\[[^\]]*\]", text):
                    if "--annotations" not in call:
                        offenders.append(f"{name}: {call}")
    assert offenders == []
