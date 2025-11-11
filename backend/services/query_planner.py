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
        return """Expert data analyst creating execution plans for complex queries.

TASK: Break down analysis into clear, ordered steps.

STEP REQUIREMENTS:
• Clear description | Operation type (filter/aggregate/transform/sort/join/calculate)
• Dependencies on previous steps | Executable independently

JSON OUTPUT:
{
  "steps": [
    {
      "step_num": 1,
      "description": "Clear description",
      "operation": "filter|aggregate|transform|sort|join|calculate",
      "details": {
        "columns": ["col1"],
        "formula": "optional",
        "condition": "optional"
      },
      "dependencies": []
    }
  ],
  "estimated_time": "< 1 sec|1-5 sec|5-30 sec",
  "complexity": "simple|moderate|complex",
  "explanation": "Why these steps"
}

EXAMPLES:
"Top 10 fastest growing stocks" → [1. Calculate growth: (close-open)/open, 2. Sort descending, 3. Top 10]
"Avg price by sector, top 5" → [1. Group by sector, 2. Mean price, 3. Sort, 4. Top 5]
"Stocks >$100 with volume >1M" → [1. Filter price>100, 2. Filter volume>1M, 3. Return results]

Keep it concise but complete."""

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
