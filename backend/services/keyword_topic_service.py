from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from services.review_service import CATEGORY_TEXT_FIELDS, build_full_review, clean_html_text

TOPIC_TEXT_FIELDS: List[str] = [
    'stellenbeschreibung', 'verbesserungsvorschlaege',
    'jobbeschreibung', 'gut_am_arbeitgeber_finde_ich',
    'schlecht_am_arbeitgeber_finde_ich', 'titel'
]

EXPLANATION_TOPIC_TEXT_FIELDS: List[str] = TOPIC_TEXT_FIELDS + CATEGORY_TEXT_FIELDS

QUOTE_EXCLUDED_FIELDS: tuple = ('jobbeschreibung', 'stellenbeschreibung')


EMPLOYEE_TOPIC_DEFINITIONS: Dict[str, Dict[str, List[str]]] = {
    "Work-Life Balance": {
        "keywords": [
            r'\bwork[\s-]*life[\s-]*balance\b',
            r'\büberstunden\b',
            r'\barbeitszeit\b',
            r'\burlaub\b',
            r'\bfreizeit\b',
            r'\bprivatleben\b',
            r'\bflexibilität\b',
            r'\bhomeoffice\b',
            r'\berreichbarkeit\b'
        ],
        "rating_fields": ["sternebewertung_work_life_balance"]
    },
    "Vorgesetztenverhalten": {
        "keywords": [
            r'\bführung\b',
            r'\bmanagement\b',
            r'\bvorgesetzte\b',
            r'\bchef\b',
            r'\bleitung\b',
            r'\bführungskräfte\b',
            r'\bvorgesetztenverhalten\b',
            r'\bkompetenz\b',
            r'\bentscheidung\b'
        ],
        "rating_fields": ["sternebewertung_vorgesetztenverhalten"]
    },
    "Gehalt & Sozialleistungen": {
        "keywords": [
            r'\bgehalt\b',
            r'\bbezahlung\b',
            r'\blohn\b',
            r'\bvergütung\b',
            r'\bbenefits\b',
            r'\bsozialleistungen\b',
            r'\baltersvorsorge\b',
            r'\bprämie\b',
            r'\bbonus\b'
        ],
        "rating_fields": ["sternebewertung_gehalt_sozialleistungen"]
    },
    "Kollegenzusammenhalt": {
        "keywords": [
            r'\bteam\b',
            r'\bkollegen\b',
            r'\bzusammenhalt\b',
            r'\bkollegenzusammenhalt\b',
            r'\bzusammenarbeit\b',
            r'\bgemeinschaft\b'
        ],
        "rating_fields": ["sternebewertung_kollegenzusammenhalt"]
    },
    "Karriere & Weiterbildung": {
        "keywords": [
            r'\bkarriere\b',
            r'\bweiterbildung\b',
            r'\bentwicklung\b',
            r'\baufstieg\b',
            r'\bförderung\b',
            r'\bschulungen\b',
            r'\bbeförderung\b',
            r'\bperspektive\b'
        ],
        "rating_fields": ["sternebewertung_karriere_weiterbildung"]
    },
    "Kommunikation": {
        "keywords": [
            r'\bkommunikation\b',
            r'\binformation\b',
            r'\btransparenz\b',
            r'\bfeedback\b',
            r'\bgespräch\b',
            r'\baustausch\b',
            r'\brückmeldung\b'
        ],
        "rating_fields": ["sternebewertung_kommunikation"]
    },
    "Arbeitsbedingungen": {
        "keywords": [
            r'\barbeitsbedingungen\b',
            r'\bausstattung\b',
            r'\bbüro\b',
            r'\barbeitsplatz\b',
            r'\btechnik\b',
            r'\bumgebung\b',
            r'\binfrastruktur\b'
        ],
        "rating_fields": ["sternebewertung_arbeitsbedingungen"]
    },
    "Arbeitsatmosphäre": {
        "keywords": [
            r'\batmosphäre\b',
            r'\barbeitsatmosphäre\b',
            r'\barbeitsklima\b',
            r'\bstimmung\b',
            r'\bklima\b'
        ],
        "rating_fields": ["sternebewertung_arbeitsatmosphaere"]
    },
    "Image": {
        "keywords": [
            r'\bimage\b',
            r'\bruf\b',
            r'\breputation\b',
            r'\bansehen\b',
            r'\bbekanntheitsgrad\b'
        ],
        "rating_fields": ["sternebewertung_image"]
    },
    "Interessante Aufgaben": {
        "keywords": [
            r'\baufgaben\b',
            r'\btätigkeit\b',
            r'\binteressant\b',
            r'\bherausforderung\b',
            r'\babwechslung\b',
            r'\bvielfalt\b'
        ],
        "rating_fields": ["sternebewertung_interessante_aufgaben"]
    },
    "Umwelt- & Sozialbewusstsein": {
        "keywords": [
            r'\bumwelt\b',
            r'\bnachhaltigkeit\b',
            r'\bsozialbewusstsein\b',
            r'\bverantwortung\b',
            r'\böko\b',
            r'\bklima\b'
        ],
        "rating_fields": ["sternebewertung_umwelt_sozialbewusstsein"]
    },
    "Umgang mit älteren Kollegen": {
        "keywords": [
            r'\bältere kollegen\b',
            r'\balter\b',
            r'\bsenior\b',
            r'\berfahrung\b',
            r'\bumgang\b'
        ],
        "rating_fields": ["sternebewertung_umgang_mit_aelteren_kollegen"]
    },
    "Gleichberechtigung": {
        "keywords": [
            r'\bgleichberechtigung\b',
            r'\bdiversität\b',
            r'\bvielfalt\b',
            r'\bdiskriminierung\b',
            r'\bchancengleichheit\b',
            r'\binklusion\b'
        ],
        "rating_fields": ["sternebewertung_gleichberechtigung"]
    }
}


