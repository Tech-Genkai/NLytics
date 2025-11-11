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
        """Build lean but sufficient dataset context for the AI"""
        context_parts = []
        
        # Basic info
        context_parts.append(f"Dataset: {len(df)} rows × {len(df.columns)} columns\n")
        
        # Column information with types and 2 sample values only
        context_parts.append("Columns:")
        for col in df.columns:
            dtype = str(df[col].dtype)
            
            # Get 2 sample values (sufficient for AI to understand data)
            sample_values = df[col].dropna().unique()[:2].tolist()
            sample_str = ", ".join([str(v)[:40] for v in sample_values])
            
            # Simplified format - AI doesn't need null counts for every column
            context_parts.append(f"  - {col} ({dtype}): {sample_str}")
        
        # Quick statistics for top 5 numeric columns (reduced from 10)
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            context_parts.append("\nKey Statistics:")
            for col in numeric_cols[:5]:
                stats = df[col].describe()
                # 1 decimal place is sufficient for AI understanding
                context_parts.append(
                    f"  - {col}: range {stats['min']:.1f}-{stats['max']:.1f}, avg {stats['mean']:.1f}"
                )
        
        return "\n".join(context_parts)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI"""
        return """Expert data analyst. Extract structured intent from natural language queries.

TASK: Analyze user query + dataset context → Return JSON with intent, columns, operations.

INTENTS:
• summary: Overview/summary | aggregate: Stats (avg, sum, count, min, max)
• filter: Filter rows | top_bottom: Top/bottom N by column | group_by: Aggregate by group
• distribution: Value breakdown | compare: Compare groups | trend: Time analysis
• correlation: Relationships | visualization: Change chart type for existing data

JSON FORMAT:
{
  "intent": "intent_name",
  "confidence": 0.95,
  "columns": ["col1", "col2"],
  "aggregation": "mean|sum|count|min|max|median|null",
  "filters": [{"column": "col", "operator": ">|<|==|!=|>=|<=", "value": "val"}],
  "group_by": "column_name or null",
  "sort_by": {"column": "name", "ascending": true/false} or null,
  "limit": 10 or null,
  "clarifications_needed": [],
  "explanation": "Brief explanation"
}

CRITICAL RULES:
• Use EXACT column names from dataset (case-sensitive)
• Smart matching: "price" → "close_price" if only price column
• Minimal clarifications - make intelligent guesses when reasonable
• "highest valued stock" = top N sorted by value (not just 1)
• Conversational context: "bar graph" after "top 10 companies" = bar graph of THOSE companies
• Follow-up viz requests: intent="visualization", preserve previous data context

GROWTH QUERIES:
• "highest growing" = PERCENTAGE GROWTH, not highest value
• "fastest growing" = GROWTH RATE | "biggest increase" = CHANGE/GROWTH
• Calculation: (current - previous) / previous * 100 or (close - open) / open * 100
• Capture growth intent in "explanation", let query planner determine method

CONVERSATION CONTEXT:
• Track previous queries: "top 10 X" → "bar graph" = visualize same data
• Pronouns: "analyze its growth" = company from previous context
• Maintain continuity across conversation"""

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
