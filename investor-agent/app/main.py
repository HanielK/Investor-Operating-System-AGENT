"""
Main entry point for the Investor Operating System Agent.

This module orchestrates the investment evaluation workflow:
1. Fetches financial data via FMP API
2. Calculates key metrics
3. Scores companies based on investment criteria
4. Writes results to Google Sheets/Excel
5. Stores data in Google Drive/GCS
"""

import logging
import sys
from uuid import uuid4
from typing import Optional

try:
    import structlog
except ImportError:  # pragma: no cover - fallback when structlog is missing
    structlog = None

# Use relative imports when run as a module
try:
    from .config import Config
    from .fmp_client import FMPClient
    from .metrics import MetricsCalculator
    from .scoring import InvestmentScorer
    from .writers.sheets_writer import SheetsWriter
    from .writers.excel_writer import ExcelWriter
    from .storage.drive_store import DriveStore
    from .storage.gcs_store import GCSStore
except ImportError:
    # Fall back to absolute imports when run directly
    from config import Config
    from fmp_client import FMPClient
    from metrics import MetricsCalculator
    from scoring import InvestmentScorer
    from writers.sheets_writer import SheetsWriter
    from writers.excel_writer import ExcelWriter
    from storage.drive_store import DriveStore
    from storage.gcs_store import GCSStore


def _setup_logging() -> logging.Logger:
    """Configure structured logging."""
    log_level = logging.INFO
    if structlog:
        logging.basicConfig(level=log_level, format="%(message)s")
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        return structlog.get_logger("investor-agent")

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    return logging.getLogger("investor-agent")


def _bind_logger(logger: logging.Logger, **fields: str) -> logging.Logger:
    if hasattr(logger, "bind"):
        return logger.bind(**fields)
    return logging.LoggerAdapter(logger, extra=fields)


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
        logger = _setup_logging()
        logger = _bind_logger(logger, ticker=ticker, output_format=output_format)

        # Initialize configuration
        config = Config()
        
        # Initialize FMP API client
        fmp_client = FMPClient(config.fmp_api_key, logger=logger)
        
        # Fetch company data
        logger.info("Fetching data from FMP")
        company_data = fmp_client.get_company_data(ticker)
        
        # Calculate metrics
        logger.info("Calculating investment metrics")
        calculator = MetricsCalculator()
        metrics = calculator.calculate(company_data)
        
        # Score the company
        logger.info("Scoring investment opportunity")
        scorer = InvestmentScorer()
        score = scorer.score(metrics)
        
        # Prepare results
        profile = company_data.get("profile", {})
        results = {
            "ticker": ticker,
            "company_name": profile.get("companyName", ticker),
            "current_price": profile.get("price"),
            "year_high": profile.get("yearHigh"),
            "metrics": metrics,
            "score": score,
            "recommendation": scorer.get_recommendation(score),
            "last_updated": company_data.get("fetched_at")
        }
        
        # Write results
        logger.info("Writing results", output_format=output_format)
        if output_format == "sheets":
            writer = SheetsWriter(config, logger=logger)
            sheet_url = writer.write(
                results,
                allow_append=config.sheets_allow_append,
                dry_run=config.sheets_dry_run,
                run_id=str(uuid4())
            )
            logger.info("Results written to Google Sheets", sheet_url=sheet_url)
            
            # Store in Google Drive
            storage = DriveStore(config)
            storage.store(results, ticker)
        else:
            writer = ExcelWriter(config)
            file_path = writer.write(results)
            logger.info("Results written to Excel", file_path=file_path)
            
            # Store in GCS
            storage = GCSStore(config)
            storage.store(file_path, ticker)
        
        logger.info("Investment analysis complete")
        return 0
        
    except Exception as e:
        if "logger" in locals():
            logger.exception("Investment analysis failed")
        else:
            print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <TICKER> [sheets|excel]")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    output_format = sys.argv[2] if len(sys.argv) > 2 else "sheets"
    
    sys.exit(main(ticker, output_format))