CANDIDATE_TOPIC_DEFINITIONS: Dict[str, Dict[str, List[str]]] = {
    "Erklärung der weiteren Schritte": {
        "keywords": [
            r'\bschritte\b',
            r'\bweitere schritte\b',
            r'\bprozess\b',
            r'\berklärung\b',
            r'\binformation\b',
            r'\bablauf\b'
        ],
        "rating_fields": ["sternebewertung_erklaerung_der_weiteren_schritte"]
    },
    "Zufriedenstellende Reaktion": {
        "keywords": [
            r'\breaktion\b',
            r'\brückmeldung\b',
            r'\bantwort\b',
            r'\bresponse\b',
            r'\bzufriedenstellend\b'
        ],
        "rating_fields": ["sternebewertung_zufriedenstellende_reaktion"]
    },
    "Vollständigkeit der Infos": {
        "keywords": [
            r'\binformation\b',
            r'\binfos\b',
            r'\bvollständig\b',
            r'\bdetail\b',
            r'\bausführlich\b'
        ],
        "rating_fields": ["sternebewertung_vollstaendigkeit_der_infos"]
    },
    "Zufriedenstellende Antworten": {
        "keywords": [
            r'\bantwort\b',
            r'\bfrage\b',
            r'\bzufriedenstellend\b',
            r'\bauskunft\b'
        ],
        "rating_fields": ["sternebewertung_zufriedenstellende_antworten"]
    },
    "Angenehme Atmosphäre": {
        "keywords": [
            r'\batmosphäre\b',
            r'\bangenehm\b',
            r'\bstimmung\b',
            r'\bklima\b',
            r'\bwohlbefinden\b'
        ],
        "rating_fields": ["sternebewertung_angenehme_atmosphaere"]
    },
    "Professionalität des Gesprächs": {
        "keywords": [
            r'\bprofessionalität\b',
            r'\bgespräch\b',
            r'\binterview\b',
            r'\bprofessionell\b',
            r'\bkompetent\b'
        ],
        "rating_fields": ["sternebewertung_professionalitaet_des_gespraechs"]
    },
    "Wertschätzende Behandlung": {
        "keywords": [
            r'\bwertschätzung\b',
            r'\bbehandlung\b',
            r'\brespekt\b',
            r'\bwertschätzend\b',
            r'\bhöflich\b'
        ],
        "rating_fields": ["sternebewertung_wertschaetzende_behandlung"]
    },
    "Erwartbarkeit des Prozesses": {
        "keywords": [
            r'\berwartbarkeit\b',
            r'\bprozess\b',
            r'\bvorhersehbar\b',
            r'\bstruktur\b',
            r'\borganisation\b'
        ],
        "rating_fields": ["sternebewertung_erwartbarkeit_des_prozesses"]
    },
    "Zeitgerechte Zu- oder Absage": {
        "keywords": [
            r'\bzusage\b',
            r'\babsage\b',
            r'\bzeitgerecht\b',
            r'\bpünktlich\b',
            r'\bfrist\b',
            r'\btermin\b'
        ],
        "rating_fields": ["sternebewertung_zeitgerechte_zu_oder_absage"]
    },
    "Schnelle Antwort": {
        "keywords": [
            r'\bschnell\b',
            r'\bantwort\b',
            r'\breaktionszeit\b',
            r'\bzügig\b',
            r'\bprompt\b'
        ],
        "rating_fields": ["sternebewertung_schnelle_antwort"]
    }
}


