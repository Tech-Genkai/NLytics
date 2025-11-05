"""
Code Validator and Retry Logic
Validates generated code and provides structured error feedback
Phase 6: Assurance Loop
"""
import ast
import re
from typing import Dict, List, Any, Optional, Tuple


class CodeValidator:
    """
    Validates generated code for safety and correctness
    """
    
    def __init__(self):
        # Blacklisted operations for security
        self.blacklist_patterns = [
            r'\bopen\s*\(',
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'\b__import__\s*\(',
            r'\bcompile\s*\(',
            r'\bgetattr\s*\(',
            r'\bsetattr\s*\(',
            r'\bdelattr\s*\(',
            r'\bhasattr\s*\(',
            r'\bglobals\s*\(',
            r'\blocals\s*\(',
            r'\bvars\s*\(',
            r'\bdir\s*\(',
            r'\b__builtins__',
            r'\b__dict__',
            r'\b__class__',
            r'\b__bases__',
            r'\b__subclasses__',
            r'\bos\.',
            r'\bsys\.',
            r'\bsubprocess\.',
            r'\bimportlib\.',
            r'\.to_csv\(',
            r'\.to_excel\(',
            r'\.to_sql\(',
            r'\bread_\w+\(',
            r'\.read_',
            r'\.to_pickle\(',
            r'\.to_hdf\(',
            r'\bfile\s*\(',
        ]
        
        # Required patterns
        self.required_patterns = [
            (r'\bresult\s*=', 'Must assign final result to variable "result"'),
        ]
        
        # Allowed imports
        self.allowed_imports = {'pandas', 'numpy', 'pd', 'np'}
    
    def validate(
        self,
        code: str,
        df_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Validate generated code
        
        Returns:
            {
                'valid': bool,
                'errors': [{'type': 'security|syntax|logic', 'message': '...', 'line': 1}],
                'warnings': [{'message': '...', 'line': 1}],
                'score': 0-100
            }
        """
        errors = []
        warnings = []
        
        # Security checks
        security_errors = self._check_security(code)
        errors.extend(security_errors)
        
        # Syntax validation
        syntax_errors = self._check_syntax(code)
        errors.extend(syntax_errors)
        
        # Required patterns
        pattern_errors = self._check_required_patterns(code)
        errors.extend(pattern_errors)
        
        # Import validation
        import_errors = self._check_imports(code)
        errors.extend(import_errors)
        
        # Column references
        column_warnings = self._check_column_references(code, df_columns)
        warnings.extend(column_warnings)
        
        # Calculate score
        score = 100
        score -= len(errors) * 25
        score -= len(warnings) * 5
        score = max(0, score)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'score': score
        }
    
    def _check_security(self, code: str) -> List[Dict[str, Any]]:
        """Check for dangerous operations"""
        errors = []
        for pattern in self.blacklist_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                errors.append({
                    'type': 'security',
                    'message': f'Dangerous operation detected: {match.group()}',
                    'line': line_num,
                    'severity': 'critical'
                })
        return errors
    
    def _check_syntax(self, code: str) -> List[Dict[str, Any]]:
        """Check Python syntax"""
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append({
                'type': 'syntax',
                'message': f'Syntax error: {e.msg}',
                'line': e.lineno or 0,
                'severity': 'critical'
            })
        return errors
    
    def _check_required_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Check for required code patterns"""
        errors = []
        for pattern, message in self.required_patterns:
            if not re.search(pattern, code):
                errors.append({
                    'type': 'logic',
                    'message': message,
                    'line': 0,
                    'severity': 'error'
                })
        return errors
    
    def _check_imports(self, code: str) -> List[Dict[str, Any]]:
        """Validate imports are safe"""
        errors = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.allowed_imports:
                            errors.append({
                                'type': 'security',
                                'message': f'Unauthorized import: {alias.name}',
                                'line': node.lineno,
                                'severity': 'critical'
                            })
                elif isinstance(node, ast.ImportFrom):
                    if node.module not in self.allowed_imports:
                        errors.append({
                            'type': 'security',
                            'message': f'Unauthorized import from: {node.module}',
                            'line': node.lineno,
                            'severity': 'critical'
                        })
        except:
            pass  # Syntax errors already caught
        return errors
    
    def _check_column_references(
        self,
        code: str,
        df_columns: List[str]
    ) -> List[Dict[str, Any]]:
        """Check if referenced columns exist"""
        warnings = []
        
        # Find string literals that might be column names
        column_pattern = r'[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]'
        matches = re.finditer(column_pattern, code)
        
        for match in matches:
            potential_col = match.group(1)
            if potential_col not in df_columns and len(potential_col) > 2:
                # Might be a column reference
                line_num = code[:match.start()].count('\n') + 1
                warnings.append({
                    'message': f'Column "{potential_col}" not found in dataframe',
                    'line': line_num,
                    'severity': 'warning'
                })
        
        return warnings
    
    def format_validation_for_display(
        self,
        validation: Dict[str, Any]
    ) -> str:
        """Format validation result for chat display"""
        if validation['valid']:
            return f"✅ **Code Validation Passed** (Score: {validation['score']}/100)"
        
        lines = [
            f"### ❌ Code Validation Failed (Score: {validation['score']}/100)",
            ""
        ]
        
        if validation['errors']:
            lines.append("**Errors:**")
            for err in validation['errors']:
                lines.append(f"- Line {err['line']}: {err['message']} ({err['type']})")
            lines.append("")
        
        if validation['warnings']:
            lines.append("**Warnings:**")
            for warn in validation['warnings']:
                lines.append(f"- Line {warn['line']}: {warn['message']}")
        
        return "\n".join(lines)


class RetryManager:
    """
    Manages retry logic for failed code generation/execution
    """
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
    
    def should_retry(
        self,
        attempt: int,
        validation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if we should retry and provide feedback
        
        Returns:
            (should_retry, feedback_for_llm)
        """
        if attempt >= self.max_retries:
            return False, None
        
        if validation['valid']:
            return False, None
        
        # Build feedback for LLM
        feedback_parts = ["The generated code has issues:\n"]
        
        for err in validation['errors']:
            feedback_parts.append(f"- {err['type'].title()} error (line {err['line']}): {err['message']}")
        
        feedback_parts.append("\nPlease regenerate the code addressing these issues.")
        
        return True, "\n".join(feedback_parts)
    
    def format_retry_info(self, attempt: int, feedback: str) -> str:
        """Format retry information for chat display"""
        return f"🔄 **Retrying** (Attempt {attempt}/{self.max_retries})\n\n{feedback}"
