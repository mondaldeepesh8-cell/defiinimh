"""
backend/main.py
=============================================================================
FastAPI Microservice for THERMOSHELTER ANSYS & Enterprise Validation Bridge
Direct API integration for institutional FEA pipelines, CAD scripts & solvers.
=============================================================================
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from fastapi import FastAPI, Query, Response, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import PlainTextResponse, StreamingResponse, FileResponse, HTMLResponse
    import io
except ImportError:
    FastAPI = None

try:
    from backend.services.ansys_export_service import AnsysExportService
except ImportError:
    try:
        from ansys_export_service import AnsysExportService
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).resolve().parent))
        from ansys_export_service import AnsysExportService

if FastAPI is not None:
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

    @app.get("/", response_class=HTMLResponse)
    def root():
        root_dir = Path(__file__).resolve().parent.parent
        index_file = root_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file, media_type="text/html")
        return HTMLResponse("<h1>THERMOSHELTER</h1>")

    @app.get("/api")
    @app.get("/api/status")
    def api_status():
        return {
            "platform": "THERMOSHELTER",
            "module": "ANSYS & Enterprise Validation Bridge",
            "kernel": AnsysExportService.DEFAULT_KERNEL,
            "status": "OPERATIONAL",
            "compliance": ["ISO 13790", "ISO 6946", "NBC 2016 Part 8"]
        }

    @app.get("/api/ansys/payload")
    def get_full_payload(altitude: float = Query(3500.0, description="Altitude MSL in meters"), sim_id: str = Query("TS-LAD-2026-0042")):
        payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude, "simulation_id": sim_id})
        return payload.dict() if hasattr(payload, "dict") else payload.model_dump()

    @app.get("/api/ansys/export/json")
    def export_json_file(altitude: float = Query(3500.0), sim_id: str = Query("TS-LAD-2026-0042")):
        payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude, "simulation_id": sim_id})
        content = AnsysExportService.export_json(payload)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={sim_id}_ANSYS_Payload.json"}
        )

    @app.get("/api/ansys/export/fluent-dat")
    def export_fluent_dat_file(altitude: float = Query(3500.0), sim_id: str = Query("TS-LAD-2026-0042")):
        payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude, "simulation_id": sim_id})
        content = AnsysExportService.export_fluent_dat(payload)
        return PlainTextResponse(
            content=content,
            headers={"Content-Disposition": f"attachment; filename={sim_id}_Fluent_BC.dat"}
        )

    @app.get("/api/ansys/export/transient-csv")
    def export_csv_file(altitude: float = Query(3500.0), sim_id: str = Query("TS-LAD-2026-0042")):
        payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude, "simulation_id": sim_id})
        content = AnsysExportService.export_transient_csv(payload)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={sim_id}_Transient_Loads.csv"}
        )

    @app.get("/api/ansys/export/zip")
    def export_zip_bundle(altitude: float = Query(3500.0), sim_id: str = Query("TS-LAD-2026-0042")):
        payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude, "simulation_id": sim_id})
        zip_bytes = AnsysExportService.export_zip_archive(payload)
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={sim_id}_ANSYS_Validation_Package.zip"}
        )

    @app.get("/api/ansys/validate")
    def run_preflight_validation(altitude: float = Query(3500.0)):
        payload = AnsysExportService.build_simulation_payload({"altitude_m": altitude})
        audit = payload.validation_audit
        return audit.dict() if hasattr(audit, "dict") else audit.model_dump()
else:
    app = None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
