"""
Visualization and Insight Generation
Creates charts and narrative summaries with Plotly support
Phase 8: Insight Studio
"""
import pandas as pd
import json
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px


class InsightGenerator:
    """
    Generates insights, narratives, and visualization configs from results
    """
    
    def generate_insights(
        self,
        result: Any,
        query: str,
        execution_time: float,
        requested_chart_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate insights from execution results
        
        Args:
            result: The execution result (DataFrame, Series, scalar, etc.)
            query: The original user query
            execution_time: How long execution took
            requested_chart_type: Explicitly requested chart type (pie, bar, scatter, etc.)
        
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
            insights.update(self._analyze_dataframe(result, query, requested_chart_type))
        elif isinstance(result, pd.Series):
            insights.update(self._analyze_series(result, query))
        elif isinstance(result, dict):
            insights.update(self._analyze_dict(result, query))
        elif isinstance(result, (int, float)):
            insights.update(self._analyze_scalar(result, query))
        else:
            # For any other type (list, tuple, str, bool, None, numpy array, etc.)
            # Just provide basic info - let AI Answer Synthesizer handle the explanation
            insights.update(self._analyze_generic(result, query))
        
        # Add export options
        insights['export_options'] = self._get_export_options(result)
        
        return insights
    
    def _analyze_dataframe(self, df: pd.DataFrame, query: str, requested_chart_type: Optional[str] = None) -> Dict[str, Any]:
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
                    
                    # Neutral narrative language
                    narrative_parts.append(
                        f"**{top_label}** has the highest {metric_name.lower()} at **{max_val:.2f}**, "
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
        
        # Determine visualization type - RESPECT EXPLICIT REQUEST!
        if requested_chart_type:
            # User explicitly requested a chart type - create it!
            viz_type = self._create_requested_visualization(df, requested_chart_type)
        else:
            # Auto-detect appropriate visualization
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
    
    def _analyze_dict(self, result_dict: dict, query: str) -> Dict[str, Any]:
        """Analyze dictionary results - often contains multiple DataFrames/Series"""
        narrative_parts = []
        findings = []
        
        # Count what's in the dictionary
        num_keys = len(result_dict)
        narrative_parts.append(f"Analysis contains **{num_keys} components**:")
        
        # Analyze each key-value pair
        for key, value in result_dict.items():
            key_display = str(key).replace('_', ' ').title()
            
            if isinstance(value, pd.DataFrame):
                rows, cols = value.shape
                narrative_parts.append(f"\n**{key_display}**: {rows} rows × {cols} columns")
                
                # Get summary stats for first numeric column
                numeric_cols = value.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    first_col = numeric_cols[0]
                    mean_val = value[first_col].mean()
                    findings.append(f"{key_display} - Average {first_col}: {mean_val:.2f}")
                
            elif isinstance(value, pd.Series):
                length = len(value)
                narrative_parts.append(f"\n**{key_display}**: {length} values")
                
                if value.dtype in ['int64', 'float64']:
                    mean_val = value.mean()
                    findings.append(f"{key_display} - Average: {mean_val:.2f}")
                
            elif isinstance(value, (int, float)):
                narrative_parts.append(f"\n**{key_display}**: {value:.2f}")
                findings.append(f"{key_display}: {value:.2f}")
            
            else:
                narrative_parts.append(f"\n**{key_display}**: {type(value).__name__}")
        
        # Try to create a visualization from the first DataFrame in the dict
        viz = None
        for key, value in result_dict.items():
            if isinstance(value, pd.DataFrame):
                viz = self._suggest_visualization(value)
                break
        
        return {
            'narrative': " ".join(narrative_parts),
            'visualization': viz,
            'key_findings': findings[:5],  # Top 5 findings
            'recommendations': ["Examine individual components", "Export for detailed analysis"]
        }
    
    def _analyze_scalar(self, value: Any, query: str) -> Dict[str, Any]:
        """Analyze scalar results"""
        return {
            'narrative': f"The result is: **{value}**",
            'visualization': None,
            'key_findings': [f"Single value: {value}"],
            'recommendations': ["Break down by category", "Compare with other metrics"]
        }
    
    def _analyze_generic(self, result: Any, query: str) -> Dict[str, Any]:
        """
        Generic analyzer for any result type not specifically handled.
        Provides basic info and lets AI Answer Synthesizer do the interpretation.
        
        Handles: list, tuple, str, bool, None, numpy arrays, and any unknown types
        """
        result_type = type(result).__name__
        findings = [f"Type: {result_type}"]
        
        # Provide basic info based on type
        if result is None:
            narrative = "**No result returned.** The query completed but did not produce output."
        elif isinstance(result, bool):
            narrative = f"The result is: **{result}** {'✓' if result else '✗'}"
        elif isinstance(result, str):
            length = len(result)
            if length < 100:
                narrative = f"The result is: **\"{result}\"**"
            else:
                narrative = f"Result is a text string with **{length} characters**."
                findings.append(f"{length} chars")
        elif isinstance(result, (list, tuple)):
            length = len(result)
            narrative = f"Found **{length} items** in the result."
            findings.append(f"{length} items")
        elif hasattr(result, 'shape'):  # numpy array
            narrative = f"Result is an array with shape **{result.shape}**."
            findings.append(f"Shape: {result.shape}")
        elif hasattr(result, '__len__'):
            length = len(result)
            narrative = f"Result has **{length} elements**."
            findings.append(f"{length} elements")
        else:
            # Unknown type - basic display
            try:
                result_str = str(result)[:100]
                narrative = f"Result: `{result_str}`"
            except:
                narrative = f"Result type: **{result_type}**"
        
        return {
            'narrative': narrative,
            'visualization': None,
            'key_findings': findings,
            'recommendations': []  # Let AI answer provide the interpretation
        }
    
    def _create_line_chart(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Create line chart for time-series data
        
        Handles:
        - Date-based time series (date column + value columns)
        - Multi-entity time series (date + ticker + values)
        """
        # Look for date/time column (could be index or column)
        date_col = None
        
        # Check if index looks like dates
        if hasattr(df.index, 'name') and df.index.name and ('date' in str(df.index.name).lower() or 'time' in str(df.index.name).lower()):
            date_col = df.index.name
            df_to_use = df.reset_index()  # Make index into a column
            # Convert to datetime if it's not already
            if df_to_use[date_col].dtype == 'object':
                df_to_use[date_col] = pd.to_datetime(df_to_use[date_col])
        elif df.index.dtype == 'datetime64[ns]' or str(df.index.dtype).startswith('datetime'):
            # Index is datetime but unnamed
            date_col = 'date'
            df_to_use = df.reset_index()
            df_to_use.columns = [date_col] + df_to_use.columns.tolist()[1:]
        else:
            # Look for date column in columns
            df_to_use = df.copy()
            for col in df_to_use.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    date_col = col
                    # Convert to datetime if it's not already
                    if df_to_use[date_col].dtype == 'object':
                        df_to_use[date_col] = pd.to_datetime(df_to_use[date_col])
                    break
        
        if not date_col:
            # No date column - can't create line chart
            return None
        
        # Check if data is already pivoted (columns are entities) or needs pivoting
        numeric_cols = df_to_use.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df_to_use.select_dtypes(include=['object']).columns.tolist()
        
        # Remove date column from categoricals if it's there
        categorical_cols = [c for c in categorical_cols if c != date_col]
        
        if len(categorical_cols) > 0:
            # Un-pivoted data (has ticker/entity column)
            # Example: date | ticker | value
            entity_col = categorical_cols[0]  # ticker, company, etc.
            
            if len(numeric_cols) == 0:
                return None
            
            value_col = numeric_cols[0]  # market_cap, price, etc.
            
            # Pivot the data: date as index, ticker as columns, value as values
            try:
                pivoted = df_to_use.pivot_table(
                    index=date_col,
                    columns=entity_col,
                    values=value_col,
                    aggfunc='mean'  # Handle duplicates
                )
                
                # Limit to top N entities by final value
                final_values = pivoted.iloc[-1].sort_values(ascending=False)
                top_entities = final_values.head(10).index.tolist()
                pivoted = pivoted[top_entities]
                
                # Create Plotly line chart
                plotly_json = self._create_plotly_line(pivoted, value_col)
                
                return {
                    'type': 'line',
                    'suitable': True,
                    'x_column': date_col,
                    'y_column': value_col,
                    'entities': top_entities,
                    'description': f"{self._explain_metric(value_col)} over time",
                    'plotly': plotly_json
                }
            except Exception as e:
                print(f"⚠️ Failed to pivot data for line chart: {e}")
                return None
        
        else:
            # Already pivoted data - columns are different entities
            # Example: date | AAPL | MSFT | GOOGL
            if len(numeric_cols) == 0:
                return None
            
            # Use df_to_use, date should now be a column
            try:
                # Set date as index for plotting
                df_plot = df_to_use.set_index(date_col)
                
                # Limit to 10 series for readability
                if len(df_plot.columns) > 10:
                    # Take top 10 by final value
                    final_values = df_plot.iloc[-1].sort_values(ascending=False)
                    top_cols = final_values.head(10).index.tolist()
                    df_plot = df_plot[top_cols]
                
                plotly_json = self._create_plotly_line(df_plot, "Value")
                
                return {
                    'type': 'line',
                    'suitable': True,
                    'x_column': date_col,
                    'y_column': 'Value',
                    'entities': df_plot.columns.tolist(),
                    'description': "Trend over time",
                    'plotly': plotly_json
                }
            except Exception as e:
                print(f"⚠️ Failed to create line chart: {e}")
                import traceback
                traceback.print_exc()
                return None
    
    def _create_plotly_line(self, df, y_label):
        """Create Plotly line chart from pivoted DataFrame"""
        try:
            fig = go.Figure()
            
            colors = self._get_color_palette(len(df.columns))
            
            # Add a line for each column (entity)
            for i, col in enumerate(df.columns):
                y_values = df[col].tolist()
                
                fig.add_trace(go.Scatter(
                    x=df.index.tolist(),  # Convert index to list explicitly
                    y=y_values,  # Already converted to list above
                    mode='lines+markers',
                    name=str(col),
                    line=dict(color=colors[i], width=2),
                    marker=dict(size=6)
                ))
            
            fig.update_layout(
                title=dict(text=f"{self._explain_metric(y_label)} Over Time", font=dict(size=16)),
                xaxis_title="Date",
                yaxis_title=self._explain_metric(y_label),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.05
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial, sans-serif", size=12),
                margin=dict(l=50, r=150, t=80, b=50),
                height=400,
                hovermode='x unified'
            )
            
            fig.update_xaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            
            return fig.to_json()
        except Exception as e:
            print(f"⚠️ Plotly line chart generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_color_palette(self, count: int) -> List[str]:
        """Generate vibrant, professional color palette for charts"""
        # Professional, vibrant color palette
        base_colors = [
            '#3b82f6',  # Blue
            '#10b981',  # Green
            '#f59e0b',  # Amber
            '#ef4444',  # Red
            '#8b5cf6',  # Purple
            '#ec4899',  # Pink
            '#14b8a6',  # Teal
            '#f97316',  # Orange
            '#6366f1',  # Indigo
            '#84cc16',  # Lime
            '#06b6d4',  # Cyan
            '#f43f5e',  # Rose
        ]
        
        if count <= len(base_colors):
            return base_colors[:count]
        
        # If more colors needed, cycle through with slight variations
        colors = []
        for i in range(count):
            colors.append(base_colors[i % len(base_colors)])
        return colors
    
    def _create_requested_visualization(self, df: pd.DataFrame, chart_type: str) -> Optional[Dict[str, Any]]:
        """
        Create the specific visualization type requested by the user
        
        Args:
            df: DataFrame with data
            chart_type: Requested chart type (pie, bar, scatter, line, box)
        
        Returns:
            Visualization config dict or None
        """
        rows, cols = df.shape
        
        if rows == 0 or cols == 0:
            return None
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        # Normalize chart type
        chart_type = chart_type.lower() if chart_type else ''
        
        if chart_type == 'pie' and len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            # Create pie chart
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # Limit to reasonable number for pie chart
            display_df = df.head(min(10, len(df)))
            colors = self._get_color_palette(len(display_df))
            
            plotly_json = self._create_plotly_pie(
                display_df[cat_col].tolist(),
                display_df[num_col].tolist(),
                f"{self._explain_metric(num_col)} by {cat_col}"
            )
            
            return {
                'type': 'pie',
                'suitable': True,
                'category_column': cat_col,
                'value_column': num_col,
                'labels': display_df[cat_col].tolist(),
                'values': display_df[num_col].tolist(),
                'colors': colors,
                'description': f"{self._explain_metric(num_col)} by {cat_col}",
                'plotly': plotly_json
            }
        
        elif chart_type == 'bar' and len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            # Create bar chart
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # IMPORTANT: For time-series data, group by category first!
            # Check if we have multiple rows per category (time-series)
            if df[cat_col].duplicated().any():
                # Time-series data - aggregate by category
                aggregated = df.groupby(cat_col)[num_col].sum().reset_index()
                top_data = aggregated.nlargest(min(10, len(aggregated)), num_col)
            else:
                # Already aggregated - just sort
                top_data = df.nlargest(min(10, len(df)), num_col)
            
            colors = self._get_color_palette(len(top_data))
            metric_explanation = self._explain_metric(num_col)
            
            plotly_json = self._create_plotly_bar(
                top_data[cat_col].tolist(),
                top_data[num_col].tolist(),
                colors,
                metric_explanation,
                cat_col
            )
            
            return {
                'type': 'bar',
                'suitable': True,
                'x_column': cat_col,
                'y_column': num_col,
                'x_values': top_data[cat_col].tolist(),
                'y_values': top_data[num_col].tolist(),
                'colors': colors,
                'description': f"{metric_explanation} by {cat_col}",
                'y_label': metric_explanation,
                'plotly': plotly_json
            }
        
        elif chart_type == 'line':
            # Create line chart for time-series data
            return self._create_line_chart(df)
        
        elif chart_type == 'scatter' and len(numeric_cols) >= 2:
            # Create scatter plot
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            sample_df = df.sample(min(50, len(df)))
            
            plotly_json = self._create_plotly_scatter(
                sample_df[x_col].tolist(),
                sample_df[y_col].tolist(),
                x_col,
                y_col
            )
            
            return {
                'type': 'scatter',
                'suitable': True,
                'x_column': x_col,
                'y_column': y_col,
                'x_values': sample_df[x_col].tolist(),
                'y_values': sample_df[y_col].tolist(),
                'point_color': '#3b82f6',
                'description': f"Scatter plot of {y_col} vs {x_col}",
                'plotly': plotly_json
            }
        
        elif chart_type == 'box' and len(numeric_cols) >= 1:
            # Create box plot
            num_col = numeric_cols[0]
            
            if len(categorical_cols) >= 1:
                cat_col = categorical_cols[0]
                num_categories = df[cat_col].nunique()
                
                if num_categories <= 10:
                    plotly_json = self._create_plotly_box(
                        df, num_col, cat_col,
                        f"Distribution of {num_col} by {cat_col}"
                    )
                    
                    return {
                        'type': 'box',
                        'suitable': True,
                        'y_column': num_col,
                        'x_column': cat_col,
                        'description': f"Distribution of {num_col} by {cat_col}",
                        'plotly': plotly_json
                    }
            else:
                # Single box plot
                plotly_json = self._create_plotly_box(
                    df, num_col,
                    title=f"Distribution of {num_col}"
                )
                
                return {
                    'type': 'box',
                    'suitable': True,
                    'y_column': num_col,
                    'description': f"Distribution of {num_col}",
                    'plotly': plotly_json
                }
        
        # If requested chart type can't be created with available data,
        # fall back to auto-detection
        print(f"⚠️ Requested chart type '{chart_type}' couldn't be created with available data. Auto-detecting...")
        return self._suggest_visualization(df)
    
    def _suggest_visualization(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Suggest appropriate visualization based on data shape"""
        rows, cols = df.shape
        
        if rows == 0 or cols == 0:
            return None
        
        # DEBUG: Print dataframe info
        print(f"🔍 _suggest_visualization called:")
        print(f"   Shape: {rows}x{cols}")
        print(f"   Index type: {type(df.index)}")
        print(f"   Is DatetimeIndex? {isinstance(df.index, pd.DatetimeIndex)}")
        print(f"   Columns: {df.columns.tolist()[:5]}")
        print(f"   Dtypes: {df.dtypes.tolist()[:5]}")
        
        # Check data types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        print(f"   Numeric cols: {len(numeric_cols)}, Categorical: {len(categorical_cols)}")
        
        # **NEW: Pattern 0: Detect pivoted time-series data (line chart)**
        # Characteristics: datetime index + all numeric columns
        has_datetime_index = isinstance(df.index, pd.DatetimeIndex) or (
            len(df.index) > 0 and isinstance(df.index[0], (pd.Timestamp, str)) and 
            pd.api.types.is_datetime64_any_dtype(pd.to_datetime(df.index, errors='coerce'))
        )
        
        # Or check if first column looks like dates
        has_date_column = False
        date_col_name = None
        if len(df.columns) > 0:
            first_col = df.columns[0]
            if pd.api.types.is_datetime64_any_dtype(df[first_col]) or \
               (df[first_col].dtype == 'object' and 'date' in str(first_col).lower()):
                has_date_column = True
                date_col_name = first_col
        
        # If we have datetime index/column and multiple numeric columns → LINE CHART
        if (has_datetime_index or has_date_column) and len(numeric_cols) >= 1:
            # Time-series line chart with multiple series
            x_col = 'index' if has_datetime_index else date_col_name
            y_cols = [col for col in numeric_cols if col != date_col_name]  # All numeric cols except date
            
            # Limit to first 10 series if more
            if len(y_cols) > 10:
                y_cols = y_cols[:10]
            
            # Prepare pivoted DataFrame for line chart (index=dates, columns=series)
            if has_datetime_index:
                df_plot = df[y_cols].copy()
            else:
                df_plot = df.set_index(date_col_name)[y_cols].copy()
            
            plotly_json = self._create_plotly_line(df_plot, "Value")
            
            return {
                'type': 'line',
                'suitable': True,
                'x_column': x_col,
                'y_columns': y_cols,
                'description': f"Time series: {', '.join(y_cols[:3])}{'...' if len(y_cols) > 3 else ''}",
                'plotly': plotly_json
            }
        
        # Pattern 1: Check for percentage/ratio data (pie chart candidate)
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # If the numeric values look like percentages or proportions (sum to ~100 or ~1)
            # or represent parts of a whole, suggest pie chart
            total = df[num_col].sum()
            is_percentage = (95 < total < 105) or (0.95 < total < 1.05)
            is_small_categories = len(df) <= 10  # Pie works best with few categories
            
            # Keywords suggesting pie chart
            pie_keywords = ['percentage', 'percent', 'share', 'proportion', 'distribution', 
                           'composition', 'breakdown', 'split']
            has_pie_keyword = any(keyword in num_col.lower() for keyword in pie_keywords)
            
            if (is_percentage or has_pie_keyword) and is_small_categories:
                # Use pie/donut chart
                colors = self._get_color_palette(len(df))
                
                plotly_json = self._create_plotly_pie(
                    df[cat_col].tolist(),
                    df[num_col].tolist(),
                    f"{num_col} by {cat_col}"
                )
                
                return {
                    'type': 'pie',
                    'suitable': True,
                    'category_column': cat_col,
                    'value_column': num_col,
                    'labels': df[cat_col].tolist(),
                    'values': df[num_col].tolist(),
                    'colors': colors,
                    'description': f"{num_col} by {cat_col}",
                    'plotly': plotly_json
                }
        
        # Pattern 2: Single numeric column with many values = box plot (distribution)
        if len(numeric_cols) >= 1 and rows > 20:
            num_col = numeric_cols[0]
            
            # Check for distribution/outlier keywords
            dist_keywords = ['distribution', 'outlier', 'spread', 'range', 'variance']
            # Note: We can't check the query here, but the data pattern is good
            
            # If we have a categorical column, do grouped box plot
            if len(categorical_cols) >= 1:
                cat_col = categorical_cols[0]
                
                # Only do grouped box if reasonable number of categories
                num_categories = df[cat_col].nunique()
                if num_categories <= 10:
                    plotly_json = self._create_plotly_box(
                        df, num_col, cat_col,
                        f"Distribution of {num_col} by {cat_col}"
                    )
                    
                    return {
                        'type': 'box',
                        'suitable': True,
                        'y_column': num_col,
                        'x_column': cat_col,
                        'description': f"Distribution of {num_col} by {cat_col}",
                        'plotly': plotly_json
                    }
        
        # Pattern 3: Category + numeric = bar chart (existing logic)
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            # Category + numeric = bar chart
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # Limit to top 10 for readability
            top_data = df.nlargest(min(10, len(df)), num_col)
            
            # Add metric explanation
            metric_explanation = self._explain_metric(num_col)
            
            # Get colorful palette
            colors = self._get_color_palette(len(top_data))
            
            # Generate Plotly chart
            plotly_json = self._create_plotly_bar(
                top_data[cat_col].tolist(),
                top_data[num_col].tolist(),
                colors,
                metric_explanation,
                cat_col
            )
            
            return {
                'type': 'bar',
                'suitable': True,
                'x_column': cat_col,
                'y_column': num_col,
                'x_values': top_data[cat_col].tolist(),
                'y_values': top_data[num_col].tolist(),
                'colors': colors,
                'description': f"{metric_explanation} by {cat_col}",
                'y_label': metric_explanation,
                'plotly': plotly_json  # Plotly chart data
            }
        elif len(numeric_cols) >= 2:
            # Multiple numerics = scatter or line
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            # Sample data if too large
            sample_df = df.sample(min(50, len(df)))
            
            # Generate Plotly scatter chart
            plotly_json = self._create_plotly_scatter(
                sample_df[x_col].tolist(),
                sample_df[y_col].tolist(),
                x_col,
                y_col
            )
            
            return {
                'type': 'scatter',
                'suitable': True,
                'x_column': x_col,
                'y_column': y_col,
                'x_values': sample_df[x_col].tolist(),
                'y_values': sample_df[y_col].tolist(),
                'point_color': '#3b82f6',
                'description': f"Scatter plot of {y_col} vs {x_col}",
                'plotly': plotly_json
            }
        elif len(numeric_cols) == 1:
            # Single numeric = histogram (bin the data)
            num_col = numeric_cols[0]
            values = df[num_col].dropna()
            
            # Create histogram bins
            hist, bin_edges = pd.cut(values, bins=10, retbins=True, duplicates='drop')
            bin_counts = hist.value_counts().sort_index()
            
            # Gradient colors for histogram
            colors = self._get_color_palette(len(bin_counts))
            
            return {
                'type': 'bar',  # Use bar for histogram
                'suitable': True,
                'column': num_col,
                'x_values': [f"{edge:.2f}" for edge in bin_edges[:-1]],
                'y_values': bin_counts.tolist(),
                'colors': colors,
                'description': f"Distribution of {num_col}",
                'y_label': 'Count'
            }
        
        return {'type': 'table', 'suitable': True}
    
    def _create_plotly_bar(self, x_values, y_values, colors, y_label, x_label):
        """Create Plotly bar chart as JSON"""
        try:
            fig = go.Figure(data=[
                go.Bar(
                    x=x_values,
                    y=y_values,
                    marker=dict(
                        color=colors,
                        line=dict(color='rgba(0,0,0,0.2)', width=1)
                    ),
                    text=y_values,
                    texttemplate='%{text:.2f}',
                    textposition='outside'
                )
            ])
            
            fig.update_layout(
                title=dict(text=f"{y_label} by {x_label}", font=dict(size=16)),
                xaxis_title=x_label,
                yaxis_title=y_label,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial, sans-serif", size=12),
                margin=dict(l=50, r=50, t=80, b=50),
                height=400
            )
            
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            
            return fig.to_json()
        except Exception as e:
            print(f"⚠️ Plotly chart generation failed: {e}")
            return None
    
    def _create_plotly_scatter(self, x_values, y_values, x_label, y_label):
        """Create Plotly scatter plot as JSON"""
        try:
            fig = go.Figure(data=[
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color='#3b82f6',
                        opacity=0.7,
                        line=dict(color='white', width=1)
                    )
                )
            ])
            
            fig.update_layout(
                title=f"{y_label} vs {x_label}",
                xaxis_title=x_label,
                yaxis_title=y_label,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            
            fig.update_xaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            
            return fig.to_json()
        except Exception as e:
            print(f"⚠️ Plotly scatter generation failed: {e}")
            return None
    
    def _create_plotly_pie(self, labels, values, title):
        """Create Plotly pie/donut chart as JSON"""
        try:
            fig = go.Figure(data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,  # Donut chart (0 = full pie, 0.3 = donut)
                    textinfo='label+percent',
                    textposition='auto',
                    marker=dict(
                        colors=self._get_color_palette(len(labels)),
                        line=dict(color='white', width=2)
                    ),
                    hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percent: %{percent}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title=dict(text=title, font=dict(size=16)),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial, sans-serif", size=12),
                margin=dict(l=50, r=150, t=80, b=50),
                height=400
            )
            
            return fig.to_json()
        except Exception as e:
            print(f"⚠️ Plotly pie chart generation failed: {e}")
            return None
    
    def _create_plotly_box(self, df, y_column, x_column=None, title=None):
        """Create Plotly box plot for distribution analysis as JSON"""
        try:
            if x_column and x_column in df.columns:
                # Grouped box plot by category
                fig = go.Figure()
                categories = df[x_column].unique()
                colors = self._get_color_palette(len(categories))
                
                for i, category in enumerate(categories):
                    category_data = df[df[x_column] == category][y_column]
                    fig.add_trace(go.Box(
                        y=category_data,
                        name=str(category),
                        marker_color=colors[i],
                        boxmean='sd'  # Show mean and standard deviation
                    ))
                
                fig.update_layout(
                    title=title or f"Distribution of {y_column} by {x_column}",
                    yaxis_title=y_column,
                    xaxis_title=x_column,
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=400
                )
            else:
                # Single box plot
                fig = go.Figure(data=[
                    go.Box(
                        y=df[y_column],
                        name=y_column,
                        marker_color='#3b82f6',
                        boxmean='sd',
                        boxpoints='outliers'  # Show outlier points
                    )
                ])
                
                fig.update_layout(
                    title=title or f"Distribution of {y_column}",
                    yaxis_title=y_column,
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=400
                )
            
            fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            
            return fig.to_json()
        except Exception as e:
            print(f"⚠️ Plotly box plot generation failed: {e}")
            return None
    
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
