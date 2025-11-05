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
