"""
Google Sheets Writer.

Writes investment analysis results to Google Sheets.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime, timezone
from uuid import uuid4

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9
    ZoneInfo = None

try:
    import structlog
    _LOGGER_FACTORY = structlog.get_logger
except ImportError:  # pragma: no cover - fallback when structlog is missing
    _LOGGER_FACTORY = logging.getLogger


class SheetsWriter:
    """
    Writes investment analysis results to Google Sheets.
    
    Uses Google Sheets API to update spreadsheets with analysis data.
    """
    
    def __init__(self, config, logger: Optional[Any] = None):
        """
        Initialize the Google Sheets writer.
        
        Args:
            config: Configuration object with Google Sheets settings
        """
        self.config = config
        self.spreadsheet_id = config.sheets_spreadsheet_id
        self.dashboard_tab = config.sheets_worksheet_name
        self.promo_log_tab = config.promotion_log_worksheet_name
        self.block_start = config.dashboard_block_start_row
        self.block_end = config.dashboard_block_end_row
        self.promote_score_threshold = config.promote_score_threshold
        self.high_priority_threshold = config.high_priority_threshold
        self.moat_gate_threshold = config.moat_gate_threshold
        self.min_fcf_positive = config.min_fcf_positive
        self.roic_gate_above_sector_median = config.roic_gate_above_sector_median
        self.max_risk_flag_count = config.max_risk_flag_count
        self.max_net_debt_to_ebitda = config.max_net_debt_to_ebitda
        self.require_thesis_not_broken = config.require_thesis_not_broken
        self.logger = logger or _LOGGER_FACTORY(__name__)
        
        # Initialize Google Sheets API client
        self._init_sheets_client()
    
    def _init_sheets_client(self):
        """Initialize Google Sheets API client."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            credentials = service_account.Credentials.from_service_account_file(
                self.config.google_credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
        except ImportError:
            print("Warning: Google API client libraries not installed. Install with: pip install google-api-python-client google-auth")
            self.sheets_service = None
        except Exception as e:
            print(f"Warning: Could not initialize Google Sheets client: {e}")
            self.sheets_service = None

    def _log(self, level: str, message: str, **fields: Any) -> None:
        if hasattr(self.logger, "bind"):
            getattr(self.logger, level)(message, **fields)
        else:
            getattr(self.logger, level)(message, extra=fields)

    def _ensure_tab(self, tab_name: str) -> None:
        """Ensure the target worksheet exists."""
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id
        ).execute()
        sheets = spreadsheet.get("sheets", [])
        sheet_titles = {s.get("properties", {}).get("title") for s in sheets}
        if tab_name in sheet_titles:
            return

        self._log(
            "info",
            "Creating worksheet",
            worksheet=tab_name,
            spreadsheet_id=self.spreadsheet_id,
        )
        body = {
            "requests": [
                {"addSheet": {"properties": {"title": tab_name}}}
            ]
        }
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=body
        ).execute()

    def _ensure_promotion_log_tab(self) -> None:
        self._ensure_tab(self.promo_log_tab)
        header = [["Timestamp_ET", "Ticker", "Company", "TotalScore", "Recommendation", "Action", "Reason", "RunId"]]
        header_range = f"{self.promo_log_tab}!A1:H1"
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=header_range,
            valueInputOption="RAW",
            body={"values": header}
        ).execute()

    @staticmethod
    def _normalize_ticker(raw: Any) -> str:
        if raw is None:
            return ""
        return str(raw).strip().upper()

    def _read_dashboard_column_a(self) -> List[List[str]]:
        range_a = f"{self.dashboard_tab}!A{self.block_start}:A{self.block_end}"
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_a,
            majorDimension="ROWS"
        ).execute()
        return result.get("values", [])

    def _build_ticker_row_map(self, rows: List[List[str]]) -> Dict[str, int]:
        mapping: Dict[str, int] = {}
        for index, row in enumerate(rows, start=self.block_start):
            ticker = self._normalize_ticker(row[0]) if row else ""
            if not ticker:
                continue
            if ticker == "TICKER":
                continue
            mapping[ticker] = index
        return mapping

    def _find_first_empty_row(self, rows: List[List[str]]) -> Optional[int]:
        for offset, row in enumerate(rows):
            row_index = self.block_start + offset
            if row_index > self.block_end:
                break
            value = row[0] if row else ""
            if not self._normalize_ticker(value):
                return row_index
        return None

    @staticmethod
    def _coerce_number(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _now_et_timestamp(self) -> str:
        if ZoneInfo:
            tz = ZoneInfo("America/New_York")
            return datetime.now(tz=tz).isoformat()
        return datetime.now(timezone.utc).isoformat()

    def _build_dashboard_row(self, results: Dict[str, Any]) -> List[Any]:
        metrics = results.get("metrics", {})
        price = self._coerce_number(results.get("current_price") or metrics.get("price"))
        year_high = self._coerce_number(results.get("year_high") or metrics.get("year_high"))
        drawdown_pct = self._coerce_number(metrics.get("drawdown_pct"))
        if drawdown_pct is None and price is not None and year_high and year_high > 0:
            drawdown_pct = ((price - year_high) / year_high) * 100

        score = results.get("score", {}).get("total") or results.get("score", {}).get("total_score")
        recommendation = results.get("recommendation", "")
        last_updated = results.get("last_updated") or self._now_et_timestamp()

        return [
            price if price is not None else "",
            year_high if year_high is not None else "",
            round(drawdown_pct, 2) if drawdown_pct is not None else "",
            score if score is not None else "",
            recommendation,
            last_updated,
        ]

    def _append_new_ticker_row(self, row_index: int, ticker: str, dry_run: bool) -> None:
        range_a = f"{self.dashboard_tab}!A{row_index}:D{row_index}"
        values = [[ticker, "", "", ""]]
        if dry_run:
            self._log("info", "DRY_RUN append ticker row", range=range_a, values=values)
            return
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_a,
            valueInputOption="RAW",
            body={"values": values}
        ).execute()

    def _update_dashboard_ai_columns(self, row_index: int, results: Dict[str, Any], dry_run: bool) -> None:
        range_ej = f"{self.dashboard_tab}!E{row_index}:J{row_index}"
        values = [self._build_dashboard_row(results)]
        if dry_run:
            self._log("info", "DRY_RUN update dashboard AI columns", range=range_ej, values=values)
            return
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_ej,
            valueInputOption="RAW",
            body={"values": values}
        ).execute()

    def _should_promote(self, results: Dict[str, Any]) -> Tuple[bool, str]:
        reasons: List[str] = []
        score = results.get("score", {})
        metrics = results.get("metrics", {})

        total_score = score.get("total")
        if total_score is None:
            total_score = score.get("total_score")
        if total_score is None or total_score < self.promote_score_threshold:
            reasons.append(f"Total score below {self.promote_score_threshold}")
            return False, "; ".join(reasons)

        moat_score = score.get("moat_score")
        quality_metrics = metrics.get("quality", {})
        fcf = quality_metrics.get("free_cash_flow")
        roic = metrics.get("roic") or metrics.get("profitability", {}).get("roic")
        roic_above_median = bool(metrics.get("roic_above_sector_median"))

        business_pass = False
        if moat_score is not None and moat_score >= self.moat_gate_threshold:
            business_pass = True
        elif self.min_fcf_positive and fcf is not None and fcf > 0:
            business_pass = True
        elif self.roic_gate_above_sector_median and roic is not None and roic_above_median:
            business_pass = True

        if not business_pass:
            reasons.append("Business quality gate failed (no strong moat/FCF/ROIC)")
            return False, "; ".join(reasons)

        thesis_broken = bool(score.get("thesis_broken", False))
        if self.require_thesis_not_broken and thesis_broken:
            reasons.append("Thesis broken flag true")
            return False, "; ".join(reasons)

        risk_flags = score.get("risk_flags", []) or []
        if len(risk_flags) > self.max_risk_flag_count:
            reasons.append("Risk flags present: " + ",".join(risk_flags))
            return False, "; ".join(reasons)

        net_debt_to_ebitda = (
            metrics.get("net_debt_to_ebitda")
            or quality_metrics.get("net_debt_to_ebitda")
            or quality_metrics.get("debt_to_ebitda")
        )
        if net_debt_to_ebitda is not None and net_debt_to_ebitda > self.max_net_debt_to_ebitda:
            reasons.append("Net debt/EBITDA too high")
            return False, "; ".join(reasons)

        reasons.append("Passed: score, business gate, risk gate")
        return True, "; ".join(reasons)

    def _log_promotion_event(
        self,
        results: Dict[str, Any],
        action: str,
        reason: str,
        run_id: str,
        dry_run: bool
    ) -> None:
        row = [
            self._now_et_timestamp(),
            results.get("ticker", ""),
            results.get("company_name", ""),
            results.get("score", {}).get("total_score") or results.get("score", {}).get("total"),
            results.get("recommendation", ""),
            action,
            reason,
            run_id,
        ]
        if dry_run:
            self._log("info", "DRY_RUN promotion log append", row=row)
            return
        self.sheets_service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.promo_log_tab}!A:H",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]}
        ).execute()

    def write(
        self,
        results: Dict[str, Any],
        allow_append: bool = False,
        dry_run: bool = False,
        run_id: Optional[str] = None
    ) -> str:
        """
        Write investment analysis results to Google Sheets.
        
        Args:
            results: Analysis results dictionary
            allow_append: Allow auto-append to dashboard when promoted
            dry_run: When true, do not write to sheets
            run_id: Optional run id for promotion log
        
        Returns:
            URL to the Google Sheets document
        """
        if not self.sheets_service:
            raise RuntimeError("Google Sheets service not initialized")
        if not self.spreadsheet_id:
            raise RuntimeError("SHEETS_SPREADSHEET_ID is not configured")
        if not self.dashboard_tab:
            raise RuntimeError("SHEETS_WORKSHEET_NAME is not configured")
        if not self.promo_log_tab:
            raise RuntimeError("PROMOTION_LOG_WORKSHEET_NAME is not configured")

        ticker = self._normalize_ticker(results.get("ticker"))
        if not ticker:
            raise RuntimeError("Result payload missing ticker")

        run_id = run_id or str(uuid4())
        self._ensure_tab(self.dashboard_tab)
        self._ensure_promotion_log_tab()

        dashboard_rows = self._read_dashboard_column_a()
        ticker_map = self._build_ticker_row_map(dashboard_rows)

        if ticker in ticker_map:
            row_index = ticker_map[ticker]
            self._update_dashboard_ai_columns(row_index, results, dry_run)
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"

        promote, reason = self._should_promote(results)
        if not allow_append:
            self._log_promotion_event(
                results,
                action="NOT_APPENDED_ALLOW_APPEND_FALSE",
                reason=reason,
                run_id=run_id,
                dry_run=dry_run
            )
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"

        if not promote:
            self._log_promotion_event(
                results,
                action="REJECTED",
                reason=reason,
                run_id=run_id,
                dry_run=dry_run
            )
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"

        empty_row = self._find_first_empty_row(dashboard_rows)
        if empty_row is None:
            self._log_promotion_event(
                results,
                action="FAILED_NO_CAPACITY",
                reason=f"Dashboard block full A{self.block_start}:A{self.block_end}",
                run_id=run_id,
                dry_run=dry_run
            )
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"

        self._append_new_ticker_row(empty_row, ticker, dry_run)
        self._update_dashboard_ai_columns(empty_row, results, dry_run)

        action = "PROMOTED"
        total_score = results.get("score", {}).get("total") or results.get("score", {}).get("total_score")
        if total_score is not None and total_score >= self.high_priority_threshold:
            action = "HIGH_PRIORITY"

        self._log_promotion_event(
            results,
            action=action,
            reason=reason,
            run_id=run_id,
            dry_run=dry_run
        )
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
