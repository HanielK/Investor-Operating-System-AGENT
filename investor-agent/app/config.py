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
        raw_fmp_api_key = os.getenv("FMP_API_KEY", "")
        self.fmp_api_key = (raw_fmp_api_key or "").strip().strip('"').strip("'")
        
        # Storage Configuration
        self.output_storage_backend = os.getenv("OUTPUT_STORAGE_BACKEND", "gcs").strip().lower()
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID", "")
        self.gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "")
        self.gcs_prefix = os.getenv("GCS_PREFIX", "investor-analysis").strip()
        self.google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        
        # Google Sheets Configuration
        self.sheets_spreadsheet_id = os.getenv("SHEETS_SPREADSHEET_ID", "")
        self.sheets_worksheet_name = os.getenv("SHEETS_WORKSHEET_NAME", "Investment Analysis")
        
        # Google Drive Configuration
        self.drive_folder_id = os.getenv("DRIVE_FOLDER_ID", "")
        self.enable_drive_upload = self._get_bool(os.getenv("ENABLE_DRIVE_UPLOAD", "false"))
        
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
            "SHEETS_SPREADSHEET_ID": self.sheets_spreadsheet_id,
            "SHEETS_WORKSHEET_NAME": self.sheets_worksheet_name,
        }
        
        missing = [key for key, value in required_fields.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                "Please set the required environment variables."
            )

        if self.output_storage_backend not in {"gcs", "drive", "none"}:
            raise ValueError(
                "OUTPUT_STORAGE_BACKEND must be one of: gcs, drive, none"
            )
        if self.output_storage_backend == "gcs" and not self.gcs_bucket_name:
            raise ValueError(
                "GCS_BUCKET_NAME is required when OUTPUT_STORAGE_BACKEND=gcs"
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
