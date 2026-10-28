from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.context_service import company_finance, company_market
from services.news_service import company_news

router = APIRouter(prefix="/api/analytics", tags=["Market"])


@router.get("/company/{company_id}/market")
def get_company_market(
    company_id: int,
    start: Optional[str] = Query(None, description="Erster Monat (YYYY-MM, einschließlich)"),
    end: Optional[str] = Query(None, description="Letzter Monat (YYYY-MM, einschließlich)"),
):
    try:
        result = company_market(company_id, start=start, end=end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading market data: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")
    return result


@router.get("/company/{company_id}/finance")
def get_company_finance(company_id: int):
    try:
        result = company_finance(company_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading finance data: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")
    return result


@router.get("/company/{company_id}/news")
def get_company_news(company_id: int):
    try:
        result = company_news(company_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading news: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")
    return result
