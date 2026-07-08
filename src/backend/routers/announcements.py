"""
Announcement management endpoints for the High School Management System API
"""

from datetime import date
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    message: str
    expiration_date: str
    start_date: Optional[str] = None


def _to_public(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id")),
        "message": doc.get("message", ""),
        "start_date": doc.get("start_date"),
        "expiration_date": doc.get("expiration_date", ""),
        "created_by": doc.get("created_by", "")
    }


def _validate_dates(start_date: Optional[str], expiration_date: str) -> None:
    try:
        expires = date.fromisoformat(expiration_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Expiration date must be in YYYY-MM-DD format"
        ) from exc

    start = None
    if start_date:
        try:
            start = date.fromisoformat(start_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Start date must be in YYYY-MM-DD format"
            ) from exc

    if start and start > expires:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after expiration date"
        )


def _require_authenticated_teacher(teacher_username: Optional[str]) -> Dict[str, Any]:
    if not teacher_username:
        raise HTTPException(
            status_code=401,
            detail="Authentication required for this action"
        )

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401,
            detail="Invalid teacher credentials"
        )

    return teacher


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get active announcements for public display."""
    today = date.today().isoformat()
    query = {
        "expiration_date": {"$gte": today},
        "$or": [
            {"start_date": None},
            {"start_date": ""},
            {"start_date": {"$lte": today}}
        ]
    }

    announcements = announcements_collection.find(query).sort("expiration_date", 1)
    return [_to_public(doc) for doc in announcements]


@router.get("/manage", response_model=List[Dict[str, Any]])
def list_announcements_for_management(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """List all announcements for authenticated users managing content."""
    _require_authenticated_teacher(teacher_username)

    announcements = announcements_collection.find().sort("expiration_date", 1)
    return [_to_public(doc) for doc in announcements]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(payload: AnnouncementPayload, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new announcement (authenticated users only)."""
    teacher = _require_authenticated_teacher(teacher_username)

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    _validate_dates(payload.start_date, payload.expiration_date)

    insert_doc = {
        "message": message,
        "start_date": payload.start_date or None,
        "expiration_date": payload.expiration_date,
        "created_by": teacher["_id"]
    }

    result = announcements_collection.insert_one(insert_doc)
    created = announcements_collection.find_one({"_id": result.inserted_id})
    return _to_public(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement (authenticated users only)."""
    _require_authenticated_teacher(teacher_username)

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    _validate_dates(payload.start_date, payload.expiration_date)

    query: Dict[str, Any] = {"_id": announcement_id}
    if ObjectId.is_valid(announcement_id):
        query = {"$or": [{"_id": announcement_id}, {"_id": ObjectId(announcement_id)}]}

    existing = announcements_collection.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")

    update_result = announcements_collection.update_one(
        {"_id": existing["_id"]},
        {
            "$set": {
                "message": message,
                "start_date": payload.start_date or None,
                "expiration_date": payload.expiration_date
            }
        }
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update announcement")

    updated = announcements_collection.find_one({"_id": existing["_id"]})
    return _to_public(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, str]:
    """Delete an announcement (authenticated users only)."""
    _require_authenticated_teacher(teacher_username)

    query: Dict[str, Any] = {"_id": announcement_id}
    if ObjectId.is_valid(announcement_id):
        query = {"$or": [{"_id": announcement_id}, {"_id": ObjectId(announcement_id)}]}

    existing = announcements_collection.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")

    delete_result = announcements_collection.delete_one({"_id": existing["_id"]})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete announcement")

    return {"message": "Announcement deleted"}
