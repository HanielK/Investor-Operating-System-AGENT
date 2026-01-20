"""
Google Drive Storage.

Stores investment analysis files in Google Drive.
"""

from typing import Dict, Any, Optional
import json
import os
from datetime import datetime


class DriveStore:
    """
    Stores investment analysis data in Google Drive.
    
    Uses Google Drive API to upload and organize analysis files.
    """
    
    def __init__(self, config):
        """
        Initialize the Google Drive storage handler.
        
        Args:
            config: Configuration object with Google Drive settings
        """
        self.config = config
        self.folder_id = config.drive_folder_id
        
        # Initialize Google Drive API client
        self._init_drive_client()
    
    def _init_drive_client(self):
        """Initialize Google Drive API client using Application Default Credentials (ADC)."""
        try:
            import google.auth
            from googleapiclient.discovery import build

            credentials, _ = google.auth.default(
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            self.drive_service = build('drive', 'v3', credentials=credentials)

        except ImportError:
            print("Warning: Google API client libraries not installed. Install with: pip install google-api-python-client google-auth")
            self.drive_service = None
        except Exception as e:
            print(f"Warning: Could not initialize Google Drive client: {e}")
            self.drive_service = None

    
    def store(self, results: Dict[str, Any], ticker: str) -> str:
        """
        Store investment analysis results in Google Drive.
        
        Args:
            results: Analysis results dictionary
            ticker: Stock ticker symbol
        
        Returns:
            File ID of the uploaded file
        """
        if not self.drive_service:
            raise RuntimeError("Google Drive service not initialized")
        
        # Create JSON file from results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_analysis_{timestamp}.json"
        
        # Save to temp file first
        temp_path = f"/tmp/{filename}"
        with open(temp_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        try:
            # Upload to Google Drive
            file_metadata = {
                'name': filename,
                'mimeType': 'application/json'
            }
            
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]
            
            from googleapiclient.http import MediaFileUpload
            
            media = MediaFileUpload(
                temp_path,
                mimetype='application/json',
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            # Clean up temp file
            os.remove(temp_path)
            
            file_id = file.get('id')
            web_link = file.get('webViewLink', '')
            
            print(f"Stored in Google Drive: {web_link}")
            
            return file_id
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(f"Failed to upload to Google Drive: {e}")

    def store_file(self, file_path: str, ticker: str) -> str:
        """
        Store a file in Google Drive.

        Args:
            file_path: Path to the file to upload
            ticker: Stock ticker symbol

        Returns:
            File ID of the uploaded file
        """
        if not self.drive_service:
            raise RuntimeError("Google Drive service not initialized")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            upload_name = f"{name}_{ticker}_{timestamp}{ext}"

            file_metadata = {"name": upload_name}
            if self.folder_id:
                file_metadata["parents"] = [self.folder_id]

            from googleapiclient.http import MediaFileUpload

            media = MediaFileUpload(file_path, resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id,webViewLink"
            ).execute()

            file_id = file.get("id")
            web_link = file.get("webViewLink", "")
            print(f"Stored file in Google Drive: {web_link}")

            return file_id
        except Exception as e:
            raise RuntimeError(f"Failed to upload file to Google Drive: {e}")
    
    def list_files(self, ticker: Optional[str] = None) -> list:
        """
        List analysis files in Google Drive.
        
        Args:
            ticker: Optional ticker to filter by
        
        Returns:
            List of file metadata dictionaries
        """
        if not self.drive_service:
            raise RuntimeError("Google Drive service not initialized")
        
        try:
            query = "mimeType='application/json'"
            
            if ticker:
                query += f" and name contains '{ticker}'"
            
            if self.folder_id:
                query += f" and '{self.folder_id}' in parents"
            
            results = self.drive_service.files().list(
                q=query,
                pageSize=100,
                fields="files(id, name, createdTime, webViewLink)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            raise RuntimeError(f"Failed to list files from Google Drive: {e}")
