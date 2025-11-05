#  NLytics - Conversational Data Analytics

**Ask questions in plain English. Get AI-powered insights with visualizations.**

NLytics lets you analyze data through natural conversation. Upload a CSV, ask questions like "highest growing stock" or "average sales by region", and get interactive charts with plain-language explanations.

---

##  Features

-  **AI-Powered**: Uses Groq Llama 3.3-70B to understand your questions
-  **Code Generation**: Generates real pandas/Python code from natural language
-  **Interactive Charts**: Bar, line, and scatter plots with Chart.js
-  **Smart Query Refinement**: Turns "highest X" into "top 10 comparison" for better insights
-  **Plain-Language Answers**: Get explanations, not just raw numbers
-  **Safe Execution**: Sandboxed environment with validation layers

---

##  Quick Start

### 1. Get a Groq API Key
- Sign up at [console.groq.com](https://console.groq.com/keys)
- Free tier works perfectly!

### 2. Set Up Environment
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Install & Run
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start the server
python start.py
```

### 4. Open Your Browser
```
http://localhost:5000
```

---

##  Example Queries

Upload `samples/stock_data_july_2025.csv` and try:

- **"highest growing stock"** → Top 10 comparison with bar chart
- **"average price by sector"** → Grouped analysis with insights
- **"show outliers in volume"** → Statistical outlier detection
- **"top 10 volatile stocks"** → Ranked by volatility metrics

Works with any dataset:
- "show me a summary" → Overview with statistics
- "average [column] by [category]" → Grouped aggregation
- "distribution of [column]" → Value counts and percentages
- "top 10 [column]" → Highest values ranked

---

##  How It Works

```
Your Question
    
1. AI Intent Detection (understands what you want)
    
2. Query Refinement (makes query more analytical)
    
3. Code Generation (creates pandas/Python code)
    
4. Security Validation (checks for safety)
    
5. Sandboxed Execution (runs code safely)
    
6. Insight Generation (creates charts + analysis)
    
7. Answer Synthesis (plain-language explanation)
    
Results: Chart + Data + Plain-English Answer
```

---

##  Project Structure

```
NLytics/
 backend/
    main.py                    # Flask application
    requirements.txt           # Dependencies
    services/                  # Core AI services
       ai_intent_detector.py  # Understands queries
       query_refiner.py       # Makes queries better
       code_generator.py      # Generates pandas code
       code_validator.py      # Security validation
       safe_executor.py       # Sandboxed execution
       insight_generator.py   # Charts & analysis
       answer_synthesizer.py  # Plain answers
    models/
        chat_message.py        # Message types
 frontend/
    index.html                 # Chat interface
    static/
        js/app.js              # Frontend logic
        css/style.css          # Styling
 data/
    uploads/                   # Your uploaded files
    processed/                 # Cleaned data (auto-cleanup)
 samples/                       # Sample CSV files
    sample_data.csv
    stock_data_july_2025.csv
 docs/                          # Additional documentation
 .env                           # Your API keys (create this!)
 start.py                       # Startup script
 README.md                      # This file
```

---

##  Configuration

### Environment Variables (.env)
```env
# Required
GROQ_API_KEY=your_groq_api_key_here
```

### Supported Files
- CSV (.csv)
- Excel (.xlsx, .xls)
- Max size: 50MB

### Execution Settings
- Query timeout: 30 seconds
- Max code retries: 3 attempts
- Result limit: Top 10 rows for comparisons

---

##  Security

### Validation Layers
1. **Blacklist Check**: No eval, exec, open, os, sys, subprocess
2. **Import Whitelist**: Only pandas and numpy allowed
3. **AST Parsing**: Syntax validation before execution
4. **Column Validation**: Only uses columns that exist in your data

### Sandboxed Execution
- Restricted __builtins__ (only safe functions like len, sum, max)
- No file system access
- No network access
- Timeout enforcement
- Memory limits

---

##  Documentation

For more details, check the `docs/` folder:
- **AI_SETUP.md** - Groq API key setup guide
- **TROUBLESHOOTING.md** - Common issues & fixes
- **PROJECT_COMPLETE.md** - Complete technical overview

---

##  Why NLytics?

1. **Real Code, Not Black Boxes**: See the actual pandas code generated for every query
2. **Query Intelligence**: Automatically refines queries for better insights
3. **Context-Aware AI**: Understands your column names and data types
4. **Transparency**: Shows you the code before execution
5. **Educational**: Learn pandas by seeing how queries become code

---

##  Requirements

- **Python**: 3.9 or higher
- **RAM**: 2GB minimum
- **Internet**: Required for AI API calls
- **Browser**: Any modern browser

---

##  Contributing

1. Fork the repo
2. Create a feature branch (git checkout -b feature/cool-feature)
3. Commit changes (git commit -m 'Add cool feature')
4. Push to branch (git push origin feature/cool-feature)
5. Open a Pull Request

---

##  License

MIT License

---

##  Tech Stack

- **AI:** Groq Llama 3.3-70B (fast LLM inference)
- **Backend:** Flask + Pandas + NumPy
- **Frontend:** Vanilla JS + Chart.js + Marked.js
- **Testing:** pytest

---

**Built for students, analysts, and anyone who wants to understand their data without coding.**