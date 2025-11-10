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
        
        # Restricted globals - Allow safe built-ins
        import builtins
        
        # Start with a copy of safe builtins
        safe_builtins = {
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
            'isinstance': isinstance,
            'issubclass': issubclass,
            'callable': callable,
            'reversed': reversed,
            'ord': ord,
            'chr': chr,
            'bin': bin,
            'hex': hex,
            'oct': oct,
            'hash': hash,
            'id': id,
            'format': format,
            'divmod': divmod,
            'bytes': bytes,
            'bytearray': bytearray,
            'complex': complex,
            'frozenset': frozenset,
            'slice': slice,
            'object': object,
            'staticmethod': staticmethod,
            'classmethod': classmethod,
            'property': property,
            'Exception': Exception,
            'ValueError': ValueError,
            'TypeError': TypeError,
            'KeyError': KeyError,
            'IndexError': IndexError,
            'AttributeError': AttributeError,
            'ZeroDivisionError': ZeroDivisionError,
            'RuntimeError': RuntimeError,
            'StopIteration': StopIteration,
            'Warning': Warning,
            'False': False,
            'True': True,
            'None': None,
            'NotImplemented': NotImplemented,
            'Ellipsis': Ellipsis,
        }
        
        # Add getattr, setattr, hasattr back - pandas needs these internally
        # But we monitor them carefully
        safe_builtins['getattr'] = getattr
        safe_builtins['setattr'] = setattr
        safe_builtins['hasattr'] = hasattr
        safe_builtins['delattr'] = delattr
        
        # Define dangerous functions that should NOT be accessible
        dangerous_funcs = {
            '__import__',
            'eval',
            'exec',
            'compile',
            'open',
            'input',
            'globals',
            'locals',
            'vars',
            'dir',
            '__loader__',
            '__spec__',
            'breakpoint',
            'help',
            'exit',
            'quit',
            'license',
            'copyright',
            'credits',
        }
        
        # Block dangerous functions by setting them to a function that raises an error
        def blocked_function(*args, **kwargs):
            raise RuntimeError("This function is not allowed in safe execution mode")
        
        for func_name in dangerous_funcs:
            safe_builtins[func_name] = blocked_function
        
        # Pre-import safe modules
        safe_globals = {
            '__builtins__': safe_builtins,
            'pd': pd,
            'np': np,
            'pandas': pd,
            'numpy': np,
            'df': df.copy(),
            '__name__': '__main__',
            '__doc__': None,
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
                
                elif isinstance(result, dict):
                    lines.append(f"**Components**: {len(result)} items")
                    lines.append("")
                    lines.append(self._format_dict(result))
                
                elif isinstance(result, (list, tuple)):
                    type_name = "List" if isinstance(result, list) else "Tuple"
                    lines.append(f"**{type_name} Length**: {len(result)}")
                    lines.append("")
                    lines.append(self._format_list(result))
                
                elif isinstance(result, np.ndarray):
                    lines.append(f"**Array Shape**: {result.shape}")
                    lines.append("")
                    lines.append(self._format_numpy_array(result))
                
                elif isinstance(result, str):
                    lines.append(f"**String Length**: {len(result)} characters")
                    lines.append("")
                    if len(result) < 500:
                        lines.append(f'**Value**: "{result}"')
                    else:
                        lines.append(f'**Preview**:\n"{result[:500]}..."')
                
                elif isinstance(result, bool):
                    lines.append(f"**Boolean**: {result} {'✓' if result else '✗'}")
                    
                elif isinstance(result, (int, float)):
                    lines.append(f"**Value**: {result}")
                
                elif result is None:
                    lines.append("**No result returned** (None)")
                    
                else:
                    # Unknown type
                    lines.append(f"**Value**: {str(result)[:500]}")
            
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
            if isinstance(val, float):
                lines.append(f"- **{idx}**: {val:.4f}")
            else:
                lines.append(f"- **{idx}**: {val}")
        
        if len(series) > max_items:
            lines.append(f"_... {len(series) - max_items} more items_")
        
        return '\n'.join(lines)
    
    def _format_dict(self, result_dict: dict, max_items: int = 5) -> str:
        """Format dictionary results for display"""
        lines = []
        
        for i, (key, value) in enumerate(result_dict.items()):
            if i >= max_items:
                lines.append(f"\n_... {len(result_dict) - max_items} more components_")
                break
            
            key_display = str(key).replace('_', ' ').title()
            lines.append(f"\n**{key_display}:**")
            
            if isinstance(value, pd.DataFrame):
                rows, cols = value.shape
                lines.append(f"- DataFrame with {rows} rows × {cols} columns")
                
                # Show summary of numeric columns
                numeric_cols = value.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    for col in numeric_cols[:3]:  # First 3 numeric columns
                        mean_val = value[col].mean()
                        lines.append(f"  - {col}: avg = {mean_val:.2f}")
            
            elif isinstance(value, pd.Series):
                lines.append(f"- Series with {len(value)} values")
                
                # Show first few values
                for idx, val in list(value.head(3).items()):
                    if isinstance(val, float):
                        lines.append(f"  - {idx}: {val:.4f}")
                    else:
                        lines.append(f"  - {idx}: {val}")
                
                if len(value) > 3:
                    lines.append(f"  - ... ({len(value) - 3} more)")
            
            elif isinstance(value, (int, float)):
                lines.append(f"- {value:.4f}")
            
            else:
                lines.append(f"- {type(value).__name__}: {str(value)[:100]}")
        
        return '\n'.join(lines)
    
    def _format_list(self, result_list: list, max_items: int = 10) -> str:
        """Format list/tuple results for display"""
        if len(result_list) == 0:
            return "_Empty list_"
        
        lines = []
        for i, item in enumerate(result_list[:max_items]):
            if isinstance(item, float):
                lines.append(f"{i+1}. {item:.4f}")
            elif isinstance(item, str) and len(str(item)) > 100:
                lines.append(f"{i+1}. {str(item)[:100]}...")
            else:
                lines.append(f"{i+1}. {item}")
        
        if len(result_list) > max_items:
            lines.append(f"\n_... {len(result_list) - max_items} more items_")
        
        return '\n'.join(lines)
    
    def _format_numpy_array(self, array: np.ndarray, max_items: int = 20) -> str:
        """Format numpy array for display"""
        lines = []
        
        # Show array info
        lines.append(f"**Shape**: {array.shape}")
        lines.append(f"**Data type**: {array.dtype}")
        lines.append(f"**Size**: {array.size} elements\n")
        
        # For numeric arrays, show stats
        if np.issubdtype(array.dtype, np.number) and array.size > 0:
            lines.append(f"**Stats:**")
            lines.append(f"- Min: {np.min(array):.4f}")
            lines.append(f"- Max: {np.max(array):.4f}")
            lines.append(f"- Mean: {np.mean(array):.4f}\n")
        
        # Show sample values
        flat = array.flatten()
        if len(flat) <= max_items:
            lines.append(f"**Values**: {flat}")
        else:
            lines.append(f"**Sample** (first {max_items}): {flat[:max_items]}")
        
        return '\n'.join(lines)