NEUTRAL_FROM = 2.5
POSITIVE_FROM = 3.5
CLASSIFICATION_BASIS = "Einstufung nach dem Durchschnitt der Sternebewertung der Bewertungen, die das Thema nennen; keine Textanalyse"


def rating_class(value: float) -> str:
    if value >= POSITIVE_FROM:
        return "positive"
    if value >= NEUTRAL_FROM:
        return "neutral"
    return "negative"


@lru_cache(maxsize=256)
def _compiled_keywords(keywords: tuple) -> tuple:
    single = tuple(re.compile(p, re.IGNORECASE) for p in keywords)
    combined = re.compile("|".join(f"(?:{p})" for p in keywords), re.IGNORECASE)
    return single, combined


def analyze_topic(
    topic_name: str,
    keywords: List[str],
    rating_fields: List[str],
    all_reviews: List[Dict[str, Any]]
) -> Dict[str, Any]:
    text_fields = TOPIC_TEXT_FIELDS
    keyword_res, any_keyword = _compiled_keywords(tuple(keywords))
    
    mentions = []
    ratings = []
    example_texts = []
    typical_statements = []
    review_details = []
    distribution = {"negative": 0, "neutral": 0, "positive": 0}
    fallback_overall = 0

    for review in all_reviews:
        mentioned = False
        mention_texts = []
        full_review_text = []
        
        for field in text_fields:
            text = review.get(field, "")
            if text and isinstance(text, str):
                text_lower = text.lower()
                if not any_keyword.search(text_lower):
                    continue
                for keyword_re in keyword_res:
                    if keyword_re.search(text_lower):
                        mentioned = True
                        sentences = re.split(r'[.!?]+', text) if field not in QUOTE_EXCLUDED_FIELDS else []
                        for sentence in sentences:
                            if keyword_re.search(sentence) and len(sentence.strip()) > 20:
                                mention_texts.append(sentence.strip())
                                break
                        
                        full_review_text.append(f"{field}: {text}")
                        break
        
        if mentioned:
            mentions.append(review)
            
            if mention_texts:
                for text in mention_texts[:3]:
                    example_texts.append(clean_html_text(text))
                    review_details.append({
                        "id": review.get("id"),
                        "preview": clean_html_text(text),
                        "fullReview": build_full_review(review),
                    })
            
            topic_specific = []
            for field in rating_fields:
                field_rating = review.get(field)
                if field_rating is not None:
                    try:
                        topic_specific.append(float(field_rating))
                    except (TypeError, ValueError):
                        pass

            review_value = None
            if topic_specific:
                ratings.extend(topic_specific)
                review_value = sum(topic_specific) / len(topic_specific)
            else:
                avg_rating_val = review.get("durchschnittsbewertung")
                if avg_rating_val is not None:
                    try:
                        review_value = float(avg_rating_val)
                        ratings.append(review_value)
                        fallback_overall += 1
                    except (TypeError, ValueError):
                        pass
            if review_value is not None:
                distribution[rating_class(review_value)] += 1
    
    avg_exact = sum(ratings) / len(ratings) if ratings else 0.0
    avg_rating = round(avg_exact, 2)
    sentiment, color = {
        "positive": ("Positiv", "green"),
        "neutral": ("Neutral", "orange"),
        "negative": ("Negativ", "red"),
    }[rating_class(avg_exact)]
    
    timeline_data = []
    months_order = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    
    all_dates = []
    for review in mentions:
        date_str = review.get("datum")
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                all_dates.append(date)
            except:
                pass
    
    if all_dates:
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        current_date = min_date.replace(day=1)
        end_date = max_date.replace(day=1)
        
        monthly_data = defaultdict(list)
        for review in mentions:
            date_str = review.get("datum")
            avg_rating_review = review.get("durchschnittsbewertung")
            if date_str and avg_rating_review:
                try:
                    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    month_year_key = f"{months_order[date.month - 1]} {date.year}"
                    monthly_data[month_year_key].append(float(avg_rating_review))
                except:
                    pass
        
        while current_date <= end_date:
            month_name = months_order[current_date.month - 1]
            month_year_key = f"{month_name} {current_date.year}"
            
            if month_year_key in monthly_data and monthly_data[month_year_key]:
                month_avg = sum(monthly_data[month_year_key]) / len(monthly_data[month_year_key])
                timeline_data.append({
                    "month": month_year_key,
                    "rating": round(month_avg, 1),
                    "year": current_date.year,
                    "monthNum": current_date.month
                })
            
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    
    def _richness_score(detail):
        fr = detail.get("fullReview") or {}
        fields = [
            fr.get("gut_am_arbeitgeber", "") or "",
            fr.get("schlecht_am_arbeitgeber", "") or "",
            fr.get("verbesserungsvorschlaege", "") or "",
            fr.get("stellenbeschreibung", "") or "",
            fr.get("jobbeschreibung", "") or "",
        ]
        filled = sum(1 for f in fields if len(f.strip()) > 20)
        total_chars = sum(len(f) for f in fields)
        gut = fr.get("gut_am_arbeitgeber", "") or ""
        schlecht = fr.get("schlecht_am_arbeitgeber", "") or ""
        both_bonus = 15 if (len(gut.strip()) > 20 and len(schlecht.strip()) > 20) else 0
        return filled * 10 + both_bonus + min(total_chars / 100, 20)

    if review_details:
        def score_statement(detail):
            text = detail.get("preview", "")
            text_lower = text.lower()
            score = 0.0

            keyword_hits = 0
            for kw in keywords:
                keyword_hits += len(re.findall(kw, text_lower, re.IGNORECASE))
            score += keyword_hits * 10

            length = len(text)
            if 40 <= length <= 200:
                score += 8
            elif 25 <= length <= 300:
                score += 4
            elif length > 300:
                score += 1

            generic_patterns = [
                r'^(ja|nein|ok|gut|schlecht|nichts|keine ahnung|kein kommentar)',
                r'^(s\.?\s*o\.?|siehe oben|wie gesagt)',
                r'^[-–—•\s]*$',
            ]
            for pattern in generic_patterns:
                if re.search(pattern, text_lower.strip()):
                    score -= 15

            substantive_indicators = [
                r'\b(ist|sind|war|wurde|haben|kann|sollte|muss|finde|denke|fühle)\b',
                r'\b(sehr|besonders|leider|leicht|schwer|gut|toll|super|schlecht|mangelhaft)\b',
            ]
            for pattern in substantive_indicators:
                if re.search(pattern, text_lower):
                    score += 2

            score += _richness_score(detail) * 0.4

            return score
        
        scored = [(score_statement(d), i, d) for i, d in enumerate(review_details)]
        scored.sort(key=lambda x: -x[0])
        
        selected_reviews = []
        selected_texts = []
        
        def is_too_similar(new_text, existing_texts, threshold=0.6):
            new_words = set(new_text.lower().split())
            if len(new_words) < 3:
                return any(new_text.lower().strip() == e.lower().strip() for e in existing_texts)
            for existing in existing_texts:
                existing_words = set(existing.lower().split())
                if not existing_words or not new_words:
                    continue
                overlap = len(new_words & existing_words)
                max_len = max(len(new_words), len(existing_words))
                if max_len > 0 and overlap / max_len > threshold:
                    return True
            return False
        
        for _score, _idx, detail in scored:
            if len(selected_reviews) >= 13:
                break
            preview = detail.get("preview", "")
            preview_lower = preview.lower()
            has_keyword = any(re.search(kw, preview_lower, re.IGNORECASE) for kw in keywords)
            if has_keyword and not is_too_similar(preview, selected_texts):
                selected_reviews.append(detail)
                selected_texts.append(preview)
        
        if len(selected_reviews) < 13:
            for _score, _idx, detail in scored:
                if len(selected_reviews) >= 13:
                    break
                if detail not in selected_reviews:
                    preview = detail.get("preview", "")
                    preview_lower = preview.lower()
                    has_keyword = any(re.search(kw, preview_lower, re.IGNORECASE) for kw in keywords)
                    if has_keyword:
                        selected_reviews.append(detail)
        
        top_statements = selected_reviews[:3]
        example_pool = selected_reviews[3:]
        example_pool.sort(key=_richness_score, reverse=True)
        selected_reviews = top_statements + example_pool
        
        typical_statements = [detail["preview"] for detail in selected_reviews]
    else:
        typical_statements = [f"Keine spezifischen Aussagen zu {topic_name} gefunden"]
        selected_reviews = [{
            "id": None,
            "preview": typical_statements[0],
            "fullReview": None
        }]
    
    example = typical_statements[0] if typical_statements else f"Thema: {topic_name}"
    if len(example) > 80:
        example = example[:77] + "..."
    
    n_rated = sum(distribution.values())
    return {
        "topic": topic_name,
        "frequency": len(mentions),
        "avgRating": avg_rating,
        "sentiment": sentiment,
        "n_rated": n_rated,
        "rating_basis": {
            "fields": list(rating_fields),
            "n_category": n_rated - fallback_overall,
            "n_overall_fallback": fallback_overall,
            "classification": CLASSIFICATION_BASIS,
            "neutral_from": NEUTRAL_FROM,
            "positive_from": POSITIVE_FROM,
        },
        "ratingDistribution": {
            **distribution,
            "n": sum(distribution.values()),
            "fallback_overall": fallback_overall,
            "neutral_from": NEUTRAL_FROM,
            "positive_from": POSITIVE_FROM,
        },
        "example": example,
        "color": color,
        "timelineData": timeline_data,
        "typicalStatements": typical_statements,
        "reviewDetails": selected_reviews
    }


