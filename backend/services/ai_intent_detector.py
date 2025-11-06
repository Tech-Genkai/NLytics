"""
AI-Powered Intent Detection Service
Uses Groq LLM to intelligently understand user queries with dataset context
Phase 3: Conversational Intake (Enhanced)
"""
import json
import os
from typing import Dict, List, Any, Optional
from groq import Groq
import pandas as pd


class AIIntentDetector:
    """
    AI-powered intent detector that uses Groq to understand queries with full dataset context
    """
    
    def __init__(self):
        api_key = os.environ.get('GROQ_API_KEY', '')
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found in environment variables. "
                "Please set it in your .env file or environment."
            )
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"  # Fast and smart
        
    def detect_intent(
        self, 
        query: str, 
        df: pd.DataFrame,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Detect intent using AI with full dataset context
        
        Args:
            query: User's natural language query
            df: The actual dataframe for context
            conversation_history: Previous messages for context
            
        Returns:
            Structured intent with all parameters needed for execution
        """
        # Build dataset context
        dataset_context = self._build_dataset_context(df)
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            recent_messages = conversation_history[-4:]  # Last 4 messages for context
            conversation_context = "\n".join([
                f"{msg['type']}: {msg['content'][:200]}" 
                for msg in recent_messages
            ])
        
        # Build the prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, dataset_context, conversation_context)
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent, focused responses
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Validate and structure the result
            return self._validate_and_structure_result(result, df.columns.tolist())
            
        except Exception as e:
            print(f"⚠️ AI Intent Detection failed: {str(e)}")
            # Fallback to a basic intent
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'entities': {'columns': []},
                'aggregation': None,
                'filters': [],
                'group_by': None,
                'sort_by': None,
                'limit': None,
                'clarifications_needed': [],
                'explanation': f"I encountered an error: {str(e)}",
                'original_query': query
            }
    
    def _build_dataset_context(self, df: pd.DataFrame) -> str:
        """Build comprehensive dataset context for the AI"""
        context_parts = []
        
        # Basic info
        context_parts.append(f"Dataset: {len(df)} rows × {len(df.columns)} columns")
        
        # Column information with types and sample values
        context_parts.append("\nColumns:")
        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null = df[col].count()
            null_count = len(df) - non_null
            
            # Get sample values (unique, limited)
            sample_values = df[col].dropna().unique()[:5].tolist()
            sample_str = ", ".join([str(v)[:50] for v in sample_values])
            
            context_parts.append(
                f"  - {col} ({dtype}): {non_null} non-null values, "
                f"{null_count} nulls. Samples: [{sample_str}]"
            )
        
        # Statistical summary for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            context_parts.append("\nNumeric Column Statistics:")
            for col in numeric_cols[:10]:  # Limit to first 10 numeric columns
                stats = df[col].describe()
                context_parts.append(
                    f"  - {col}: min={stats['min']:.2f}, max={stats['max']:.2f}, "
                    f"mean={stats['mean']:.2f}, median={stats['50%']:.2f}"
                )
        
        return "\n".join(context_parts)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI"""
        return """You are an expert data analyst assistant. Your job is to understand user queries about their dataset and extract structured intent information.

Given a user's natural language query and the dataset context, you must:
1. Determine what the user wants to do (intent)
2. Identify which columns they're referring to
3. Extract any filters, aggregations, groupings, or sorting requirements
4. Determine if you have enough information or need clarification

Intents:
- summary: Show overview/summary of data
- aggregate: Calculate statistics (avg, sum, count, min, max, etc.)
- filter: Filter rows based on conditions
- top_bottom: Show top N or bottom N rows by a column
- group_by: Aggregate data grouped by a column
- distribution: Show distribution/breakdown of values
- compare: Compare values between groups
- trend: Analyze trends over time
- correlation: Find relationships between columns

Output Format (JSON):
{
  "intent": "intent_name",
  "confidence": 0.95,
  "columns": ["column1", "column2"],
  "aggregation": "mean|sum|count|min|max|median|null",
  "filters": [{"column": "col", "operator": ">|<|==|!=|>=|<=", "value": "val"}],
  "group_by": "column_name or null",
  "sort_by": {"column": "column_name", "ascending": true/false} or null,
  "limit": 10 or null,
  "clarifications_needed": [],
  "explanation": "Brief explanation of what you understood"
}

Important Rules:
- Use EXACT column names from the dataset context
- Be smart about column name matching (e.g., "price" could match "close_price" if that's the only price column)
- If the query is ambiguous, leave clarifications_needed empty and make your best intelligent guess
- For queries like "highest valued stock", understand they want top N sorted by a value column
- Consider the conversation history for context
- Only ask for clarification if truly necessary (multiple equally valid options)

**CRITICAL: Understanding "Growth" queries:**
- "highest growing" = calculate PERCENTAGE GROWTH or RATE OF CHANGE, not just highest value
- "fastest growing" = calculate GROWTH RATE, not just highest value
- "biggest increase" = calculate CHANGE or GROWTH, not just final value
- Growth calculation depends on data structure:
  * For price data: (current - previous) / previous * 100
  * For time series: trend analysis or period-over-period change
  * For single snapshot: (close - open) / open * 100
- Always capture growth-related intent in the "explanation" field
- Let the query planner determine the specific calculation method based on available columns"""

    def _build_user_prompt(
        self, 
        query: str, 
        dataset_context: str, 
        conversation_context: str
    ) -> str:
        """Build the user prompt with query and context"""
        prompt_parts = [
            f"Dataset Context:\n{dataset_context}",
            f"\nUser Query: {query}"
        ]
        
        if conversation_context:
            prompt_parts.insert(1, f"\nRecent Conversation:\n{conversation_context}")
        
        return "\n".join(prompt_parts)
    
    def _validate_and_structure_result(
        self, 
        result: Dict[str, Any],
        available_columns: List[str]
    ) -> Dict[str, Any]:
        """Validate AI response and ensure proper structure"""
        # Ensure all required fields exist
        structured = {
            'intent': result.get('intent', 'unknown'),
            'confidence': float(result.get('confidence', 0.5)),
            'entities': {
                'columns': result.get('columns', [])
            },
            'aggregation': result.get('aggregation'),
            'filters': result.get('filters', []),
            'group_by': result.get('group_by'),
            'sort_by': result.get('sort_by'),
            'limit': result.get('limit'),
            'clarifications_needed': result.get('clarifications_needed', []),
            'explanation': result.get('explanation', ''),
            'original_query': result.get('original_query', '')
        }
        
        # Validate column names exist
        valid_columns = []
        for col in structured['entities']['columns']:
            if col in available_columns:
                valid_columns.append(col)
        structured['entities']['columns'] = valid_columns
        
        return structured
