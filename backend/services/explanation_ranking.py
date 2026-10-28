from __future__ import annotations

import re
from datetime import date as _date
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from services.event_categories import classify_title, load_event_categories
from services.evidence_service import KIND_CHANGE, KIND_OUTLIER, KIND_SELECTION, month_index
from services.evidence_sources import TYPE_ADHOC, TYPE_GLOBAL, TYPE_NEWS
from services.keyword_topic_service import EXPLANATION_TOPIC_TEXT_FIELDS, topic_definitions_for, topics_in_review
from services.review_terms import MIN_TERM_LENGTH, STOPWORDS, match_terms, term_set

_TITLE_WORD_RE = re.compile(r"[a-zäöüß0-9&]+")
_INNER_DOT_RE = re.compile(r"(?<=[a-zäöüß0-9])\.(?=[a-zäöüß0-9])")


TERM_MATCH_PER_TERM = 0.5
TERM_MATCH_STRONG = 1.0
TERM_STRONG_MIN_AFTER = 5
TERM_STRONG_MIN_RATIO = 3.0
TERM_STRONG_MIN_SHIFT = 0.05

TOPIC_SHIFT_MIN_PP = 5.0
CATEGORY_MATCH_WITH_SHIFT = 1.0
CATEGORY_MATCH_ONLY = 0.5

TIME_NEAR = 1.0
TIME_AFTER_FACTOR = 0.5

TOPIC_STRONG = 1.0
TOPIC_WEAK = 0.5
TIME_MID = 0.5
TIME_MIN = 0.3

RULES_VERSION = 2
RULES_VERSION_DATE = "2026-10-08"
TEXT_VERSION = 1
TEXT_VERSION_DATE = "2026-10-23"
TERM_IN_TITLE = "title"
TERM_IN_TEXT = "text"
TEXT_TERM_MAX_SHARE = 0.2
TEXT_TERM_MIN_HITS = 3
TEXT_NOTE = ("Liegt zu einer Meldung der Text vor (EQS-Mitteilungen vollständig, Presseartikel für die Kandidaten der "
             "Markierungs- und Vergleichsfenster), sucht der Wortbezug die Begriffe der Bewertungen auch im Text; "
             "je Begriff steht, ob er im Titel oder im Text steht. Ein Begriff, der in mehr als 20 % der Texte des "
             "Fensters steht (mindestens 3 Texte), zählt im Text nicht, weil er dort nichts kennzeichnet. Ereignisart, "
             "Arbeitgeberbezug und die Nennung des Unternehmens kommen weiter aus dem Titel. Meldungen ohne gespeicherten "
             "Text werden nur über den Titel bewertet.")
CORRECTIONS = (
    "2026-10-13: Schlüsselwort 'verdi' nur als ganzes Wort (trifft nicht mehr 'verdient', 'verdienen'; E22)",
    "2026-10-13: Begriffe, Themen und Stimmung der Bewertungen mit den Kommentaren zu den Kategorien (E10, E11, E21)",
    "2026-10-13: Vergleichsfenster begrenzt durch den ersten und letzten bewerteten statt datierten Monat (E18)",
    "2026-10-13: 'Unternehmen im Titel genannt' erkennt Namen mit Punkt oder Ziffern (E.ON, 1&1; ohne Einfluss auf die Stufe)",
    "2026-10-13: EQS-Mitteilungen heißen nur bei der EQS-Kategorie 'Ad-hoc' Ad-hoc-Mitteilung (E19; ohne Einfluss auf die Stufe)",
    "2026-10-23: Stoppwörter um Funktionswörter, Adverbien und Modalverben ergänzt ('andere', 'bisher', 'deutlich', …; E35)",
)

STAGE_HIGH, STAGE_MEDIUM, STAGE_LOW, STAGE_NONE = "hoch", "mittel", "niedrig", "keine"
STAGES = (STAGE_HIGH, STAGE_MEDIUM, STAGE_LOW, STAGE_NONE)
_STAGE_RANK = {s: i for i, s in enumerate(STAGES)}

STAGE_LABELS = {
    STAGE_HIGH: "Wortbezug und Ereignisart",
    STAGE_MEDIUM: "Wortbezug oder Themenbezug",
    STAGE_LOW: "nur Ereignisart",
    STAGE_NONE: "kein Bezug",
}
SIGNAL_TERM = "Wortbezug"
SIGNAL_CATEGORY = "Ereignisart"
SIGNAL_SHIFT = "Themenverschiebung"
SIGNAL_NON_EMPLOYER = "ohne Arbeitgeberbezug"
SIGNAL_NAMES = (SIGNAL_TERM, SIGNAL_CATEGORY, SIGNAL_SHIFT, SIGNAL_NON_EMPLOYER)
SIGNAL_SEPARATOR = " · "
SIGNAL_NONE_LABEL = "kein Signal"

STAGE_FINDING_NOTE = ("In der Auswertung vom 08.10.2026 traten Einträge dieser Art in Zeiträumen ohne Markierung "
                      "ähnlich häufig auf wie bei Markierungen. Sie sind Kandidaten für die eigene Einordnung.")

BUNDLE_MAX_DAYS = 3
BUNDLE_TITLE_SIMILARITY = 0.5

MAX_EXPLANATIONS = 5
SOURCE_TYPE_ORDER = {TYPE_ADHOC: 0, TYPE_NEWS: 1}
STATE_OPEN, STATE_FOUND = "offen", "ansaetze"

EXPLANATION_NOTE = ("Die Einstufung beruht auf Titeln und Wortbezügen. Sie zeigt mögliche Zusammenhänge, "
                    "keine Ursachen.")
OPEN_NOTE = ("Keine Meldung im Ereignisfenster erfüllt die strengen Auswahlregeln (Unternehmen im Titel genannt, "
             "Arbeitgeberbezug, Wortbezug zu den Bewertungen oder Ereignisart mit Themenverschiebung, zeitliche Nähe "
             "mindestens 0,5). Interne Auslöser sind von außen nicht sichtbar; die Veränderung bleibt offen.")
