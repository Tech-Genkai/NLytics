"""
Visualization and Insight Generation
Creates charts and narrative summaries
Phase 8: Insight Studio
"""
import pandas as pd
import json
from typing import Dict, List, Any, Optional


class InsightGenerator:
    """
    Generates insights, narratives, and visualization configs from results
    """
    
    def generate_insights(
        self,
        result: Any,
        query: str,
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Generate insights from execution results
        
        Returns:
            {
                'narrative': 'plain English summary',
                'visualization': {'type': 'bar', 'config': {...}},
                'key_findings': ['finding 1', 'finding 2'],
                'recommendations': ['next steps']
            }
        """
        insights = {
            'narrative': '',
            'visualization': None,
            'key_findings': [],
            'recommendations': [],
            'export_options': []
        }
        
        if isinstance(result, pd.DataFrame):
            insights.update(self._analyze_dataframe(result, query))
        elif isinstance(result, pd.Series):
            insights.update(self._analyze_series(result, query))
        elif isinstance(result, (int, float)):
            insights.update(self._analyze_scalar(result, query))
        
        # Add export options
        insights['export_options'] = self._get_export_options(result)
        
        return insights
    
    def _analyze_dataframe(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Analyze DataFrame results"""
        rows, cols = df.shape
        
        # Generate narrative
        if rows == 0:
            narrative_parts = ["No data matched your criteria."]
            findings = []
        elif rows == 1:
            narrative_parts = [f"Found {rows} result with {cols} columns."]
            findings = ["This is a unique result"]
        else:
            narrative_parts = [f"Showing **top {rows} results** with {cols} columns for comparison."]
            findings = []
            
            # Analyze numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                first_num_col = numeric_cols[0]
                max_val = df[first_num_col].max()
                min_val = df[first_num_col].min()
                mean_val = df[first_num_col].mean()
                
                # Get top and bottom performers
                top_idx = df[first_num_col].idxmax()
                bottom_idx = df[first_num_col].idxmin()
                
                # Try to get a name/label column
                label_cols = df.select_dtypes(include=['object']).columns
                metric_name = self._explain_metric(first_num_col)
                
                if len(label_cols) > 0:
                    label_col = label_cols[0]
                    top_label = df.loc[top_idx, label_col]
                    bottom_label = df.loc[bottom_idx, label_col]
                    
                    # More natural narrative
                    narrative_parts.append(
                        f"**{top_label}** leads with {metric_name.lower()} of **{max_val:.2f}**, "
                        f"while **{bottom_label}** has the lowest at **{min_val:.2f}**."
                    )
                    findings.append(f"Highest: {top_label} ({max_val:.2f})")
                    findings.append(f"Lowest: {bottom_label} ({min_val:.2f})")
                    findings.append(f"Average across all: {mean_val:.2f}")
                else:
                    narrative_parts.append(
                        f"Values range from **{min_val:.2f}** to **{max_val:.2f}**, "
                        f"averaging **{mean_val:.2f}**."
                    )
                    findings.append(f"Range: {min_val:.2f} - {max_val:.2f}")
                    findings.append(f"Average: {mean_val:.2f}")
        
        # Determine visualization type
        viz_type = self._suggest_visualization(df)
        
        recommendations = [
            "Export data for further analysis",
            "Filter results to focus on specific criteria",
            "Compare with other time periods or categories"
        ]
        
        return {
            'narrative': " ".join(narrative_parts),
            'visualization': viz_type,
            'key_findings': findings,
            'recommendations': recommendations[:2]
        }
    
    def _analyze_series(self, series: pd.Series, query: str) -> Dict[str, Any]:
        """Analyze Series results"""
        length = len(series)
        
        narrative = f"Found {length} values. "
        
        if series.dtype in ['int64', 'float64']:
            mean_val = series.mean()
            max_val = series.max()
            min_val = series.min()
            narrative += f"Values range from {min_val:.2f} to {max_val:.2f}, averaging {mean_val:.2f}."
        
        return {
            'narrative': narrative,
            'visualization': {'type': 'line', 'suitable': True},
            'key_findings': [f"Total items: {length}"],
            'recommendations': ["View distribution", "Compare trends"]
        }
    
    def _analyze_scalar(self, value: Any, query: str) -> Dict[str, Any]:
        """Analyze scalar results"""
        return {
            'narrative': f"The result is: **{value}**",
            'visualization': None,
            'key_findings': [f"Single value: {value}"],
            'recommendations': ["Break down by category", "Compare with other metrics"]
        }
    
    def _suggest_visualization(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Suggest appropriate visualization based on data shape"""
        rows, cols = df.shape
        
        if rows == 0 or cols == 0:
            return None
        
        # Check data types
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        # Suggest chart type based on data structure and include actual data
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            # Category + numeric = bar chart
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # Limit to top 10 for readability
            top_data = df.nlargest(min(10, len(df)), num_col)
            
            # Add metric explanation
            metric_explanation = self._explain_metric(num_col)
            
            return {
                'type': 'bar',
                'suitable': True,
                'x_column': cat_col,
                'y_column': num_col,
                'x_values': top_data[cat_col].tolist(),
                'y_values': top_data[num_col].tolist(),
                'description': f"{metric_explanation} by {cat_col}",
                'y_label': metric_explanation
            }
        elif len(numeric_cols) >= 2:
            # Multiple numerics = scatter or line
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            # Sample data if too large
            sample_df = df.sample(min(50, len(df)))
            
            return {
                'type': 'scatter',
                'suitable': True,
                'x_column': x_col,
                'y_column': y_col,
                'x_values': sample_df[x_col].tolist(),
                'y_values': sample_df[y_col].tolist(),
                'description': f"Scatter plot of {y_col} vs {x_col}"
            }
        elif len(numeric_cols) == 1:
            # Single numeric = histogram (bin the data)
            num_col = numeric_cols[0]
            values = df[num_col].dropna()
            
            # Create histogram bins
            hist, bin_edges = pd.cut(values, bins=10, retbins=True, duplicates='drop')
            bin_counts = hist.value_counts().sort_index()
            
            return {
                'type': 'bar',  # Use bar for histogram
                'suitable': True,
                'column': num_col,
                'x_values': [f"{edge:.2f}" for edge in bin_edges[:-1]],
                'y_values': bin_counts.tolist(),
                'description': f"Distribution of {num_col}",
                'y_label': 'Count'
            }
        
        return {'type': 'table', 'suitable': True}
    
    def _explain_metric(self, column_name: str) -> str:
        """Provide human-readable explanation for metric names"""
        explanations = {
            'growth': 'Growth Rate (%)',
            'growth_rate': 'Growth Rate (%)',
            'growth_pct': 'Growth Rate (%)',
            'avg_growth': 'Average Growth (%)',
            'average_daily_growth': 'Daily Growth Rate (%)',
            'daily_growth': 'Daily Growth Rate (%)',
            'price': 'Price ($)',
            'close_price': 'Closing Price ($)',
            'open_price': 'Opening Price ($)',
            'avg_price': 'Average Price ($)',
            'volume': 'Trading Volume',
            'market_cap': 'Market Capitalization ($)',
            'revenue': 'Revenue ($)',
            'profit': 'Profit ($)',
            'sales': 'Sales ($)',
            'count': 'Count',
            'total': 'Total',
            'percentage': 'Percentage (%)',
            'ratio': 'Ratio'
        }
        
        # Try exact match first
        col_lower = column_name.lower()
        if col_lower in explanations:
            return explanations[col_lower]
        
        # Try partial match
        for key, value in explanations.items():
            if key in col_lower:
                return value
        
        # Fallback: capitalize and add spaces
        return column_name.replace('_', ' ').title()
    
    def _get_export_options(self, result: Any) -> List[Dict[str, str]]:
        """Get available export options"""
        options = []
        
        if isinstance(result, (pd.DataFrame, pd.Series)):
            options.extend([
                {'format': 'csv', 'label': 'Download as CSV'},
                {'format': 'excel', 'label': 'Download as Excel'},
                {'format': 'json', 'label': 'Download as JSON'}
            ])
        
        return options
    
    def format_insights_for_display(self, insights: Dict[str, Any]) -> str:
        """Format insights as markdown - cleaner, more professional"""
        lines = ["### 📊 Data Overview\n"]
        
        # Narrative summary
        if insights.get('narrative'):
            lines.append(insights['narrative'])
            lines.append("")
        
        # Key findings - only if substantial
        if insights.get('key_findings') and len(insights['key_findings']) > 0:
            lines.append("**Key Statistics:**")
            for finding in insights['key_findings']:
                lines.append(f"- {finding}")
            lines.append("")
        
        return "\n".join(lines)
