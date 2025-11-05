"""
Data Preprocessing Service
Handles data cleaning, normalization, and quality analysis
Phase 2: Preprocessing
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import re
from datetime import datetime, timezone


class DataPreprocessor:
    """
    Comprehensive data preprocessing and cleaning service
    """
    
    def __init__(self):
        self.preprocessing_log = []
    
    def preprocess(self, df: pd.DataFrame, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Main preprocessing pipeline
        Returns: (cleaned_df, preprocessing_manifest)
        """
        manifest = {
            'filename': filename,
            'original_shape': df.shape,
            'preprocessing_timestamp': datetime.now(timezone.utc).isoformat(),
            'steps_applied': [],
            'issues_found': [],
            'recommendations': []
        }
        
        self.preprocessing_log = []
        
        # Create a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Step 1: Normalize column names
        cleaned_df, column_changes = self._normalize_column_names(cleaned_df)
        if column_changes:
            manifest['steps_applied'].append('column_name_normalization')
            manifest['column_changes'] = column_changes
        
        # Step 2: Detect and parse dates
        cleaned_df, date_columns = self._normalize_dates(cleaned_df)
        if date_columns:
            manifest['steps_applied'].append('date_normalization')
            manifest['date_columns'] = date_columns
        
        # Step 3: Clean numeric columns
        cleaned_df, numeric_issues = self._clean_numeric_columns(cleaned_df)
        if numeric_issues:
            manifest['issues_found'].extend(numeric_issues)
        
        # Step 4: Detect duplicates
        dup_info = self._detect_duplicates(cleaned_df)
        if dup_info['duplicate_count'] > 0:
            manifest['issues_found'].append({
                'type': 'duplicates',
                'details': dup_info
            })
            manifest['recommendations'].append(
                f"Found {dup_info['duplicate_count']} duplicate rows. Consider removing duplicates."
            )
        
        # Step 5: Analyze missing data patterns
        missing_info = self._analyze_missing_data(cleaned_df)
        if missing_info['total_missing'] > 0:
            manifest['issues_found'].append({
                'type': 'missing_data',
                'details': missing_info
            })
            manifest['recommendations'].extend(missing_info['recommendations'])
        
        # Step 6: Detect outliers
        outlier_info = self._detect_outliers(cleaned_df)
        if outlier_info['columns_with_outliers']:
            manifest['issues_found'].append({
                'type': 'outliers',
                'details': outlier_info
            })
        
        manifest['final_shape'] = cleaned_df.shape
        manifest['preprocessing_log'] = self.preprocessing_log
        
        return cleaned_df, manifest
    
    def _normalize_column_names(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """
        Normalize column names to snake_case and remove special characters
        """
        changes = {}
        new_columns = []
        
        for col in df.columns:
            # Convert to string
            col_str = str(col)
            
            # Store original
            original = col_str
            
            # Convert to lowercase
            normalized = col_str.lower()
            
            # Replace spaces and special characters with underscore
            normalized = re.sub(r'[^\w\s]', '', normalized)
            normalized = re.sub(r'\s+', '_', normalized)
            
            # Remove multiple underscores
            normalized = re.sub(r'_+', '_', normalized)
            
            # Remove leading/trailing underscores
            normalized = normalized.strip('_')
            
            # If empty, use generic name
            if not normalized:
                normalized = f'column_{len(new_columns)}'
            
            # Handle duplicates
            if normalized in new_columns:
                count = 1
                while f"{normalized}_{count}" in new_columns:
                    count += 1
                normalized = f"{normalized}_{count}"
            
            new_columns.append(normalized)
            
            if original != normalized:
                changes[original] = normalized
                self.preprocessing_log.append(f"Renamed column: '{original}' → '{normalized}'")
        
        df.columns = new_columns
        return df, changes
    
    def _normalize_dates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, str]]]:
        """
        Detect and normalize date columns
        """
        date_columns = []
        
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_columns.append({
                    'column': col,
                    'format': 'datetime64',
                    'action': 'already_datetime'
                })
                continue
            
            # Try to parse as date for object columns
            if df[col].dtype == 'object':
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    try:
                        # Try parsing a sample
                        sample = non_null.head(min(10, len(non_null)))
                        parsed = pd.to_datetime(sample, errors='coerce', format='mixed')
                        
                        # If most values parse successfully, convert the column
                        success_rate = parsed.notna().sum() / len(sample)
                        if success_rate > 0.8:
                            df[col] = pd.to_datetime(df[col], errors='coerce', format='mixed')
                            date_columns.append({
                                'column': col,
                                'format': 'parsed_from_string',
                                'action': 'converted_to_datetime'
                            })
                            self.preprocessing_log.append(f"Converted '{col}' to datetime")
                    except:
                        pass
        
        return df, date_columns
    
    def _clean_numeric_columns(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Clean numeric columns (remove non-numeric characters, convert types)
        """
        issues = []
        
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    # Remove common non-numeric characters
                    cleaned = df[col].astype(str).str.replace(r'[$,]', '', regex=True)
                    numeric = pd.to_numeric(cleaned, errors='coerce')
                    
                    # If most values are numeric, convert
                    non_null_original = df[col].notna().sum()
                    non_null_converted = numeric.notna().sum()
                    
                    if non_null_converted > 0 and non_null_converted / non_null_original > 0.8:
                        df[col] = numeric
                        self.preprocessing_log.append(f"Converted '{col}' to numeric")
                        
                        if non_null_converted < non_null_original:
                            issues.append({
                                'type': 'numeric_conversion_loss',
                                'column': col,
                                'values_lost': non_null_original - non_null_converted
                            })
                except:
                    pass
        
        return df, issues
    
    def _detect_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect duplicate rows
        """
        duplicates = df.duplicated()
        duplicate_count = duplicates.sum()
        
        return {
            'duplicate_count': int(duplicate_count),
            'duplicate_percentage': round((duplicate_count / len(df)) * 100, 2),
            'unique_rows': len(df) - duplicate_count
        }
    
    def _analyze_missing_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze missing data patterns
        """
        total_cells = df.size
        total_missing = df.isna().sum().sum()
        
        column_missing = []
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                column_missing.append({
                    'column': col,
                    'missing_count': int(missing_count),
                    'missing_percentage': round((missing_count / len(df)) * 100, 2)
                })
        
        # Sort by missing percentage
        column_missing.sort(key=lambda x: x['missing_percentage'], reverse=True)
        
        recommendations = []
        for col_info in column_missing:
            if col_info['missing_percentage'] > 50:
                recommendations.append(
                    f"Column '{col_info['column']}' has {col_info['missing_percentage']}% missing data. "
                    "Consider removing this column or investigating why data is missing."
                )
            elif col_info['missing_percentage'] > 10:
                recommendations.append(
                    f"Column '{col_info['column']}' has {col_info['missing_percentage']}% missing data. "
                    "Consider imputation or careful handling."
                )
        
        return {
            'total_missing': int(total_missing),
            'missing_percentage': round((total_missing / total_cells) * 100, 2),
            'columns_with_missing': column_missing,
            'recommendations': recommendations
        }
    
    def _detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect outliers in numeric columns using IQR method
        """
        outlier_info = {
            'columns_with_outliers': [],
            'total_outliers': 0
        }
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            non_null = df[col].dropna()
            if len(non_null) < 4:  # Need at least 4 values for IQR
                continue
            
            Q1 = non_null.quantile(0.25)
            Q3 = non_null.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = ((non_null < lower_bound) | (non_null > upper_bound)).sum()
            
            if outliers > 0:
                outlier_info['columns_with_outliers'].append({
                    'column': col,
                    'outlier_count': int(outliers),
                    'outlier_percentage': round((outliers / len(non_null)) * 100, 2),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound)
                })
                outlier_info['total_outliers'] += outliers
        
        return outlier_info
    
    def generate_health_report(self, manifest: Dict[str, Any]) -> str:
        """
        Generate a human-readable health report from the manifest
        """
        report_lines = []
        
        report_lines.append("### 📊 Data Health Report\n")
        report_lines.append(f"**Dataset:** {manifest['filename']}")
        report_lines.append(f"**Original Size:** {manifest['original_shape'][0]:,} rows × {manifest['original_shape'][1]} columns")
        report_lines.append(f"**Final Size:** {manifest['final_shape'][0]:,} rows × {manifest['final_shape'][1]} columns\n")
        
        # Steps applied
        if manifest['steps_applied']:
            report_lines.append("**Preprocessing Steps Applied:**")
            for step in manifest['steps_applied']:
                report_lines.append(f"✓ {step.replace('_', ' ').title()}")
            report_lines.append("")
        
        # Issues found
        if manifest['issues_found']:
            report_lines.append("**⚠️ Issues Detected:**")
            for issue in manifest['issues_found']:
                issue_type = issue['type'].replace('_', ' ').title()
                report_lines.append(f"\n**{issue_type}:**")
                
                if issue['type'] == 'duplicates':
                    report_lines.append(f"- Found {issue['details']['duplicate_count']} duplicate rows "
                                      f"({issue['details']['duplicate_percentage']}%)")
                
                elif issue['type'] == 'missing_data':
                    report_lines.append(f"- Total missing values: {issue['details']['total_missing']} "
                                      f"({issue['details']['missing_percentage']}%)")
                    if issue['details']['columns_with_missing']:
                        report_lines.append("- Most affected columns:")
                        for col_info in issue['details']['columns_with_missing'][:5]:
                            report_lines.append(f"  • {col_info['column']}: {col_info['missing_percentage']}% missing")
                
                elif issue['type'] == 'outliers':
                    report_lines.append(f"- Found outliers in {len(issue['details']['columns_with_outliers'])} columns")
                    for col_info in issue['details']['columns_with_outliers'][:3]:
                        report_lines.append(f"  • {col_info['column']}: {col_info['outlier_count']} outliers "
                                          f"({col_info['outlier_percentage']}%)")
            report_lines.append("")
        
        # Recommendations
        if manifest['recommendations']:
            report_lines.append("**💡 Recommendations:**")
            for i, rec in enumerate(manifest['recommendations'][:5], 1):
                report_lines.append(f"{i}. {rec}")
            report_lines.append("")
        
        # Summary
        issue_count = len(manifest['issues_found'])
        if issue_count == 0:
            report_lines.append("✅ **Your data looks great!** No major issues detected.")
        elif issue_count <= 2:
            report_lines.append("⚠️ **Minor issues detected.** Your data is mostly clean but could benefit from some attention.")
        else:
            report_lines.append("🔧 **Multiple issues detected.** Consider addressing these before analysis.")
        
        return "\n".join(report_lines)

