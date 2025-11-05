"""
Tests for Safe Executor Service
"""
import pytest
import pandas as pd
from services.safe_executor import SafeExecutor


class TestSafeExecutor:
    """Test safe code execution"""
    
    def setup_method(self):
        self.executor = SafeExecutor(timeout_seconds=5)
        self.test_df = pd.DataFrame({
            'price': [10, 20, 30, 40, 50],
            'volume': [100, 200, 300, 400, 500],
            'symbol': ['A', 'B', 'C', 'D', 'E']
        })
    
    def test_successful_execution(self):
        """Test that valid code executes successfully"""
        code = "result = df.nlargest(3, 'price')"
        result = self.executor.execute(code, self.test_df)
        
        assert result['success'] == True
        assert result['result'] is not None
        assert isinstance(result['result'], pd.DataFrame)
        assert len(result['result']) == 3
    
    def test_execution_returns_result(self):
        """Test that result variable is captured"""
        code = """
import pandas as pd
result = df['price'].sum()
"""
        result = self.executor.execute(code, self.test_df)
        
        assert result['success'] == True
        assert result['result'] == 150  # Sum of prices
    
    def test_error_handling(self):
        """Test that errors are caught properly"""
        code = "result = df['nonexistent_column'].sum()"
        result = self.executor.execute(code, self.test_df)
        
        assert result['success'] == False
        assert result['error'] is not None
        assert 'nonexistent_column' in result['error'].lower() or 'keyerror' in result['error'].lower()
    
    def test_dangerous_operations_restricted(self):
        """Test that dangerous operations are handled"""
        # Test division by zero is caught
        code = "result = 1 / 0"
        result = self.executor.execute(code, self.test_df)
        assert result['success'] == False
        assert 'division' in result['error'].lower() or 'zero' in result['error'].lower()
        
        # Test undefined variable is caught
        code = "result = undefined_variable"
        result = self.executor.execute(code, self.test_df)
        assert result['success'] == False
        assert 'nameerror' in result['error'].lower() or 'not defined' in result['error'].lower()
    
    def test_execution_time_tracked(self):
        """Test that execution time is tracked"""
        code = "result = df.head()"
        result = self.executor.execute(code, self.test_df)
        
        assert 'execution_time' in result
        assert result['execution_time'] >= 0
        assert result['execution_time'] < 5  # Should be fast
    
    def test_dataframe_not_modified(self):
        """Test that original dataframe is not modified"""
        original_len = len(self.test_df)
        code = "df['new_col'] = 999; result = df"
        
        result = self.executor.execute(code, self.test_df)
        
        # Original df should be unchanged
        assert len(self.test_df.columns) == 3
        assert 'new_col' not in self.test_df.columns
        
        # But result should have the new column
        assert result['success'] == True
        assert 'new_col' in result['result'].columns
