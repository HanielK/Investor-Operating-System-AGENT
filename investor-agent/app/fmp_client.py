"""
Financial Modeling Prep (FMP) API Client.

Handles all interactions with the FMP API to fetch company financial data.
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime


class FMPClient:
    """
    Client for interacting with the Financial Modeling Prep API.
    
    Provides methods to fetch company profiles, financial statements,
    key metrics, and other investment-relevant data.
    """
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    
    def __init__(self, api_key: str):
        """
        Initialize the FMP API client.
        
        Args:
            api_key: FMP API key for authentication
        """
        if not api_key:
            raise ValueError("FMP API key is required")
        
        self.api_key = api_key
        self.session = requests.Session()
    
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
        
        response = self.session.get(url, params=params)
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
        endpoint = f"profile/{ticker}"
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
        endpoint = f"income-statement/{ticker}"
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
        endpoint = f"balance-sheet-statement/{ticker}"
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
        endpoint = f"cash-flow-statement/{ticker}"
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
        endpoint = f"key-metrics/{ticker}"
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
        return {
            "ticker": ticker,
            "profile": self.get_company_profile(ticker),
            "income_statements": self.get_income_statement(ticker),
            "balance_sheets": self.get_balance_sheet(ticker),
            "cash_flows": self.get_cash_flow(ticker),
            "key_metrics": self.get_key_metrics(ticker),
            "fetched_at": datetime.utcnow().isoformat()
        }
