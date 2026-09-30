"""
api/index.py
=============================================================================
Vercel Serverless Function Entry Point for THERMOSHELTER API
FastAPI Microservice for ANSYS & Enterprise FEA Validation Bridge
=============================================================================
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import io

# Setup sys.path for Vercel serverless environment
_current_dir = Path(__file__).resolve().parent
_root_dir = _current_dir.parent

for _p in [_root_dir, _current_dir, _root_dir / "backend"]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fastapi import FastAPI, APIRouter, Query, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse, FileResponse, HTMLResponse

# Resilient import of AnsysExportService
try:
    from backend.services.ansys_export_service import AnsysExportService
except ImportError:
    try:
        from ansys_export_service import AnsysExportService
    except ImportError:
        AnsysExportService = None

# Top-level FastAPI instance required by Vercel's Python runtime
app = FastAPI(
    title="THERMOSHELTER ANSYS & Enterprise Validation Bridge",
    description="Institutional FEA/CFD Data Export Engine for High-Altitude Passive Shelters",
    version="0.8.0-RELEASE"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Static Frontend Serving (Fallback for when Vercel routes / to Serverless Function)
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def serve_root():
    for candidate in [_root_dir / "index.html", _current_dir.parent / "index.html", Path("index.html")]:
        if candidate.exists():
            return FileResponse(candidate, media_type="text/html")
    return HTMLResponse("<h1>THERMOSHELTER Digital Twin</h1><p>Application is loading...</p>")

@app.get("/index.html", response_class=HTMLResponse)
def serve_index_file():
    return serve_root()

@app.get("/style.css")
def serve_style_css():
    for candidate in [_root_dir / "style.css", _current_dir.parent / "style.css", Path("style.css")]:
        if candidate.exists():
            return FileResponse(candidate, media_type="text/css")
    raise HTTPException(status_code=404, detail="style.css not found")

@app.get("/script.js")
def serve_script_js():
    for candidate in [_root_dir / "script.js", _current_dir.parent / "script.js", Path("script.js")]:
        if candidate.exists():
            return FileResponse(candidate, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="script.js not found")

@app.get("/assets/{filepath:path}")
def serve_asset_file(filepath: str):
    for base in [_root_dir / "assets", _current_dir.parent / "assets", Path("assets")]:
        target = base / filepath
        if target.exists() and target.is_file():
            ext = target.suffix.lower()
            mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else ("image/png" if ext == ".png" else "application/octet-stream")
            return FileResponse(target, media_type=mime)
    raise HTTPException(status_code=404, detail=f"Asset {filepath} not found")

@app.get("/{filename:path}.jpg")
@app.get("/{filename:path}.jpeg")
@app.get("/{filename:path}.png")
def serve_image_file(filename: str):
    clean = filename.split("/")[-1]
    for ext in [".jpg", ".jpeg", ".png"]:
        for base in [_root_dir, _root_dir / "assets", _current_dir.parent, Path(".")]:
            img = base / f"{clean}{ext}"
            if img.exists() and img.is_file():
                mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
                return FileResponse(img, media_type=mime)
    raise HTTPException(status_code=404, detail="Image not found")

# -----------------------------------------------------------------------------
# API Router for ANSYS & Validation Microservices
# -----------------------------------------------------------------------------
router = APIRouter()

@router.get("/")
@router.get("/status")
def status_root():
    kernel = getattr(AnsysExportService, "DEFAULT_KERNEL", "FEM-4D v4.2.8 // ANSYS-BRIDGE-v0.8")
    return {
        "platform": "THERMOSHELTER",
        "module": "ANSYS & Enterprise Validation Bridge",
        "kernel": kernel,
        "status": "OPERATIONAL",
        "environment": "Vercel Serverless Function",
        "compliance": ["ISO 13790", "ISO 6946", "NBC 2016 Part 8"]
    }

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "thermoshelter-ansys-api",
        "version": "0.8.0-RELEASE",
        "ansys_service_loaded": AnsysExportService is not None
    }

@router.get("/ansys/payload")
def get_full_payload(altitude: float = Query(3500.0, description="Altitude MSL in meters"), sim_id: str = Query("TS-LAD-2026-0042")):
    if AnsysExportService is None:
        raise HTTPException(status_code=500, detail="AnsysExportService is not available.")
    payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude, "simulation_id": sim_id})
    return payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()

@router.get("/ansys/export/json")
def export_json_file(altitude: float = Query(3500.0), sim_id: str = Query("TS-LAD-2026-0042")):
    if AnsysExportService is None:
        raise HTTPException(status_code=500, detail="AnsysExportService is not available.")
    payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude, "simulation_id": sim_id})
    content = AnsysExportService.export_json(payload)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={sim_id}_ANSYS_Payload.json"}
    )

@router.get("/ansys/export/fluent-dat")
def export_fluent_dat_file(altitude: float = Query(3500.0), sim_id: str = Query("TS-LAD-2026-0042")):
    if AnsysExportService is None:
        raise HTTPException(status_code=500, detail="AnsysExportService is not available.")
    payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude, "simulation_id": sim_id})
    content = AnsysExportService.export_fluent_dat(payload)
    return PlainTextResponse(
        content=content,
        headers={"Content-Disposition": f"attachment; filename={sim_id}_Fluent_BC.dat"}
    )

@router.get("/ansys/export/transient-csv")
def export_csv_file(altitude: float = Query(3500.0), sim_id: str = Query("TS-LAD-2026-0042")):
    if AnsysExportService is None:
        raise HTTPException(status_code=500, detail="AnsysExportService is not available.")
    payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude, "simulation_id": sim_id})
    content = AnsysExportService.export_transient_csv(payload)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={sim_id}_Transient_Loads.csv"}
    )

@router.get("/ansys/export/zip")
def export_zip_bundle(altitude: float = Query(3500.0), sim_id: str = Query("TS-LAD-2026-0042")):
    if AnsysExportService is None:
        raise HTTPException(status_code=500, detail="AnsysExportService is not available.")
    payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude, "simulation_id": sim_id})
    zip_bytes = AnsysExportService.export_zip_archive(payload)
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={sim_id}_ANSYS_Validation_Package.zip"}
    )

@router.get("/ansys/validate")
def run_preflight_validation(altitude: float = Query(3500.0)):
    if AnsysExportService is None:
        raise HTTPException(status_code=500, detail="AnsysExportService is not available.")
    payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude})
    audit = payload.validation_audit
    return audit.model_dump() if hasattr(audit, "model_dump") else audit.dict()

# Mount API endpoints under '/api'
app.include_router(router, prefix="/api")

# Also support direct '/ansys/...' routes without shadowing '/'
ansys_direct_router = APIRouter(prefix="/ansys")
ansys_direct_router.add_api_route("/payload", get_full_payload, methods=["GET"])
ansys_direct_router.add_api_route("/export/json", export_json_file, methods=["GET"])
ansys_direct_router.add_api_route("/export/fluent-dat", export_fluent_dat_file, methods=["GET"])
ansys_direct_router.add_api_route("/export/transient-csv", export_csv_file, methods=["GET"])
ansys_direct_router.add_api_route("/export/zip", export_zip_bundle, methods=["GET"])
ansys_direct_router.add_api_route("/validate", run_preflight_validation, methods=["GET"])
app.include_router(ansys_direct_router)

