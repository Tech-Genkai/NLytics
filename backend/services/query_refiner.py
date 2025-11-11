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
        dataset_context: str,
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        Refine the query to be more analytically useful
        
        Args:
            original_query: The user's query
            intent_result: The detected intent
            dataset_context: Brief dataset info
            conversation_history: Previous messages for context
        
        Returns:
            {
                'refined_query': 'better query text',
                'refinement_applied': True/False,
                'reasoning': 'why it was refined',
                'visualization_hint': 'what viz would be useful'
            }
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(original_query, intent_result, dataset_context, conversation_history)
        
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
        return """Data analysis expert. Refine queries for better insights while RESPECTING user intent.

CORE PRINCIPLE: User intent first → then enhance for better analysis.

CONVERSATIONAL CONTEXT (PRIORITY 1):
• Follow-up queries ("bar graph", "pie chart") = SAME DATA from previous query, different viz
• Example: "top 10 companies" → "bar graph" = bar chart of THOSE 10 companies, not new analysis
• Preserve filters/limits from previous query, only change visualization

EXPLICIT VISUALIZATION (PRIORITY 2):
• User specifies chart type → PRESERVE IT: "pie chart of X" → keep pie, refine data only
• Chart keywords: pie chart|bar graph|scatter plot|line chart|box plot|histogram
• Don't suggest alternatives when user specifies type

REFINEMENT RULES:
1. "Highest/best/top X": Show top 10 for comparison (unless "top N" specified or "the single best")
2. Single values: Convert to comparisons when useful ("average price" → "avg by category")
3. "Most/least": Show top N + bottom N for full picture
4. Simple queries: No refinement ("show all", "filter by X", "count rows")

VISUALIZATION HINTS (only if not specified):
• Rankings/comparisons → bar | Distributions → histogram/box
• Trends → line | Correlations → scatter | Parts of whole → pie

JSON OUTPUT:
{
  "refined_query": "improved query",
  "refinement_applied": true/false,
  "reasoning": "why this helps",
  "visualization_hint": "pie|bar|line|scatter|histogram|box|null",
  "requested_chart_type": "chart_type or null",
  "show_comparison": true/false,
  "suggested_limit": 10,
  "is_followup": true/false
}

EXAMPLES:
"pie chart of top 10 stocks" → {refined: "top 10 stocks by market cap", requested_chart_type: "pie"}
"bar graph" (after "top 10 companies") → {refined: "top 10 companies as bar", requested_chart_type: "bar", is_followup: true}
"highest growing stock" → {refined: "growth % for all stocks, top 10 descending", visualization_hint: "bar", suggested_limit: 10}
"show all tech stocks" → {refined: "show all tech stocks", refinement_applied: false}"""
    
    def _build_user_prompt(
        self,
        original_query: str,
        intent_result: Dict[str, Any],
        dataset_context: str,
        conversation_history: list = None
    ) -> str:
        prompt_parts = []
        
        # Add conversation context if available
        if conversation_history:
            # Extract last few user queries and assistant answers for context
            context_messages = []
            for msg in conversation_history[-6:]:  # Last 6 messages (3 exchanges)
                msg_type = msg.get('type', '')
                content = msg.get('content', '')
                metadata = msg.get('metadata', {})
                
                if msg_type == 'user':
                    context_messages.append(f"User asked: {content}")
                elif msg_type == 'assistant' and metadata.get('type') == 'answer':
                    # Include the answer for context
                    context_messages.append(f"Assistant answered: {content[:200]}...")
                elif msg_type == 'system' and metadata.get('type') == 'insights':
                    # Include insights about what data was shown
                    insights_data = metadata.get('insights', {})
                    if insights_data.get('narrative'):
                        context_messages.append(f"Showed: {insights_data['narrative'][:150]}...")
            
            if context_messages:
                prompt_parts.append("Conversation History (Recent Context):")
                prompt_parts.append("\n".join(context_messages))
                prompt_parts.append("")
        
        prompt_parts.append(f"""Current Query: {original_query}

AI Intent Understanding:
- Query Type: {intent_result.get('intent', 'unknown')}
- Explanation: {intent_result.get('explanation', 'N/A')}
- Columns involved: {', '.join(intent_result.get('entities', {}).get('columns', []))}

Dataset Context:
{dataset_context}

**CRITICAL: Check conversation history above. If user's current query is a follow-up (e.g., "bar graph", "analyze its growth", "show me more"), it refers to the SAME DATA from the previous query. Preserve the data context (e.g., top 10 companies) from the previous exchange.**

Should this query be refined for better analysis? If yes, how?""")
        
        return "\n".join(prompt_parts)
    
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
