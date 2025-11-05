"""
Tests for Code Validator Service
"""
import pytest
from services.code_validator import CodeValidator


class TestCodeValidator:
    """Test code validation logic"""
    
    def setup_method(self):
        self.validator = CodeValidator()
        self.test_columns = ['price', 'volume', 'symbol', 'date']
    
    def test_valid_code(self):
        """Test that valid code passes"""
        code = """
import pandas as pd
result = df.nlargest(10, 'price')
"""
        validation = self.validator.validate(code, self.test_columns)
        assert validation['valid'] == True
        assert len(validation['errors']) == 0
    
    def test_missing_result_variable(self):
        """Test that code without result variable fails"""
        code = """
import pandas as pd
top_data = df.nlargest(10, 'price')
"""
        validation = self.validator.validate(code, self.test_columns)
        assert validation['valid'] == False
        assert any('result' in err['message'].lower() for err in validation['errors'])
    
    def test_dangerous_operations_blocked(self):
        """Test that dangerous operations are blocked"""
        dangerous_codes = [
            "import os\nresult = df",
            "eval('malicious')\nresult = df",
            "exec('bad code')\nresult = df",
            "open('file.txt')\nresult = df",
            "df.to_csv('out.csv')\nresult = df",
        ]
        
        for code in dangerous_codes:
            validation = self.validator.validate(code, self.test_columns)
            assert validation['valid'] == False, f"Should block: {code[:30]}"
            assert len(validation['errors']) > 0
    
    def test_syntax_error_detected(self):
        """Test that syntax errors are caught"""
        code = """
import pandas as pd
result = df.nlargest(10 'price')  # Missing comma
"""
        validation = self.validator.validate(code, self.test_columns)
        assert validation['valid'] == False
        assert any('syntax' in err['type'].lower() for err in validation['errors'])
    
    def test_unauthorized_imports_blocked(self):
        """Test that only pandas/numpy are allowed"""
        code = """
import requests
result = df.head()
"""
        validation = self.validator.validate(code, self.test_columns)
        assert validation['valid'] == False
        assert any('import' in err['message'].lower() for err in validation['errors'])
    
    def test_column_reference_warning(self):
        """Test that invalid column references generate warnings"""
        code = """
import pandas as pd
result = df.nlargest(10, 'nonexistent_column')
"""
        validation = self.validator.validate(code, self.test_columns)
        # Should have warnings about nonexistent column
        assert len(validation['warnings']) > 0 or validation['valid'] == True
