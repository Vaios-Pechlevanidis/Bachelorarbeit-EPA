from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import user_events_service as svc

router = APIRouter(prefix="/api/companies", tags=["User events"])


class UserEventIn(BaseModel):
    title: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    note: Optional[str] = None


def _client_or_503():
    from database.supabase_client import get_supabase_client

    return get_supabase_client()


def _require_company(client, company_id: int) -> None:
    if not svc.company_exists(client, company_id):
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")


def _handle(fn):
    try:
        return fn()
    except svc.MissingTableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{company_id}/events")
def list_user_events(company_id: int):
    client = _client_or_503()
    _require_company(client, company_id)
    events = _handle(lambda: svc.list_events(client, company_id))
    return {"company_id": company_id, "events": events, "note": svc.USER_EVENT_NOTE}


@router.post("/{company_id}/events", status_code=201)
def create_user_event(company_id: int, body: UserEventIn):
    client = _client_or_503()
    _require_company(client, company_id)
    return _handle(lambda: svc.create_event(client, company_id, body.model_dump()))


@router.put("/{company_id}/events/{event_id}")
def update_user_event(company_id: int, event_id: int, body: UserEventIn):
    client = _client_or_503()
    _require_company(client, company_id)
    updated = _handle(lambda: svc.update_event(client, company_id, event_id, body.model_dump()))
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Ereignis {event_id} nicht gefunden.")
    return updated


@router.delete("/{company_id}/events/{event_id}")
def delete_user_event(company_id: int, event_id: int):
    client = _client_or_503()
    _require_company(client, company_id)
    if not _handle(lambda: svc.delete_event(client, company_id, event_id)):
        raise HTTPException(status_code=404, detail=f"Ereignis {event_id} nicht gefunden.")
    return {"deleted": event_id, "company_id": company_id}
