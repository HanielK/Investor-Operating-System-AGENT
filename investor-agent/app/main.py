"""
Main entry point for the Investor Operating System Agent.

This module orchestrates the investment evaluation workflow:
1. Fetches financial data via FMP API
2. Calculates key metrics
3. Scores companies based on investment criteria
4. Writes results to Google Sheets/Excel
5. Stores data in Google Drive/GCS
"""

import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

# Use relative imports when run as a module
try:
    from .config import Config
    from .fmp_client import FMPClient
    from .metrics import MetricsCalculator
    from .scoring import InvestmentScorer
    from .writers.sheets_writer import SheetsWriter
    from .storage.gcs_store import GCSStore
except ImportError:
    # Fall back to absolute imports when run directly
    from config import Config
    from fmp_client import FMPClient
    from metrics import MetricsCalculator
    from scoring import InvestmentScorer
    from writers.sheets_writer import SheetsWriter
    from storage.gcs_store import GCSStore


def main(ticker: str, output_format: str = "sheets") -> Dict[str, Any]:
    """
    Main execution function for evaluating a company.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        output_format: Output format - 'sheets', 'gcs', or 'both'
    
    Returns:
        Result dictionary with exit code and artifacts
    """
    result: Dict[str, Any] = {
        "ticker": ticker,
        "exit_code": 1,
        "sheet_url": None,
        "artifact_uri": None,
        "errors": []
    }
    try:
        # Initialize configuration
        config = Config()
        
        # Initialize FMP API client
        fmp_client = FMPClient(config.fmp_api_key)
        
        # Fetch company data
        print(f"Fetching data for {ticker}...")
        company_data = fmp_client.get_company_data(ticker)
        
        # Calculate metrics
        print("Calculating investment metrics...")
        calculator = MetricsCalculator()
        metrics = calculator.calculate(company_data)
        
        # Score the company
        print("Scoring investment opportunity...")
        scorer = InvestmentScorer()
        score = scorer.score(metrics)
        
        # Prepare results
        profile = company_data.get("profile", {})
        results = {
            "ticker": ticker,
            "company_name": profile.get("companyName", ticker),
            "metrics": metrics,
            "score": score,
            "recommendation": scorer.get_recommendation(score),
            "fetched_at": datetime.utcnow().isoformat(),
            "run_id": str(uuid4())
        }
        
        # Write results
        print(f"Writing results to {output_format}...")
        sheet_ok = False
        gcs_ok = True

        if output_format in ("sheets", "both"):
            try:
                writer = SheetsWriter(config)
                sheet_url = writer.write(results)
                print(f"Results written to Google Sheets: {sheet_url}")
                result["sheet_url"] = sheet_url
                sheet_ok = True
            except Exception as e:
                print(f"Warning: Sheets write failed: {e}")
                result["errors"].append(str(e))

        if output_format in ("gcs", "both"):
            try:
                gs_uri = GCSStore(config).store_json(results, ticker)
                print(f"Stored JSON artifact in GCS: {gs_uri}")
                result["artifact_uri"] = gs_uri
                gcs_ok = True
            except Exception as e:
                print(f"Warning: GCS JSON upload failed: {e}")
                result["errors"].append(str(e))
                gcs_ok = False

        result["exit_code"] = 0 if (sheet_ok and gcs_ok) else 1
        result["updated"] = 1 if sheet_ok else 0
        
        print("Investment analysis complete!")
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        result["errors"].append(str(e))
        return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <TICKER> [sheets|gcs|both]")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    output_format = sys.argv[2] if len(sys.argv) > 2 else "sheets"
    
    outcome = main(ticker, output_format)
    sys.exit(outcome.get("exit_code", 1))
