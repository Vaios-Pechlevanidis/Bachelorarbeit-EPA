# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

from __future__ import annotations

import argparse
import csv
import glob
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import evaluate_detection as ed  # noqa: E402
import validate_annotations as va  # noqa: E402
from models.changepoint_detector import WEIGHTING_COUNT, WEIGHTING_NONE  # noqa: E402
from services.anomaly_service import detect_anomalies  # noqa: E402
from services.rating_series_service import MIN_REVIEWS_PER_MONTH, OVERALL_DIMENSION, is_eligible, review_sd  # noqa: E402

SOURCE = "employee"
DIMENSION = OVERALL_DIMENSION
VARIANTS: Tuple[str, ...] = (WEIGHTING_NONE, WEIGHTING_COUNT)
DEFAULT_ANNOTATIONS = os.path.join(BACKEND_DIR, "data", "annotations.json")
DEFAULT_DZ1 = os.path.join(BACKEND_DIR, "data", "calibration", "dz1_ergebnis.json")
DEFAULT_SERIES_DIR = os.path.join(BACKEND_DIR, "data", "series")
DEFAULT_DENSITY = os.path.join(BACKEND_DIR, "data", "data_density.json")
RECHNER = os.path.join(REPO_DIR, "docs", "dz1-referenz", "dz1_rechner.py")
NOTE = ("Post hoc und explorativ: Die DZ1-Auswertung vom 2026-10-10 (dz1_ergebnis.json) bleibt das Ergebnis der "
        "Arbeit. Die gewichtete Variante wurde vor diesem Abgleich festgelegt (Strafterm-Faktor, min_size, min_delta "
        "unverändert) und zuerst semisynthetisch geprüft; hier wird nichts an der Referenz eingestellt. Die Kandidaten "
        "stammen aus dem archivierten Regelprüfer (scan) und sind regelkonforme Zeiträume, die nicht in der Referenz "
        "stehen, z. B. wegen Regel 5 (höchstens drei je Reihe).")


