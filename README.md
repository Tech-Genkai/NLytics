# NLytics

**Natural Language Analytics Engine**

NLytics is an AI-driven data analysis platform that converts natural language queries into executable analytics code. Built for data analysts, researchers, and business users who need rapid insights without manual coding.

## Architecture

NLytics employs a 9-phase AI pipeline that transforms conversational queries into validated, executable analytics:

1. **Intent Detection** - Natural language understanding using Groq Llama 3.3-70B
2. **Query Refinement** - Semantic optimization for analytical depth
3. **Multi-Step Planning** - Decomposition into logical execution steps
4. **Code Generation** - Pandas/Python synthesis from natural language
5. **Security Validation** - AST parsing and blacklist verification
6. **Sandboxed Execution** - Isolated subprocess with restricted builtins
7. **Insight Generation** - Statistical analysis and visualization configuration
8. **Answer Synthesis** - Plain-language explanation generation
9. **Result Presentation** - Interactive charts with narrative context

## Key Features

- **Real Code Generation** - Generates actual pandas/Python code, not API wrappers
- **Self-Correcting Pipeline** - Automatic retry loops with structured feedback (3 attempts)
- **Multi-Layer Security** - AST parsing, blacklist filtering, and sandboxed execution
- **Context-Aware Intelligence** - Schema analysis and column-aware code generation
- **Interactive Visualizations** - Plotly charts with zoom, pan, and hover tooltips
- **Transparent Execution** - View generated code before execution

## Quick Start

