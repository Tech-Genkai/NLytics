"""
File Handler Service
Handles file uploads, validation, and loading
"""
import pandas as pd
import os
from typing import Optional


class FileHandler:
    """Manages file operations for uploaded datasets"""
    
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
    
    def load_file(self, file_path: str) -> pd.DataFrame:
        """
        Load a file into a pandas DataFrame
        Supports CSV and Excel formats
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == '.csv':
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
                try:
                    return pd.read_csv(file_path, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode CSV file with supported encodings")
        
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def validate_file_size(self, file_path: str, max_size_mb: int = 50) -> bool:
        """Check if file size is within limits"""
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        return file_size_mb <= max_size_mb
    
    def get_file_info(self, file_path: str) -> dict:
        """Get basic file information"""
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        return {
            'name': file_name,
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'path': file_path
        }