OPEN_NOTE_LENIENT = ("Kein Beleg erreicht die Stufe niedrig: Keine Meldung im Ereignisfenster hat einen Wortbezug "
                     "zu den Bewertungen oder eine erkannte Ereignisart mit Arbeitgeberbezug. Interne Auslöser sind "
                     "von außen nicht sichtbar; die Veränderung bleibt offen.")

STRICT_SELECTION = True
SELECTION_VERSION = 1
SELECTION_DATE = "2026-10-18"
SELECTION_MIN_TIME = TIME_MID
COMPANY_TITLE_MAX_SUFFIX = 2
GENERIC_NAME_WORDS = frozenset({
    "medical", "software", "semiconductor", "digital", "technology", "technologie", "technologies", "europe", "europa",
    "data", "institut", "institute", "universität", "university", "uni", "technische", "group", "holding",
    "international", "systems", "solutions", "services", "service", "partners", "consulting", "deutschland", "germany",
    "network", "networks", "energy", "energie", "capital", "industries", "industrie",
})
EXCLUDED_COMPANY = "Unternehmen im Titel nicht genannt"
EXCLUDED_NON_EMPLOYER = "ohne Arbeitgeberbezug"
EXCLUDED_TOPIC = "kein Wortbezug und keine Themenverschiebung"
EXCLUDED_TIME = "zeitliche Nähe unter 0,5"
EXCLUSION_REASONS = (EXCLUDED_COMPANY, EXCLUDED_NON_EMPLOYER, EXCLUDED_TOPIC, EXCLUDED_TIME)
SELECTION_RULES = (
    "Der Titel nennt das Unternehmen: ein Wort des Namens oder des Suchbegriffs steht im Titel "
    "(allgemeine Wörter wie „Deutsche“ zählen nicht); EQS-Mitteilungen des Emittenten gelten als genannt.",
    "Die Meldung hat Arbeitgeberbezug: Börsenberichte, Kursziele, Sport- und Produktmeldungen sind ausgeschlossen, "
    "nicht nur zurückgestuft.",
    "Die Meldung hat thematische Korrespondenz: ein kennzeichnender Begriff der Bewertungen steht im Titel oder, wenn "
    "er vorliegt, im Text der Meldung (Wortbezug: der Begriff selbst oder ein Wort, das mit ihm beginnt) oder die "
    "erkannte Ereignisart hat ein zugeordnetes Thema, "
    "das sich im Vergleich merklich verschiebt (Themenverschiebung); eine nur erkannte Ereignisart genügt nicht.",
    "Die Meldung liegt nahe am Übergang: zeitliche Nähe mindestens 0,5, also nicht am Rand des Fensters davor.",
)
SELECTION_NOTE = ("Strenge Auswahl: Nur Meldungen, die alle vier Regeln erfüllen, werden zu Erklärungsansätzen; "
                  "die übrigen stehen in der Belegliste mit der Regel, die sie nicht erfüllen.")



def _texts_enabled() -> bool:
    from services.evidence_text import texts_enabled
    return texts_enabled()


def selection_rules() -> Dict[str, Any]:
    return {
        "strict": STRICT_SELECTION, "version": SELECTION_VERSION, "date": SELECTION_DATE,
        "require_company_in_title": True, "exclude_non_employer": True,
        "min_topic": f"term_match >= {TOPIC_WEAK} oder category_match >= {TOPIC_STRONG}",
        "term_match_compound_only": True,
        "min_time": SELECTION_MIN_TIME, "min_stage": STAGE_MEDIUM,
        "company_title_max_suffix": COMPANY_TITLE_MAX_SUFFIX,
        "rules": list(SELECTION_RULES), "reasons": list(EXCLUSION_REASONS), "note": SELECTION_NOTE,
    }


def rules() -> Dict[str, Any]:
    return {
        "term_match_per_term": TERM_MATCH_PER_TERM, "term_match_strong": TERM_MATCH_STRONG,
        "term_strong_min_after": TERM_STRONG_MIN_AFTER, "term_strong_min_ratio": TERM_STRONG_MIN_RATIO,
        "term_strong_min_shift": TERM_STRONG_MIN_SHIFT,
        "topic_shift_min_pp": TOPIC_SHIFT_MIN_PP, "category_match_with_shift": CATEGORY_MATCH_WITH_SHIFT,
        "category_match_only": CATEGORY_MATCH_ONLY, "time_near": TIME_NEAR, "time_after_factor": TIME_AFTER_FACTOR,
        "topic_strong": TOPIC_STRONG, "topic_weak": TOPIC_WEAK, "time_mid": TIME_MID, "time_min": TIME_MIN,
        "bundle_max_days": BUNDLE_MAX_DAYS, "bundle_title_similarity": BUNDLE_TITLE_SIMILARITY,
        "max_explanations": MAX_EXPLANATIONS,
        "version": RULES_VERSION, "version_date": RULES_VERSION_DATE,
        "corrections": list(CORRECTIONS),
        "text": {"version": TEXT_VERSION, "version_date": TEXT_VERSION_DATE, "used_for": "term_match", "enabled": _texts_enabled(),
                 "title_only": ["category_match", "employer_related", "company_in_title"],
                 "term_max_share": TEXT_TERM_MAX_SHARE, "term_min_hits": TEXT_TERM_MIN_HITS, "note": TEXT_NOTE},
        "stage_labels": dict(STAGE_LABELS),
        "finding_note": STAGE_FINDING_NOTE,
        "selection": selection_rules(),
        "stages": {
            STAGE_HIGH: f"term_match >= {TOPIC_WEAK} und Ereignisart erkannt (category_match >= {CATEGORY_MATCH_ONLY}) und time_match >= {TIME_NEAR}",
            STAGE_MEDIUM: f"term_match >= {TOPIC_WEAK} oder category_match >= {TOPIC_STRONG}, und time_match >= {TIME_MID}",
            STAGE_LOW: f"Ereignisart erkannt (category_match >= {CATEGORY_MATCH_ONLY}) oder term_match >= {TOPIC_WEAK}, und time_match >= {TIME_MIN}",
            STAGE_NONE: "sonst; Gruppe ohne Arbeitgeberbezug eine Stufe tiefer",
        },
    }


