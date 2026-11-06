# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import simulate_detection as sd  # noqa: E402
from models.changepoint_detector import WEIGHTING_COUNT, WEIGHTING_NONE  # noqa: E402
from services.anomaly_service import detect_anomalies  # noqa: E402
from services.rating_series_service import build_monthly_series, review_sd  # noqa: E402

VARIANTS: Tuple[str, ...] = (WEIGHTING_NONE, WEIGHTING_COUNT)
BOOTSTRAP = 2000

Row = Dict[str, Any]


WEIGHTED_FACTOR = 2.0


def detect_variant(series: Sequence[Row], company_id: int, weighting: str, sd_review: Optional[float]) -> Dict[str, Any]:
    factor = WEIGHTED_FACTOR if weighting == WEIGHTING_COUNT else sd.PeltDetector().penalty_factor
    found = detect_anomalies(list(series), company_id=company_id, source=sd.SOURCE, dimension=sd.DIMENSION,
                             weighting=weighting, review_sd=sd_review, penalty_factor=factor)
    evaluated = sd.evaluated_of(series)
    return {"found": found, "evaluated": {m["period"] for m in evaluated},
            "sigma": sd.noise_sigma([float(m["mean"]) for m in evaluated])}


def run_company_rep(rows: Sequence[Row], company_id: int, rep: int, deltas: Sequence[float],
                    seed: int = sd.SEED, margin: int = sd.MARGIN) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(np.random.SeedSequence([int(seed), int(company_id), int(rep)]))
    permuted = sd.permute_values(rows, sd.COLUMN, rng)
    noisy: Dict[str, List[Row]] = {"bewertungen": build_monthly_series(permuted, sd.COLUMN)}
    n_b = len(sd.evaluated_of(noisy["bewertungen"]))
    draws = {("bewertungen", "mitte"): (sd.choose_change_index(n_b, margin, rng), 1 if rng.random() < 0.5 else -1)}
    draws[("bewertungen", "ende")] = (sd.choose_end_index(n_b, margin, rng), 1 if rng.random() < 0.5 else -1)
    noisy["monate"] = sd.permute_months(build_monthly_series(list(rows), sd.COLUMN), rng)
    n_m = len(sd.evaluated_of(noisy["monate"]))
    draws[("monate", "mitte")] = (sd.choose_change_index(n_m, margin, rng), 1 if rng.random() < 0.5 else -1)
    sds = {"bewertungen": review_sd(permuted, sd.COLUMN), "monate": review_sd(list(rows), sd.COLUMN)}

    null = {(c, v): detect_variant(noisy[c], company_id, v, sds[c]) for c in sd.CONDITIONS for v in VARIANTS}
    out: List[Dict[str, Any]] = []
    for condition, placement in sd.DESIGN:
        series = noisy[condition]
        evaluated = sd.evaluated_of(series)
        k, sign = draws[(condition, placement)]
        change_period = evaluated[k]["period"]
        direction = "rise" if sign > 0 else "fall"
        base = {
            "company_id": int(company_id), "rep": int(rep), "condition": condition, "placement": placement,
            "change_period": change_period, "direction": direction,
            "n_at_change": int(evaluated[k].get("n_values", evaluated[k].get("count", 0))),
            "n_neighbours": sd.neighbour_reviews(evaluated, k),
            "gap_before": sd.months_between(evaluated[k - 1]["period"], change_period) - 1,
            "review_sd": round(float(sds[condition]), 4),
        }
        for delta in deltas:
            shifted = sd.inject_shift(series, change_period, sign * float(delta)) if delta else series
            for variant in VARIANTS:
                detection = null[(condition, variant)] if not delta else detect_variant(shifted, company_id, variant, sds[condition])
                out.append({**base, "variant": variant, "delta": float(delta),
                            **sd.match_change(detection, change_period, direction),
                            "n_outliers": 0, "sigma_sim": round(detection["sigma"], 4),
                            "out_of_range": any(not 1.0 <= float(m["mean"]) <= 5.0 for m in sd.evaluated_of(shifted))})
    return out


