from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.changepoint_detector import DEFAULT_PENALTY_FACTOR
from services.anomaly_service import DEFAULT_MIN_DELTA, company_anomalies, company_anomalies_all
from services.explanation_service import DEFAULT_WINDOW_MONTHS, compare_period, explain_anomaly
from services.rating_series_service import OVERALL_DIMENSION

router = APIRouter(prefix="/api/analytics", tags=["Anomalies"])


@router.get("/company/{company_id}/anomalies")
def get_company_anomalies(
    company_id: int,
    source: str = Query("employee", description="Quelle: employee oder candidates"),
    dimension: str = Query(OVERALL_DIMENSION, description="Dimension aus DIMENSIONS_BY_SOURCE oder 'all'"),
    penalty: Optional[float] = Query(None, gt=0, description="Fester PELT-Strafterm in quadrierten Sternen; schaltet auf den festen Modus"),
    penalty_factor: Optional[float] = Query(None, gt=0, description=f"Faktor des skalierten Strafterms Faktor · sigma² · ln(n) (Standard {DEFAULT_PENALTY_FACTOR})"),
    min_delta: Optional[float] = Query(None, ge=0, description=f"Mindestbetrag der Veränderung in Sternen (Standard {DEFAULT_MIN_DELTA})"),
    status: Optional[str] = Query(None, description="Statusschlüssel der Bewertendengruppe (E13); ohne = alle"),
):
    penalty_factor = DEFAULT_PENALTY_FACTOR if penalty_factor is None else penalty_factor
    min_delta = DEFAULT_MIN_DELTA if min_delta is None else min_delta
    try:
        if dimension == "all":
            return company_anomalies_all(
                company_id, source=source, penalty=penalty, min_delta=min_delta, penalty_factor=penalty_factor,
                status=status,
            )
        return company_anomalies(
            company_id,
            source=source,
            dimension=dimension,
            penalty=penalty,
            min_delta=min_delta,
            penalty_factor=penalty_factor,
            status=status,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


@router.get("/company/{company_id}/anomalies/{anomaly_id}/explanations")
def get_anomaly_explanations(
    company_id: int,
    anomaly_id: str,
    source: Optional[str] = Query(None, description="Quelle; Standard aus anomaly_id"),
    dimension: Optional[str] = Query(None, description="Dimension; Standard aus anomaly_id"),
    status: Optional[str] = Query(None, description="Statusschlüssel der Bewertendengruppe (E13); ohne = alle"),
    window_months: int = Query(DEFAULT_WINDOW_MONTHS, ge=1, le=36, description=f"Monate je Vergleichsfenster (Standard {DEFAULT_WINDOW_MONTHS}, E12)"),
):
    try:
        result = explain_anomaly(
            company_id, anomaly_id, source=source, dimension=dimension, status=status, window_months=window_months,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing periods: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Auffällige Veränderung '{anomaly_id}' nicht gefunden.")
    return result


@router.get("/company/{company_id}/compare")
def get_period_comparison(
    company_id: int,
    from_: str = Query(..., alias="from", description="Erster Monat der Auswahl (YYYY-MM)"),
    to: str = Query(..., description="Letzter Monat der Auswahl (YYYY-MM, einschließlich)"),
    source: str = Query("employee", description="Quelle: employee oder candidates"),
    dimension: Optional[str] = Query(None, description="Dimension; Standard Gesamtbewertung"),
    status: Optional[str] = Query(None, description="Statusschlüssel der Bewertendengruppe (E13); ohne = alle"),
):
    try:
        return compare_period(company_id, from_, to, source=source, dimension=dimension, status=status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing periods: {str(e)}")