TOPIC_DEFINITIONS_BY_SOURCE: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "employee": EMPLOYEE_TOPIC_DEFINITIONS,
    "candidates": CANDIDATE_TOPIC_DEFINITIONS,
}


def topic_definitions_for(source: Optional[str]) -> Dict[str, Dict[str, List[str]]]:
    if source in TOPIC_DEFINITIONS_BY_SOURCE:
        return TOPIC_DEFINITIONS_BY_SOURCE[source]
    return {**EMPLOYEE_TOPIC_DEFINITIONS, **CANDIDATE_TOPIC_DEFINITIONS}


_COMPILED: Dict[Optional[str], List[tuple]] = {}


def _compiled_topics(source: Optional[str]) -> List[tuple]:
    if source not in _COMPILED:
        _COMPILED[source] = [
            (name, [re.compile(p, re.IGNORECASE) for p in config["keywords"]])
            for name, config in topic_definitions_for(source).items()
        ]
    return _COMPILED[source]


_COMBINED: Dict[Optional[str], List[tuple]] = {}


def _combined_topics(source: Optional[str]) -> List[tuple]:
    if source not in _COMBINED:
        _COMBINED[source] = [
            (name, re.compile("|".join(f"(?:{p})" for p in config["keywords"]), re.IGNORECASE))
            for name, config in topic_definitions_for(source).items()
        ]
    return _COMBINED[source]


