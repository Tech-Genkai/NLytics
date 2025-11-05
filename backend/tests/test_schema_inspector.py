"""
Tests for Schema Inspector
"""
import pytest
import pandas as pd
import numpy as np
from services.schema_inspector import SchemaInspector


class TestSchemaInspector:
    """Test suite for SchemaInspector service"""
    
    @pytest.fixture
    def inspector(self):
        return SchemaInspector()
    
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing"""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 40, 45],
            'salary': [50000.0, 60000.0, 70000.0, 80000.0, 90000.0],
            'department': ['IT', 'HR', 'IT', 'Finance', 'IT'],
            'join_date': pd.to_datetime(['2020-01-01', '2019-06-15', '2021-03-20', '2018-11-05', '2022-07-30']),
            'active': [True, True, False, True, True]
        })
    
    def test_inspect_returns_schema_info(self, inspector, sample_df):
        """Test that inspect returns proper schema information"""
        result = inspector.inspect(sample_df, 'test.csv')
        
        assert result['filename'] == 'test.csv'
        assert result['row_count'] == 5
        assert result['column_count'] == 7
        assert 'columns' in result
        assert 'memory_usage_mb' in result
    
    def test_column_analysis(self, inspector, sample_df):
        """Test column analysis"""
        result = inspector.inspect(sample_df, 'test.csv')
        columns = result['columns']
        
        # Check that all columns are analyzed
        assert len(columns) == 7
        
        # Check column names
        column_names = [col['name'] for col in columns]
        assert 'id' in column_names
        assert 'name' in column_names
        assert 'age' in column_names
    
    def test_numeric_type_inference(self, inspector, sample_df):
        """Test numeric type inference"""
        result = inspector.inspect(sample_df, 'test.csv')
        columns = {col['name']: col for col in result['columns']}
        
        # Integer column
        assert columns['id']['inferred_type'] == 'integer'
        assert 'statistics' in columns['id']
        
        # Float column
        assert columns['salary']['inferred_type'] == 'float'
        assert columns['salary']['statistics']['min'] == 50000.0
        assert columns['salary']['statistics']['max'] == 90000.0
    
    def test_categorical_inference(self, inspector, sample_df):
        """Test categorical type inference"""
        result = inspector.inspect(sample_df, 'test.csv')
        columns = {col['name']: col for col in result['columns']}
        
        # Department should be categorical (3 unique values out of 5)
        assert columns['department']['inferred_type'] == 'categorical'
        assert columns['department']['unique_count'] == 3
    
    def test_missing_value_detection(self, inspector):
        """Test missing value detection"""
        df_with_nulls = pd.DataFrame({
            'col1': [1, 2, None, 4, 5],
            'col2': ['a', 'b', 'c', None, 'e']
        })
        
        result = inspector.inspect(df_with_nulls, 'test.csv')
        columns = {col['name']: col for col in result['columns']}
        
        assert columns['col1']['missing_count'] == 1
        assert columns['col1']['missing_percentage'] == 20.0
        assert columns['col2']['missing_count'] == 1
    
    def test_sample_values(self, inspector, sample_df):
        """Test sample value extraction"""
        result = inspector.inspect(sample_df, 'test.csv')
        columns = {col['name']: col for col in result['columns']}
        
        # Check that sample values are provided
        assert len(columns['name']['sample_values']) <= 3
        assert 'Alice' in columns['name']['sample_values']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
