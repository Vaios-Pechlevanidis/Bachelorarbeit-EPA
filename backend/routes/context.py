from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.evidence_service import (
    DEFAULT_WINDOW_AFTER,
    DEFAULT_WINDOW_BEFORE,
    EVIDENCE_NOTE,
    MAX_WINDOW_MONTHS,
    context_for_anchor,
    context_for_selection,
    load_global_events,
    paginate,
)

router = APIRouter(prefix="/api/analytics", tags=["Context"])

DEFAULT_LIMIT = 25
MAX_LIMIT = 200


def _window_params(window_before: int, window_after: int) -> dict:
    return {"window_before": window_before, "window_after": window_after}


@router.get("/company/{company_id}/anomalies/{anomaly_id}/context")
def get_anomaly_context(
    company_id: int,
    anomaly_id: str,
    source: Optional[str] = Query(None, description="Quelle; Standard aus anomaly_id"),
    dimension: Optional[str] = Query(None, description="Dimension; Standard aus anomaly_id"),
    status: Optional[str] = Query(None, description="Statusschlüssel der Bewertendengruppe (E13); ohne = alle"),
    dimension_only: bool = Query(False, description="Nur Belege zur Dimension (Schlüsselwort des Themas im Titel oder zugeordnete Ereignisart, 2026-10-23); braucht eine Einzeldimension"),
    window_before: int = Query(DEFAULT_WINDOW_BEFORE, ge=0, le=MAX_WINDOW_MONTHS, description="Monate vor dem Beginn des Übergangs (Standard 3)"),
    window_after: int = Query(DEFAULT_WINDOW_AFTER, ge=0, le=MAX_WINDOW_MONTHS, description="Monate nach dem markierten Monat (Standard 1)"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Belege je Seite"),
    offset: int = Query(0, ge=0, description="Erster Beleg der Seite"),
):
    try:
        result = context_for_anchor(
            company_id, anomaly_id, source=source, dimension=dimension, status=status,
            dimension_only=dimension_only, **_window_params(window_before, window_after),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error loading context: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")
    if result.get("anchor") is None:
        raise HTTPException(status_code=404, detail=f"Auffällige Veränderung '{anomaly_id}' nicht gefunden.")
    return paginate(result, offset, limit)


@router.get("/company/{company_id}/context")
def get_selection_context(
    company_id: int,
    from_: str = Query(..., alias="from", description="Erster Monat der Auswahl (YYYY-MM)"),
    to: str = Query(..., description="Letzter Monat der Auswahl (YYYY-MM, einschließlich)"),
    source: Optional[str] = Query(None, description="Quelle der Dimension (Standard employee); nur mit dimension"),
    dimension: Optional[str] = Query(None, description="Einzeldimension für dimension_only (2026-10-23)"),
    dimension_only: bool = Query(False, description="Nur Belege zur Dimension (Schlüsselwort des Themas im Titel oder zugeordnete Ereignisart); braucht dimension"),
    window_before: int = Query(DEFAULT_WINDOW_BEFORE, ge=0, le=MAX_WINDOW_MONTHS, description="Monate vor der Auswahl (Standard 3)"),
    window_after: int = Query(DEFAULT_WINDOW_AFTER, ge=0, le=MAX_WINDOW_MONTHS, description="Monate nach der Auswahl (Standard 1)"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Belege je Seite"),
    offset: int = Query(0, ge=0, description="Erster Beleg der Seite"),
):
    try:
        result = context_for_selection(
            company_id, from_, to, source=source, dimension=dimension, dimension_only=dimension_only,
            **_window_params(window_before, window_after),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error loading context: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")
    return paginate(result, offset, limit)


@router.get("/global-events")
def get_global_events(
    all_events: bool = Query(False, alias="all", description="ohne Wirkung seit E29 (alle Ereignisse gelten als bestätigt)"),
):
    from services import macro_events

    events = load_global_events(confirmed_only=not all_events)
    return {
        "events": events,
        "n_confirmed": sum(1 for e in events if e.get("confirmed") is True),
        "basis": macro_events.status(),
        "note": EVIDENCE_NOTE,
    }
