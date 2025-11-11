"""
Answer Synthesizer
Creates plain-language final answers for non-technical users
Explains what the results mean in context
"""
import pandas as pd
from typing import Dict, Any, Optional
import json
from groq import Groq
import os


class AnswerSynthesizer:
    """
    Synthesizes a plain-language answer that directly addresses the user's question
    
    Example:
    Query: "highest growing stock"
    Result: DataFrame with growth data
    Answer: "**PYPL (PayPal)** is the highest growing stock with a daily growth rate 
             of 0.56%, meaning it gained about 56 cents per $100 invested each day on 
             average. It outperformed the second-place INTU by 0.03 percentage points."
    """
    
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def synthesize_answer(
        self,
        original_query: str,
        result: Any,
        query_context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create a direct, plain-language answer to the user's question
        
        Args:
            original_query: What the user asked
            result: The data result (DataFrame, Series, scalar)
            query_context: Additional context about the query
            
        Returns:
            Plain English answer string, or None if not applicable
        """
        # Convert result to text representation
        result_text = self._result_to_text(result)
        
        if not result_text:
            return None
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(original_query, result_text, query_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
            
        except Exception as e:
            print(f"⚠️ Answer synthesis failed: {str(e)}")
            return None
    
    def _result_to_text(self, result: Any) -> Optional[str]:
        """Convert result to text for LLM processing"""
        try:
            if isinstance(result, pd.DataFrame):
                if len(result) == 0:
                    return "No results found"
                
                # Convert to simple text table (first 10 rows)
                top_results = result.head(10)
                
                # Build simple table without requiring external libraries
                lines = []
                cols = top_results.columns.tolist()
                lines.append(" | ".join(str(c) for c in cols))
                lines.append("-" * 50)
                
                for idx, row in top_results.iterrows():
                    # Format numbers nicely
                    formatted_values = []
                    for col in cols:
                        val = row[col]
                        if isinstance(val, float):
                            formatted_values.append(f"{val:.4f}")
                        else:
                            formatted_values.append(str(val))
                    lines.append(" | ".join(formatted_values))
                
                return "\n".join(lines)
            elif isinstance(result, pd.Series):
                # Format Series nicely
                if len(result) == 0:
                    return "No results found"
                
                lines = []
                for idx, val in result.head(20).items():
                    if isinstance(val, float):
                        lines.append(f"{idx}: {val:.4f}")
                    else:
                        lines.append(f"{idx}: {val}")
                
                if len(result) > 20:
                    lines.append(f"... ({len(result) - 20} more values)")
                
                return "\n".join(lines)
            elif isinstance(result, dict):
                # Handle dictionary results
                lines = []
                lines.append("Results contain multiple components:\n")
                
                for key, value in result.items():
                    key_display = str(key).replace('_', ' ').title()
                    
                    if isinstance(value, pd.DataFrame):
                        rows, cols = value.shape
                        lines.append(f"\n{key_display} ({rows} rows):")
                        
                        # Show first few rows
                        display_df = value.head(5)
                        for col in display_df.columns:
                            if display_df[col].dtype in ['int64', 'float64']:
                                mean_val = display_df[col].mean()
                                lines.append(f"  - {col}: avg={mean_val:.2f}")
                    
                    elif isinstance(value, pd.Series):
                        lines.append(f"\n{key_display}:")
                        for idx, val in value.head(10).items():
                            if isinstance(val, float):
                                lines.append(f"  - {idx}: {val:.4f}")
                            else:
                                lines.append(f"  - {idx}: {val}")
                        
                        if len(value) > 10:
                            lines.append(f"  ... ({len(value) - 10} more)")
                    
                    elif isinstance(value, (int, float)):
                        lines.append(f"{key_display}: {value:.4f}")
                    else:
                        lines.append(f"{key_display}: {type(value).__name__}")
                
                return "\n".join(lines)
            elif isinstance(result, (list, tuple)):
                # Handle list/tuple results
                if len(result) == 0:
                    return "Empty list - no results found"
                
                lines = []
                lines.append(f"List with {len(result)} items:")
                
                # Show sample items
                for i, item in enumerate(result[:20]):
                    if isinstance(item, float):
                        lines.append(f"{i+1}. {item:.4f}")
                    else:
                        lines.append(f"{i+1}. {item}")
                
                if len(result) > 20:
                    lines.append(f"... ({len(result) - 20} more items)")
                
                return "\n".join(lines)
            elif isinstance(result, (int, float)):
                return f"Numeric result: {result}"
            elif isinstance(result, str):
                # Handle string results
                return f'Text result: "{result}"' if len(result) < 500 else f'Long text ({len(result)} chars): "{result[:500]}..."'
            elif isinstance(result, bool):
                return f"Boolean result: {result}"
            elif result is None:
                return "No result returned (None)"
            else:
                # For ANY other type, just convert to string and let AI figure it out
                # AI is smart enough to interpret numpy arrays, custom objects, etc.
                try:
                    result_str = str(result)
                    # Truncate if too long
                    if len(result_str) > 2000:
                        result_str = result_str[:2000] + "... (truncated)"
                    return f"{type(result).__name__}:\n{result_str}"
                except:
                    return f"Result of type {type(result).__name__} (unable to display as text)"
        except Exception as e:
            print(f"⚠️ Error converting result to text: {str(e)}")
            return f"Results: {len(result) if hasattr(result, '__len__') else 1} items"
    
    def _build_system_prompt(self) -> str:
        return """Data analyst explaining results to non-technical users.

TASK: Write clear, direct answer to user's question from data results.

STYLE:
• Direct answer first (no "Based on the data..." or "Here's what I found")
• Plain language, avoid jargon | Explain technical terms when used
• Bold for emphasis (**key values/names**) | Concise (2-3 sentences max)
• Add context/comparison when useful | Conversational and helpful

INCLUDE:
1. Direct answer to their question
2. Metric definition (e.g., "growth rate = daily % change")
3. Context/comparison if relevant
4. Real-world meaning (practical impact)

EXAMPLES:
Q: "highest growing stock"
Data: PYPL, growth=0.56
A: "**PYPL (PayPal)** is the highest growing stock with a daily growth rate of **0.56%**, meaning on average it gained 56 cents per $100 invested each day. It outperformed the second-place stock (INTU) by 0.03 percentage points."

Q: "average price by sector"
Data: Technology avg=$245.50, Consumer Goods avg=$89.20
A: "The average stock prices vary significantly by sector. **Technology** has the highest average price at **$245.50**, while **Consumer Goods** has the lowest at **$89.20**. The overall market average is $156.30."

Q: "total sales in Q2"
Data: 1500000
A: "Total sales in Q2 were **$1.5 million**, representing the sum of all transactions during the April-June period."

RULES: No bullets/lists, no "According to...", start with answer, use ** for bold, explain metrics simply."""
    
    def _build_user_prompt(
        self,
        original_query: str,
        result_text: str,
        query_context: Dict[str, Any]
    ) -> str:
        context_info = ""
        if query_context.get('refined_query'):
            context_info = f"\nRefined Query: {query_context['refined_query']}"
        
        return f"""User Question: {original_query}{context_info}

Data Results:
{result_text}

Write a clear, direct answer to their question. Start with the main finding, explain what the metric means, and add helpful context."""
    
    def format_answer_for_display(self, answer: str) -> str:
        """Format the answer as a chat message"""
        return f"### 💡 Answer\n\n{answer}"
