"""
Investment Metrics Calculator.

Calculates key financial metrics and ratios for investment analysis.
"""

from typing import Dict, List, Optional, Any


class MetricsCalculator:
    """
    Calculates investment metrics from company financial data.
    
    Computes profitability, growth, value, and quality metrics
    used in the investment evaluation framework.
    """
    
    def calculate(self, company_data: Dict) -> Dict[str, Any]:
        """
        Calculate all investment metrics from company data.
        
        Args:
            company_data: Company financial data from FMP API
        
        Returns:
            Dictionary containing calculated metrics
        """
        profile = company_data.get("profile", {})
        income_statements = company_data.get("income_statements", [])
        balance_sheets = company_data.get("balance_sheets", [])
        cash_flows = company_data.get("cash_flows", [])
        key_metrics = company_data.get("key_metrics", [])
        
        metrics = {
            "profitability": self._calculate_profitability(income_statements, balance_sheets),
            "growth": self._calculate_growth(income_statements),
            "value": self._calculate_value_metrics(profile, key_metrics),
            "quality": self._calculate_quality_metrics(balance_sheets, cash_flows, income_statements),
            "financial_health": self._calculate_financial_health(balance_sheets, income_statements)
        }
        
        return metrics
    
    def _calculate_profitability(self, income_statements: List[Dict], balance_sheets: List[Dict]) -> Dict:
        """Calculate profitability metrics."""
        if not income_statements or not balance_sheets:
            return {}
        
        latest_income = income_statements[0]
        latest_balance = balance_sheets[0]
        
        net_income = latest_income.get("netIncome", 0)
        revenue = latest_income.get("revenue", 1)
        total_assets = latest_balance.get("totalAssets", 1)
        shareholders_equity = latest_balance.get("totalStockholdersEquity", 1)
        
        return {
            "net_margin": (net_income / revenue * 100) if revenue else 0,
            "roa": (net_income / total_assets * 100) if total_assets else 0,
            "roe": (net_income / shareholders_equity * 100) if shareholders_equity else 0,
            "gross_margin": (latest_income.get("grossProfit", 0) / revenue * 100) if revenue else 0,
            "operating_margin": (latest_income.get("operatingIncome", 0) / revenue * 100) if revenue else 0
        }
    
    def _calculate_growth(self, income_statements: List[Dict]) -> Dict:
        """Calculate growth metrics."""
        if len(income_statements) < 2:
            return {}
        
        current = income_statements[0]
        previous = income_statements[1]
        
        revenue_growth = self._calculate_growth_rate(
            previous.get("revenue", 0),
            current.get("revenue", 0)
        )
        
        earnings_growth = self._calculate_growth_rate(
            previous.get("netIncome", 0),
            current.get("netIncome", 0)
        )
        
        # Calculate CAGR if we have enough data
        revenue_cagr = self._calculate_cagr(
            [stmt.get("revenue", 0) for stmt in income_statements[:5]]
        )
        
        return {
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "revenue_cagr_5y": revenue_cagr
        }
    
    def _calculate_value_metrics(self, profile: Dict, key_metrics: List[Dict]) -> Dict:
        """Calculate valuation metrics."""
        if not key_metrics:
            return {}
        
        latest_metrics = key_metrics[0]
        
        return {
            "pe_ratio": latest_metrics.get("peRatio", 0),
            "pb_ratio": latest_metrics.get("pbRatio", 0),
            "price_to_sales": latest_metrics.get("priceToSalesRatio", 0),
            "ev_to_ebitda": latest_metrics.get("evToOperatingCashFlow", 0),
            "market_cap": profile.get("mktCap", 0)
        }
    
    def _calculate_quality_metrics(
        self, 
        balance_sheets: List[Dict], 
        cash_flows: List[Dict],
        income_statements: List[Dict]
    ) -> Dict:
        """Calculate quality and sustainability metrics."""
        if not balance_sheets or not cash_flows or not income_statements:
            return {}
        
        latest_balance = balance_sheets[0]
        latest_cash_flow = cash_flows[0]
        latest_income = income_statements[0]
        
        total_debt = latest_balance.get("totalDebt", 0)
        total_equity = latest_balance.get("totalStockholdersEquity", 1)
        ebitda = latest_income.get("ebitda", 1)
        
        operating_cash_flow = latest_cash_flow.get("operatingCashFlow", 0)
        net_income = latest_income.get("netIncome", 1)
        
        return {
            "debt_to_equity": total_debt / total_equity if total_equity else 0,
            "debt_to_ebitda": total_debt / ebitda if ebitda else 0,
            "cash_flow_to_net_income": operating_cash_flow / net_income if net_income else 0,
            "free_cash_flow": latest_cash_flow.get("freeCashFlow", 0)
        }
    
    def _calculate_financial_health(self, balance_sheets: List[Dict], income_statements: List[Dict]) -> Dict:
        """Calculate financial health metrics."""
        if not balance_sheets or not income_statements:
            return {}
        
        latest_balance = balance_sheets[0]
        latest_income = income_statements[0]
        
        current_assets = latest_balance.get("totalCurrentAssets", 0)
        current_liabilities = latest_balance.get("totalCurrentLiabilities", 1)
        
        return {
            "current_ratio": current_assets / current_liabilities if current_liabilities else 0,
            "quick_ratio": (current_assets - latest_balance.get("inventory", 0)) / current_liabilities if current_liabilities else 0,
            "interest_coverage": latest_income.get("operatingIncome", 0) / latest_income.get("interestExpense", 1) if latest_income.get("interestExpense") else float('inf')
        }
    
    @staticmethod
    def _calculate_growth_rate(old_value: float, new_value: float) -> float:
        """Calculate percentage growth rate."""
        if old_value == 0:
            return 0
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def _calculate_cagr(values: List[float]) -> float:
        """Calculate Compound Annual Growth Rate."""
        if len(values) < 2:
            return 0
        
        # Filter out zero or negative values
        positive_values = [v for v in values if v > 0]
        if len(positive_values) < 2:
            return 0
        
        # Values are in reverse chronological order (newest first)
        # So beginning_value is at the end and ending_value is at the start
        ending_value = positive_values[0]  # Most recent
        beginning_value = positive_values[-1]  # Oldest
        n = len(positive_values) - 1
        
        if beginning_value == 0:
            return 0
        
        return (((ending_value / beginning_value) ** (1 / n)) - 1) * 100
