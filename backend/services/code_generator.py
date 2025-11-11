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
            
            # Post-process: Remove any import statements (they cause errors in safe execution)
            code = result['code']
            code_lines = code.split('\n')
            filtered_lines = []
            for line in code_lines:
                stripped = line.strip()
                # Skip import statements
                if stripped.startswith('import ') or stripped.startswith('from '):
                    continue
                filtered_lines.append(line)
            
            # Dedent the code to remove leading whitespace (fixes indentation issues)
            import textwrap
            cleaned_code = textwrap.dedent('\n'.join(filtered_lines)).strip()
            
            return {
                'code': cleaned_code,
                'explanation': result.get('explanation', 'Execute query'),
                'imports': result.get('imports', ['pandas', 'numpy']),
                'variables': result.get('variables', {'result': 'final result'}),
                'warnings': result.get('warnings', [])
            }
            
        except Exception as e:
            print(f"❌ Code generation failed: {str(e)}")
            # Use intelligent fallback based on query keywords
            fallback_code = self._generate_fallback_code(query, df_columns, df_dtypes)
            return {
                'code': fallback_code,
                'explanation': f'Using fallback code due to API error. Attempting to answer query with basic analysis.',
                'imports': ['pandas'],
                'variables': {'result': 'query result'},
                'error': str(e)
            }
    
    def _build_code_gen_prompt(self) -> str:
        """System prompt for code generation"""
        return """You are an expert Python/pandas code generator.

Your job is to generate clean, efficient, executable pandas code based on user queries.

**EXECUTION ENVIRONMENT (Pre-configured for you):**
- `df`: pandas.DataFrame - The input data (already loaded)
- `pd`: pandas module (already imported)
- `np`: numpy module (already imported)
- All standard Python builtins: len, sum, max, min, range, etc.
- NO file system access (open, read, write)
- NO network access
- NO subprocess/system calls
- NO plotting libraries (matplotlib, plotly, seaborn are NOT available)

**CRITICAL RULES:**
1. Input dataframe is ALWAYS named `df` (already exists in scope)
2. Final result MUST be stored in variable named `result` (this is what gets returned)
3. Use pandas and numpy operations only (use `pd` for pandas, `np` for numpy)
4. DO NOT include import statements - pandas and numpy are already imported as `pd` and `np`
5. NO file I/O operations (no read_csv, to_csv, open, etc.)
6. NO system calls or dangerous operations
7. NO plotting code (plt, matplotlib, seaborn, plotly) - visualization is handled separately
8. Code must be production-ready and efficient
9. Include comments explaining each step
10. Handle edge cases (empty results, missing columns, etc.)
11. **TIME-SERIES DATA HANDLING**: If data has Date/Ticker columns with multiple rows per entity:
    - For "top N" queries, MUST group by entity (ticker/company/name) first
    - Aggregate values (sum/mean/last) across time periods
    - THEN select top N entities, not top N rows
    - Example: "top 10 companies by market cap" → group by ticker, average market cap, then nlargest(10)
    - DON'T just do nlargest(10) on raw rows - you'll get the same entity multiple times!
12. **VISUALIZATION QUERIES**: If user requests a specific chart type:
    - **Scatter plot**: Return the RAW DATA POINTS (x and y columns), not aggregated stats
      - WRONG: correlation coefficient only
      - RIGHT: df[['x_col', 'y_col']].sample(min(50, len(df)))
    - **Pie chart**: Return aggregated categories with values (e.g., grouped by company)
    - **Box plot**: Return raw numeric data (can be grouped by category)
    - **Bar chart**: Return aggregated data (top N, grouped totals, etc.)
    - Visualization is handled AFTER code execution - just return the right data structure!

**Code Structure (NO IMPORTS NEEDED):**
```python
# Step 1: Description
intermediate_step = df.operation()

# Step 2: Description  
another_step = intermediate_step.operation()

# Final result
result = final_operation()
```

**IMPORTANT: Do NOT include 'import pandas as pd' or 'import numpy as np' - they are already available!**

**Output Format (JSON):**
{
  "code": "complete executable python code WITHOUT any import statements",
  "explanation": "plain English explanation of what code does",
  "imports": ["pandas", "numpy"],  // For documentation only, don't include in code
  "variables": {
    "result": "description of final result variable (this will be extracted and returned)",
    "intermediate_var": "optional description of intermediate variables"
  },
  "warnings": ["optional warnings about data requirements or limitations"]
}

**CRITICAL OUTPUT REQUIREMENTS:**
- The `result` variable MUST exist after code execution
- `result` should contain the answer to the user's query
- `result` can be: DataFrame, Series, scalar (int/float/string), dict, or list
- DO NOT print the result - it will be automatically captured
- If no meaningful result, set `result = None`
- DO NOT generate plotting code (plt, matplotlib, seaborn) - visualizations are created automatically from your result data

**IMPORTANT: If user asks for a chart/graph/plot:**
- Generate code to prepare the DATA only (top N rows, aggregated values, etc.)
- Return the data as a DataFrame or Series in `result`
- The system will AUTOMATICALLY create visualizations from your result
- DO NOT use plt, matplotlib, seaborn, or any plotting library
- Example: If asked "pie chart of top 10", return a DataFrame with top 10 rows - the system handles the chart

**Common Patterns (remember: NO imports needed!):**

1. **Top N by column:**
```python
# Get top 10 by column value
result = df.nlargest(10, 'column_name')[['col1', 'col2', 'col3']]
```

2. **Growth calculation:**
```python
# Calculate growth percentage
df['growth'] = ((df['end_value'] - df['start_value']) / df['start_value'] * 100)
result = df.nlargest(10, 'growth')
```

3. **Aggregation with grouping:**
```python
# Group and aggregate
result = df.groupby('category')['value'].mean().reset_index()
result.columns = ['category', 'avg_value']
result = result.sort_values('avg_value', ascending=False)
```

4. **Filtering:**
```python
# Filter rows
result = df[df['column'] > threshold].copy()
```

5. **Complex calculations:**
```python
# Calculate new metric
df['new_metric'] = (df['col1'] + df['col2']) / df['col3']
result = df.nlargest(10, 'new_metric')[['id', 'name', 'new_metric']]
```

**REMEMBER: pandas is available as `pd`, numpy as `np`. DO NOT write import statements!**

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

**Available Columns (use EXACT names):**
{', '.join(df_columns)}

**What's Already Available in Execution Environment:**
- Variable `df`: pandas.DataFrame with the columns above
- Module `pd`: pandas (already imported, don't import again)
- Module `np`: numpy (already imported, don't import again)
- All Python builtins: len(), sum(), max(), min(), etc.

**What You Need to Generate:**
Complete, executable pandas code that:
1. Uses input dataframe `df` (already exists, don't create it)
2. Stores final result in variable `result` (REQUIRED - this gets returned)
3. Implements all steps from the execution plan
4. Handles edge cases gracefully (empty df, missing values)
5. Includes clear comments
6. NO import statements (pd and np are already available)

**Expected Output:**
The code should define the `result` variable containing the answer."""

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
    
    def _generate_fallback_code(self, query: str, df_columns: List[str], df_dtypes: Dict[str, str]) -> str:
        """
        Generate intelligent fallback code when API fails
        Attempts to answer common query patterns
        """
        query_lower = query.lower()
        
        # Detect numeric and categorical columns
        numeric_cols = [col for col, dtype in df_dtypes.items() if dtype in ['int64', 'float64']]
        categorical_cols = [col for col, dtype in df_dtypes.items() if dtype == 'object']
        
        # Pattern: "top N" or "highest" with numeric comparison
        if any(keyword in query_lower for keyword in ['top', 'highest', 'largest', 'biggest', 'best']):
            # Try to find value column (market cap, price, value, etc.)
            value_col = None
            for col in numeric_cols:
                if any(keyword in col.lower() for keyword in ['cap', 'value', 'price', 'amount', 'total', 'sum']):
                    value_col = col
                    break
            
            # Try to find name/category column
            name_col = None
            for col in categorical_cols:
                if any(keyword in col.lower() for keyword in ['name', 'company', 'stock', 'symbol', 'ticker']):
                    name_col = col
                    break
            
            # Extract number (default to 10)
            import re
            number_match = re.search(r'\b(\d+)\b', query)
            top_n = int(number_match.group(1)) if number_match else 10
            
            if value_col and name_col:
                # Group by name and sum, then get top N
                return f"""# Get top {top_n} by {value_col}
result = df.groupby('{name_col}')['{value_col}'].sum().sort_values(ascending=False).head({top_n}).reset_index()
result.columns = ['{name_col}', '{value_col}']"""
            elif value_col:
                # Just sort by value
                return f"""# Get top {top_n} by {value_col}
result = df.nlargest({top_n}, '{value_col}')"""
        
        # Pattern: "show all" or "display"
        if any(keyword in query_lower for keyword in ['show all', 'display all', 'list all', 'get all']):
            return "# Show all data\nresult = df"
        
        # Pattern: "average" or "mean"
        if any(keyword in query_lower for keyword in ['average', 'mean']):
            if numeric_cols:
                return f"""# Calculate averages
result = df[{numeric_cols}].mean().to_frame('Average').reset_index()
result.columns = ['Metric', 'Average']"""
        
        # Pattern: "count" or "how many"
        if any(keyword in query_lower for keyword in ['count', 'how many', 'number of']):
            if categorical_cols:
                cat_col = categorical_cols[0]
                return f"""# Count by {cat_col}
result = df['{cat_col}'].value_counts().reset_index()
result.columns = ['{cat_col}', 'Count']"""
        
        # Default fallback: show first 10 rows
        return "# Show sample data\nresult = df.head(10)"
