import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from app.db.session import get_db
from app.models.user import User
from app.models.persona import Persona
from app.models.zone import Zone
from app.models.innovation import Innovation
from app.models.relevance import InnovationPersonaRelevance
from app.models.suggestion import ResearchSuggestion
from app.models.telemetry import TelemetryLog
from app.schemas.persona import PersonaCreate, PersonaUpdate, PersonaResponse
from app.schemas.zone import ZoneCreate, ZoneUpdate, ZoneResponse
from app.schemas.innovation import InnovationCreate, InnovationUpdate, InnovationResponse, RelevanceMappingItem
from app.schemas.suggestion import SuggestionResponse, SuggestionStatusUpdate
from app.schemas.admin import BulkStatusUpdate, BulkDeleteRequest, DashboardAnalyticsResponse
from app.api.v1.deps import get_current_admin
from app.core.helpers import build_full_url
from app.core.config import UPLOADS_DIR

router = APIRouter()


# =========================================================================
# 📊 1. HISTORI PEMAKAIAN MODUL (BERAPA KALI DIPAKAI & STATISTIK KOMBINASI)
# =========================================================================

@router.get("/module-usage")
def get_module_usage_history(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    Mengambil histori & statistik berapa kali setiap Modul Pengguna (Slot 1) 
    dan Token Tantangan (Slot 2) digunakan di meja sentuh.
    """
    personas = db.query(Persona).order_by(Persona.created_at.asc()).all()
    zones = db.query(Zone).order_by(Zone.created_at.asc()).all()

    # Hitung pemakaian persona dari telemetry & usulan
    persona_stats = []
    for p in personas:
        t_count = db.query(func.count(TelemetryLog.id)).filter(TelemetryLog.persona_id == p.id).scalar() or 0
        s_count = db.query(func.count(ResearchSuggestion.id)).filter(ResearchSuggestion.persona_id == p.id).scalar() or 0
        total_usage = t_count + s_count
        persona_stats.append({
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "tagline": p.tagline,
            "icon_url": build_full_url(p.icon_url),
            "is_active": p.is_active,
            "usage_count": total_usage,
            "suggestion_count": s_count
        })

    # Hitung pemakaian zona dari telemetry & usulan
    zone_stats = []
    for z in zones:
        t_count = db.query(func.count(TelemetryLog.id)).filter(TelemetryLog.zone_id == z.id).scalar() or 0
        s_count = db.query(func.count(ResearchSuggestion.id)).filter(ResearchSuggestion.zone_id == z.id).scalar() or 0
        total_usage = t_count + s_count
        zone_stats.append({
            "id": z.id,
            "name": z.name,
            "slug": z.slug,
            "description": z.description,
            "icon_url": build_full_url(z.icon_url),
            "is_active": z.is_active,
            "usage_count": total_usage,
            "suggestion_count": s_count
        })

    # Kombinasi paling sering dimainkan (Persona + Zona)
    comb_suggestions = (
        db.query(Persona.name, Zone.name, func.count(ResearchSuggestion.id))
        .join(Persona, ResearchSuggestion.persona_id == Persona.id)
        .join(Zone, ResearchSuggestion.zone_id == Zone.id)
        .group_by(Persona.name, Zone.name)
        .order_by(func.count(ResearchSuggestion.id).desc())
        .limit(10)
        .all()
    )
    top_combinations = [
        {"persona": row[0], "zone": row[1], "count": row[2]}
        for row in comb_suggestions
    ]

    # Log aktivitas interaksi terbaru
    recent_logs = (
        db.query(TelemetryLog)
        .options(
            joinedload(TelemetryLog.persona),
            joinedload(TelemetryLog.zone),
            joinedload(TelemetryLog.innovation)
        )
        .order_by(TelemetryLog.created_at.desc())
        .limit(25)
        .all()
    )

    total_sessions = db.query(func.count(TelemetryLog.id)).scalar() or 0
    total_suggestions = db.query(func.count(ResearchSuggestion.id)).scalar() or 0

    return {
        "summary": {
            "total_persona_types": len(personas),
            "total_zone_types": len(zones),
            "total_interactive_plays": total_sessions + total_suggestions,
            "total_suggestions_submitted": total_suggestions
        },
        "persona_stats": sorted(persona_stats, key=lambda x: x["usage_count"], reverse=True),
        "zone_stats": sorted(zone_stats, key=lambda x: x["usage_count"], reverse=True),
        "top_combinations": top_combinations,
        "recent_logs": [
            {
                "id": log.id,
                "event": log.event_type,
                "persona_id": log.persona_id,
                "persona": log.persona.name if log.persona else "-",
                "zone_id": log.zone_id,
                "zone": log.zone.name if log.zone else "-",
                "innovation_id": log.innovation_id,
                "innovation_title": log.innovation.title if log.innovation else None,
                "description": log.description,
                "keterangan": log.description,
                "created_at": log.created_at
            }
            for log in recent_logs
        ]
    }


# =========================================================================
# 👥 2. CRUD MASTER MODUL PENGGUNA (PERSONA) & TOKEN TANTANGAN (ZONA)
# =========================================================================

# --- PERSONA CRUD ---
@router.get("/personas", response_model=List[PersonaResponse])
def get_all_personas(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(Persona).order_by(Persona.created_at.asc()).all()


@router.post("/personas", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
def create_persona(payload: PersonaCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    existing = db.query(Persona).filter(Persona.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug persona sudah digunakan")
    
    persona = Persona(**payload.model_dump())
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


@router.put("/personas/{id}", response_model=PersonaResponse)
def update_persona(id: uuid.UUID, payload: PersonaUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    persona = db.query(Persona).filter(Persona.id == id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona tidak ditemukan")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(persona, key, val)
    db.commit()
    db.refresh(persona)
    return persona


@router.delete("/personas/{id}")
def delete_persona(id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    persona = db.query(Persona).filter(Persona.id == id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona tidak ditemukan")
    try:
        name = persona.name
        db.delete(persona)
        db.commit()
        return {"message": f"Persona '{name}' berhasil dihapus"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menghapus persona: {str(e)}")


# --- ZONE CRUD ---
@router.get("/zones", response_model=List[ZoneResponse])
def get_all_zones(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.query(Zone).order_by(Zone.created_at.asc()).all()


@router.post("/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    existing = db.query(Zone).filter(Zone.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug zona sudah digunakan")
    
    zone = Zone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.put("/zones/{id}", response_model=ZoneResponse)
def update_zone(id: uuid.UUID, payload: ZoneUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    zone = db.query(Zone).filter(Zone.id == id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zona tidak ditemukan")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(zone, key, val)
    db.commit()
    db.refresh(zone)
    return zone


@router.delete("/zones/{id}")
def delete_zone(id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    zone = db.query(Zone).filter(Zone.id == id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zona tidak ditemukan")
    try:
        name = zone.name
        db.delete(zone)
        db.commit()
        return {"message": f"Zona '{name}' berhasil dihapus"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menghapus zona: {str(e)}")


# =========================================================================
# 📬 3. MODERASI USULAN RISET PENGUNJUNG
# =========================================================================

@router.get("/suggestions", response_model=List[SuggestionResponse])
def get_all_suggestions(
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    query = db.query(ResearchSuggestion).options(
        joinedload(ResearchSuggestion.persona),
        joinedload(ResearchSuggestion.zone)
    )
    if status and status != 'ALL':
        query = query.filter(ResearchSuggestion.status == status.upper())
    
    rows = query.order_by(ResearchSuggestion.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": r.id,
            "visitor_name": r.visitor_name,
            "age_range": r.age_range,
            "topic_wanted": r.topic_wanted,
            "feedback": r.feedback,
            "persona_id": r.persona_id,
            "persona_name": r.persona.name if r.persona else None,
            "zone_id": r.zone_id,
            "zone_name": r.zone.name if r.zone else None,
            "screen_context": r.screen_context,
            "status": r.status,
            "admin_notes": r.admin_notes,
            "created_at": r.created_at,
            "updated_at": r.created_at
        }
        for r in rows
    ]


@router.patch("/suggestions/{suggestion_id}/status", response_model=SuggestionResponse)
def update_suggestion_status(
    suggestion_id: uuid.UUID,
    payload: SuggestionStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    suggestion = db.query(ResearchSuggestion).options(
        joinedload(ResearchSuggestion.persona),
        joinedload(ResearchSuggestion.zone)
    ).filter(ResearchSuggestion.id == suggestion_id).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Usulan tidak ditemukan")

    suggestion.status = payload.status.upper()
    if payload.admin_notes is not None:
        suggestion.admin_notes = payload.admin_notes

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


@router.post("/suggestions/bulk-status")
def bulk_update_suggestion_status(
    payload: BulkStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    if not payload.ids:
        raise HTTPException(status_code=422, detail="Daftar ID tidak boleh kosong")

    updated_count = db.query(ResearchSuggestion).filter(ResearchSuggestion.id.in_(payload.ids)).update(
        {ResearchSuggestion.status: payload.status.upper()}, synchronize_session=False
    )
    db.commit()
    return {"message": f"{updated_count} usulan berhasil diperbarui", "updated_count": updated_count}


@router.delete("/suggestions/{suggestion_id}")
def delete_suggestion(suggestion_id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    suggestion = db.query(ResearchSuggestion).filter(ResearchSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    try:
        db.delete(suggestion)
        db.commit()
        return {"message": "Usulan berhasil dihapus"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menghapus usulan: {str(e)}")


@router.post("/suggestions/bulk-delete")
def bulk_delete_suggestions(payload: BulkDeleteRequest, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    if not payload.ids:
        raise HTTPException(status_code=422, detail="Daftar ID tidak boleh kosong")

    try:
        deleted_count = db.query(ResearchSuggestion).filter(ResearchSuggestion.id.in_(payload.ids)).delete(synchronize_session=False)
        db.commit()
        return {"message": f"{deleted_count} data usulan berhasil dihapus", "deleted_count": deleted_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menghapus usulan terpilih: {str(e)}")


# =========================================================================
# 💡 4. INOVASI CRUD (PENDUKUNG KATALOG)
# =========================================================================

@router.get("/innovations", response_model=List[InnovationResponse])
def list_innovations(
    zone_id: Optional[uuid.UUID] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    query = db.query(Innovation).options(joinedload(Innovation.zone), joinedload(Innovation.persona))
    if zone_id:
        query = query.filter(Innovation.zone_id == zone_id)
    return query.order_by(Innovation.created_at.asc()).offset(offset).limit(limit).all()


@router.post("/innovations", response_model=InnovationResponse, status_code=status.HTTP_201_CREATED)
def create_innovation(payload: InnovationCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    inno = Innovation(**payload.model_dump())
    db.add(inno)
    db.commit()
    db.refresh(inno)
    return inno


@router.put("/innovations/{id}", response_model=InnovationResponse)
def update_innovation(id: uuid.UUID, payload: InnovationUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    inno = db.query(Innovation).filter(Innovation.id == id).first()
    if not inno:
        raise HTTPException(status_code=404, detail="Inovasi tidak ditemukan")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(inno, key, val)
    db.commit()
    db.refresh(inno)
    return inno


@router.delete("/innovations/{id}")
def delete_innovation(id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    inno = db.query(Innovation).filter(Innovation.id == id).first()
    if not inno:
        raise HTTPException(status_code=404, detail="Inovasi tidak ditemukan")
    db.delete(inno)
    db.commit()
    return {"message": "Inovasi berhasil dihapus"}


# =========================================================================
# ⚙️ 5. RINGKASAN ANALITIK & PENGATURAN
# =========================================================================

@router.get("/analytics", response_model=DashboardAnalyticsResponse)
def get_analytics(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    total_inno = db.query(func.count(Innovation.id)).scalar() or 0
    total_personas = db.query(func.count(Persona.id)).scalar() or 0
    total_zones = db.query(func.count(Zone.id)).scalar() or 0
    total_sugg = db.query(func.count(ResearchSuggestion.id)).scalar() or 0
    new_sugg = db.query(func.count(ResearchSuggestion.id)).filter(ResearchSuggestion.status == "NEW").scalar() or 0
    rev_sugg = db.query(func.count(ResearchSuggestion.id)).filter(ResearchSuggestion.status == "REVIEWED").scalar() or 0

    trl_res = db.query(Innovation.trl, func.count(Innovation.id)).group_by(Innovation.trl).all()
    trl_dist = {f"TRL {row[0]}": row[1] for row in trl_res}

    tz_res = (
        db.query(Zone.name, func.count(ResearchSuggestion.id))
        .join(ResearchSuggestion, Zone.id == ResearchSuggestion.zone_id, isouter=True)
        .group_by(Zone.id, Zone.name)
        .order_by(func.count(ResearchSuggestion.id).desc())
        .limit(5)
        .all()
    )
    top_zones = [{"zone": r[0], "count": r[1]} for r in tz_res]

    tp_res = (
        db.query(Persona.name, func.count(ResearchSuggestion.id))
        .join(ResearchSuggestion, Persona.id == ResearchSuggestion.persona_id, isouter=True)
        .group_by(Persona.id, Persona.name)
        .order_by(func.count(ResearchSuggestion.id).desc())
        .limit(5)
        .all()
    )
    top_personas = [{"persona": r[0], "count": r[1]} for r in tp_res]

    return {
        "total_innovations": total_inno,
        "total_personas": total_personas,
        "total_zones": total_zones,
        "total_suggestions": total_sugg,
        "new_suggestions": new_sugg,
        "reviewed_suggestions": rev_sugg,
        "top_zones": top_zones,
        "top_personas": top_personas,
        "trl_distribution": trl_dist
    }



# =========================================================================
# 📁 6. FILE UPLOAD (ICONS, THUMBNAILS, MEDIA)
# =========================================================================

@router.post("/upload")
def upload_file(file: UploadFile = File(...), admin: User = Depends(get_current_admin)):
    """
    Endpoint untuk mengunggah file gambar (thumbnail, icon) ke server.
    Akan mengembalikan URL publik yang bisa diakses via browser atau Unity.
    """
    if not file.filename:
        raise HTTPException(status_code=422, detail="Tidak ada file yang dipilih")
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    file_path = os.path.join(UPLOADS_DIR, unique_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    full_url = build_full_url(f"/uploads/{unique_filename}")
    relative_url = f"/uploads/{unique_filename}"
    
    return {
        "message": "File berhasil diunggah", 
        "url": full_url,
        "relative_url": relative_url,
        "filename": unique_filename
    }
