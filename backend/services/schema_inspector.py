"""
Schema Inspector Service
Analyzes uploaded datasets and generates schema information
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any


class SchemaInspector:
    """Inspects and analyzes dataset schemas"""
    
    def inspect(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """
        Generate comprehensive schema information from a DataFrame
        """
        schema_info = {
            'filename': filename,
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': self._analyze_columns(df),
            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        }
        
        return schema_info
    
    def _analyze_columns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze each column in the dataset"""
        columns = []
        
        for col in df.columns:
            col_info = {
                'name': col,
                'dtype': str(df[col].dtype),
                'inferred_type': self._infer_type(df[col]),
                'missing_count': int(df[col].isna().sum()),
                'missing_percentage': round((df[col].isna().sum() / len(df)) * 100, 2),
                'unique_count': int(df[col].nunique()),
                'sample_values': self._get_sample_values(df[col])
            }
            
            # Add numeric statistics if applicable
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info['statistics'] = {
                    'min': float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    'max': float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    'mean': float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    'median': float(df[col].median()) if not pd.isna(df[col].median()) else None
                }
            
            columns.append(col_info)
        
        return columns
    
    def _infer_type(self, series: pd.Series) -> str:
        """Infer the semantic type of a column"""
        if pd.api.types.is_numeric_dtype(series):
            if pd.api.types.is_integer_dtype(series):
                return 'integer'
            return 'float'
        
        if pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'
        
        if pd.api.types.is_bool_dtype(series):
            return 'boolean'
        
        # Check if it could be a date string
        non_null = series.dropna()
        if len(non_null) > 0:
            try:
                pd.to_datetime(non_null.head(10), format='mixed')
                return 'date_string'
            except:
                pass
        
        # Check if categorical
        unique_ratio = series.nunique() / len(series)
        if unique_ratio < 0.05:  # Less than 5% unique values
            return 'categorical'
        
        return 'text'
    
    def _get_sample_values(self, series: pd.Series, n: int = 3) -> List[Any]:
        """Get sample non-null values from the series"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return []
        
        samples = non_null.head(n).tolist()
        # Convert to native Python types for JSON serialization
        return [self._convert_to_native_type(v) for v in samples]
    
    def _convert_to_native_type(self, value: Any) -> Any:
        """Convert numpy/pandas types to native Python types"""
        if pd.isna(value):
            return None
        if isinstance(value, (np.integer, np.floating)):
            return float(value)
        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        return str(value)