def signals_present(term: float, category: float, employer_related: Optional[bool] = None) -> List[str]:
    present = []
    if term >= TOPIC_WEAK:
        present.append(SIGNAL_TERM)
    if category >= CATEGORY_MATCH_ONLY:
        present.append(SIGNAL_CATEGORY)
    if category >= TOPIC_STRONG:
        present.append(SIGNAL_SHIFT)
    if employer_related is False:
        present.append(SIGNAL_NON_EMPLOYER)
    return present


def signal_label(term: float, category: float, employer_related: Optional[bool] = None) -> str:
    present = signals_present(term, category, employer_related)
    return SIGNAL_SEPARATOR.join(present) if present else SIGNAL_NONE_LABEL


def time_match(month: Optional[str], window: Dict[str, Any]) -> float:
    if not month:
        return 0.0
    try:
        m = month_index(str(month)[:7])
    except ValueError:
        return 0.0
    start, end = month_index(window["from"]), month_index(window["to"])
    if m < start or m > end:
        return 0.0
    near_from = month_index(window["transition_from"]) - 1
    anchor_to = month_index(window["anchor_to"])
    if near_from <= m <= anchor_to:
        return TIME_NEAR
    if m < near_from:
        before = int(window.get("window_before") or (near_from + 1 - start))
        return round(max(0.0, TIME_NEAR - (near_from - m) / before), 2) if before > 0 else 0.0
    after = int(window.get("window_after") or (end - anchor_to))
    if after <= 0:
        return 0.0
    return round(max(0.0, TIME_AFTER_FACTOR * (1 - (m - anchor_to - 1) / after)), 2)


def is_strong_term(term: Dict[str, Any]) -> bool:
    ratio = term.get("ratio")
    shift = float(term.get("after_share") or 0.0) - float(term.get("before_share") or 0.0)
    return (int(term.get("after") or 0) >= TERM_STRONG_MIN_AFTER and (ratio is None or float(ratio) >= TERM_STRONG_MIN_RATIO)
            and shift >= TERM_STRONG_MIN_SHIFT)


def term_match(matched_terms: List[Dict[str, Any]]) -> float:
    total = sum(TERM_MATCH_STRONG if is_strong_term(t) else TERM_MATCH_PER_TERM for t in matched_terms)
    return round(min(1.0, total), 2)


