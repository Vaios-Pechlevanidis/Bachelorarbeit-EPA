from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from services.event_categories import classify_title
from services.evidence_sources import TYPE_ADHOC, TYPE_GLOBAL, TYPE_NEWS
from services.evidence_text import attach_texts
from services.keyword_topic_service import (
    EXPLANATION_TOPIC_TEXT_FIELDS,
    topic_definitions_for,
    topic_for_dimension,
    topic_spans,
    topics_in_review,
)
from services.rating_series_service import OVERALL_DIMENSION, value_column
from services.review_service import CATEGORY_TEXT_FIELDS, clean_html_text, has_text_content
from services.review_terms import match_terms

SCOPE_VERSION = 1
SCOPE_DATE = "2026-10-23"

REVIEW_SCOPE_NOTE = (
    "Zur Dimension gehört eine Bewertung, wenn sie einen Kommentar zu dieser Kategorie hat "
    "oder ein Schlüsselwort ihres Themas nennt; die Sterne allein genügen nicht."
)
EVIDENCE_SCOPE_NOTE = (
    "Zur Dimension gehört eine Meldung, wenn ihr Titel ein Schlüsselwort des Themas nennt "
    "oder ihre Ereignisart dem Thema zugeordnet ist. Allgemeine Ereignisse entfallen."
)
NO_EVIDENCE_IN_DIMENSION = "Kein Beleg im Fenster gehört zur gewählten Dimension."

_PLAIN_KEYWORD_RE = re.compile(r"^\\b([a-zäöüß]+)\\b$")


def single_dimension_topic(source: str, dimension: Optional[str]) -> Optional[str]:
    if dimension is None:
        raise ValueError("dimension_only braucht dimension.")
    if dimension == OVERALL_DIMENSION:
        raise ValueError("dimension_only braucht eine Einzeldimension, nicht die Gesamtbewertung.")
    return topic_for_dimension(source, dimension)


def dimension_comment(row: Dict[str, Any], source: str, dimension: str) -> Optional[str]:
    if source != "employee" or dimension not in CATEGORY_TEXT_FIELDS:
        return None
    raw = row.get(dimension)
    if not has_text_content(raw):
        return None
    text = clean_html_text(raw)
    return text.strip() if has_text_content(text) else None


def review_dimension_info(
    row: Dict[str, Any], source: str, dimension: str, topic: Optional[str] = None, topics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    column = value_column(source, dimension)
    if topic is None:
        topic = topic_for_dimension(source, dimension)
    if topics is None:
        topics = topics_in_review(row, source, EXPLANATION_TOPIC_TEXT_FIELDS)
    comment = dimension_comment(row, source, dimension)
    mentions = topic is not None and topic in topics
    return {
        "key": dimension,
        "rating": row.get(column),
        "comment": comment,
        "mentions_topic": mentions,
        "in_dimension": comment is not None or mentions,
    }


def mean_rating(infos: List[Dict[str, Any]]) -> Optional[float]:
    values = []
    for info in infos:
        try:
            values.append(float(info["rating"]))
        except (TypeError, ValueError):
            continue
    return round(sum(values) / len(values), 2) if values else None


def topic_title_terms(topic: str, source: Optional[str]) -> List[str]:
    definition = topic_definitions_for(source).get(topic) or {}
    terms: List[str] = []
    for pattern in definition.get("keywords", []):
        match = _PLAIN_KEYWORD_RE.match(pattern)
        if match and match.group(1) not in terms:
            terms.append(match.group(1))
    return terms


def evidence_dimension_match(
    item: Dict[str, Any], topic: Optional[str], source: Optional[str], categories: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    title = item.get("title")
    if not topic or not title or not isinstance(title, str) or item.get("source_type") == TYPE_GLOBAL:
        return None
    terms = [{"term": t} for t in topic_title_terms(topic, source)]

    def hits(text: str) -> List[str]:
        found: List[str] = []
        for start, end in topic_spans(text, topic, source):
            word = text[start:end].lower()
            if word not in found:
                found.append(word)
        for hit in match_terms(text, terms, compound_only=True):
            if hit["word"] not in found:
                found.append(hit["word"])
        return found

    words = hits(title)
    text = item.get("text") if isinstance(item.get("text"), str) else ""
    words_in_text = [w for w in hits(text) if w not in words] if text else []
    primary = classify_title(title, categories, eqs_category=item.get("category"))["primary"]
    category = primary["label"] if primary and primary["employer_related"] and topic in primary["topics"] else None
    if not words and not words_in_text and category is None:
        return None
    return {"terms": words, "terms_in_text": words_in_text, "category": category, "has_text": bool(text)}


def scope_evidence(evidence: Dict[str, Any], source: str, dimension: Optional[str],
                   company_id: Optional[int] = None) -> Dict[str, Any]:
    topic = single_dimension_topic(source, dimension)
    items = evidence.get("items") or []
    with_text = attach_texts(company_id, items)[0] if company_id is not None else items
    kept: List[Dict[str, Any]] = []
    for item, probe in zip(items, with_text):
        match = evidence_dimension_match(probe, topic, source)
        if match is not None:
            kept.append({**item, "dimension_match": match})
    counts = {TYPE_NEWS: 0, TYPE_ADHOC: 0, TYPE_GLOBAL: 0}
    for item in kept:
        counts[item["source_type"]] = counts.get(item["source_type"], 0) + 1
    reason = evidence.get("reason")
    if items and not kept:
        reason = NO_EVIDENCE_IN_DIMENSION
    return {
        **evidence,
        "items": kept,
        "total": len(kept),
        "counts": counts,
        "coverage": counts[TYPE_NEWS] + counts[TYPE_ADHOC] > 0,
        "reason": reason,
        "scope": {
            "dimension": dimension,
            "topic": topic,
            "n_all": len(items),
            "n_dimension": len(kept),
            "note": EVIDENCE_SCOPE_NOTE,
        },
    }


__all__ = [
    "SCOPE_VERSION", "SCOPE_DATE", "REVIEW_SCOPE_NOTE", "EVIDENCE_SCOPE_NOTE", "NO_EVIDENCE_IN_DIMENSION",
    "single_dimension_topic", "dimension_comment", "review_dimension_info", "mean_rating",
    "topic_title_terms", "evidence_dimension_match", "scope_evidence",
]
