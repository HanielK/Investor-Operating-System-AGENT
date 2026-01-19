"""
Configuration management for the Investor Operating System Agent.

Handles environment variables and application settings.
"""

import os
from typing import Optional


class Config:
    """
    Configuration class for managing application settings.
    
    Loads configuration from environment variables with sensible defaults.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # API Keys
        self.fmp_api_key = os.getenv("FMP_API_KEY", "")
        
        # Google Cloud Configuration
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID", "")
        self.gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "investor-analysis")
        self.google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        
        # Google Sheets Configuration
        self.sheets_spreadsheet_id = os.getenv("SHEETS_SPREADSHEET_ID", "")
        self.sheets_worksheet_name = os.getenv("SHEETS_WORKSHEET_NAME", "Dashboard")
        self.promotion_log_worksheet_name = os.getenv(
            "PROMOTION_LOG_WORKSHEET_NAME",
            "Promotion Log"
        )

        # Dashboard block bounds
        self.dashboard_block_start_row = int(os.getenv("DASHBOARD_BLOCK_START_ROW", "2"))
        self.dashboard_block_end_row = int(os.getenv("DASHBOARD_BLOCK_END_ROW", "250"))

        # Promotion thresholds
        self.promote_score_threshold = int(os.getenv("PROMOTE_SCORE_THRESHOLD", "75"))
        self.high_priority_threshold = int(os.getenv("HIGH_PRIORITY_THRESHOLD", "85"))
        self.moat_gate_threshold = int(os.getenv("MOAT_GATE_THRESHOLD", "8"))
        self.min_fcf_positive = self._get_bool(os.getenv("MIN_FCF_POSITIVE", "true"))
        self.roic_gate_above_sector_median = self._get_bool(os.getenv("ROIC_GATE_ABOVE_SECTOR_MEDIAN", "true"))
        self.max_risk_flag_count = int(os.getenv("MAX_RISK_FLAG_COUNT", "0"))
        self.max_net_debt_to_ebitda = float(os.getenv("MAX_NET_DEBT_TO_EBITDA", "4.0"))
        self.require_thesis_not_broken = self._get_bool(os.getenv("REQUIRE_THESIS_NOT_BROKEN", "true"))

        # Write controls
        self.sheets_allow_append = self._get_bool(os.getenv("SHEETS_ALLOW_APPEND", "false"))
        self.sheets_dry_run = self._get_bool(os.getenv("SHEETS_DRY_RUN", "false"))
        
        # Google Drive Configuration
        self.drive_folder_id = os.getenv("DRIVE_FOLDER_ID", "")
        
        # Application Settings
        self.output_dir = os.getenv("OUTPUT_DIR", "/tmp/investor-analysis")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Scoring Thresholds
        self.score_threshold_buy = float(os.getenv("SCORE_THRESHOLD_BUY", "80"))
        self.score_threshold_hold = float(os.getenv("SCORE_THRESHOLD_HOLD", "60"))
        
        # Validate required configuration
        self._validate()
    
    def _validate(self):
        """Validate that required configuration is present."""
        required_fields = {
            "FMP_API_KEY": self.fmp_api_key,
        }
        
        missing = [key for key, value in required_fields.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                "Please set the required environment variables."
            )

    @staticmethod
    def _get_bool(raw_value: str) -> bool:
        return str(raw_value).strip().lower() in {"1", "true", "yes", "y", "on"}
    
    def __repr__(self):
        """Return string representation of config (hiding sensitive data)."""
        return (
            f"Config("
            f"fmp_api_key={'*' * 8 if self.fmp_api_key else 'NOT_SET'}, "
            f"gcp_project_id={self.gcp_project_id}, "
            f"output_dir={self.output_dir}"
            f")"
        )
