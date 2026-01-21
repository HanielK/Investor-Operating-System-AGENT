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
    results = []
    updated = 0

    for t in req.tickers:
        t = t.upper().strip()

        sheet_ok = False
        gcs_ok = False
        artifact_uri = None
        error_message = ""

        try:
            outcome = run_one(t, req.output_format)
        except Exception as e:
            outcome = {"exit_code": 1, "artifact_uri": None, "errors": [str(e)]}

        # Normalize outcome fields
        artifact_uri = outcome.get("artifact_uri")
        errors = outcome.get("errors", []) or []

        # Backend success checks
        if req.output_format in ("sheets", "both"):
            # Treat sheets as success if the runner says exit_code=0
            sheet_ok = (outcome.get("exit_code", 1) == 0)

        if req.output_format in ("gcs", "both"):
            # Treat gcs as success if we got a gs:// URI
            gcs_ok = isinstance(artifact_uri, str) and artifact_uri.startswith("gs://")

        # Final exit code rules
        if req.output_format == "sheets":
            final_code = 0 if sheet_ok else 1
        elif req.output_format == "gcs":
            final_code = 0 if gcs_ok else 1
        else:  # both
            final_code = 0 if (sheet_ok and gcs_ok) else 1

        # Error message only when failing
        if final_code != 0 and errors:
            error_message = errors[0]

        # Don't return artifact_uri if GCS wasn't successful
        if req.output_format in ("gcs", "both") and not gcs_ok:
            artifact_uri = None

        results.append({
            "ticker": t,
            "exit_code": final_code,          # ✅ always return final_code
            "artifact_uri": artifact_uri,
            "error_message": error_message,
        })

        if sheet_ok:
            updated += 1

    return {"updated": updated, "updated_at": "server_time", "results": results}
