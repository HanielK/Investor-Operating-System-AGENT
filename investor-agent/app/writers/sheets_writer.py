"""
Google Sheets Writer.

Writes investment analysis results to Google Sheets.
"""

from typing import Dict, Any
import json


class SheetsWriter:
    """
    Writes investment analysis results to Google Sheets.
    
    Uses Google Sheets API to update spreadsheets with analysis data.
    """
    
    def __init__(self, config):
        """
        Initialize the Google Sheets writer.
        
        Args:
            config: Configuration object with Google Sheets settings
        """
        self.config = config
        self.spreadsheet_id = config.sheets_spreadsheet_id
        self.worksheet_name = config.sheets_worksheet_name
        
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
    
    def write(self, results: Dict[str, Any]) -> str:
        """
        Write investment analysis results to Google Sheets.
        
        Args:
            results: Analysis results dictionary
        
        Returns:
            URL to the Google Sheets document
        """
        if not self.sheets_service:
            raise RuntimeError("Google Sheets service not initialized")
        
        # Prepare data rows
        rows = self._format_results_for_sheets(results)
        
        # Write to sheets
        try:
            # Get the sheet to append to
            sheet_range = f"{self.worksheet_name}!A:Z"
            
            body = {
                'values': rows
            }
            
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            # Return URL to the spreadsheet
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
            
        except Exception as e:
            raise RuntimeError(f"Failed to write to Google Sheets: {e}")
    
    def _format_results_for_sheets(self, results: Dict[str, Any]) -> list:
        """
        Format results into rows for Google Sheets.
        
        Args:
            results: Analysis results
        
        Returns:
            List of rows (each row is a list of values)
        """
        ticker = results.get("ticker", "")
        company_name = results.get("company_name", "")
        score = results.get("score", {})
        metrics = results.get("metrics", {})
        recommendation = results.get("recommendation", "")
        
        # Header row (if needed)
        rows = []
        
        # Summary row
        summary_row = [
            ticker,
            company_name,
            score.get("total_score", 0),
            recommendation,
            ", ".join(score.get("strengths", [])),
            ", ".join(score.get("concerns", []))
        ]
        rows.append(summary_row)
        
        # Category scores
        category_scores = score.get("category_scores", {})
        for category, value in category_scores.items():
            rows.append([f"  {category}", "", value, "", "", ""])
        
        # Add blank row for separation
        rows.append([""] * 6)
        
        return rows
