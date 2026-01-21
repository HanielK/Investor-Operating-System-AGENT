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
        sheet_ok = False
        gcs_ok = False
        try:
            outcome = run_one(t, req.output_format)
        except Exception as e:
            outcome = {"exit_code": 1, "artifact_uri": None, "errors": [str(e)]}

        errors = outcome.get("errors", []) or []
        artifact_uri = outcome.get("artifact_uri")
        sheet_url = outcome.get("sheet_url")

        if req.output_format in ("sheets", "both"):
            sheet_ok = bool(sheet_url)

        if req.output_format in ("gcs", "both"):
            gcs_ok = isinstance(artifact_uri, str) and artifact_uri.startswith("gs://")

        if req.output_format == "sheets":
            code = 0 if sheet_ok else 1
        elif req.output_format == "gcs":
            code = 0 if gcs_ok else 1
        else:
            code = 0 if (sheet_ok and gcs_ok) else 1

        error_message = ""
        if code != 0 and errors:
            error_message = errors[0]
        if req.output_format in ("gcs", "both") and not gcs_ok:
            artifact_uri = None

        results.append({
            "ticker": t,
            "exit_code": code,
            "artifact_uri": artifact_uri,
            "error_message": error_message
        })
        if sheet_ok:
            updated += 1

    return {
        "updated": updated,
        "updated_at": "server_time",
        "results": results,
    }
