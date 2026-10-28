from fastapi import APIRouter, HTTPException, Query
from database.supabase_client import get_supabase_client
from typing import Optional, List, Dict, Any, Literal
from services.topic_average_rating_service import _fetch_all_rows, fetch_all_rows_parallel, get_topic_rating_timeseries
import services.review_service as review_service
from services.keyword_topic_service import EXPLANATION_TOPIC_TEXT_FIELDS, analyze_topic, topic_definitions_for, topic_for_dimension, topic_spans, topics_in_review
from services.dimension_scope import REVIEW_SCOPE_NOTE, mean_rating, review_dimension_info, single_dimension_topic
from services.rating_series_service import OVERALL_DIMENSION
from services.review_service import (
    clean_html_text,
    fetch_review_rows_in_range,
    filter_by_status,
    full_review_item,
    parse_day,
    sort_by_date,
    validate_status,
)
from services.statistical_validator import StatisticalValidator
from services.statistical_enrichment import (
    enrich_with_statistical_metadata,
    enrich_topic_analysis_with_metadata,
    enrich_comparison_with_metadata
)
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import random

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/company/{company_id}/overview")
def get_company_overview(company_id: int):
    supabase = get_supabase_client()
    try:
        candidates_response = supabase.table("candidates")\
            .select("durchschnittsbewertung, datum")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_response = supabase.table("employee")\
            .select("durchschnittsbewertung, datum")\
            .eq("company_id", company_id)\
            .execute()
        
        candidates_data = candidates_response.data or []
        employee_data = employee_response.data or []
        
        all_ratings = [
            float(r["durchschnittsbewertung"]) 
            for r in candidates_data + employee_data 
            if r.get("durchschnittsbewertung")
        ]
        
        avg_score = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 0
        
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        def _parse_datum(d: str) -> datetime:
            dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None) if dt.tzinfo else dt

        recent_ratings = [
            float(r["durchschnittsbewertung"])
            for r in candidates_data + employee_data
            if r.get("durchschnittsbewertung") and r.get("datum")
            and _parse_datum(r["datum"]) >= thirty_days_ago
        ]

        previous_ratings = [
            float(r["durchschnittsbewertung"])
            for r in candidates_data + employee_data
            if r.get("durchschnittsbewertung") and r.get("datum")
            and sixty_days_ago <= _parse_datum(r["datum"]) < thirty_days_ago
        ]
        
        recent_avg = sum(recent_ratings) / len(recent_ratings) if recent_ratings else 0
        previous_avg = sum(previous_ratings) / len(previous_ratings) if previous_ratings else 0
        trend = round(recent_avg - previous_avg, 2)
        
        critical_category = get_most_critical_category(company_id)
        
        return {
            "average_score": avg_score,
            "trend": trend,
            "total_reviews": len(candidates_data) + len(employee_data),
            "candidate_reviews": len(candidates_data),
            "employee_reviews": len(employee_data),
            "most_critical": critical_category
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company overview: {str(e)}")


@router.get("/company/{company_id}/timeline")
def get_company_timeline(
    company_id: int,
    days: int = Query(default=365, description="Number of days to include"),
    forecast_months: int = Query(default=12, description="Number of months to forecast"),
    source: str = Query(default="all", description="Data source: 'employee', 'candidates', or 'all'")
):
    supabase = get_supabase_client()
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        timeline_data = []
        
        if source in ["candidates", "all"]:
            candidates_query = supabase.table("candidates")\
                .select("durchschnittsbewertung, datum")\
                .eq("company_id", company_id)\
                .gte("datum", cutoff_date.isoformat())\
                .order("datum")\
                .order("id")
            
            candidates_data = _fetch_all_rows(candidates_query, page_size=review_service.PAGE_SIZE)
            for item in candidates_data:
                if item.get("datum") and item.get("durchschnittsbewertung"):
                    timeline_data.append({
                        "date": item["datum"],
                        "score": float(item["durchschnittsbewertung"]),
                        "type": "candidate"
                    })
        
        if source in ["employee", "all"]:
            employee_query = supabase.table("employee")\
                .select("durchschnittsbewertung, datum")\
                .eq("company_id", company_id)\
                .gte("datum", cutoff_date.isoformat())\
                .order("datum")\
                .order("id")
            
            employee_data = _fetch_all_rows(employee_query, page_size=review_service.PAGE_SIZE)
            for item in employee_data:
                if item.get("datum") and item.get("durchschnittsbewertung"):
                    timeline_data.append({
                        "date": item["datum"],
                        "score": float(item["durchschnittsbewertung"]),
                        "type": "employee"
                    })
        
        timeline_data.sort(key=lambda x: x["date"])
        
        monthly_data = defaultdict(list)
        for item in timeline_data:
            try:
                date = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
                month_key = date.strftime("%Y-%m")
                monthly_data[month_key].append(item["score"])
            except:
                pass
        
        aggregated_timeline = []
        for month_key in sorted(monthly_data.keys()):
            scores = monthly_data[month_key]
            date_obj = datetime.strptime(month_key, "%Y-%m")
            aggregated_timeline.append({
                "date": month_key,
                "date_display": date_obj.strftime("%b %Y"),
                "score": round(sum(scores) / len(scores), 2),
                "count": len(scores),
                "is_forecast": False
            })
        
        forecast_data, forecast_info = forecast_with_details(aggregated_timeline, forecast_months)
        
        return {
            "timeline": aggregated_timeline,
            "forecast": forecast_data,
            "forecast_info": forecast_info,
            "total_points": len(timeline_data),
            "current_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timeline: {str(e)}")


def _fallback_forecast_average(
    historical_data: List[Dict[str, Any]], months: int, y_values: List[float]
) -> List[Dict[str, Any]]:
    avg_score = sum(y_values) / len(y_values)
    forecast = []
    last_date = datetime.strptime(historical_data[-1]["date"], "%Y-%m")
    for i in range(1, months + 1):
        month_offset = last_date.month + i
        year_offset = (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        next_month = last_date.replace(year=last_date.year + year_offset, month=month)
        forecast.append({
            "date": next_month.strftime("%Y-%m"),
            "date_display": next_month.strftime("%b %Y"),
            "score": round(avg_score, 2),
            "is_forecast": True
        })
    return forecast


def calculate_forecast(historical_data: List[Dict[str, Any]], months: int) -> List[Dict[str, Any]]:
    return forecast_with_details(historical_data, months)[0]


def _months_since(last_month: str, today: Optional[datetime] = None) -> int:
    now = today or datetime.now()
    y, m = (int(x) for x in last_month.split("-"))
    return (now.year - y) * 12 + (now.month - m)


def forecast_with_details(
    historical_data: List[Dict[str, Any]], months: int, today: Optional[datetime] = None
) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if months <= 0:
        return [], None
    if len(historical_data) < 2:
        return [], None

    from services.forecast_service import (
        INTERVAL_LEVEL, MIN_TRAIN, interval_offsets, public_backtest, rolling_origin_backtest,
    )
    from services.rating_series_service import MIN_REVIEWS_PER_MONTH

    y_values = [point["score"] for point in historical_data]
    last_date = datetime.strptime(historical_data[-1]["date"], "%Y-%m")
    info: Dict[str, Any] = {
        "n_months": len(historical_data),
        "first_month": historical_data[0]["date"],
        "last_month": historical_data[-1]["date"],
        "historical_mean": round(sum(y_values) / len(y_values), 4),
        "months_since_last_data": _months_since(historical_data[-1]["date"], today),
        "months_below_min_reviews": sum(
            1 for point in historical_data
            if point.get("count") is not None and int(point["count"]) < MIN_REVIEWS_PER_MONTH
        ),
        "min_reviews_per_month": MIN_REVIEWS_PER_MONTH,
    }
    backtest = rolling_origin_backtest(y_values, horizon=months, min_train=MIN_TRAIN)
    info["backtest"] = public_backtest(backtest)
    offsets = interval_offsets(backtest, method="holt", level=INTERVAL_LEVEL)
    info["interval"] = {
        "level": INTERVAL_LEVEL,
        "basis": "empirische Quantile der Backtest-Fehler je Horizont (Beobachtung minus Prognose)",
        "available": bool(offsets),
    }

    try:
        from statsmodels.tsa.holtwinters import Holt  # type: ignore[import-untyped]
        import numpy as np

        series = np.asarray(y_values, dtype=float)
        model = Holt(series)
        fit = model.fit()
        preds = fit.forecast(steps=months)
    except Exception:
        info["method"] = "mean"
        return _fallback_forecast_average(historical_data, months, y_values), info

    def _num(value: Any) -> Optional[float]:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None
        return round(v, 4) if np.isfinite(v) else None

    levels = list(np.asarray(fit.level, dtype=float))
    trends = list(np.asarray(fit.trend, dtype=float))
    info.update({
        "method": "holt",
        "alpha": _num(fit.params.get("smoothing_level")),
        "beta": _num(fit.params.get("smoothing_trend")),
        "level": _num(levels[-1]) if levels else None,
        "trend": _num(trends[-1]) if trends else None,
        "smoothed": [
            {"date": point["date"], "value": _num(levels[i])}
            for i, point in enumerate(historical_data)
            if i < len(levels)
        ],
    })

    forecast = []
    clamped = False
    for i in range(months):
        month_offset = last_date.month + (i + 1)
        year_offset = (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        next_month = last_date.replace(year=last_date.year + year_offset, month=month)
        raw = float(preds[i])
        score = max(0.0, min(5.0, raw))
        clamped = clamped or score != raw
        band = offsets.get(i + 1)
        forecast.append({
            "date": next_month.strftime("%Y-%m"),
            "date_display": next_month.strftime("%b %Y"),
            "score": round(score, 2),
            "is_forecast": True,
            "low": round(max(0.0, min(5.0, score + band["low"])), 2) if band else None,
            "high": round(max(0.0, min(5.0, score + band["high"])), 2) if band else None
        })
    info["clamped"] = clamped
    return forecast, info


@router.get("/company/{company_id}/category-ratings")
def get_category_ratings(company_id: int):
    supabase = get_supabase_client()
    try:
        candidates_response = supabase.table("candidates")\
            .select("*")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_response = supabase.table("employee")\
            .select("*")\
            .eq("company_id", company_id)\
            .execute()
        
        candidates_data = candidates_response.data or []
        employee_data = employee_response.data or []
        
        candidate_categories = {}
        candidate_rating_fields = [
            col for col in (candidates_data[0].keys() if candidates_data else [])
            if col.startswith("sternebewertung_")
        ]
        
        for field in candidate_rating_fields:
            ratings = [
                float(r[field]) for r in candidates_data 
                if r.get(field) is not None
            ]
            if ratings:
                category_name = field.replace("sternebewertung_", "").replace("_", " ").title()
                candidate_categories[category_name] = round(sum(ratings) / len(ratings), 2)
        
        employee_categories = {}
        employee_rating_fields = [
            col for col in (employee_data[0].keys() if employee_data else [])
            if col.startswith("sternebewertung_")
        ]
        
        for field in employee_rating_fields:
            ratings = [
                float(r[field]) for r in employee_data 
                if r.get(field) is not None
            ]
            if ratings:
                category_name = field.replace("sternebewertung_", "").replace("_", " ").title()
                employee_categories[category_name] = round(sum(ratings) / len(ratings), 2)
        
        return {
            "candidate_categories": candidate_categories,
            "employee_categories": employee_categories
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category ratings: {str(e)}")


def get_most_critical_category(company_id: int) -> Dict[str, Any]:
    try:
        category_data = get_category_ratings(company_id)
        
        all_categories = {
            **category_data["candidate_categories"],
            **category_data["employee_categories"]
        }
        
        if not all_categories:
            return {"category": "N/A", "score": 0}
        
        lowest = min(all_categories.items(), key=lambda x: x[1])
        return {
            "category": lowest[0],
            "score": lowest[1]
        }
        
    except Exception:
        return {"category": "N/A", "score": 0}


def _review_list_item(item: Dict[str, Any], source: str) -> Dict[str, Any]:
    if source == "candidates":
        return {
            "id": item["id"],
            "type": "candidate",
            "date": item.get("datum"),
            "score": float(item.get("durchschnittsbewertung", 0)),
            "title": item.get("titel", ""),
            "description": item.get("stellenbeschreibung", ""),
            "improvements": item.get("verbesserungsvorschlaege", "")
        }
    return {
        "id": item["id"],
        "type": "employee",
        "date": item.get("datum"),
        "score": float(item.get("durchschnittsbewertung", 0)),
        "title": item.get("titel", ""),
        "job_description": item.get("jobbeschreibung", ""),
        "positive": item.get("gut_am_arbeitgeber_finde_ich", ""),
        "negative": item.get("schlecht_am_arbeitgeber_finde_ich", ""),
        "improvements": item.get("verbesserungsvorschlaege", "")
    }


def _reviews_in_range(
    company_id: int,
    source: Optional[str],
    start: Optional[str],
    end: Optional[str],
    status: Optional[str],
    offset: int,
    limit: int,
    full: bool,
    dimension: Optional[str] = None,
    topic_only: bool = False,
    topic_filter: Optional[str] = None,
    order: str = "desc",
    dimension_only: bool = False,
) -> Dict[str, Any]:
    if source is not None and source not in ("employee", "candidates"):
        raise ValueError(f"source '{source}' ungültig; erlaubt: employee, candidates.")
    if status is not None and source is None:
        raise ValueError("status braucht source (employee oder candidates).")
    start_day, end_day = parse_day(start, "start"), parse_day(end, "end")
    if start_day and end_day and start_day > end_day:
        raise ValueError("start liegt nach end.")
    validate_status(source, status) if source else None
    if dimension is not None and source is None:
        raise ValueError("dimension braucht source (employee oder candidates).")
    topic = topic_for_dimension(source, dimension) if dimension is not None else None
    if topic_only and dimension is None:
        raise ValueError("topic_only braucht dimension.")
    if dimension_only:
        single_dimension_topic(source, dimension)
    single = dimension is not None and dimension != OVERALL_DIMENSION
    if topic_filter is not None:
        if topic_only:
            raise ValueError("topic und topic_only schließen sich aus.")
        if topic_filter not in topic_definitions_for(source):
            raise ValueError(f"Thema '{topic_filter}' gibt es für diese Quelle nicht.")
    if order not in ("desc", "asc"):
        raise ValueError(f"order '{order}' ungültig; erlaubt: desc, asc.")

    sources = [source] if source else ["candidates", "employee"]
    tagged = []
    for src in sources:
        rows = fetch_review_rows_in_range(src, company_id, start_day, end_day)
        tagged.extend({**row, "_source": src} for row in filter_by_status(rows, src, status))
    ordered = sort_by_date(tagged, newest_first=order == "desc")
    for row in ordered:
        row["_topics"] = topics_in_review(row, row["_source"], EXPLANATION_TOPIC_TEXT_FIELDS)
        if single:
            row["_dim"] = review_dimension_info(row, row["_source"], dimension, topic, row["_topics"])
    n_all = len(ordered)
    if dimension_only:
        ordered = [r for r in ordered if r["_dim"]["in_dimension"]]
    scoped = ordered
    mentioning = [r for r in ordered if topic in r["_topics"]] if topic else []
    counts = Counter(t for r in ordered for t in r["_topics"])
    topic_summary = {
        "counts": [{"topic": name, "n": counts[name]} for name in topic_definitions_for(source) if counts[name]],
        "without_topic": sum(1 for r in ordered if not r["_topics"]),
        "filter": topic_filter if topic_filter is not None else topic if topic_only else None,
    }
    if topic_only:
        ordered = mentioning
    elif topic_filter is not None:
        ordered = [r for r in ordered if topic_filter in r["_topics"]]
    marked = topic_summary["filter"] or topic
    topic_summary["marked"] = marked
    page = ordered[offset: offset + max(limit, 0)]

    def item(row: Dict[str, Any]) -> Dict[str, Any]:
        src = row.pop("_source")
        topics = row.pop("_topics")
        dim = row.pop("_dim", None)
        out = full_review_item(row, src) if full else _review_list_item(row, src)
        out["topics"] = topics
        if topic is not None:
            out["mentions_topic"] = topic in topics
        if dim is not None:
            out["dimension"] = {k: dim[k] for k in ("key", "rating", "comment", "mentions_topic", "in_dimension")}
        if marked is not None and full:
            texts = {"preview": out["preview"], **{k: out["fullReview"].get(k) for k in HIGHLIGHT_FIELDS}}
            if dim is not None and dim["comment"]:
                texts["comment"] = dim["comment"]
            spans = {k: topic_spans(v, marked, src) for k, v in texts.items()}
            out["highlights"] = {k: v for k, v in spans.items() if v}
        return out

    result = {
        "reviews": [item(dict(row)) for row in page],
        "total": len(ordered),
        "offset": offset,
        "limit": limit,
        "order": order,
        "topic_summary": topic_summary,
    }
    if dimension is not None:
        result["highlight"] = {
            "dimension": dimension,
            "topic": topic,
            "mentions": len(mentioning) if topic else None,
            "topic_only": topic_only,
        }
        if dimension_only:
            result["highlight"].update({
                "dimension_only": True,
                "n_all": n_all,
                "n_dimension": len(scoped),
                "dimension_mean": mean_rating([r["_dim"] for r in scoped]),
                "note": REVIEW_SCOPE_NOTE,
            })
    return result


HIGHLIGHT_FIELDS = (
    "titel", "gut_am_arbeitgeber", "schlecht_am_arbeitgeber", "verbesserungsvorschlaege",
    "stellenbeschreibung", "jobbeschreibung",
)


@router.get("/company/{company_id}/reviews")
def get_company_reviews(
    company_id: int,
    limit: int = Query(default=50, description="Maximum number of reviews to return"),
    source: Optional[str] = Query(default=None, description="Filter by source: 'candidates' or 'employee'"),
    start: Optional[str] = Query(default=None, description="Erster Tag (YYYY-MM-DD, einschließlich)"),
    end: Optional[str] = Query(default=None, description="Letzter Tag (YYYY-MM-DD, einschließlich)"),
    status: Optional[str] = Query(default=None, description="Statusschlüssel der Bewertendengruppe, braucht source"),
    offset: Optional[int] = Query(default=None, ge=0, description="Anzahl übersprungener Bewertungen"),
    format_: Optional[Literal["full"]] = Query(default=None, alias="format", description="'full': je Bewertung id, preview, fullReview"),
    dimension: Optional[str] = Query(default=None, description="Dimension; markiert Fundstellen des zugehörigen Schlüsselwort-Themas, braucht source"),
    topic_only: bool = Query(default=False, description="Nur Bewertungen, die das Thema der Dimension nennen; braucht dimension"),
    topic: Optional[str] = Query(default=None, description="Nur Bewertungen, die dieses Schlüsselwort-Thema nennen (Name wie in der Themenübersicht)"),
    order: Optional[Literal["desc", "asc"]] = Query(default=None, description="Sortierung nach Datum: 'desc' neueste zuerst (Standard), 'asc' älteste zuerst"),
    dimension_only: bool = Query(default=False, description="Nur Bewertungen zur Dimension (Kommentar zur Kategorie oder Schlüsselwort des Themas); braucht eine Einzeldimension"),
):
    if any(p is not None for p in (start, end, status, offset, format_, dimension, topic, order)):
        try:
            return _reviews_in_range(
                company_id, source, start, end, status, offset or 0, limit, full=format_ == "full",
                dimension=dimension, topic_only=topic_only, topic_filter=topic, order=order or "desc",
                dimension_only=dimension_only,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")

    supabase = get_supabase_client()
    try:
        reviews = []
        
        if source is None or source == "candidates":
            candidates_response = supabase.table("candidates")\
                .select("*")\
                .eq("company_id", company_id)\
                .order("datum", desc=True)\
                .limit(limit if source == "candidates" else limit // 2)\
                .execute()
            
            for item in candidates_response.data or []:
                reviews.append(_review_list_item(item, "candidates"))
        
        if source is None or source == "employee":
            employee_response = supabase.table("employee")\
                .select("*")\
                .eq("company_id", company_id)\
                .order("datum", desc=True)\
                .limit(limit if source == "employee" else limit // 2)\
                .execute()
            
            for item in employee_response.data or []:
                reviews.append(_review_list_item(item, "employee"))
        
        reviews.sort(key=lambda x: x.get("date") or "", reverse=True)
        
        return {
            "reviews": reviews[:limit],
            "total": len(reviews)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")


@router.get("/company/{company_id}/negative-topics")
def get_negative_topics(company_id: int):
    supabase = get_supabase_client()
    try:
        employee_response = supabase.table("employee")\
            .select("schlecht_am_arbeitgeber_finde_ich, durchschnittsbewertung")\
            .eq("company_id", company_id)\
            .execute()
        
        candidates_response = supabase.table("candidates")\
            .select("verbesserungsvorschlaege, durchschnittsbewertung")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_data = employee_response.data or []
        candidates_data = candidates_response.data or []
        
        negative_texts = []
        for item in employee_data:
            if item.get("schlecht_am_arbeitgeber_finde_ich"):
                negative_texts.append(item["schlecht_am_arbeitgeber_finde_ich"])
        
        for item in candidates_data:
            if item.get("verbesserungsvorschlaege"):
                negative_texts.append(item["verbesserungsvorschlaege"])
        
        keywords = {}
        negative_keywords = [
            "gehalt", "kommunikation", "management", "work-life-balance", 
            "stress", "überstunden", "kollegen", "chef", "führung",
            "bezahlung", "karriere", "entwicklung", "atmosphäre"
        ]
        
        for text in negative_texts:
            text_lower = text.lower()
            for keyword in negative_keywords:
                if keyword in text_lower:
                    keywords[keyword] = keywords.get(keyword, 0) + 1
        
        sorted_topics = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "negative_topics": [
                {"topic": topic, "count": count} 
                for topic, count in sorted_topics[:10]
            ],
            "total_negative_mentions": sum(keywords.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching negative topics: {str(e)}")


@router.get("/company/{company_id}/topic-overview")
def get_topic_overview(
    company_id: int,
    source: Optional[str] = Query(default=None, description="Filter by source: 'candidates' or 'employee'"),
    start_date: Optional[str] = Query(default=None, description="Filter reviews from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Letzter Tag (YYYY-MM-DD, einschließlich)"),
):
    try:
        end_day = parse_day(end_date, "end_date")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    end_exclusive = (end_day + timedelta(days=1)).isoformat() if end_day else None
    try:
        candidates_data = []
        employee_data = []

        def review_query(table: str):
            def build(count=None):
                query = get_supabase_client().table(table).select("*", count=count).eq("company_id", company_id)
                if start_date:
                    query = query.gte("datum", start_date)
                if end_exclusive:
                    query = query.lt("datum", end_exclusive)
                return query.order("id")
            return build

        if source is None or source == "candidates":
            candidates_data = fetch_all_rows_parallel(review_query("candidates"), page_size=review_service.PAGE_SIZE)

        if source is None or source == "employee":
            employee_data = fetch_all_rows_parallel(review_query("employee"), page_size=review_service.PAGE_SIZE)
        
        all_reviews = candidates_data + employee_data
        
        if not all_reviews:
            return {
                "topics": [],
                "total_reviews": 0,
                "message": "No reviews found for this company"
            }
        
        topic_definitions = topic_definitions_for(source)
        if source == "employee":
            reviews_to_analyze = employee_data
        elif source == "candidates":
            reviews_to_analyze = candidates_data
        else:
            reviews_to_analyze = all_reviews
        
        topics_data = []
        
        for topic_name, topic_config in topic_definitions.items():
            topic_analysis = analyze_topic(
                topic_name=topic_name,
                keywords=topic_config["keywords"],
                rating_fields=topic_config["rating_fields"],
                all_reviews=reviews_to_analyze
            )
            
            if topic_analysis["frequency"] > 0:
                topics_data.append(topic_analysis)
        
        topics_data.sort(key=lambda x: x["frequency"], reverse=True)
        
        for idx, topic in enumerate(topics_data, start=1):
            topic["id"] = idx
        
        total_reviews = len(reviews_to_analyze)
        enriched_topics = enrich_topic_analysis_with_metadata(topics_data, total_reviews)
        
        result = {
            "topics": enriched_topics,
            "total_reviews": total_reviews,
            "total_by_source": {
                "employee": len(employee_data) if source in (None, "employee") else 0,
                "candidates": len(candidates_data) if source in (None, "candidates") else 0,
            },
            "total_topics": len(enriched_topics)
        }
        
        result = enrich_with_statistical_metadata(
            result,
            sample_size=total_reviews,
            analysis_type="anova"
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating topic overview: {str(e)}")

@router.get("/company/{company_id}/topic-ratings-timeseries")
def topic_ratings_timeseries(
    company_id: int,
    source: Literal["employee", "candidates"] = Query(..., description="employee or candidates"),
    granularity: Literal["month", "year"] = Query("month", description="month or year"),
    start: Optional[str] = Query(None, description="ISO date/time, e.g. 2023-01-01"),
    end: Optional[str] = Query(None, description="ISO date/time, e.g. 2024-12-31"),
):
    try:
        return get_topic_rating_timeseries(
            source=source,
            company_id=company_id,
            granularity=granularity,
            start=start,
            end=end,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building topic ratings timeseries: {str(e)}")


def extract_short_kritikpunkt(text: str, max_words: int = 4) -> str:
    if not text or not isinstance(text, str):
        return ""
    
    text = clean_html_text(text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    
    negative_patterns = [
        r'keine?\s+(\w+)',
        r'schlechte[rns]?\s+(\w+)',
        r'fehlende[rns]?\s+(\w+)',
        r'mangelnde[rns]?\s+(\w+)',
        r'wenig\s+(\w+)',
        r'zu\s+wenig\s+(\w+)',
        r'kaum\s+(\w+)',
    ]
    
    negative_adjectives = {
        'schlechte', 'schlechter', 'schlechtes', 'schlecht',
        'fehlende', 'fehlender', 'fehlendes', 'fehlend',
        'mangelnde', 'mangelnder', 'mangelndes', 'mangelnd',
        'keine', 'kein', 'keiner', 'keines',
        'wenig', 'kaum', 'niedrige', 'niedriger', 'niedriges',
        'unklare', 'unklarer', 'unklares',
        'langsame', 'langsamer', 'langsames',
        'starre', 'starrer', 'starres',
        'veraltete', 'veralteter', 'veraltetes',
        'toxische', 'toxischer', 'toxisches',
    }
    
    important_nouns = {
        'kommunikation', 'führung', 'management', 'vorgesetzte', 'chef',
        'gehalt', 'bezahlung', 'vergütung', 'wertschätzung', 'respekt',
        'transparenz', 'feedback', 'entwicklung', 'karriere', 'weiterbildung',
        'arbeitsatmosphäre', 'atmosphäre', 'klima', 'kultur', 'umgang',
        'prozesse', 'strukturen', 'entscheidungen', 'hierarchie',
        'work-life-balance', 'überstunden', 'arbeitszeit', 'druck',
        'zusammenhalt', 'teamarbeit', 'kollegen', 'mitarbeiter',
    }
    
    for pattern in negative_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match in important_nouns or len(match) > 5:
                full_match = re.search(rf'(\w+\s+{match})', text)
                if full_match:
                    result = full_match.group(1).strip()
                    return result[0].upper() + result[1:]
    
    words = text.split()
    for i, word in enumerate(words):
        clean_word = re.sub(r'[^\wäöüß]', '', word)
        if clean_word in negative_adjectives and i + 1 < len(words):
            next_word = re.sub(r'[^\wäöüß]', '', words[i + 1])
            if len(next_word) >= 4:
                result = f"{clean_word} {next_word}"
                return result[0].upper() + result[1:]
    
    for word in words:
        clean_word = re.sub(r'[^\wäöüß]', '', word)
        if clean_word in important_nouns:
            return clean_word[0].upper() + clean_word[1:]
    
    return ""
    
    return ""


@router.get("/company/{company_id}/negative-kritikpunkte")
def get_negative_kritikpunkte(company_id: int):
    supabase = get_supabase_client()
    try:
        employee_response = supabase.table("employee")\
            .select("*")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_data = employee_response.data or []
        
        if not employee_data:
            return {
                "topic": None,
                "kritikpunkte": [],
                "avg_rating": None,
                "negative_share_percent": None,
                "message": "Keine Bewertungen gefunden"
            }
        
        negative_reviews = [
            r for r in employee_data 
            if r.get("durchschnittsbewertung") and float(r["durchschnittsbewertung"]) <= 2.5
        ]
        
        if len(negative_reviews) < 2:
            sorted_reviews = sorted(
                [r for r in employee_data if r.get("durchschnittsbewertung")],
                key=lambda x: float(x["durchschnittsbewertung"])
            )
            negative_reviews = sorted_reviews[:5]
        
        negative_reviews.sort(key=lambda x: float(x.get("durchschnittsbewertung", 5)))
        
        kritikpunkte = []
        seen_texts = set()
        
        for review in negative_reviews:
            text = review.get("schlecht_am_arbeitgeber_finde_ich", "")
            
            if not text or not isinstance(text, str) or len(text.strip()) < 10:
                continue
            
            sentences = re.split(r'[.!?\n]+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 15:
                    continue
                    
                kritikpunkt = extract_short_kritikpunkt(sentence, max_words=4)
                
                if kritikpunkt and len(kritikpunkt) >= 8 and kritikpunkt.lower() not in seen_texts:
                    kritikpunkte.append(kritikpunkt)
                    seen_texts.add(kritikpunkt.lower())
                
                if len(kritikpunkte) >= 2:
                    break
            
            if len(kritikpunkte) >= 2:
                break
        
        topic_keywords = {
            "Führungsqualität": ["führung", "vorgesetzte", "chef", "management", "leitung"],
            "Kommunikation": ["kommunikation", "information", "transparenz", "feedback"],
            "Gehalt & Benefits": ["gehalt", "bezahlung", "lohn", "vergütung", "benefits"],
            "Work-Life Balance": ["work-life", "überstunden", "arbeitszeit", "balance"],
            "Teamzusammenhalt": ["team", "kollegen", "zusammenhalt", "atmosphäre"],
            "Karriereentwicklung": ["karriere", "weiterbildung", "entwicklung", "aufstieg"]
        }
        
        topic_scores = defaultdict(int)
        for review in negative_reviews:
            text_fields = [
                review.get("schlecht_am_arbeitgeber_finde_ich", ""),
                review.get("verbesserungsvorschlaege", ""),
                review.get("titel", "")
            ]
            combined_text = " ".join(str(t) for t in text_fields if t).lower()
            
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in combined_text:
                        topic_scores[topic] += 1
        
        main_topic = max(topic_scores.items(), key=lambda x: x[1])[0] if topic_scores else "Allgemein"
        
        total_reviews = len(employee_data)
        negative_count = len([r for r in employee_data if r.get("durchschnittsbewertung") and float(r["durchschnittsbewertung"]) <= 2.5])
        negative_share = round((negative_count / total_reviews) * 100) if total_reviews > 0 else 0
        
        avg_rating = sum(float(r["durchschnittsbewertung"]) for r in negative_reviews if r.get("durchschnittsbewertung")) / len(negative_reviews) if negative_reviews else None
        
        return {
            "topic": main_topic,
            "kritikpunkte": kritikpunkte[:2],
            "avg_rating": round(avg_rating, 1) if avg_rating else None,
            "negative_share_percent": negative_share,
            "categories": [main_topic]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistical/validate-sample-size")
def validate_sample_size(
    n: int = Query(..., description="Sample size to validate", ge=1)
) -> Dict[str, Any]:
    try:
        validator = StatisticalValidator()
        assessment = validator.assess_sample_size(n)
        return assessment.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistical/validate-comparison")
def validate_comparison(
    n1: int = Query(..., description="Size of group 1 (or total n for ANOVA)", ge=1),
    n2: int = Query(..., description="Size of group 2 (or k groups for ANOVA)", ge=1),
    comparison_type: Literal["two_group", "anova"] = Query(
        "two_group", 
        description="Type of comparison: two_group (t-test) or anova"
    )
) -> Dict[str, Any]:
    try:
        validator = StatisticalValidator()
        assessment = validator.assess_comparison(n1, n2, comparison_type)
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistical/validate-correlation")
def validate_correlation(
    n: int = Query(..., description="Sample size for correlation analysis", ge=1)
) -> Dict[str, Any]:
    try:
        validator = StatisticalValidator()
        assessment = validator.validate_correlation_stability(n)
        return assessment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{company_id}/statistical-assessment")
def get_company_statistical_assessment(company_id: int) -> Dict[str, Any]:
    supabase = get_supabase_client()
    try:
        validator = StatisticalValidator()
        
        employee_response = supabase.table("employee")\
            .select("id", count="exact")\
            .eq("company_id", company_id)\
            .execute()
        
        candidate_response = supabase.table("candidates")\
            .select("id", count="exact")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_count = employee_response.count or 0
        candidate_count = candidate_response.count or 0
        total_count = employee_count + candidate_count
        
        overall_assessment = validator.assess_sample_size(total_count)
        
        employee_assessment = validator.assess_sample_size(employee_count)
        
        candidate_assessment = validator.assess_sample_size(candidate_count)
        
        comparison_assessment = validator.assess_comparison(
            employee_count, 
            candidate_count, 
            "two_group"
        ) if employee_count > 0 and candidate_count > 0 else None
        
        k_topics = 13
        topic_assessment = validator.assess_comparison(
            total_count,
            k_topics,
            "anova"
        ) if total_count > 0 else None
        
        return {
            "company_id": company_id,
            "sample_sizes": {
                "total": total_count,
                "employee": employee_count,
                "candidate": candidate_count
            },
            "overall_assessment": overall_assessment.to_dict(),
            "employee_assessment": employee_assessment.to_dict(),
            "candidate_assessment": candidate_assessment.to_dict(),
            "comparison_assessment": comparison_assessment,
            "topic_anova_assessment": topic_assessment,
            "summary": {
                "data_quality": overall_assessment.risk_level.value,
                "can_compare_employee_candidate": employee_count >= 30 and candidate_count >= 30,
                "can_perform_topic_analysis": total_count >= (k_topics * 30),
                "primary_limitation": (
                    "Sample size below CLT heuristic - prefer non-parametric tests"
                    if total_count < validator.HEURISTIC_CLT
                    else "Power may be insufficient for small effects"
                    if total_count < validator.HEURISTIC_POWER
                    else "Confidence intervals may be wide"
                    if total_count < validator.HEURISTIC_PRECISION
                    else "Sample size adequate for robust analysis"
                )
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        raise HTTPException(status_code=500, detail=f"Error fetching negative kritikpunkte: {str(e)}")