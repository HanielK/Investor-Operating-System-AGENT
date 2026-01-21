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
            outcome = {
                "exit_code": 1,
                "artifact_uri": None,
                "errors": [str(e)],
            }

        exit_code = outcome.get("exit_code", 1)
        artifact_uri = outcome.get("artifact_uri")
        errors = outcome.get("errors", []) or []

        # ---- Evaluate success per backend ----
        if req.output_format in ("sheets", "both"):
            sheet_ok = exit_code == 0

        if req.output_format in ("gcs", "both"):
            gcs_ok = isinstance(artifact_uri, str) and artifact_uri.startswith("gs://")

        # ---- Final exit code logic ----
        if req.output_format == "sheets":
            final_code = 0 if sheet_ok else 1
        elif req.output_format == "gcs":
            final_code = 0 if gcs_ok else 1
        else:  # both
            final_code = 0 if (sheet_ok and gcs_ok) else 1

        # ---- Error message handling ----
        if final_code != 0 and errors:
            error_message = errors[0]

        # Do not return artifact_uri if GCS failed
        if req.output_format in ("gcs", "both") and not gcs_ok:
            artifact_uri = None

        results.append({
            "ticker": t,
            "exit_code": final_code,
            "artifact_uri": artifact_uri,
            "error_message": error_message,
        })

        if sheet_ok:
            updated += 1

    return {
        "updated": updated,
        "updated_at": "server_time",
        "results": results,
    }
