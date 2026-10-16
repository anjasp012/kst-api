import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, UPLOADS_DIR
from app.db.session import engine, Base
from app.api.v1.router import api_router

# Migrasi dan seed dijalankan secara manual via script (python -m app.db.auto_migrate / python -m app.seed.seed_data)

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
from starlette.requests import Request
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    import traceback
    traceback.print_exc()
    err_str = str(exc.orig) if hasattr(exc, "orig") and exc.orig else str(exc)
    low_err = err_str.lower()
    
    if "foreign key" in low_err or "is still referenced" in low_err or "foreignkeyviolation" in low_err:
        msg = "Data ini tidak dapat dihapus karena masih digunakan atau terhubung dengan data lain di sistem (misal data lokasi kawasan). Silakan ubah atau hapus data terkait terlebih dahulu."
    elif "unique" in low_err or "duplicate key" in low_err or "uniqueviolation" in low_err:
        msg = "Data dengan nama atau identitas tersebut sudah terdaftar di sistem. Silakan gunakan nama atau identitas yang berbeda."
    else:
        msg = "Operasi data tidak dapat diproses karena terdapat konflik relasi data di sistem."

    response = JSONResponse(
        status_code=400,
        content={"detail": msg},
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    response = JSONResponse(
        status_code=500,
        content={"detail": "Terjadi kendala pada sistem server saat memproses data. Silakan coba beberapa saat lagi atau hubungi administrator."},
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "api_v1": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
