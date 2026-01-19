"""
Investment Scoring Engine.

Scores companies based on calculated metrics and investment criteria.
"""

from typing import Dict, Any, List, Tuple


class InvestmentScorer:
    """
    Scores investment opportunities based on financial metrics.
    
    Implements a refined evaluation framework based on 7 key questions:
    1. Is the business profitable and growing?
    2. Does it have a sustainable competitive advantage?
    3. Is management effective and shareholder-friendly?
    4. Is the valuation reasonable?
    5. Is the financial position strong?
    6. Are there catalysts for growth?
    7. What is the margin of safety?
    """
    
    # Scoring weights for different categories
    WEIGHTS = {
        "profitability": 0.25,
        "growth": 0.20,
        "value": 0.20,
        "quality": 0.20,
        "financial_health": 0.15
    }
    
    def score(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall investment score from metrics.
        
        Args:
            metrics: Dictionary of calculated financial metrics
        
        Returns:
            Dictionary containing scores and analysis
        """
        # Score each category
        profitability_score = self._score_profitability(metrics.get("profitability", {}))
        growth_score = self._score_growth(metrics.get("growth", {}))
        value_score = self._score_value(metrics.get("value", {}))
        quality_score = self._score_quality(metrics.get("quality", {}))
        health_score = self._score_financial_health(metrics.get("financial_health", {}))
        
        # Calculate weighted total score
        total_score = (
            profitability_score * self.WEIGHTS["profitability"] +
            growth_score * self.WEIGHTS["growth"] +
            value_score * self.WEIGHTS["value"] +
            quality_score * self.WEIGHTS["quality"] +
            health_score * self.WEIGHTS["financial_health"]
        )
        
        subscores = {
            "profitability": round(profitability_score, 2),
            "growth": round(growth_score, 2),
            "value": round(value_score, 2),
            "quality": round(quality_score, 2),
            "financial_health": round(health_score, 2)
        }

        moat_score = self._estimate_moat_score(metrics, profitability_score, quality_score)
        risk_flags = self._derive_risk_flags(metrics)
        thesis_broken = bool(metrics.get("thesis_broken", False))

        score_payload = {
            "total": round(total_score, 2),
            "total_score": round(total_score, 2),
            "moat_score": moat_score,
            "risk_flags": risk_flags,
            "thesis_broken": thesis_broken,
            "subscores": subscores,
            "category_scores": subscores,
            "strengths": self._identify_strengths(metrics),
            "concerns": self._identify_concerns(metrics)
        }
        score_payload["decision"] = self.get_recommendation(score_payload)
        return score_payload
    
    def _score_profitability(self, profitability: Dict) -> float:
        """Score profitability metrics (0-100)."""
        if not profitability:
            return 0
        
        score = 0
        
        # Net margin scoring (0-30 points)
        net_margin = profitability.get("net_margin", 0)
        if net_margin > 20:
            score += 30
        elif net_margin > 10:
            score += 20
        elif net_margin > 5:
            score += 10
        
        # ROE scoring (0-40 points)
        roe = profitability.get("roe", 0)
        if roe > 20:
            score += 40
        elif roe > 15:
            score += 30
        elif roe > 10:
            score += 20
        
        # Gross margin scoring (0-30 points)
        gross_margin = profitability.get("gross_margin", 0)
        if gross_margin > 50:
            score += 30
        elif gross_margin > 30:
            score += 20
        elif gross_margin > 20:
            score += 10
        
        return min(score, 100)
    
    def _score_growth(self, growth: Dict) -> float:
        """Score growth metrics (0-100)."""
        if not growth:
            return 0
        
        score = 0
        
        # Revenue growth scoring (0-50 points)
        revenue_growth = growth.get("revenue_growth", 0)
        if revenue_growth > 20:
            score += 50
        elif revenue_growth > 10:
            score += 35
        elif revenue_growth > 5:
            score += 20
        elif revenue_growth > 0:
            score += 10
        
        # Earnings growth scoring (0-50 points)
        earnings_growth = growth.get("earnings_growth", 0)
        if earnings_growth > 20:
            score += 50
        elif earnings_growth > 10:
            score += 35
        elif earnings_growth > 5:
            score += 20
        elif earnings_growth > 0:
            score += 10
        
        return min(score, 100)
    
    def _score_value(self, value: Dict) -> float:
        """Score valuation metrics (0-100)."""
        if not value:
            return 0
        
        score = 0
        
        # P/E ratio scoring (0-50 points) - lower is better
        pe_ratio = value.get("pe_ratio", 0)
        if 0 < pe_ratio < 15:
            score += 50
        elif 15 <= pe_ratio < 25:
            score += 35
        elif 25 <= pe_ratio < 35:
            score += 20
        elif pe_ratio >= 35:
            score += 10
        
        # P/B ratio scoring (0-30 points) - lower is better
        pb_ratio = value.get("pb_ratio", 0)
        if 0 < pb_ratio < 2:
            score += 30
        elif 2 <= pb_ratio < 4:
            score += 20
        elif 4 <= pb_ratio < 6:
            score += 10
        
        # Price to Sales (0-20 points)
        ps_ratio = value.get("price_to_sales", 0)
        if 0 < ps_ratio < 2:
            score += 20
        elif 2 <= ps_ratio < 4:
            score += 10
        
        return min(score, 100)
    
    def _score_quality(self, quality: Dict) -> float:
        """Score quality metrics (0-100)."""
        if not quality:
            return 0
        
        score = 0
        
        # Debt to equity scoring (0-40 points) - lower is better
        debt_to_equity = quality.get("debt_to_equity", 0)
        if debt_to_equity < 0.5:
            score += 40
        elif debt_to_equity < 1.0:
            score += 30
        elif debt_to_equity < 2.0:
            score += 15
        
        # Cash flow quality (0-40 points)
        cf_to_ni = quality.get("cash_flow_to_net_income", 0)
        if cf_to_ni > 1.2:
            score += 40
        elif cf_to_ni > 1.0:
            score += 30
        elif cf_to_ni > 0.8:
            score += 20
        
        # Free cash flow (0-20 points)
        fcf = quality.get("free_cash_flow", 0)
        if fcf > 0:
            score += 20
        
        return min(score, 100)
    
    def _score_financial_health(self, health: Dict) -> float:
        """Score financial health metrics (0-100)."""
        if not health:
            return 0
        
        score = 0
        
        # Current ratio scoring (0-40 points)
        current_ratio = health.get("current_ratio", 0)
        if current_ratio > 2.0:
            score += 40
        elif current_ratio > 1.5:
            score += 30
        elif current_ratio > 1.0:
            score += 20
        
        # Quick ratio scoring (0-30 points)
        quick_ratio = health.get("quick_ratio", 0)
        if quick_ratio > 1.5:
            score += 30
        elif quick_ratio > 1.0:
            score += 20
        elif quick_ratio > 0.75:
            score += 10
        
        # Interest coverage (0-30 points)
        interest_coverage = health.get("interest_coverage", 0)
        if interest_coverage > 10:
            score += 30
        elif interest_coverage > 5:
            score += 20
        elif interest_coverage > 2:
            score += 10
        
        return min(score, 100)
    
    def _identify_strengths(self, metrics: Dict) -> List[str]:
        """Identify key strengths of the investment."""
        strengths = []
        
        profitability = metrics.get("profitability", {})
        if profitability.get("roe", 0) > 20:
            strengths.append("Exceptional return on equity (>20%)")
        if profitability.get("net_margin", 0) > 15:
            strengths.append("Strong profit margins")
        
        growth = metrics.get("growth", {})
        if growth.get("revenue_growth", 0) > 15:
            strengths.append("High revenue growth rate")
        
        quality = metrics.get("quality", {})
        debt_to_equity = quality.get("debt_to_equity")
        if debt_to_equity is not None and debt_to_equity < 0.5:
            strengths.append("Low debt levels")
        if quality.get("cash_flow_to_net_income", 0) > 1.2:
            strengths.append("Excellent cash flow generation")
        
        health = metrics.get("financial_health", {})
        if health.get("current_ratio", 0) > 2.0:
            strengths.append("Strong liquidity position")
        
        return strengths
    
    def _identify_concerns(self, metrics: Dict) -> List[str]:
        """Identify potential concerns or red flags."""
        concerns = []
        
        profitability = metrics.get("profitability", {})
        if profitability.get("net_margin", 0) < 0:
            concerns.append("Company is not profitable")
        
        growth = metrics.get("growth", {})
        if growth.get("revenue_growth", 0) < 0:
            concerns.append("Declining revenues")
        
        quality = metrics.get("quality", {})
        if quality.get("debt_to_equity", 0) > 2.0:
            concerns.append("High debt levels relative to equity")
        if quality.get("free_cash_flow", 0) < 0:
            concerns.append("Negative free cash flow")
        
        health = metrics.get("financial_health", {})
        if health.get("current_ratio", 0) < 1.0:
            concerns.append("Liquidity concerns (current ratio < 1.0)")
        
        value = metrics.get("value", {})
        if value.get("pe_ratio", 0) > 50:
            concerns.append("High valuation (P/E > 50)")
        
        return concerns
    
    def get_recommendation(self, score: Dict[str, Any]) -> str:
        """
        Get investment recommendation based on score.
        
        Args:
            score: Score dictionary from score() method
        
        Returns:
            Investment recommendation string
        """
        total_score = score.get("total", score.get("total_score", 0))
        
        if total_score >= 80:
            return "STRONG BUY - Excellent investment opportunity"
        elif total_score >= 70:
            return "BUY - Good investment with solid fundamentals"
        elif total_score >= 60:
            return "HOLD - Acceptable investment, monitor closely"
        elif total_score >= 50:
            return "CAUTIOUS - Weak fundamentals, consider alternatives"
        else:
            return "AVOID - Poor investment metrics"

    def _estimate_moat_score(
        self,
        metrics: Dict[str, Any],
        profitability_score: float,
        quality_score: float
    ) -> int:
        """
        Estimate moat score on a 0-10 scale.

        Uses explicit metric if provided, otherwise approximates from quality/profitability.
        """
        explicit = metrics.get("moat_score")
        if explicit is not None:
            try:
                return int(round(float(explicit)))
            except (TypeError, ValueError):
                pass
        estimated = (profitability_score + quality_score) / 20
        return max(0, min(10, int(round(estimated))))

    def _derive_risk_flags(self, metrics: Dict[str, Any]) -> List[str]:
        """Derive risk flags from provided metrics or concerns."""
        risk_flags = metrics.get("risk_flags")
        if isinstance(risk_flags, list):
            return [str(flag) for flag in risk_flags]
        return self._identify_concerns(metrics)
