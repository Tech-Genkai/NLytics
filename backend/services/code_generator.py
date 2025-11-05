"""
Code Generation Engine
Generates executable pandas/Python code from intent and plans
Phase 5: Code Forge
"""
import json
import os
from typing import Dict, List, Any, Optional
from groq import Groq
import pandas as pd


class CodeGenerator:
    """
    AI-powered code generator that creates executable pandas code
    """
    
    def __init__(self):
        api_key = os.environ.get('GROQ_API_KEY', '')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def generate_code(
        self,
        query: str,
        intent_result: Dict[str, Any],
        execution_plan: Dict[str, Any],
        df_columns: List[str],
        df_dtypes: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generate executable pandas code from query intent and plan
        
        Returns:
            {
                'code': 'executable pandas code',
                'explanation': 'what the code does',
                'imports': ['pandas', 'numpy'],
                'variables': {'result_df': 'final dataframe', ...}
            }
        """
        system_prompt = self._build_code_gen_prompt()
        user_prompt = self._build_user_code_prompt(
            query, intent_result, execution_plan, df_columns, df_dtypes
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temp for consistent code
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            if 'code' not in result:
                raise ValueError("Generated response missing 'code' field")
            
            return {
                'code': result['code'],
                'explanation': result.get('explanation', 'Execute query'),
                'imports': result.get('imports', ['pandas', 'numpy']),
                'variables': result.get('variables', {'result': 'final result'}),
                'warnings': result.get('warnings', [])
            }
            
        except Exception as e:
            print(f"❌ Code generation failed: {str(e)}")
            # Return fallback code
            return {
                'code': '# Code generation failed\nresult = df.head(10)',
                'explanation': f'Error generating code: {str(e)}',
                'imports': ['pandas'],
                'variables': {'result': 'top 10 rows'},
                'error': str(e)
            }
    
    def _build_code_gen_prompt(self) -> str:
        """System prompt for code generation"""
        return """You are an expert Python/pandas code generator.

Your job is to generate clean, efficient, executable pandas code based on user queries.

**CRITICAL RULES:**
1. Input dataframe is ALWAYS named `df`
2. Final result MUST be stored in variable named `result`
3. Use pandas and numpy operations only
4. NO external libraries except pandas, numpy
5. NO file I/O operations (no read_csv, to_csv, etc.)
6. NO system calls or dangerous operations
7. Code must be production-ready and efficient
8. Include comments explaining each step
9. Handle edge cases (empty results, missing columns, etc.)

**Code Structure:**
```python
import pandas as pd
import numpy as np

# Step 1: Description
intermediate_step = df.operation()

# Step 2: Description  
another_step = intermediate_step.operation()

# Final result
result = final_operation()
```

**Output Format (JSON):**
{
  "code": "complete executable python code",
  "explanation": "plain English explanation of what code does",
  "imports": ["pandas", "numpy"],
  "variables": {
    "result": "description of final result variable",
    "intermediate_var": "optional description of intermediate variables"
  },
  "warnings": ["optional warnings about data requirements or limitations"]
}

**Common Patterns:**

1. **Top N by column:**
```python
result = df.nlargest(10, 'column_name')[['col1', 'col2', 'col3']]
```

2. **Growth calculation:**
```python
df['growth'] = ((df['end_value'] - df['start_value']) / df['start_value'] * 100)
result = df.nlargest(10, 'growth')
```

3. **Aggregation with grouping:**
```python
result = df.groupby('category')['value'].mean().reset_index()
result.columns = ['category', 'avg_value']
result = result.sort_values('avg_value', ascending=False)
```

4. **Filtering:**
```python
result = df[df['column'] > threshold].copy()
```

5. **Complex calculations:**
```python
df['new_metric'] = (df['col1'] + df['col2']) / df['col3']
result = df.nlargest(10, 'new_metric')[['id', 'name', 'new_metric']]
```

Always prioritize correctness, efficiency, and readability."""

    def _build_user_code_prompt(
        self,
        query: str,
        intent_result: Dict[str, Any],
        execution_plan: Dict[str, Any],
        df_columns: List[str],
        df_dtypes: Dict[str, str]
    ) -> str:
        """Build user prompt with all context"""
        # Format dtypes nicely
        dtype_str = "\n".join([f"  - {col}: {dtype}" for col, dtype in list(df_dtypes.items())[:15]])
        
        # Format execution steps
        steps_str = "\n".join([
            f"  {s['step_num']}. {s['operation']}: {s['description']}"
            for s in execution_plan.get('steps', [])
        ])
        
        return f"""Generate pandas code for this query:

**User Query:** {query}

**Intent Analysis:**
- Intent: {intent_result['intent']}
- Columns: {intent_result['entities'].get('columns', [])}
- Aggregation: {intent_result.get('aggregation', 'none')}
- Filters: {intent_result.get('filters', [])}
- Group By: {intent_result.get('group_by', 'none')}
- Sort By: {intent_result.get('sort_by', 'none')}
- Limit: {intent_result.get('limit', 'none')}

**Execution Plan:**
{steps_str}

**DataFrame Schema:**
Columns and types:
{dtype_str}

**Available Columns:**
{', '.join(df_columns)}

Generate complete, executable pandas code that:
1. Uses input dataframe `df`
2. Stores final result in variable `result`
3. Implements all steps from the execution plan
4. Handles edge cases gracefully
5. Includes clear comments"""

    def format_code_for_display(self, code_result: Dict[str, Any]) -> str:
        """Format generated code as markdown for chat display"""
        lines = [
            "### 💻 Generated Code",
            f"\n_{code_result['explanation']}_\n"
        ]
        
        if code_result.get('warnings'):
            lines.append("**⚠️ Warnings:**")
            for warning in code_result['warnings']:
                lines.append(f"- {warning}")
            lines.append("")
        
        lines.append("```python")
        lines.append(code_result['code'])
        lines.append("```")
        
        if code_result.get('variables'):
            lines.append("\n**Variables:**")
            for var, desc in code_result['variables'].items():
                lines.append(f"- `{var}`: {desc}")
        
        return "\n".join(lines)
