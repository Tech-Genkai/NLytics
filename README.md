# NLytics

**Natural Language Analytics Engine**

NLytics is an AI-powered data analysis platform that transforms natural language questions into executable Python code. Built for data analysts, researchers, and business users who need rapid insights without manual coding.

🚀 **[Live Demo on Render](https://nlytics.onrender.com)** 🚀

---

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Architecture](#architecture)
- [Example Queries](#example-queries)
- [Installation](#installation)
- [Usage](#usage)
- [REST API](#rest-api)
- [Security](#security)
- [Configuration](#configuration)
- [Testing](#testing)
- [Project Scope](#project-scope)
- [License](#license)

---

## Quick Start

### Prerequisites
- **Python 3.9+** (tested on 3.13.7)
- **Groq API key** (free tier available at [console.groq.com](https://console.groq.com/keys))

### Installation

```bash
# Clone repository
git clone https://github.com/Tech-Genkai/NLytics.git
cd NLytics

# Configure environment
echo "GROQ_API_KEY=your_api_key_here" > .env

# Install dependencies
pip install -r backend/requirements.txt

# Start server
python start.py
```

Access the interface at `http://localhost:5000`

---

## Features

### 🤖 AI-Powered Understanding
- **Groq Llama 3.3-70B** for natural language understanding
- Full dataset context awareness (columns, types, samples, statistics)
- Conversation history tracking for contextual queries
- Minimal clarifications needed

### 💻 Real Code Generation
- Generates actual **pandas/Python code**, not API wrappers
- Shows generated code before execution
- Self-correcting with retry logic (3 attempts with structured feedback)
- Validates for syntax, security, and correctness

### 🔒 Multi-Layer Security
- **AST parsing** for syntax validation
- **Blacklist filtering** - blocks dangerous operations (eval, exec, os, sys, file I/O)
- **Import whitelist** - only pandas and numpy allowed
- **Sandboxed execution** with restricted builtins
- **Timeout protection** (30-second default)
- Column-aware validation

### 📊 Smart Visualizations
- Auto-detects best chart type (bar, scatter, pie, box, line)
- Interactive **Plotly** charts with Chart.js fallback
- Professional color palette
- Statistical insights and narrative summaries

### 🎯 Transparent Execution
- View generated code before execution
- Clear error messages with retry feedback
- Execution time tracking
- Export results (CSV, Excel, JSON)

---

## Architecture

NLytics employs a **9-phase AI pipeline** that transforms conversational queries into validated, executable analytics:

```
1. Intent Detection       → Natural language understanding (Groq Llama 3.3-70B)
2. Query Refinement       → Semantic optimization for analytical depth
3. Multi-Step Planning    → Decomposition into logical execution steps
4. Code Generation        → Pandas/Python synthesis from natural language
5. Security Validation    → AST parsing and blacklist verification
6. Sandboxed Execution    → Isolated subprocess with restricted builtins
7. Insight Generation     → Statistical analysis and visualization config
8. Answer Synthesis       → Plain-language explanation generation
9. Result Presentation    → Interactive charts with narrative context
```

### Pipeline Flow

```
User Query
    ↓
AI Intent Detection (Groq Llama 3.3)
    ↓
Query Refinement (Semantic optimization)
    ↓
Query Planning (Multi-step decomposition)
    ↓
Code Generation (Pandas/Python)
    ↓
Validation (Security, Syntax, Logic)
    ↓  [Retry loop with feedback - 3 attempts]
Safe Execution (Sandboxed, Timeout)
    ↓
Insights (Narrative, Plotly viz, Export)
```

---

## Example Queries

Stock market analysis (`samples/stock_data_july_2025.csv`):

```
"highest growing stock"           → Top 10 comparison with volatility analysis
"average market cap by sector"    → Grouped aggregation with visualizations
"stocks with PE ratio below 15"   → Multi-condition filtering
"correlation between volume and price" → Statistical correlation with scatter plot
```

General analytics patterns:

```
"show me a summary"               → Statistical overview
"average [column] by [category]"  → Grouped aggregation
"distribution of [column]"        → Frequency analysis
"top 10 [column] by [metric]"     → Ranked comparisons
"outliers in [column]"            → Statistical outlier detection
```

---

## Installation

### System Requirements
- Python 3.9 or higher
- 2GB RAM minimum
- Internet connection (for Groq API)
- Modern web browser

### Step-by-Step Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Tech-Genkai/NLytics.git
   cd NLytics
   ```

2. **Get your Groq API key:**
   - Visit [console.groq.com/keys](https://console.groq.com/keys)
   - Sign up for free (no credit card required)
   - Create and copy your API key (starts with `gsk_...`)

3. **Configure environment:**
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_actual_key_here" > .env
   ```

4. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

5. **Start the server:**
   ```bash
   python start.py
   ```

6. **Open your browser:**
   Navigate to `http://localhost:5000`

---

## Usage

### Chat Interface

1. **Upload Data**
   - Click "📤 Upload Data" button
   - Select CSV or Excel file (max 50MB)
   - Wait for preprocessing confirmation

2. **Ask Questions**
   - Type natural language queries
   - Press Enter to send
   - View generated code, results, and insights

3. **View Insights**
   - Interactive Plotly charts
   - Statistical summaries
   - Key findings and recommendations

### Supported File Formats
- CSV (.csv)
- Excel (.xlsx, .xls)
- Maximum file size: 50MB

---

## REST API

NLytics provides a comprehensive REST API for programmatic access.

### Base URL
- **Production:** `https://nlytics.onrender.com/api/v1`
- **Local:** `http://localhost:5000/api/v1`

### Quick Example

```bash
# Complete analysis in one call
curl -X POST https://nlytics.onrender.com/api/v1/analyze \
  -F "file=@data.csv" \
  -F "query=highest stock by volume"
```

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Upload & analyze in one call |
| `/query` | POST | Query existing session |
| `/status/<session_id>` | GET | Get session status |
| `/code/validate` | POST | Validate code |
| `/code/execute` | POST | Execute code |
| `/health` | GET | Health check |

### Response Format

```json
{
  "success": true,
  "status": "completed",
  "query": {
    "original": "highest stock",
    "refined": "top 10 stocks comparison",
    "intent": {...}
  },
  "code": {
    "generated": "df.nlargest(10, 'Close')...",
    "execution_time": 0.23
  },
  "result": {
    "data": [...]
  },
  "visualization": {
    "type": "bar",
    "plotly": "{...}",
    "config": {...}
  },
  "insights": {
    "narrative": "...",
    "key_findings": [...]
  },
  "answer": "Based on the data, AAPL is the highest..."
}
```

See **DEV_GUIDE.md** for complete API documentation with examples.

---

## Security

### Multi-Layer Validation

1. **AST Parsing** - Syntax validation before execution
2. **Blacklist Filtering** - Blocks dangerous operations:
   - `eval`, `exec`, `compile`, `__import__`
   - `open`, `input`, `getattr`, `setattr`
   - `os`, `sys`, `subprocess`, `socket`
   - `globals`, `locals`, `vars`, `dir`
3. **Import Whitelist** - Only pandas and numpy permitted
4. **Column Validation** - Schema-aware code generation
5. **Timeout Enforcement** - 30-second execution limit

### Sandboxed Execution Environment

- **Restricted builtins** - Only safe functions available
- **No introspection** - Blocked getattr, setattr, globals, locals
- **No imports** - Prevented __import__ access
- **No file system** - No read/write operations
- **No network** - No external connections
- **Isolated context** - Each execution is independent

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_secret_key_for_flask  # Optional
FLASK_ENV=development  # or production
PORT=5000  # Optional, default is 5000
```

### Execution Parameters

Configurable in `backend/config.py`:

```python
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB file upload limit
API_TIMEOUT = 30  # API request timeout (seconds)
MAX_RETRIES = 3  # Code generation retry attempts
EXECUTION_TIMEOUT = 300  # Code execution timeout (5 minutes)
MAX_ROWS = 1_000_000  # Maximum rows to process
MAX_COLUMNS = 500  # Maximum columns to process
```

---

## Testing

### Run Tests

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

### Test Coverage

- **Code validation** - Syntax, security, imports
- **Safe execution** - Error handling, result capture, isolation
- **Insight generation** - DataFrames, scalars, visualizations
- **Schema inspection** - Column types, statistics
- **Integration tests** - 60+ scenarios covering:
  - Basic aggregations
  - Growth & performance analysis
  - Sector comparisons
  - Complex queries
  - Statistical insights
  - Rankings
  - Investment screening
  - Natural language variations
  - Edge cases

---

## Project Scope

### What This Is
- **Proof-of-concept** validating AI-powered code generation
- **Educational tool** demonstrating LLM-powered analytics
- **Personal analysis tool** for local use and demos
- **Architecture blueprint** for conversational analytics

### What This Is NOT
- Production-ready SaaS platform
- Enterprise-grade software
- Fully hardened security system
- Scalable multi-user service

### Design Philosophy

NLytics prioritizes **transparency and education** over abstraction:

1. **Code Visibility** - Generated pandas code is always visible
2. **Query Refinement** - Automatically enhances queries for analytical depth
3. **Schema Awareness** - Understands data types and relationships
4. **Self-Correction** - Retry loops with structured feedback
5. **Educational Value** - Learn data analysis by observing code generation

### Design Decisions

**Why no database?**
- Users analyze sensitive data - no storage = no liability
- Sessions expire on restart by design
- This is an analysis tool, not a data warehouse
- Stateless architecture works for cloud deployment

**Why no authentication?**
- Single-user tool - control access via URL sharing
- For public deployment: use Render's basic auth
- Adding app-level auth is overkill for demos

**Why no caching?**
- Queries are rarely identical
- Groq API responses are fast (~5s average)
- Cache invalidation complexity outweighs benefits

**Why no Docker?**
- Local development tool for single users
- Python virtual environment is simpler
- Docker adds complexity with no benefit

### Current Scope
- **Single-user** - Local or Render deployment
- **Session-based** - No persistence by design
- **API-dependent** - Requires Groq API key
- **Dataset limits** - Optimized for <100K rows
- **Stateless** - Works on cloud platforms

---

## Technical Stack

| Layer | Technology |
|-------|-----------|
| **AI Model** | Groq Llama 3.3-70B (70B parameters) |
| **Backend** | Flask 3.1.0, Python 3.9+ |
| **Data Processing** | pandas 2.2.3, numpy 2.2.4 |
| **Visualization** | Plotly 5.24.1, Chart.js fallback |
| **Frontend** | Vanilla JavaScript, Marked.js |
| **Testing** | pytest, 60+ integration scenarios |

---

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
│   │   ├── query_refiner.py            # Query optimization
│   │   ├── query_planner.py            # Multi-step planning
│   │   ├── code_generator.py           # LLM code synthesis
│   │   ├── code_validator.py           # Security validation
│   │   ├── safe_executor.py            # Sandboxed execution
│   │   ├── insight_generator.py        # Statistical insights
│   │   ├── answer_synthesizer.py       # Natural language answers
│   │   ├── preprocessor.py             # Data cleaning
│   │   ├── schema_inspector.py         # Column analysis
│   │   └── file_handler.py             # File operations
│   ├── models/
│   │   └── chat_message.py             # Message types
│   ├── tests/                          # Test suite
│   │   ├── automated_test.py           # Integration tests (60+)
│   │   ├── test_api.py
│   │   ├── test_code_validator.py
│   │   ├── test_insight_generator.py
│   │   ├── test_safe_executor.py
│   │   └── test_schema_inspector.py
│   └── utils/                          # Utility modules
├── frontend/
│   ├── index.html                      # Chat interface
│   └── static/
│       ├── js/app.js                   # Client logic
│       └── css/style.css               # Styling
├── data/
│   ├── uploads/                        # User files
│   └── processed/                      # Cleaned data
├── samples/                            # Example datasets
├── .env                                # Environment config
├── .gitignore
├── README.md                           # This file
├── DEV_GUIDE.md                        # Developer guide
└── start.py                            # Application entry point
```

---

## Troubleshooting

### Common Issues

**"GROQ_API_KEY not found"**
- Ensure `.env` file exists in project root
- Verify API key is correct (starts with `gsk_...`)
- Restart server after creating `.env`

**"Address already in use" (Port 5000)**
```powershell
# Windows: Kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or change port in backend/main.py
```

**"File type not supported"**
- Only CSV (.csv) and Excel (.xlsx, .xls) supported
- File must be under 50MB
- Try re-saving as CSV (UTF-8)

**"Column not found"**
- Use exact column names from upload confirmation
- Preprocessing normalizes names (spaces → underscores)
- Check health report for actual column names

**"No dataset loaded"**
- Upload a file before asking questions
- Check if upload completed successfully
- Try refreshing the page

For more troubleshooting, see **DEV_GUIDE.md**.

---

## Contributing

This is a proof-of-concept project. Contributions are welcome for:
- Bug fixes
- Documentation improvements
- Test coverage expansion
- Additional visualization types
- Performance optimizations

Please open an issue before submitting large changes.

---

## License

MIT License - See LICENSE file for details.

---

## Acknowledgments

- **Groq** for fast LLM inference
- **Plotly** for interactive visualizations
- **pandas** and **numpy** for data processing
- **Flask** for web framework

---

**Built with ❤️ by Tech-Genkai**

*Proof-of-concept demonstrating AI-powered natural language to code generation for data analytics.*