_DATA: Dict[int, List[Row]] = {}


def _init(data: Dict[int, List[Row]], factor: float = 2.0) -> None:
    global _DATA, WEIGHTED_FACTOR
    _DATA = data
    WEIGHTED_FACTOR = factor


def _task(args: Tuple[int, int, Tuple[float, ...], int, int]) -> List[Dict[str, Any]]:
    cid, rep, deltas, seed, margin = args
    return run_company_rep(_DATA[cid], cid, rep, deltas, seed, margin)


def simulate(data: Dict[int, List[Row]], reps: int, deltas: Sequence[float], seed: int, margin: int,
             workers: int, factor: float = 2.0) -> List[Dict[str, Any]]:
    tasks = [(cid, rep, tuple(deltas), seed, margin) for cid in sorted(data) for rep in range(reps)]
    if workers <= 1:
        _init(data, factor)
        chunks = [_task(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(data, factor)) as pool:
            chunks = list(pool.map(_task, tasks, chunksize=max(1, len(tasks) // (workers * 8))))
    return [r for chunk in chunks for r in chunk]


def _key(r: Dict[str, Any]) -> Tuple[Any, ...]:
    return (r["company_id"], r["rep"], r["condition"], r["placement"], r["delta"])


def paired(records: Sequence[Dict[str, Any]], seed: int, draws: int = BOOTSTRAP) -> List[Dict[str, Any]]:
    by_variant: Dict[str, Dict[Tuple[Any, ...], Dict[str, Any]]] = {v: {} for v in VARIANTS}
    for r in records:
        by_variant[r["variant"]][_key(r)] = r
    groups: Dict[Tuple[str, str, float], List[Tuple[Dict[str, Any], Dict[str, Any]]]] = {}
    for k, a in by_variant[WEIGHTING_NONE].items():
        b = by_variant[WEIGHTING_COUNT][k]
        groups.setdefault((a["condition"], a["placement"], a["delta"]), []).append((a, b))
    out = []
    for (condition, placement, delta), pairs in sorted(groups.items(), key=lambda kv: (sd.DESIGN.index(kv[0][:2]), kv[0][2])):
        if delta:
            stat = lambda r: 1.0 if r["hit"] else 0.0  # noqa: E731
            label = "Trefferquote"
        else:
            stat = lambda r: 1.0 if r["n_detections"] else 0.0  # noqa: E731
            label = "Anteil Reihen mit Fehlalarm"
        extra = lambda r: float(r["extras"])  # noqa: E731
        per_series: Dict[int, List[Tuple[float, float, float, float]]] = {}
        for a, b in pairs:
            per_series.setdefault(a["company_id"], []).append((stat(a), stat(b), extra(a), extra(b)))
        cids = sorted(per_series)

        def means(sel: Sequence[int]) -> Tuple[float, float, float, float]:
            vals = [v for c in sel for v in per_series[c]]
            arr = np.asarray(vals)
            return tuple(float(x) for x in arr.mean(axis=0))

        m = means(cids)
        rng = random.Random(f"{seed}/{condition}/{placement}/{delta}")
        diffs, ediffs = [], []
        for _ in range(draws):
            sel = [rng.choice(cids) for _ in cids]
            mm = means(sel)
            diffs.append(mm[1] - mm[0])
            ediffs.append(mm[3] - mm[2])
        only_none = sum(1 for a, b in pairs if stat(a) > stat(b))
        only_count = sum(1 for a, b in pairs if stat(b) > stat(a))
        n_disc = only_none + only_count
        p_sign = None
        if n_disc:
            k = min(only_none, only_count)
            p_sign = min(1.0, 2 * sum(math.comb(n_disc, i) for i in range(k + 1)) / 2 ** n_disc)
        out.append({
            "condition": condition, "placement": placement, "delta": delta, "measure": label, "n": len(pairs),
            "ungewichtet": round(m[0], 4), "gewichtet": round(m[1], 4), "differenz": round(m[1] - m[0], 4),
            "differenz_bootstrap95": [round(float(np.percentile(diffs, 2.5)), 4), round(float(np.percentile(diffs, 97.5)), 4)],
            "nur_ungewichtet": only_none, "nur_gewichtet": only_count, "p_vorzeichen": p_sign,
            "extras_ungewichtet": round(m[2], 4), "extras_gewichtet": round(m[3], 4),
            "extras_differenz_bootstrap95": [round(float(np.percentile(ediffs, 2.5)), 4), round(float(np.percentile(ediffs, 97.5)), 4)],
        })
    return out


def strata_thin(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: Dict[Tuple[str, str, float, str, str], List[int]] = {}
    for r in records:
        if not r["delta"]:
            continue
        label = f"n<{sd.THIN_N}" if r["n_at_change"] < sd.THIN_N else f"n>={sd.THIN_N}"
        out.setdefault((r["condition"], r["placement"], r["delta"], label, r["variant"]), []).append(1 if r["hit"] else 0)
    rows = []
    for (c, p, d, label, v), hits in sorted(out.items()):
        rows.append({"condition": c, "placement": p, "delta": d, "wechselmonat": label, "variant": v,
                     "reps": len(hits), "recall": round(sum(hits) / len(hits), 4)})
    return rows


def _pct(x: Optional[float]) -> str:
    return "–" if x is None else f"{100 * x:.1f} %".replace(".", ",")


def _pp(x: float) -> str:
    return f"{100 * x:+.1f}".replace(".", ",")


def format_report(report: Dict[str, Any]) -> str:
    lines = ["# Gewichtung nach Bewertungszahl: semisynthetischer Vergleich (DZ1)", "",
             f"{len(report['series'])} Reihen × {report['params']['reps']} Wiederholungen, "
             f"Startwert {report['params']['seed']}; Strafterm-Faktor gewichtet {report['params']['penalty_factor'][WEIGHTING_COUNT]:g}, ungewichtet 2. Gepaart: beide Varianten auf denselben Reihen, Wechseln und Richtungen.", "",
             "| Bedingung | Lage | Δ | Maß | ungewichtet | gewichtet | Differenz (pp) | 95 %-Intervall (Cluster-Bootstrap) | nur ungew. / nur gew. | p (Vorzeichen) | weitere Markierungen je Reihe ungew. / gew. |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in report["paired"]:
        iv = r["differenz_bootstrap95"]
        p = "–" if r["p_vorzeichen"] is None else (f"{r['p_vorzeichen']:.3f}".replace(".", ",") if r["p_vorzeichen"] >= 0.001 else "< 0,001")
        lines.append(f"| {r['condition']} | {r['placement']} | {r['delta']:g} | {r['measure']} | {_pct(r['ungewichtet'])} | {_pct(r['gewichtet'])} | "
                     f"{_pp(r['differenz'])} | [{_pp(iv[0])}; {_pp(iv[1])}] | {r['nur_ungewichtet']} / {r['nur_gewichtet']} | {p} | "
                     f"{r['extras_ungewichtet']:.2f} / {r['extras_gewichtet']:.2f} |".replace(".", ","))
    lines += ["", "**Trefferquote nach Belegung des Wechselmonats**", "",
              "| Bedingung | Lage | Δ | Wechselmonat | Wiederholungen | ungewichtet | gewichtet |", "|---|---|---|---|---|---|---|"]
    th: Dict[Tuple[str, str, float, str], Dict[str, Any]] = {}
    for r in report["strata_wechselmonat"]:
        th.setdefault((r["condition"], r["placement"], r["delta"], r["wechselmonat"]), {})[r["variant"]] = r
    for (c, p, d, label), v in sorted(th.items(), key=lambda kv: (sd.DESIGN.index(kv[0][:2]), kv[0][2], kv[0][3])):
        lines.append(f"| {c} | {p} | {d:g} | {label} | {v[WEIGHTING_NONE]['reps']} | {_pct(v[WEIGHTING_NONE]['recall'])} | {_pct(v[WEIGHTING_COUNT]['recall'])} |")
    lines += ["", "Lesart: Δ 0 = Reihe ohne eingesetzten Wechsel; jede Markierung ist dort ein Fehlalarm. "
              "„bewertungen“ mischt die Einzelnoten über die Monate (nur Stichprobenrauschen), „monate“ mischt ganze Monate "
              "(echte Schwankung zwischen Monaten bleibt). Gewichtet: Kosten je Monat mit 1/(τ² + s²/n), s = Streuung "
              "innerhalb der Monate, τ robust aus den Monatsdifferenzen; Strafterm 2·ln(n) wie bisher in Einheiten der Varianz."]
    return "\n".join(lines) + "\n"


def load_rows(path: Optional[str], companies: Sequence[Tuple[int, str]]) -> Dict[int, Tuple[str, List[Row]]]:
    if path:
        with open(path, encoding="utf-8") as fh:
            cached = json.load(fh)
        return {int(cid): (e["name"], e["rows"]) for cid, e in cached.items() if int(cid) in {c for c, _ in companies}}
    return {cid: (name, sd.fetch_rows(cid)) for cid, name in companies}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gepaarter semisynthetischer Vergleich: PELT ungewichtet gegen gewichtet nach Bewertungszahl (DZ1).")
    parser.add_argument("--reps", type=int, default=sd.REPS)
    parser.add_argument("--deltas", type=float, nargs="+", default=list(sd.DELTAS))
    parser.add_argument("--seed", type=int, default=sd.SEED)
    parser.add_argument("--margin", type=int, default=sd.MARGIN)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--company", type=int, action="append")
    parser.add_argument("--density", default=sd.DEFAULT_DENSITY)
    parser.add_argument("--weighted-factor", type=float, default=2.0,
                        help="Strafterm-Faktor nur der gewichteten Variante (ungewichtet bleibt beim Standard 2,0)")
    parser.add_argument("--rows", help="zwischengespeicherte Bewertungen (JSON {id: {name, rows}}) statt Datenbank")
    parser.add_argument("--json", dest="json_out")
    parser.add_argument("--md", dest="md_out")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    deltas = tuple(sorted(dict.fromkeys(float(d) for d in args.deltas)))
    started = time.time()
    loaded = load_rows(args.rows, sd.load_companies(args.density, args.company))
    data: Dict[int, List[Row]] = {}
    series = []
    for cid in sorted(loaded):
        name, rows = loaded[cid]
        info = sd.describe_series(rows, cid)
        if not info["eligible"] or info["evaluated_months"] < 2 * args.margin:
            continue
        data[cid] = rows
        series.append({"company_id": cid, "company": name, "evaluated_months": info["evaluated_months"],
                       "review_sd": round(float(review_sd(rows, sd.COLUMN)), 4), "fingerprint": sd.fingerprint(rows)})
    print(f"Simuliere {len(data)} Reihen × {args.reps} Wiederholungen × 2 Varianten …", file=sys.stderr)
    records = simulate(data, args.reps, deltas, args.seed, args.margin, args.workers, args.weighted_factor)
    months = {s["company_id"]: s["evaluated_months"] for s in series}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_s": round(time.time() - started, 1),
        "argv": list(argv) if argv is not None else sys.argv[1:],
        "git": sd.git_state(),
        "versions": sd._versions(),
        "params": {"reps": args.reps, "deltas": list(deltas), "seed": args.seed, "margin": args.margin,
                   "design": [list(d) for d in sd.DESIGN], "variants": list(VARIANTS), "bootstrap": BOOTSTRAP,
                   "penalty_factor": {WEIGHTING_NONE: 2.0, WEIGHTING_COUNT: args.weighted_factor},
                   "rows_source": "cache" if args.rows else "datenbank"},
        "series": series,
        "paired": paired(records, args.seed),
        "strata_wechselmonat": strata_thin(records),
        "aggregate": {v: sd.aggregate([r for r in records if r["variant"] == v], deltas, months, args.seed)["total"]
                      for v in VARIANTS},
    }
    text = format_report(report)
    print(text)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    if args.md_out:
        with open(args.md_out, "w", encoding="utf-8") as fh:
            fh.write("> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.\n\n" + text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