def topic_shift_index(topics: Optional[Iterable[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for t in topics or []:
        if isinstance(t, dict) and t.get("topic"):
            out[t["topic"]] = {"share_shift_pp": t.get("share_shift_pp"), "low_basis": bool(t.get("low_basis"))}
    return out


def category_match(primary: Optional[Dict[str, Any]], shifts: Dict[str, Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
    if not primary or not primary.get("employer_related"):
        return 0.0, []
    shifted = []
    for topic in primary.get("topics") or []:
        s = shifts.get(topic)
        if not s or s.get("low_basis") or s.get("share_shift_pp") is None:
            continue
        if abs(float(s["share_shift_pp"])) >= TOPIC_SHIFT_MIN_PP:
            shifted.append({"topic": topic, "share_shift_pp": float(s["share_shift_pp"])})
    shifted.sort(key=lambda s: (-abs(s["share_shift_pp"]), s["topic"]))
    return (CATEGORY_MATCH_WITH_SHIFT, shifted) if shifted else (CATEGORY_MATCH_ONLY, [])


def stage_for(term: float, category: float, time: float, employer_related: Optional[bool] = None) -> str:
    has_term = term >= TOPIC_WEAK
    has_category = category >= CATEGORY_MATCH_ONLY
    has_shift = category >= TOPIC_STRONG
    if has_term and has_category and time >= TIME_NEAR:
        stage = STAGE_HIGH
    elif (has_term or has_shift) and time >= TIME_MID:
        stage = STAGE_MEDIUM
    elif (has_category or has_term) and time >= TIME_MIN:
        stage = STAGE_LOW
    else:
        stage = STAGE_NONE
    if employer_related is False and stage != STAGE_NONE:
        stage = STAGES[_STAGE_RANK[stage] + 1]
    return stage


def company_title_words(company_words: Iterable[str], extra: Iterable[str] = ()) -> Set[str]:
    words = {str(w).lower().strip() for w in (company_words or ()) if w}
    words = {w for w in words if len(w) >= MIN_TERM_LENGTH and w not in STOPWORDS}
    specific = {w for w in words if w not in GENERIC_NAME_WORDS}
    out = specific or words
    for e in extra or ():
        lowered = str(e).lower()
        tokens = _TITLE_WORD_RE.findall(lowered) + _TITLE_WORD_RE.findall(_INNER_DOT_RE.sub("", lowered))
        out |= {t for t in tokens if len(t) >= MIN_TERM_LENGTH}
    return out


def company_in_title(title: Any, company_words: Iterable[str]) -> Optional[bool]:
    words = {str(w).lower() for w in (company_words or ()) if w}
    if not words or not title or not isinstance(title, str):
        return None
    lowered = title.lower()
    tokens = set(_TITLE_WORD_RE.findall(lowered)) | set(_TITLE_WORD_RE.findall(_INNER_DOT_RE.sub("", lowered)))
    for t in tokens:
        if t in words:
            return True
        if any(t.startswith(w) and len(t) - len(w) <= COMPANY_TITLE_MAX_SUFFIX for w in words):
            return True
    return False


def frequent_text_terms(items: Iterable[Dict[str, Any]], terms: List[Dict[str, Any]], strict_terms: bool = False,
                        max_share: float = TEXT_TERM_MAX_SHARE, min_hits: int = TEXT_TERM_MIN_HITS) -> Dict[str, Any]:
    texts = [i["text"] for i in items if isinstance(i.get("text"), str) and i.get("text")]
    counts: Dict[str, int] = {}
    for text in texts:
        for hit in match_terms(text, terms, compound_only=strict_terms):
            counts[hit["term"]] = counts.get(hit["term"], 0) + 1
    excluded = [{"term": term, "n_texts_with_term": n, "share": round(n / len(texts), 3)}
                for term, n in counts.items() if n >= min_hits and n / len(texts) > max_share]
    return {"n_texts": len(texts), "excluded": excluded}


def score_item(item: Dict[str, Any], window: Dict[str, Any], terms: List[Dict[str, Any]],
               shifts: Dict[str, Dict[str, Any]], categories: Optional[List[Dict[str, Any]]] = None,
               company_words: Iterable[str] = (), strict_terms: bool = False,
               text_excluded: Iterable[str] = ()) -> Dict[str, Any]:
    title = item.get("title") or ""
    text = item.get("text") if isinstance(item.get("text"), str) else ""
    matched = [{**t, "in": TERM_IN_TITLE} for t in match_terms(title, terms, compound_only=strict_terms)]
    if text:
        skip = {t["term"] for t in matched} | set(text_excluded)
        matched += [{**t, "in": TERM_IN_TEXT} for t in match_terms(text, terms, compound_only=strict_terms)
                    if t["term"] not in skip]
    classification = classify_title(title, categories, eqs_category=item.get("category"))
    primary = classification["primary"]
    cat_match, shifted = category_match(primary, shifts)
    t_match, tm = term_match(matched), time_match(item.get("date"), window)
    topic = max(t_match, cat_match)
    employer = primary["employer_related"] if primary else None
    stage = stage_for(t_match, cat_match, tm, employer)
    category = None
    if primary:
        category = {"id": primary["id"], "label": primary["label"], "employer_related": primary["employer_related"],
                    "keywords": primary["keywords"], "topics": primary["topics"], "match": cat_match,
                    "shifted_topics": shifted}
    return {
        "id": item.get("id"), "date": item.get("date"), "title": title, "publisher": item.get("publisher"),
        "url": item.get("url"), "source": item.get("source"), "source_type": item.get("source_type"),
        "reliability": item.get("reliability"), "language": item.get("language"), "issuer": item.get("issuer"),
        "eqs_category": item.get("category") if item.get("source_type") == TYPE_ADHOC else None,
        "time_match": tm, "term_match": t_match, "category_match": cat_match, "topic_match": topic,
        "terms": [{"term": t["term"], "word": t["word"], "before": t["before"], "after": t["after"],
                   "n_before": t["n_before"], "n_after": t["n_after"], "strong": is_strong_term(t), "in": t["in"]}
                  for t in matched],
        "category": category,
        "employer_related": employer,
        "company_in_title": company_in_title(title, company_words),
        "has_text": bool(text),
        "text_status": item.get("text_status") if text else None,
        "stage": stage,
        "stage_label": STAGE_LABELS[stage],
        "signal_label": signal_label(t_match, cat_match, employer),
    }


def exclusion_reason(scored: Dict[str, Any]) -> Optional[str]:
    if scored.get("source_type") != TYPE_ADHOC and scored.get("company_in_title") is False:
        return EXCLUDED_COMPANY
    if scored.get("employer_related") is False:
        return EXCLUDED_NON_EMPLOYER
    term, category = float(scored.get("term_match") or 0.0), float(scored.get("category_match") or 0.0)
    if not (term >= TOPIC_WEAK or category >= TOPIC_STRONG):
        return EXCLUDED_TOPIC
    if float(scored.get("time_match") or 0.0) < SELECTION_MIN_TIME:
        return EXCLUDED_TIME
    return None


def select_items(scored: List[Dict[str, Any]], strict: bool = STRICT_SELECTION) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    kept: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    for item in scored:
        reason = exclusion_reason(item) if strict else None
        item["selected"], item["excluded"] = reason is None, reason
        (kept if reason is None else dropped).append(item)
    return kept, dropped


def _excluded_sort_key(scored: Dict[str, Any]) -> Tuple:
    return (_STAGE_RANK[scored["stage"]], SOURCE_TYPE_ORDER.get(scored.get("source_type"), 9),
            -scored["topic_match"], -scored["time_match"], str(scored.get("date") or "9999"), str(scored.get("id")))


def title_similarity(a: str, b: str, exclude: Iterable[str] = ()) -> float:
    sa, sb = term_set(a, exclude), term_set(b, exclude)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _day(value: Optional[str]) -> Optional[_date]:
    try:
        return _date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def _days_apart(a: Optional[str], b: Optional[str]) -> Optional[int]:
    da, db = _day(a), _day(b)
    return abs((da - db).days) if da and db else None


def _category_key(scored: Dict[str, Any]) -> Optional[str]:
    return scored["category"]["id"] if scored.get("category") else None


def bundle_items(scored: List[Dict[str, Any]], exclude: Iterable[str] = ()) -> List[Dict[str, Any]]:
    ordered = sorted(scored, key=lambda s: (str(s.get("date") or "9999"), SOURCE_TYPE_ORDER.get(s.get("source_type"), 9), str(s.get("id"))))
    excluded = set(exclude)
    bundles: List[Dict[str, Any]] = []
    for s in ordered:
        home = None
        for b in bundles:
            first = b["items"][0]
            if _category_key(first) != _category_key(s):
                continue
            apart = _days_apart(first.get("date"), s.get("date"))
            if apart is None or apart > BUNDLE_MAX_DAYS:
                continue
            if title_similarity(first["title"], s["title"], excluded) >= BUNDLE_TITLE_SIMILARITY:
                home = b
                break
        if home is None:
            bundles.append({"items": [s]})
        else:
            home["items"].append(s)
    return [_finish_bundle(b["items"]) for b in bundles]


def _finish_bundle(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    representative = next((i for i in items if i.get("source_type") == TYPE_ADHOC), items[0])
    items = [representative] + [i for i in items if i is not representative]
    tm = max(i["time_match"] for i in items)
    t_match = max(i["term_match"] for i in items)
    cat_match = max(i["category_match"] for i in items)
    topic = max(t_match, cat_match)
    terms: Dict[str, Dict[str, Any]] = {}
    for i in items:
        for t in i["terms"]:
            terms.setdefault(t["term"], t)
    category = representative.get("category")
    if category is None:
        category = next((i["category"] for i in items if i.get("category")), None)
    employer = category["employer_related"] if category else None
    if category:
        category = {**category, "match": cat_match}
    publishers = list(dict.fromkeys(i.get("publisher") for i in items if i.get("publisher")))
    stage = stage_for(t_match, cat_match, tm, employer)
    return {
        "representative": representative,
        "items": items,
        "n_items": len(items),
        "publishers": publishers,
        "date": representative.get("date"),
        "time_match": tm, "term_match": t_match, "category_match": cat_match, "topic_match": topic,
        "terms": list(terms.values()),
        "category": category,
        "employer_related": employer,
        "stage": stage,
        "stage_label": STAGE_LABELS[stage],
        "signal_label": signal_label(t_match, cat_match, employer),
        "source_type": representative.get("source_type"),
        "eqs_category": representative.get("eqs_category"),
        "has_adhoc": any(i.get("source_type") == TYPE_ADHOC for i in items),
        "has_eqs_adhoc": any(is_eqs_adhoc(i) for i in items),
        "company_in_title": representative.get("company_in_title"),
        "has_text": any(i.get("has_text") for i in items),
    }


def sort_key(bundle: Dict[str, Any]) -> Tuple:
    return (
        _STAGE_RANK[bundle["stage"]],
        SOURCE_TYPE_ORDER.get(bundle.get("source_type"), 9),
        -bundle["topic_match"], -bundle["time_match"], -bundle["n_items"],
        str(bundle.get("date") or "9999"),
    )


_MONTHS_DE = ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sep.", "Okt.", "Nov.", "Dez."]


def fmt_month(period: str) -> str:
    return f"{_MONTHS_DE[int(period[5:7]) - 1]} {period[:4]}"


def time_phrase(month: Optional[str], window: Dict[str, Any], kind: Optional[str] = None) -> str:
    kind = kind or window.get("kind") or KIND_CHANGE
    if kind == KIND_SELECTION:
        anchor, before_word, inside = "der Auswahl", "vor der Auswahl", "in der Auswahl"
    elif kind == KIND_OUTLIER:
        anchor, before_word, inside = "dem auffälligen Monat", "vor dem auffälligen Monat", "im auffälligen Monat"
    else:
        anchor, before_word, inside = "dem markierten Monat", "vor dem Übergang", "im Übergang"
    if not month:
        return "ohne Datum im Fenster"
    m = month_index(str(month)[:7])
    near_from = month_index(window["transition_from"]) - 1
    anchor_from, anchor_to = month_index(window["anchor_from"]), month_index(window["anchor_to"])
    if m == near_from:
        return f"im Monat {before_word}"
    if m < near_from:
        d = near_from - m + 1
        return f"{d} Monate {before_word}"
    if m <= anchor_to:
        if kind in (KIND_SELECTION, KIND_OUTLIER):
            return inside
        if m >= anchor_from:
            return "im markierten Monat"
        return f"{inside} ({fmt_month(str(month)[:7])})"
    d = m - anchor_to
    return f"im Monat nach {anchor}" if d == 1 else f"{d} Monate nach {anchor}"


def is_eqs_adhoc(item: Dict[str, Any]) -> bool:
    return item.get("source_type") == TYPE_ADHOC and str(item.get("eqs_category") or "").strip().lower() == "ad-hoc"


def _eqs_phrase(bundle: Dict[str, Any]) -> str:
    return "Ad-hoc-Mitteilung" if is_eqs_adhoc(bundle) else "EQS-Mitteilung"


def _count_phrase(bundle: Dict[str, Any]) -> str:
    n, adhoc = bundle["n_items"], bundle.get("has_adhoc")
    if n == 1:
        return f"eine {_eqs_phrase(bundle)}" if bundle.get("source_type") == TYPE_ADHOC else "eine Meldung"
    if not adhoc:
        return f"{n} Meldungen"
    return f"{n} Meldungen (darunter eine {'Ad-hoc-Mitteilung' if bundle.get('has_eqs_adhoc') else 'EQS-Mitteilung'})"


def _term_name(t: Dict[str, Any]) -> str:
    return f"'{t['term']}'" + (" (im Text der Meldung)" if t.get("in") == TERM_IN_TEXT else "")


def _term_phrase(terms: List[Dict[str, Any]], kind: str) -> str:
    if not terms:
        return ""
    where = "in den Bewertungen der Auswahl" if kind == KIND_SELECTION else "in den Bewertungen danach"
    if len(terms) == 1:
        t = terms[0]
        if t.get("in") == TERM_IN_TEXT:
            return (f"; '{t['term']}' steht im Text der Meldung und wird {where} häufiger genannt "
                    f"({t['after']} gegenüber {t['before']} Bewertungen)")
        return f"; {where} wird '{t['term']}' häufiger genannt ({t['after']} gegenüber {t['before']} Bewertungen)"
    counts = ", ".join(f"{t['term']}: {t['after']} gegenüber {t['before']}" for t in terms)
    if all(t.get("in") == TERM_IN_TEXT for t in terms):
        plain = ", ".join(f"'{t['term']}'" for t in terms[:-1]) + f" und '{terms[-1]['term']}'"
        return f"; {plain} stehen im Text der Meldung und werden {where} häufiger genannt ({counts} Bewertungen)"
    names = ", ".join(_term_name(t) for t in terms[:-1]) + f" und {_term_name(terms[-1])}"
    return f"; {where} werden {names} häufiger genannt ({counts} Bewertungen)"


def _category_phrase(category: Optional[Dict[str, Any]]) -> str:
    if not category or not category.get("employer_related"):
        return ""
    shifted = category.get("shifted_topics") or []
    if shifted:
        parts = ", ".join(f"{s['topic']} um {s['share_shift_pp']:+.1f}".replace(".", ",") for s in shifted)
        word = "verschiebt sich das zugeordnete Thema" if len(shifted) == 1 else "verschieben sich die zugeordneten Themen"
        return f"; im Vergleich {word} {parts} Prozentpunkte"
    return "; die Ereignisart ist aus dem Titel erkannt, ein zugeordnetes Thema verschiebt sich nicht merklich"


def explanation_text(bundle: Dict[str, Any], window: Dict[str, Any], kind: Optional[str] = None) -> str:
    kind = kind or window.get("kind") or KIND_CHANGE
    category = bundle.get("category")
    when = time_phrase(bundle.get("date"), window, kind)
    head = f"Möglicher Zusammenhang: {_count_phrase(bundle)}"
    if category and category.get("employer_related"):
        head += f" zu {category['label']}"
    elif category:
        head += " ohne erkennbaren Arbeitgeberbezug (Börsenbericht, Kursziel, Sport oder Produkt)"
    text = head + f" {when}" + _term_phrase(bundle.get("terms") or [], kind) + _category_phrase(category)
    if category and not category.get("employer_related"):
        text += "; eine Stufe zurückgestuft"
    if not bundle.get("terms") and not (category and category.get("employer_related")):
        text += "; kein Wortbezug zu den Bewertungen"
    return text + "."


def title_sentiment(title: str, analyzer, direction: Optional[str], cache: Optional[Dict[str, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    if analyzer is None or not title:
        return None
    if cache is not None and title in cache:
        raw = cache[title]
    else:
        try:
            result = analyzer.analyze_sentiment(title, None)
            raw = {"label": result.get("sentiment", "neutral"), "polarity": round(float(result.get("polarity", 0.0)), 3)}
        except Exception:  # noqa: BLE001
            return None
        if cache is not None:
            cache[title] = raw
    fits = None
    if direction in ("fall", "rise") and raw["label"] in ("positive", "negative"):
        fits = (direction == "fall") == (raw["label"] == "negative")
    return {**raw, "fits_direction": fits}


GROUP_BY_CATEGORY, GROUP_BY_TERM = "ereignisart", "begriff"


def group_key(bundle: Dict[str, Any]) -> Tuple[str, str, str]:
    category = bundle.get("category")
    if category:
        return (GROUP_BY_CATEGORY, str(category["id"]), str(category["label"]))
    terms = sorted({t["term"] for t in bundle.get("terms") or []})
    label = "Begriff " + ", ".join(f"'{t}'" for t in terms) if terms else "ohne Ereignisart und Begriff"
    return (GROUP_BY_TERM, "+".join(terms), label)


def group_bundles(bundles: List[Dict[str, Any]]) -> List[Tuple[Tuple[str, str, str], List[Dict[str, Any]]]]:
    groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
    for b in bundles:
        groups.setdefault(group_key(b), []).append(b)
    return list(groups.items())


def _group_member(bundle: Dict[str, Any], window: Dict[str, Any], kind: str) -> Dict[str, Any]:
    rep = bundle["representative"]
    return {
        "id": rep.get("id"), "confidence": bundle["stage"], "stage_label": bundle["stage_label"],
        "signal_label": bundle["signal_label"], "event": rep.get("title"), "date": rep.get("date"), "source": rep.get("publisher"), "url": rep.get("url"),
        "has_text": bool(bundle.get("has_text")),
        "source_type": rep.get("source_type"), "eqs_category": rep.get("eqs_category"),
        "language": rep.get("language"), "issuer": rep.get("issuer"),
        "n_items": bundle["n_items"], "publishers": bundle["publishers"],
        "time_match": bundle["time_match"], "topic_match": bundle["topic_match"], "term_match": bundle["term_match"],
        "terms": [t["term"] for t in bundle["terms"]], "time_phrase": time_phrase(rep.get("date"), window, kind),
        "company_in_title": bundle.get("company_in_title"), "text": explanation_text(bundle, window, kind),
    }


def _group_info(key: Tuple[str, str, str], members: List[Dict[str, Any]], window: Dict[str, Any], kind: str) -> Dict[str, Any]:
    publishers = list(dict.fromkeys(p for m in members for p in m["publishers"]))
    return {
        "kind": key[0], "key": key[1], "label": key[2],
        "n_bundles": len(members), "n_items": sum(m["n_items"] for m in members), "publishers": publishers,
        "others": [_group_member(m, window, kind) for m in members[1:]],
    }


def _entry(bundle: Dict[str, Any], window: Dict[str, Any], kind: str, analyzer, direction: Optional[str],
           cache: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    rep = bundle["representative"]
    item_fields = ("id", "date", "title", "publisher", "url", "source", "source_type", "eqs_category", "reliability",
                   "language", "issuer", "time_match", "term_match", "category_match", "topic_match", "stage", "stage_label", "signal_label",
                   "company_in_title", "has_text", "terms")
    return {
        "id": rep.get("id"),
        "confidence": bundle["stage"],
        "stage_label": bundle["stage_label"],
        "signal_label": bundle["signal_label"],
        "event": rep.get("title"),
        "date": rep.get("date"),
        "source": rep.get("publisher"),
        "url": rep.get("url"),
        "source_type": rep.get("source_type"),
        "eqs_category": rep.get("eqs_category"),
        "reliability": rep.get("reliability"),
        "language": rep.get("language"),
        "issuer": rep.get("issuer"),
        "n_items": bundle["n_items"],
        "publishers": bundle["publishers"],
        "time_match": bundle["time_match"],
        "topic_match": bundle["topic_match"],
        "term_match": bundle["term_match"],
        "terms": bundle["terms"],
        "category": bundle["category"],
        "time_phrase": time_phrase(rep.get("date"), window, kind),
        "company_in_title": bundle.get("company_in_title"),
        "has_text": bool(bundle.get("has_text")),
        "sentiment": title_sentiment(rep.get("title") or "", analyzer, direction, cache),
        "text": explanation_text(bundle, window, kind),
        "items": [{k: i.get(k) for k in item_fields} for i in bundle["items"]],
    }


def _item_score(i: Dict[str, Any], rank: int, bundle: Optional[Dict[str, Any]], b_index: Optional[int]) -> Dict[str, Any]:
    return {
        "rank": rank,
        "stage": bundle["stage"] if bundle else i["stage"],
        "stage_label": bundle["stage_label"] if bundle else i["stage_label"],
        "signal_label": bundle["signal_label"] if bundle else i["signal_label"],
        "item_signal_label": i["signal_label"], "bundle": b_index, "bundle_size": bundle["n_items"] if bundle else 1,
        "time_match": i["time_match"], "term_match": i["term_match"], "category_match": i["category_match"],
        "topic_match": i["topic_match"], "item_stage": i["stage"],
        "category": i["category"]["id"] if i.get("category") else None,
        "category_label": i["category"]["label"] if i.get("category") else None,
        "employer_related": i.get("employer_related"),
        "company_in_title": i.get("company_in_title"),
        "terms": [t["term"] for t in i["terms"]],
        "terms_in_text": [t["term"] for t in i["terms"] if t.get("in") == TERM_IN_TEXT],
        "has_text": bool(i.get("has_text")),
        "selected": bool(i.get("selected", True)),
        "excluded": i.get("excluded"),
    }


def rank_evidence(
    items: List[Dict[str, Any]],
    window: Dict[str, Any],
    *,
    terms: List[Dict[str, Any]],
    topics: Optional[Iterable[Dict[str, Any]]] = None,
    direction: Optional[str] = None,
    exclude: Iterable[str] = (),
    categories: Optional[List[Dict[str, Any]]] = None,
    analyzer=None,
    kind: Optional[str] = None,
    max_explanations: int = MAX_EXPLANATIONS,
    group_by_category: bool = True,
    strict: bool = STRICT_SELECTION,
    title_words: Iterable[str] = (),
) -> Dict[str, Any]:
    cats = load_event_categories() if categories is None else categories
    kind = kind or window.get("kind") or KIND_CHANGE
    shifts = topic_shift_index(topics)
    name_words = company_title_words(exclude, title_words)
    evidence_items = [i for i in items if i.get("source_type") != TYPE_GLOBAL]
    text_terms = frequent_text_terms(evidence_items, terms, strict_terms=bool(strict))
    text_excluded = {e["term"] for e in text_terms["excluded"]}
    scored = [score_item(i, window, terms, shifts, cats, name_words, strict_terms=bool(strict), text_excluded=text_excluded)
              for i in evidence_items]
    global_events = global_events_in_window([i for i in items if i.get("source_type") == TYPE_GLOBAL], window)
    selected, excluded = select_items(scored, strict)
    bundles = sorted(bundle_items(selected, exclude), key=sort_key)
    n_by_stage = {s: 0 for s in STAGES}
    for b in bundles:
        n_by_stage[b["stage"]] += 1
    cache: Dict[str, Dict[str, Any]] = {}
    eligible = [b for b in bundles if b["stage"] != STAGE_NONE]
    groups = group_bundles(eligible)
    if group_by_category:
        explanations = []
        for key, members in groups[:max_explanations]:
            e = _entry(members[0], window, kind, analyzer, direction, cache)
            e["group"] = _group_info(key, members, window, kind)
            explanations.append(e)
    else:
        explanations = [_entry(b, window, kind, analyzer, direction, cache) for b in eligible[:max_explanations]]
        for e in explanations:
            e["group"] = None
    for rank, e in enumerate(explanations, start=1):
        e["rank"] = rank
    item_scores: Dict[str, Dict[str, Any]] = {}
    rank = 0
    for b_index, b in enumerate(bundles):
        for i in b["items"]:
            rank += 1
            item_scores[str(i.get("id"))] = _item_score(i, rank, b, b_index)
    for i in sorted(excluded, key=_excluded_sort_key):
        rank += 1
        item_scores[str(i.get("id"))] = _item_score(i, rank, None, None)
    n_by_signal_label: Dict[str, int] = {}
    for b in eligible:
        n_by_signal_label[b["signal_label"]] = n_by_signal_label.get(b["signal_label"], 0) + 1
    n_excluded_by_reason = {reason: 0 for reason in EXCLUSION_REASONS}
    for i in excluded:
        n_excluded_by_reason[i["excluded"]] = n_excluded_by_reason.get(i["excluded"], 0) + 1
    state = STATE_FOUND if explanations else STATE_OPEN
    return {
        "texts": {"n_texts": text_terms["n_texts"], "excluded_terms": text_terms["excluded"],
                  "n_with_text": sum(1 for sc in scored if sc.get("has_text"))},
        "state": state,
        "explanations": explanations,
        "n_items": len(scored),
        "n_selected": len(selected),
        "n_excluded": len(excluded),
        "n_excluded_by_reason": n_excluded_by_reason,
        "n_bundles": len(bundles),
        "n_groups": len(groups),
        "n_by_stage": n_by_stage,
        "n_by_signal_label": n_by_signal_label,
        "item_scores": item_scores,
        "terms": terms,
        "note": EXPLANATION_NOTE,
        "open_note": (OPEN_NOTE if strict else OPEN_NOTE_LENIENT) if state == STATE_OPEN else None,
        "rules": rules(),
        "selection": {**selection_rules(), "strict": bool(strict)},
        "global_events": global_events,
    }


GLOBAL_EVENT_NOTE = (
    "Allgemeine Ereignisse sind Zeiträume, in denen sich die gesamtwirtschaftliche Lage in Deutschland "
    "schnell verschlechtert hat (Eurostat: Wirtschaftsstimmung, Inflationsrate). Sie sind eine Hypothese: "
    "Sie zählen nicht als Beleg und gehen nicht in die Rangfolge ein."
)


def global_events_in_window(items: List[Dict[str, Any]], window: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for item in items:
        e = item.get("event") or {}
        date_from = str(e.get("from") or (item.get("date") or "")[:7])
        date_to = str(e.get("to") or date_from)
        if not date_from:
            continue
        try:
            months = _month_index(date_to) - _month_index(date_from) + 1
        except ValueError:
            months = None
        out.append({
            "id": str(e.get("id") or item.get("id")),
            "item_id": item.get("id"),
            "title": item.get("title"),
            "from": date_from,
            "to": date_to,
            "months": months,
            "scope": e.get("scope"),
            "note": e.get("note"),
            "url": item.get("url"),
            "time_phrase": time_phrase(date_from, window, window.get("kind")),
        })
    return sorted(out, key=lambda g: (g["from"], g["to"], g["id"]))


def _month_index(period: str) -> int:
    year, month = str(period)[:7].split("-")
    return int(year) * 12 + int(month) - 1


def topic_shift_table(before_rows: List[Dict[str, Any]], after_rows: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
    from services.explanation_service import LOW_BASIS_MIN_MENTIONS, LOW_BASIS_MIN_REVIEWS

    topics = list(topic_definitions_for(source).keys())
    counts = {"before": {t: 0 for t in topics}, "after": {t: 0 for t in topics}}
    sizes = {"before": len(before_rows), "after": len(after_rows)}
    for side, rows in (("before", before_rows), ("after", after_rows)):
        for row in rows:
            for t in topics_in_review(row, source, EXPLANATION_TOPIC_TEXT_FIELDS):
                if t in counts[side]:
                    counts[side][t] += 1
    small = any(n < LOW_BASIS_MIN_REVIEWS for n in sizes.values())
    out = []
    for t in topics:
        b, a = counts["before"][t], counts["after"][t]
        b_share = round(b / sizes["before"], 4) if sizes["before"] else None
        a_share = round(a / sizes["after"], 4) if sizes["after"] else None
        shift = None if b_share is None or a_share is None else round((a_share - b_share) * 100, 2)
        out.append({"topic": t, "before": {"mentions": b, "share": b_share}, "after": {"mentions": a, "share": a_share},
                    "share_shift_pp": shift, "low_basis": small or (a + b < LOW_BASIS_MIN_MENTIONS)})
    out.sort(key=lambda e: (-abs(e["share_shift_pp"] or 0.0), e["topic"]))
    return out


__all__ = [
    "TERM_MATCH_PER_TERM", "TERM_MATCH_STRONG", "TERM_STRONG_MIN_AFTER", "TERM_STRONG_MIN_RATIO", "TERM_STRONG_MIN_SHIFT",
    "TOPIC_SHIFT_MIN_PP",
    "CATEGORY_MATCH_WITH_SHIFT", "CATEGORY_MATCH_ONLY", "TIME_NEAR", "TIME_AFTER_FACTOR", "TOPIC_STRONG", "TOPIC_WEAK",
    "TIME_MID", "TIME_MIN", "RULES_VERSION", "RULES_VERSION_DATE",
    "TEXT_VERSION", "TEXT_VERSION_DATE", "TERM_IN_TITLE", "TERM_IN_TEXT", "TEXT_TERM_MAX_SHARE", "TEXT_TERM_MIN_HITS",
    "TEXT_NOTE", "frequent_text_terms",
    "STRICT_SELECTION", "SELECTION_VERSION", "SELECTION_DATE", "SELECTION_MIN_TIME", "COMPANY_TITLE_MAX_SUFFIX",
    "GENERIC_NAME_WORDS", "EXCLUDED_COMPANY", "EXCLUDED_NON_EMPLOYER", "EXCLUDED_TOPIC", "EXCLUDED_TIME", "EXCLUSION_REASONS",
    "SELECTION_RULES", "SELECTION_NOTE", "OPEN_NOTE_LENIENT", "selection_rules", "company_title_words", "exclusion_reason",
    "select_items", "STAGE_HIGH", "STAGE_MEDIUM", "STAGE_LOW", "STAGE_NONE", "STAGES", "STAGE_LABELS", "STAGE_FINDING_NOTE", "BUNDLE_MAX_DAYS",
    "BUNDLE_TITLE_SIMILARITY", "MAX_EXPLANATIONS", "SOURCE_TYPE_ORDER", "STATE_OPEN", "STATE_FOUND", "EXPLANATION_NOTE",
    "OPEN_NOTE", "GLOBAL_EVENT_NOTE", "global_events_in_window", "SIGNAL_NAMES", "SIGNAL_NONE_LABEL", "signals_present", "signal_label", "rules", "time_match", "is_strong_term", "term_match", "topic_shift_index", "category_match", "stage_for",
    "company_in_title", "score_item", "title_similarity", "bundle_items", "sort_key", "group_key", "group_bundles", "fmt_month", "time_phrase", "explanation_text",
    "title_sentiment", "rank_evidence", "topic_shift_table",
]
