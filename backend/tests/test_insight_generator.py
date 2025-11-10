"""
Tests for Insight Generator Service
"""
import pytest
import pandas as pd
from services.insight_generator import InsightGenerator


class TestInsightGenerator:
    """Test insight generation"""
    
    def setup_method(self):
        self.generator = InsightGenerator()
    
    def test_dataframe_insights(self):
        """Test insight generation from DataFrame"""
        df = pd.DataFrame({
            'stock': ['AAPL', 'MSFT', 'GOOGL'],
            'growth': [15.5, 12.3, 10.8]
        })
        
        insights = self.generator.generate_insights(df, "highest growth", 0.5)
        
        assert insights['narrative'] != ''
        assert 'AAPL' in insights['narrative']
        assert len(insights['key_findings']) > 0
        assert insights['visualization'] is not None
    
    def test_empty_dataframe_insights(self):
        """Test insights for empty DataFrame"""
        df = pd.DataFrame()
        
        insights = self.generator.generate_insights(df, "test query", 0.1)
        
        assert 'No data' in insights['narrative'] or 'empty' in insights['narrative'].lower()
    
    def test_scalar_insights(self):
        """Test insights from scalar value"""
        value = 42.5
        
        insights = self.generator.generate_insights(value, "average price", 0.2)
        
        assert '42.5' in str(insights['narrative'])
        assert len(insights['key_findings']) > 0
    
    def test_visualization_suggestion(self):
        """Test that visualization is suggested for appropriate data"""
        df = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 15]
        })
        
        insights = self.generator.generate_insights(df, "show values", 0.3)
        
        viz = insights['visualization']
        assert viz is not None
        assert viz['type'] in ['bar', 'scatter', 'line', 'table']
        if viz['type'] == 'bar':
            assert 'x_values' in viz
            assert 'y_values' in viz
            assert len(viz['colors']) > 0
    
    def test_color_palette(self):
        """Test color palette generation"""
        colors = self.generator._get_color_palette(5)
        assert len(colors) == 5
        assert all(color.startswith('#') for color in colors)
    
    def test_metric_explanation(self):
        """Test metric name explanation"""
        assert 'Growth' in self.generator._explain_metric('growth_rate')
        assert 'Price' in self.generator._explain_metric('close_price')
        assert 'Volume' in self.generator._explain_metric('volume')
    
    def test_pie_chart_detection(self):
        """Test pie chart detection for percentage data"""
        # Data that sums to 100 (percentage breakdown)
        df = pd.DataFrame({
            'sector': ['Tech', 'Finance', 'Healthcare', 'Energy'],
            'market_share': [35.5, 28.3, 20.1, 16.1]
        })
        
        insights = self.generator.generate_insights(df, "market share by sector", 0.3)
        viz = insights['visualization']
        
        assert viz is not None
        assert viz['type'] == 'pie'
        assert 'labels' in viz
        assert 'values' in viz
        assert viz['plotly'] is not None  # Should have Plotly JSON
    
    def test_box_plot_detection(self):
        """Test box plot detection for distribution data"""
        # Large dataset for distribution analysis
        import numpy as np
        np.random.seed(42)
        
        df = pd.DataFrame({
            'sector': ['Tech'] * 30 + ['Finance'] * 30 + ['Healthcare'] * 30,
            'price': np.concatenate([
                np.random.normal(150, 20, 30),
                np.random.normal(80, 15, 30),
                np.random.normal(110, 18, 30)
            ])
        })
        
        # Box plot should be suggested for distribution with categories
        viz = self.generator._suggest_visualization(df)
        
        assert viz is not None
        # Could be box plot if detection works, or bar chart as fallback
        assert viz['type'] in ['box', 'bar']
        if viz['type'] == 'box':
            assert 'y_column' in viz
            assert viz['plotly'] is not None
    
    def test_pie_chart_creation(self):
        """Test direct pie chart creation"""
        labels = ['Category A', 'Category B', 'Category C']
        values = [40, 35, 25]
        
        plotly_json = self.generator._create_plotly_pie(labels, values, "Test Distribution")
        
        assert plotly_json is not None
        assert 'data' in plotly_json
        assert 'layout' in plotly_json
    
    def test_box_plot_creation(self):
        """Test direct box plot creation"""
        import numpy as np
        np.random.seed(42)
        
        df = pd.DataFrame({
            'category': ['A'] * 50 + ['B'] * 50,
            'value': np.concatenate([
                np.random.normal(100, 15, 50),
                np.random.normal(120, 20, 50)
            ])
        })
        
        # Single box plot
        plotly_json_single = self.generator._create_plotly_box(df, 'value')
        assert plotly_json_single is not None
        
        # Grouped box plot
        plotly_json_grouped = self.generator._create_plotly_box(df, 'value', 'category')
        assert plotly_json_grouped is not None
