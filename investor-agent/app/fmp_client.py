"""
Financial Modeling Prep (FMP) API Client.

Handles all interactions with the FMP API to fetch company financial data.
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import structlog
    _LOGGER_FACTORY = structlog.get_logger
except ImportError:  # pragma: no cover - fallback when structlog is missing
    _LOGGER_FACTORY = logging.getLogger


class FMPClient:
    """
    Client for interacting with the Financial Modeling Prep API.
    
    Provides methods to fetch company profiles, financial statements,
    key metrics, and other investment-relevant data.
    """
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    
    def __init__(self, api_key: str, timeout_seconds: int = 15, logger: Optional[logging.Logger] = None):
        """
        Initialize the FMP API client.
        
        Args:
            api_key: FMP API key for authentication
        """
        if not api_key:
            raise ValueError("FMP API key is required")
        
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.logger = logger or _LOGGER_FACTORY(__name__)
        self.session = requests.Session()
        self._init_session_retries()

    def _log(self, level: str, message: str, **fields: Any) -> None:
        if hasattr(self.logger, "bind"):
            getattr(self.logger, level)(message, **fields)
        else:
            getattr(self.logger, level)(message, extra=fields)

    def _init_session_retries(self) -> None:
        """Configure retries and backoff for transient API errors."""
        retry = Retry(
            total=4,
            connect=4,
            read=4,
            status=4,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    @staticmethod
    def _normalize_ticker(ticker: str) -> str:
        """Normalize tickers for FMP (e.g., BRK.B -> BRK-B)."""
        return ticker.strip().upper().replace(".", "-")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make a request to the FMP API.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
        
        Returns:
            JSON response from the API
        
        Raises:
            requests.RequestException: If the request fails
        """
        if params is None:
            params = {}
        
        params["apikey"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"

        response = self.session.get(url, params=params, timeout=self.timeout_seconds)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            self._log(
                "warning",
                "FMP rate limit hit",
                endpoint=endpoint,
                retry_after=retry_after,
            )
        response.raise_for_status()
        
        return response.json()
    
    def get_company_profile(self, ticker: str) -> Dict:
        """
        Get company profile information.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Company profile data
        """
        normalized = self._normalize_ticker(ticker)
        endpoint = f"profile/{normalized}"
        data = self._make_request(endpoint)
        
        if not data or len(data) == 0:
            raise ValueError(f"No profile found for ticker {ticker}")
        
        return data[0]
    
    def get_income_statement(self, ticker: str, period: str = "annual", limit: int = 5) -> List[Dict]:
        """
        Get income statement data.
        
        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to fetch
        
        Returns:
            List of income statement data
        """
        normalized = self._normalize_ticker(ticker)
        endpoint = f"income-statement/{normalized}"
        params = {"period": period, "limit": limit}
        return self._make_request(endpoint, params)
    
    def get_balance_sheet(self, ticker: str, period: str = "annual", limit: int = 5) -> List[Dict]:
        """
        Get balance sheet data.
        
        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to fetch
        
        Returns:
            List of balance sheet data
        """
        normalized = self._normalize_ticker(ticker)
        endpoint = f"balance-sheet-statement/{normalized}"
        params = {"period": period, "limit": limit}
        return self._make_request(endpoint, params)
    
    def get_cash_flow(self, ticker: str, period: str = "annual", limit: int = 5) -> List[Dict]:
        """
        Get cash flow statement data.
        
        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to fetch
        
        Returns:
            List of cash flow data
        """
        normalized = self._normalize_ticker(ticker)
        endpoint = f"cash-flow-statement/{normalized}"
        params = {"period": period, "limit": limit}
        return self._make_request(endpoint, params)
    
    def get_key_metrics(self, ticker: str, period: str = "annual", limit: int = 5) -> List[Dict]:
        """
        Get key financial metrics.
        
        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to fetch
        
        Returns:
            List of key metrics data
        """
        normalized = self._normalize_ticker(ticker)
        endpoint = f"key-metrics/{normalized}"
        params = {"period": period, "limit": limit}
        return self._make_request(endpoint, params)
    
    def get_company_data(self, ticker: str) -> Dict:
        """
        Get comprehensive company data for investment analysis.
        
        Fetches profile, financial statements, and key metrics.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary containing all company data
        """
        normalized = self._normalize_ticker(ticker)
        self._log("info", "Fetching FMP data", ticker=ticker, fmp_ticker=normalized)
        return {
            "ticker": ticker,
            "fmp_ticker": normalized,
            "profile": self.get_company_profile(ticker),
            "income_statements": self.get_income_statement(ticker),
            "balance_sheets": self.get_balance_sheet(ticker),
            "cash_flows": self.get_cash_flow(ticker),
            "key_metrics": self.get_key_metrics(ticker),
            "fetched_at": datetime.utcnow().isoformat()
        }
