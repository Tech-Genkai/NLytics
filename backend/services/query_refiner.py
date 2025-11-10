"""
Query Refinement Layer
Adds intelligence to understand user intent better
Converts literal queries into more useful analytical queries
"""
import json
from typing import Dict, Any
from groq import Groq
import os


class QueryRefiner:
    """
    Intelligently refines queries to be more useful for analysis
    
    Examples:
    - "highest growing stock" → "show growth for all stocks, ranked"
    - "best performer" → "compare all performers"
    - "most expensive" → "show price comparison across all items"
    """
    
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def refine_query(
        self,
        original_query: str,
        intent_result: Dict[str, Any],
        dataset_context: str
    ) -> Dict[str, Any]:
        """
        Refine the query to be more analytically useful
        
        Returns:
            {
                'refined_query': 'better query text',
                'refinement_applied': True/False,
                'reasoning': 'why it was refined',
                'visualization_hint': 'what viz would be useful'
            }
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(original_query, intent_result, dataset_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"⚠️ Query refinement failed: {str(e)}")
            # Fallback: no refinement, but detect explicit chart requests with keyword matching
            requested_chart = self._detect_chart_type_from_keywords(original_query)
            return {
                'refined_query': original_query,
                'refinement_applied': False,
                'reasoning': 'Refinement failed, using original query',
                'visualization_hint': requested_chart,
                'requested_chart_type': requested_chart
            }
    
    def _build_system_prompt(self) -> str:
        return """You are a data analysis expert who helps users get better insights from their queries.

Your job: Take a user's query and refine it to be MORE USEFUL for analysis.

**Key Principle: RESPECT USER INTENT FIRST, THEN ENHANCE**

**CRITICAL: If user EXPLICITLY requests a visualization type, PRESERVE IT!**
- "pie chart of..." → Keep pie chart, don't suggest bar chart
- "scatter plot of..." → Keep scatter plot
- "line graph of..." → Keep line graph
- "box plot of..." → Keep box plot
- Only suggest alternatives if NO visualization type is mentioned

When users ask for "the highest/best/top" - they usually want to:
1. See the TOP item IN CONTEXT of others
2. Understand HOW MUCH better it is
3. Compare it to alternatives

**Refinement Rules:**

1. **EXPLICIT VISUALIZATION REQUESTS (HIGHEST PRIORITY):**
   - ✅ DO: Preserve the requested chart type (pie, bar, scatter, line, box, etc.)
   - ✅ DO: Only refine the DATA query, not the visualization
   - Example: "pie chart of top 10 stocks" → "show top 10 stocks by market cap" (keep pie chart intent)
   - Example: "scatter plot of price vs volume" → keep scatter plot
   - ❌ DON'T: Suggest a different chart type when user specifies one

2. **"Highest/Best/Top X" queries:**
   - ❌ DON'T: Return just 1 result unless explicitly asked for "the one" or "which single"
   - ✅ DO: Show top 5-10 for comparison (default to 10 if unspecified)
   - If user says "top 5" or "top 3", respect their number
   - Example: "highest growing stock" → "show top 10 stocks by growth percentage, ranked"
   - Example: "show me the single best stock" → "show top 1 stock" (respect literal request)

2. **Single value queries:**
   - ❌ DON'T: Return a scalar if a comparison would be more useful
   - ✅ DO: Show rankings, distributions, or breakdowns
   - Example: "average price" → "show average price by category"

3. **"Most/Least" queries:**
   - ✅ DO: Show top N and bottom N for full picture
   - Example: "most expensive" → "show top 10 and bottom 10 by price"

4. **Keep simple queries simple:**
   - "show all data" → no refinement needed
   - "filter by X" → no refinement needed
   - "count rows" → no refinement needed