def topics_in_review(row: Dict[str, Any], source: Optional[str], fields: Optional[List[str]] = None) -> List[str]:
    texts = [
        row.get(field).lower()
        for field in (TOPIC_TEXT_FIELDS if fields is None else fields)
        if row.get(field) and isinstance(row.get(field), str)
    ]
    if not texts:
        return []
    return [
        name for name, pattern in _combined_topics(source)
        if any(pattern.search(text) for text in texts)
    ]


def topic_for_dimension(source: str, dimension: str) -> Optional[str]:
    from services.rating_series_service import OVERALL_DIMENSION, value_column

    column = value_column(source, dimension)
    if dimension == OVERALL_DIMENSION:
        return None
    return next(
        (name for name, config in topic_definitions_for(source).items() if column in config["rating_fields"]),
        None,
    )


def dimension_for_topic(source: str, topic: str) -> Optional[str]:
    from services.rating_series_service import DIMENSIONS_BY_SOURCE, OVERALL_DIMENSION, value_column

    fields = (topic_definitions_for(source).get(topic) or {}).get("rating_fields") or []
    for dimension in DIMENSIONS_BY_SOURCE.get(source, []):
        if dimension != OVERALL_DIMENSION and value_column(source, dimension) in fields:
            return dimension
    return None


def topic_spans(text: Any, topic: str, source: Optional[str]) -> List[List[int]]:
    if not text or not isinstance(text, str):
        return []
    patterns = next((p for name, p in _compiled_topics(source) if name == topic), [])
    found = sorted((m.start(), m.end()) for p in patterns for m in p.finditer(text) if m.end() > m.start())
    merged: List[List[int]] = []
    for start, end in found:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


__all__ = [
    "topic_for_dimension", "dimension_for_topic", "topic_spans",
    "TOPIC_TEXT_FIELDS", "EXPLANATION_TOPIC_TEXT_FIELDS", "EMPLOYEE_TOPIC_DEFINITIONS", "CANDIDATE_TOPIC_DEFINITIONS",
    "QUOTE_EXCLUDED_FIELDS", "TOPIC_DEFINITIONS_BY_SOURCE", "topic_definitions_for", "topics_in_review", "analyze_topic",
    "NEUTRAL_FROM", "POSITIVE_FROM", "CLASSIFICATION_BASIS", "rating_class",
]
