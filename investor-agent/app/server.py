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
        code = run_one(t, req.output_format)
        results.append({"ticker": t, "exit_code": code})
        if code == 0:
            updated += 1

    return {
        "updated": updated,
        "updated_at": "server_time",
        "results": results,
    }