5. **Visualization hints (ONLY if user didn't specify):**
   - If user said "pie chart" → Use "pie" (don't suggest bar!)
   - If user said "scatter plot" → Use "scatter"
   - If user said "line chart" → Use "line"
   - If NO visualization mentioned:
     - Top N rankings → suggest bar chart
     - Comparisons → suggest bar chart or grouped bar
     - Distributions → suggest histogram or box plot
     - Trends → suggest line chart
     - Correlations → suggest scatter plot

**Output Format (JSON):**
{
  "refined_query": "the improved query text",
  "refinement_applied": true/false,
  "reasoning": "brief explanation of why refinement helps",
  "visualization_hint": "pie|bar|line|scatter|histogram|box|null",
  "requested_chart_type": "pie|bar|line|scatter|box|null (if user explicitly requested)",
  "show_comparison": true/false,
  "suggested_limit": 10 (for top N queries)
}

**CRITICAL: Check for these keywords to detect explicit visualization requests:**
- "pie chart", "pie graph", "donut chart" → requested_chart_type: "pie"
- "bar chart", "bar graph" → requested_chart_type: "bar"
- "scatter plot", "scatter chart" → requested_chart_type: "scatter"
- "line chart", "line graph" → requested_chart_type: "line"
- "box plot", "box chart" → requested_chart_type: "box"
- "histogram" → requested_chart_type: "histogram"
- If none found → requested_chart_type: null

**Examples:**

Input: "pie chart of top 10 companies by market cap"
Output:
{
  "refined_query": "show top 10 companies by market capitalization",
  "refinement_applied": true,
  "reasoning": "User explicitly requested pie chart - preserving that visualization choice while ensuring top 10 data is prepared",
  "visualization_hint": "pie",
  "requested_chart_type": "pie",
  "show_comparison": true,
  "suggested_limit": 10
}

Input: "highest growing stock"
Output:
{
  "refined_query": "show growth percentage for all stocks, sorted by growth descending, show top 10",
  "refinement_applied": true,
  "reasoning": "User wants to see the highest growing stock IN CONTEXT of others, not just a single value. Top 10 comparison is more insightful.",
  "visualization_hint": "bar",
  "requested_chart_type": null,
  "show_comparison": true,
  "suggested_limit": 10
}

Input: "average price"
Output:
{
  "refined_query": "calculate average price and show price distribution by category",
  "refinement_applied": true,
  "reasoning": "A single average is less useful than seeing how prices vary across categories",
  "visualization_hint": "bar",
  "requested_chart_type": null,
  "show_comparison": true,
  "suggested_limit": null
}

Input: "show all technology stocks"
Output:
{
  "refined_query": "show all technology stocks",
  "refinement_applied": false,
  "reasoning": "Query is already clear and specific, no refinement needed",
  "visualization_hint": null,
  "requested_chart_type": null,
  "show_comparison": false,
  "suggested_limit": null
}

Input: "scatter plot of volume vs price"
Output:
{
  "refined_query": "show relationship between volume and price for all stocks",
  "refinement_applied": true,
  "reasoning": "User explicitly requested scatter plot - preserving that choice",
  "visualization_hint": "scatter",
  "requested_chart_type": "scatter",
  "show_comparison": false,
  "suggested_limit": null
}
"""
    
    def _build_user_prompt(
        self,
        original_query: str,
        intent_result: Dict[str, Any],
        dataset_context: str
    ) -> str:
        return f"""Original Query: {original_query}

AI Intent Understanding:
- Query Type: {intent_result.get('intent', 'unknown')}
- Explanation: {intent_result.get('explanation', 'N/A')}
- Columns involved: {', '.join(intent_result.get('entities', {}).get('columns', []))}

Dataset Context:
{dataset_context}

Should this query be refined for better analysis? If yes, how?"""
    
    def format_refinement_for_display(self, refinement: Dict[str, Any]) -> str:
        """Format refinement info as markdown"""
        if not refinement.get('refinement_applied'):
            return ""
        
        return f"""**🔍 Query Refined for Better Insights**

_{refinement.get('reasoning', 'Refining for more useful analysis')}_

**Analyzing:** {refinement.get('refined_query', '')}
"""
    
    def _detect_chart_type_from_keywords(self, query: str) -> str:
        """
        Simple keyword-based chart type detection (fallback when API fails)
        
        Args:
            query: User's query text
            
        Returns:
            Chart type string or None
        """
        query_lower = query.lower()
        
        # Check for explicit visualization keywords
        if any(keyword in query_lower for keyword in ['pie chart', 'pie graph', 'donut chart', 'donut graph']):
            return 'pie'
        elif any(keyword in query_lower for keyword in ['bar chart', 'bar graph']):
            return 'bar'
        elif any(keyword in query_lower for keyword in ['scatter plot', 'scatter chart', 'scatter graph']):
            return 'scatter'
        elif any(keyword in query_lower for keyword in ['line chart', 'line graph', 'line plot']):
            return 'line'
        elif any(keyword in query_lower for keyword in ['box plot', 'box chart', 'boxplot']):
            return 'box'
        elif 'histogram' in query_lower:
            return 'histogram'
        
        return None
