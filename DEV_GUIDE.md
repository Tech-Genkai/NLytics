# NLytics Developer Guide

Complete technical documentation for developers working with NLytics.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Setup & Configuration](#setup--configuration)
3. [REST API Reference](#rest-api-reference)
4. [Service Components](#service-components)
5. [Code Generation](#code-generation)
6. [Security & Validation](#security--validation)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)
10. [Development Workflow](#development-workflow)

---

## Architecture Overview

### 9-Phase AI Pipeline

NLytics implements a sophisticated pipeline that transforms natural language into executable analytics:

```
Phase 1: File Upload & Schema Inspection
   ↓
Phase 2: Data Preprocessing & Cleaning
   ↓
Phase 3: AI Intent Detection (Groq Llama 3.3-70B)
   ↓
Phase 3.5: Query Refinement
   ↓
Phase 4: Multi-Step Query Planning
   ↓
Phase 5: Code Generation (AI-powered)
   ↓
Phase 6: Validation & Security Checks
   ↓  [Retry loop with feedback - up to 3 attempts]
Phase 7: Sandboxed Execution
   ↓
Phase 8: Insight Generation & Visualization
   ↓
Phase 9: Answer Synthesis & Presentation
```

### Component Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (Vanilla JS)           │
│  - Chat Interface (index.html)          │
│  - Message Rendering (app.js)           │
│  - Plotly/Chart.js Integration          │
└─────────────────┬───────────────────────┘
                  │ HTTP/REST
┌─────────────────▼───────────────────────┐
│         Flask Backend (main.py)         │
│  - Session Management (File-based)      │
│  - Route Handlers                       │
│  - Error Handling                       │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌──────▼─────────┐
│  Chat API      │  │  REST API      │
│  /api/chat     │  │  /api/v1/*     │
│  /api/upload   │  │  /api/v1/analyze│
│  /api/session  │  │  /api/v1/query │
└───────┬────────┘  └──────┬─────────┘
        │                   │
        └─────────┬─────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Service Layer                   │
│  ┌────────────────────────────────┐    │
│  │  AI Services (Groq)            │    │
│  │  - Intent Detector             │    │
│  │  - Query Refiner               │    │
│  │  - Query Planner               │    │
│  │  - Code Generator              │    │
│  │  - Answer Synthesizer          │    │
│  └────────────────────────────────┘    │
│  ┌────────────────────────────────┐    │
│  │  Data Services                 │    │
│  │  - File Handler                │    │
│  │  - Schema Inspector            │    │
│  │  - Preprocessor                │    │
│  └────────────────────────────────┘    │
│  ┌────────────────────────────────┐    │
│  │  Execution Services            │    │
│  │  - Code Validator              │    │
│  │  - Safe Executor               │    │
│  │  - Insight Generator           │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### Data Flow

```
1. User uploads CSV/Excel
   → FileHandler loads file
   → SchemaInspector analyzes columns
   → Preprocessor cleans data
   → Session stores metadata

2. User asks question
   → AIIntentDetector understands query
   → QueryRefiner optimizes query
   → QueryPlanner creates execution plan
   → CodeGenerator produces pandas code
   → CodeValidator checks security
   → SafeExecutor runs in sandbox
   → InsightGenerator creates visualizations
   → AnswerSynthesizer generates response
   → Frontend displays results
```

---

## Setup & Configuration

### Environment Variables

Create `.env` file in project root:

```env
# Required
GROQ_API_KEY=gsk_your_api_key_here

# Optional
SECRET_KEY=your_flask_secret_key
FLASK_ENV=development
PORT=5000
```

### Configuration File

`backend/config.py`:

```python
# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Flask settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('FLASK_ENV', 'development') == 'development'

# File upload settings
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'
PROCESSED_FOLDER = BASE_DIR / 'data' / 'processed'

# API settings
API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Model settings
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# Session settings
SESSION_TIMEOUT = 3600  # 1 hour

# Processing limits
MAX_ROWS = 1_000_000
MAX_COLUMNS = 500
EXECUTION_TIMEOUT = 300  # 5 minutes
```

### Dependencies

`backend/requirements.txt`:

```
Flask>=3.0.0
flask-cors>=4.0.0
Werkzeug>=3.0.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
plotly>=5.18.0
python-dotenv>=1.0.0
groq>=0.4.0
gunicorn>=21.2.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

---

## REST API Reference

### Base URLs

- **Production:** `https://nlytics.onrender.com/api/v1`
- **Local:** `http://localhost:5000/api/v1`

### Authentication

None required in current version. Access control managed at deployment level.

---

### POST /api/v1/analyze

Complete analysis in one request.

**Content-Type:** `multipart/form-data`

**Request Parameters:**
- `file` (required) - CSV/Excel file
- `query` (required) - Natural language question
- `return_code` (optional) - Include generated code (default: true)
- `return_visualization` (optional) - Include chart config (default: true)

**Example Request:**

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "file=@stock_data.csv" \
  -F "query=highest growing stock" \
  -F "return_code=true"
```

**Response (200 OK):**

```json
{
  "success": true,
  "status": "completed",
  "query": {
    "original": "highest growing stock",
    "refined": "top 10 stocks by growth comparison",
    "intent": {
      "type": "ranking",
      "explanation": "User wants to find and compare highest performing stocks"
    }
  },
  "code": {
    "generated": "df['growth'] = ((df['Close'] - df['Open']) / df['Open']) * 100\nresult = df.nlargest(10, 'growth')[['Symbol', 'growth']].round(2)",
    "language": "python",
    "explanation": "Calculate growth rate and get top 10",
    "execution_time": 0.23
  },
  "result": {
    "data": [
      {"Symbol": "AAPL", "growth": 15.3},
      {"Symbol": "MSFT", "growth": 12.1}
    ],
    "type": "DataFrame"
  },
  "visualization": {
    "type": "bar",
    "suitable": true,
    "plotly": "{\"data\": [...], \"layout\": {...}}",
    "x_column": "Symbol",
    "y_column": "growth",
    "x_values": ["AAPL", "MSFT", "GOOGL"],
    "y_values": [15.3, 12.1, 10.5],
    "colors": ["#3b82f6", "#10b981", "#f59e0b"],
    "description": "Growth Rate (%) by Symbol",
    "y_label": "Growth Rate (%)"
  },
  "insights": {
    "narrative": "AAPL leads with growth rate of 15.3%, while MSFT follows at 12.1%.",
    "key_findings": [
      "Highest: AAPL (15.3%)",
      "Average across all: 9.2%"
    ],
    "recommendations": [
      "Export data for further analysis",
      "Compare with other time periods"
    ]
  },
  "answer": "Based on the data, AAPL is the highest growing stock with a 15.3% increase."
}
```

---

### POST /api/v1/query

Execute query on existing session.

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "session_id": "abc-123",
  "query": "show average price by sector"
}
```

**Response:** Same structure as `/analyze`

---

### GET /api/v1/status/<session_id>

Get session status and dataset info.

**Response (200 OK):**

```json
{
  "session_id": "abc-123",
  "status": "active",
  "dataset": {
    "loaded": true,
    "filename": "stock_data.csv",
    "rows": 4348,
    "columns": 14,
    "column_names": ["Symbol", "Date", "Open", "Close", "Volume"]
  },
  "message_count": 5,
  "created_at": "2025-11-05T10:30:00Z"
}
```

---

### POST /api/v1/code/validate

Validate Python code without execution.

**Request Body:**

```json
{
  "code": "df.nlargest(10, 'Close')",
  "columns": ["Close", "Open", "High", "Low"]
}
```

**Response (200 OK):**

```json
{
  "is_valid": true,
  "errors": [],
  "warnings": []
}
```

**Response (400 Bad Request):**

```json
{
  "is_valid": false,
  "errors": [
    {
      "type": "SecurityError",
      "message": "Dangerous operation detected: eval",
      "line": 5
    }
  ],
  "warnings": [
    {
      "type": "ColumnWarning",
      "message": "Column 'price' not found in dataset"
    }
  ]
}
```

---

### POST /api/v1/code/execute

Execute validated code on session dataset.

**Request Body:**

```json
{
  "session_id": "abc-123",
  "code": "df.nlargest(10, 'Close')"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "result": [...],
  "execution_time": 0.15
}
```

**Response (500 Internal Server Error):**

```json
{
  "success": false,
  "error": "Column 'Close' not found in dataset"
}
```

---

### GET /api/health

Health check endpoint.

**Response (200 OK):**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "api_version": "v1",
  "features": {
    "chat_interface": true,
    "rest_api": true,
    "code_generation": true,
    "visualization": true,
    "colorful_charts": true
  },
  "endpoints": {
    "analyze": "/api/v1/analyze",
    "query": "/api/v1/query",
    "validate_code": "/api/v1/code/validate",
    "execute_code": "/api/v1/code/execute",
    "status": "/api/v1/status/<session_id>"
  }
}
```

---

### Error Responses

#### 400 Bad Request
```json
{
  "error": "Query is required"
}
```

#### 404 Not Found
```json
{
  "error": "Session not found"
}
```

#### 413 Payload Too Large
```json
{
  "error": "File too large. Maximum size is 50MB"
}
```

#### 500 Internal Server Error
```json
{
  "error": "Execution failed",
  "details": "Column 'X' not found in dataset"
}
```

---

## Service Components

### 1. FileHandler (`services/file_handler.py`)

Handles file upload and loading operations.

```python
class FileHandler:
    def load_file(self, file_path: str) -> pd.DataFrame:
        """Load CSV or Excel file into DataFrame"""
        
    def save_file(self, df: pd.DataFrame, filename: str, format: str) -> str:
        """Save DataFrame to file"""
```

**Supported Formats:**
- CSV (.csv)
- Excel (.xlsx, .xls)

---

### 2. SchemaInspector (`services/schema_inspector.py`)

Analyzes DataFrame schema and column statistics.

```python
class SchemaInspector:
    def inspect(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """
        Returns:
        {
            'filename': str,
            'row_count': int,
            'column_count': int,
            'columns': [
                {
                    'name': str,
                    'type': 'numeric'|'categorical'|'datetime'|'boolean',
                    'missing_count': int,
                    'missing_percentage': float,
                    'unique_count': int,
                    'sample_values': list
                }
            ]
        }
        """
```

**Column Type Inference:**
- **Numeric:** int64, float64
- **Categorical:** object with <50% unique values
- **Datetime:** datetime64, date strings
- **Boolean:** bool, binary values
- **Text:** object with >50% unique values

---

### 3. Preprocessor (`services/preprocessor.py`)

Cleans and normalizes data.

```python
class DataPreprocessor:
    def preprocess(self, df: pd.DataFrame, filename: str) -> Tuple[pd.DataFrame, Dict]:
        """
        Returns: (cleaned_df, preprocessing_manifest)
        
        Manifest:
        {
            'steps_applied': ['normalize_names', 'handle_missing', ...],
            'column_changes': {...},
            'missing_values': {...},
            'outliers_detected': {...},
            'duplicates_removed': int
        }
        """
```

**Preprocessing Steps:**
1. Normalize column names (lowercase, underscores)
2. Detect and handle missing values
3. Identify outliers (IQR method)
4. Remove duplicate rows
5. Convert data types

---

### 4. AIIntentDetector (`services/ai_intent_detector.py`)

AI-powered query understanding using Groq Llama 3.3-70B.

```python
class AIIntentDetector:
    def detect_intent(
        self,
        query: str,
        df: pd.DataFrame,
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            'intent': 'ranking'|'aggregation'|'filtering'|'statistical'|...,
            'query_type': str,
            'entities': {
                'columns': List[str],
                'operations': List[str],
                'filters': List[Dict],
                'group_by': Optional[str],
                'sort_by': Optional[str],
                'limit': Optional[int]
            },
            'explanation': str,
            'clarifications_needed': List[str]
        }
        """
```

**Intent Types:**
- **ranking** - Top N, best, worst
- **aggregation** - Sum, average, count
- **filtering** - Where, having conditions
- **statistical** - Correlation, distribution
- **comparison** - Differences, changes
- **grouping** - Group by, pivot

---

### 5. QueryRefiner (`services/query_refiner.py`)

Optimizes queries for better analytics.

```python
class QueryRefiner:
    def refine_query(
        self,
        query: str,
        intent_result: Dict,
        dataset_context: str
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            'refinement_applied': bool,
            'refined_query': str,
            'reasoning': str,
            'requested_chart_type': Optional[str]
        }
        """
```

**Refinement Patterns:**
- "highest X" → "top 10 X comparison"
- "average" → "average with distribution analysis"
- "show chart" → Specific chart type detection

---

### 6. QueryPlanner (`services/query_planner.py`)

Creates multi-step execution plans.

```python
class QueryPlanner:
    def create_plan(
        self,
        query: str,
        intent_result: Dict,
        dataset_summary: Dict
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            'needs_planning': bool,
            'complexity': 'simple'|'moderate'|'complex',
            'steps': [
                {
                    'step_num': int,
                    'operation': str,
                    'description': str,
                    'depends_on': List[int]
                }
            ],
            'estimated_time': float
        }
        """
```

**Complexity Levels:**
- **Simple:** Single operation (filter, sort, aggregate)
- **Moderate:** 2-3 operations (filter + aggregate + sort)
- **Complex:** 4+ operations with dependencies

---

### 7. CodeGenerator (`services/code_generator.py`)

AI-powered pandas code generation.

```python
class CodeGenerator:
    def generate_code(
        self,
        query: str,
        intent_result: Dict,
        execution_plan: Dict,
        df_columns: List[str],
        df_dtypes: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            'code': str,  # Executable pandas code
            'explanation': str,
            'imports': List[str],
            'variables': Dict[str, str],
            'warnings': List[str]
        }
        """
```

**Code Generation Rules:**
1. Input DataFrame always named `df`
2. Result must be stored in `result` variable
3. Only pandas (`pd`) and numpy (`np`) allowed
4. No import statements in generated code
5. No file I/O or system calls
6. No plotting code (handled separately)

**Example Generated Code:**

```python
# Calculate growth rate
df['growth'] = ((df['Close'] - df['Open']) / df['Open']) * 100

# Get top 10 by growth
result = df.nlargest(10, 'growth')[['Symbol', 'Date', 'growth']]

# Round for readability
result = result.round(2)
```

---

### 8. CodeValidator (`services/code_validator.py`)

Security and syntax validation.

```python
class CodeValidator:
    def validate(
        self,
        code: str,
        df_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            'valid': bool,
            'errors': List[Dict],
            'warnings': List[Dict],
            'security_check': bool,
            'syntax_check': bool
        }
        """
```

**Validation Checks:**

1. **Syntax Check** - AST parsing
2. **Security Check** - Blacklist dangerous operations:
   - `eval`, `exec`, `compile`, `__import__`
   - `open`, `input`, `file`
   - `os`, `sys`, `subprocess`, `socket`
   - `getattr`, `setattr`, `delattr`
   - `globals`, `locals`, `vars`, `dir`
3. **Import Check** - Only pandas/numpy allowed
4. **Column Check** - Verify columns exist in dataset

**Retry Manager:**

```python
class RetryManager:
    def should_retry(self, attempt: int, validation_result: Dict) -> Tuple[bool, str]:
        """
        Determines if code generation should retry
        Returns: (should_retry, feedback_message)
        """
```

---

### 9. SafeExecutor (`services/safe_executor.py`)

Sandboxed code execution with timeouts.

```python
class SafeExecutor:
    def execute(
        self,
        code: str,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            'success': bool,
            'result': Any,  # DataFrame, Series, scalar, etc.
            'execution_time': float,
            'stdout': str,
            'stderr': str,
            'error': Optional[str]
        }
        """
```

**Sandbox Restrictions:**

```python
restricted_builtins = {
    # Allowed
    'abs', 'all', 'any', 'bool', 'dict', 'enumerate',
    'filter', 'float', 'int', 'isinstance', 'len',
    'list', 'map', 'max', 'min', 'range', 'round',
    'set', 'sorted', 'str', 'sum', 'tuple', 'type',
    'zip', 'True', 'False', 'None',
    
    # Blocked (not in dict)
    'eval', 'exec', 'compile', '__import__',
    'open', 'input', 'getattr', 'setattr',
    'globals', 'locals', 'vars', 'dir'
}
```

**Timeout Handling:**
- Default: 30 seconds
- Configurable per execution
- Raises `ExecutionTimeout` exception

---

### 10. InsightGenerator (`services/insight_generator.py`)

Statistical analysis and visualization config.

```python
class InsightGenerator:
    def generate_insights(
        self,
        result: Any,
        query: str,
        execution_time: float,
        requested_chart_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            'narrative': str,
            'key_findings': List[str],
            'recommendations': List[str],
            'visualization': {
                'type': 'bar'|'scatter'|'pie'|'box'|'line',
                'suitable': bool,
                'plotly': str,  # JSON Plotly figure
                'config': {...}  # Chart.js fallback
            },
            'export_options': List[str]
        }
        """
```

**Chart Type Selection:**

| Data Type | Chart Type | Use Case |
|-----------|------------|----------|
| DataFrame (categorical + numeric) | Bar | Comparisons, rankings |
| DataFrame (2 numeric columns) | Scatter | Correlations, relationships |
| Series (categorical) | Pie | Distributions, proportions |
| Series (numeric) | Box | Outliers, quartiles |
| DataFrame (time series) | Line | Trends over time |

**Color Palette:**

```python
COLORS = [
    '#3b82f6',  # Blue
    '#10b981',  # Green
    '#f59e0b',  # Amber
    '#ef4444',  # Red
    '#8b5cf6',  # Purple
    '#ec4899',  # Pink
    '#14b8a6',  # Teal
    '#f97316',  # Orange
    '#6366f1',  # Indigo
    '#84cc16',  # Lime
    '#06b6d4',  # Cyan
    '#f43f5e'   # Rose
]
```

---

### 11. AnswerSynthesizer (`services/answer_synthesizer.py`)

Generates plain-language answers.

```python
class AnswerSynthesizer:
    def synthesize_answer(
        self,
        query: str,
        result: Any,
        context: Dict[str, Any]
    ) -> str:
        """
        Returns plain-language answer to user's question
        
        Context:
        {
            'refined_query': Optional[str],
            'execution_time': float
        }
        """
```

**Answer Templates:**

- **DataFrame result:** "Based on the data, here are the top results: ..."
- **Scalar result:** "The answer is [value]"
- **Statistical result:** "The analysis shows: ..."

---

## Code Generation

### Prompt Engineering

The code generator uses a sophisticated system prompt:

```
**EXECUTION ENVIRONMENT:**
- `df`: pandas.DataFrame (pre-loaded)
- `pd`: pandas module (pre-imported)
- `np`: numpy module (pre-imported)
- NO file system access
- NO network access
- NO subprocess/system calls

**CRITICAL RULES:**
1. Input dataframe is `df`
2. Final result stored in `result`
3. Use only pandas and numpy
4. NO import statements
5. NO file I/O operations
6. NO plotting code
7. Handle edge cases
```

### Common Code Patterns

**Top N by column:**
```python
result = df.nlargest(10, 'column_name')[['col1', 'col2', 'col3']]
```

**Growth calculation:**
```python
df['growth'] = ((df['end'] - df['start']) / df['start'] * 100)
result = df.nlargest(10, 'growth')
```

**Aggregation with grouping:**
```python
result = df.groupby('category')['value'].mean().reset_index()
result.columns = ['category', 'avg_value']
result = result.sort_values('avg_value', ascending=False)
```

**Filtering:**
```python
result = df[df['column'] > threshold].copy()
```

**Complex calculations:**
```python
df['new_metric'] = (df['col1'] + df['col2']) / df['col3']
result = df.nlargest(10, 'new_metric')[['id', 'name', 'new_metric']]
```

---

## Security & Validation

### Security Layers

```
Layer 1: AST Parsing
   ↓ (validates syntax)
Layer 2: Blacklist Check
   ↓ (blocks dangerous operations)
Layer 3: Import Whitelist
   ↓ (only pandas, numpy)
Layer 4: Column Validation
   ↓ (verify columns exist)
Layer 5: Sandboxed Execution
   ↓ (restricted builtins, timeout)
Result
```

### Dangerous Operations Blacklist

```python
BLACKLIST = {
    # Code execution
    'eval', 'exec', 'compile', '__import__',
    
    # File system
    'open', 'file', 'input', 'raw_input',
    
    # System access
    'os', 'sys', 'subprocess', 'socket',
    'commands', 'popen', 'execfile',
    
    # Introspection
    'getattr', 'setattr', 'delattr', 'hasattr',
    'globals', 'locals', 'vars', 'dir',
    '__dict__', '__class__', '__bases__',
    
    # Module loading
    'importlib', 'imp', '__loader__',
    
    # Other dangerous
    'breakpoint', 'exit', 'quit', 'reload'
}
```

### Column Validation

```python
def validate_columns(code: str, df_columns: List[str]) -> List[str]:
    """
    Extract column references from code and verify they exist
    
    Detects:
    - df['column_name']
    - df.column_name
    - df[['col1', 'col2']]
    """
```

---

## Testing

### Test Structure

```
backend/tests/
├── automated_test.py           # Integration tests (60+ scenarios)
├── test_api.py                 # API endpoint tests
├── test_code_validator.py      # Code validation tests
├── test_insight_generator.py   # Insight generation tests
├── test_safe_executor.py       # Safe execution tests
└── test_schema_inspector.py    # Schema inspection tests
```

### Running Tests

```bash
# All tests
python -m pytest backend/tests/ -v

# Specific test file
python -m pytest backend/tests/test_safe_executor.py -v

# With coverage
python -m pytest backend/tests/ --cov=backend/services --cov-report=html

# Integration tests
python backend/tests/automated_test.py

# Quick integration test
python backend/tests/automated_test.py --quick
```

### Test Coverage Areas

1. **Code Validation**
   - Syntax errors
   - Security violations
   - Import restrictions
   - Column references

2. **Safe Execution**
   - Successful execution
   - Error handling
   - Timeout enforcement
   - Result capture

3. **Insight Generation**
   - DataFrame insights
   - Scalar insights
   - Visualization suggestions
   - Color palette

4. **Schema Inspection**
   - Type inference
   - Missing values
   - Sample values
   - Statistics

5. **Integration**
   - Basic aggregations
   - Growth analysis
   - Sector comparisons
   - Complex queries
   - Statistical insights
   - Rankings
   - Edge cases

### Example Test

```python
def test_safe_execution():
    executor = SafeExecutor()
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    
    code = "result = df.nlargest(2, 'A')"
    result = executor.execute(code, df)
    
    assert result['success'] == True
    assert len(result['result']) == 2
    assert result['execution_time'] > 0
```

---

## Deployment

### Local Development

```bash
# Start development server
python start.py

# Or use Flask directly
cd backend
python main.py
```

### Production (Render)

1. **Create `render.yaml`:**

```yaml
services:
  - type: web
    name: nlytics
    env: python
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "gunicorn -w 4 -b 0.0.0.0:$PORT backend.main:app"
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: FLASK_ENV
        value: production
```

2. **Configure environment variables** in Render dashboard

3. **Deploy** via Git push or manual deploy

### Gunicorn Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
```

---

## Troubleshooting

### Common Development Issues

**Import errors:**
```bash
# Ensure you're in the correct directory
cd backend
python -c "import services.code_generator"
```

**API key not found:**
```bash
# Check .env file exists
cat .env

# Verify environment variable
python -c "import os; print(os.environ.get('GROQ_API_KEY'))"
```

**Port already in use:**
```powershell
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

**File upload fails:**
- Check `data/uploads/` directory exists
- Verify permissions (read/write)
- Check file size (<50MB)

**Code validation fails:**
- Check blacklist in `code_validator.py`
- Verify column names match dataset
- Review generated code in logs

**Execution timeout:**
- Increase timeout in `safe_executor.py`
- Simplify query
- Check for infinite loops

### Debugging

**Enable verbose logging:**

```python
# backend/main.py
logging.basicConfig(level=logging.DEBUG)
```

**View generated code:**

Check terminal output after query:
```
📝 Phase 5: Generating code...
✅ Code generated (XXX chars)
📝 Generated code:
<code appears here>
```

**Inspect session data:**

```python
# In Python console
import json
with open('backend/data/sessions/<session_id>.json') as f:
    session = json.load(f)
print(json.dumps(session, indent=2))
```

---

## Development Workflow

### Adding New Features

1. **Create feature branch:**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Implement service:**
   - Add to `backend/services/`
   - Follow existing patterns
   - Add type hints

3. **Write tests:**
   - Add to `backend/tests/`
   - Test happy path and edge cases
   - Run tests: `pytest backend/tests/ -v`

4. **Update documentation:**
   - Update this DEV_GUIDE.md
   - Update README.md if needed

5. **Submit PR:**
   - Ensure all tests pass
   - Include example usage

### Code Style

- Follow PEP 8
- Use type hints
- Document complex logic
- Keep functions focused
- Use descriptive variable names

### Git Workflow

```bash
# Feature branch
git checkout -b feature/visualization-enhancements

# Make changes
git add backend/services/insight_generator.py
git commit -m "Add pie chart support"

# Push and create PR
git push origin feature/visualization-enhancements
```

---

## Performance Optimization

### Caching Strategies (Not Implemented)

Why no caching?
- Queries are rarely identical
- Dataset variations make cache ineffective
- Groq API is fast (~5s average)

If you need caching:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def generate_code_cached(query_hash, intent_hash):
    # Implementation
    pass
```

### Dataset Optimization

For large datasets (>100K rows):
- Use sampling for exploration
- Aggregate before analysis
- Consider chunking

```python
# Sample large dataset
if len(df) > 100_000:
    df_sample = df.sample(n=100_000, random_state=42)
```

---

## Future Enhancements

### Potential Improvements

1. **More Chart Types**
   - Heatmaps
   - Box plots
   - Network graphs
   - 3D scatter plots

2. **Advanced Analytics**
   - Time series forecasting
   - Clustering analysis
   - Regression models
   - Anomaly detection

3. **Export Options**
   - PDF reports
   - LaTeX tables
   - PowerPoint slides

4. **Query Templates**
   - Saved queries
   - Query history
   - Shareable templates

5. **Multi-File Support**
   - Join multiple datasets
   - Cross-file comparisons
   - Data merging

---

## API Client Examples

### Python Client

```python
import requests

def analyze_data(file_path, query):
    url = "http://localhost:5000/api/v1/analyze"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'query': query,
            'return_code': 'true',
            'return_visualization': 'true'
        }
        
        response = requests.post(url, files=files, data=data)
    
    return response.json()

# Usage
result = analyze_data('data.csv', 'top 10 stocks by volume')
print(result['answer'])
```

### JavaScript Client

```javascript
async function analyzeData(file, query) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('query', query);
    
    const response = await fetch('http://localhost:5000/api/v1/analyze', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

// Usage
const file = document.getElementById('file-input').files[0];
const result = await analyzeData(file, 'average price by sector');
console.log(result.answer);
```

### cURL Examples

```bash
# Analyze
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "file=@data.csv" \
  -F "query=highest growing stock"

# Validate code
curl -X POST http://localhost:5000/api/v1/code/validate \
  -H "Content-Type: application/json" \
  -d '{"code": "df.describe()", "columns": ["A", "B"]}'

# Health check
curl http://localhost:5000/api/health
```

---

## License

MIT License - See LICENSE file for details.

---

**Last Updated:** November 2025

**Maintained by:** Tech-Genkai

**Questions?** Open an issue on GitHub: https://github.com/Tech-Genkai/NLytics/issues
