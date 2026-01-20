import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

# Import your existing main runner function
# main(ticker, output_format) returns exit code
from app.main import main as run_one

app = FastAPI(title="Investor Operating System Agent")

class RunRequest(BaseModel):
    tickers: List[str]
    output_format: str = "sheets"
    allow_append: bool = False
    dry_run: bool = False

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/run")
def run(req: RunRequest):
    # Wire allow_append/dry_run later in your writers/config if desired
    results = []
    updated = 0

    for t in req.tickers:
        t = t.upper().strip()
        sheet_ok = True
        gcs_ok = True
        try:
            outcome = run_one(t, req.output_format)
        except Exception as e:
            outcome = {"exit_code": 1, "artifact_uri": None, "errors": [str(e)]}
            sheet_ok = False

        base_code = outcome.get("exit_code", 1)
        errors = outcome.get("errors", []) or []

        if base_code != 0:
            sheet_ok = False
        elif req.output_format == "sheets":
            sheet_ok = True

        gcs_requested = False
        artifact_uri = outcome.get("artifact_uri")
        if isinstance(artifact_uri, str) and artifact_uri.startswith("gs://"):
            gcs_requested = True
        if any("GCS" in err or "gs://" in err for err in errors):
            gcs_requested = True
            gcs_ok = False

        if not gcs_requested:
            gcs_ok = True

        code = 0 if (sheet_ok and gcs_ok) else 1
        results.append({
            "ticker": t,
            "exit_code": code,
            "artifact_uri": artifact_uri,
            "error_message": errors[0] if errors else ""
        })
        if sheet_ok:
            updated += 1

    return {
        "updated": updated,
        "updated_at": "server_time",
        "results": results,
    }
