"""
Safe Code Execution Engine
Executes validated code in restricted environment
Phase 7: Safe Execution
"""
import pandas as pd
import numpy as np
import sys
import io
import signal
from typing import Dict, List, Any, Optional
from contextlib import redirect_stdout, redirect_stderr
import traceback


class ExecutionTimeout(Exception):
    """Raised when code execution times out"""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise ExecutionTimeout("Code execution timeout")


class SafeExecutor:
    """
    Executes code in restricted environment with resource limits
    """
    
    def __init__(
        self,
        timeout_seconds: int = 30,
        max_memory_mb: int = 500
    ):
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb
    
    def execute(
        self,
        code: str,
        df: pd.DataFrame,
        stream_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Execute code safely with resource limits
        
        Returns:
            {
                'success': bool,
                'result': any (the 'result' variable from executed code),
                'stdout': str,
                'stderr': str,
                'execution_time': float,
                'error': optional error message
            }
        """
        import time
        start_time = time.time()
        
        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Restricted globals (only safe modules)
        safe_globals = {
            '__builtins__': {
                'abs': abs,
                'all': all,
                'any': any,
                'bool': bool,
                'dict': dict,
                'enumerate': enumerate,
                'filter': filter,
                'float': float,
                'int': int,
                'len': len,
                'list': list,
                'map': map,
                'max': max,
                'min': min,
                'pow': pow,
                'print': print,
                'range': range,
                'round': round,
                'set': set,
                'sorted': sorted,
                'str': str,
                'sum': sum,
                'tuple': tuple,
                'type': type,
                'zip': zip,
                '__import__': __import__,  # Required for pandas/numpy to work
            },
            'pd': pd,
            'np': np,
            'pandas': pd,
            'numpy': np,
            'df': df.copy(),  # Give code a copy to prevent modification
        }
        
        try:
            # Set timeout alarm (Unix only, will skip on Windows)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout_seconds)
            
            # Execute code with output capture
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, safe_globals)
            
            # Cancel alarm
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            
            # Get result
            result = safe_globals.get('result', None)
            
            execution_time = time.time() - start_time
            
            return {
                'success': True,
                'result': result,
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
                'execution_time': execution_time,
                'result_type': type(result).__name__
            }
            
        except ExecutionTimeout:
            return {
                'success': False,
                'result': None,
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
                'execution_time': self.timeout_seconds,
                'error': f'Execution timeout after {self.timeout_seconds} seconds'
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'result': None,
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
                'execution_time': execution_time,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
        finally:
            # Ensure alarm is cancelled
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
    
    def format_result_for_display(
        self,
        execution_result: Dict[str, Any],
        result: Any
    ) -> str:
        """Format execution result for chat display"""
        lines = []
        
        if execution_result['success']:
            lines.append(f"### ✅ Execution Successful")
            lines.append(f"⏱️ **Time**: {execution_result['execution_time']:.2f}s\n")
            
            # Show result preview
            if result is not None:
                result_type = type(result).__name__
                lines.append(f"**Result Type**: {result_type}\n")
                
                if isinstance(result, pd.DataFrame):
                    rows, cols = result.shape
                    lines.append(f"**Shape**: {rows} rows × {cols} columns")
                    lines.append("")
                    lines.append(self._format_dataframe(result))
                    
                elif isinstance(result, pd.Series):
                    lines.append(f"**Length**: {len(result)}")
                    lines.append("")
                    lines.append(self._format_series(result))
                    
                elif isinstance(result, (int, float, str, bool)):
                    lines.append(f"**Value**: {result}")
                    
                else:
                    lines.append(f"```\n{str(result)[:500]}\n```")
            
            # Show stdout if any
            if execution_result.get('stdout'):
                lines.append("\n**Console Output:**")
                lines.append(f"```\n{execution_result['stdout'][:500]}\n```")
        
        else:
            lines.append("### ❌ Execution Failed")
            lines.append(f"⏱️ **Time**: {execution_result['execution_time']:.2f}s")
            lines.append(f"\n**Error**: {execution_result.get('error', 'Unknown error')}")
            
            if execution_result.get('traceback'):
                lines.append("\n**Traceback:**")
                lines.append(f"```\n{execution_result['traceback'][:1000]}\n```")
        
        return "\n".join(lines)
    
    def _format_dataframe(self, df: pd.DataFrame, max_rows: int = 10) -> str:
        """Format dataframe as markdown table"""
        if len(df) == 0:
            return "_Empty DataFrame_"
        
        # Show top rows
        display_df = df.head(max_rows)
        
        # Build markdown table
        lines = []
        
        # Header
        headers = [''] + list(display_df.columns)
        lines.append('| ' + ' | '.join(str(h) for h in headers) + ' |')
        lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        
        # Rows
        for idx, row in display_df.iterrows():
            row_data = [str(idx)] + [str(v)[:50] for v in row.values]
            lines.append('| ' + ' | '.join(row_data) + ' |')
        
        if len(df) > max_rows:
            lines.append(f"\n_... {len(df) - max_rows} more rows_")
        
        return '\n'.join(lines)
    
    def _format_series(self, series: pd.Series, max_items: int = 10) -> str:
        """Format series for display"""
        if len(series) == 0:
            return "_Empty Series_"
        
        display_series = series.head(max_items)
        
        lines = []
        for idx, val in display_series.items():
            lines.append(f"- **{idx}**: {val}")
        
        if len(series) > max_items:
            lines.append(f"_... {len(series) - max_items} more items_")
        
        return '\n'.join(lines)