def load_rechner():
    spec = importlib.util.spec_from_file_location("dz1_rechner", RECHNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def series_from_csv(path: str) -> List[Dict[str, Any]]:
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            raw = (r.get("mean_durchschnittsbewertung") or "").strip()
            n = int(r.get("count") or 0)
            out.append({"period": r["period"], "mean": float(raw) if raw else None, "count": n, "n_values": n,
                        "evaluated": bool(raw) and n >= MIN_REVIEWS_PER_MONTH})
    return sorted(out, key=lambda m: m["period"])


def find_csvs(series_dir: str) -> Dict[int, str]:
    out = {}
    for path in glob.glob(os.path.join(series_dir, f"*_{SOURCE}.csv")):
        head = os.path.basename(path).split("_", 1)[0]
        if head.isdigit():
            out[int(head)] = path
    return out


def classify_extra(extra: Dict[str, Any], candidates: Tuple[List[Dict[str, Any]], List[Dict[str, Any]]],
                   evaluated: set) -> str:
    good, doubtful = candidates
    for label, group in (("regelkonformer_kandidat", good), ("zweifelsfall", doubtful)):
        for c in group:
            if c.get("richtung") != extra["direction"]:
                continue
            lo, hi = ed.match_window(c["von"], c["bis"], evaluated)
            if lo <= extra["date"] <= hi:
                return label
    return "kein_kandidat"


def _sum(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    fn = sum(r["fn"] for r in rows)
    fp_cand = sum(r["fp_kandidat"]["regelkonformer_kandidat"] for r in rows)
    fp_doubt = sum(r["fp_kandidat"]["zweifelsfall"] for r in rows)
    m = ed.metrics(tp, fp, fn)
    m_cand = ed.metrics(tp, fp - fp_cand, fn)
    r4 = lambda x: None if x is None else round(x, 4)  # noqa: E731
    return {"tp": tp, "fp": fp, "fn": fn, "precision": r4(m["precision"]), "recall": r4(m["recall"]), "f1": r4(m["f1"]),
            "fp_regelkonformer_kandidat": fp_cand, "fp_zweifelsfall": fp_doubt, "fp_kein_kandidat": fp - fp_cand - fp_doubt,
            "precision_ohne_kandidaten_fp": r4(m_cand["precision"]), "f1_ohne_kandidaten_fp": r4(m_cand["f1"])}


def run(annotations: Dict[str, Any], names: Dict[int, str], csvs: Dict[int, str], sds: Dict[int, Optional[float]],
        rechner) -> Dict[str, Any]:
    by_company: Dict[str, List[Dict[str, Any]]] = {}
    for ann in annotations.get("annotations") or []:
        if ann.get("source") == SOURCE and ann.get("dimension") == DIMENSION:
            by_company.setdefault(ann["company"], []).append(ann)
    per_series = []
    for cid in sorted(csvs):
        series = series_from_csv(csvs[cid])
        if not is_eligible(series):
            continue
        name = names.get(cid, str(cid))
        anns = by_company.get(name, [])
        evaluated = {m["period"] for m in series if m["evaluated"]}
        candidates = rechner.scan(rechner.lese(csvs[cid]))
        entry: Dict[str, Any] = {"company_id": cid, "company": name, "annotated": bool(anns),
                                 "evaluated_months": len(evaluated), "n_annotations": len(anns),
                                 "review_sd": None if sds.get(cid) is None else round(float(sds[cid]), 4),
                                 "n_kandidaten_regelkonform": len(candidates[0]), "variants": {}}
        for variant in VARIANTS:
            found = detect_anomalies(series, company_id=cid, source=SOURCE, dimension=DIMENSION, weighting=variant,
                                     review_sd=sds.get(cid) if variant == WEIGHTING_COUNT else None)
            dets = ed.detections_from_result({"anomalies": found}, with_outliers=False)
            match = ed.match_series(anns, dets, evaluated)
            kinds = {"regelkonformer_kandidat": 0, "zweifelsfall": 0, "kein_kandidat": 0}
            extras = []
            for e in match["extras"]:
                label = classify_extra(e, candidates, evaluated)
                kinds[label] += 1
                extras.append({**e, "kandidat": label})
            entry["variants"][variant] = {"tp": match["tp"], "fp": match["fp"], "fn": match["fn"], "fp_kandidat": kinds,
                                          "hits": [{"annotation": h["annotation"], "detection": h["detection"]} for h in match["hits"]],
                                          "misses": [m["annotation"] for m in match["misses"]], "extras": extras,
                                          "params": found[0]["params"] if found else None}
        per_series.append(entry)
    totals = {}
    for scope, keep in (("hauptwert", lambda s: s["annotated"]), ("regelkonform", lambda s: True)):
        totals[scope] = {v: _sum([s["variants"][v] for s in per_series if keep(s)]) for v in VARIANTS}
    paired = {"nur_ungewichtet": 0, "nur_gewichtet": 0, "beide": 0, "keine": 0}
    for s in per_series:
        if not s["annotated"]:
            continue
        hit_sets = {v: {(h["annotation"]["period_from"], h["annotation"]["period_to"]) for h in s["variants"][v]["hits"]} for v in VARIANTS}
        for ann in by_company.get(s["company"], []):
            k = (ann["period_from"], ann["period_to"])
            a, b = k in hit_sets[WEIGHTING_NONE], k in hit_sets[WEIGHTING_COUNT]
            paired["beide" if a and b else "nur_ungewichtet" if a else "nur_gewichtet" if b else "keine"] += 1
    return {"series": per_series, "totals": totals, "paired_annotations": paired}


def check_reproduction(result: Dict[str, Any], dz1: Dict[str, Any]) -> Dict[str, Any]:
    ref = {s["company_id"]: s["variants"]["niveauwechsel"] for s in dz1.get("series") or []}
    problems = []
    for s in result["series"]:
        if s["company_id"] not in ref:
            continue
        mine, theirs = s["variants"][WEIGHTING_NONE], ref[s["company_id"]]
        if (mine["tp"], mine["fp"], mine["fn"]) != (theirs["tp"], theirs["fp"], theirs["fn"]):
            problems.append(f"{s['company']}: {mine['tp']}/{mine['fp']}/{mine['fn']} statt {theirs['tp']}/{theirs['fp']}/{theirs['fn']}")
    return {"ok": not problems, "problems": problems,
            "detail": "ungewichtete Variante aus den Serien-CSVs gleich dz1_ergebnis.json (TP/FP/FN je annotierter Reihe)"}


def _pct(x: Optional[float]) -> str:
    return "–" if x is None else f"{100 * x:.1f} %".replace(".", ",")


def _f(x: Optional[float]) -> str:
    return "–" if x is None else f"{x:.3f}".replace(".", ",")


def format_report(report: Dict[str, Any]) -> str:
    lines = ["# DZ1 post hoc: Gewichtung nach Bewertungszahl und Fehlalarme gegen Regelkandidaten", "",
             report["note"], "",
             f"Prüfung: {report['check']['detail']}: {'ja' if report['check']['ok'] else 'NEIN – ' + '; '.join(report['check']['problems'])}.", ""]
    for scope, label in (("hauptwert", "Annotierte Reihen (wie DZ1-Hauptwert)"), ("regelkonform", "Alle geeigneten Reihen (Markierungen in Reihen ohne Eintrag zählen als FP)")):
        lines += [f"**{label}**", "",
                  "| Variante | TP | FP | FN | Precision | Recall | F1 | FP = regelkonformer Kandidat | FP = Zweifelsfall | FP ohne Kandidat | Precision ohne Kandidaten-FP | F1 ohne Kandidaten-FP |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for v in VARIANTS:
            t = report["totals"][scope][v]
            lines.append(f"| {'ungewichtet (DZ1)' if v == WEIGHTING_NONE else 'gewichtet'} | {t['tp']} | {t['fp']} | {t['fn']} | {_pct(t['precision'])} | "
                         f"{_pct(t['recall'])} | {_f(t['f1'])} | {t['fp_regelkonformer_kandidat']} | {t['fp_zweifelsfall']} | {t['fp_kein_kandidat']} | "
                         f"{_pct(t['precision_ohne_kandidaten_fp'])} | {_f(t['f1_ohne_kandidaten_fp'])} |")
        lines.append("")
    p = report["paired_annotations"]
    lines += [f"Gepaart je Referenzzeitraum (20): beide finden {p['beide']}, nur ungewichtet {p['nur_ungewichtet']}, "
              f"nur gewichtet {p['nur_gewichtet']}, keine {p['keine']}.", "",
              "**Je Reihe**", "",
              "| Reihe | Einträge | s je Bewertung | ungewichtet TP/FP/FN | gewichtet TP/FP/FN | gewichtet: Markierungen |", "|---|---|---|---|---|---|"]
    for s in report["series"]:
        a, b = s["variants"][WEIGHTING_NONE], s["variants"][WEIGHTING_COUNT]
        marks = ", ".join(sorted([h["detection"]["date"] + " " + h["detection"]["direction"] + " (TP)" for h in b["hits"]] +
                                 [e["date"] + " " + e["direction"] + f" ({e['kandidat']})" for e in b["extras"]])) or "–"
        lines.append(f"| {s['company']} | {s['n_annotations']} | {_f(s['review_sd'])} | {a['tp']}/{a['fp']}/{a['fn']} | {b['tp']}/{b['fp']}/{b['fn']} | {marks} |")
    return "\n".join(lines) + "\n"


def load_sds(rows_path: Optional[str], ids: Sequence[int], default: Optional[float]) -> Dict[int, Optional[float]]:
    if default is not None:
        return {cid: default for cid in ids}
    if rows_path:
        with open(rows_path, encoding="utf-8") as fh:
            cached = json.load(fh)
        return {cid: review_sd(cached[str(cid)]["rows"], DIMENSION) if str(cid) in cached else None for cid in ids}
    from services.rating_series_service import fetch_review_rows
    return {cid: review_sd(fetch_review_rows(SOURCE, cid, DIMENSION), DIMENSION) for cid in ids}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="DZ1 post hoc (explorativ): gewichtete Erkennung und Fehlalarme gegen die regelkonformen Kandidaten des Regelprüfers.")
    parser.add_argument("--annotations", default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--dz1", default=DEFAULT_DZ1)
    parser.add_argument("--series-dir", default=DEFAULT_SERIES_DIR)
    parser.add_argument("--density", default=DEFAULT_DENSITY)
    parser.add_argument("--rows", help="zwischengespeicherte Bewertungen für s je Bewertung (sonst Datenbank, nur SELECT)")
    parser.add_argument("--review-sd", type=float, help="feste Streuung je Bewertung für alle Reihen (ohne Datenbank)")
    parser.add_argument("--json", dest="json_out")
    parser.add_argument("--md", dest="md_out")
    args = parser.parse_args(argv)

    with open(args.annotations, encoding="utf-8") as fh:
        annotations = json.load(fh)
    with open(args.dz1, encoding="utf-8") as fh:
        dz1 = json.load(fh)
    density, err = va._load_json(args.density, "data_density.json")
    if err:
        raise SystemExit(f"FEHLER: {err}")
    names = {int(i.id): i.name for i in va.companies_from_density(density).values() if i.id is not None}
    csvs = find_csvs(args.series_dir)
    sds = load_sds(args.rows, sorted(csvs), args.review_sd)
    result = run(annotations, names, csvs, sds, load_rechner())
    report = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "note": NOTE,
              "argv": list(argv) if argv is not None else sys.argv[1:],
              "review_sd_source": "fest" if args.review_sd is not None else ("cache" if args.rows else "datenbank"),
              "check": check_reproduction(result, dz1), **result}
    text = format_report(report)
    print(text)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    if args.md_out:
        with open(args.md_out, "w", encoding="utf-8") as fh:
            fh.write("> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.\n\n" + text)
    return 0 if report["check"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
