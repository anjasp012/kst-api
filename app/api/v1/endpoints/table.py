import uuid
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.persona import Persona
from app.models.zone import Zone
from app.models.innovation import Innovation
from app.models.suggestion import ResearchSuggestion
from app.models.telemetry import TelemetryLog
from app.schemas.persona import PersonaResponse
from app.schemas.zone import ZoneResponse
from app.schemas.innovation import (
    InnovationResponse, 
    InnovationExploreCard,
    InnovationExplorePaginatedResponse
)
from app.schemas.suggestion import SuggestionCreate, SuggestionResponse
from app.schemas.stats import TelemetryEventCreate
from app.core.helpers import build_full_url

router = APIRouter()


def _get_explore_cards(
    db: Session,
    persona_id: Optional[uuid.UUID] = None,
    zone_id: Optional[uuid.UUID] = None
) -> List[dict]:
    """Helper internal untuk mengambil & menghitung skor relevansi inovasi"""
    resolved_persona_id = persona_id
    resolved_zone_id = zone_id

    query = db.query(Innovation).options(
        joinedload(Innovation.zone),
        joinedload(Innovation.persona_relevances)
    ).filter(Innovation.is_active == True)

    if resolved_zone_id:
        query = query.filter(Innovation.zone_id == resolved_zone_id)

    innovations = query.limit(50).all()

    cards = []
    for item in innovations:
        relevance_score = 0
        if resolved_persona_id:
            rel = next((r for r in item.persona_relevances if r.persona_id == resolved_persona_id), None)
            if rel:
                relevance_score += rel.relevance_score
            else:
                relevance_score += 10

        cards.append({
            "id": item.id,
            "title": item.title,
            "slug": item.slug,
            "trl": item.trl,
            "short_description": item.short_description,
            "summary": item.summary,
            "impact": item.impact,
            "thumbnail_url": build_full_url(item.thumbnail_url),
            "research_center": item.research_center,
            "implementation_potential": item.implementation_potential,
            "relevant_tags": item.relevant_tags,
            "zone_name": item.zone.name if item.zone else "Umum",
            "research_center_name": item.research_center if item.research_center else "Pusat Riset BRIN",
            "persona_id": item.persona_id,
            "persona_name": item.persona.name if item.persona else "Umum",
            "relevance_score": relevance_score
        })

    # Urutkan berdasarkan relevansi persona tertinggi lalu TRL
    cards.sort(key=lambda x: (x["relevance_score"], x["trl"]), reverse=True)
    return cards


@router.get("/personas", response_model=List[PersonaResponse])
def get_active_personas(db: Session = Depends(get_db)):
    """Mengambil seluruh daftar Modul Pengguna (Persona) yang aktif"""
    return db.query(Persona).filter(Persona.is_active == True).order_by(Persona.created_at.asc()).all()


@router.get("/zones", response_model=List[ZoneResponse])
def get_active_zones(db: Session = Depends(get_db)):
    """Mengambil seluruh daftar Token Tantangan (Zona Riset BRIN) yang aktif"""
    return db.query(Zone).filter(Zone.is_active == True).order_by(Zone.created_at.asc()).all()


@router.get("/explore", response_model=List[InnovationExploreCard])
def explore_innovations(
    persona_id: Optional[uuid.UUID] = None,
    zone_id: Optional[uuid.UUID] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Mengambil inovasi BRIN berdasarkan kombinasi Persona dan Zona.
    """
    cards = _get_explore_cards(
        db=db,
        persona_id=persona_id,
        zone_id=zone_id
    )

    if page is not None and page_size is not None and page >= 1 and page_size >= 1:
        start = (page - 1) * page_size
        end = start + page_size
        return cards[start:end]

    return cards


@router.get("/explore/paginated", response_model=InnovationExplorePaginatedResponse)
def explore_innovations_paginated(
    persona_id: Optional[uuid.UUID] = Query(None, description="ID Persona (Slot 1)"),
    zone_id: Optional[uuid.UUID] = Query(None, description="ID Zona Riset (Slot 2)"),
    page: int = Query(1, ge=1, description="Nomor halaman (mulai 1)"),
    page_size: int = Query(3, ge=1, le=50, description="Jumlah data per halaman (default 3)"),
    db: Session = Depends(get_db)
):
    """
    Mengembalikan `items`, `total`, `page`, `page_size`, dan `total_pages`.
    """
    all_cards = _get_explore_cards(
        db=db,
        persona_id=persona_id,
        zone_id=zone_id
    )

    total = len(all_cards)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size
    items = all_cards[start:end]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/innovations/{identifier}", response_model=InnovationResponse)
def get_innovation_detail(identifier: str, db: Session = Depends(get_db)):
    """
    Mengambil detail inovasi spesifik berdasarkan UUID atau slug.
    """
    query = db.query(Innovation).options(
        joinedload(Innovation.zone),
        joinedload(Innovation.persona)
    )
    try:
        uuid_obj = uuid.UUID(identifier)
        innovation = query.filter(Innovation.id == uuid_obj).first()
    except ValueError:
        innovation = query.filter(Innovation.slug == identifier).first()

    if not innovation:
        raise HTTPException(status_code=404, detail="Inovasi tidak ditemukan")
    return innovation


@router.post("/suggestions", response_model=SuggestionResponse, status_code=status.HTTP_201_CREATED)
def submit_research_suggestion(payload: SuggestionCreate, db: Session = Depends(get_db)):
    """
    Pengunjung mengirim usulan riset baru.
    """
    if not payload.topic_wanted or len(payload.topic_wanted.strip()) == 0:
        raise HTTPException(status_code=422, detail="Topik yang dicari wajib diisi")

    suggestion = ResearchSuggestion(
        visitor_name=payload.visitor_name,
        age_range=payload.age_range,
        topic_wanted=payload.topic_wanted.strip(),
        feedback=payload.feedback.strip() if payload.feedback else None,
        persona_id=payload.persona_id,
        zone_id=payload.zone_id,
        screen_context=payload.screen_context or "Explore",
        status="NEW"
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)

    return {
        "id": suggestion.id,
        "visitor_name": suggestion.visitor_name,
        "age_range": suggestion.age_range,
        "topic_wanted": suggestion.topic_wanted,
        "feedback": suggestion.feedback,
        "persona_id": suggestion.persona_id,
        "persona_name": suggestion.persona.name if suggestion.persona else None,
        "zone_id": suggestion.zone_id,
        "zone_name": suggestion.zone.name if suggestion.zone else None,
        "screen_context": suggestion.screen_context,
        "status": suggestion.status,
        "admin_notes": suggestion.admin_notes,
        "created_at": suggestion.created_at,
        "updated_at": suggestion.created_at
    }


@router.post("/telemetry", status_code=status.HTTP_201_CREATED)
def log_telemetry_event(payload: TelemetryEventCreate, db: Session = Depends(get_db)):
    """Pencatatan log interaksi layar sentuh"""
    desc = payload.description or payload.keterangan
    log_entry = TelemetryLog(
        event_type=payload.event_type,
        persona_id=payload.persona_id,
        zone_id=payload.zone_id,
        innovation_id=payload.innovation_id,
        description=desc,
        metadata_payload=payload.metadata_payload or {}
    )
    db.add(log_entry)
    db.commit()
    return {"status": "success", "event": payload.event_type}
