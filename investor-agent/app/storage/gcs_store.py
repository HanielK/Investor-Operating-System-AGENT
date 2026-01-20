"""
Google Cloud Storage (GCS) Handler.

Stores investment analysis files in Google Cloud Storage.
"""

from typing import Dict, Any, Optional
import json
import os
from datetime import datetime


class GCSStore:
    """
    Stores investment analysis data in Google Cloud Storage.
    
    Uses GCS client library to upload and organize analysis files.
    """
    
    def __init__(self, config):
        """
        Initialize the GCS storage handler.
        
        Args:
            config: Configuration object with GCS settings
        """
        self.config = config
        self.bucket_name = config.gcs_bucket_name
        self.gcs_prefix = config.gcs_prefix
        
        # Initialize GCS client
        self._init_gcs_client()
    
    def _init_gcs_client(self):
        """Initialize Google Cloud Storage client."""
        try:
            from google.cloud import storage
            
            # Initialize client using ADC
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.bucket_name)
            
        except ImportError:
            print("Warning: Google Cloud Storage library not installed. Install with: pip install google-cloud-storage")
            self.storage_client = None
            self.bucket = None
        except Exception as e:
            print(f"Warning: Could not initialize GCS client: {e}")
            self.storage_client = None
            self.bucket = None
    
    def _build_object_name(self, ticker: str, filename: str) -> str:
        prefix = self.gcs_prefix.strip("/")
        if prefix:
            prefix = f"{prefix}/"
        return f"{prefix}{ticker}/{filename}"

    def store(self, file_path: str, ticker: str) -> str:
        """
        Store a file in Google Cloud Storage.
        
        Args:
            file_path: Path to the file to upload
            ticker: Stock ticker symbol for organizing
        
        Returns:
            GCS URI of the uploaded file
        """
        if not self.storage_client or not self.bucket:
            raise RuntimeError("GCS client not initialized")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.lower().endswith(".xlsx"):
            return self.store_excel(file_path, ticker)

        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            object_name = self._build_object_name(
                ticker,
                f"{name}_{timestamp}{ext}"
            )

            blob = self.bucket.blob(object_name)
            blob.upload_from_filename(file_path)

            gcs_uri = f"gs://{self.bucket_name}/{object_name}"
            print(f"Stored in GCS: {gcs_uri}")

            return gcs_uri
        except Exception as e:
            raise RuntimeError(f"Failed to upload to GCS: {e}")
    
    def store_json(self, data: Dict[str, Any], ticker: str) -> str:
        """
        Store JSON data directly to GCS.
        
        Args:
            data: Dictionary to store as JSON
            ticker: Stock ticker symbol
        
        Returns:
            GCS URI of the uploaded file
        """
        if not self.storage_client or not self.bucket:
            raise RuntimeError("GCS client not initialized")
        
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            object_name = self._build_object_name(
                ticker,
                f"{ticker}_analysis_{timestamp}.json"
            )

            json_bytes = json.dumps(data, indent=2).encode("utf-8")
            blob = self.bucket.blob(object_name)
            blob.upload_from_string(
                json_bytes,
                content_type="application/json"
            )
            
            gcs_uri = f"gs://{self.bucket_name}/{object_name}"
            print(f"Stored JSON in GCS: {gcs_uri}")
            
            return gcs_uri
            
        except Exception as e:
            raise RuntimeError(f"Failed to upload JSON to GCS: {e}")
    
    def list_files(self, ticker: Optional[str] = None) -> list:
        """
        List analysis files in GCS.
        
        Args:
            ticker: Optional ticker to filter by
        
        Returns:
            List of blob names
        """
        if not self.storage_client or not self.bucket:
            raise RuntimeError("GCS client not initialized")
        
        try:
            prefix = self.gcs_prefix.strip("/")
            if prefix:
                prefix = f"{prefix}/"
            if ticker:
                prefix = f"{prefix}{ticker}/"
            
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            return [blob.name for blob in blobs]
            
        except Exception as e:
            raise RuntimeError(f"Failed to list files from GCS: {e}")
    
    def download_file(self, blob_name: str, destination_path: str) -> str:
        """
        Download a file from GCS.
        
        Args:
            blob_name: Name of the blob in GCS
            destination_path: Local path to save the file
        
        Returns:
            Path to the downloaded file
        """
        if not self.storage_client or not self.bucket:
            raise RuntimeError("GCS client not initialized")
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.download_to_filename(destination_path)
            
            print(f"Downloaded from GCS: {blob_name} -> {destination_path}")
            
            return destination_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to download from GCS: {e}")

    def store_excel(self, file_path: str, ticker: str) -> str:
        """
        Store an Excel file in GCS.

        Args:
            file_path: Path to the Excel file
            ticker: Stock ticker symbol for organizing

        Returns:
            GCS URI of the uploaded file
        """
        if not self.storage_client or not self.bucket:
            raise RuntimeError("GCS client not initialized")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            object_name = self._build_object_name(
                ticker,
                f"{ticker}_excel_{timestamp}.xlsx"
            )
            blob = self.bucket.blob(object_name)
            blob.upload_from_filename(file_path)

            gcs_uri = f"gs://{self.bucket_name}/{object_name}"
            print(f"Stored Excel in GCS: {gcs_uri}")
            return gcs_uri
        except Exception as e:
            raise RuntimeError(f"Failed to upload Excel to GCS: {e}")
