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
from typing import Optional

from config import Config
from fmp_client import FMPClient
from metrics import MetricsCalculator
from scoring import InvestmentScorer
from writers.sheets_writer import SheetsWriter
from writers.excel_writer import ExcelWriter
from storage.drive_store import DriveStore
from storage.gcs_store import GCSStore


def main(ticker: str, output_format: str = "sheets") -> int:
    """
    Main execution function for evaluating a company.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        output_format: Output format - 'sheets' or 'excel'
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
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
            "recommendation": scorer.get_recommendation(score)
        }
        
        # Write results
        print(f"Writing results to {output_format}...")
        if output_format == "sheets":
            writer = SheetsWriter(config)
            sheet_url = writer.write(results)
            print(f"Results written to Google Sheets: {sheet_url}")
            
            # Store in Google Drive
            storage = DriveStore(config)
            storage.store(results, ticker)
        else:
            writer = ExcelWriter(config)
            file_path = writer.write(results)
            print(f"Results written to Excel: {file_path}")
            
            # Store in GCS
            storage = GCSStore(config)
            storage.store(file_path, ticker)
        
        print("✓ Investment analysis complete!")
        return 0
        
    except Exception as e:
        print(f"✗ Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <TICKER> [sheets|excel]")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    output_format = sys.argv[2] if len(sys.argv) > 2 else "sheets"
    
    sys.exit(main(ticker, output_format))