### Prerequisites
- Python 3.9+
- Groq API key ([console.groq.com](https://console.groq.com/keys))

### Installation

```bash
# Clone repository
git clone https://github.com/Tech-Genkai/NLytics.git
cd NLytics

# Configure environment (create .env file)
# Windows PowerShell:
Set-Content -Path .env -Value "GROQ_API_KEY=your_api_key_here"
# Linux/Mac:
echo "GROQ_API_KEY=your_api_key_here" > .env

# Install dependencies
pip install -r backend/requirements.txt

# Start server
python start.py
```

Access the interface at `http://localhost:5000`

## Example Queries

Stock market analysis (`samples/stock_data_july_2025.csv`):
```
"highest growing stock"           → Top 10 comparison with volatility analysis
"average market cap by sector"    → Grouped aggregation with visualizations
"stocks with PE ratio below 15"   → Multi-condition filtering
"correlation between volume and price" → Statistical correlation analysis
```

General analytics patterns:
```
"show me a summary"               → Statistical overview
"average [column] by [category]"  → Grouped aggregation
"distribution of [column]"        → Frequency analysis
"top 10 [column] by [metric]"     → Ranked comparisons
"outliers in [column]"            → Statistical outlier detection
```

## Project Structure

```
NLytics/
├── backend/
│   ├── main.py                         # Flask application core
│   ├── config.py                       # Configuration management
│   ├── requirements.txt                # Python dependencies
│   ├── api/
│   │   └── analytics_api.py            # REST API endpoints
│   ├── services/                       # AI pipeline services
│   │   ├── ai_intent_detector.py       # Natural language understanding
│   │   ├── query_refiner.py            # Semantic query optimization
│   │   ├── query_planner.py            # Multi-step execution planning
│   │   ├── code_generator.py           # LLM-powered code synthesis
│   │   ├── code_validator.py           # Security validation layer
│   │   ├── safe_executor.py            # Sandboxed execution environment
│   │   ├── insight_generator.py        # Statistical analysis & visualization
│   │   ├── answer_synthesizer.py       # Natural language generation
│   │   ├── preprocessor.py             # Data cleaning & normalization
│   │   ├── schema_inspector.py         # Column type detection
│   │   └── file_handler.py             # CSV/Excel operations
│   ├── models/
│   │   └── chat_message.py             # Message type definitions
│   ├── tests/
│   │   ├── automated_test.py           # Integration test suite (60+ scenarios)
│   │   ├── test_api.py                 # API endpoint tests
│   │   ├── test_code_validator.py      # Code validation tests
│   │   ├── test_insight_generator.py   # Insight generation tests
│   │   ├── test_safe_executor.py       # Safe execution tests
│   │   └── test_schema_inspector.py    # Schema inspection tests
│   └── utils/                          # Utility modules
├── frontend/
│   ├── index.html                      # Chat-based interface
│   └── static/
│       ├── js/app.js                   # Client-side logic
│       └── css/style.css               # UI styling
├── data/
│   ├── uploads/                        # User-uploaded datasets
│   └── processed/                      # Preprocessed cache
├── samples/                             # Example datasets
├── docs/                                # Technical documentation
├── .env                                 # Environment configuration
└── start.py                             # Application entry point
```

## Configuration

### Environment Variables
```env
GROQ_API_KEY=your_groq_api_key_here
```

### Supported Formats
- CSV (.csv)
- Excel (.xlsx, .xls)
- Maximum file size: 50MB

### Execution Parameters
- Query timeout: 30 seconds
- Code generation retries: 3 attempts with structured feedback
- Result limit: Configurable (default: top 10 for comparisons)

## Security

### Multi-Layer Validation
1. **AST Parsing** - Syntax validation before execution
2. **Blacklist Filtering** - Blocks dangerous operations (eval, exec, getattr, open, os, sys, subprocess, globals, etc.)
3. **Import Whitelist** - Only pandas and numpy permitted
4. **Column Validation** - Schema-aware code generation
5. **Timeout Enforcement** - 30-second execution limit

### Sandboxed Execution Environment
- Restricted `__builtins__` - Only safe functions available
- Blocked introspection functions (getattr, setattr, globals, locals, vars, dir)
- No `__import__` access to prevent import smuggling
- No file system access
- No network access
- Isolated execution context

## Technical Stack

| Layer | Technology |
|-------|-----------|
| **AI Model** | Groq Llama 3.3-70B (70B parameter model) |
| **Backend** | Flask 3.1.0, Python 3.9+ |
| **Data Processing** | pandas 2.2.3, numpy 2.2.4 |
| **Visualization** | Plotly 5.24.1, Chart.js (fallback) |
| **Frontend** | Vanilla JavaScript, Marked.js |
| **Testing** | pytest, automated integration tests (60+ scenarios) |

## Testing

Run the test suite:
```bash
# All unit tests
python -m pytest backend/tests/ -v

# With coverage report
python -m pytest backend/tests/ --cov=backend/services --cov-report=html

# Automated integration tests (60+ scenarios)
python backend/tests/automated_test.py

# Quick integration test
python backend/tests/automated_test.py --quick
```

**Test Coverage:**
- Code validation (syntax, security, imports)
- Safe execution (error handling, result capture, isolation)
- Insight generation (DataFrames, scalar values, visualizations)
- Schema inspection (column types, statistics)
- Integration tests covering 9 categories: Basic Aggregations, Growth & Performance, Sector Analysis, Complex Queries, Statistical Insights, Rankings, Investment Screening, Natural Language, Edge Cases

## REST API

NLytics provides a REST API for programmatic access:

```bash
# Complete analysis in one call
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "file=@data.csv" \
  -F "query=highest stock by volume"
```

**Available Endpoints:**
- `POST /api/v1/analyze` - Upload & analyze in one call
- `POST /api/v1/query` - Query existing session
- `GET /api/v1/status/<session_id>` - Get session status
- `POST /api/v1/code/validate` - Validate code
- `POST /api/v1/code/execute` - Execute code

Response includes generated code, execution results, Plotly/Chart.js visualization config, narrative insights, and plain-language answer.

See `docs/API.md` for complete API documentation with examples.

## Documentation

- `docs/API.md` - Complete REST API documentation
- `docs/AI_SETUP.md` - Groq API configuration
- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- `docs/PROJECT_COMPLETE.md` - Complete technical architecture

## Design Philosophy

NLytics prioritizes transparency and education over abstraction:

1. **Code Visibility** - Generated pandas code is always visible to users
2. **Query Refinement** - Automatically enhances queries for analytical depth
3. **Schema Awareness** - Understands data types and column relationships
4. **Self-Correction** - Retry loops with structured feedback for robustness
5. **Educational Value** - Learn data analysis by observing code generation

## Design Decisions & Scope

**Why no database?**
- Users analyze sensitive data - storing it creates liability and security risks
- Sessions expire on restart by design - no data retention, no privacy concerns
- This is an analysis tool, not a data warehouse
- Stateless architecture works for Render/cloud deployment

**Why no authentication?**
- Single-user tool - you control access via URL sharing (or lack thereof)
- For public deployment: Render provides basic auth at platform level
- Adding app-level auth is overkill for personal/demo usage
- If you need real auth, add it when you actually have multiple real users

**Why no caching?**
- Queries are rarely identical (different datasets, query variations)
- Groq API responses are fast (~5s average)
- Cache invalidation complexity outweighs benefits for ad-hoc analysis

**Why no Docker?**
- Local development tool for single users
- Python virtual environment is simpler and sufficient
- Docker adds deployment complexity with no benefit for local usage

**Current scope:**
- **Single-user tool**: Runs locally or on Render for personal/demo usage
- **Session-based**: Analyze, get results, close - no persistence by design
- **API-dependent**: Requires Groq API key and internet connection
- **Dataset limits**: Optimized for datasets under 100K rows
- **Stateless**: Works on cloud platforms (Render, Fly.io, Railway) without modifications

**Deployment notes:**
- Render/cloud deployment works out of the box (stateless sessions are fine)
- Use Render's environment variables for `GROQ_API_KEY`
- Use Render's basic auth if you want to restrict access
- In-memory sessions reset on dyno restart - acceptable for demo/personal use

**If you actually need:**
- **Real multi-user SaaS**: Add database, proper auth, rate limiting, billing
- **Enterprise**: Add SSO, audit logs, compliance, SLAs

This tool is intentionally minimal - works for local dev and simple cloud deployment.

## System Requirements

- Python 3.9 or higher
- 2GB RAM minimum
- Internet connection (for Groq API)
- Modern web browser

## License

MIT License

---

**Proof-of-concept natural language analytics engine. Demonstrates AI-powered code generation for data analysis with transparent execution.**