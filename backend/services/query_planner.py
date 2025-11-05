"""
Query Planner Service
Breaks complex queries into ordered multi-step plans
Phase 4: Planning Canvas
"""
import json
import os
from typing import Dict, List, Any, Optional
from groq import Groq


class QueryPlanner:
    """
    AI-powered query planner that creates multi-step execution plans
    """
    
    def __init__(self):
        api_key = os.environ.get('GROQ_API_KEY', '')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def create_plan(
        self,
        query: str,
        intent_result: Dict[str, Any],
        dataset_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a multi-step execution plan for complex queries
        
        Returns:
            {
                'needs_planning': bool,
                'steps': [{'step_num': 1, 'description': '...', 'operation': '...', 'dependencies': []}],
                'estimated_time': str,
                'complexity': 'simple|moderate|complex'
            }
        """
        # Check if query needs multi-step planning
        if self._is_simple_query(intent_result):
            return {
                'needs_planning': False,
                'steps': [{
                    'step_num': 1,
                    'description': intent_result.get('explanation', 'Execute query'),
                    'operation': intent_result['intent'],
                    'dependencies': []
                }],
                'estimated_time': '< 1 second',
                'complexity': 'simple'
            }
        
        # Create multi-step plan using AI
        system_prompt = self._build_planning_prompt()
        user_prompt = self._build_user_planning_prompt(
            query, intent_result, dataset_summary
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            plan = json.loads(response.choices[0].message.content)
            plan['needs_planning'] = True
            
            return plan
            
        except Exception as e:
            print(f"⚠️ Planning failed: {str(e)}")
            # Fallback to simple plan
            return {
                'needs_planning': False,
                'steps': [{
                    'step_num': 1,
                    'description': f"Execute: {query}",
                    'operation': intent_result['intent'],
                    'dependencies': []
                }],
                'estimated_time': '< 5 seconds',
                'complexity': 'simple',
                'error': str(e)
            }
    
    def _is_simple_query(self, intent_result: Dict[str, Any]) -> bool:
        """Determine if query needs multi-step planning"""
        # Simple queries: single aggregation, filter, or top/bottom
        simple_intents = ['summary', 'aggregate', 'filter', 'top_bottom']
        
        if intent_result['intent'] not in simple_intents:
            return False
        
        # Complex if multiple filters or group_by with aggregation
        has_multiple_filters = len(intent_result.get('filters', [])) > 2
        has_group_and_agg = (
            intent_result.get('group_by') and 
            intent_result.get('aggregation')
        )
        
        return not (has_multiple_filters or has_group_and_agg)
    
    def _build_planning_prompt(self) -> str:
        """System prompt for query planning"""
        return """You are an expert data analyst creating execution plans for data queries.

Your job is to break down complex data analysis queries into clear, ordered steps.

Each step should:
1. Have a clear description of what it does
2. Specify the operation type (filter, aggregate, transform, sort, etc.)
3. List dependencies on previous steps
4. Be executable independently

Output Format (JSON):
{
  "steps": [
    {
      "step_num": 1,
      "description": "Clear description",
      "operation": "filter|aggregate|transform|sort|join|calculate",
      "details": {
        "columns": ["col1", "col2"],
        "formula": "optional calculation",
        "condition": "optional filter condition"
      },
      "dependencies": []
    }
  ],
  "estimated_time": "< 1 second|1-5 seconds|5-30 seconds",
  "complexity": "simple|moderate|complex",
  "explanation": "Why we need these steps"
}

Examples:

Query: "Show me top 10 fastest growing stocks"
Steps:
1. Calculate growth: (close - open) / open
2. Sort by growth descending
3. Take top 10 results

Query: "Compare average prices by sector for tech stocks"
Steps:
1. Filter to tech sector stocks
2. Group by sector
3. Calculate average price per sector
4. Format results for comparison"""

    def _build_user_planning_prompt(
        self,
        query: str,
        intent_result: Dict[str, Any],
        dataset_summary: Dict[str, Any]
    ) -> str:
        """Build user prompt with query context"""
        return f"""Create an execution plan for this query:

Query: {query}

Intent Analysis:
- Intent: {intent_result['intent']}
- Columns: {intent_result['entities'].get('columns', [])}
- Aggregation: {intent_result.get('aggregation', 'none')}
- Filters: {intent_result.get('filters', [])}
- Group By: {intent_result.get('group_by', 'none')}

Dataset:
- Rows: {dataset_summary.get('row_count', 'unknown')}
- Columns: {', '.join(dataset_summary.get('columns', [])[:10])}

Break this into clear, executable steps."""

    def format_plan_for_display(self, plan: Dict[str, Any]) -> str:
        """Format plan as markdown for chat display"""
        if not plan.get('needs_planning'):
            return f"**Quick Query** ({plan['complexity']})\n\n{plan['steps'][0]['description']}"
        
        lines = [
            f"### 📋 Execution Plan",
            f"**Complexity**: {plan['complexity'].title()} | **Est. Time**: {plan['estimated_time']}",
            ""
        ]
        
        if plan.get('explanation'):
            lines.append(f"_{plan['explanation']}_\n")
        
        lines.append("**Steps:**")
        for step in plan['steps']:
            deps = f" (requires step {', '.join(map(str, step['dependencies']))})" if step['dependencies'] else ""
            lines.append(f"{step['step_num']}. **{step['operation'].title()}**: {step['description']}{deps}")
        
        return "\n".join(lines)
